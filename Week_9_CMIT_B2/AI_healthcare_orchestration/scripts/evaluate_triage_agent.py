"""
Evaluation script for Triage Agent across 50 clinical symptom scenarios.
Calculates:
- Emergency Recall (Must be 100%)
- Emergency Specificity
- Over-triage rate
- Under-triage rate
"""

import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Fix Windows console UTF-8 output
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.agents.triage_agent import TriageAgent

# 50 CLINICAL SCENARIOS (15 EMERGENCY, 18 URGENT, 17 ROUTINE)
SCENARIOS_50 = [
    # --- 15 EMERGENCY SCENARIOS ---
    {"id": 1, "cc": "Shadeed seene mein dard jo ultee baazoo mein ja raha hai", "sev": 9, "symptoms": ["sweating", "nausea"], "truth": "EMERGENCY"},
    {"id": 2, "cc": "Crushing chest pain and tightness radiating to jaw", "sev": 10, "symptoms": ["shortness of breath"], "truth": "EMERGENCY"},
    {"id": 3, "cc": "Achanak chehra tedha ho gaya aur zuban ladkhada rahi hai", "sev": 8, "symptoms": ["right arm weak"], "truth": "EMERGENCY"},
    {"id": 4, "cc": "Sudden one-sided body paralysis and slurred speech", "sev": 9, "symptoms": ["confusion"], "truth": "EMERGENCY"},
    {"id": 5, "cc": "Saans nahi aa rahi, dum ghut raha hai aur hont neelay par gaye hain", "sev": 9, "symptoms": ["cyanosis", "gasping"], "truth": "EMERGENCY"},
    {"id": 6, "cc": "Severe acute respiratory distress and gasping for air", "sev": 10, "symptoms": ["blue lips"], "truth": "EMERGENCY"},
    {"id": 7, "cc": "Khoon ki ulti shuru ho gayi hai aur chakkar aa rahe hain", "sev": 8, "symptoms": ["vomiting blood", "pallor"], "truth": "EMERGENCY"},
    {"id": 8, "cc": "Profuse arterial bleeding from wound that will not stop", "sev": 9, "symptoms": ["weakness"], "truth": "EMERGENCY"},
    {"id": 9, "cc": "Dawai khane ke baad gala band ho raha hai aur zuban soojh gayi hai", "sev": 9, "symptoms": ["throat closing", "wheezing"], "truth": "EMERGENCY"},
    {"id": 10, "cc": "Severe anaphylaxis with swollen lips and difficulty breathing", "sev": 10, "symptoms": ["stridor"], "truth": "EMERGENCY"},
    {"id": 11, "cc": "Mareez achanak behosh ho gaya hai aur hosh nahi aa raha", "sev": 10, "symptoms": ["unconscious", "unresponsive"], "truth": "EMERGENCY"},
    {"id": 12, "cc": "Sudden onset violent seizure and unresponsiveness", "sev": 9, "symptoms": ["seizure", "convulsions"], "truth": "EMERGENCY"},
    {"id": 13, "cc": "Dil ka daura par gaya lagta hai, chhati mein shadeed dabao hai", "sev": 9, "symptoms": ["chest pain", "diaphoresis"], "truth": "EMERGENCY"},
    {"id": 14, "cc": "Face drooping suddenly on left side with arm numbness", "sev": 8, "symptoms": ["slurred speech"], "truth": "EMERGENCY"},
    {"id": 15, "cc": "Coughing up large amounts of fresh blood with chest pain", "sev": 9, "symptoms": ["coughing blood", "dyspnea"], "truth": "EMERGENCY"},

    # --- 18 URGENT SCENARIOS ---
    {"id": 16, "cc": "Tez bukhar 103F do din se aur kapkapi", "sev": 7, "symptoms": ["high fever", "rigors"], "truth": "URGENT"},
    {"id": 17, "cc": "Severe flank pain radiating to groin 8/10, suspect kidney stone", "sev": 8, "symptoms": ["dysuria", "nausea"], "truth": "URGENT"},
    {"id": 18, "cc": "Musal-sal ultiyan subah se, pani bhi hazam nahi ho raha", "sev": 7, "symptoms": ["persistent vomiting", "dehydration"], "truth": "URGENT"},
    {"id": 19, "cc": "Acute severe ear pain and purulent discharge in child", "sev": 7, "symptoms": ["fever", "crying"], "truth": "URGENT"},
    {"id": 20, "cc": "Deep cut on kitchen knife requiring stitches, bleeding controlled", "sev": 6, "symptoms": ["laceration"], "truth": "URGENT"},
    {"id": 21, "cc": "Acute asthma exacerbation responding partially to inhaler", "sev": 6, "symptoms": ["wheezing", "cough"], "truth": "URGENT"},
    {"id": 22, "cc": "High fever 102F with productive yellow sputum and chest discomfort", "sev": 7, "symptoms": ["fever", "chills"], "truth": "URGENT"},
    {"id": 23, "cc": "Shadeed sir dard subah se aur ulti aa rahi hai", "sev": 7, "symptoms": ["migraine", "photophobia"], "truth": "URGENT"},
    {"id": 24, "cc": "Acute painful red eye with reduced vision and photophobia", "sev": 7, "symptoms": ["eye pain"], "truth": "URGENT"},
    {"id": 25, "cc": "Severe diarrhea 8 times today with signs of dehydration", "sev": 7, "symptoms": ["cramps", "thirst"], "truth": "URGENT"},
    {"id": 26, "cc": "Acute urinary retention, unable to pass urine for 8 hours", "sev": 8, "symptoms": ["suprapubic pain"], "truth": "URGENT"},
    {"id": 27, "cc": "Pao phisla aur takhna soojh gaya hai, chalna na-mumkin hai", "sev": 7, "symptoms": ["ankle swelling", "bruising"], "truth": "URGENT"},
    {"id": 28, "cc": "Diabetic patient with high blood sugar 380 mg/dL and extreme fatigue", "sev": 7, "symptoms": ["polyuria", "polydipsia"], "truth": "URGENT"},
    {"id": 29, "cc": "Acute tonsillitis with inability to swallow liquids", "sev": 7, "symptoms": ["severe sore throat", "fever"], "truth": "URGENT"},
    {"id": 30, "cc": "Boil / abscess on thigh that is growing red, hot, and throbbing", "sev": 6, "symptoms": ["erythema", "fluctuance"], "truth": "URGENT"},
    {"id": 31, "cc": "Bache ko tez bukhar aur jism par daaney nikal aaye hain", "sev": 7, "symptoms": ["rash", "fever"], "truth": "URGENT"},
    {"id": 32, "cc": "Hypertensive crisis reading 190/110 with headache but no chest pain", "sev": 7, "symptoms": ["headache"], "truth": "URGENT"},
    {"id": 33, "cc": "Severe acute lower abdominal pain in early pregnancy without bleeding", "sev": 7, "symptoms": ["cramps"], "truth": "URGENT"},

    # --- 17 ROUTINE SCENARIOS ---
    {"id": 34, "cc": "Chehre par acne aur daaney nikal rahe hain pichle maah se", "sev": 3, "symptoms": ["acne", "blemishes"], "truth": "ROUTINE"},
    {"id": 35, "cc": "Chronic low back ache for past 3 months after desk work", "sev": 4, "symptoms": ["stiffness"], "truth": "ROUTINE"},
    {"id": 36, "cc": "Diabetes ka regular checkup karwana hai aur prescription renew karni hai", "sev": 2, "symptoms": ["medication refill"], "truth": "ROUTINE"},
    {"id": 37, "cc": "Mild dry cough at night for 1 week, no fever", "sev": 3, "symptoms": ["cough"], "truth": "ROUTINE"},
    {"id": 38, "cc": "Bal gir rahe hain pichle do mahinon se", "sev": 2, "symptoms": ["hair fall"], "truth": "ROUTINE"},
    {"id": 39, "cc": "Routine antenatal checkup for second trimester pregnancy", "sev": 1, "symptoms": ["routine checkup"], "truth": "ROUTINE"},
    {"id": 40, "cc": "Ear wax blockage causing mild hearing reduction for 2 weeks", "sev": 3, "symptoms": ["ear fullness"], "truth": "ROUTINE"},
    {"id": 41, "cc": "Mild seasonal allergic sneezing and watery eyes", "sev": 3, "symptoms": ["sneezing", "rhinorrhea"], "truth": "ROUTINE"},
    {"id": 42, "cc": "Puranay ghutnay ka dard jo chalne par hota hai", "sev": 4, "symptoms": ["osteoarthritis"], "truth": "ROUTINE"},
    {"id": 43, "cc": "Skin dryness and mild eczema patches on elbows", "sev": 3, "symptoms": ["dry skin", "itching"], "truth": "ROUTINE"},
    {"id": 44, "cc": "Annual executive health screening and lipid profile consultation", "sev": 1, "symptoms": ["wellness check"], "truth": "ROUTINE"},
    {"id": 45, "cc": "Mild acidity and indigestion after spicy dinner", "sev": 3, "symptoms": ["heartburn"], "truth": "ROUTINE"},
    {"id": 46, "cc": "Fungal nail infection discoloration on toe for 2 months", "sev": 2, "symptoms": ["nail discoloration"], "truth": "ROUTINE"},
    {"id": 47, "cc": "Routine blood pressure checkup and dosage confirmation", "sev": 2, "symptoms": ["follow up"], "truth": "ROUTINE"},
    {"id": 48, "cc": "General fatigue and lethargy for 3 weeks, suspect iron deficiency", "sev": 3, "symptoms": ["fatigue"], "truth": "ROUTINE"},
    {"id": 49, "cc": "Mild dandruff and itchy scalp for past month", "sev": 2, "symptoms": ["scaling"], "truth": "ROUTINE"},
    {"id": 50, "cc": "Minor tension headache after long office screen time", "sev": 3, "symptoms": ["mild headache"], "truth": "ROUTINE"}
]


