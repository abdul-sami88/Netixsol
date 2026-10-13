"""
Intake Agent for City Care Clinics.
Collects patient intake information through natural, empathetic conversation:
- Asks ONE question at a time (never an overwhelming form).
- Bilingual: UrduLish (conversational Roman Urdu) and English.
- Captures:
  1. Patient relationship (self, child, parent, spouse)
  2. Chief complaint
  3. Duration
  4. Severity (1–10)
  5. Associated symptoms
  6. Documented allergies
  7. Current medications
  8. Relevant medical history (Diabetes, BP, Pregnancy, etc.)
- Sanitizes PII before cloud processing.
- Returns structured JSON IntakeForm upon completion.
"""

import os
import json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from src.privacy.pii_anonymizer import sanitize_patient_text


class IntakeForm(BaseModel):
    patient_relationship: str = Field(..., description="Who the patient is: self, child, parent, spouse, etc.")
    patient_name: Optional[str] = Field(default=None, description="Patient's legal full name")
    patient_phone: Optional[str] = Field(default=None, description="Patient's contact mobile number")
    patient_cnic: Optional[str] = Field(default=None, description="Patient's National Identity Card (CNIC)")
    chief_complaint: str = Field(..., description="Primary reason for visit / main symptom")
    duration: str = Field(..., description="How long the symptom has been present")
    severity_scale: int = Field(..., ge=1, le=10, description="Pain or discomfort severity from 1 to 10")
    associated_symptoms: List[str] = Field(default_factory=list, description="Other symptoms reported")
    allergies: List[str] = Field(default_factory=list, description="Documented drug or environmental allergies")
    current_medications: List[str] = Field(default_factory=list, description="Current medicines being taken")
    medical_history: List[str] = Field(default_factory=list, description="Chronic conditions or pregnancy")
    is_complete: bool = Field(default=False, description="Whether all intake fields have been captured")


