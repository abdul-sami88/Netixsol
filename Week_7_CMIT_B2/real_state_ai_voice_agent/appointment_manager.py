import sqlite3
import json
import time
from typing import Dict, Any, List, Optional
from database import get_db_connection, get_agent_by_city
from calendar_service import calendar_service
from email_service import email_service, HARDCODED_RECEIVER_EMAIL
from crm_store import crm_store

class AppointmentManager:
    def __init__(self):
        pass

    def book_appointment(
        self,
        session_id: str,
        client_name: str = "Valued Client",
        client_email: str = HARDCODED_RECEIVER_EMAIL,
        client_phone: str = "Email Priority Client",
        city: str = "Lahore",
        property_title: str = "General Real Estate Consultation",
        appointment_date: str = "Tomorrow",
        appointment_time: str = "11:00 AM",
        notes: str = "Site visit & investment consultation."
    ) -> Dict[str, Any]:
        """
        Books an appointment:
        1. Saves appointment record in SQLite database.
        2. Creates event in Google Calendar.
        3. Sends 2 automated emails (Client + Manager) to HARDCODED_RECEIVER_EMAIL with Add to Calendar URL button.
        4. Logs event into CRM Appointment History and creates automatic Follow-up Reminder!
        """
        target_email = client_email.strip() if (client_email and "@" in client_email) else HARDCODED_RECEIVER_EMAIL
        agent = get_agent_by_city(city)
        employee_name = agent["name"]
        employee_email = HARDCODED_RECEIVER_EMAIL

        # 1. Google Calendar Integration
        cal_res = calendar_service.create_event(
            client_name=client_name,
            client_email=target_email,
            client_phone=client_phone,
            employee_name=employee_name,
            employee_email=employee_email,
            property_title=property_title,
            date_str=appointment_date,
            time_str=appointment_time,
            meeting_notes=notes
        )
        cal_event_id = cal_res.get("event_id", "")

        # 2. Email Automation (2 Emails: Client + Manager)
        email_res = email_service.send_appointment_notification(
            action_type="BOOKING",
            client_name=client_name,
            client_email=target_email,
            client_phone=client_phone,
            employee_name=employee_name,
            employee_email=employee_email,
            property_title=property_title,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            requirements_summary=f"City: {city} | Property: {property_title} | Notes: {notes}"
        )

        # 3. Save to SQLite Database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO appointments (
                session_id, client_name, client_phone, client_email,
                employee_name, employee_email, property_title,
                appointment_date, appointment_time, status, calendar_event_id, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id, client_name, client_phone, target_email,
            employee_name, employee_email, property_title,
            appointment_date, appointment_time, 'BOOKED', cal_event_id, notes
        ))
        conn.commit()
        appointment_id = cursor.lastrowid
        conn.close()

        # 4. CRM Store Audit & Automatic Follow-up Reminder Generation
        crm_store.log_appointment_history(
            appointment_id=appointment_id,
            client_email=target_email,
            action_type="BOOKING",
            details=f"Booked visit for {property_title} on {appointment_date} at {appointment_time}"
        )
        
        crm_store.create_followup_reminder(
            client_email=target_email,
            client_name=client_name,
            reminder_type="Pre-Visit Call Reminder",
            reminder_date=appointment_date,
            notes=f"Call client to confirm arrival for {property_title} visit."
        )

        print(f"[Appointment Manager] Booked Appointment ID {appointment_id} & Logged into CRM Store.")

        return {
            "success": True,
            "appointment_id": appointment_id,
            "status": "BOOKED",
            "client_name": client_name,
            "client_email": target_email,
            "employee_name": employee_name,
            "employee_email": employee_email,
            "property_title": property_title,
            "appointment_date": appointment_date,
            "appointment_time": appointment_time,
            "calendar_result": cal_res,
            "email_result": email_res
        }

    def reschedule_appointment(
        self,
        appointment_id: int,
        new_date: str,
        new_time: str
    ) -> Dict[str, Any]:
        """Reschedules an appointment, updates Calendar, sends 2 emails, logs CRM audit event & updates follow-up reminder."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM appointments WHERE id = ?", (appointment_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return {"success": False, "error": f"Appointment ID {appointment_id} not found."}

        app_data = dict(row)
        cursor.execute("""
            UPDATE appointments 
            SET appointment_date = ?, appointment_time = ?, status = 'RESCHEDULED'
            WHERE id = ?
        """, (new_date, new_time, appointment_id))
        conn.commit()
        conn.close()

        # Update Calendar
        cal_res = calendar_service.update_event(
            event_id=app_data.get("calendar_event_id", ""),
            new_date_str=new_date,
            new_time_str=new_time,
            client_name=app_data["client_name"],
            property_title=app_data["property_title"]
        )

        # Send Email Notification (2 Emails)
        email_res = email_service.send_appointment_notification(
            action_type="RESCHEDULING",
            client_name=app_data["client_name"],
            client_email=HARDCODED_RECEIVER_EMAIL,
            client_phone=app_data["client_phone"],
            employee_name=app_data["employee_name"],
            employee_email=HARDCODED_RECEIVER_EMAIL,
            property_title=app_data["property_title"],
            appointment_date=new_date,
            appointment_time=new_time,
            requirements_summary=f"Rescheduled meeting to {new_date} at {new_time}"
        )

        # CRM Logging
        crm_store.log_appointment_history(
            appointment_id=appointment_id,
            client_email=app_data["client_email"],
            action_type="RESCHEDULING",
            details=f"Rescheduled meeting to {new_date} at {new_time}"
        )
        crm_store.create_followup_reminder(
            client_email=app_data["client_email"],
            client_name=app_data["client_name"],
            reminder_type="Rescheduled Visit Follow-up",
            reminder_date=new_date,
            notes=f"Verify rescheduled site visit for {app_data['property_title']}."
        )

        return {
            "success": True,
            "appointment_id": appointment_id,
            "status": "RESCHEDULED",
            "new_date": new_date,
            "new_time": new_time,
            "calendar_result": cal_res,
            "email_result": email_res
        }

    def cancel_appointment(self, appointment_id: int) -> Dict[str, Any]:
        """Cancels an appointment, updates Calendar, sends 2 emails, and logs CRM cancellation event."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM appointments WHERE id = ?", (appointment_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return {"success": False, "error": f"Appointment ID {appointment_id} not found."}

        app_data = dict(row)
        cursor.execute("UPDATE appointments SET status = 'CANCELLED' WHERE id = ?", (appointment_id,))
        conn.commit()
        conn.close()

        # Cancel Calendar event
        cal_res = calendar_service.cancel_event(app_data.get("calendar_event_id", ""))

        # Send Cancellation Email (2 Emails)
        email_res = email_service.send_appointment_notification(
            action_type="CANCELLATION",
            client_name=app_data["client_name"],
            client_email=HARDCODED_RECEIVER_EMAIL,
            client_phone=app_data["client_phone"],
            employee_name=app_data["employee_name"],
            employee_email=HARDCODED_RECEIVER_EMAIL,
            property_title=app_data["property_title"],
            appointment_date=app_data["appointment_date"],
            appointment_time=app_data["appointment_time"],
            requirements_summary="Appointment cancelled as per client request."
        )

        # CRM Logging
        crm_store.log_appointment_history(
            appointment_id=appointment_id,
            client_email=app_data["client_email"],
            action_type="CANCELLATION",
            details="Appointment cancelled by client."
        )

        return {
            "success": True,
            "appointment_id": appointment_id,
            "status": "CANCELLED",
            "calendar_result": cal_res,
            "email_result": email_res
        }

    def list_appointments(self, limit: int = 20) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM appointments ORDER BY id DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_latest_appointment_for_session(self, session_id: str, client_email: Optional[str] = None) -> Optional[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()
        if client_email and "@" in client_email:
            cursor.execute("""
                SELECT * FROM appointments 
                WHERE (session_id = ? OR client_email = ?) AND status != 'CANCELLED'
                ORDER BY id DESC LIMIT 1
            """, (session_id, client_email.strip()))
        else:
            cursor.execute("""
                SELECT * FROM appointments 
                WHERE session_id = ? AND status != 'CANCELLED'
                ORDER BY id DESC LIMIT 1
            """, (session_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

appointment_manager = AppointmentManager()
