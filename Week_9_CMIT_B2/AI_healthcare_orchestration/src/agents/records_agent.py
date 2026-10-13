"""
Records Agent for City Care Clinics.
Answers patient and physician inquiries using verified FHIR records:
- Patient demographics & chronic diagnoses
- Active prescriptions and dosage history
- Documented allergies and severities
- Historical laboratory observations & vitals (CBC, HbA1c, LFT, Lipid profile)
- Non-diagnostic bilingual explanations (UrduLish & English)
"""

import os
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.mcp_servers.patient_records_server import (
    get_patient_profile,
    get_patient_allergies,
    get_active_medications,
    get_lab_history
)
from src.privacy.pii_anonymizer import sanitize_patient_text


class RecordsAgent:
    def __init__(self):
        self.groq_key = os.getenv("GROQ_API_KEY")

    def answer_patient_record_query(
        self,
        patient_id: str,
        query: str,
        language: str = "both"
    ) -> Dict[str, Any]:
        """
        Retrieves factual patient data and answers queries without diagnosing.
        """
        # 1. Fetch factual records
        profile = get_patient_profile(patient_id)
        if profile.get("status") != "success":
            return {"status": "error", "message": f"Patient records for {patient_id} could not be retrieved."}

        allergies = get_patient_allergies(patient_id).get("allergies", [])
        meds = get_active_medications(patient_id).get("medications", [])
        labs = get_lab_history(patient_id, limit=5).get("observations", [])

        # Build context
        med_strs = [f"{m['brand_name']} ({m['dosage_instruction']})" for m in meds]
        context_lines = [
            f"Patient: {profile.get('full_name')} (Age: {profile.get('dob')}, City: {profile.get('city')})",
            f"Chronic Conditions: {', '.join([c['code'] for c in profile.get('conditions', [])]) or 'None'}",
            f"Active Allergies: {', '.join([a['allergy'] for a in allergies]) or 'None'}",
            f"Active Prescriptions: {', '.join(med_strs) or 'None'}",
            "Recent Lab Results:"
        ]
        for l in labs:
            context_lines.append(
                f"- {l['test_name']}: {l['value']} {l['unit']} (Ref: {l['reference_range']}, Interpretation: {l['interpretation']})"
            )

        context_str = "\n".join(context_lines)
        sanitized_query = sanitize_patient_text(query)

        # Generate answer using Groq LLM with non-diagnostic constraint
        if self.groq_key:
            try:
                from groq import Groq
                client = Groq(api_key=self.groq_key)
                prompt = (
                    "You are a medical records assistant at City Care Clinics.\n"
                    "RULES:\n"
                    "1. Answer ONLY using the factual patient data provided below.\n"
                    "2. You MUST NOT diagnose any disease. If asked 'kya mujhe cancer hai?', explain that only a doctor can diagnose.\n"
                    "3. Provide answers in English and UrduLish (Roman Urdu).\n\n"
                    f"<PATIENT_FILE>\n{context_str}\n</PATIENT_FILE>\n\n"
                    f"User Query: {sanitized_query}\n\n"
                    "Output JSON with keys 'english' and 'urdulish'."
                )
                res = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "You are a professional clinic records assistant. Return valid JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.0,
                    response_format={"type": "json_object"}
                )
                parsed = json.loads(res.choices[0].message.content)
                return {
                    "status": "success",
                    "patient_id": patient_id,
                    "query": query,
                    "answer_english": parsed.get("english", ""),
                    "answer_urdulish": parsed.get("urdulish", ""),
                    "raw_context": context_str
                }
            except Exception:
                pass

        # Deterministic fallback response
        en_resp = f"According to your clinic file: {context_str}"
        ur_resp = f"Aap ke clinic record ke mutabiq aap ki active dawaiyan aur recent test reports darj hain. Baraye meherbani doctor se tafseeli mashwara karein."

        return {
            "status": "success",
            "patient_id": patient_id,
            "query": query,
            "answer_english": en_resp,
            "answer_urdulish": ur_resp,
            "raw_context": context_str
        }
