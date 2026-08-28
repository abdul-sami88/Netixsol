"""
chunk_experiment.py — Task 2: "Evaluate different chunk sizes."

Since individual documents here (property brochures, FAQs) are naturally
short (50-90 words), we stress-test chunking the way it matters in
practice: by concatenating ALL documents into a handful of long synthetic
"pages" (simulating long brochures/PDFs) and then chunking THOSE at
different sizes, measuring:

  - Recall@5: for each of a set of labelled queries (query -> the doc_id
    that should be retrieved), does the correct source document's content
    appear in the top-5 retrieved chunks?
  - Avg chunk count (index size / cost proxy)
  - Avg chunk length (context-window cost proxy)

Run: python3 -m rag.chunk_experiment
"""
import os
import random
from document_loader import load_documents, Document
from chunking import chunk_documents
from embeddings import get_embedder
from vector_store import VectorStore

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "..", "db", "real_estate.db")

CHUNK_SIZES = [25, 50, 100, 200, 400]
OVERLAP_RATIO = 0.2


def build_long_pages(docs: list[Document], docs_per_page: int = 8) -> list[Document]:
    """Simulate long-form brochures by concatenating several short
    documents into a handful of multi-hundred-word pages, tagging which
    original doc_ids ended up on each page (used as ground truth)."""
    random.seed(7)
    shuffled = docs[:]
    random.shuffle(shuffled)
    pages = []
    for i in range(0, len(shuffled), docs_per_page):
        group = shuffled[i:i + docs_per_page]
        if not group:
            continue
        text = " ".join(f"[[{d.doc_id}]] {d.text}" for d in group)
        page_id = f"page_{i // docs_per_page}"
        pages.append(Document(doc_id=page_id, text=text,
                               metadata={"source_doc_ids": [d.doc_id for d in group]}))
    return pages


def make_eval_queries(docs: list[Document], n=25):
    """Ground-truth queries: pick a doc, use a distinctive substring of its
    own text as a proxy 'question' whose correct target is that doc."""
    random.seed(3)
    picks = random.sample(docs, min(n, len(docs)))
    queries = []
    for d in picks:
        words = d.text.split()
        if len(words) < 12:
            continue
        # take a mid-slice as a "query" (proxy for someone asking about that fact)
        snippet = " ".join(words[4:12])
        queries.append((snippet, d.doc_id))
    return queries


def recall_at_k(pages, chunk_size, overlap, queries, k=5):
    overlap_words = max(1, int(chunk_size * OVERLAP_RATIO))
    chunks = chunk_documents(pages, chunk_size=chunk_size, overlap=overlap_words)
    embedder = get_embedder("tfidf")
    store = VectorStore(embedder).build(chunks)

    hits = 0
    for query, target_doc_id in queries:
        results = store.search(query, top_k=k)
        found = any(target_doc_id in c.chunk_id or f"[[{target_doc_id}]]" in c.text
                    for c, _ in results)
        hits += int(found)
    recall = hits / len(queries)
    avg_len = sum(len(c.text.split()) for c in chunks) / len(chunks)
    return dict(chunk_size=chunk_size, overlap=overlap_words, n_chunks=len(chunks),
                avg_chunk_words=round(avg_len, 1), recall_at_5=round(recall, 3))


def run():
    docs = load_documents(DB)
    pages = build_long_pages(docs, docs_per_page=8)
    queries = make_eval_queries(docs, n=30)
    print(f"{len(pages)} synthetic long pages built from {len(docs)} docs, {len(queries)} eval queries\n")

    results = []
    for cs in CHUNK_SIZES:
        r = recall_at_k(pages, cs, None, queries, k=5)
        results.append(r)
        print(f"chunk_size={cs:>4} | n_chunks={r['n_chunks']:>4} | avg_words/chunk={r['avg_chunk_words']:>6} "
              f"| Recall@5={r['recall_at_5']}")
    return results


if __name__ == "__main__":
    run()
