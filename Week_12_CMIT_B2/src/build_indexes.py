"""Task 5: Build BM25 index + ChromaDB vector index with legal metadata & parent lookup."""

import argparse
import json
from pathlib import Path
import pickle
import re
import chromadb
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
from tqdm import tqdm


CHILDREN_JSONL = Path("outputs/chunks_children.jsonl")
PARENTS_JSON = Path("outputs/chunks_parents.json")
BM25_PATH = Path("indexes/bm25_index.pkl")
CHROMA_DIR = Path("indexes/chroma_db")
EMBED_MODEL = "intfloat/multilingual-e5-small"

TOKEN_RE = re.compile(r"[A-Za-z0-9]+|[\u0600-\u06FF]+")


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in TOKEN_RE.findall(text)]


def load_children(limit: int = 0) -> list[dict]:
    chunks = []
    with CHILDREN_JSONL.open("r", encoding="utf-8") as fin:
        for line in fin:
            chunks.append(json.loads(line))
            if limit > 0 and len(chunks) >= limit:
                break
    return chunks


def build_bm25(chunks: list[dict]) -> None:
    BM25_PATH.parent.mkdir(parents=True, exist_ok=True)
    tokenized = [tokenize(c["text"]) for c in chunks]
    bm25 = BM25Okapi(tokenized)
    payload = {"bm25": bm25, "chunks": chunks}
    with BM25_PATH.open("wb") as fout:
        pickle.dump(payload, fout)
    print(f"Saved BM25 index ({len(chunks)} chunks) to {BM25_PATH}")


def build_chroma(chunks: list[dict], batch_size: int = 32) -> None:
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    # Recreate collection cleanly on rebuild
    try:
        client.delete_collection("khan_associates_legal")
    except Exception:
        pass
    collection = client.create_collection(
        name="khan_associates_legal",
        metadata={"hnsw:space": "cosine"},
    )

    print(f"Loading embedding model '{EMBED_MODEL}' (CPU)...")
    model = SentenceTransformer(EMBED_MODEL, device="cpu")

    for start in tqdm(range(0, len(chunks), batch_size), desc="Indexing ChromaDB"):
        batch = chunks[start : start + batch_size]
        texts = [f"passage: {c['text']}" for c in batch]
        embeddings = model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=False,
        ).tolist()

        ids = [c["chunk_id"] for c in batch]
        docs = [c["text"] for c in batch]
        metas = [
            {
                "parent_id": str(c.get("parent_id", "")),
                "doc_id": str(c.get("doc_id", "")),
                "matter_id": str(c.get("matter_id", "")),
                "doc_type": str(c.get("doc_type", "")),
                "language": str(c.get("language", "")),
                "act": str(c.get("act", ""))[:200],
                "section": str(c.get("section", ""))[:100],
                "court": str(c.get("court", ""))[:120],
                "year": int(c.get("year") or 0),
                "page": int(c.get("page") or 1),
            }
            for c in batch
        ]
        collection.add(ids=ids, documents=docs, embeddings=embeddings, metadatas=metas)

    print(f"Saved ChromaDB collection ({collection.count()} chunks) to {CHROMA_DIR}")


def run_sanity_queries(parents: dict) -> None:
    """Verify hybrid retrieval + metadata filtering + parent lookup."""
    with BM25_PATH.open("rb") as fin:
        bm25_data = pickle.load(fin)
    bm25 = bm25_data["bm25"]
    chunks = bm25_data["chunks"]

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_collection("khan_associates_legal")
    model = SentenceTransformer(EMBED_MODEL, device="cpu")

    test_queries = [
        ("What is the punishment for qatl-i-amd under Section 302?", {"doc_type": "statute"}),
        ("limitation of liability aggregate fees twelve months", {"doc_type": "contract"}),
    ]
    print("\n=== HYBRID RETRIEVAL SANITY CHECK ===")
    for q, where_filter in test_queries:
        q_emb = model.encode([f"query: {q}"], normalize_embeddings=True).tolist()
        vec_res = collection.query(query_embeddings=q_emb, n_results=2, where=where_filter)
        scores = bm25.get_scores(tokenize(q))
        top_bm25_idx = max(range(len(scores)), key=lambda i: scores[i])

        print(f"\nQuery: {q} (filter={where_filter})")
        if vec_res["metadatas"] and vec_res["metadatas"][0]:
            m = vec_res["metadatas"][0][0]
            parent_len = len(parents.get(m["parent_id"], {}).get("text", ""))
            print(f"  [Vector Top-1] {m['matter_id']} | {m['act']} | Sec {m['section']} | p.{m['page']} (parent {parent_len} chars)")
        b_top = chunks[top_bm25_idx]
        print(f"  [BM25   Top-1] {b_top['matter_id']} | {b_top['act']} | Sec {b_top['section']} | p.{b_top['page']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build BM25 and ChromaDB hybrid indexes.")
    parser.add_argument("--vector-limit", type=int, default=0, help="Optional cap on chunks embedded into ChromaDB (0 = all).")
    parser.add_argument("--batch-size", type=int, default=32)
    args = parser.parse_args()

    all_chunks = load_children()
    print(f"Loaded {len(all_chunks)} child chunks from {CHILDREN_JSONL}")
    build_bm25(all_chunks)

    vec_chunks = all_chunks[: args.vector_limit] if args.vector_limit > 0 else all_chunks
    build_chroma(vec_chunks, batch_size=args.batch_size)

    parents = json.loads(PARENTS_JSON.read_text(encoding="utf-8"))
    run_sanity_queries(parents)


if __name__ == "__main__":
    main()

