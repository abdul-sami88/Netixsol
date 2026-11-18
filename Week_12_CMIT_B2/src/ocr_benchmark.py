"""Task 2: Benchmark 2 OCR tools (EasyOCR vs Tesseract) on 10 Urdu pages using CER."""

import os
from pathlib import Path
import re
import time
import unicodedata
import easyocr
from jiwer import cer
import pandas as pd
import pytesseract
from PIL import Image


BENCHMARK_DIR = Path("data_sources/ocr_benchmark")
OUT_CSV = Path("outputs/ocr_comparison.csv")
OUT_MD = Path("reports/ocr_comparison.md")


def find_tesseract() -> str | None:
    """Locate tesseract.exe on PATH or standard Windows install folders."""
    candidates = [
        "tesseract",
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
    ]
    for cmd in candidates:
        if cmd == "tesseract":
            from shutil import which
            found = which("tesseract")
            if found:
                return found
        elif Path(cmd).exists():
            return cmd
    return None


def normalize_urdu(text: str) -> str:
    """Normalize Arabic/Urdu Unicode variants and whitespace for fair CER calculation."""
    text = unicodedata.normalize("NFKC", text)
    replacements = {
        "\u064a": "\u06cc",  # Arabic Yeh -> Urdu Yeh
        "\u0643": "\u06a9",  # Arabic Kaf -> Urdu Keheh
        "\u06c0": "\u06c1",  # Heh with Yeh above -> Heh Goal
        "\u0629": "\u06c3",  # Teh Marbuta
        "\u200c": "",        # Zero-width non-joiner
        "\u200d": "",        # Zero-width joiner
        "\u200e": "",
        "\u200f": "",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def run_benchmark() -> None:
    pngs = sorted(BENCHMARK_DIR.glob("*.png"))[:10]
    if not pngs:
        raise FileNotFoundError(f"No PNG benchmark pages found in {BENCHMARK_DIR}")

    tess_path = find_tesseract()
    tess_ready = False
    if tess_path:
        pytesseract.pytesseract.tesseract_cmd = tess_path
        try:
            langs = pytesseract.get_languages(config="")
            tess_ready = "urd" in langs
            if not tess_ready:
                print(f"[WARN] Tesseract found at {tess_path}, but 'urd' traineddata is missing (langs={langs}).")
        except Exception as exc:
            print(f"[WARN] Tesseract found at {tess_path} but failed check: {exc}")
    else:
        print("[WARN] Tesseract executable not found. Install via: winget install --id=UB-Mannheim.TesseractOCR -e")

    print("Loading EasyOCR Urdu reader (CPU)...")
    reader = easyocr.Reader(["ur"], gpu=False, verbose=False)

    rows = []
    for png in pngs:
        gt_file = png.with_suffix(".txt")
        gt_raw = gt_file.read_text(encoding="utf-8")
        gt_norm = normalize_urdu(gt_raw)

        # Tool 1: EasyOCR
        t0 = time.perf_counter()
        easy_lines = reader.readtext(str(png), detail=0, paragraph=True)
        easy_time = time.perf_counter() - t0
        easy_text = normalize_urdu(" ".join(easy_lines))
        easy_cer = cer(gt_norm, easy_text)

        # Tool 2: Tesseract (if installed with urd)
        tess_text = ""
        tess_cer = None
        tess_time = None
        if tess_ready:
            t1 = time.perf_counter()
            img = Image.open(png)
            tess_raw = pytesseract.image_to_string(img, lang="urd")
            tess_time = round(time.perf_counter() - t1, 2)
            tess_text = normalize_urdu(tess_raw)
            tess_cer = round(cer(gt_norm, tess_text), 4)

        rows.append({
            "page": png.stem,
            "gt_chars": len(gt_norm),
            "easyocr_cer": round(easy_cer, 4),
            "easyocr_sec": round(easy_time, 2),
            "tesseract_cer": tess_cer,
            "tesseract_sec": tess_time,
            "easyocr_sample": easy_text[:80],
            "tesseract_sample": tess_text[:80],
        })
        print(
            f"  {png.stem:<32} | EasyOCR CER={easy_cer:.4f} ({easy_time:.1f}s)"
            + (f" | Tesseract CER={tess_cer:.4f} ({tess_time:.1f}s)" if tess_ready else "")
        )

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")

    avg_easy_cer = df["easyocr_cer"].mean()
    avg_easy_sec = df["easyocr_sec"].mean()

    md_lines = [
        "# Urdu OCR Benchmark (10 Legal Pages, CER)",
        "",
        "Character Error Rate (CER) computed after Unicode NFKC & Urdu character normalization (`jiwer.cer`). Lower is better.",
        "",
        "## Aggregate Results",
        "",
        "| OCR Tool | Language Pack | Pages | Avg CER | Avg Time / Page |",
        "| :--- | :--- | ---: | ---: | ---: |",
        f"| **EasyOCR** | `ur` (CPU) | {len(df)} | {avg_easy_cer:.4f} | {avg_easy_sec:.2f}s |",
    ]
    if tess_ready:
        md_lines.append(
            f"| **Tesseract OCR** | `urd` (LSTM) | {len(df)} | {df['tesseract_cer'].mean():.4f} | {df['tesseract_sec'].mean():.2f}s |"
        )
    else:
        md_lines.append("| **Tesseract OCR** | `urd` | — | *Pending Tesseract + urd.traineddata install* | — |")

    md_lines.extend(["", "## Per-Page Breakdown", "", df[["page", "gt_chars", "easyocr_cer", "easyocr_sec", "tesseract_cer", "tesseract_sec"]].to_markdown(index=False)])
    OUT_MD.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"\nSaved OCR results to {OUT_CSV} and {OUT_MD}")


if __name__ == "__main__":
    run_benchmark()

