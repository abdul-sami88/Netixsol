"""
Prescription Safety Agent for City Care Clinics.
Connects attending physicians to the deterministic PrescriptionSafetyEngine:
- Reviews doctor's draft prescriptions before signing.
- Executes 5 deterministic checks (Allergies, Interactions, Max Dose, Duplicates, Special Populations).
- Generates clear doctor warnings in English and UrduLish:
  Example: "⚠️ Patient ko Penicillin se allergy hai — Amoxicillin contraindicated hai."
- Produces bilingual patient explanations for approved or modified regimens.
"""

import os
import json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from src.safety.prescription_safety_engine import PrescriptionSafetyEngine, explain_safety_verdict_llm


class PrescriptionReviewVerdict(BaseModel):
    doctor_name: str
    patient_id: str
    can_sign: bool = Field(..., description="Whether prescription can be safely signed")
    safety_verdict: str = Field(..., description="PASS, WARNING, or BLOCKED")
    doctor_alerts: List[str] = Field(default_factory=list, description="Direct clinical warnings to physician")
    doctor_warning_summary_ur: str = Field(..., description="UrduLish warning summary for doctor")
    patient_explanation_ur: str = Field(..., description="UrduLish explanation for patient counseling")
    patient_explanation_en: str = Field(..., description="English explanation for patient counseling")
    detailed_issues: List[Dict[str, Any]] = Field(default_factory=list)


class PrescriptionSafetyAgent:
    def __init__(self):
        self.engine = PrescriptionSafetyEngine()

    def review_draft_prescription(
        self,
        doctor_name: str,
        patient_id: str,
        proposed_medications: List[Dict[str, Any]],
        patient_age: Optional[int] = None,
        patient_gender: Optional[str] = None,
        is_pregnant: bool = False,
        is_lactating: bool = False,
        patient_allergies: Optional[List[str]] = None,
        active_medications: Optional[List[str]] = None
    ) -> PrescriptionReviewVerdict:
        """
        Evaluates a physician's draft prescription.
        """
        # Run deterministic engine
        engine_result = self.engine.evaluate_prescription(
            proposed_medications=proposed_medications,
            patient_id=patient_id,
            patient_age=patient_age,
            patient_gender=patient_gender,
            is_pregnant=is_pregnant,
            is_lactating=is_lactating,
            patient_allergies=patient_allergies,
            active_medications=active_medications
        )

        verdict = engine_result["verdict"]
        issues = engine_result["issues"]
        can_sign = (verdict != "BLOCKED")

        # Format doctor alerts
        doctor_alerts = []
        for i in issues:
            prefix = "⛔ BLOCKED" if i["severity"] == "CRITICAL_BLOCK" else "⚠️ WARNING"
            doctor_alerts.append(f"{prefix}: {i['title']} — {i['description']} Action: {i.get('clinical_action', 'Review medication')}")

        # UrduLish doctor summary
        if verdict == "BLOCKED":
            doc_sum_ur = "⛔ EHTIYAT: Draft prescription mein shadeed contraindications hain. Dawa dispense nahi ki ja sakti."
            for i in issues:
                if i.get("category") == "ALLERGY_CONFLICT":
                    doc_sum_ur += f"\n• ⚠️ Patient ko {i.get('allergen')} se allergy hai — {i.get('drug')} contraindicated hai."
                elif i.get("category") == "DRUG_INTERACTION":
                    doc_sum_ur += f"\n• ⚠️ Khatarnak interaction: {', '.join(i.get('drugs_involved', []))} sath nahi de sakte."
        elif verdict == "WARNING":
            doc_sum_ur = "⚠️ NOTICE: Prescription mein clinical cautions hain (monitoring ya dose adjustment zaroori hai)."
        else:
            doc_sum_ur = "✅ SAFE: Prescription mukammal taur par safe hai. Koi allergy ya interaction issue nahi mila."

        # Get bilingual patient explanations from decoupled LLM explainer
        llm_explanations = explain_safety_verdict_llm(engine_result)

        return PrescriptionReviewVerdict(
            doctor_name=doctor_name,
            patient_id=patient_id,
            can_sign=can_sign,
            safety_verdict=verdict,
            doctor_alerts=doctor_alerts,
            doctor_warning_summary_ur=doc_sum_ur,
            patient_explanation_ur=llm_explanations["urdulish"],
            patient_explanation_en=llm_explanations["english"],
            detailed_issues=issues
        )
