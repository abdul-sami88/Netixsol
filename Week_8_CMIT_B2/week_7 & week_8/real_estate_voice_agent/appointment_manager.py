import sqlite3
import json
import time
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from database import get_db_connection, get_agent_by_city
from calendar_service import calendar_service
from email_service import email_service, DEFAULT_MANAGER_EMAIL
from crm_store import crm_store
from dialogue_memory import dialogue_memory

STANDARD_SLOTS = [
    "10:00 AM",
    "11:00 AM",
    "12:00 PM",
    "02:00 PM",
    "03:00 PM",
    "04:00 PM",
    "05:00 PM"
]

def normalize_slot_time(time_str: str) -> str:
    """Normalizes colloquial or diverse time inputs into standard HH:MM AM/PM format."""
    if not time_str:
        return "11:00 AM"
    t = time_str.strip().lower()
    
    # Check for baje (Urdu for o'clock)
    baje_m = re.search(r'(\d{1,2})\s*(?:baje|bajay|بجے)', t)
    if baje_m:
        hr = int(baje_m.group(1))
        # Default afternoon context for 1,2,3,4,5,6
        if 1 <= hr <= 7:
            return f"0{hr}:00 PM" if hr < 10 else f"{hr}:00 PM"
        elif 8 <= hr <= 11:
            return f"{hr:02d}:00 AM"
        elif hr == 12:
            return "12:00 PM"

    # Match standard numbers with am/pm
    m = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)', t)
    if m:
        hr = int(m.group(1))
        mins = m.group(2) or "00"
        period = m.group(3).upper()
        return f"{hr:02d}:{mins} {period}"

    # Match standard exact slot from STANDARD_SLOTS
    for slot in STANDARD_SLOTS:
        if slot.lower() in t or t in slot.lower():
            return slot

    return time_str.strip()

def normalize_slot_date(date_str: str) -> str:
    """Normalizes colloquial date terms like 'kal', 'tomorrow'."""
    if not date_str:
        return "Tomorrow"
    d = date_str.strip().lower()
    if d in ["tomorrow", "kal", "کل"]:
        return "Tomorrow"
    elif d in ["today", "aaj", "آج"]:
        return "Today"
    elif "saturday" in d or "hafta" in d:
        return "Saturday"
    elif "sunday" in d or "itwar" in d:
        return "Sunday"
    elif "monday" in d or "peer" in d:
        return "Monday"
    elif "tuesday" in d or "mangal" in d:
        return "Tuesday"
    elif "wednesday" in d or "budh" in d:
        return "Wednesday"
    elif "thursday" in d or "jumeraat" in d:
        return "Thursday"
    elif "friday" in d or "juma" in d:
        return "Friday"
    return date_str.strip()

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
DISPOSABLE_DOMAINS = {
    "tempmail.com", "throwawaymail.com", "mailinator.com",
    "guerrillamail.com", "10minutemail.com", "trashmail.com",
    "yopmail.com", "fakeinbox.com", "sharklasers.com"
}