class IntakeAgent:
    """
    Turn-by-turn conversational intake manager.
    Tracks dialogue state and determines the next single question to ask.
    """

    INTAKE_QUESTIONS = [
        {
            "field": "patient_relationship",
            "prompt_ur": "Assalam-o-Alaikum! City Care Clinics mein khushamdeed. Yeh appointment aap apne liye book kar rahe hain ya kisi bache, walidain ya ghar ke fard ke liye?",
            "prompt_en": "Welcome to City Care Clinics. Are you booking this appointment for yourself or for a child, parent, or family member?"
        },
        {
            "field": "patient_name",
            "prompt_ur": "Bara-e-meherbani mareez (patient) ka mukammal naam bata dein?",
            "prompt_en": "Please share the patient's full name for the clinic records?"
        },
        {
            "field": "patient_phone",
            "prompt_ur": "Booking confirmation aur clinic records ke liye apna mobile number ya CNIC number (maslan 03xx-xxxxxxx ya 35201-xxxxxxx-x) share karein?",
            "prompt_en": "Please provide your contact mobile number or CNIC (e.g. 03xx-xxxxxxx or 35201-xxxxxxx-x) for clinic records and confirmation?"
        },
        {
            "field": "chief_complaint",
            "prompt_ur": "Meherbani farma kar batayen ke patient ko kya takleef hai ya kya masla pesh aa raha hai?",
            "prompt_en": "Please tell me what main symptoms or health concern the patient is experiencing?"
        },
        {
            "field": "duration",
            "prompt_ur": "Yeh takleef kab se hai? Kitne din ya ghanton se yeh masla shuru hua?",
            "prompt_en": "How long have you had this issue? How many days or hours ago did it begin?"
        },
        {
            "field": "severity_scale",
            "prompt_ur": "1 se 10 ke paimanay par aap is dard ya takleef ki shiddat kitni mehsoos kar rahe hain (1 ka matlab halka, 10 shadeed tareen)?",
            "prompt_en": "On a scale of 1 to 10, how severe is the pain or discomfort (1 being very mild, 10 being unbearable)?"
        },
        {
            "field": "associated_symptoms",
            "prompt_ur": "Kya is ke saath koi aur alamat bhi hain? Maslan bukhar, ulti, chakkar, ya khansi?",
            "prompt_en": "Are there any other associated symptoms, such as fever, nausea, dizziness, or cough?"
        },
        {
            "field": "allergies",
            "prompt_ur": "Kya patient ko kisi dawa (maslan Penicillin ya Sulfa) ya cheez se koi allergy hai?",
            "prompt_en": "Does the patient have any known allergies to medicines (e.g. Penicillin, Sulfa) or foods?"
        },
        {
            "field": "current_medications",
            "prompt_ur": "Kya patient pehle se koi rozana ki dawa le rahe hain? Agar haan, to unke naam bata dein.",
            "prompt_en": "Is the patient currently taking any daily medicines? If so, please share their names."
        },
        {
            "field": "medical_history",
            "prompt_ur": "Kya patient ko pehle se koi bimari hai, maslan Sugar (Diabetes), Blood Pressure, ya hamal (pregnancy)?",
            "prompt_en": "Does the patient have any chronic medical history, such as Diabetes, Blood Pressure, or Pregnancy?"
        }
    ]

    def __init__(self):
        self.groq_key = os.getenv("GROQ_API_KEY")

    def process_turn(
        self,
        current_state: Dict[str, Any],
        user_message: str
    ) -> Dict[str, Any]:
        """
        Processes one conversational user turn:
        1. Scrubs PII from user_message.
        2. Strictly answers the currently asked question (or extracts multiple fields).
        3. Advances to the next unanswered question without repeating.
        4. If all questions answered, marks is_complete=True.
        """
        import re
        state = dict(current_state) if current_state else {}

        # Extract raw CNIC and Pakistani mobile number before PII scrubbing
        m_cnic = re.search(r"(\b\d{5}[- ]?\d{7}[- ]?\d{1}\b)", user_message)
        m_phone = re.search(r"(\+?92[- ]?3\d{2}[- ]?\d{7}|03\d{2}[- ]?\d{7}|\b03\d{9}\b|\b\d{10,11}\b)", user_message)
        if m_cnic:
            state["patient_cnic"] = m_cnic.group(1).replace(" ", "-")
            if not state.get("patient_phone"):
                state["patient_phone"] = state["patient_cnic"]
        if m_phone:
            state["patient_phone"] = m_phone.group(1).replace(" ", "")

        sanitized_input = sanitize_patient_text(user_message)

        # 1. Update state using extraction
        updated_state = self._extract_intake_fields(state, sanitized_input, raw_message=user_message)

        # 2. Find next unanswered question
        next_q_obj = None
        next_idx = None
        for idx, q in enumerate(self.INTAKE_QUESTIONS):
            field = q["field"]
            val = updated_state.get(field)
            if val is None or val == "" or val == []:
                next_q_obj = q
                next_idx = idx
                break

        if next_q_obj is not None:
            updated_state["_question_idx"] = next_idx
            is_complete = False
            response_message = next_q_obj["prompt_ur"]
            next_ur = next_q_obj["prompt_ur"]
            next_en = next_q_obj["prompt_en"]
        else:
            updated_state["_question_idx"] = len(self.INTAKE_QUESTIONS)
            is_complete = True
            next_ur = None
            next_en = None
            response_message = "Shukriya! Aap ki tamam zaroori tafseelat record ho chuki hain. Ab hamara Triage Agent aap ki alamat ka jaiza le raha hai."

        return {
            "is_complete": is_complete,
            "next_question_urdulish": next_ur,
            "next_question_english": next_en,
            "response_message": response_message,
            "intake_state": updated_state
        }

    def _extract_intake_fields(
        self,
        existing_state: Dict[str, Any],
        user_input: str,
        raw_message: str = ""
    ) -> Dict[str, Any]:
        """
        Extracts information from user input using Llama-3.3-70B on Groq
        with a deterministic fallback.
        """
        state = dict(existing_state)
        curr_idx = state.get("_question_idx", 0)
        expected_field = self.INTAKE_QUESTIONS[curr_idx]["field"] if curr_idx < len(self.INTAKE_QUESTIONS) else None

        val_lower = user_input.lower().strip()
        raw_val_lower = (raw_message or user_input).lower().strip()
        is_denial = any(w in val_lower for w in [
            "nhi", "nahi", "nahin", "ni ", " ni", "koi nahi", "koi ni", "kuch nahi", 
            "kuch ni", "na ", " no", "no ", "none", "denied", "koi dawa ni", "koi masla ni"
        ])

        # 1. First attempt Groq LLM extraction using active Groq model
        if self.groq_key:
            try:
                from groq import Groq
                client = Groq(api_key=self.groq_key)
                prompt = (
                    f"Extract patient intake clinical details from user message.\n"
                    f"Currently asked question is for field: {expected_field}\n"
                    f"User message: \"{user_input}\"\n\n"
                    f"Return a JSON object updating any fields mentioned:\n"
                    f"- patient_relationship (e.g. 'self', 'child', 'mother', 'father')\n"
                    f"- patient_name (full name string, e.g. 'Ali Khan')\n"
                    f"- patient_phone (mobile number, e.g. '0300-1234567')\n"
                    f"- chief_complaint (e.g. 'fever', 'headache', 'chest pain')\n"
                    f"- duration (e.g. '2 days', '1 week')\n"
                    f"- severity_scale (integer 1-10)\n"
                    f"- associated_symptoms (list of strings, e.g. ['cough', 'nausea'])\n"
                    f"- allergies (list of strings, or ['None / Denied'] if denied/none)\n"
                    f"- current_medications (list of strings, or ['None / Denied'] if denied/none)\n"
                    f"- medical_history (list of strings, or ['None / Denied'] if denied/none)\n"
                )
                res = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "You are a clinical data extraction assistant. Return valid JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.0,
                    response_format={"type": "json_object"}
                )
                parsed = json.loads(res.choices[0].message.content)
                for k, v in parsed.items():
                    if v is not None and v != "":
                        # Never let redaction markers overwrite real values
                        if k in ("patient_phone", "patient_cnic") and any(r in str(v) for r in ["[CNIC_REDACTED]", "[PHONE_REDACTED]"]):
                            continue
                        if k in ("allergies", "current_medications", "medical_history", "associated_symptoms"):
                            if v in ([], ["none"], ["None"], "none", "None", ["None / Denied"]):
                                state[k] = ["None / Denied"]
                            elif isinstance(v, list):
                                state[k] = v
                            else:
                                state[k] = [str(v)]
                        else:
                            state[k] = v
            except Exception:
                pass

        # 2. Strict Deterministic Fallback for expected_field to guarantee advancement
        if expected_field and (expected_field not in state or state[expected_field] is None or state[expected_field] == []):
            if expected_field == "patient_relationship":
                if any(w in val_lower for w in ["apne", "mera", "self", "me"]):
                    state["patient_relationship"] = "self"
                elif any(w in val_lower for w in ["bacha", "child", "beta", "beti", "son", "daughter"]):
                    state["patient_relationship"] = "child"
                elif any(w in val_lower for w in ["walid", "walida", "mother", "father", "parent"]):
                    state["patient_relationship"] = "parent"
                elif any(w in val_lower for w in ["ghar", "fard", "family", "relative"]):
                    state["patient_relationship"] = "family member"
                else:
                    state["patient_relationship"] = (raw_message or user_input).strip()
            elif expected_field == "patient_name":
                src_name = raw_message.strip() if raw_message else user_input.strip()
                clean_name = src_name
                for prefix in ["mera naam", "patient ka naam", "name is", "naam", "patient is"]:
                    if clean_name.lower().startswith(prefix):
                        clean_name = clean_name[len(prefix):].replace("hai", "").replace("is", "").strip(": ").strip()
                state["patient_name"] = clean_name if clean_name else src_name
            elif expected_field == "patient_phone":
                import re
                src_text = raw_message if raw_message else user_input
                m_cnic = re.search(r"(\b\d{5}[- ]?\d{7}[- ]?\d{1}\b)", src_text)
                m_phone = re.search(r"(\+?92[- ]?3\d{2}[- ]?\d{7}|03\d{2}[- ]?\d{7}|\b03\d{9}\b|\b\d{10,11}\b)", src_text)
                if m_cnic:
                    state["patient_cnic"] = m_cnic.group(1).replace(" ", "-")
                if m_phone:
                    state["patient_phone"] = m_phone.group(1)
                elif m_cnic:
                    state["patient_phone"] = state["patient_cnic"]
                elif not any(r in user_input for r in ["[CNIC_REDACTED]", "[PHONE_REDACTED]"]):
                    state["patient_phone"] = user_input.strip()
            elif expected_field == "severity_scale":
                import re
                m = re.search(r"\b([1-9]|10)\b", val_lower)
                state["severity_scale"] = int(m.group(1)) if m else 5
            elif expected_field in ("allergies", "current_medications", "medical_history", "associated_symptoms"):
                if is_denial:
                    state[expected_field] = ["None / Denied"]
                else:
                    src_meds = raw_message if raw_message else user_input
                    state[expected_field] = [s.strip() for s in src_meds.split(",") if s.strip()]
            else:
                state[expected_field] = (raw_message or user_input).strip()

        return state

