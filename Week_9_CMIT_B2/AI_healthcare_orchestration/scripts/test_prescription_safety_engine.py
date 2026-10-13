"""
Comprehensive Evaluation & Test Suite for Prescription Safety Engine.
Validates all 5 deterministic checks + LLM decoupled explanation:
1. Allergy conflicts & cross-reactivity
2. Drug-drug interactions (DDI)
3. Maximum daily dose bounds
4. Duplicate therapy (active ingredients)
5. Special populations (Pregnancy, Pediatrics, Geriatrics)
6. Decoupled UrduLish & English LLM explanation
"""

import sys
import json
from pathlib import Path

# Fix Windows console UTF-8 output
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.safety.prescription_safety_engine import PrescriptionSafetyEngine, explain_safety_verdict_llm


def run_tests():
    engine = PrescriptionSafetyEngine()
    print("=" * 70)
    print("PRESCRIPTION SAFETY ENGINE — DETERMINISTIC VERIFICATION SUITE")
    print("=" * 70)

    # -------------------------------------------------------------
    # TEST 1: ALLERGY CONFLICT
    # -------------------------------------------------------------
    print("\n--- TEST 1: ALLERGY CONFLICT ---")
    case1 = engine.evaluate_prescription(
        proposed_medications=[
            {"drug_name": "Augmentin", "daily_dose_mg": 1250},
            {"drug_name": "Cefspan", "daily_dose_mg": 400}
        ],
        patient_allergies=["Penicillin Allergy"]
    )
    print(f"Verdict: {case1['verdict']} (Blocking: {case1['summary']['blocking_issues']}, Warnings: {case1['summary']['warning_issues']})")
    assert case1["verdict"] == "BLOCKED", "Case 1 should be BLOCKED for Augmentin in Penicillin allergy"
    categories = [i["category"] for i in case1["issues"]]
    assert "ALLERGY_CONFLICT" in categories
    assert "ALLERGY_CROSS_REACTIVITY" in categories
    print("PASS: Successfully blocked Augmentin and flagged Cefspan cross-reactivity.")

    # -------------------------------------------------------------
    # TEST 2: DRUG-DRUG INTERACTIONS
    # -------------------------------------------------------------
    print("\n--- TEST 2: DRUG-DRUG INTERACTIONS (NSAID + Antiplatelet) ---")
    case2 = engine.evaluate_prescription(
        proposed_medications=[
            {"drug_name": "Voltral", "daily_dose_mg": 100}
        ],
        active_medications=["Plavix"]
    )
    print(f"Verdict: {case2['verdict']} (Issues: {case2['summary']['total_issues']})")
    assert case2["verdict"] == "BLOCKED", "Case 2 should be BLOCKED for Voltral + Plavix"
    assert case2["issues"][0]["category"] == "DRUG_INTERACTION"
    print(f"PASS: Caught DDI: {case2['issues'][0]['title']}")

    # -------------------------------------------------------------
    # TEST 3: MAXIMUM DAILY DOSE BOUNDS
    # -------------------------------------------------------------
    print("\n--- TEST 3: MAXIMUM DAILY DOSE (Overdose Check) ---")
    # Panadol safe limit is 4000mg. Test 5000mg (overdose) vs 2000mg (safe)
    case3_overdose = engine.evaluate_prescription(
        proposed_medications=[
            {"drug_name": "Panadol", "daily_dose_mg": 6000}
        ]
    )
    print(f"Overdose Verdict: {case3_overdose['verdict']}")
    assert case3_overdose["verdict"] == "BLOCKED"
    assert case3_overdose["issues"][0]["category"] == "OVERDOSE_HAZARD"
    print(f"PASS: Overdose of Panadol (6000mg) blocked: {case3_overdose['issues'][0]['title']}")

    case3_safe = engine.evaluate_prescription(
        proposed_medications=[
            {"drug_name": "Panadol", "daily_dose_mg": 2000}
        ]
    )
    print(f"Safe Dose Verdict: {case3_safe['verdict']}")
    assert case3_safe["verdict"] == "PASS"
    print("PASS: Safe dose of Panadol (2000mg) passed with zero issues.")

    # -------------------------------------------------------------
    # TEST 4: DUPLICATE THERAPY (Identical Generics)
    # -------------------------------------------------------------
    print("\n--- TEST 4: DUPLICATE THERAPY (Two Brands, Same Generic) ---")
    # Prescribing Panadol while active on Calpol Syrup (both Paracetamol)
    case4 = engine.evaluate_prescription(
        proposed_medications=[
            {"drug_name": "Panadol", "daily_dose_mg": 1000}
        ],
        active_medications=["Calpol Syrup"]
    )
    print(f"Duplicate Verdict: {case4['verdict']}")
    assert case4["verdict"] == "WARNING"
    assert case4["issues"][0]["category"] == "DUPLICATE_THERAPY"
    print(f"PASS: Caught duplicate Paracetamol therapy: {case4['issues'][0]['title']}")

    # -------------------------------------------------------------
    # TEST 5: SPECIAL POPULATIONS
    # -------------------------------------------------------------
    print("\n--- TEST 5: SPECIAL POPULATIONS ---")

    # 5A: Pregnancy (Zestril / ACEi and Lipitor / Statin in pregnancy)
    case5_preg = engine.evaluate_prescription(
        proposed_medications=[
            {"drug_name": "Zestril", "daily_dose_mg": 10},
            {"drug_name": "Lipitor", "daily_dose_mg": 20}
        ],
        is_pregnant=True
    )
    print(f"5A (Pregnancy) Verdict: {case5_preg['verdict']} (Blocks: {case5_preg['summary']['blocking_issues']})")
    assert case5_preg["verdict"] == "BLOCKED"
    assert any(i["category"] == "PREGNANCY_CONTRAINDICATION" for i in case5_preg["issues"])
    print("PASS: Blocked ACE-Inhibitor and Statin in pregnancy.")

    # 5B: Pediatric (Disprin in 9-year-old child -> Reye's Syndrome risk)
    case5_peds = engine.evaluate_prescription(
        proposed_medications=[
            {"drug_name": "Disprin", "daily_dose_mg": 300}
        ],
        patient_age=9
    )
    print(f"5B (Pediatric) Verdict: {case5_peds['verdict']}")
    assert case5_peds["verdict"] == "BLOCKED"
    assert case5_peds["issues"][0]["category"] == "PEDIATRIC_CONTRAINDICATION"
    print(f"PASS: Blocked Aspirin in 9-year-old: {case5_peds['issues'][0]['title']}")

    # 5C: Geriatric (Hydryllin & Voltral in 78-year-old patient -> Beers Criteria)
    case5_geri = engine.evaluate_prescription(
        proposed_medications=[
            {"drug_name": "Hydryllin Syrup", "daily_dose_mg": 20},
            {"drug_name": "Voltral", "daily_dose_mg": 100}
        ],
        patient_age=78
    )
    print(f"5C (Geriatric) Verdict: {case5_geri['verdict']} (Warnings: {case5_geri['summary']['warning_issues']})")
    assert case5_geri["verdict"] == "WARNING"
    assert any(i["category"] == "GERIATRIC_BEERS_CRITERIA" for i in case5_geri["issues"])
    print("PASS: Flagged Beers Criteria cautions for elderly patient.")

    # -------------------------------------------------------------
    # TEST 6: DECOUPLED LLM EXPLANATION (English & UrduLish)
    # -------------------------------------------------------------
    print("\n--- TEST 6: DECOUPLED LLM EXPLANATION GENERATION ---")
    explanation = explain_safety_verdict_llm(case1)
    print("\n[ENGLISH EXPLANATION]:")
    print(explanation["english"][:300] + "...")
    print("\n[URDULISH EXPLANATION]:")
    print(explanation["urdulish"][:300] + "...")
    assert len(explanation["english"]) > 20
    assert len(explanation["urdulish"]) > 20
    print("\nPASS: Dual-language explanation generated successfully.")

    print("\n" + "=" * 70)
    print("ALL 6 TESTS IN PRESCRIPTION SAFETY ENGINE PASSED WITH 100% SUCCESS!")
    print("=" * 70)


if __name__ == "__main__":
    run_tests()
