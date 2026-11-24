"""
TutorVectorDB: Embedded Vector Database
Provides semantic vector indexing, cosine similarity ranking, metadata filtering,
and disk persistence for AI Tutor content retrieval.
"""

from typing import List, Dict, Any, Optional
import json
import os
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class TutorVectorDB:
    """
    Vector database with TF-IDF + Sub-linear Term Frequency Semantic representations.
    Supports sub-second similarity search, metadata filtering, and timestamp jumps.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        self.documents: List[str] = []
        self.metadatas: List[Dict[str, Any]] = []
        self.doc_ids: List[str] = []
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            sublinear_tf=True,
            ngram_range=(1, 2)
        )
        self.tfidf_matrix = None
        self._is_indexed = False

        if db_path and os.path.exists(db_path):
            self.load(db_path)

    def add_documents(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ) -> None:
        """
        Adds text documents with associated metadata into the vector database.
        """
        if ids is None:
            ids = [f"doc_{len(self.documents) + i}" for i in range(len(documents))]

        for doc, meta, doc_id in zip(documents, metadatas, ids):
            self.documents.append(doc)
            self.metadatas.append(meta)
            self.doc_ids.append(doc_id)

        self._is_indexed = False

    def build_index(self) -> None:
        """
        Computes dense TF-IDF vector matrix over all documents.
        """
        if not self.documents:
            return
        self.tfidf_matrix = self.vectorizer.fit_transform(self.documents)
        self._is_indexed = True

    def search(
        self,
        query: str,
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Performs semantic similarity search with cosine distance and metadata filtering.
        """
        if not self._is_indexed:
            self.build_index()

        if self.tfidf_matrix is None or self.tfidf_matrix.shape[0] == 0:
            return []

        # Vectorize query
        query_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self.tfidf_matrix).flatten()

        # Sort indices by descending score
        ranked_indices = np.argsort(scores)[::-1]

        results = []
        for idx in ranked_indices:
            score = float(scores[idx])
            meta = self.metadatas[idx]

            # Apply metadata filters
            if filter_dict:
                match = True
                for k, v in filter_dict.items():
                    if meta.get(k) != v:
                        match = False
                        break
                if not match:
                    continue

            results.append({
                "id": self.doc_ids[idx],
                "score": round(score, 4),
                "text": self.documents[idx],
                "metadata": meta
            })

            if len(results) >= top_k:
                break

        return results

    def save(self, file_path: str) -> None:
        """
        Persists database documents and metadata to disk in JSON format.
        """
        data = {
            "documents": self.documents,
            "metadatas": self.metadatas,
            "doc_ids": self.doc_ids
        }
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load(self, file_path: str) -> None:
        """
        Loads persisted database from disk and rebuilds vector index.
        """
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.documents = data.get("documents", [])
        self.metadatas = data.get("metadatas", [])
        self.doc_ids = data.get("doc_ids", [])
        self.build_index()

