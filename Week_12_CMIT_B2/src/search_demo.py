"""Quick hybrid search helper (ChromaDB + BM25 + Parent-Child expansion) for Day 1 verification."""

import argparse
import json
from pathlib import Path
import pickle
import re
import chromadb
from sentence_transformers import SentenceTransformer


PARENTS_JSON = Path("outputs/chunks_parents.json")
BM25_PATH = Path("indexes/bm25_index.pkl")
CHROMA_DIR = Path("indexes/chroma_db")
EMBED_MODEL = "intfloat/multilingual-e5-small"
TOKEN_RE = re.compile(r"[A-Za-z0-9]+|[\u0600-\u06FF]+")


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in TOKEN_RE.findall(text)]


def hybrid_search(query: str, doc_type: str | None = None, top_k: int = 5) -> list[dict]:
    """Combine Reciprocal Rank Fusion (RRF) of Vector DB and BM25, expanding to parent text."""
    parents = json.loads(PARENTS_JSON.read_text(encoding="utf-8"))
    with BM25_PATH.open("rb") as fin:
        bm25_data = pickle.load(fin)
    bm25 = bm25_data["bm25"]
    chunks = bm25_data["chunks"]

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_collection("khan_associates_legal")
    model = SentenceTransformer(EMBED_MODEL, device="cpu")

    where = {"doc_type": doc_type} if doc_type else None
    q_emb = model.encode([f"query: {query}"], normalize_embeddings=True).tolist()
    vec_res = collection.query(query_embeddings=q_emb, n_results=top_k * 2, where=where)

    rrf_scores: dict[str, float] = {}
    meta_by_parent: dict[str, dict] = {}

    if vec_res["metadatas"] and vec_res["metadatas"][0]:
        for rank, meta in enumerate(vec_res["metadatas"][0], 1):
            pid = meta["parent_id"]
            rrf_scores[pid] = rrf_scores.get(pid, 0.0) + 1.0 / (60 + rank)
            meta_by_parent[pid] = meta

    bm25_scores = bm25.get_scores(tokenize(query))
    ranked_bm25 = sorted(range(len(chunks)), key=lambda i: bm25_scores[i], reverse=True)
    bm25_added = 0
    for idx in ranked_bm25:
        ch = chunks[idx]
        if doc_type and ch.get("doc_type") != doc_type:
            continue
        pid = ch["parent_id"]
        bm25_added += 1
        rrf_scores[pid] = rrf_scores.get(pid, 0.0) + 1.0 / (60 + bm25_added)
        meta_by_parent.setdefault(pid, ch)
        if bm25_added >= top_k * 2:
            break

    results = []
    for pid, score in sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]:
        parent = parents.get(pid, {})
        meta = meta_by_parent[pid]
        results.append({
            "rrf_score": round(score, 5),
            "matter_id": meta.get("matter_id"),
            "doc_type": meta.get("doc_type"),
            "act": meta.get("act"),
            "section": meta.get("section"),
            "court": meta.get("court"),
            "year": meta.get("year"),
            "page": meta.get("page"),
            "parent_text_preview": parent.get("text", "")[:240].replace("\n", " "),
        })
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Test hybrid legal search.")
    parser.add_argument("query", nargs="?", default="punishment for qatl-i-amd Section 302")
    parser.add_argument("--type", dest="doc_type", default=None, help="Filter: statute, judgment, contract, scanned_urdu")
    parser.add_argument("--top-k", type=int, default=3)
    args = parser.parse_args()

    hits = hybrid_search(args.query, doc_type=args.doc_type, top_k=args.top_k)
    print(json.dumps(hits, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

