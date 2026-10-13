"""
Follow-up Agent for City Care Clinics.
Creates comprehensive patient care plans and reminder workflows:
1. Daily Medicine Times Schedule (Morning, Afternoon, Evening, Bedtime).
2. Diagnostic Lab Test Due Dates & Preparation Reminders.
3. Follow-up Doctor Visit Target Dates.
4. Empathetic bilingual patient messaging (WhatsApp, SMS, Email).
"""

import os
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from src.mcp_servers.notifications_server import send_email, send_whatsapp, send_sms


class ReminderPlan(BaseModel):
    patient_name: str
    doctor_name: str
    daily_medicine_schedule: Dict[str, List[str]] = Field(..., description="Schedule categorized by time of day")
    lab_test_milestones: List[Dict[str, Any]] = Field(default_factory=list, description="Scheduled lab tests")
    follow_up_visit_date: str = Field(..., description="Target date for clinic follow-up")
    whatsapp_message_ur: str = Field(..., description="UrduLish WhatsApp reminder message")
    sms_alert_ur: str = Field(..., description="Compact SMS alert")
    email_subject: str = Field(..., description="Email subject")
    email_body_text: str = Field(..., description="Full email body")


class FollowUpAgent:
    def __init__(self):
        pass

    def create_reminder_plan(
        self,
        patient_name: str,
        doctor_name: str,
        prescribed_medications: List[Dict[str, Any]],
        required_lab_tests: Optional[List[Dict[str, Any]]] = None,
        follow_up_days: int = 7,
        patient_phone: Optional[str] = None,
        patient_email: Optional[str] = None
    ) -> ReminderPlan:
        """
        Builds a comprehensive care plan and drafts patient messages.
        """
        required_lab_tests = required_lab_tests or []
        today = date.today()
        follow_up_date = (today + timedelta(days=follow_up_days)).strftime("%Y-%m-%d")

        # 1. Categorize Daily Medicine Schedule
        schedule = {
            "Subah (Morning - Nashte ke baad)": [],
            "Dopehr (Afternoon - Lunch ke baad)": [],
            "Sham (Evening / Maghrib)": [],
            "Raat (Bedtime - Sone se pehle)": []
        }

        for med in prescribed_medications:
            name = med.get("brand") or med.get("drug_name", "Medicine")
            dose = med.get("dose") or med.get("dosage_instruction", "As directed")
            timing = med.get("timing", "").lower()

            entry = f"{name} ({dose})"
            if "once daily" in timing or "morning" in timing or "subah" in timing or "breakfast" in timing:
                schedule["Subah (Morning - Nashte ke baad)"].append(entry)
            elif "twice daily" in timing or "do dafa" in timing or "12 hours" in timing:
                schedule["Subah (Morning - Nashte ke baad)"].append(entry)
                schedule["Raat (Bedtime - Sone se pehle)"].append(entry)
            elif "three times" in timing or "teen dafa" in timing:
                schedule["Subah (Morning - Nashte ke baad)"].append(entry)
                schedule["Dopehr (Afternoon - Lunch ke baad)"].append(entry)
                schedule["Raat (Bedtime - Sone se pehle)"].append(entry)
            elif "night" in timing or "bedtime" in timing or "raat" in timing:
                schedule["Raat (Bedtime - Sone se pehle)"].append(entry)
            else:
                schedule["Subah (Morning - Nashte ke baad)"].append(entry)

        # 2. Lab Test Milestones
        lab_milestones = []
        for lab in required_lab_tests:
            due_days = lab.get("due_in_days", 3)
            due_date = (today + timedelta(days=due_days)).strftime("%Y-%m-%d")
            t_name = lab.get("test_name", "Lab Test")
            prep = lab.get("prep_instruction", "10-12 ghantay ki roza/fasting zaroori hai.")
            lab_milestones.append({
                "test_name": t_name,
                "due_date": due_date,
                "preparation_urdu": prep
            })

        # 3. Draft UrduLish Messages
        med_summary_lines = []
        for time_slot, meds in schedule.items():
            if meds:
                med_summary_lines.append(f"• {time_slot}: {', '.join(meds)}")
        med_summary_text = "\n".join(med_summary_lines)

        lab_summary_lines = [
            f"• {l['test_name']}: {l['due_date']} ({l['preparation_urdu']})"
            for l in lab_milestones
        ]
        lab_summary_text = "\n".join(lab_summary_lines) if lab_summary_lines else "• Koi naya lab test tajweez nahi kiya gaya."

        whatsapp_ur = f"""
Assalam-o-Alaikum {patient_name}!
City Care Clinics ki janib se aap ka personalized health & medication reminder:

💊 Rozana Dawai Ka Schedule:
{med_summary_text}

🧪 Zaroori Lab Tests:
{lab_summary_text}

📅 Doctor Follow-Up:
{doctor_name} ke sath agla checkup {follow_up_date} ko schedule karein.

Kisi bhi takleef ya emergency ki soorat mein helpline 1122 par foran rabta karein.
City Care Clinics Support: 042-35750011
"""

        sms_ur = f"City Care Clinics: {patient_name}, aap ki dawai ka waqt ho gaya hai. Doctor {doctor_name} se follow-up {follow_up_date} ko tay hai. Help: 042-35750011"

        email_subject = f"City Care Clinics — Care Plan & Medication Schedule for {patient_name}"
        email_body = f"""
Dear {patient_name},

Thank you for visiting City Care Clinics. Below is your comprehensive care plan prescribed by {doctor_name}.

DAILY MEDICATION SCHEDULE:
{med_summary_text}

UPCOMING LAB TESTS:
{lab_summary_text}

FOLLOW-UP APPOINTMENT:
Your recommended follow-up clinic consultation is on or before: {follow_date if 'follow_date' in locals() else follow_up_date}.

For appointments or medical queries:
Phone: 042-35750011 | Emergency Helpline: 1122
"""

        plan = ReminderPlan(
            patient_name=patient_name,
            doctor_name=doctor_name,
            daily_medicine_schedule=schedule,
            lab_test_milestones=lab_milestones,
            follow_up_visit_date=follow_up_date,
            whatsapp_message_ur=whatsapp_ur.strip(),
            sms_alert_ur=sms_ur.strip(),
            email_subject=email_subject,
            email_body_text=email_body.strip()
        )

        return plan

    def dispatch_patient_reminders(
        self,
        plan: ReminderPlan,
        to_email: Optional[str] = None,
        phone_number: Optional[str] = None
    ) -> Dict[str, Any]:
        """Dispatches generated reminders via notifications MCP server."""
        email_dest = to_email or os.getenv("DEFAULT_RECIPIENT_EMAIL", "samiworkspace11@gmail.com")
        phone_dest = phone_number or "+92-300-1234567"

        res_email = send_email(subject=plan.email_subject, body_text=plan.email_body_text, to_email=email_dest)
        res_wa = send_whatsapp(phone_number=phone_dest, message=plan.whatsapp_message_ur)
        res_sms = send_sms(phone_number=phone_dest, message=plan.sms_alert_ur)

        return {
            "status": "dispatched",
            "email_status": res_email.get("status"),
            "whatsapp_status": res_wa.get("status"),
            "sms_status": res_sms.get("status")
        }
