"""
Scheduling Agent for City Care Clinics.
Implements:
1. Symptom -> Specialty Mapping (6 clinical specialties).
2. Doctor preference matching (Gender, Branch, Language, Consultation Fee).
3. Slot availability, anti-double-booking, and past-date protection.
4. Appointment booking, rescheduling, and cancellation.
5. Live Google Calendar synchronization and confirmation notifications.
6. Conversational UrduLish & English appointment confirmations.
"""

import sys
import os
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.mcp_servers.scheduling_server import (
    find_doctors,
    get_available_slots,
    book_appointment,
    reschedule_appointment,
    cancel_appointment
)
from src.mcp_servers.notifications_server import send_appointment_confirmation

SPECIALTY_MAPPING_RULES = [
    {
        "specialty": "Cardiology",
        "keywords": ["chest pain", "seena", "heart", "blood pressure", "hypertension", "palpitations", "dil", "cholesterol"]
    },
    {
        "specialty": "Paediatrics",
        "keywords": ["child", "bacha", "bache", "bachon", "baby", "infant", "toddler", "vaccination", "pediatric", "teething"]
    },
    {
        "specialty": "Gynaecology",
        "keywords": ["pregnancy", "hamal", "period", "menses", "gyne", "pelvic", "fertility", "antenatal", "pcos"]
    },
    {
        "specialty": "Dermatology",
        "keywords": ["skin", "jild", "acne", "rash", "daaney", "itching", "eczema", "hair fall", "dandruff", "psoriasis"]
    },
    {
        "specialty": "ENT",
        "keywords": ["ear", "kaan", "nose", "naak", "throat", "gala", "tonsil", "hearing", "sinus", "voice"]
    },
    {
        "specialty": "General Medicine",
        "keywords": ["fever", "bukhar", "diabetes", "sugar", "cough", "weakness", "indigestion", "headache", "body ache", "flu"]
    }
]


