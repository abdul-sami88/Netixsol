"""Task 3: Convert parsed statutes, judgments, contracts, and Urdu docs into structured JSON."""

import json
from pathlib import Path
import re
import pandas as pd


PARSED_JSONL = Path("outputs/parsed_docs.jsonl")
OUT_DIR = Path("outputs/structured")

STATUTE_NAMES = {
    "Penal_code_pakistan.pdf": ("Pakistan Penal Code, 1860", 1860),
    "Qaunun-e-shahadat.pdf": ("Qanun-e-Shahadat Order, 1984", 1984),
    "Specific-relief-act.pdf": ("Specific Relief Act, 1877", 1877),
    "The-muslim-family-law-ordinance.pdf": ("Muslim Family Laws Ordinance, 1961", 1961),
    "The_contitution_of_Pakistan.pdf": ("Constitution of the Islamic Republic of Pakistan, 1973", 1973),
    "anti-money-laundering.pdf": ("Anti-Money Laundering Act, 2010", 2010),
    "anti-terrorism-act.pdf": ("Anti-Terrorism Act, 1997", 1997),
    "code_of_civil_procedure_1908.pdf": ("Code of Civil Procedure, 1908", 1908),
    "contract_act.pdf": ("Contract Act, 1872", 1872),
    "criminal_code.pdf": ("Code of Criminal Procedure, 1898", 1898),
}

CASE_REPORT_RE = re.compile(
    r"\b(?:PLD\s+\d{4}\s+[A-Za-z]+\s+\d+|\d{4}\s+(?:SCMR|PLD|CLC|YLR|PCrLJ|PTD|PLC|CLD|MLD)\s+\d+)\b"
)
SECTION_LINE_RE = re.compile(
    r"(?m)^(?:Section|Article)?\s*(\d+[A-Z]{0,2})\.\s+([A-Z][^\n]{3,90})"
)
CLAUSE_SPLIT_RE = re.compile(
    r"(?m)^(?:ARTICLE\s+[IVXLC]+|SECTION\s+\d+|\d+\.)\s+([A-Z][A-Za-z0-9 ,/&()-]{2,80})"
)


def classify_clause(heading: str, body: str) -> str:
    """Assign a CUAD-style category label to a contract clause."""
    combined = (heading + " " + body[:300]).lower()
    mapping = [
        ("Governing Law / Dispute Resolution", ("governing law", "jurisdiction", "arbitration", "dispute")),
        ("Limitation of Liability", ("limitation of liability", "consequential damages", "aggregate liability")),
        ("Indemnification", ("indemnif", "hold harmless")),
        ("Term & Termination", ("termination", "term,", "force majeure", "cure")),
        ("Confidentiality / NDA", ("confidential", "non-disclosure", "proprietary", "non-solicitation")),
        ("Payment & Fees", ("consideration", "payment", "fee", "milestone", "invoice", "royalty")),
        ("Definitions", ("definition", "interpretation")),
        ("Representations & Warranties", ("representation", "warrant")),
        ("Intellectual Property", ("intellectual property", "copyright", "trademark", "license")),
    ]
    for label, keywords in mapping:
        if any(k in combined for k in keywords):
            return label
    return "General"


