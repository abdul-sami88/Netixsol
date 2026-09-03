import sqlite3
import time
from typing import Dict, Any, List, Optional
from database import get_db_connection, init_db
DEFAULT_CRM_GUEST_EMAIL = "guest_client@realestatehub.pk"

class CRMStore:
    def __init__(self):
        init_db()

    def log_transcript(
        self,
        session_id: str,
        client_email: Optional[str],
        raw_transcript: str,
        normalized_transcript: str,
        agent_response: str,
        latency_sec: float = 0.0
    ) -> Dict[str, Any]:
        """Logs a single conversation turn (STT raw/normalized + AI response + timing) into SQLite CRM."""
        email = (client_email or DEFAULT_CRM_GUEST_EMAIL).strip()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO crm_call_transcripts (
                session_id, client_email, raw_transcript, normalized_transcript, agent_response, latency_sec
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (session_id, email, raw_transcript, normalized_transcript, agent_response, latency_sec))
        conn.commit()
        log_id = cursor.lastrowid
        conn.close()
        return {"success": True, "log_id": log_id}

    def update_client_preferences(
        self,
        client_email: Optional[str],
        memory_summary: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Saves or updates extracted client preferences (city, area, budget, bedrooms, type, purpose)."""
        email = (client_email or DEFAULT_CRM_GUEST_EMAIL).strip()
        city = memory_summary.get("city")
        area = memory_summary.get("area")
        budget = memory_summary.get("budget_pkr")
        beds = memory_summary.get("bedrooms")
        prop_type = memory_summary.get("property_type")
        purpose = memory_summary.get("purpose")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO crm_client_preferences (
                client_email, preferred_city, preferred_area, max_budget_pkr, bedrooms, property_type, purpose, last_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(client_email) DO UPDATE SET
                preferred_city = COALESCE(excluded.preferred_city, crm_client_preferences.preferred_city),
                preferred_area = COALESCE(excluded.preferred_area, crm_client_preferences.preferred_area),
                max_budget_pkr = COALESCE(excluded.max_budget_pkr, crm_client_preferences.max_budget_pkr),
                bedrooms = COALESCE(excluded.bedrooms, crm_client_preferences.bedrooms),
                property_type = COALESCE(excluded.property_type, crm_client_preferences.property_type),
                purpose = COALESCE(excluded.purpose, crm_client_preferences.purpose),
                last_updated = CURRENT_TIMESTAMP
        """, (email, city, area, budget, beds, prop_type, purpose))
        conn.commit()
        conn.close()
        return {"success": True, "email": email}

    def log_appointment_history(
        self,
        appointment_id: int,
        client_email: Optional[str],
        action_type: str,
        details: str
    ) -> Dict[str, Any]:
        """Logs an appointment status lifecycle event into appointment history audit table."""
        email = (client_email or DEFAULT_CRM_GUEST_EMAIL).strip()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO crm_appointment_history (appointment_id, client_email, action_type, details)
            VALUES (?, ?, ?, ?)
        """, (appointment_id, email, action_type, details))
        conn.commit()
        history_id = cursor.lastrowid
        conn.close()
        return {"success": True, "history_id": history_id}

    def create_followup_reminder(
        self,
        client_email: Optional[str],
        client_name: str,
        reminder_type: str,
        reminder_date: str,
        notes: str = ""
    ) -> Dict[str, Any]:
        """Creates a scheduled follow-up reminder task for sales relationship managers."""
        email = (client_email or DEFAULT_CRM_GUEST_EMAIL).strip()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO crm_followup_reminders (client_email, client_name, reminder_type, reminder_date, notes)
            VALUES (?, ?, ?, ?, ?)
        """, (email, client_name, reminder_type, reminder_date, notes))
        conn.commit()
        reminder_id = cursor.lastrowid
        conn.close()
        return {"success": True, "reminder_id": reminder_id}

    def complete_followup_reminder(self, reminder_id: int) -> Dict[str, Any]:
        """Marks a follow-up reminder task as COMPLETED."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE crm_followup_reminders SET status = 'COMPLETED' WHERE id = ?", (reminder_id,))
        conn.commit()
        conn.close()
        return {"success": True, "reminder_id": reminder_id}

    # Fetchers for API / Dashboard
    def get_transcripts(self, limit: int = 50) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM crm_call_transcripts ORDER BY id DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_preferences(self, limit: int = 50) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM crm_client_preferences ORDER BY id DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_appointment_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM crm_appointment_history ORDER BY id DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_followups(self, status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()
        if status:
            cursor.execute("SELECT * FROM crm_followup_reminders WHERE status = ? ORDER BY id DESC LIMIT ?", (status, limit))
        else:
            cursor.execute("SELECT * FROM crm_followup_reminders ORDER BY id DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

crm_store = CRMStore()