def evaluate():
    agent = TriageAgent()
    print("=" * 70)
    print("TRIAGE AGENT EVALUATION — 50 CLINICAL SCENARIOS")
    print("=" * 70)

    tp_emerg = 0
    fn_emerg = 0
    fp_emerg = 0

    over_triage_count = 0
    under_triage_count = 0
    correct_count = 0

    results_table = []

    for s in SCENARIOS_50:
        res = agent.evaluate_triage(
            chief_complaint=s["cc"],
            severity_scale=s["sev"],
            associated_symptoms=s["symptoms"]
        )

        pred = res.urgency_tier
        truth = s["truth"]

        # Emergency metrics
        if truth == "EMERGENCY":
            if pred == "EMERGENCY":
                tp_emerg += 1
            else:
                fn_emerg += 1
        elif pred == "EMERGENCY":
            fp_emerg += 1

        # Overall triage ranking: EMERGENCY (3) > URGENT (2) > ROUTINE (1)
        rank_map = {"EMERGENCY": 3, "URGENT": 2, "ROUTINE": 1}
        truth_rank = rank_map[truth]
        pred_rank = rank_map[pred]

        if pred_rank == truth_rank:
            correct_count += 1
            status = "EXACT_MATCH"
        elif pred_rank > truth_rank:
            over_triage_count += 1
            status = "OVER_TRIAGE"
        else:
            under_triage_count += 1
            status = "UNDER_TRIAGE"

        results_table.append({
            "id": s["id"],
            "complaint": s["cc"][:35] + "...",
            "truth": truth,
            "pred": pred,
            "status": status,
            "confidence": res.confidence_score
        })

    # Calculations
    total_emerg = sum(1 for s in SCENARIOS_50 if s["truth"] == "EMERGENCY")
    emergency_recall = (tp_emerg / total_emerg) * 100.0 if total_emerg > 0 else 100.0
    over_triage_rate = (over_triage_count / len(SCENARIOS_50)) * 100.0
    under_triage_rate = (under_triage_count / len(SCENARIOS_50)) * 100.0
    accuracy = (correct_count / len(SCENARIOS_50)) * 100.0

    print(f"\nTotal Scenarios Evaluated: {len(SCENARIOS_50)}")
    print(f"Correct Exact Classifications: {correct_count} / 50 ({accuracy:.1f}%)")
    print(f"--------------------------------------------------")
    print(f"EMERGENCY RECALL:     {emergency_recall:.1f}%  (Target: 100.0%)")
    print(f"OVER-TRIAGE RATE:     {over_triage_rate:.1f}%")
    print(f"UNDER-TRIAGE RATE:    {under_triage_rate:.1f}%")
    print(f"--------------------------------------------------")

    # Safety Assertions
    assert emergency_recall == 100.0, f"FAILED: Emergency recall must be 100%, got {emergency_recall}%"
    assert under_triage_rate <= 5.0, f"FAILED: Under-triage rate must be <= 5%, got {under_triage_rate}%"

    print("\nSAFETY VERIFICATION PASSED: 100% Emergency Recall Achieved!")

    return {
        "emergency_recall": emergency_recall,
        "over_triage_rate": over_triage_rate,
        "under_triage_rate": under_triage_rate,
        "accuracy": accuracy,
        "total": len(SCENARIOS_50)
    }


if __name__ == "__main__":
    evaluate()
