"""
Clinical Summary Agent for City Care Clinics.
Generates structured pre-visit SOAP notes for attending physicians:
- S (Subjective): Patient-reported facts from conversational intake.
- O (Objective): Verified clinic EHR data, active prescriptions, and recent lab results.
- A (Assessment for Doctor Review): AI-generated differential considerations (STRICTLY MARKED AS AI SUGGESTIONS).
- P (Plan Suggestions): AI-suggested lab workups and counseling talking points.

Crucial Design Requirement:
Patient-reported facts MUST be strictly separated from AI clinical suggestions.
"""

import os
import json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class SOAPNote(BaseModel):
    patient_id: str = Field(..., description="Patient Identifier")
    patient_name: str = Field(..., description="Full Name")
    appointment_reason: str = Field(..., description="Primary visit reason")
    
    # 1. Subjective (Patient-Reported Facts)
    subjective: Dict[str, Any] = Field(..., description="Patient-reported symptoms, duration, severity")
    
    # 2. Objective (Verified EHR Data)
    objective: Dict[str, Any] = Field(..., description="Verified EHR conditions, active prescriptions, lab values")
    
    # 3. Assessment (AI Suggestions for Doctor Review)
    assessment_ai_suggestions: Dict[str, Any] = Field(..., description="Provisional AI considerations for doctor review")
    
    # 4. Plan Suggestions (AI Suggestions)
    plan_ai_suggestions: Dict[str, Any] = Field(..., description="Suggested diagnostic investigations and counseling")
    
    clinical_disclaimer: str = Field(
        default="AI CLINICAL SUMMARY DISCLAIMER: Assessment and Plan sections represent preliminary algorithmic syntheses generated for attending physician convenience. These do not constitute medical diagnoses or prescriptive orders. All clinical decisions remain the exclusive responsibility of the licensed practitioner.",
        description="Mandatory legal and safety disclaimer"
    )


class ClinicalSummaryAgent:
    def __init__(self):
        self.groq_key = os.getenv("GROQ_API_KEY")

    def generate_soap_note(
        self,
        patient_id: str,
        patient_name: str,
        intake_data: Dict[str, Any],
        patient_history: Optional[List[str]] = None,
        patient_allergies: Optional[List[str]] = None,
        active_medications: Optional[List[str]] = None,
        recent_labs: Optional[List[Dict[str, Any]]] = None
    ) -> SOAPNote:
        """
        Synthesizes a pre-visit SOAP note from intake + EHR history + lab observations.
        Guarantees strict structural separation between patient facts and AI suggestions.
        """
        patient_history = patient_history or []
        patient_allergies = patient_allergies or []
        active_medications = active_medications or []
        recent_labs = recent_labs or []

        # 1. SUBJECTIVE: Patient-reported facts
        subjective_data = {
            "chief_complaint": intake_data.get("chief_complaint", "General Consultation"),
            "duration": intake_data.get("duration", "Unspecified duration"),
            "reported_severity_scale": f"{intake_data.get('severity_scale', 5)} / 10",
            "associated_symptoms": intake_data.get("associated_symptoms", []),
            "patient_relationship": intake_data.get("patient_relationship", "self"),
            "self_reported_allergies": intake_data.get("allergies", []),
            "self_reported_medications": intake_data.get("current_medications", [])
        }

        # 2. OBJECTIVE: Verified Clinic EHR Data
        lab_summary = [
            f"{l.get('test_name')}: {l.get('value')} {l.get('unit')} (Ref: {l.get('reference_range')}, Flag: {l.get('interpretation')})"
            for l in recent_labs
        ]
        objective_data = {
            "verified_chronic_conditions": patient_history,
            "documented_allergies": patient_allergies,
            "active_prescriptions": active_medications,
            "recent_laboratory_observations": lab_summary if lab_summary else ["No recent lab tests on file within 90 days"]
        }

        # 3. AI ASSESSMENT & PLAN GENERATION
        ai_assessment, ai_plan = self._generate_ai_differential(
            patient_name=patient_name,
            subjective=subjective_data,
            objective=objective_data
        )

        return SOAPNote(
            patient_id=patient_id,
            patient_name=patient_name,
            appointment_reason=subjective_data["chief_complaint"],
            subjective=subjective_data,
            objective=objective_data,
            assessment_ai_suggestions=ai_assessment,
            plan_ai_suggestions=ai_plan
        )

    def _generate_ai_differential(
        self,
        patient_name: str,
        subjective: Dict[str, Any],
        objective: Dict[str, Any]
    ) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Calls Groq LLM to synthesize provisional differentials and workup suggestions.
        """
        prompt = f"""
