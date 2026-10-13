"""
Generates 30 Authentic-Looking Diagnostic Lab Report Images & Ground Truth JSON
Panels covered:
- Complete Blood Count (CBC) - 8 reports
- Liver Function Tests (LFT) - 7 reports
- Lipid Profile - 5 reports
- Glycated Hemoglobin (HbA1c) & Glucose - 5 reports
- Renal Function Tests (KFT / RFT) - 5 reports

Saved to: data/synthetic_lab_reports/
"""

import os
import json
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "data" / "synthetic_lab_reports"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

random.seed(101)

PATIENT_NAMES = [
    ("Muhammad Bilal", 34, "Male"),
    ("Fatima Tariq", 28, "Female"),
    ("Usman Ghani", 52, "Male"),
    ("Zainab Bibi", 45, "Female"),
    ("Ahmad Raza", 61, "Male"),
    ("Ayesha Siddiqa", 22, "Female"),
    ("Hamza Ali", 38, "Male"),
    ("Sana Malik", 31, "Female"),
    ("Tariq Mahmood", 58, "Male"),
    ("Hira Farooq", 19, "Female"),
    ("Bilal Aslam", 47, "Male"),
    ("Rabia Zafar", 36, "Female"),
    ("Kashif Munir", 50, "Male"),
    ("Maryam Noor", 29, "Female"),
    ("Imran Khan", 42, "Male"),
    ("Sadia Bashir", 39, "Female"),
    ("Waqas Cheema", 27, "Male"),
    ("Bushra Rehman", 64, "Female"),
    ("Haris Nadeem", 33, "Male"),
    ("Nadia Afzal", 41, "Female"),
    ("Zainab Bokhari", 55, "Female"),
    ("Faisal Munir", 48, "Male"),
    ("Mahnoor Javed", 24, "Female"),
    ("Omer Farooq", 53, "Male"),
    ("Farzana Malik", 62, "Female"),
    ("Shazia Parveen", 37, "Female"),
    ("Asim Jamil", 44, "Male"),
    ("Shahzad Rasheed", 60, "Male"),
    ("Kamran Qureshi", 51, "Male"),
    ("Sara Malik", 30, "Female")
]

DOCTORS = [
    "Dr. Ahmad Khan (General Medicine)",
    "Dr. Ayesha Siddiqa (Internal Medicine)",
    "Dr. Kamran Qureshi (Cardiology)",
    "Dr. Farzana Malik (Gynaecology)",
    "Dr. Fatima Zahra (Paediatrics)"
]

PANELS = [
    # 8 CBC Reports
    {
        "panel_name": "Complete Blood Count (CBC)",
        "tests": [
            ("Hemoglobin", 12.0, 16.0, "g/dL", "12.0 - 16.0"),
            ("RBC Count", 4.0, 5.5, "mil/uL", "4.0 - 5.5"),
            ("WBC Count", 4000, 11000, "/uL", "4000 - 11000"),
            ("Platelet Count", 150000, 450000, "/mcL", "150000 - 450000"),
            ("Hematocrit (PCV)", 36.0, 48.0, "%", "36.0 - 48.0")
        ]
    },
    # 7 LFT Reports
    {
        "panel_name": "Liver Function Tests (LFT)",
        "tests": [
            ("Total Bilirubin", 0.2, 1.2, "mg/dL", "0.2 - 1.2"),
            ("ALT (SGPT)", 10.0, 40.0, "U/L", "10.0 - 40.0"),
            ("AST (SGOT)", 10.0, 35.0, "U/L", "10.0 - 35.0"),
            ("Alkaline Phosphatase (ALP)", 44.0, 147.0, "U/L", "44.0 - 147.0"),
            ("Serum Albumin", 3.5, 5.0, "g/dL", "3.5 - 5.0")
        ]
    },
    # 5 Lipid Reports
    {
        "panel_name": "Lipid Profile",
        "tests": [
            ("Total Cholesterol", 120.0, 200.0, "mg/dL", "< 200.0"),
            ("Triglycerides", 50.0, 150.0, "mg/dL", "< 150.0"),
            ("HDL Cholesterol", 40.0, 60.0, "mg/dL", "> 40.0"),
            ("LDL Cholesterol", 60.0, 100.0, "mg/dL", "< 100.0")
        ]
    },
    # 5 HbA1c Reports
    {
        "panel_name": "Glycemic Assessment (HbA1c & Glucose)",
        "tests": [
            ("Fasting Blood Sugar", 70.0, 100.0, "mg/dL", "70.0 - 100.0"),
            ("HbA1c (Glycated Hemoglobin)", 4.0, 5.6, "%", "4.0 - 5.6"),
            ("Estimated Average Glucose", 70.0, 115.0, "mg/dL", "70.0 - 115.0")
        ]
    },
    # 5 Renal Reports
    {
        "panel_name": "Renal Function Tests (RFT / KFT)",
        "tests": [
            ("Serum Creatinine", 0.6, 1.2, "mg/dL", "0.6 - 1.2"),
            ("Blood Urea Nitrogen", 7.0, 20.0, "mg/dL", "7.0 - 20.0"),
            ("Serum Uric Acid", 3.5, 7.2, "mg/dL", "3.5 - 7.2")
        ]
    }
]


