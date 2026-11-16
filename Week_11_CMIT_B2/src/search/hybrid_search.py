"""
Hybrid Search Engine for ShopKaro E-Commerce Platform
Implements Task 1:
- BM25 Keyword Search (rank_bm25)
- Multilingual Semantic Vector Search (TF-IDF / Sublinear n-grams)
- Reciprocal Rank Fusion (RRF) Hybrid Scoring
- Cross-Encoder Interaction Reranker (Top 50 candidates) with query attribute constraints
"""

import os
import re
import duckdb
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import TfidfVectorizer
import scipy.sparse as sp

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "data", "processed", "shopkaro.duckdb")

from src.search.query_parser import QueryUnderstandingEngine


def tokenize_corpus(text: str) -> List[str]:
    """Tokenizes text into lowercase alphanumeric words."""
    if not isinstance(text, str):
        return []
    return re.findall(r'\b[a-zA-Z0-9_\-]+\b', text.lower())


class HybridSearchEngine:
    """
    Two-stage retrieval and ranking engine:
    Stage 1: Multi-index retrieval (BM25 lexical + Semantic dense/sparse vector) merged with RRF.
    Stage 2: Cross-Encoder interaction reranker over top 50 candidates applying query attribute constraints.
    """
    def __init__(self, rrf_k: int = 60):
        self.rrf_k = rrf_k
        self.query_parser = QueryUnderstandingEngine()
        
        # Catalogue storage
        self.products_df = None
        self.product_ids = []
        self.pid_to_idx = {}
        self.idx_to_pid = {}
        
        # BM25 model
        self.bm25 = None
        self.bm25_corpus = []
        
        # Semantic vector model (Optimized for < 200MB memory footprint)
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 1),
            sublinear_tf=True,
            max_features=4000,
            token_pattern=r'(?u)\b\w+\b'
        )
        self.item_vectors = None # (n_items, n_features)

    def fit(self, con=None):
        """Builds BM25 index and Semantic Vector matrix across all catalogue products."""
        import gc
        should_close = False
        if con is None:
            con = duckdb.connect(DB_PATH, read_only=True)
            should_close = True
            
        print("Loading 50,000 catalogue products for Search Indexing...")
        self.products_df = con.execute("""
            SELECT 
                p.product_id,
                p.title,
                p.category,
                p.subcategory,
                p.brand,
                p.price_pkr,
                p.stock_quantity,
                p.rating_avg,
                SUBSTRING(p.description, 1, 60) AS description,
                f.popularity_score
            FROM products p
            LEFT JOIN item_features f ON p.product_id = f.product_id
            ORDER BY p.product_id
        """).df()
        
        if should_close:
            con.close()
            
        self.product_ids = self.products_df["product_id"].tolist()
        self.pid_to_idx = {pid: i for i, pid in enumerate(self.product_ids)}
        self.idx_to_pid = {i: pid for i, pid in enumerate(self.product_ids)}
        
        # Build concise searchable document text
        doc_texts = []
        tokenized_corpus = []
        for row in self.products_df.itertuples(index=False):
            doc = f"{row.title} {row.brand} {row.category} {row.subcategory} {row.description}"
            doc_texts.append(doc)
            tokenized_corpus.append(tokenize_corpus(doc))
            
        print("Building BM25 Okapi lexical index...")
        self.bm25 = BM25Okapi(tokenized_corpus)
        del tokenized_corpus
        gc.collect()
        
        print("Building Multilingual Semantic Vector index (4,000 features)...")
        self.item_vectors = self.vectorizer.fit_transform(doc_texts).tocsr()
        del doc_texts
        gc.collect()

        # Normalize rows to unit length for fast cosine dot products
        norms = sp.linalg.norm(self.item_vectors, axis=1)
        norms[norms == 0] = 1.0
        self.item_vectors = self.item_vectors.multiply(1.0 / norms[:, None]).tocsr()
        gc.collect()
        
        print(f"Hybrid Search Engine ready! Indexed {len(self.products_df):,} SKUs.")
        return self

    def bm25_search(self, query: str, top_k: int = 50) -> List[Tuple[str, float]]:
        """Executes BM25 Okapi lexical search."""
        tokens = tokenize_corpus(query)
        if not tokens:
            return []
        scores = self.bm25.get_scores(tokens)
        top_indices = np.argsort(-scores)[:top_k]
        return [(self.idx_to_pid[i], float(scores[i])) for i in top_indices if scores[i] > 0]

    def semantic_search(self, query: str, top_k: int = 50) -> List[Tuple[str, float]]:
        """Executes Vector Space cosine similarity search."""
        q_vec = self.vectorizer.transform([query])
        q_norm = np.linalg.norm(q_vec.toarray())
        if q_norm > 0:
            q_vec = q_vec.multiply(1.0 / q_norm)
        # Cosine dot product: (1, dim) @ (dim, n_items) -> (n_items,)
        scores = np.asarray(self.item_vectors.dot(q_vec.T).toarray()).flatten()
        top_indices = np.argsort(-scores)[:top_k]
        return [(self.idx_to_pid[i], float(scores[i])) for i in top_indices if scores[i] > 0]

    def hybrid_search_rrf(self, query: str, top_k: int = 50) -> List[Tuple[str, float]]:
        """
        Combines BM25 and Semantic search rankings using Reciprocal Rank Fusion (RRF):
        RRF_score(d) = sum_{m} 1 / (k + rank_m(d))
        """
        parsed = self.query_parser.extract_attributes(query)
        clean_q = parsed["clean_query"]
        
        bm25_results = self.bm25_search(clean_q, top_k=100)
        semantic_results = self.semantic_search(clean_q, top_k=100)
        
        rrf_scores = {}
        for rank, (pid, _) in enumerate(bm25_results, 1):
            rrf_scores[pid] = rrf_scores.get(pid, 0.0) + (1.0 / (self.rrf_k + rank))
            
        for rank, (pid, _) in enumerate(semantic_results, 1):
            rrf_scores[pid] = rrf_scores.get(pid, 0.0) + (1.0 / (self.rrf_k + rank))
            
        sorted_rrf = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        return sorted_rrf

    def cross_encoder_rerank(self, query: str, candidate_pids: List[str], top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Stage 2 Cross-Encoder Style Reranking:
        Takes top candidates and scores exact multi-attribute alignment:
        - Query Category affinity
        - Price budget compliance (min_price, max_price)
        - Color match in title/description
        - Occasion / target audience match
        - Product rating & quality prior
        """
        parsed = self.query_parser.extract_attributes(query)
        inferred_cat = parsed["inferred_category"]
        color = parsed["color"]
        occasion = parsed["occasion"]
        min_p = parsed["min_price"]
        max_p = parsed["max_price"]
        clean_q_tokens = set(tokenize_corpus(parsed["clean_query"]))
        
        reranked = []
        for pid in candidate_pids:
            idx = self.pid_to_idx.get(pid)
            if idx is None:
                continue
            row = self.products_df.iloc[idx]
            
            title_lower = row["title"].lower()
            desc_lower = str(row["description"]).lower()
            title_tokens = set(tokenize_corpus(title_lower))
            
            # 1. Lexical overlap score (Jaccard on clean query tokens)
            overlap = len(clean_q_tokens.intersection(title_tokens))
            lex_score = overlap / max(1, len(clean_q_tokens))
            
            # 2. Category alignment
            cat_score = 1.0
            if inferred_cat:
                if row["category"] == inferred_cat:
                    cat_score = 1.5
                else:
                    cat_score = 0.3 # Penalize cross-category mismatch
                    
            # 3. Price constraint score
            price = float(row["price_pkr"])
            price_score = 1.0
            if max_p is not None:
                if price <= max_p:
                    # Reward items nicely within budget
                    price_score = 1.3
                elif price <= max_p * 1.15:
                    # Slight stretch (+15%)
                    price_score = 0.8
                else:
                    # Way above budget!
                    price_score = 0.2
                    
            if min_p is not None:
                if price < min_p * 0.8:
                    price_score *= 0.5
                    
            # 4. Color match
            color_score = 1.0
            if color:
                if color in title_lower or color in desc_lower:
                    color_score = 1.35
                else:
                    color_score = 0.8
                    
            # 5. Occasion / Festive match
            occasion_score = 1.0
            if occasion:
                occ_keywords = [w.lower() for w in occasion.split()]
                if any(kw in title_lower or kw in desc_lower for kw in occ_keywords):
                    occasion_score = 1.4
                    
            # 6. Quality & Rating prior
            rating_score = float(row["rating_avg"]) / 5.0
            pop_score = min(1.0, float(row["popularity_score"] or 0) / 100.0)
            
            # Final composite cross-encoder score
            total_score = (
                (lex_score * 0.35) +
                (rating_score * 0.10) +
                (pop_score * 0.05)
            ) * cat_score * price_score * color_score * occasion_score
            
            reranked.append({
                "product_id": pid,
                "title": row["title"],
                "category": row["category"],
                "brand": row["brand"],
                "price_pkr": int(price),
                "rating_avg": float(row["rating_avg"]),
                "stock_quantity": int(row["stock_quantity"]),
                "cross_score": round(float(total_score), 4),
                "in_budget": (max_p is None or price <= max_p) and (min_p is None or price >= min_p)
            })
            
        reranked.sort(key=lambda x: x["cross_score"], reverse=True)
        return reranked[:top_k]

    def search(self, query: str, top_k: int = 10, mode: str = "hybrid_cross") -> List[Dict[str, Any]]:
        """
        Unified search API:
        - mode='keyword': Pure BM25
        - mode='semantic': Pure Vector search
        - mode='hybrid': RRF fusion
        - mode='hybrid_cross': RRF + Cross-encoder reranking
        """
        if mode == "keyword":
            results = self.bm25_search(query, top_k=top_k)
            return [self._format_result(pid, score) for pid, score in results]
            
        elif mode == "semantic":
            results = self.semantic_search(query, top_k=top_k)
            return [self._format_result(pid, score) for pid, score in results]
            
        elif mode == "hybrid":
            results = self.hybrid_search_rrf(query, top_k=top_k)
            return [self._format_result(pid, score) for pid, score in results]
            
        else: # 'hybrid_cross'
            rrf_candidates = self.hybrid_search_rrf(query, top_k=50)
            candidate_pids = [pid for pid, _ in rrf_candidates]
            return self.cross_encoder_rerank(query, candidate_pids, top_k=top_k)

    def _format_result(self, pid: str, score: float) -> Dict[str, Any]:
        idx = self.pid_to_idx[pid]
        row = self.products_df.iloc[idx]
        return {
            "product_id": pid,
            "title": row["title"],
            "category": row["category"],
            "brand": row["brand"],
            "price_pkr": int(row["price_pkr"]),
            "rating_avg": float(row["rating_avg"]),
            "stock_quantity": int(row["stock_quantity"]),
            "score": round(float(score), 4)
        }

