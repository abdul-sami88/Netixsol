"""Task 2: Parse digital PDFs (PyMuPDF + pdfplumber tables) and OCR scanned/legacy PDFs."""

import argparse
from pathlib import Path
import shutil
import pandas as pd
import pdfplumber
import pymupdf
import pytesseract
from PIL import Image
from tqdm import tqdm


INVENTORY_CSV = Path("outputs/inventory.csv")
OUT_JSONL = Path("outputs/parsed_docs.jsonl")


def find_tesseract() -> str | None:
    """Locate tesseract.exe on PATH or standard Windows install directories."""
    for candidate in (
        "tesseract",
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ):
        if candidate == "tesseract":
            found = shutil.which("tesseract")
            if found:
                return found
        elif Path(candidate).exists():
            return candidate
    return None


def extract_digital_pages(pdf_path: Path, extract_tables: bool = True) -> tuple[list[dict], int]:
    """Extract text via PyMuPDF and tables via pdfplumber."""
    pages_out: list[dict] = []
    table_count = 0

    doc = pymupdf.open(pdf_path)
    plumber_doc = pdfplumber.open(pdf_path) if extract_tables else None
    try:
        for i in range(len(doc)):
            text = doc[i].get_text("text").strip()
            tables: list[list[list[str]]] = []
            if plumber_doc is not None:
                try:
                    raw_tables = plumber_doc.pages[i].extract_tables() or []
                    for tbl in raw_tables:
                        cleaned = [[(cell or "").strip() for cell in row] for row in tbl]
                        if cleaned:
                            tables.append(cleaned)
                    table_count += len(tables)
                except Exception:
                    pass
            pages_out.append({
                "page": i + 1,
                "text": text,
                "tables": tables,
                "method": "pymupdf+pdfplumber" if tables else "pymupdf",
            })
    finally:
        doc.close()
        if plumber_doc is not None:
            plumber_doc.close()

    return pages_out, table_count


def ocr_pdf_pages(
    pdf_path: Path,
    lang: str,
    max_pages: int,
    tess_cmd: str | None,
    easy_readers: dict,
) -> list[dict]:
    """Render PDF pages at 150 DPI and OCR using Tesseract (preferred for speed) or EasyOCR."""
    doc = pymupdf.open(pdf_path)
    pages_out: list[dict] = []
    limit = min(len(doc), max_pages) if max_pages > 0 else len(doc)

    tess_lang = "urd" if lang == "ur" else "eng"
    use_tess = False
    if tess_cmd:
        pytesseract.pytesseract.tesseract_cmd = tess_cmd
        try:
            avail = pytesseract.get_languages(config="")
            use_tess = tess_lang in avail
        except Exception:
            use_tess = False

    try:
        for i in range(limit):
            pix = doc[i].get_pixmap(dpi=150, colorspace=pymupdf.csGRAY)
            img = Image.frombytes("L", [pix.width, pix.height], pix.samples)

            if use_tess:
                text = pytesseract.image_to_string(img, lang=tess_lang).strip()
                method = f"tesseract_{tess_lang}"
            else:
                import easyocr
                import numpy as np

                reader_key = "ur" if lang == "ur" else "en"
                if reader_key not in easy_readers:
                    easy_readers[reader_key] = easyocr.Reader([reader_key], gpu=False, verbose=False)
                lines = easy_readers[reader_key].readtext(np.array(img), detail=0, paragraph=True)
                text = "\n".join(lines).strip()
                method = f"easyocr_{reader_key}"

            pages_out.append({
                "page": i + 1,
                "text": text,
                "tables": [],
                "method": method,
            })
    finally:
        doc.close()

    return pages_out


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse digital and scanned legal PDFs.")
    parser.add_argument("--max-ocr-pages", type=int, default=3, help="Max OCR pages per scanned PDF (0 = all).")
    parser.add_argument("--no-tables", action="store_true", help="Skip pdfplumber table extraction.")
    args = parser.parse_args()

    df = pd.read_csv(INVENTORY_CSV)
    tess_cmd = find_tesseract()
    easy_readers: dict = {}

    OUT_JSONL.parent.mkdir(parents=True, exist_ok=True)
    total_tables = 0
    import json

    with OUT_JSONL.open("w", encoding="utf-8") as fout:
        for row in tqdm(df.to_dict(orient="records"), desc="Parsing corpus"):
            pdf_path = Path(row["rel_path"])
            mode = row["extraction_mode"]
            if mode == "digital":
                # Run pdfplumber table extraction on contracts (contains Schedule A tables) & short statutes
                do_tables = (not args.no_tables) and (row["type"] == "contract" or row["pages"] <= 60)
                pages, tcount = extract_digital_pages(pdf_path, extract_tables=do_tables)
                total_tables += tcount
            else:
                pages = ocr_pdf_pages(
                    pdf_path,
                    lang=row["language"],
                    max_pages=args.max_ocr_pages,
                    tess_cmd=tess_cmd,
                    easy_readers=easy_readers,
                )

            record = {
                "doc_id": row["doc_id"],
                "matter_id": row["matter_id"],
                "filename": row["filename"],
                "type": row["type"],
                "language": row["language"],
                "source": row["source"],
                "extraction_mode": mode,
                "total_pages": int(row["pages"]),
                "parsed_pages": len(pages),
                "pages": pages,
            }
            fout.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Saved parsed corpus to {OUT_JSONL} | Extracted {total_tables} tables across digital docs.")


if __name__ == "__main__":
    main()

