"""
Deterministic Prescription Safety Engine for City Care Clinics.
Performs 100% deterministic, rule-based clinical safety verification:
1. Allergy conflicts & cross-reactivity
2. Drug-drug interactions (DDI)
3. Maximum 24-hour daily dose bounds
4. Duplicate therapy (identical active pharmaceutical ingredients)
5. Special populations (Pregnancy, Pediatrics, Geriatrics / Beers Criteria)

Includes a decoupled LLM explanation layer that translates deterministic
verdicts into compassionate UrduLish and English patient/doctor advisories
WITHOUT ever being able to alter the deterministic safety gate.
"""

import sys
import os
import json
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.database.connection import db_session
from src.database.models import Patient, Condition, MedicationRequest
from src.mcp_servers.drug_database_server import PAKISTANI_FORMULARY, INTERACTION_RULES


# -------------------------------------------------------------
# 1. SPECIAL POPULATIONS & VULNERABILITY RULES
# -------------------------------------------------------------

PREGNANCY_RULES = [
    {
        "classes": ["ACE Inhibitor", "ARB", "CCB/ARB", "ARB/Diuretic"],
        "drugs": ["capoten", "captopril", "zestril", "lisinopril", "cozaar", "losartan", "diovan", "valsartan", "hyzaar", "exforge"],
        "severity": "CRITICAL_BLOCK",
        "title": "Severe Teratogenicity / Fetotoxicity",
        "description": "ACE inhibitors and ARBs cause fetal renal dysgenesis, oligohydramnios, pulmonary hypoplasia, and neonatal renal failure (FDA Category D/X). Contraindicated throughout pregnancy."
    },
    {
        "classes": ["Statin"],
        "drugs": ["lipitor", "atorvastatin", "atorva", "crestor", "rosuvastatin", "roseday"],
        "severity": "CRITICAL_BLOCK",
        "title": "Fetal Cholesterol Synthesis Disruption",
        "description": "Statins interfere with fetal lipid synthesis essential for central nervous system and membrane embryogenesis (FDA Category X). Absolutely contraindicated in pregnancy and lactation."
    },
    {
        "classes": ["Fluoroquinolone"],
        "drugs": ["cravit", "levofloxacin", "ciprobid", "ciprofloxacin", "avelox", "moxifloxacin"],
        "severity": "CRITICAL_BLOCK",
        "title": "Fetal Cartilage & Arthropathy Risk",
        "description": "Fluoroquinolones cause articular cartilage damage, arthropathy, and potential chondrotoxicity in growing fetal bones. Use alternative category B antibiotics (e.g. Cephalosporins, Amoxicillin)."
    },
    {
        "classes": ["Tetracycline"],
        "drugs": ["vibramycin", "doxycycline"],
        "severity": "CRITICAL_BLOCK",
        "title": "Permanent Tooth Discoloration & Bone Retardation",
        "description": "Tetracyclines cross the placenta, deposit in fetal teeth and bones, causing permanent yellow-gray-brown tooth discoloration and enamel hypoplasia."
    },
    {
        "classes": ["NSAID"],
        "drugs": ["brufen", "ibuprofen", "voltral", "diclofenac", "ponstan", "mefenamic", "synflex", "naproxen", "disprin", "aspirin", "ansaid", "toradol", "celebrex"],
        "severity": "CRITICAL_BLOCK",
        "title": "Premature Ductus Arteriosus Closure",
        "description": "NSAIDs taken in pregnancy (especially 3rd trimester) risk premature closure of the fetal ductus arteriosus, persistent pulmonary hypertension, and oligohydramnios."
    }
]

