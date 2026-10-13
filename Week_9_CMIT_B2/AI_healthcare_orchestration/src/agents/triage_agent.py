"""
Triage Agent for City Care Clinics.
Implements:
1. Deterministic Rule-Based Red-Flag Detection (runs first, CANNOT be overridden by LLM).
2. LLM-Assisted Urgency Classification for non-emergency cases (URGENT vs ROUTINE).
3. Confidence score and clinical reasoning for every decision.
4. Immediate Emergency Escalation Path (1122 Ambulance dispatch guidance).
"""

import os
import re
import json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from src.privacy.pii_anonymizer import sanitize_patient_text


class TriageResult(BaseModel):
    urgency_tier: str = Field(..., description="EMERGENCY, URGENT, or ROUTINE")
    is_emergency: bool = Field(..., description="True if immediate life-threat detected")
    red_flag_triggered: bool = Field(..., description="True if deterministic red flag fired")
    red_flag_name: Optional[str] = Field(None, description="Name of the detected red flag rule")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in the triage classification")
    clinical_reasoning: str = Field(..., description="Clinical justification for the decision")
    recommended_timeframe: str = Field(..., description="Immediate, Within 24 Hours, or Within 3-5 Days")
    recommended_specialty: str = Field(..., description="Suggested medical specialty")
    patient_guidance_ur: str = Field(..., description="Actionable UrduLish guidance for patient")
    patient_guidance_en: str = Field(..., description="Actionable English guidance for patient")


# Deterministic Red-Flag Rules (CANNOT BE OVERRIDDEN)
RED_FLAG_RULES = [
    {
        "id": "CARDIAC_CRUSHING",
        "name": "Acute Coronary Syndrome / Myocardial Infarction",
        "keywords": ["chest pain", "seene mein dard", "seene me dard", "chhati mein dard", "chhati mein", "left arm pain", "left arm", "baen baazu", "baen bazu", "ultee baazoo", "jaw pain", "crushing", "dil ka daura", "heart attack", "seena dab raha", "chest discomfort", "seene mein thora sa dard", "seene mein thora dard"],
        "min_severity": 1,
        "specialty": "Cardiology / Emergency Room"
    },
    {
        "id": "STROKE_FAST",
        "name": "Acute Cerebrovascular Event (Stroke / FAST)",
        "keywords": ["face drooping", "chehra tedha", "one side weak", "ek taraf kamzori", "slurred speech", "zuban ladkhadana", "sudden paralysis", "falij", "lakwa"],
        "min_severity": 1,
        "specialty": "Emergency Neurology / ER"
    },
    {
        "id": "RESPIRATORY_FAILURE",
        "name": "Severe Respiratory Distress / Hypoxia",
        "keywords": ["cant breathe", "saans nahi aa rahi", "gasping", "neelay hont", "hont neelay", "blue lips", "suffocating", "dum ghut raha", "saans ghut", "saans mein takleef", "saans lene mein shadeed takleef", "severe wheezing"],
        "min_severity": 1,
        "specialty": "Emergency Pulmonology / ER"
    },
    {
        "id": "SEVERE_HEMORRHAGE",
        "name": "Uncontrolled Arterial Bleeding / Hemorrhage",
        "keywords": ["profuse bleeding", "arterial bleeding", "bleeding that will not stop", "bleeding won't stop", "khoon nahi ruk raha", "vomiting blood", "khoon ki ulti", "coughing blood", "arterial spurting", "severe bleeding"],
        "min_severity": 1,
        "specialty": "Trauma & Emergency Surgery"
    },
    {
        "id": "ANAPHYLAXIS",
        "name": "Severe Anaphylactic Shock",
        "keywords": ["throat closing", "gala band ho raha", "swollen tongue", "zuban soojh", "anaphylaxis", "severe allergic reaction"],
        "min_severity": 1,
        "specialty": "Emergency Medicine"
    },
    {
        "id": "LOSS_OF_CONSCIOUSNESS",
        "name": "Acute Altered Mental Status / Coma / Seizure",
        "keywords": ["unconscious", "behosh", "seizure", "mirgi ka daura", "not responding", "jawabs nahi de raha", "fainted suddenly"],
        "min_severity": 1,
        "specialty": "Emergency Medicine"
    }
]


