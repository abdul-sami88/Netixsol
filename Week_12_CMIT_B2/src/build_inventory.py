"""Build the complete corpus inventory (`outputs/inventory.csv`) for Khan & Associates."""

from pathlib import Path
import re
import pandas as pd
import pymupdf


DATA_ROOT = Path("data_sources")
OUT_CSV = Path("outputs/inventory.csv")

URDU_UNICODE_RE = re.compile(r"[\u0600-\u06FF]")
ASCII_WORD_RE = re.compile(r"[A-Za-z]{2,}")


def classify_pdf_mode(path: Path, expected_lang: str) -> tuple[int, str]:
    """Return (page_count, extraction_mode) by inspecting sampled pages."""
    doc = pymupdf.open(path)
    pages = len(doc)
    sample_n = min(pages, 3)
    texts = [doc[i].get_text("text").strip() for i in range(sample_n)]
    doc.close()

    joined = "\n".join(texts)
    avg_chars = sum(len(t) for t in texts) / sample_n if sample_n else 0
    if avg_chars < 50:
        return pages, "scanned_ocr"

    if expected_lang == "ur":
        urdu_hits = len(URDU_UNICODE_RE.findall(joined))
        if urdu_hits < 10:
            # Legacy InPage / PUA glyph encoding extracts gibberish -> route to OCR
            return pages, "legacy_encoding_ocr"
    else:
        ascii_words = len(ASCII_WORD_RE.findall(joined))
        if ascii_words < 5:
            return pages, "scanned_ocr"

    return pages, "digital"


def build_rows() -> list[dict]:
    rows: list[dict] = []

    # 1. Statutes (English)
    for idx, pdf in enumerate(sorted((DATA_ROOT / "statutes").glob("*.pdf")), 1):
        pages, mode = classify_pdf_mode(pdf, "en")
        rows.append({
            "doc_id": f"stat_{idx:03d}",
            "matter_id": f"KA-STAT-{idx:03d}",
            "filename": pdf.name,
            "rel_path": pdf.as_posix(),
            "type": "statute",
            "language": "en",
            "pages": pages,
            "extraction_mode": mode,
            "source": "Pakistan Code (EN)",
        })

    # 2. Judgments (200 sample)
    judg_pdfs = sorted((DATA_ROOT / "judgments_sample").rglob("*.pdf"))
    for idx, pdf in enumerate(judg_pdfs, 1):
        pages, mode = classify_pdf_mode(pdf, "en")
        rows.append({
            "doc_id": f"judg_{idx:03d}",
            "matter_id": f"KA-JUDG-{idx:03d}",
            "filename": pdf.name,
            "rel_path": pdf.as_posix(),
            "type": "judgment",
            "language": "en",
            "pages": pages,
            "extraction_mode": mode,
            "source": f"Supreme Court of Pakistan ({pdf.parent.name})",
        })

    # 3. Contracts (30 CUAD + 20 Synthetic)
    cuad_pdfs = sorted((DATA_ROOT / "contracts/cuad").glob("*.pdf"))
    for idx, pdf in enumerate(cuad_pdfs, 1):
        pages, mode = classify_pdf_mode(pdf, "en")
        rows.append({
            "doc_id": f"cont_{idx:03d}",
            "matter_id": f"KA-CONT-{idx:03d}",
            "filename": pdf.name,
            "rel_path": pdf.as_posix(),
            "type": "contract",
            "language": "en",
            "pages": pages,
            "extraction_mode": mode,
            "source": "CUAD (Atticus Project)",
        })

    synth_pdfs = sorted((DATA_ROOT / "contracts/synthetic").glob("*.pdf"))
    for idx, pdf in enumerate(synth_pdfs, len(cuad_pdfs) + 1):
        pages, mode = classify_pdf_mode(pdf, "en")
        rows.append({
            "doc_id": f"cont_{idx:03d}",
            "matter_id": f"KA-CONT-{idx:03d}",
            "filename": pdf.name,
            "rel_path": pdf.as_posix(),
            "type": "contract",
            "language": "en",
            "pages": pages,
            "extraction_mode": mode,
            "source": "Synthetic (PK Law)",
        })

    # 4. Scanned / Urdu docs (30 total)
    urdu_pdfs = sorted((DATA_ROOT / "scanned_urdu").glob("*.pdf"))
    for idx, pdf in enumerate(urdu_pdfs, 1):
        pages, mode = classify_pdf_mode(pdf, "ur")
        src = (
            "Synthetic Scanned Legal (UR)"
            if pdf.name.endswith("_scanned.pdf")
            else "Pakistan Code (UR)"
        )
        rows.append({
            "doc_id": f"urdu_{idx:03d}",
            "matter_id": f"KA-URDU-{idx:03d}",
            "filename": pdf.name,
            "rel_path": pdf.as_posix(),
            "type": "scanned_urdu",
            "language": "ur",
            "pages": pages,
            "extraction_mode": mode,
            "source": src,
        })

    return rows


def main() -> None:
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    rows = build_rows()
    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")

    print(f"Saved inventory to {OUT_CSV} ({len(df)} total documents, {df['pages'].sum()} total pages)\n")
    print("=== SUMMARY BY TYPE & EXTRACTION MODE ===")
    summary = df.groupby(["type", "language", "extraction_mode"]).agg(
        docs=("doc_id", "count"),
        pages=("pages", "sum"),
    )
    print(summary.to_string())


if __name__ == "__main__":
    main()