PEDIATRIC_RULES = [
    {
        "max_age": 16,
        "classes": ["Antiplatelet", "NSAID"],
        "drugs": ["disprin", "aspirin", "loprin"],
        "severity": "CRITICAL_BLOCK",
        "title": "Reye's Syndrome Risk in Children",
        "description": "Aspirin/Salicylates in children and adolescents under 16 years recovering from viral illness are associated with Reye's Syndrome (rapid, life-threatening hepatic steatosis and cerebral edema)."
    },
    {
        "max_age": 18,
        "classes": ["Fluoroquinolone"],
        "drugs": ["cravit", "levofloxacin", "ciprobid", "ciprofloxacin", "avelox", "moxifloxacin"],
        "severity": "CRITICAL_BLOCK",
        "title": "Pediatric Cartilage Erosion & Tendinopathy",
        "description": "Fluoroquinolones are contraindicated in patients under 18 years due to demonstrated risk of permanent cartilage damage in weight-bearing joints."
    },
    {
        "max_age": 8,
        "classes": ["Tetracycline"],
        "drugs": ["vibramycin", "doxycycline"],
        "severity": "CRITICAL_BLOCK",
        "title": "Dental Enamel Hypoplasia in Children",
        "description": "Doxycycline binds calcium in developing dentition, leading to irreversible staining and enamel hypoplasia in children under 8 years of age."
    },
    {
        "max_age": 12,
        "classes": ["Opioid Analgesic"],
        "drugs": ["tramal", "tramadol"],
        "severity": "CRITICAL_BLOCK",
        "title": "Fatal Pediatric Respiratory Depression",
        "description": "Tramadol is contraindicated in pediatric patients under 12 years due to unpredictable ultra-rapid CYP2D6 metabolism leading to fatal respiratory arrest."
    }
]

GERIATRIC_RULES = [
    {
        "min_age": 65,
        "classes": ["Antiemetic", "Cough Expectorant", "Cough Suppressant"],
        "drugs": ["gravinate", "dimenhydrinate", "hydryllin", "pulmonol", "chlorpheniramine", "diphenhydramine"],
        "severity": "HIGH_WARNING",
        "title": "Beers Criteria: High Anticholinergic Burden",
        "description": "First-generation antihistamines and sedatives cause marked anticholinergic toxicity in elderly patients: severe sedation, confusion, acute urinary retention, and increased fall/fracture risk."
    },
    {
        "min_age": 65,
        "classes": ["NSAID"],
        "drugs": ["voltral", "diclofenac", "ponstan", "mefenamic", "synflex", "naproxen", "toradol", "ansaid"],
        "severity": "HIGH_WARNING",
        "title": "Beers Criteria: Acute Renal & GI Ulcer Risk",
        "description": "Systemic NSAIDs in elderly patients over 65 significantly accelerate renal decline (prerenal AKI), fluid retention, and silent gastrointestinal perforation/bleeding."
    },
    {
        "min_age": 65,
        "classes": ["Opioid Analgesic"],
        "drugs": ["tramal", "tramadol"],
        "severity": "HIGH_WARNING",
        "title": "Beers Criteria: High Fall & Delirium Risk",
        "description": "Opioids in elderly patients precipitate acute delirium, severe constipation, urinary retention, ataxia, and traumatic falls."
    }
]


# -------------------------------------------------------------
# 2. DETERMINISTIC SAFETY ENGINE CLASS
# -------------------------------------------------------------