def render_report_image(report_meta: dict, file_path: Path):
    """Draws a clean, realistic clinical lab report on a crisp canvas."""
    width, height = 800, 750
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Header Banner
    draw.rectangle([(0, 0), (width, 85)], fill=(20, 65, 120))
    draw.text((25, 18), "CITY CARE DIAGNOSTICS & CLINICAL LABORATORIES", fill=(255, 255, 255))
    draw.text((25, 42), "Main Boulevard, Gulberg III, Lahore  |  Tel: +92-42-35750011", fill=(200, 220, 245))
    draw.text((25, 60), "ISO 15189 Certified Medical Laboratory Network", fill=(180, 210, 240))

    # Patient Details Box
    draw.rectangle([(25, 105), (width - 25, 195)], outline=(180, 190, 205), width=2)
    p = report_meta["patient"]
    draw.text((40, 115), f"Patient Name: {p['name']}", fill=(20, 20, 20))
    draw.text((360, 115), f"Age / Gender: {p['age']} Y / {p['gender']}", fill=(20, 20, 20))
    draw.text((600, 115), f"MR #: {report_meta['mr_number']}", fill=(20, 20, 20))

    draw.text((40, 142), f"Referred By:  {report_meta['ref_doctor']}", fill=(20, 20, 20))
    draw.text((360, 142), f"Sample Date:  {report_meta['date']}", fill=(20, 20, 20))
    draw.text((600, 142), f"Status: Final Approved", fill=(30, 120, 30))

    draw.text((40, 168), f"Specimen:     Venous Whole Blood / Serum", fill=(80, 80, 80))
    draw.text((360, 168), f"Reporting Lab: City Care Central Lahore", fill=(80, 80, 80))

    # Test Panel Header
    draw.rectangle([(25, 215), (width - 25, 248)], fill=(235, 242, 250))
    draw.text((40, 224), f"DEPARTMENT OF PATHOLOGY — {report_meta['panel_name'].upper()}", fill=(20, 65, 120))

    # Table Columns Header
    y = 265
    draw.line([(25, y), (width - 25, y)], fill=(120, 130, 150), width=2)
    draw.text((40, y + 6), "Test Parameter", fill=(40, 40, 40))
    draw.text((290, y + 6), "Observed Value", fill=(40, 40, 40))
    draw.text((440, y + 6), "Unit", fill=(40, 40, 40))
    draw.text((540, y + 6), "Reference Range", fill=(40, 40, 40))
    draw.text((700, y + 6), "Flag", fill=(40, 40, 40))
    y += 30
    draw.line([(25, y), (width - 25, y)], fill=(200, 205, 215), width=1)
    y += 10

    # Draw Test Rows
    for t in report_meta["results"]:
        flag_color = (20, 20, 20)
        if t["flag"] in ["HIGH", "LOW"]:
            flag_color = (200, 20, 20)
        elif t["flag"] == "CRITICAL":
            flag_color = (180, 0, 0)

        draw.text((40, y), t["name"], fill=(30, 30, 30))
        draw.text((290, y), str(t["value"]), fill=flag_color)
        draw.text((440, y), t["unit"], fill=(60, 60, 60))
        draw.text((540, y), t["reference_range"], fill=(70, 70, 70))
        draw.text((700, y), t["flag"], fill=flag_color)
        y += 32

    # Footer
    draw.line([(25, 630), (width - 25, 630)], fill=(180, 190, 205), width=1)
    draw.text((40, 642), "Methodology: Automated Enzymatic / Chemiluminescence / Flow Cytometry Analysis.", fill=(100, 100, 100))
    draw.text((40, 660), "Verified by: Dr. Zafar Iqbal, FCPS (Haematology & Chemical Pathology)", fill=(60, 60, 60))
    draw.text((40, 680), "** Note: Clinical correlation is required. Not valid for medico-legal purposes.", fill=(130, 130, 130))

    img.save(file_path, "PNG")


