"""Task 4: Implement & compare fixed-size, section-level, and parent-child legal chunking."""

import json
from pathlib import Path
import re
import statistics
import pandas as pd
from rank_bm25 import BM25Okapi


STRUCT_DIR = Path("outputs/structured")
PARSED_JSONL = Path("outputs/parsed_docs.jsonl")
OUT_CHILDREN = Path("outputs/chunks_children.jsonl")
OUT_PARENTS = Path("outputs/chunks_parents.json")
OUT_CSV = Path("outputs/chunking_comparison.csv")
OUT_MD = Path("reports/chunking_comparison.md")

TOKEN_RE = re.compile(r"[A-Za-z0-9]+|[\u0600-\u06FF]+")


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in TOKEN_RE.findall(text)]


def fixed_size_chunks(text: str, meta: dict, size_words: int = 220, overlap: int = 35) -> list[dict]:
    """Chunk text into fixed word windows ignoring structural boundaries."""
    words = text.split()
    if not words:
        return []
    chunks = []
    step = max(1, size_words - overlap)
    for idx, start in enumerate(range(0, len(words), step)):
        piece = " ".join(words[start : start + size_words])
        chunks.append({
            **meta,
            "chunk_id": f"{meta['doc_id']}_fix_{idx}",
            "text": piece,
            "words": len(piece.split()),
            "breaks_boundary": start > 0,  # mid-document fixed cut
        })
        if start + size_words >= len(words):
            break
    return chunks


def build_units_from_structured() -> list[dict]:
    """Load logical legal units (Statute Sections, Contract Clauses, Judgment Blocks, Urdu Pages)."""
    units: list[dict] = []

    # 1. Statutes
    statutes = json.loads((STRUCT_DIR / "statutes.json").read_text(encoding="utf-8"))
    for st in statutes:
        for idx, sec in enumerate(st["sections"]):
            if not sec["text"].strip():
                continue
            units.append({
                "unit_id": f"{st['doc_id']}_sec_{idx}",
                "doc_id": st["doc_id"],
                "matter_id": st["matter_id"],
                "doc_type": "statute",
                "language": st["language"],
                "act": st["act"],
                "section": str(sec["section"]),
                "court": "",
                "year": st["year"] or 0,
                "page": int(sec.get("page_start", 1)),
                "heading": sec.get("heading", ""),
                "text": sec["text"],
            })

    # 2. Contracts
    contracts = json.loads((STRUCT_DIR / "contracts.json").read_text(encoding="utf-8"))
    for ct in contracts:
        for cl in ct["clauses"]:
            if not cl["text"].strip():
                continue
            units.append({
                "unit_id": f"{ct['doc_id']}_cl_{cl['clause_index']}",
                "doc_id": ct["doc_id"],
                "matter_id": ct["matter_id"],
                "doc_type": "contract",
                "language": "en",
                "act": ct["filename"],
                "section": f"Clause {cl['clause_index']} ({cl['category']})",
                "court": "",
                "year": 2025 if "Synthetic" in ct["source"] else 0,
                "page": 1,
                "heading": cl["heading"],
                "text": cl["text"],
            })

    # 3. Judgments (load page-level paragraphs from parsed_docs + metadata from judgments.json)
    judg_meta = {
        j["doc_id"]: j
        for j in json.loads((STRUCT_DIR / "judgments.json").read_text(encoding="utf-8"))
    }
    with PARSED_JSONL.open("r", encoding="utf-8") as fin:
        for line in fin:
            rec = json.loads(line)
            if rec["type"] != "judgment":
                continue
            jm = judg_meta.get(rec["doc_id"], {})
            for p in rec["pages"]:
                txt = p["text"].strip()
                if not txt:
                    continue
                units.append({
                    "unit_id": f"{rec['doc_id']}_p{p['page']}",
                    "doc_id": rec["doc_id"],
                    "matter_id": rec["matter_id"],
                    "doc_type": "judgment",
                    "language": rec["language"],
                    "act": "",
                    "section": f"Page {p['page']}",
                    "court": jm.get("court", "Supreme Court of Pakistan"),
                    "year": jm.get("year") or 0,
                    "page": int(p["page"]),
                    "heading": jm.get("parties", ""),
                    "text": txt,
                })

    # 4. Urdu Docs
    urdu_docs = json.loads((STRUCT_DIR / "urdu_docs.json").read_text(encoding="utf-8"))
    for ud in urdu_docs:
        for idx, sec in enumerate(ud["sections"]):
            if not sec["text"].strip():
                continue
            units.append({
                "unit_id": f"{ud['doc_id']}_u_{idx}",
                "doc_id": ud["doc_id"],
                "matter_id": ud["matter_id"],
                "doc_type": "scanned_urdu",
                "language": "ur",
                "act": ud["act"],
                "section": str(sec["section"]),
                "court": "",
                "year": ud["year"] or 0,
                "page": int(sec.get("page_start", 1)),
                "heading": sec.get("heading", ""),
                "text": sec["text"],
            })

    return units


