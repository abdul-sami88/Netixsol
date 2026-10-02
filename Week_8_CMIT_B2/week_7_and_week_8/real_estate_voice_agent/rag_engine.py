import time
from pathlib import Path
from typing import List, Dict, Any, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from database import get_db_connection

KNOWLEDGE_DIR = Path(__file__).parent / "knowledge_docs"

class TextChunk:
    def __init__(self, content: str, source: str, chunk_id: int):
        self.content = content
        self.source = source
        self.chunk_id = chunk_id

class RAGEngine:
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 64):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.chunks: List[TextChunk] = []
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.tfidf_matrix = None
        self.load_documents()

    def load_documents(self):
        self.chunks = []
        raw_texts = []
        
        # 1. Load markdown knowledge docs
        if KNOWLEDGE_DIR.exists():
            for filepath in KNOWLEDGE_DIR.glob("*.md"):
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                    raw_texts.append((content, filepath.name))

        # 2. Load FAQs from database
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT category, question, answer FROM faqs")
            faqs = cursor.fetchall()
            conn.close()
            faq_text = "\n\n".join([f"FAQ Category: {f['category']}\nQuestion: {f['question']}\nAnswer: {f['answer']}" for f in faqs])
            if faq_text:
                raw_texts.append((faq_text, "Database FAQs"))
        except Exception:
            pass

        # 3. Chunking logic
        chunk_id = 0
        for text, source in raw_texts:
            text_chunks = self._chunk_text(text, self.chunk_size, self.chunk_overlap)
            for c in text_chunks:
                self.chunks.append(TextChunk(content=c, source=source, chunk_id=chunk_id))
                chunk_id += 1

        # Build Vector Store Matrix
        if self.chunks:
            corpus = [c.content for c in self.chunks]
            self.tfidf_matrix = self.vectorizer.fit_transform(corpus)

    def _chunk_text(self, text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
        words = text.split()
        chunks = []
        i = 0
        while i < len(words):
            chunk = " ".join(words[i:i + chunk_size])
            chunks.append(chunk)
            i += max(1, chunk_size - chunk_overlap)
        return chunks

    def retrieve(self, query: str, top_k: int = 3) -> List[Tuple[TextChunk, float]]:
        if not self.chunks or self.tfidf_matrix is None:
            return []

        query_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            if scores[idx] > 0.05: # Minimum relevance threshold
                results.append((self.chunks[idx], float(scores[idx])))
        return results

    def get_context_str(self, query: str, top_k: int = 3) -> str:
        results = self.retrieve(query, top_k=top_k)
        if not results:
            return ""
        context_blocks = []
        for chunk, score in results:
            context_blocks.append(f"[{chunk.source} | Score: {score:.2f}]:\n{chunk.content}")
        return "\n\n".join(context_blocks)

def evaluate_chunk_sizes(sample_queries: List[str]) -> Dict[int, Dict[str, Any]]:
    """Evaluate retrieval accuracy, average score, and latency across chunk sizes (128, 256, 512, 1024)."""
    sizes = [128, 256, 512, 1024]
    metrics = {}

    for size in sizes:
        start_t = time.time()
        engine = RAGEngine(chunk_size=size, chunk_overlap=max(16, size // 8))
        load_time = time.time() - start_t
        
        query_times = []
        query_scores = []
        hit_count = 0
        
        for q in sample_queries:
            t0 = time.time()
            res = engine.retrieve(q, top_k=3)
            query_times.append(time.time() - t0)
            if res:
                hit_count += 1
                query_scores.append(res[0][1]) # top 1 score
            else:
                query_scores.append(0.0)

        metrics[size] = {
            "chunk_count": len(engine.chunks),
            "avg_query_time_ms": float(np.mean(query_times) * 1000),
            "avg_top_score": float(np.mean(query_scores)),
            "retrieval_hit_rate": float(hit_count / len(sample_queries)),
            "load_time_sec": float(load_time)
        }
        
    return metrics

if __name__ == "__main__":
    test_queries = [
        "DHA transfer procedure requirements",
        "Emaar Crescent Bay NOC approval SBCA",
        "Overseas Pakistani Power of Attorney RDA account",
        "Installment discount upfront cash payment"
    ]
    print("Evaluating Chunk Sizes for RAG Pipeline...")
    res = evaluate_chunk_sizes(test_queries)
    for size, stats in res.items():
        print(f"\nChunk Size {size} words:")
        print(f"  Total Chunks: {stats['chunk_count']}")
        print(f"  Avg Top Score: {stats['avg_top_score']:.4f}")
        print(f"  Hit Rate: {stats['retrieval_hit_rate']*100:.1f}%")
        print(f"  Avg Retrieval Latency: {stats['avg_query_time_ms']:.2f} ms")