Generate an Assessment and Plan for an attending physician pre-visit SOAP note.
Patient: {patient_name}
Subjective Facts (Patient-Reported):
- Chief Complaint: {subjective['chief_complaint']}
- Duration: {subjective['duration']}
- Severity: {subjective['reported_severity_scale']}
- Associated Symptoms: {', '.join(subjective['associated_symptoms'])}

Objective EHR Facts:
- Chronic Conditions: {', '.join(objective['verified_chronic_conditions'])}
- Documented Allergies: {', '.join(objective['documented_allergies'])}
- Active Prescriptions: {', '.join(objective['active_prescriptions'])}
- Lab Results: {'; '.join(objective['recent_laboratory_observations'])}

Output valid JSON with:
"assessment": {{
    "provisional_differential_considerations": ["diff 1", "diff 2", "diff 3"],
    "clinical_rationale": "Brief rationale",
    "risk_factors_to_review": ["risk 1", "risk 2"]
}},
"plan": {{
    "suggested_diagnostic_workup": ["test 1", "test 2"],
    "medication_safety_cautions": ["caution 1"],
    "patient_counseling_points": ["point 1", "point 2"],
    "red_flag_warning_signs_for_patient": ["warning sign"]
}}
"""

        if self.groq_key:
            try:
                from groq import Groq
                client = Groq(api_key=self.groq_key)
                res = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "You are a senior clinical consultant assisting outpatient doctors in Pakistan. Return valid JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    response_format={"type": "json_object"}
                )
                data = json.loads(res.choices[0].message.content)
                return data.get("assessment", {}), data.get("plan", {})
            except Exception:
                pass

        # Deterministic fallback differential
        cc = subjective["chief_complaint"].lower()
        if "chest" in cc or "heart" in cc:
            diffs = ["Angina Pectoris / Ischemic Heart Disease", "Gastroesophageal Reflux Disease (GERD)", "Costochondritis / Musculoskeletal Strain"]
            tests = ["12-Lead ECG", "Cardiac Troponin I", "Echocardiogram"]
        elif "fever" in cc or "bukhar" in cc:
            diffs = ["Acute Viral Upper Respiratory Infection", "Enteric (Typhoid) Fever", "Urinary Tract Infection (UTI)"]
            tests = ["Complete Blood Count (CBC) with ESR", "Urine Routine Examination", "Typhidot / Blood Culture if > 5 days"]
        elif "cough" in cc or "khansi" in cc:
            diffs = ["Acute Bronchitis", "Allergic Cough / Asthma Exacerbation", "Post-Nasal Drip Syndrome"]
            tests = ["Chest X-Ray PA View", "Peak Expiratory Flow Rate (PEFR)"]
        else:
            diffs = ["Unspecified Symptom Presentation for In-Person Evaluation", "Viral Illness / Systemic Fatigue", "Secondary Symptom to Underlying Chronic Condition"]
            tests = ["Complete Blood Count (CBC)", "Basic Metabolic Panel (Serum Creatinine, Electrolytes)"]

        ai_assessment = {
            "provisional_differential_considerations": diffs,
            "clinical_rationale": f"Based on reported presentation of {subjective['chief_complaint']} for {subjective['duration']}.",
            "risk_factors_to_review": objective["verified_chronic_conditions"] or ["No major pre-existing chronic risks"]
        }
        ai_plan = {
            "suggested_diagnostic_workup": tests,
            "medication_safety_cautions": [f"Review allergy cross-reactions against documented: {', '.join(objective['documented_allergies']) or 'None'}"],
            "patient_counseling_points": ["Hydration and rest", "Monitor temperature and vital signs twice daily"],
            "red_flag_warning_signs_for_patient": ["Sudden shortness of breath, chest pressure, confusion, or inability to keep fluids down"]
        }
        return ai_assessment, ai_plan
