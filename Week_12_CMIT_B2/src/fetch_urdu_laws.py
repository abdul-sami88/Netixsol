"""Download 20 concise Urdu Pakistani statutes from user-provided Pakistan Code URLs."""

from pathlib import Path
import requests
import pymupdf
import truststore

truststore.inject_into_ssl()

OUT_DIR = Path("data_sources/scanned_urdu")

URDU_LAWS = [
    ("limitation_act_1908_urdu.pdf", "https://pakistancode.gov.pk/pdffiles/administratorcurdua7f4f2b3b5b93d09a4aa78gh.pdf"),
    ("dissolution_muslim_marriages_1939_urdu.pdf", "https://pakistancode.gov.pk/pdffiles/administratorcurdua7f4f2b3b5b93d09a4aa20kl.pdf"),
    ("child_marriage_restraint_1929_urdu.pdf", "https://pakistancode.gov.pk/pdffiles/administratorcurdua7f4f2b3b5b93d09a4aa121mn.pdf"),
    ("lawyers_welfare_protection_2023_urdu.pdf", "https://pakistancode.gov.pk/pdffiles/administratorcurdu7f4f2b3b5b93d09a4aa5454.pdf"),
    ("commercial_dispute_resolution_2022_urdu.pdf", "https://pakistancode.gov.pk/pdffiles/administratorcurdua7f4f2b3b5b93d09a4aa6045.pdf"),
    ("sc_review_judgments_2023_urdu.pdf", "https://pakistancode.gov.pk/pdffiles/administratorcurdua7f4f2b3b5b93d09a4aa6746.pdf"),
    ("sc_practice_procedure_2023_urdu.pdf", "https://pakistancode.gov.pk/pdffiles/administratorcurdua7f4f2b3b5b93d09a4aa6923.pdf"),
    ("control_narcotic_substances_1997_urdu.pdf", "https://pakistancode.gov.pk/pdffiles/administratorcurdua7f4f2b3b5b93d09a4aa3802.pdf"),
    ("prohibition_private_interest_2023_urdu.pdf", "https://pakistancode.gov.pk/pdffiles/administratorcurdua7f4f2b3b5b93d09a4aa8305.pdf"),
    ("illegal_dispossession_2005_urdu.pdf", "https://pakistancode.gov.pk/pdffiles/administratorcurdua7f4f2b3b5b93d09a4aa6846.pdf"),
    ("right_access_information_2017_urdu.pdf", "https://pakistancode.gov.pk/pdffiles/administratorcurdua7f4f2b3b5b93d09a4aa0567.pdf"),
    ("workplace_harassment_2010_urdu.pdf", "https://pakistancode.gov.pk/pdffiles/administratorcurdua7f4f2b3b5b93d09a4aa6757.pdf"),
    ("investigation_fair_trial_2013_urdu.pdf", "https://pakistancode.gov.pk/pdffiles/administratorcurdua7f4f2b3b5b93d09a4aa5683.pdf"),
    ("maternity_paternity_leave_2023_urdu.pdf", "https://pakistancode.gov.pk/pdffiles/administratorcurdua7f4f2b3b5b93d09a4aa9790.pdf"),
    ("women_property_rights_2020_urdu.pdf", "https://pakistancode.gov.pk/pdffiles/administratorcurdua7f4f2b3b5b93d09a4aa4789.pdf"),
    ("gas_theft_recovery_2014_urdu.pdf", "https://pakistancode.gov.pk/pdffiles/administratorcurdua7f4f2b3b5b93d09a4edf544.pdf"),
    ("offence_of_qazf_1979_urdu.pdf", "https://pakistancode.gov.pk/pdffiles/administratorcurdua7f4f2b3b5b93d09a4jkd787.pdf"),
    ("adr_act_2017_urdu.pdf", "https://pakistancode.gov.pk/pdffiles/administratorcurdua7f4f2b3b5b93d04sfsr0.pdf"),
    ("transfer_of_property_1882_urdu.pdf", "https://pakistancode.gov.pk/pdffiles/administratorcurdua7f4f2b3b5b93d04f0033.pdf"),
    ("family_courts_act_1964_urdu.pdf", "https://pakistancode.gov.pk/pdffiles/administratorcurdua7f4f2b3b5b93d04f7800.pdf"),
]


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    headers = {"User-Agent": "Mozilla/5.0"}
    downloaded = 0

    for fname, url in URDU_LAWS:
        dest = OUT_DIR / fname
        if dest.exists() and dest.stat().st_size > 1000:
            print(f"[SKIP] {fname} already exists")
        else:
            try:
                resp = requests.get(url, headers=headers, timeout=30)
                resp.raise_for_status()
                dest.write_bytes(resp.content)
                downloaded += 1
            except Exception as exc:
                print(f"[FAIL] {fname}: {exc}")
                continue

        try:
            doc = pymupdf.open(dest)
            pages = len(doc)
            sample_n = min(pages, 3)
            chars = sum(len(doc[i].get_text("text").strip()) for i in range(sample_n))
            avg_chars = chars / sample_n if sample_n else 0
            kind = "SCANNED" if avg_chars < 50 else "DIGITAL"
            doc.close()
            print(f"[OK] {fname:<44} | {pages:>3} pages | avg {avg_chars:>6.1f} chars/p | {kind}")
        except Exception as exc:
            print(f"[BAD PDF] {fname}: {exc}")

    print(f"\nNewly downloaded: {downloaded} | Total in {OUT_DIR}: {len(list(OUT_DIR.glob('*.pdf')))}")


if __name__ == "__main__":
    main()
