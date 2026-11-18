"""Inspect existing PDFs in data_sources/ for page counts and digital vs. scanned status."""

from pathlib import Path
import pymupdf


def inspect_pdf(path: Path, sample_pages: int = 5) -> dict:
    """Return page count and whether sampled pages contain extractable digital text."""
    try:
        doc = pymupdf.open(path)
        num_pages = len(doc)
        check_n = min(num_pages, sample_pages)
        text_chars = sum(len(doc[i].get_text("text").strip()) for i in range(check_n))
        avg_chars = text_chars / check_n if check_n else 0
        doc.close()
        return {
            "path": str(path),
            "pages": num_pages,
            "avg_chars_sampled": round(avg_chars, 1),
            "likely_scanned": avg_chars < 50,
            "error": None,
        }
    except Exception as exc:
        return {
            "path": str(path),
            "pages": 0,
            "avg_chars_sampled": 0,
            "likely_scanned": None,
            "error": str(exc),
        }


def main() -> None:
    root = Path("data_sources")
    statutes_dir = root / "statutes"
    judgments_dir = root / "Supreme Court Judgements"

    print("=== STATUTES ===")
    if statutes_dir.exists():
        total_pages = 0
        for pdf in sorted(statutes_dir.glob("*.pdf")):
            info = inspect_pdf(pdf, sample_pages=10)
            total_pages += info["pages"]
            kind = "SCANNED" if info["likely_scanned"] else "DIGITAL"
            print(
                f"  {pdf.name:<38} | {info['pages']:>4} pages | "
                f"avg {info['avg_chars_sampled']:>6} chars/page | {kind}"
            )
        print(f"Total statute pages: {total_pages}")

    print("\n=== JUDGMENTS (SAMPLE OF 30 ACROSS FOLDERS) ===")
    if judgments_dir.exists():
        pdfs = sorted(judgments_dir.rglob("*.pdf"))
        print(f"Total judgment PDFs found: {len(pdfs)}")
        step = max(1, len(pdfs) // 30)
        sampled = pdfs[::step][:30]
        scanned_count = 0
        errors = 0
        pages_list = []
        for pdf in sampled:
            info = inspect_pdf(pdf, sample_pages=3)
            if info["error"]:
                errors += 1
            else:
                pages_list.append(info["pages"])
                if info["likely_scanned"]:
                    scanned_count += 1
        avg_p = round(sum(pages_list) / len(pages_list), 1) if pages_list else 0
        print(
            f"Sampled {len(sampled)} judgments: avg {avg_p} pages, "
            f"{scanned_count} likely scanned, {errors} errors"
        )


if __name__ == "__main__":
    main()

