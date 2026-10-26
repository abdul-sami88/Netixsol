"""
Zarya Digital Bank - Multilingual RAG Engine
Week 10 - Day 4: Task 3 RAG + Fine-Tune Hybrid Implementation
"""

import os
import json
from typing import List, Dict, Any, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


POLICY_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "rag", "zarya_banking_policies.json")


class ZaryaBankingRAG:
    """
    RAG Engine for sovereign retail banking policies (UrduLish + English).
    Uses multilingual sublinear TF-IDF character & word n-grams for zero-dependency robust local inference.
    """

    def __init__(self, policy_file: str = POLICY_PATH):
        self.policy_file = os.path.abspath(policy_file)
        self.documents: List[Dict[str, Any]] = []
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.doc_vectors = None
        self.load_and_index()

    def load_and_index(self):
        """Loads policy JSON and builds the search index."""
        if not os.path.exists(self.policy_file):
            raise FileNotFoundError(f"Policy file not found: {self.policy_file}")

        with open(self.policy_file, "r", encoding="utf-8") as f:
            self.documents = json.load(f)

        # Build corpus of combined UrduLish + English + Keywords
        corpus = []
        for doc in self.documents:
            keywords_str = " ".join(doc.get("keywords", []))
            text = f"{doc.get('title', '')} {keywords_str} {doc.get('content_ur', '')} {doc.get('content_en', '')}"
            corpus.append(text)

        # Multilingual character n-gram + word vectorizer captures UrduLish transliterations
        self.vectorizer = TfidfVectorizer(
            analyzer="word",
            ngram_range=(1, 3),
            sublinear_tf=True,
            lowercase=True
        )
        self.doc_vectors = self.vectorizer.fit_transform(corpus)

    def retrieve(self, query: str, top_k: int = 2) -> List[Dict[str, Any]]:
        """
        Retrieves top_k most relevant policy chunks.
        """
        if not self.vectorizer or self.doc_vectors is None:
            self.load_and_index()

        query_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self.doc_vectors)[0]

        top_indices = np.argsort(scores)[::-1][:top_k]
        results = []
        for idx in top_indices:
            score = float(scores[idx])
            doc = dict(self.documents[idx])
            doc["retrieval_score"] = round(score, 4)
            results.append(doc)
        return results

    def build_augmented_prompt(self, query: str, top_k: int = 2) -> Dict[str, Any]:
        """
        Constructs system prompt with retrieved context and returns full chat message.
        """
        retrieved_docs = self.retrieve(query, top_k=top_k)

        context_snippets = []
        for i, doc in enumerate(retrieved_docs, 1):
            context_snippets.append(
                f"[Doc {i} - {doc['doc_id']} ({doc['title']})]:\n"
                f"UrduLish: {doc['content_ur']}\n"
                f"English: {doc['content_en']}\n"
                f"Effective Date: {doc.get('effective_date', 'N/A')}"
            )

        context_block = "\n\n".join(context_snippets)

        system_prompt = (
            "Aap Zarya Digital Bank ke official customer support AI assistant hain.\n"
            "Guiding Principles:\n"
            "1. Strictly answer based on the following verified bank policy schedule. Do NOT hallucinate fees or limits.\n"
            "2. Always communicate in courteous, authentic Pakistani UrduLish.\n"
            "3. State exact fees, turnaround times, and regulatory limits.\n\n"
            f"--- OFFICIAL ZARYA BANK POLICIES ---\n{context_block}\n-------------------------------------"
        )

        return {
            "system_prompt": system_prompt,
            "user_query": query,
            "retrieved_docs": retrieved_docs
        }

    def update_policy_document(self, doc_id: str, new_fields: Dict[str, Any]) -> bool:
        """
        Demonstrates RAG capability: updates a policy document on disk and re-indexes.
        No model retraining needed!
        """
        updated = False
        for doc in self.documents:
            if doc["doc_id"] == doc_id:
                doc.update(new_fields)
                updated = True
                break

        if updated:
            with open(self.policy_file, "w", encoding="utf-8") as f:
                json.dump(self.documents, f, indent=2, ensure_ascii=False)
            self.load_and_index()
            return True
        return False