class PrescriptionSafetyEngine:
    """
    Deterministic clinical safety guardrail for drug prescribing.
    Executes 5 strict verification checks without any probabilistic LLM guessing.
    """

    def __init__(self):
        # Build quick lookup indexes from Pakistani formulary
        self.brand_to_drug: Dict[str, Dict[str, Any]] = {}
        self.generic_to_drugs: Dict[str, List[Dict[str, Any]]] = {}

        for drug in PAKISTANI_FORMULARY:
            b_key = drug["brand"].strip().lower()
            g_key = drug["generic"].strip().lower()

            self.brand_to_drug[b_key] = drug

            if g_key not in self.generic_to_drugs:
                self.generic_to_drugs[g_key] = []
            self.generic_to_drugs[g_key].append(drug)

    def find_drug_details(self, drug_query: str) -> Optional[Dict[str, Any]]:
        """Matches a drug by brand name or generic name."""
        q = drug_query.strip().lower()
        if q in self.brand_to_drug:
            return self.brand_to_drug[q]

        for b, drug in self.brand_to_drug.items():
            if q in b or b in q:
                return drug

        for g, drugs in self.generic_to_drugs.items():
            if q in g or g in q:
                return drugs[0]

        return None

    def evaluate_prescription(
        self,
        proposed_medications: List[Dict[str, Any]],
        patient_id: Optional[str] = None,
        patient_age: Optional[int] = None,
        patient_gender: Optional[str] = None,
        is_pregnant: bool = False,
        is_lactating: bool = False,
        patient_allergies: Optional[List[str]] = None,
        active_medications: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Runs comprehensive deterministic clinical safety checks on proposed medications.

        proposed_medications format:
        [
            {"drug_name": "Augmentin", "daily_dose_mg": 1250, "frequency": "twice daily"},
            {"drug_name": "Panadol", "daily_dose_mg": 2000, "frequency": "every 6 hours"}
        ]
        """
        # Pull from PostgreSQL if patient_id provided
        if patient_id:
            db_patient, db_allergies, db_meds = self._fetch_patient_context(patient_id)
            if db_patient:
                if patient_age is None and db_patient.date_of_birth:
                    today = date.today()
                    patient_age = today.year - db_patient.date_of_birth.year - (
                        (today.month, today.day) < (db_patient.date_of_birth.month, db_patient.date_of_birth.day)
                    )
                if patient_gender is None:
                    patient_gender = db_patient.gender
            if patient_allergies is None:
                patient_allergies = db_allergies
            if active_medications is None:
                active_medications = db_meds

        patient_allergies = patient_allergies or []
        active_medications = active_medications or []

        issues: List[Dict[str, Any]] = []

        # CHECK 1: Allergy Conflicts
        allergy_issues = self._check_allergies(proposed_medications, patient_allergies)
        issues.extend(allergy_issues)

        # CHECK 2: Drug-Drug Interactions (Proposed + Active)
        ddi_issues = self._check_drug_interactions(proposed_medications, active_medications)
        issues.extend(ddi_issues)

        # CHECK 3: Maximum Daily Dose Bounds
        dose_issues = self._check_max_doses(proposed_medications)
        issues.extend(dose_issues)

        # CHECK 4: Duplicate Therapy
        duplicate_issues = self._check_duplicate_therapy(proposed_medications, active_medications)
        issues.extend(duplicate_issues)

        # CHECK 5: Special Populations (Pregnancy, Pediatric, Geriatric)
        special_issues = self._check_special_populations(
            proposed_meds=proposed_medications,
            age=patient_age,
            gender=patient_gender,
            is_pregnant=is_pregnant,
            is_lactating=is_lactating
        )
        issues.extend(special_issues)

        # Calculate Verdict
        blocking_count = sum(1 for i in issues if i["severity"] == "CRITICAL_BLOCK")
        warning_count = sum(1 for i in issues if i["severity"] in ("HIGH_WARNING", "MODERATE_WARNING"))

        if blocking_count > 0:
            verdict = "BLOCKED"
            action = "PRESCRIPTION BLOCKED: Critical patient safety contraindications detected. Requires immediate physician intervention."
        elif warning_count > 0:
            verdict = "WARNING"
            action = "PRESCRIPTION FLAGGED WITH WARNINGS: Review clinical alerts and consider dosage adjustment or patient monitoring."
        else:
            verdict = "PASS"
            action = "PRESCRIPTION APPROVED: No safety contraindications detected across deterministic checks."

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "verdict": verdict,
            "patient_context": {
                "patient_id": patient_id,
                "age": patient_age,
                "gender": patient_gender,
                "is_pregnant": is_pregnant,
                "is_lactating": is_lactating,
                "documented_allergies": patient_allergies,
                "active_medications": active_medications
            },
            "proposed_medications": proposed_medications,
            "summary": {
                "total_issues": len(issues),
                "blocking_issues": blocking_count,
                "warning_issues": warning_count
            },
            "action_directive": action,
            "issues": issues
        }

    # ---------------------------------------------------------
    # INTERNAL CHECK IMPLEMENTATIONS
    # ---------------------------------------------------------

    def _fetch_patient_context(self, patient_id: str) -> Tuple[Optional[Patient], List[str], List[str]]:
        session = db_session()
        try:
            patient = session.query(Patient).filter(Patient.id == patient_id).first()
            if not patient:
                return None, [], []

            allergies = [
                c.code_display for c in patient.conditions
                if c.category == "allergy_intolerance" and c.clinical_status == "active"
            ]

            active_meds = [
                m.brand_name for m in patient.prescriptions
                if m.status == "active"
            ]

            return patient, allergies, active_meds
        finally:
            session.close()

    def _check_allergies(self, proposed_meds: List[Dict[str, Any]], allergies: List[str]) -> List[Dict[str, Any]]:
        issues = []
        if not allergies:
            return issues

        allergies_lower = [a.lower() for a in allergies]

        for p_med in proposed_meds:
            d_name = p_med.get("drug_name", "")
            d_info = self.find_drug_details(d_name)
            d_class = d_info.get("class", "") if d_info else ""
            d_generic = d_info.get("generic", "").lower() if d_info else d_name.lower()

            # Penicillin Allergy
            if any("penicillin" in a for a in allergies_lower):
                if "penicillin" in d_class.lower() or any(k in d_generic for k in ["amoxicillin", "ampicillin", "cloxacillin"]):
                    issues.append({
                        "category": "ALLERGY_CONFLICT",
                        "severity": "CRITICAL_BLOCK",
                        "drug": d_name,
                        "allergen": "Penicillin",
                        "title": "Severe Penicillin Allergy Contraindication",
                        "description": f"{d_name} belongs to the Penicillin antibiotic class ({d_class}). Patient has a documented Penicillin allergy. Risk of life-threatening anaphylaxis or angioedema.",
                        "clinical_action": "Do NOT dispense. Switch to non-beta-lactam alternative (e.g. Macrolide or Fluoroquinolone)."
                    })
                elif "cephalosporin" in d_class.lower():
                    issues.append({
                        "category": "ALLERGY_CROSS_REACTIVITY",
                        "severity": "HIGH_WARNING",
                        "drug": d_name,
                        "allergen": "Penicillin",
                        "title": "Cephalosporin Cross-Reactivity Risk",
                        "description": f"{d_name} is a Cephalosporin. Patients with severe Penicillin allergy have an estimated 1-3% cross-reactivity risk.",
                        "clinical_action": "Verify exact prior reaction history (rash vs anaphylaxis). Use with caution or choose an unrelated class."
                    })

            # Sulfa Allergy
            if any("sulfa" in a for a in allergies_lower):
                if "sulfonamide" in d_class.lower() or "sulfamethoxazole" in d_generic or "septran" in d_name.lower():
                    issues.append({
                        "category": "ALLERGY_CONFLICT",
                        "severity": "CRITICAL_BLOCK",
                        "drug": d_name,
                        "allergen": "Sulfa",
                        "title": "Severe Sulfonamide Hypersensitivity",
                        "description": f"{d_name} contains Sulfamethoxazole. Documented sulfa allergy presents extreme risk of Stevens-Johnson syndrome, toxic epidermal necrolysis, and erythema multiforme.",
                        "clinical_action": "Contraindicated. Select alternative non-sulfonamide antimicrobial."
                    })

            # Aspirin / NSAID Hypersensitivity
            if any("aspirin" in a or "nsaid" in a for a in allergies_lower):
                if "nsaid" in d_class.lower() or "antiplatelet" in d_class.lower() or any(k in d_generic for k in ["aspirin", "ibuprofen", "diclofenac", "naproxen", "mefenamic"]):
                    issues.append({
                        "category": "ALLERGY_CONFLICT",
                        "severity": "CRITICAL_BLOCK",
                        "drug": d_name,
                        "allergen": "Aspirin / NSAID",
                        "title": "NSAID-Exacerbated Respiratory/Anaphylactoid Reaction",
                        "description": f"{d_name} is an NSAID/Salicylate. Patient has documented sensitivity, presenting high risk of acute severe bronchospasm, asthma exacerbation, and urticaria.",
                        "clinical_action": "Contraindicated. Use Paracetamol (at safe doses) for analgesia."
                    })

        return issues

    def _check_drug_interactions(self, proposed_meds: List[Dict[str, Any]], active_meds: List[str]) -> List[Dict[str, Any]]:
        issues = []
        # Combine all drugs to screen
        all_drugs = [p.get("drug_name", "") for p in proposed_meds] + list(active_meds)
        cleaned_drugs = [d.strip().lower() for d in all_drugs if d.strip()]

        seen_pairs = set()

        for i in range(len(cleaned_drugs)):
            for j in range(i + 1, len(cleaned_drugs)):
                d1 = cleaned_drugs[i]
                d2 = cleaned_drugs[j]
                pair_key = tuple(sorted([d1, d2]))

                if pair_key in seen_pairs:
                    continue

                for rule in INTERACTION_RULES:
                    m1a = any(k in d1 for k in rule["drugs_a"])
                    m2b = any(k in d2 for k in rule["drugs_b"])
                    m1b = any(k in d1 for k in rule["drugs_b"])
                    m2a = any(k in d2 for k in rule["drugs_a"])

                    if (m1a and m2b) or (m1b and m2a):
                        seen_pairs.add(pair_key)
                        sev = "CRITICAL_BLOCK" if rule["severity"] == "CRITICAL" else "HIGH_WARNING"
                        issues.append({
                            "category": "DRUG_INTERACTION",
                            "severity": sev,
                            "drugs_involved": [all_drugs[i], all_drugs[j]],
                            "title": f"Drug Interaction: {all_drugs[i]} + {all_drugs[j]}",
                            "description": rule["description"],
                            "clinical_action": "Discontinue one agent or separate administration times / adjust dosing regimen."
                        })

        return issues

    def _check_max_doses(self, proposed_meds: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        issues = []
        for p in proposed_meds:
            d_name = p.get("drug_name", "")
            proposed_dose = p.get("daily_dose_mg")

            if proposed_dose is None:
                continue

            d_info = self.find_drug_details(d_name)
            if not d_info or d_info.get("max_dose_mg", 0) == 0:
                continue

            max_dose = d_info["max_dose_mg"]
            if proposed_dose > max_dose:
                pct = round((proposed_dose / max_dose) * 100, 1)
                is_lethal = pct >= 150.0
                issues.append({
                    "category": "OVERDOSE_HAZARD",
                    "severity": "CRITICAL_BLOCK" if is_lethal else "HIGH_WARNING",
                    "drug": d_name,
                    "proposed_dose_mg": proposed_dose,
                    "max_safe_dose_mg": max_dose,
                    "percentage": f"{pct}%",
                    "title": f"Overdose Threshold Exceeded for {d_name}",
                    "description": f"Proposed daily dose of {proposed_dose}mg exceeds maximum safe ceiling limit of {max_dose}mg/day ({pct}% of limit). High risk of dose-dependent acute toxicity.",
                    "clinical_action": f"Reduce daily dose to <= {max_dose}mg."
                })

        return issues

    def _check_duplicate_therapy(self, proposed_meds: List[Dict[str, Any]], active_meds: List[str]) -> List[Dict[str, Any]]:
        """Detects if two different brand medicines share the same active generic substance."""
        issues = []
        generic_map: Dict[str, List[str]] = {}

        # 1. Map proposed meds
        for p in proposed_meds:
            b_name = p.get("drug_name", "")
            d_info = self.find_drug_details(b_name)
            if d_info:
                g_name = d_info["generic"].lower().strip()
                generic_map.setdefault(g_name, []).append(f"{b_name} (Proposed)")

        # 2. Map active meds
        for a_name in active_meds:
            d_info = self.find_drug_details(a_name)
            if d_info:
                g_name = d_info["generic"].lower().strip()
                generic_map.setdefault(g_name, []).append(f"{a_name} (Active)")

        # 3. Detect duplicates
        for generic, brand_list in generic_map.items():
            if len(brand_list) > 1:
                issues.append({
                    "category": "DUPLICATE_THERAPY",
                    "severity": "HIGH_WARNING",
                    "shared_generic": generic.title(),
                    "medicines": brand_list,
                    "title": f"Duplicate Therapeutic Ingredient: {generic.title()}",
                    "description": f"Multiple medicines containing identical active ingredient '{generic.title()}' ({', '.join(brand_list)}) are concurrently prescribed. Extreme risk of accidental double-dosing and cumulative toxicity.",
                    "clinical_action": "Consolidate into a single prescription and remove redundant brand."
                })

        return issues

    def _check_special_populations(
        self,
        proposed_meds: List[Dict[str, Any]],
        age: Optional[int],
        gender: Optional[str],
        is_pregnant: bool,
        is_lactating: bool
    ) -> List[Dict[str, Any]]:
        issues = []

        for p in proposed_meds:
            d_name = p.get("drug_name", "")
            d_info = self.find_drug_details(d_name)
            if not d_info:
                continue

            d_class = d_info.get("class", "")
            d_generic = d_info.get("generic", "").lower()
            d_brand = d_name.lower()

            # A. PREGNANCY & LACTATION CHECKS
            if is_pregnant or is_lactating:
                for rule in PREGNANCY_RULES:
                    match_class = any(c.lower() in d_class.lower() for c in rule["classes"])
                    match_drug = any(k in d_brand or k in d_generic for k in rule["drugs"])

                    if match_class or match_drug:
                        issues.append({
                            "category": "PREGNANCY_CONTRAINDICATION",
                            "severity": rule["severity"],
                            "drug": d_name,
                            "title": f"Pregnancy Alert: {rule['title']} ({d_name})",
                            "description": rule["description"],
                            "clinical_action": "Strictly contraindicated in pregnancy/lactation. Switch to pregnancy-safe alternative."
                        })

            # B. PEDIATRIC CHECKS (< 18)
            if age is not None and age < 18:
                for rule in PEDIATRIC_RULES:
                    if age < rule["max_age"]:
                        match_class = any(c.lower() in d_class.lower() for c in rule["classes"])
                        match_drug = any(k in d_brand or k in d_generic for k in rule["drugs"])

                        if match_class or match_drug:
                            issues.append({
                                "category": "PEDIATRIC_CONTRAINDICATION",
                                "severity": rule["severity"],
                                "drug": d_name,
                                "patient_age": age,
                                "max_safe_age": rule["max_age"],
                                "title": f"Pediatric Contraindication: {rule['title']} ({d_name})",
                                "description": rule["description"],
                                "clinical_action": f"Do not administer to patients under {rule['max_age']} years of age."
                            })

            # C. GERIATRIC CHECKS (>= 65, Beers Criteria)
            if age is not None and age >= 65:
                for rule in GERIATRIC_RULES:
                    if age >= rule["min_age"]:
                        match_class = any(c.lower() in d_class.lower() for c in rule["classes"])
                        match_drug = any(k in d_brand or k in d_generic for k in rule["drugs"])

                        if match_class or match_drug:
                            issues.append({
                                "category": "GERIATRIC_BEERS_CRITERIA",
                                "severity": rule["severity"],
                                "drug": d_name,
                                "patient_age": age,
                                "title": f"Geriatric Caution: {rule['title']} ({d_name})",
                                "description": rule["description"],
                                "clinical_action": "Evaluate benefit-risk ratio in elderly patient. Consider safer non-anticholinergic/renal-sparing agents."
                            })

        return issues


# -------------------------------------------------------------
# 3. LLM EXPLANATION LAYER (DECOUPLED & NON-OVERRIDING)
# -------------------------------------------------------------

def explain_safety_verdict_llm(
    deterministic_result: Dict[str, Any],
    language: str = "both"
) -> Dict[str, str]:
    """
    Uses an LLM (Groq / Gemini) to explain the deterministic safety verdict
    in clear, non-technical UrduLish and English for patients and doctors.

    CRITICAL ARCHITECTURAL GUARANTEE:
    The LLM cannot alter the verdict, downgrade severity, or bypass a block.
    It functions strictly as an empathetic communicative translator.
    """
    verdict = deterministic_result["verdict"]
    issues = deterministic_result["issues"]

    if verdict == "PASS" and not issues:
        return {
            "english": "All prescribed medications have been checked and verified safe. No allergy conflicts, dangerous drug interactions, or overdose risks were detected.",
            "urdulish": "Tamam tajweez karda dawaiyan safe hain. Kisi qisam ki allergy, dangerous interaction ya zyada dose ka masla nahi mila. Aap ba-itminaan le sakte hain."
        }

    # Format issues into clean bullets for LLM prompt
    issues_summary = "\n".join([
        f"- [{i['severity']}] {i['title']}: {i['description']} (Action: {i.get('clinical_action', 'Review medication')})"
        for i in issues
    ])

    system_prompt = (
        "You are an empathetic, highly trained clinical pharmacist assistant at City Care Clinics in Pakistan.\n"
        "You are provided with a 100% DETERMINISTIC clinical safety verdict on a patient's prescription.\n"
        "RULES:\n"
        "1. You CANNOT change the verdict. If it is BLOCKED, you MUST clearly state the medicine cannot be given safely.\n"
        "2. Provide an explanation in two sections: ENGLISH and URDULISH (conversational Roman Urdu).\n"
        "3. Explain the medical reason simply without medical jargon (e.g. explain why taking two Paracetamols damages the liver, or why Penicillin causes breathing difficulty).\n"
        "4. Emphasize that the patient or doctor must discuss alternative medicines.\n"
        "5. Output valid JSON with keys 'english' and 'urdulish'."
    )

    user_prompt = f"""
Deterministic Verdict: {verdict}
Action Directive: {deterministic_result['action_directive']}
Issues Detected:
{issues_summary}

Please provide clear, compassionate explanations for patient and physician.
"""

    # Call LLM via Groq or Gemini with deterministic fallback
    groq_api_key = os.getenv("GROQ_API_KEY")
    gemini_api_key = os.getenv("GEMINI_API_KEY")

    if groq_api_key:
        groq_models = ["openai/gpt-oss-20b", "llama-3.1-8b-instant", "qwen/qwen3.8-27b"]
        for m in groq_models:
            try:
                from groq import Groq
                client = Groq(api_key=groq_api_key)
                completion = client.chat.completions.create(
                    model=m,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.2,
                    response_format={"type": "json_object"}
                )
                raw_text = completion.choices[0].message.content
                parsed = json.loads(raw_text)
                if "english" in parsed and "urdulish" in parsed:
                    return {
                        "english": parsed["english"],
                        "urdulish": parsed["urdulish"]
                    }
            except Exception:
                continue

    if gemini_api_key:
        try:
            from google import genai
            client = genai.Client(api_key=gemini_api_key)
            prompt = f"{system_prompt}\n\n{user_prompt}"
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            raw = response.text.strip()
            if raw.startswith("```json"):
                raw = raw[7:-3].strip()
            elif raw.startswith("```"):
                raw = raw[3:-3].strip()
            parsed = json.loads(raw)
            if "english" in parsed and "urdulish" in parsed:
                return {
                    "english": parsed["english"],
                    "urdulish": parsed["urdulish"]
                }
        except Exception:
            pass

    # Deterministic Fallback Explanation (if LLM offline)
    en_lines = [f"Safety Verdict: {verdict}"]
    ur_lines = [f"Safety Nateeja: {verdict}"]

    for i in issues:
        en_lines.append(f"• {i['title']}: {i['description']}")
        ur_lines.append(f"• {i['title']}: Is dawai mein khatra hai — {i.get('clinical_action', 'Doctor se rabta karein')}")

    return {
        "english": "\n".join(en_lines),
        "urdulish": "\n".join(ur_lines)
    }