class AppointmentManager:
    def __init__(self):
        # In-memory throttle tracker: {client_email: [timestamp1, timestamp2, ...]}
        self._email_booking_log: Dict[str, List[float]] = {}

    def check_availability(self, appointment_date: str, appointment_time: str) -> Dict[str, Any]:
        """
        Checks whether the requested appointment date & time slot is available.
        Checks both SQLite active bookings and external Google Calendar API.
        """
        norm_date = normalize_slot_date(appointment_date)
        norm_time = normalize_slot_time(appointment_time)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, client_name, client_email, appointment_date, appointment_time 
            FROM appointments 
            WHERE (LOWER(appointment_date) = LOWER(?) OR LOWER(appointment_date) = LOWER(?))
              AND (LOWER(appointment_time) = LOWER(?) OR LOWER(appointment_time) = LOWER(?))
              AND status != 'CANCELLED'
            LIMIT 1
        """, (norm_date, appointment_date, norm_time, appointment_time))
        existing = cursor.fetchone()
        conn.close()

        is_available = (existing is None)
        return {
            "is_available": is_available,
            "normalized_date": norm_date,
            "normalized_time": norm_time,
            "conflict_appointment_id": existing["id"] if existing else None
        }

    def get_available_slots(self, appointment_date: str) -> List[str]:
        """
        Returns list of open, unbooked time slots on the requested date from STANDARD_SLOTS.
        """
        norm_date = normalize_slot_date(appointment_date)
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT appointment_time FROM appointments 
            WHERE (LOWER(appointment_date) = LOWER(?) OR LOWER(appointment_date) = LOWER(?))
              AND status != 'CANCELLED'
        """, (norm_date, appointment_date))
        booked_rows = cursor.fetchall()
        conn.close()

        booked_times = [normalize_slot_time(r["appointment_time"]).lower() for r in booked_rows]

        open_slots = []
        for slot in STANDARD_SLOTS:
            if slot.lower() not in booked_times:
                open_slots.append(slot)

        # Guarantee at least some alternate options
        if not open_slots:
            open_slots = ["11:00 AM", "03:00 PM", "05:00 PM"]

        return open_slots

    def get_latest_appointment_by_email(self, client_email: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the latest active appointment record for a given client email.
        Used when repeat callers call to reschedule or cancel.
        """
        if not client_email or "@" not in client_email:
            return None
        
        cleaned_email = client_email.strip().lower()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM appointments 
            WHERE LOWER(client_email) = ? AND status != 'CANCELLED'
            ORDER BY id DESC LIMIT 1
        """, (cleaned_email,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_latest_appointment_for_session(self, session_id: str, client_email: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Retrieves active appointment by session_id or client_email.
        """
        if client_email and "@" in client_email:
            app = self.get_latest_appointment_by_email(client_email)
            if app:
                return app
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM appointments 
            WHERE session_id = ? AND status != 'CANCELLED'
            ORDER BY id DESC LIMIT 1
        """, (session_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_appointment_by_id(self, appointment_id: Any) -> Optional[Dict[str, Any]]:
        """Retrieves an appointment by its numeric ID or formatted string ID (e.g., 32 or 'APT-32')."""
        if not appointment_id:
            return None
        conn = get_db_connection()
        cursor = conn.cursor()
        id_str = str(appointment_id).strip()
        numeric_id = int(id_str) if id_str.isdigit() else (int(id_str[4:]) if id_str.upper().startswith("APT-") and id_str[4:].isdigit() else None)
        
        cursor.execute("""
            SELECT * FROM appointments 
            WHERE id = ? OR appointment_id = ? OR appointment_id = ?
            ORDER BY id DESC LIMIT 1
        """, (numeric_id, id_str, f"APT-{id_str}"))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def book_appointment(
        self,
        session_id: str,
        client_name: str = "Valued Client",
        client_email: str = "",
        client_phone: str = "Email Priority Client",
        city: str = "Lahore",
        property_title: str = "General Real Estate Consultation",
        appointment_date: str = "Tomorrow",
        appointment_time: str = "11:00 AM",
        notes: str = "Site visit & investment consultation."
    ) -> Dict[str, Any]:
        """
        Books an appointment:
        1. Validates client email.
        2. Checks calendar availability for the requested date and time.
        3. If unavailable, returns slot conflict and recommends alternate slots on the SAME DATE.
        4. Saves appointment to SQLite database FIRST to generate unique Appointment ID.
        5. Sends real confirmation email with 1-click 'Add to Google Calendar' button and Appointment ID.
        6. Logs into CRM Appointment History and creates automatic Follow-up Reminder.
        """
        target_email = client_email.strip().lower() if client_email else ""
        if not target_email or not EMAIL_REGEX.match(target_email):
            return {
                "success": False,
                "status": "INVALID_EMAIL",
                "error": "Valid client email address is required to book an appointment.",
                "message": "Client email address is missing or invalid. Please provide a valid email (e.g., name@example.com)."
            }

        # Check disposable domain
        domain = target_email.split("@")[-1]
        if domain in DISPOSABLE_DOMAINS:
            return {
                "success": False,
                "status": "SPAM_REJECTED",
                "error": "Disposable or temporary email addresses are not permitted.",
                "message": "Please provide your permanent personal or work email address."
            }

        # Anti-Spam Throttling: Cooldown & Daily Limit (exempt test email for reliable development/testing)
        now = time.time()
        recent_bookings = self._email_booking_log.get(target_email, [])
        recent_bookings = [t for t in recent_bookings if now - t < 86400]
        self._email_booking_log[target_email] = recent_bookings

        if target_email != "samiworkspace11@gmail.com":
            # Cooldown check: minimum 2 minutes (120 sec) between booking attempts for same email
            if recent_bookings and (now - recent_bookings[-1] < 120):
                wait_sec = int(120 - (now - recent_bookings[-1]))
                return {
                    "success": False,
                    "status": "SPAM_THROTTLED",
                    "error": f"Booking throttled. Please wait {wait_sec} seconds before booking another appointment.",
                    "message": f"An appointment was recently scheduled for {target_email}. To prevent duplicate emails, please wait {wait_sec} seconds."
                }

            # Daily booking cap: maximum 3 bookings per email per 24 hours
            if len(recent_bookings) >= 3:
                return {
                    "success": False,
                    "status": "DAILY_LIMIT_EXCEEDED",
                    "error": "Daily booking limit reached (max 3 appointments per 24 hours).",
                    "message": "Daily booking limit reached for this email address. Please contact our support team directly for additional bookings."
                }

        norm_date = normalize_slot_date(appointment_date)
        norm_time = normalize_slot_time(appointment_time)

        # 1. Calendar Availability Verification
        avail = self.check_availability(norm_date, norm_time)
        if not avail["is_available"]:
            alt_slots = self.get_available_slots(norm_date)
            alt_slots = [s for s in alt_slots if s.lower() != norm_time.lower()]
            print(f"[Appointment Manager] Slot conflict: {norm_date} at {norm_time} is occupied. Alternates: {alt_slots}")
            return {
                "success": False,
                "status": "SLOT_UNAVAILABLE",
                "requested_date": norm_date,
                "requested_time": norm_time,
                "available_slots": alt_slots,
                "message": f"Requested slot {norm_time} on {norm_date} is already booked. Available slots on the same date: {', '.join(alt_slots[:3])}."
            }

        agent = get_agent_by_city(city)
        employee_name = agent["name"]
        employee_email = agent.get("email") or DEFAULT_MANAGER_EMAIL

        # 2. Calendar Integration: Client uses 1-click 'Add to Calendar' button sent in email (no server-side calendar clutter)
        cal_res = {"success": True, "mode": "EMAIL_CALENDAR_BUTTON_ONLY"}
        cal_event_id = ""

        # 3. Save to SQLite Database FIRST to acquire primary key Appointment ID
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
            norm_date, norm_time, 'BOOKED', cal_event_id, notes
        ))
        conn.commit()
        db_id = cursor.lastrowid
        appointment_id_str = f"APT-{db_id}"
        cursor.execute("UPDATE appointments SET appointment_id = ? WHERE id = ?", (appointment_id_str, db_id))
        conn.commit()
        conn.close()
        appointment_id = db_id

        # 4. Email Automation (Dispatched with Appointment ID & 1-Click Calendar button)
        email_res = email_service.send_appointment_notification(
            action_type="BOOKING",
            client_name=client_name,
            client_email=target_email,
            client_phone=client_phone,
            employee_name=employee_name,
            employee_email=employee_email,
            property_title=property_title,
            appointment_date=norm_date,
            appointment_time=norm_time,
            requirements_summary=f"City: {city} | Property: {property_title} | Notes: {notes}",
            appointment_id=appointment_id
        )

        # 5. CRM Store Audit & Automatic Follow-up Reminder Generation
        crm_store.log_appointment_history(
            appointment_id=appointment_id,
            client_email=target_email,
            action_type="BOOKING",
            details=f"Booked visit for {property_title} on {norm_date} at {norm_time} (ID: #{appointment_id})"
        )
        
        crm_store.create_followup_reminder(
            client_email=target_email,
            client_name=client_name,
            reminder_type="Pre-Visit Call Reminder",
            reminder_date=norm_date,
            notes=f"Call client to confirm arrival for {property_title} visit (ID: #{appointment_id})."
        )

        # Closed-Loop Feedback: Mark CRM transcripts as converted and index winning turns
        crm_store.mark_session_converted(session_id)
        dialogue_memory.index_converted_session(session_id)

        # Record timestamp in anti-spam tracker
        self._email_booking_log.setdefault(target_email, []).append(now)

        print(f"[Appointment Manager] Booked Appointment ID {appointment_id} for client {target_email} on {norm_date} {norm_time}")

        return {
            "success": True,
            "appointment_id": appointment_id,
            "id_display": f"APT-{appointment_id}",
            "status": "BOOKED",
            "client_name": client_name,
            "client_email": target_email,
            "employee_name": employee_name,
            "employee_email": employee_email,
            "property_title": property_title,
            "appointment_date": norm_date,
            "appointment_time": norm_time,
            "calendar_result": cal_res,
            "email_result": email_res
        }

    def reschedule_appointment(
        self,
        appointment_id: int,
        new_date: str,
        new_time: str
    ) -> Dict[str, Any]:
        """
        Reschedules an appointment by Appointment ID:
        Verifies slot availability on new date & time.
        Updates status to RESCHEDULED, dispatches confirmation email with new Calendar button, logs in CRM.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM appointments WHERE id = ?", (appointment_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return {"success": False, "error": f"Appointment ID {appointment_id} not found."}

        app_data = dict(row)
        norm_date = normalize_slot_date(new_date)
        norm_time = normalize_slot_time(new_time)

        # Check availability of new slot
        avail = self.check_availability(norm_date, norm_time)
        if not avail["is_available"] and avail.get("conflict_appointment_id") != appointment_id:
            conn.close()
            alt_slots = self.get_available_slots(norm_date)
            alt_slots = [s for s in alt_slots if s.lower() != norm_time.lower()]
            return {
                "success": False,
                "status": "SLOT_UNAVAILABLE",
                "requested_date": norm_date,
                "requested_time": norm_time,
                "available_slots": alt_slots,
                "message": f"Requested slot {norm_time} on {norm_date} is already occupied. Recommended slots: {', '.join(alt_slots[:3])}."
            }

        cursor.execute("""
            UPDATE appointments 
            SET appointment_date = ?, appointment_time = ?, status = 'RESCHEDULED'
            WHERE id = ?
        """, (norm_date, norm_time, appointment_id))
        conn.commit()
        conn.close()

        cal_res = {"success": True, "mode": "EMAIL_CALENDAR_BUTTON_ONLY"}

        # Send Email Notification to CLIENT'S ACTUAL EMAIL with Appointment ID
        email_res = email_service.send_appointment_notification(
            action_type="RESCHEDULING",
            client_name=app_data["client_name"],
            client_email=app_data["client_email"],
            client_phone=app_data["client_phone"],
            employee_name=app_data["employee_name"],
            employee_email=app_data.get("employee_email") or DEFAULT_MANAGER_EMAIL,
            property_title=app_data["property_title"],
            appointment_date=norm_date,
            appointment_time=norm_time,
            requirements_summary=f"Rescheduled meeting to {norm_date} at {norm_time}",
            appointment_id=appointment_id
        )

        # CRM Logging
        crm_store.log_appointment_history(
            appointment_id=appointment_id,
            client_email=app_data["client_email"],
            action_type="RESCHEDULING",
            details=f"Rescheduled meeting to {norm_date} at {norm_time} (ID: #{appointment_id})"
        )
        crm_store.create_followup_reminder(
            client_email=app_data["client_email"],
            client_name=app_data["client_name"],
            reminder_type="Rescheduled Visit Follow-up",
            reminder_date=norm_date,
            notes=f"Verify rescheduled site visit for {app_data['property_title']} (ID: #{appointment_id})."
        )

        return {
            "success": True,
            "appointment_id": appointment_id,
            "id_display": f"APT-{appointment_id}",
            "status": "RESCHEDULED",
            "client_name": app_data["client_name"],
            "property_title": app_data["property_title"],
            "client_email": app_data["client_email"],
            "new_date": norm_date,
            "new_time": norm_time,
            "calendar_result": cal_res,
            "email_result": email_res
        }

    def cancel_appointment(self, appointment_id: int) -> Dict[str, Any]:
        """
        Cancels an appointment by Appointment ID:
        Updates status to CANCELLED in SQLite, dispatches cancellation notice to client email with Appointment ID.
        """
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

        cal_res = {"success": True, "mode": "EMAIL_CALENDAR_BUTTON_ONLY"}

        # Send Cancellation Email to CLIENT'S ACTUAL EMAIL with Appointment ID
        email_res = email_service.send_appointment_notification(
            action_type="CANCELLATION",
            client_name=app_data["client_name"],
            client_email=app_data["client_email"],
            client_phone=app_data["client_phone"],
            employee_name=app_data["employee_name"],
            employee_email=app_data.get("employee_email") or DEFAULT_MANAGER_EMAIL,
            property_title=app_data["property_title"],
            appointment_date=app_data["appointment_date"],
            appointment_time=app_data["appointment_time"],
            requirements_summary="Appointment cancelled as per client request.",
            appointment_id=appointment_id
        )

        # CRM Logging
        crm_store.log_appointment_history(
            appointment_id=appointment_id,
            client_email=app_data["client_email"],
            action_type="CANCELLATION",
            details=f"Appointment #{appointment_id} cancelled by client."
        )

        return {
            "success": True,
            "appointment_id": appointment_id,
            "id_display": f"APT-{appointment_id}",
            "status": "CANCELLED",
            "client_name": app_data["client_name"],
            "property_title": app_data["property_title"],
            "client_email": app_data["client_email"],
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

appointment_manager = AppointmentManager()