def extract_statute(record: dict) -> dict:
    """Extract Act -> Sections structure from a statute PDF."""
    act_name, year = STATUTE_NAMES.get(
        record["filename"], (Path(record["filename"]).stem.replace("_", " ").title(), None)
    )
    pages = record["pages"]
    # Build page-tagged text stream
    sections: list[dict] = []
    current: dict | None = None

    for p in pages:
        pno = p["page"]
        lines = p["text"].splitlines()
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            m = SECTION_LINE_RE.match(stripped)
            if m and len(m.group(1)) <= 4:
                if current is not None:
                    current["text"] = "\n".join(current["lines"]).strip()
                    del current["lines"]
                    if len(current["text"]) >= 20:
                        sections.append(current)
                current = {
                    "section": m.group(1),
                    "heading": m.group(2).strip(" .:-"),
                    "page_start": pno,
                    "page_end": pno,
                    "lines": [stripped],
                }
            elif current is not None:
                current["page_end"] = pno
                current["lines"].append(stripped)

    if current is not None:
        current["text"] = "\n".join(current["lines"]).strip()
        del current["lines"]
        if len(current["text"]) >= 20:
            sections.append(current)

    # Fallback if OCR/Urdu text didn't match English section numbers
    if not sections:
        sections = [
            {
                "section": f"Page-{p['page']}",
                "heading": f"Page {p['page']}",
                "page_start": p["page"],
                "page_end": p["page"],
                "text": p["text"],
            }
            for p in pages
            if p["text"].strip()
        ]

    return {
        "doc_id": record["doc_id"],
        "matter_id": record["matter_id"],
        "doc_type": "statute",
        "act": act_name,
        "year": year,
        "language": record["language"],
        "section_count": len(sections),
        "sections": sections,
    }


def extract_judgment(record: dict) -> dict:
    """Extract court, parties, judges, year, citations, and holding from a judgment."""
    pages = record["pages"]
    full_text = "\n\n".join(p["text"] for p in pages if p["text"].strip())
    first_page = pages[0]["text"] if pages else ""

    # Year from filename or text
    year_match = re.search(r"(19\d{2}|20\d{2})", record["filename"]) or re.search(
        r"\b(19\d{2}|20\d{2})\b", first_page
    )
    year = int(year_match.group(1)) if year_match else None

    # Court (all files in judgments_sample come from Supreme Court of Pakistan)
    court = "Supreme Court of Pakistan"

    # Judge from folder name in source + PRESENT block
    judge_from_src = re.sub(r"^Supreme Court of Pakistan \((.+)\)$", r"\1", record["source"])
    present_match = re.search(
        r"PRESENT:\s*(.+?)(?=\n\s*(?:Civil|Criminal|Constitutional|Jail|Human|Suo|Review|[A-Z]\.[A-Z]\.))",
        first_page,
        re.S | re.I,
    )
    bench = (
        re.sub(r"\s+", " ", present_match.group(1)).strip()
        if present_match
        else judge_from_src
    )

    # Parties (Petitioner/Appellant vs Respondent)
    parties_match = re.search(
        r"([A-Z][^\n]{2,120}(?:\n[^\n]{2,80})?)\s+(?:versus|vs\.?|v\.)\s+([^\n]{2,120}(?:\n[^\n]{2,80})?)",
        first_page,
        re.I,
    )
    if parties_match:
        p1 = re.sub(r"\s+", " ", parties_match.group(1)).strip()
        p2 = re.sub(r"\s+", " ", parties_match.group(2)).strip()
        parties = f"{p1[:100]} v. {p2[:100]}"
    else:
        parties = "Not extracted (check scanned/header format)"

    # Citations
    citations = sorted(set(CASE_REPORT_RE.findall(full_text)))[:30]
    statute_refs = sorted(
        set(re.findall(r"\b(?:Section|Article)\s+\d+[A-Z]?\b", full_text))
    )[:20]

    # Holding heuristic: search last 2 pages for operative conclusion sentences
    tail_text = "\n".join(p["text"] for p in pages[-2:]) if pages else ""
    holding = ""
    for pat in (
        r"(?is)((?:for the foregoing reasons|in view of the above|consequently|accordingly|for what has been discussed above).{40,700})",
        r"(?is)((?:the (?:appeal|petition) is (?:allowed|dismissed|disposed of)).{0,500})",
    ):
        hm = re.search(pat, tail_text)
        if hm:
            holding = re.sub(r"\s+", " ", hm.group(1)).strip()[:600]
            break
    if not holding and tail_text.strip():
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", tail_text) if len(p.strip()) > 60]
        holding = re.sub(r"\s+", " ", paragraphs[-1])[:500] if paragraphs else ""

    return {
        "doc_id": record["doc_id"],
        "matter_id": record["matter_id"],
        "doc_type": "judgment",
        "filename": record["filename"],
        "court": court,
        "author_judge": judge_from_src,
        "bench": bench[:200],
        "year": year,
        "parties": parties,
        "citations": citations,
        "statute_references": statute_refs,
        "holding": holding,
        "page_count": record["total_pages"],
    }