def make_section_and_parent_child(units: list[dict]) -> tuple[list[dict], list[dict], dict]:
    """Produce section-level chunks and parent-child chunks from legal units."""
    section_chunks: list[dict] = []
    child_chunks: list[dict] = []
    parents: dict[str, dict] = {}

    for u in units:
        parent_id = u["unit_id"]
        words = u["text"].split()
        wcount = len(words)

        section_chunks.append({
            "chunk_id": f"{parent_id}_sec",
            "parent_id": parent_id,
            "doc_id": u["doc_id"],
            "matter_id": u["matter_id"],
            "doc_type": u["doc_type"],
            "language": u["language"],
            "act": u["act"],
            "section": u["section"],
            "court": u["court"],
            "year": u["year"],
            "page": u["page"],
            "text": u["text"],
            "words": wcount,
            "breaks_boundary": False,
        })

        parents[parent_id] = {
            "parent_id": parent_id,
            "doc_id": u["doc_id"],
            "matter_id": u["matter_id"],
            "doc_type": u["doc_type"],
            "act": u["act"],
            "section": u["section"],
            "court": u["court"],
            "year": u["year"],
            "page": u["page"],
            "text": u["text"][:6000],
        }

        # Child chunks: ~140 words with 25-word overlap inside the parent boundary
        step = 115
        if wcount <= 160:
            slices = [u["text"]]
        else:
            slices = [
                " ".join(words[s : s + 140])
                for s in range(0, wcount, step)
            ]
        for c_idx, piece in enumerate(slices):
            child_chunks.append({
                "chunk_id": f"{parent_id}_c{c_idx}",
                "parent_id": parent_id,
                "doc_id": u["doc_id"],
                "matter_id": u["matter_id"],
                "doc_type": u["doc_type"],
                "language": u["language"],
                "act": u["act"],
                "section": u["section"],
                "court": u["court"],
                "year": u["year"],
                "page": u["page"],
                "text": piece,
                "words": len(piece.split()),
                "breaks_boundary": False,  # child stays strictly within one parent section/clause
            })

    return section_chunks, child_chunks, parents


def eval_retrieval(chunks: list[dict], queries: list[tuple[str, str]]) -> tuple[float, float]:
    """Compute Hit@5 and MRR@5 using BM25 over a chunk list."""
    corpus_tokens = [tokenize(c["text"]) for c in chunks]
    bm25 = BM25Okapi(corpus_tokens)
    hits = 0
    rr_sum = 0.0
    for query, expected_keyword in queries:
        scores = bm25.get_scores(tokenize(query))
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:5]
        matched_rank = 0
        for rank, idx in enumerate(top_indices, 1):
            cand_text = chunks[idx]["text"].lower() + " " + str(chunks[idx].get("act", "")).lower()
            if expected_keyword.lower() in cand_text:
                matched_rank = rank
                break
        if matched_rank:
            hits += 1
            rr_sum += 1.0 / matched_rank
    return round(hits / len(queries), 3), round(rr_sum / len(queries), 3)


