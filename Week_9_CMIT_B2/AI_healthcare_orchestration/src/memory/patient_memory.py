"""
Privacy-Conscious Patient Memory Module.
Implements:
1. Short-Term Memory: Thread-based conversational memory via LangGraph Checkpointer.
2. Long-Term Patient Memory: Cross-visit persistence for preferences and clinical continuity:
   - Preferred Doctor & Branch
   - Preferred Language (UrduLish / English)
   - Past Summarized Complaints & Visit History
   - Chronic Conditions & Confirmed Allergies
3. Privacy Safeguard: Stores ONLY clinically necessary data; strips raw direct PII.
4. Returning Patient Recognition & Personalized UrduLish Greeting.
"""

import json
from pathlib import Path
from datetime import datetime, date
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from src.privacy.pii_anonymizer import sanitize_patient_text

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MEMORY_DIR = PROJECT_ROOT / "data"
MEMORY_FILE = MEMORY_DIR / "patient_memory_store.json"


class PatientProfileMemory(BaseModel):
    patient_id: str
    preferred_language: str = Field(default="UrduLish")
    preferred_doctor_id: Optional[str] = None
    preferred_doctor_name: Optional[str] = None
    preferred_branch: Optional[str] = None
    last_visit_date: Optional[str] = None
    last_complaint_summary: Optional[str] = None
    past_encounters_count: int = Field(default=0)
    confirmed_allergies: List[str] = Field(default_factory=list)
    chronic_conditions: List[str] = Field(default_factory=list)
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


try:
    from src.database.connection import db_session
    from src.database.models import PatientAgentMemory, Patient, Condition, MedicationRequest, Appointment
    DB_AVAILABLE = True
except Exception:
    DB_AVAILABLE = False


