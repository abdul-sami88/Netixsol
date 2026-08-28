"""
pipeline.py — Task 2 orchestrator: loader -> chunker -> embedder -> vector
store -> hybrid retriever -> generator, exposed as one `RAGPipeline` object.
"""
from __future__ import annotations
import os
from document_loader import load_documents
from chunking import chunk_documents
from embeddings import get_embedder
from vector_store import VectorStore
from retriever import StructuredRetriever, SemanticRetriever, HybridRetriever
from generator import generate_answer
from query_understanding import extract_filters

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB = os.path.join(HERE, "..", "db", "real_estate.db")


class RAGPipeline:
    def __init__(self, db_path: str = DEFAULT_DB, chunk_size: int = 100,
                 overlap: int = 20, embed_backend: str = "auto"):
        self.db_path = db_path
        docs = load_documents(db_path)
        chunks = chunk_documents(docs, chunk_size=chunk_size, overlap=overlap)
        embedder = get_embedder(embed_backend)
        self.store = VectorStore(embedder).build(chunks)

        self.structured = StructuredRetriever(db_path)
        self.semantic = SemanticRetriever(self.store)
        self.retriever = HybridRetriever(self.structured, self.semantic)
        self.n_docs = len(docs)
        self.n_chunks = len(chunks)

    def ask(self, query: str, top_k: int = 5) -> dict:
        filters = extract_filters(query)
        result = self.retriever.retrieve(query, filters=filters, top_k=top_k)
        answer = generate_answer(query, result)
        answer["route"] = result.route
        answer["filters_used"] = filters
        return answer


if __name__ == "__main__":
    pipe = RAGPipeline()
    print(f"Indexed {pipe.n_docs} documents -> {pipe.n_chunks} chunks")
    for q in [
        "What is the average price of houses in Lahore?",
        "What documents are required to buy a property in Pakistan?",
        "Show me a 3 bedroom house for sale in Karachi under 20 million",
    ]:
        out = pipe.ask(q)
        print("\nQ:", q)
        print("Route:", out["route"], "| Filters:", out["filters_used"])
        print("A:", out["answer"][:400])