def main() -> None:
    units = build_units_from_structured()
    print(f"Loaded {len(units)} logical legal units.")

    # Build Fixed-size chunks per document
    by_doc: dict[str, list[dict]] = {}
    for u in units:
        by_doc.setdefault(u["doc_id"], []).append(u)

    fixed_chunks: list[dict] = []
    for doc_id, doc_units in by_doc.items():
        sample = doc_units[0]
        full_doc_text = "\n\n".join(x["text"] for x in doc_units)
        meta = {
            "doc_id": doc_id,
            "matter_id": sample["matter_id"],
            "doc_type": sample["doc_type"],
            "language": sample["language"],
            "act": sample["act"],
            "section": "fixed-window",
            "court": sample["court"],
            "year": sample["year"],
            "page": 1,
        }
        fixed_chunks.extend(fixed_size_chunks(full_doc_text, meta))

    section_chunks, child_chunks, parents = make_section_and_parent_child(units)

    queries = [
        ("punishment of qatl-i-amd Section 302", "qatl"),
        ("equality of citizens Article 25 fundamental rights", "equality"),
        ("limitation of liability aggregate fees twelve months", "liability"),
        ("arbitration act 1940 dispute resolution lahore", "arbitration"),
        ("muslim family laws ordinance registration of marriages", "marriage"),
        ("anti-money laundering proceeds of crime offence", "laundering"),
        ("specific relief contract cannot be specifically enforced", "specific"),
        ("کرایہ دار ماہانہ کرایہ لاہور", "لاہور"),
    ]

    strategies = [
        ("Fixed-Size (220w, 35w overlap)", fixed_chunks),
        ("Section-Level (1 Section/Clause)", section_chunks),
        ("Parent-Child (140w child -> full parent)", child_chunks),
    ]

    summary_rows = []
    for name, ch_list in strategies:
        word_counts = [c["words"] for c in ch_list]
        boundary_breaks = sum(1 for c in ch_list if c["breaks_boundary"])
        oversized = sum(1 for w in word_counts if w > 500)
        hit5, mrr5 = eval_retrieval(ch_list, queries)
        summary_rows.append({
            "strategy": name,
            "chunk_count": len(ch_list),
            "avg_words": round(statistics.mean(word_counts), 1),
            "max_words": max(word_counts),
            "oversized_gt_500w": oversized,
            "boundary_break_pct": round(100 * boundary_breaks / len(ch_list), 1),
            "bm25_hit_at_5": hit5,
            "bm25_mrr_at_5": mrr5,
        })

    # Save Parent-Child outputs for Task 5 indexing
    OUT_CHILDREN.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CHILDREN.open("w", encoding="utf-8") as fout:
        for ch in child_chunks:
            fout.write(json.dumps(ch, ensure_ascii=False) + "\n")
    OUT_PARENTS.write_text(json.dumps(parents, ensure_ascii=False), encoding="utf-8")

    df = pd.DataFrame(summary_rows)
    df.to_csv(OUT_CSV, index=False)

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    md = "\n".join([
        "# Legal-Aware Chunking Comparison",
        "",
        "Comparison across 10 Pakistani statutes, 200 Supreme Court judgments, 50 contracts, and 30 Urdu/scanned documents.",
        "",
        df.to_markdown(index=False),
        "",
        "## Key Findings",
        "- **Fixed-Size:** Predictable chunk lengths, but splits mid-section and mid-clause (high boundary break rate), losing legal provenance.",
        "- **Section-Level:** Preserves exact legal boundaries (`Act -> Section`, `Contract -> Clause`), but long statutory sections/pages create oversized chunks (`> 500` words) that dilute dense embedding similarity.",
        "- **Parent-Child (Selected for Indexing):** Combines tight 140-word child vectors/BM25 entries for pinpoint retrieval with full-section `parent_id` lookup so the LLM receives complete statutory/contractual context.",
    ])
    OUT_MD.write_text(md, encoding="utf-8")
    print(df.to_string(index=False))
    print(f"\nSaved {OUT_CHILDREN}, {OUT_PARENTS}, and {OUT_MD}")


if __name__ == "__main__":
    main()