def generate_all_30_reports():
    print("=" * 70)
    print("Generating 30 Authentic Synthetic Lab Reports & Ground Truth JSON...")
    print("=" * 70)

    # Distribute 30 reports across panels
    panel_distribution = [
        (PANELS[0], 8), # CBC x8
        (PANELS[1], 7), # LFT x7
        (PANELS[2], 5), # Lipid x5
        (PANELS[3], 5), # HbA1c x5
        (PANELS[4], 5)  # RFT x5
    ]

    report_index = 1
    ground_truth = []

    for panel_def, count in panel_distribution:
        for _ in range(count):
            p_name, p_age, p_gender = PATIENT_NAMES[(report_index - 1) % len(PATIENT_NAMES)]
            doctor = DOCTORS[(report_index - 1) % len(DOCTORS)]

            report_id = f"report_{report_index:02d}"
            mr_num = f"MR-2026-{1000 + report_index}"
            date_str = f"2026-10-0{random.randint(1, 6)}"

            report_results = []

            for test_name, min_v, max_v, unit, ref_str in panel_def["tests"]:
                # 30% chance of abnormal value for testing flags
                dice = random.random()
                if dice < 0.20: # High
                    val = round(max_v * random.uniform(1.15, 1.55), 1)
                    flag = "HIGH"
                elif dice < 0.35: # Low
                    val = round(min_v * random.uniform(0.55, 0.88), 1)
                    flag = "LOW"
                else: # Normal
                    val = round(random.uniform(min_v * 1.05, max_v * 0.95), 1)
                    flag = "NORMAL"

                # Integer parameters
                if "Count" in test_name or "Platelet" in test_name or "WBC" in test_name:
                    val = int(val)

                report_results.append({
                    "name": test_name,
                    "value": val,
                    "unit": unit,
                    "reference_range": ref_str,
                    "flag": flag
                })

            report_meta = {
                "report_id": report_id,
                "mr_number": mr_num,
                "date": date_str,
                "ref_doctor": doctor,
                "panel_name": panel_def["panel_name"],
                "patient": {
                    "name": p_name,
                    "age": p_age,
                    "gender": p_gender
                },
                "results": report_results
            }

            # Render PNG image
            image_path = OUTPUT_DIR / f"{report_id}.png"
            render_report_image(report_meta, image_path)

            ground_truth.append(report_meta)
            report_index += 1

    # Save Ground Truth JSON
    gt_path = OUTPUT_DIR / "ground_truth.json"
    gt_path.write_text(json.dumps(ground_truth, indent=2), encoding="utf-8")

    print(f"Successfully generated 30 Lab Report PNGs in: {OUTPUT_DIR}")
    print(f"Ground truth dataset saved to: {gt_path}")
    print("=" * 70)


if __name__ == "__main__":
    generate_all_30_reports()