class PatientMemoryManager:
    """
    Manages cross-visit patient memory for City Care Clinics.
    Architecture:
    - Primary Store: Production PostgreSQL table `patient_agent_memories` (Indexed, ACID-safe)
    - Fallback Store: Local `data/patient_memory_store.json` (Offline/dev fallback)
    - Privacy Enforcement: Zero raw CNIC, phones, or chat logs retained.
    """

    def __init__(self, memory_file_path: Optional[Path] = None):
        self.file_path = memory_file_path or MEMORY_FILE
        self._ensure_store()

    def _ensure_store(self):
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump({}, f)

    def _load_all(self) -> Dict[str, Dict[str, Any]]:
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_all(self, data: Dict[str, Dict[str, Any]]):
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def get_memory(self, patient_id: str) -> Optional[PatientProfileMemory]:
        """
        Retrieves long-term memory for a given patient.
        Attempts PostgreSQL lookup first; falls back to JSON file.
        """
        # 1. Primary PostgreSQL lookup
        if DB_AVAILABLE:
            try:
                session = db_session()
                record = session.query(PatientAgentMemory).filter_by(patient_id=patient_id).first()
                if record:
                    allergies = json.loads(record.confirmed_allergies) if record.confirmed_allergies else []
                    conditions = json.loads(record.chronic_conditions) if record.chronic_conditions else []
                    mem = PatientProfileMemory(
                        patient_id=record.patient_id,
                        preferred_language=record.preferred_language or "UrduLish",
                        preferred_doctor_id=record.preferred_doctor_id,
                        preferred_doctor_name=record.preferred_doctor_name,
                        preferred_branch=record.preferred_branch,
                        last_visit_date=record.last_visit_date,
                        last_complaint_summary=record.last_complaint_summary,
                        past_encounters_count=record.past_encounters_count or 0,
                        confirmed_allergies=allergies,
                        chronic_conditions=conditions,
                        updated_at=record.updated_at.isoformat() if record.updated_at else datetime.utcnow().isoformat()
                    )
                    session.close()
                    return mem
                session.close()
            except Exception:
                pass

        # 2. Local JSON fallback
        all_data = self._load_all()
        if patient_id in all_data:
            return PatientProfileMemory(**all_data[patient_id])
        return None

    def lookup_patient_by_identifier(self, identifier: str) -> Optional[Dict[str, Any]]:
        """
        Looks up a registered patient by CNIC or Phone number in PostgreSQL.
        If found, retrieves:
        - Demographic records (ID, Name, CNIC, Phone, Gender, DOB, Blood Group)
        - Long-Term Agent Memory (visit count, last doctor, preferred branch)
        - Verified active allergies from Condition table
        - Chronic conditions from Condition table
        - Active prescriptions from MedicationRequest table
        """
        if not identifier or not DB_AVAILABLE:
            return None

        clean_val = identifier.strip().replace(" ", "").replace("-", "")
        if not clean_val or len(clean_val) < 5:
            return None

        session = db_session()
        try:
            # 1. Exact match by CNIC or Phone
            pat = session.query(Patient).filter(
                (Patient.cnic == identifier.strip()) | 
                (Patient.phone == identifier.strip())
            ).first()

            # 2. Match sanitized digits if direct match not found
            if not pat:
                candidates = session.query(Patient).all()
                for c in candidates:
                    c_cnic = c.cnic.replace("-", "").replace(" ", "") if c.cnic else ""
                    c_phone = c.phone.replace("-", "").replace(" ", "").replace("+92", "0") if c.phone else ""
                    clean_target = clean_val.replace("+92", "0")
                    if (c_cnic and (c_cnic == clean_val or clean_val in c_cnic)) or \
                       (c_phone and (c_phone == clean_target or clean_target in c_phone)):
                        pat = c
                        break

            if not pat:
                return None

            # Retrieve long-term memory
            mem = self.get_memory(pat.id)

            # Retrieve documented allergies & chronic conditions from EHR
            conds = session.query(Condition).filter_by(patient_id=pat.id, clinical_status="active").all()
            allergies = [c.code_display for c in conds if c.category == "allergy_intolerance"]
            chronic_conds = [c.code_display for c in conds if c.category == "chronic_disease"]

            if mem:
                if mem.confirmed_allergies:
                    allergies = list(set(allergies + mem.confirmed_allergies))
                if mem.chronic_conditions:
                    chronic_conds = list(set(chronic_conds + mem.chronic_conditions))

            # Retrieve active medications
            rxs = session.query(MedicationRequest).filter_by(patient_id=pat.id, status="active").all()
            active_meds = [r.brand_name or r.medication_name for r in rxs]

            # Last encounter details
            last_appt = session.query(Appointment).filter_by(patient_id=pat.id).order_by(Appointment.start_time.desc()).first()
            last_doc = None
            last_date = None
            last_branch = None
            if last_appt and last_appt.practitioner:
                last_doc = last_appt.practitioner.full_name
                last_date = last_appt.start_time.strftime("%Y-%m-%d") if last_appt.start_time else None
                last_branch = last_appt.branch.name if last_appt.branch else None
            elif mem:
                last_doc = mem.preferred_doctor_name
                last_date = mem.last_visit_date
                last_branch = mem.preferred_branch

            return {
                "id": pat.id,
                "name": pat.full_name,
                "cnic": pat.cnic,
                "phone": pat.phone,
                "gender": pat.gender,
                "dob": str(pat.date_of_birth) if pat.date_of_birth else None,
                "blood_group": pat.blood_group,
                "city": pat.city,
                "allergies": allergies,
                "chronic_conditions": chronic_conds,
                "active_medications": active_meds,
                "last_doctor": last_doc or "Dr. Ahmad Khan",
                "last_branch": last_branch or "City Care Clinics - Main Gulberg",
                "last_visit_date": last_date or (mem.last_visit_date if mem else None),
                "past_encounters_count": mem.past_encounters_count if mem else (1 if last_appt else 0),
                "preferred_language": mem.preferred_language if mem else "UrduLish"
            }
        finally:
            session.close()

    def update_memory_after_visit(
        self,
        patient_id: str,
        doctor_name: Optional[str] = None,
        doctor_id: Optional[str] = None,
        branch_name: Optional[str] = None,
        complaint_summary: Optional[str] = None,
        language: Optional[str] = None,
        allergies: Optional[List[str]] = None,
        conditions: Optional[List[str]] = None
    ) -> PatientProfileMemory:
        """
        Updates long-term patient memory after an encounter or consultation.
        Enforces minimal data retention (no raw chat logs, only clinical continuity markers).
        Writes to PostgreSQL database and syncs local JSON cache.
        """
        existing_mem = self.get_memory(patient_id)
        encounters = (existing_mem.past_encounters_count + 1) if existing_mem else 1
        today_str = date.today().strftime("%Y-%m-%d")

        doc_name = doctor_name or (existing_mem.preferred_doctor_name if existing_mem else None)
        doc_id = doctor_id or (existing_mem.preferred_doctor_id if existing_mem else None)
        branch = branch_name or (existing_mem.preferred_branch if existing_mem else None)
        lang = language or (existing_mem.preferred_language if existing_mem else "UrduLish")
        
        # Privacy sanitization
        clean_complaint = sanitize_patient_text(complaint_summary) if complaint_summary else (
            existing_mem.last_complaint_summary if existing_mem else None
        )

        allg_set = set(existing_mem.confirmed_allergies if existing_mem else [])
        if allergies:
            allg_set.update(allergies)

        cond_set = set(existing_mem.chronic_conditions if existing_mem else [])
        if conditions:
            cond_set.update(conditions)

        allg_list = list(allg_set)
        cond_list = list(cond_set)

        mem = PatientProfileMemory(
            patient_id=patient_id,
            preferred_language=lang,
            preferred_doctor_id=doc_id,
            preferred_doctor_name=doc_name,
            preferred_branch=branch,
            last_visit_date=today_str,
            last_complaint_summary=clean_complaint,
            past_encounters_count=encounters,
            confirmed_allergies=allg_list,
            chronic_conditions=cond_list,
            updated_at=datetime.utcnow().isoformat()
        )

        # 1. Upsert into PostgreSQL table
        if DB_AVAILABLE:
            try:
                session = db_session()
                db_record = session.query(PatientAgentMemory).filter_by(patient_id=patient_id).first()
                if not db_record:
                    db_record = PatientAgentMemory(patient_id=patient_id)
                    session.add(db_record)

                db_record.preferred_language = lang
                db_record.preferred_doctor_id = doc_id
                db_record.preferred_doctor_name = doc_name
                db_record.preferred_branch = branch
                db_record.last_visit_date = today_str
                db_record.last_complaint_summary = clean_complaint
                db_record.past_encounters_count = encounters
                db_record.confirmed_allergies = json.dumps(allg_list)
                db_record.chronic_conditions = json.dumps(cond_list)
                db_record.updated_at = datetime.utcnow()
                session.commit()
                session.close()
            except Exception:
                pass

        # 2. Sync to local JSON fallback
        all_data = self._load_all()
        all_data[patient_id] = mem.model_dump()
        self._save_all(all_data)

        return mem

    def generate_returning_patient_greeting(
        self,
        patient_id: str,
        patient_name: str
    ) -> Dict[str, str]:
        """
        Generates a personalized, context-aware greeting for returning patients.
        Example: "Assalam-o-Alaikum Ahmed sahib! Pichli dafa aap Dr. Bilal ko dikhaye thay. Kya isi doctor ke saath appointment chahiye?"
        """
        mem = self.get_memory(patient_id)
        if not mem or mem.past_encounters_count == 0 or not mem.preferred_doctor_name:
            # First-time or unremembered patient
            return {
                "greeting_urdulish": f"Assalam-o-Alaikum {patient_name}! City Care Clinics mein khushamdeed. Main aap ki kya madad kar sakta hoon?",
                "greeting_english": f"Welcome to City Care Clinics, {patient_name}. How can I assist you today?",
                "is_returning_patient": False
            }

        # Returning patient with prior history
        doc = mem.preferred_doctor_name
        branch = mem.preferred_branch or "City Care Clinics"
        last_date = mem.last_visit_date or "pichli visit"

        ur_msg = (
            f"Assalam-o-Alaikum {patient_name} sahib! Welcome again..\n"
            f"Pichli dafa ({last_date}) aap {doc} ko {branch} mein dikhaye thay.\n"
            f"Kya aaj bhi aap {doc} ke saath hi appointment book karna chahte hain, ya koi naya masla hai?"
        )
        en_msg = (
            f"Welcome back, {patient_name}!\n"
            f"On your previous visit ({last_date}), you consulted with {doc} at {branch}.\n"
            f"Would you like to schedule a follow-up with {doc}, or are you visiting for a different concern?"
        )

        return {
            "greeting_urdulish": ur_msg,
            "greeting_english": en_msg,
            "is_returning_patient": True,
            "last_doctor": doc,
            "last_branch": branch,
            "last_visit_date": last_date
        }
