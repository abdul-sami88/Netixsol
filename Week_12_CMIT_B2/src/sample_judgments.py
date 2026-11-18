"""Select a stratified, diverse sample of 200 Supreme Court judgments."""

from collections import defaultdict
from pathlib import Path
import re
import shutil
import pymupdf


SOURCE_DIR = Path("data_sources/Supreme Court Judgements")
TARGET_DIR = Path("data_sources/judgments_sample")
TARGET_COUNT = 200


def parse_case_key(filename: str) -> tuple[str, int]:
    """Extract normalized case type prefix and year from a judgment filename."""
    stem = Path(filename).stem.lower()
    prefix_match = re.match(r"^([a-z]+(?:\.[a-z]+)*)", stem)
    prefix = prefix_match.group(1) if prefix_match else "other"
    year_match = re.search(r"(19\d{2}|20\d{2})", stem)
    year = int(year_match.group(1)) if year_match else 0
    return prefix, year


def is_valid_pdf(path: Path) -> tuple[bool, int, bool]:
    """Check if PDF opens cleanly; return (valid, pages, likely_scanned)."""
    try:
        doc = pymupdf.open(path)
        pages = len(doc)
        if pages == 0:
            doc.close()
            return False, 0, False
        sample_n = min(pages, 3)
        chars = sum(len(doc[i].get_text("text").strip()) for i in range(sample_n))
        doc.close()
        return True, pages, (chars / sample_n) < 50
    except Exception:
        return False, 0, False


def stratified_pick(files: list[Path]) -> list[Path]:
    """Return files ordered for even spread across case types and years."""
    by_type: dict[str, list[tuple[int, str, Path]]] = defaultdict(list)
    for f in files:
        prefix, year = parse_case_key(f.name)
        by_type[prefix].append((year, f.name, f))

    buckets = []
    for prefix in sorted(by_type.keys()):
        sorted_items = [item[2] for item in sorted(by_type[prefix], key=lambda x: (x[0], x[1]))]
        buckets.append(sorted_items)

    # Round-robin across case types, picking evenly spaced elements from each bucket
    picked: list[Path] = []
    bucket_indices = [0] * len(buckets)
    while len(picked) < len(files):
        added_this_round = False
        for idx, bucket in enumerate(buckets):
            if len(picked) >= len(files):
                break
            if bucket_indices[idx] < len(bucket):
                picked.append(bucket[bucket_indices[idx]])
                bucket_indices[idx] += 1
                added_this_round = True
        if not added_this_round:
            break
    return picked


def main() -> None:
    if not SOURCE_DIR.exists():
        raise FileNotFoundError(f"Source directory not found: {SOURCE_DIR}")

    if TARGET_DIR.exists():
        shutil.rmtree(TARGET_DIR)
    TARGET_DIR.mkdir(parents=True, exist_ok=True)

    judge_dirs = sorted([d for d in SOURCE_DIR.iterdir() if d.is_dir()])
    judge_files: dict[str, list[Path]] = {}
    for jdir in judge_dirs:
        pdfs = sorted(jdir.glob("*.pdf"))
        if pdfs:
            judge_files[jdir.name] = pdfs

    total_available = sum(len(v) for v in judge_files.values())
    print(f"Found {total_available} PDFs across {len(judge_files)} Justice folders.")

    # Compute quotas: guarantee at least 1 per Justice, remaining proportional
    quotas: dict[str, int] = {j: 1 for j in judge_files}
    remaining = TARGET_COUNT - len(quotas)

    # Largest-remainder allocation for the remaining slots
    raw_extra = {
        j: (len(files) - 1) / max(1, total_available - len(quotas)) * remaining
        for j, files in judge_files.items()
    }
    for j in quotas:
        add = min(len(judge_files[j]) - 1, int(raw_extra[j]))
        quotas[j] += add

    deficit = TARGET_COUNT - sum(quotas.values())
    if deficit > 0:
        remainders = sorted(
            judge_files.keys(),
            key=lambda j: raw_extra[j] - int(raw_extra[j]),
            reverse=True,
        )
        for j in remainders:
            if deficit == 0:
                break
            if quotas[j] < len(judge_files[j]):
                quotas[j] += 1
                deficit -= 1

    selected: list[tuple[str, Path, int, bool]] = []
    for j, files in judge_files.items():
        candidates = stratified_pick(files)
        picked_for_j = 0
        for pdf in candidates:
            if picked_for_j >= quotas[j]:
                break
            ok, pages, scanned = is_valid_pdf(pdf)
            if ok:
                dest_dir = TARGET_DIR / j
                dest_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(pdf, dest_dir / pdf.name)
                selected.append((j, pdf, pages, scanned))
                picked_for_j += 1

    total_bytes = sum((TARGET_DIR / j / p.name).stat().st_size for j, p, _, _ in selected)
    total_pages = sum(pages for _, _, pages, _ in selected)
    scanned_cnt = sum(1 for _, _, _, s in selected if s)
    case_types = defaultdict(int)
    for _, p, _, _ in selected:
        prefix, _ = parse_case_key(p.name)
        case_types[prefix] += 1

    print(f"Copied {len(selected)} judgments to {TARGET_DIR}")
    print(f"Total size: {total_bytes / (1024 * 1024):.2f} MB | Total pages: {total_pages} | Likely scanned: {scanned_cnt}")
    print("Top case types:", dict(sorted(case_types.items(), key=lambda x: -x[1])[:10]))
    print("Justices represented:", len({j for j, _, _, _ in selected}))


if __name__ == "__main__":
    main()