def extract_contract(record: dict) -> dict:
    """Extract contract metadata, numbered clauses, and tables."""
    pages = record["pages"]
    first_page = pages[0]["text"] if pages else ""
    full_text = "\n\n".join(p["text"] for p in pages if p["text"].strip())

    # Governing law
    gov_match = re.search(
        r"(?:governed by|construed in accordance with)[^.\n]{5,140}",
        full_text,
        re.I,
    )
    governing_law = re.sub(r"\s+", " ", gov_match.group(0)).strip() if gov_match else None

    # Parties
    parties_match = re.search(
        r"(?:by and between|between)\s+([^\n]{5,140})\s+and\s+([^\n]{5,140})",
        first_page,
        re.I,
    )
    parties = (
        f"{parties_match.group(1).strip()[:80]} & {parties_match.group(2).strip()[:80]}"
        if parties_match
        else None
    )

    # Split into clauses across pages
    clauses: list[dict] = []
    matches = list(CLAUSE_SPLIT_RE.finditer(full_text))
    if matches:
        for idx, m in enumerate(matches):
            start = m.start()
            end = matches[idx + 1].start() if idx + 1 < len(matches) else len(full_text)
            chunk_txt = full_text[start:end].strip()
            heading = m.group(1).strip()
            clauses.append({
                "clause_index": idx + 1,
                "heading": heading,
                "category": classify_clause(heading, chunk_txt),
                "text": chunk_txt[:3000],
            })
    else:
        for p in pages:
            if p["text"].strip():
                clauses.append({
                    "clause_index": p["page"],
                    "heading": f"Page {p['page']}",
                    "category": classify_clause("", p["text"]),
                    "text": p["text"][:3000],
                })

    tables = [
        {"page": p["page"], "rows": tbl}
        for p in pages
        for tbl in p.get("tables", [])
    ]

    return {
        "doc_id": record["doc_id"],
        "matter_id": record["matter_id"],
        "doc_type": "contract",
        "filename": record["filename"],
        "source": record["source"],
        "parties": parties,
        "governing_law": governing_law,
        "clause_count": len(clauses),
        "table_count": len(tables),
        "clauses": clauses,
        "tables": tables,
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    statutes_out, judgments_out, contracts_out, urdu_out = [], [], [], []

    with PARSED_JSONL.open("r", encoding="utf-8") as fin:
        for line in fin:
            rec = json.loads(line)
            dtype = rec["type"]
            if dtype == "statute":
                statutes_out.append(extract_statute(rec))
            elif dtype == "judgment":
                judgments_out.append(extract_judgment(rec))
            elif dtype == "contract":
                contracts_out.append(extract_contract(rec))
            else:
                urdu_out.append(extract_statute(rec))

    (OUT_DIR / "statutes.json").write_text(json.dumps(statutes_out, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT_DIR / "judgments.json").write_text(json.dumps(judgments_out, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT_DIR / "contracts.json").write_text(json.dumps(contracts_out, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT_DIR / "urdu_docs.json").write_text(json.dumps(urdu_out, ensure_ascii=False, indent=2), encoding="utf-8")

    print(
        f"Structured JSON saved in {OUT_DIR}:\n"
        f"  statutes.json:  {len(statutes_out)} acts ({sum(s['section_count'] for s in statutes_out)} sections)\n"
        f"  judgments.json: {len(judgments_out)} judgments\n"
        f"  contracts.json: {len(contracts_out)} contracts ({sum(c['clause_count'] for c in contracts_out)} clauses, {sum(c['table_count'] for c in contracts_out)} tables)\n"
        f"  urdu_docs.json: {len(urdu_out)} Urdu documents"
    )


if __name__ == "__main__":
    main()

