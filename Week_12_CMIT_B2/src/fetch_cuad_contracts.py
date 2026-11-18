"""Download 30 diverse real CUAD contract PDFs from Hugging Face (`theatticusproject/cuad`)."""

from collections import defaultdict
from pathlib import Path
import shutil
from huggingface_hub import HfApi, hf_hub_download
import pymupdf


REPO_ID = "theatticusproject/cuad"
OUT_DIR = Path("data_sources/contracts/cuad")
TARGET_COUNT = 30


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    existing = list(OUT_DIR.glob("*.pdf"))
    if len(existing) >= TARGET_COUNT:
        print(f"Already have {len(existing)} CUAD PDFs in {OUT_DIR}")
        return

    print("Listing CUAD PDF files on Hugging Face Hub...")
    api = HfApi()
    all_files = api.list_repo_files(REPO_ID, repo_type="dataset")
    pdf_files = [
        f for f in all_files
        if f.startswith("CUAD_v1/full_contract_pdf/") and f.lower().endswith(".pdf")
    ]
    print(f"Found {len(pdf_files)} CUAD contract PDFs.")

    # Group by contract category folder (e.g. Affiliate_Agreements, Co_Branding, License_Agreements)
    by_category: dict[str, list[str]] = defaultdict(list)
    for f in sorted(pdf_files):
        parts = f.split("/")
        category = parts[-2] if len(parts) >= 2 else "other"
        by_category[category].append(f)

    # Round-robin across categories for maximum contract-type diversity
    ordered_candidates: list[str] = []
    idx = 0
    categories = sorted(by_category.keys())
    while len(ordered_candidates) < len(pdf_files):
        added = False
        for cat in categories:
            if idx < len(by_category[cat]):
                ordered_candidates.append(by_category[cat][idx])
                added = True
        if not added:
            break
        idx += 1

    saved = 0
    for repo_path in ordered_candidates:
        if saved >= TARGET_COUNT:
            break
        fname = Path(repo_path).name
        dest = OUT_DIR / fname
        if dest.exists() and dest.stat().st_size > 1000:
            saved += 1
            continue
        try:
            local_cached = hf_hub_download(
                repo_id=REPO_ID,
                filename=repo_path,
                repo_type="dataset",
            )
            shutil.copy2(local_cached, dest)
            doc = pymupdf.open(dest)
            pages = len(doc)
            chars = sum(len(doc[i].get_text("text").strip()) for i in range(min(pages, 3)))
            doc.close()
            if pages == 0:
                dest.unlink(missing_ok=True)
                continue
            saved += 1
            kind = "SCANNED" if (chars / min(pages, 3)) < 50 else "DIGITAL"
            print(f"  [{saved:02d}/{TARGET_COUNT}] {fname[:60]:<60} | {pages:>2}p | {kind}")
        except Exception as exc:
            print(f"  [SKIP] {fname}: {exc}")

    print(f"Saved {saved} diverse CUAD contract PDFs to {OUT_DIR}")


if __name__ == "__main__":
    main()
