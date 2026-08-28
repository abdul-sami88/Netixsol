"""
vector_store.py — Task 2 step 4.

A minimal in-memory vector store (cosine similarity over numpy arrays).
Swappable for FAISS/pgvector/Chroma in production; interface is the same
either way (`add`, `search`).
"""
from __future__ import annotations
import numpy as np
from chunking import Chunk


class VectorStore:
    def __init__(self, embedder):
        self.embedder = embedder
        self.chunks: list[Chunk] = []
        self.vectors: np.ndarray | None = None

    def build(self, chunks: list[Chunk]):
        self.chunks = chunks
        texts = [c.text for c in chunks]
        self.embedder.fit(texts)
        self.vectors = self.embedder.embed(texts)
        return self

    def search(self, query: str, top_k: int = 5) -> list[tuple[Chunk, float]]:
        qvec = self.embedder.embed([query])[0]
        sims = self.vectors @ qvec  # both L2-normalized -> cosine similarity
        top_idx = np.argsort(-sims)[:top_k]
        return [(self.chunks[i], float(sims[i])) for i in top_idx]