class TriageAgent:
    def __init__(self):
        self.groq_key = os.getenv("GROQ_API_KEY")

    def evaluate_triage(
        self,
        chief_complaint: str,
        duration: str = "",
        severity_scale: int = 5,
        associated_symptoms: Optional[List[str]] = None,
        medical_history: Optional[List[str]] = None,
        patient_age: Optional[int] = None
    ) -> TriageResult:
        """
        Executes two-stage triage evaluation:
        Stage 1: Deterministic Red-Flag Interceptor (Zero-Override Rule Gate)
        Stage 2: LLM Classification for Non-Emergencies (Urgent vs Routine)
        """
        associated_symptoms = associated_symptoms or []
        medical_history = medical_history or []

        combined_text = f"{chief_complaint} {' '.join(associated_symptoms)} {' '.join(medical_history)}".lower()
        sanitized_input = sanitize_patient_text(combined_text)

        # -------------------------------------------------------------
        # STAGE 1: DETERMINISTIC RED-FLAG GATE (CANNOT BE OVERRIDDEN)
        # -------------------------------------------------------------
        for rule in RED_FLAG_RULES:
            matched_kw = [kw for kw in rule["keywords"] if kw in sanitized_input]
            if matched_kw and severity_scale >= rule["min_severity"]:
                return TriageResult(
                    urgency_tier="EMERGENCY",
                    is_emergency=True,
                    red_flag_triggered=True,
                    red_flag_name=rule["name"],
                    confidence_score=1.0,
                    clinical_reasoning=f"DETERMINISTIC RED FLAG: Matches critical indicators ({', '.join(matched_kw)}) for {rule['name']}. Immediate life-threat risk.",
                    recommended_timeframe="Immediate (0 - 15 minutes)",
                    recommended_specialty=rule["specialty"],
                    patient_guidance_ur="⚠️ EMERGENCY ALERT: Yeh alamat shadeed khatarnak ho sakti hain. Bara-e-meherbani foran Rescue 1122 par call karein ya qareebi Emergency Room tashreef le jayen. Waqt zaya na karein!",
                    patient_guidance_en="⚠️ EMERGENCY ALERT: These symptoms indicate a potentially life-threatening emergency. Please call Rescue 1122 immediately or proceed to the nearest Emergency Department without delay!"
                )

        # -------------------------------------------------------------
        # STAGE 2: LLM EVALUATION FOR NON-EMERGENCY (URGENT VS ROUTINE)
        # -------------------------------------------------------------
        urgency, confidence, reason, rec_spec = self._classify_non_emergency(
            chief_complaint=chief_complaint,
            duration=duration,
            severity=severity_scale,
            symptoms=associated_symptoms,
            history=medical_history,
            age=patient_age
        )

        if urgency == "URGENT":
            guidance_ur = "Aap ki alamat ko jald medical jaizay ki zaroorat hai. Hum tajweez karte hain ke aglay 24 ghanton ke andar hamare clinic mein appointment book karein."
            guidance_en = "Your symptoms require prompt medical attention. We recommend scheduling an urgent consultation at City Care Clinics within the next 24 hours."
            timeframe = "Within 24 Hours (Same-Day / Next-Day)"
        else:
            guidance_ur = "Aap ki alamat routine hain. Aap apni sahulat ke mutabiq aglay 2-4 dinon mein ba-itminaan appointment book kar sakte hain."
            guidance_en = "Your condition appears routine. You may comfortably schedule an appointment at your convenience over the next 2-4 days."
            timeframe = "Routine (Within 3 - 5 Days)"

        return TriageResult(
            urgency_tier=urgency,
            is_emergency=False,
            red_flag_triggered=False,
            red_flag_name=None,
            confidence_score=confidence,
            clinical_reasoning=reason,
            recommended_timeframe=timeframe,
            recommended_specialty=rec_spec,
            patient_guidance_ur=guidance_ur,
            patient_guidance_en=guidance_en
        )

    def _classify_non_emergency(
        self,
        chief_complaint: str,
        duration: str,
        severity: int,
        symptoms: List[str],
        history: List[str],
        age: Optional[int]
    ) -> tuple[str, float, str, str]:
        """Classifies non-emergency cases into URGENT or ROUTINE."""
        # Fast rule fallback
        if severity >= 7 or any(k in chief_complaint.lower() for k in ["high fever", "tez bukhar", "severe pain", "persistent vomiting", "acute"]):
            fallback_urgency = "URGENT"
            fallback_conf = 0.88
            fallback_reason = f"High severity ({severity}/10) or acute systemic distress warrants prompt evaluation."
        else:
            fallback_urgency = "ROUTINE"
            fallback_conf = 0.90
            fallback_reason = f"Mild-to-moderate symptoms ({severity}/10) with subacute presentation appropriate for routine outpatient visit."

        # Map basic specialty
        c_lower = chief_complaint.lower()
        if any(w in c_lower for w in ["ear", "kaan", "nose", "naak", "throat", "gala", "tonsil", "ent"]):
            fallback_spec = "ENT"
        elif any(w in c_lower for w in ["skin", "jild", "acne", "kharish", "daaney", "itching", "dermatol", "patch"]) or bool(re.search(r"\brash\b", c_lower)):
            fallback_spec = "Dermatology"
        elif any(w in c_lower for w in ["bacha", "child", "infant", "pediatric"]) or (age is not None and age < 14):
            fallback_spec = "Paediatrics"
        elif any(w in c_lower for w in ["pregnancy", "hamal", "period", "menses", "gyne"]):
            fallback_spec = "Gynaecology"
        elif any(w in c_lower for w in ["heart", "bp", "palpitations", "dil"]):
            fallback_spec = "Cardiology"
        else:
            fallback_spec = "General Medicine"

        if not self.groq_key:
            return fallback_urgency, fallback_conf, fallback_reason, fallback_spec

        # LLM classification
        try:
            from groq import Groq
            client = Groq(api_key=self.groq_key)
            prompt = (
                f"Classify clinical triage urgency (URGENT vs ROUTINE).\n"
                f"- URGENT: Requires clinical assessment within 24 hours (high fever, severe pain >=7, uncontrolled vomiting, acute infection).\n"
                f"- ROUTINE: Subacute/chronic mild issues, routine checkup, skin rash, mild cough, medication refill.\n\n"
                f"Patient Details:\n"
                f"- Chief Complaint: {chief_complaint}\n"
                f"- Duration: {duration}\n"
                f"- Severity: {severity}/10\n"
                f"- Symptoms: {', '.join(symptoms)}\n"
                f"- Medical History: {', '.join(history)}\n\n"
                f"Output valid JSON with keys: urgency (URGENT or ROUTINE), confidence (float 0.7-1.0), reasoning (string), recommended_specialty (one of General Medicine, Paediatrics, Gynaecology, Cardiology, Dermatology, ENT)."
            )
            res = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are an expert clinical triage physician. Output valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            data = json.loads(res.choices[0].message.content)
            u = data.get("urgency", fallback_urgency).upper()
            if u not in ("URGENT", "ROUTINE"):
                u = fallback_urgency
            c = float(data.get("confidence", fallback_conf))
            r = data.get("reasoning", fallback_reason)
            s = data.get("recommended_specialty", fallback_spec)
            return u, c, r, s
        except Exception:
            return fallback_urgency, fallback_conf, fallback_reason, fallback_spec