class SchedulingAgent:
    def __init__(self):
        self.groq_key = os.getenv("GROQ_API_KEY")

    def map_symptom_to_specialty(self, symptoms_or_complaint: str) -> str:
        """Maps free-text patient symptoms or complaints to an appropriate clinic specialty."""
        text = symptoms_or_complaint.lower()
        for rule in SPECIALTY_MAPPING_RULES:
            if any(k in text for k in rule["keywords"]):
                return rule["specialty"]
        return "General Medicine"

    def match_doctors(
        self,
        specialty: Optional[str] = None,
        city: Optional[str] = None,
        gender_preference: Optional[str] = None,
        branch_preference: Optional[str] = None,
        max_fee: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Searches and filters doctors based on clinical specialty and patient preferences.
        """
        doc_res = find_doctors(specialty=specialty, city=city)
        doctors = doc_res.get("doctors", [])

        filtered = []
        for d in doctors:
            # Branch filter
            if branch_preference and branch_preference.lower() not in d["branch_name"].lower():
                continue

            # Fee filter
            if max_fee and d["consultation_fee_pkr"] > max_fee:
                continue

            # Gender filter
            if gender_preference:
                g_pref = gender_preference.lower()
                female_names = ["ayesha", "hina", "fatima", "maryam", "sadia", "farzana", "shazia", "naila", "rabia", "tahira", "zainab", "sara", "mahnoor", "saira", "bushra", "nadia"]
                is_female = any(fn in d["name"].lower() for fn in female_names) or d["specialty"] == "Gynaecology"
                if g_pref == "female" and not is_female:
                    continue
                if g_pref == "male" and is_female:
                    continue

            filtered.append(d)

        return filtered

    def propose_next_available_slot(
        self,
        doctor: Dict[str, Any],
        preferred_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculates upcoming available slots for a doctor starting from today/preferred_date.
        Prevents booking in the past.
        """
        today = date.today()
        start_date = datetime.strptime(preferred_date, "%Y-%m-%d").date() if preferred_date else today

        if start_date < today:
            start_date = today

        # Search across the next 7 days
        for day_offset in range(7):
            target_date = start_date + timedelta(days=day_offset)
            target_str = target_date.strftime("%Y-%m-%d")

            slots_info = get_available_slots(doctor["doctor_id"], target_str)
            free_slots = slots_info.get("available_slots", [])

            if free_slots:
                first_slot = free_slots[0]
                day_name_ur = {
                    "Monday": "Peer", "Tuesday": "Mangal", "Wednesday": "Budh",
                    "Thursday": "Jumerat", "Friday": "Juma", "Saturday": "Hafta", "Sunday": "Itwaar"
                }.get(slots_info["day_name"], slots_info["day_name"])

                proposal_ur = (
                    f"{doctor['name']} ({doctor['specialty']}) {slots_info['day_name']} ({target_str}) "
                    f"ko {first_slot} baje {doctor['branch_name']} mein available hain. "
                    f"Consultation fee PKR {doctor['consultation_fee_pkr']} hai. Kya main yeh confirm kar doon?"
                )
                proposal_en = (
                    f"{doctor['name']} ({doctor['specialty']}) is available on {slots_info['day_name']}, {target_str} "
                    f"at {first_slot} at {doctor['branch_name']}. Fee: PKR {doctor['consultation_fee_pkr']}. "
                    f"Would you like me to confirm this booking?"
                )

                return {
                    "status": "available",
                    "doctor_id": doctor["doctor_id"],
                    "doctor_name": doctor["name"],
                    "specialty": doctor["specialty"],
                    "branch_name": doctor["branch_name"],
                    "branch_city": doctor["city"],
                    "fee_pkr": doctor["consultation_fee_pkr"],
                    "date": target_str,
                    "day_name": slots_info["day_name"],
                    "slot_time": first_slot,
                    "all_slots_on_day": free_slots,
                    "proposal_message_urdulish": proposal_ur,
                    "proposal_message_english": proposal_en
                }

        return {
            "status": "no_slots_found",
            "message": f"No clinic slots available for {doctor['name']} within the next 7 days."
        }

    def execute_booking(
        self,
        patient_id: str,
        doctor_id: str,
        date_str: str,
        slot_time: str,
        chief_complaint: str = "General Consultation",
        urgency_tier: str = "ROUTINE",
        patient_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes verified appointment booking:
        1. Ensures date is not in the past.
        2. Books slot via MCP scheduling server (prevents double-booking).
        3. Creates Google Calendar event.
        4. Sends appointment confirmation email.
        """
        try:
            appt_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return {"status": "error", "message": "Invalid date format. Use YYYY-MM-DD."}

        if appt_date < date.today():
            return {
                "status": "error",
                "message": f"Cannot book in the past. Date {date_str} has already passed. Please select an upcoming date."
            }

        # Call booking tool
        book_res = book_appointment(
            patient_id=patient_id,
            doctor_id=doctor_id,
            date_str=date_str,
            slot_time=slot_time,
            chief_complaint=chief_complaint,
            urgency_tier=urgency_tier
        )

        if book_res.get("status") != "success":
            return book_res

        # Dispatch email confirmation
        email_recipient = patient_email or os.getenv("DEFAULT_RECIPIENT_EMAIL", "samiworkspace11@gmail.com")
        send_appointment_confirmation(
            patient_name=book_res.get("patient_name", "Patient"),
            doctor_name=book_res.get("doctor_name", "Doctor"),
            specialty=book_res.get("specialty", "Specialist"),
            clinic_branch=book_res.get("branch_name", "City Care Clinics"),
            appointment_date=date_str,
            slot_time=slot_time,
            token_number=book_res.get("token_number", "CC-000"),
            to_email=email_recipient
        )

        confirm_msg_ur = (
            f"Mubarak ho! Aap ki appointment confirm ho gayi hai.\n"
            f"• Doctor: {book_res['doctor_name']} ({book_res['specialty']})\n"
            f"• Clinic: {book_res['branch_name']}\n"
            f"• Tareekh: {date_str} at {slot_time}\n"
            f"• Token Number: {book_res['token_number']}\n"
            f"Confirmation email aur Google Calendar invite bhej diya gaya hai."
        )

        book_res["confirmation_message_urdulish"] = confirm_msg_ur
        return book_res

    def execute_reschedule(self, appointment_id: str, new_date_str: str, new_slot_time: str) -> Dict[str, Any]:
        """Reschedules an active appointment."""
        try:
            appt_date = datetime.strptime(new_date_str, "%Y-%m-%d").date()
        except ValueError:
            return {"status": "error", "message": "Invalid date format. Use YYYY-MM-DD."}

        if appt_date < date.today():
            return {"status": "error", "message": "Cannot reschedule to a past date."}

        return reschedule_appointment(
            appointment_id=appointment_id,
            new_date_str=new_date_str,
            new_slot_time=new_slot_time
        )

    def execute_cancellation(self, appointment_id: str, reason: str = "Patient request") -> Dict[str, Any]:
        """Cancels an appointment and releases calendar slot."""
        return cancel_appointment(appointment_id=appointment_id, cancellation_reason=reason)
