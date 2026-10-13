"""
Automated Follow-up Scheduler for City Care Clinics.
Implements Week 9 Day 4 Task 4:
- Automated follow-up messages on a clinical schedule:
  1. Day +1 Post-visit medication adherence check-in
  2. Day +3 Symptom progression & recovery check
  3. Day +7 Clinic re-visit / Doctor review reminder
- Multi-channel delivery: Email (live SMTP) + Simulated WhatsApp / SMS
- Persistent JSON queue & APScheduler background executor
"""

import os
import json
import uuid
from datetime import datetime, timedelta, date
from pathlib import Path
from typing import Dict, Any, List, Optional
from apscheduler.schedulers.background import BackgroundScheduler

from src.channels.email_channel import send_followup_reminder_email
from src.mcp_servers.notifications_server import send_whatsapp, send_sms

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SCHEDULE_FILE = PROJECT_ROOT / "data" / "scheduled_reminders.json"
DEFAULT_EMAIL = os.getenv("DEFAULT_RECIPIENT_EMAIL", "samiworkspace11@gmail.com")


class FollowUpScheduler:
    """Manages scheduled clinical reminders for patients across care milestones."""

    def __init__(self, storage_path: Optional[Path] = None):
        self.file_path = storage_path or SCHEDULE_FILE
        self._ensure_storage()
        self.scheduler = BackgroundScheduler(daemon=True)
        if not self.scheduler.running:
            self.scheduler.start()

    def shutdown(self):
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)

    def _ensure_storage(self):
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump([], f)

    def _load_reminders(self) -> List[Dict[str, Any]]:
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _save_reminders(self, items: List[Dict[str, Any]]):
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2)

    def schedule_patient_care_plan(
        self,
        patient_id: str,
        patient_name: str,
        doctor_name: str,
        prescribed_medications: Optional[List[Dict[str, Any]]] = None,
        recipient_email: str = DEFAULT_EMAIL,
        patient_phone: str = "+92-300-1234567"
    ) -> List[Dict[str, Any]]:
        """
        Schedules standard 3-stage clinical follow-up milestones for a patient:
        - Milestone 1: +1 Day (Medicine intake & adherence check)
        - Milestone 2: +3 Days (Symptom recovery evaluation)
        - Milestone 3: +7 Days (Doctor follow-up visit reminder)
        """
        today = date.today()
        reminders = self._load_reminders()
        new_jobs = []

        milestones = [
            {
                "offset_days": 1,
                "title": "Day 1 Medication Adherence Check",
                "instructions": "Assalam-o-Alaikum! Umeed hai aap theek hain. Kya aap ne doctor sahab ki batai hui hidayat ke mutabiq subah ki dawa li hai?",
                "channel": "email"
            },
            {
                "offset_days": 3,
                "title": "Day 3 Recovery & Symptom Check",
                "instructions": "Kya aap ki tabiyat mein behtari aayi hai? Agar bukhar ya takleef barqarar hai, to foran clinic se rujoo karein.",
                "channel": "email"
            },
            {
                "offset_days": 7,
                "title": "Day 7 Clinic Follow-Up Checkup",
                "instructions": f"Aap ka {doctor_name} ke sath 7-day follow-up checkup scheduled hai. Bara-e-meherbani clinic visit confirm karein.",
                "channel": "email"
            }
        ]

        for m in milestones:
            due_d = (today + timedelta(days=m["offset_days"])).strftime("%Y-%m-%d")
            job_id = f"REM-{patient_id[:8]}-{uuid.uuid4().hex[:6]}"
            job_record = {
                "reminder_id": job_id,
                "patient_id": patient_id,
                "patient_name": patient_name,
                "doctor_name": doctor_name,
                "title": m["title"],
                "instructions": m["instructions"],
                "due_date": due_d,
                "recipient_email": recipient_email,
                "patient_phone": patient_phone,
                "status": "SCHEDULED",
                "created_at": datetime.utcnow().isoformat()
            }
            reminders.append(job_record)
            new_jobs.append(job_record)

        self._save_reminders(reminders)
        return new_jobs

    def trigger_due_reminders(self, force_all_pending: bool = False) -> List[Dict[str, Any]]:
        """
        Processes and dispatches reminders whose due_date has arrived.
        If force_all_pending=True, dispatches all active SCHEDULED reminders immediately for testing.
        """
        reminders = self._load_reminders()
        today_str = date.today().strftime("%Y-%m-%d")
        dispatched = []

        for r in reminders:
            if r.get("status") == "SCHEDULED":
                if force_all_pending or r.get("due_date") <= today_str:
                    # Dispatch Email
                    res = send_followup_reminder_email(
                        patient_name=r["patient_name"],
                        doctor_name=r["doctor_name"],
                        reminder_title=r["title"],
                        instructions=r["instructions"],
                        recipient_email=r.get("recipient_email", DEFAULT_EMAIL)
                    )
                    # Also log simulated WhatsApp/SMS
                    send_whatsapp(
                        phone_number=r.get("patient_phone", "+92-300-1234567"),
                        message=f"City Care Clinics Reminder: {r['title']} - {r['instructions']}"
                    )

                    r["status"] = "DISPATCHED"
                    r["dispatched_at"] = datetime.utcnow().isoformat()
                    r["delivery_result"] = res.get("status", "sent")
                    dispatched.append(r)

        if dispatched:
            self._save_reminders(reminders)

        return dispatched

    def get_all_reminders(self) -> List[Dict[str, Any]]:
        return self._load_reminders()
