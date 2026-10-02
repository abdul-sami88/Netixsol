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
        latency_sec: float = 0.0,
        is_converted: int = 0
    ) -> Dict[str, Any]:
        """Logs a single conversation turn (STT raw/normalized + AI response + timing) into SQLite CRM."""
        email = (client_email or DEFAULT_CRM_GUEST_EMAIL).strip()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO crm_call_transcripts (
                session_id, client_email, raw_transcript, normalized_transcript, agent_response, latency_sec, is_converted
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (session_id, email, raw_transcript, normalized_transcript, agent_response, latency_sec, is_converted))
        conn.commit()
        log_id = cursor.lastrowid
        conn.close()
        return {"success": True, "log_id": log_id}

    def update_client_preferences(
        self,
        client_email: Optional[str],
        memory_summary: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Saves or updates extracted client preferences and ML lead scoring fields."""
        email = (client_email or DEFAULT_CRM_GUEST_EMAIL).strip()
        city = memory_summary.get("city") or memory_summary.get("preferred_city")
        area = memory_summary.get("area") or memory_summary.get("preferred_area")
        budget = memory_summary.get("budget_pkr") or memory_summary.get("max_budget_pkr")
        beds = memory_summary.get("bedrooms")
        prop_type = memory_summary.get("property_type") or memory_summary.get("property_type_preferred")
        purpose = memory_summary.get("purpose")

        lead_score = memory_summary.get("lead_score_pct")
        tier = memory_summary.get("priority_tier")
        action = memory_summary.get("recommended_action")
        lead_source = memory_summary.get("lead_source")
        objection = memory_summary.get("objection_raised")
        call_dur = memory_summary.get("avg_call_duration_mins")
        num_calls = memory_summary.get("num_calls")
        resp_time = memory_summary.get("response_time_hours")
        days_contact = memory_summary.get("days_since_first_contact")
        followup_cnt = memory_summary.get("followup_count")
        v_booked = memory_summary.get("visit_booked")
        v_completed = memory_summary.get("visit_completed")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO crm_client_preferences (
                client_email, preferred_city, preferred_area, max_budget_pkr, bedrooms, property_type, purpose,
                lead_score_pct, priority_tier, recommended_action, lead_source, objection_raised,
                avg_call_duration_mins, num_calls, response_time_hours, days_since_first_contact, followup_count,
                visit_booked, visit_completed, last_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(client_email) DO UPDATE SET
                preferred_city = COALESCE(excluded.preferred_city, crm_client_preferences.preferred_city),
                preferred_area = COALESCE(excluded.preferred_area, crm_client_preferences.preferred_area),
                max_budget_pkr = COALESCE(excluded.max_budget_pkr, crm_client_preferences.max_budget_pkr),
                bedrooms = COALESCE(excluded.bedrooms, crm_client_preferences.bedrooms),
                property_type = COALESCE(excluded.property_type, crm_client_preferences.property_type),
                purpose = COALESCE(excluded.purpose, crm_client_preferences.purpose),
                lead_score_pct = COALESCE(excluded.lead_score_pct, crm_client_preferences.lead_score_pct),
                priority_tier = COALESCE(excluded.priority_tier, crm_client_preferences.priority_tier),
                recommended_action = COALESCE(excluded.recommended_action, crm_client_preferences.recommended_action),
                lead_source = COALESCE(excluded.lead_source, crm_client_preferences.lead_source),
                objection_raised = COALESCE(excluded.objection_raised, crm_client_preferences.objection_raised),
                avg_call_duration_mins = COALESCE(excluded.avg_call_duration_mins, crm_client_preferences.avg_call_duration_mins),
                num_calls = COALESCE(excluded.num_calls, crm_client_preferences.num_calls),
                response_time_hours = COALESCE(excluded.response_time_hours, crm_client_preferences.response_time_hours),
                days_since_first_contact = COALESCE(excluded.days_since_first_contact, crm_client_preferences.days_since_first_contact),
                followup_count = COALESCE(excluded.followup_count, crm_client_preferences.followup_count),
                visit_booked = COALESCE(excluded.visit_booked, crm_client_preferences.visit_booked),
                visit_completed = COALESCE(excluded.visit_completed, crm_client_preferences.visit_completed),
                last_updated = CURRENT_TIMESTAMP
        """, (
            email, city, area, budget, beds, prop_type, purpose,
            lead_score, tier, action, lead_source, objection,
            call_dur, num_calls, resp_time, days_contact, followup_cnt,
            v_booked, v_completed
        ))
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

    def mark_session_converted(self, session_id: str) -> Dict[str, Any]:
        """Marks all transcript turns for a booked session as converted (is_converted = 1)."""
        if not session_id:
            return {"success": False, "error": "session_id required"}
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE crm_call_transcripts 
            SET is_converted = 1 
            WHERE session_id = ?
        """, (session_id,))
        conn.commit()
        updated_rows = cursor.rowcount
        conn.close()
        return {"success": True, "session_id": session_id, "updated_rows": updated_rows}

    def get_converted_transcripts(self, session_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves high-converting transcripts that led to bookings."""
        conn = get_db_connection()
        cursor = conn.cursor()
        if session_id:
            cursor.execute("SELECT * FROM crm_call_transcripts WHERE session_id = ? AND is_converted = 1 ORDER BY id ASC", (session_id,))
        else:
            cursor.execute("SELECT * FROM crm_call_transcripts WHERE is_converted = 1 ORDER BY id DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

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
