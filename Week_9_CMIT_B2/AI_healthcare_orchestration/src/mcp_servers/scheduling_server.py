"""
MCP Server: scheduling
Provides clinic appointment scheduling tools:
- find_doctors: Search doctors by specialty, city, or name
- get_available_slots: Calculate available 15-minute slots for a doctor on a specific date
- book_appointment: Book an appointment, persist in PostgreSQL, and sync with Google Calendar
- reschedule_appointment: Change appointment slot and update Google Calendar
- cancel_appointment: Cancel an appointment and release Google Calendar event
"""

import sys
import uuid
from datetime import datetime, date, time, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from mcp.server.mcpserver import MCPServer
from src.database.connection import db_session
from src.database.models import Practitioner, PractitionerSchedule, Appointment, Patient, ClinicBranch
from src.integrations.google_calendar_client import GoogleCalendarClient

server = MCPServer("scheduling")
gcal_client = GoogleCalendarClient()


@server.tool()
def find_doctors(
    specialty: Optional[str] = None,
    city: Optional[str] = None,
    doctor_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search for qualified clinic practitioners by medical specialty, clinic city, or doctor name.
    Supported Specialties: General Medicine, Paediatrics, Gynaecology, Cardiology, Dermatology, ENT.
    Supported Cities: Lahore, Islamabad.
    """
    session = db_session()
    try:
        query = session.query(Practitioner).join(Practitioner.primary_branch).filter(Practitioner.active == True)

        if specialty:
            query = query.filter(Practitioner.specialty.ilike(f"%{specialty}%"))
        if city:
            query = query.filter(ClinicBranch.city.ilike(f"%{city}%"))
        if doctor_name:
            query = query.filter(Practitioner.full_name.ilike(f"%{doctor_name}%"))

        doctors = query.all()

        results = []
        for d in doctors:
            schedules = [
                {
                    "day_of_week": s.day_of_week,
                    "day_name": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][s.day_of_week],
                    "timing": f"{s.start_time.strftime('%H:%M')} - {s.end_time.strftime('%H:%M')}",
                    "branch": s.branch.name
                }
                for s in d.schedules
            ]

            results.append({
                "doctor_id": d.id,
                "name": d.full_name,
                "specialty": d.specialty,
                "qualification": d.qualification,
                "consultation_fee_pkr": d.consultation_fee,
                "branch_name": d.primary_branch.name,
                "city": d.primary_branch.city,
                "branch_address": d.primary_branch.address,
                "languages": d.languages_spoken,
                "schedules": schedules
            })

        return {
            "status": "success",
            "matches_found": len(results),
            "doctors": results
        }
    finally:
        session.close()


@server.tool()
def get_available_slots(doctor_id: str, date_str: str) -> Dict[str, Any]:
    """
    Calculates unbooked 15-minute consultation slots for a doctor on a specific date.
    date_str format: YYYY-MM-DD (e.g. '2026-10-15')
    """
    session = db_session()
    try:
        doctor = session.query(Practitioner).filter(Practitioner.id == doctor_id).first()
        if not doctor:
            return {"status": "error", "message": f"Doctor with ID '{doctor_id}' not found."}

        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return {"status": "error", "message": "Invalid date format. Please use YYYY-MM-DD."}

        target_weekday = target_date.weekday() # 0 = Monday ... 6 = Sunday

        schedule = session.query(PractitionerSchedule).filter(
            PractitionerSchedule.practitioner_id == doctor_id,
            PractitionerSchedule.day_of_week == target_weekday
        ).first()

        if not schedule:
            day_name = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][target_weekday]
            return {
                "status": "success",
                "doctor_id": doctor_id,
                "doctor_name": doctor.full_name,
                "date": date_str,
                "day_name": day_name,
                "available_slots": [],
                "message": f"{doctor.full_name} does not have clinic hours on {day_name}s."
            }

        # Generate all 15-minute slots between start_time and end_time
        slot_duration = timedelta(minutes=schedule.slot_duration_minutes)
        curr_dt = datetime.combine(target_date, schedule.start_time)
        end_dt = datetime.combine(target_date, schedule.end_time)

        all_slots = []
        while curr_dt + slot_duration <= end_dt:
            all_slots.append(curr_dt.time().strftime("%H:%M"))
            curr_dt += slot_duration

        # Query existing appointments on that date
        day_start = datetime.combine(target_date, time.min)
        day_end = datetime.combine(target_date, time.max)

        existing_appointments = session.query(Appointment).filter(
            Appointment.practitioner_id == doctor_id,
            Appointment.start_time >= day_start,
            Appointment.start_time <= day_end,
            Appointment.status.notin_(["cancelled"])
        ).all()

        booked_slots = {appt.start_time.strftime("%H:%M") for appt in existing_appointments}
        free_slots = [s for s in all_slots if s not in booked_slots]

        return {
            "status": "success",
            "doctor_id": doctor_id,
            "doctor_name": doctor.full_name,
            "specialty": doctor.specialty,
            "branch": schedule.branch.name,
            "date": date_str,
            "day_name": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][target_weekday],
            "total_slots": len(all_slots),
            "booked_slots_count": len(booked_slots),
            "available_slots_count": len(free_slots),
            "available_slots": free_slots
        }
    finally:
        session.close()


@server.tool()
def book_appointment(
    patient_id: str,
    doctor_id: str,
    date_str: str,
    slot_time: str,
    chief_complaint: str = "General Consultation",
    urgency_tier: str = "ROUTINE"
) -> Dict[str, Any]:
    """
    Books an appointment slot for a patient, saves record in PostgreSQL, and synchronizes with Google Calendar.
    date_str: YYYY-MM-DD (e.g. '2026-10-15')
    slot_time: HH:MM (24-hour format, e.g. '14:30')
    """
    session = db_session()
    try:
        patient = session.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            return {"status": "error", "message": f"Patient with ID '{patient_id}' not found."}

        doctor = session.query(Practitioner).filter(Practitioner.id == doctor_id).first()
        if not doctor:
            return {"status": "error", "message": f"Doctor with ID '{doctor_id}' not found."}

        try:
            start_dt = datetime.strptime(f"{date_str} {slot_time}", "%Y-%m-%d %H:%M")
        except ValueError:
            return {"status": "error", "message": "Invalid date or time format. Use YYYY-MM-DD and HH:MM."}

        end_dt = start_dt + timedelta(minutes=15)

        # Check if slot already taken
        collision = session.query(Appointment).filter(
            Appointment.practitioner_id == doctor_id,
            Appointment.start_time == start_dt,
            Appointment.status.notin_(["cancelled"])
        ).first()

        if collision:
            return {
                "status": "error",
                "message": f"Slot {slot_time} on {date_str} is already booked for Dr. {doctor.full_name}. Please choose another slot."
            }

        # Generate unique token
        token_number = f"CC-{start_dt.strftime('%m%d')}-{uuid.uuid4().hex[:4].upper()}"

        branch_id = doctor.primary_branch_id
        branch = session.query(ClinicBranch).filter(ClinicBranch.id == branch_id).first()

        appointment = Appointment(
            id=str(uuid.uuid4()),
            patient_id=patient.id,
            practitioner_id=doctor.id,
            branch_id=branch_id,
            token_number=token_number,
            start_time=start_dt,
            end_time=end_dt,
            status="booked",
            appointment_type="routine" if urgency_tier == "ROUTINE" else "urgent",
            chief_complaint=chief_complaint,
            urgency_tier=urgency_tier,
            clinical_notes=f"Booked via AI Assistant. Urgency tier: {urgency_tier}"
        )
        session.add(appointment)
        session.commit()

        # Sync to Google Calendar
        gcal_summary = f"Clinic Appointment: {doctor.full_name} ({doctor.specialty}) - Token {token_number}"
        gcal_desc = (
            f"Patient: {patient.full_name} (Phone: {patient.phone})\n"
            f"Doctor: {doctor.full_name} - {doctor.qualification}\n"
            f"Branch: {branch.name}, {branch.address}\n"
            f"Fee: PKR {doctor.consultation_fee}\n"
            f"Chief Complaint: {chief_complaint}\n"
            f"Appointment ID: {appointment.id}\n"
            f"Token: {token_number}"
        )

        gcal_res = gcal_client.create_event(
            summary=gcal_summary,
            description=gcal_desc,
            start_time_iso=start_dt.isoformat(),
            end_time_iso=end_dt.isoformat(),
            location=f"{branch.name}, {branch.address}"
        )

        return {
            "status": "success",
            "message": "Appointment booked successfully.",
            "appointment_id": appointment.id,
            "token_number": token_number,
            "patient_name": patient.full_name,
            "patient_phone": patient.phone,
            "doctor_name": doctor.full_name,
            "specialty": doctor.specialty,
            "branch_name": branch.name,
            "branch_address": branch.address,
            "consultation_fee_pkr": doctor.consultation_fee,
            "appointment_date": date_str,
            "slot_time": slot_time,
            "urgency_tier": urgency_tier,
            "google_calendar_sync": gcal_res
        }
    except Exception as e:
        session.rollback()
        return {"status": "error", "message": f"Failed to book appointment: {str(e)}"}
    finally:
        session.close()


@server.tool()
def reschedule_appointment(
    appointment_id: str,
    new_date_str: str,
    new_slot_time: str
) -> Dict[str, Any]:
    """
    Reschedules an existing active appointment to a new date and time.
    """
    session = db_session()
    try:
        appointment = session.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appointment:
            return {"status": "error", "message": f"Appointment with ID '{appointment_id}' not found."}

        if appointment.status == "cancelled":
            return {"status": "error", "message": "Cannot reschedule a cancelled appointment. Please book a new one."}

        try:
            new_start_dt = datetime.strptime(f"{new_date_str} {new_slot_time}", "%Y-%m-%d %H:%M")
        except ValueError:
            return {"status": "error", "message": "Invalid date or time format. Use YYYY-MM-DD and HH:MM."}

        new_end_dt = new_start_dt + timedelta(minutes=15)

        # Check collision
        collision = session.query(Appointment).filter(
            Appointment.practitioner_id == appointment.practitioner_id,
            Appointment.start_time == new_start_dt,
            Appointment.id != appointment.id,
            Appointment.status.notin_(["cancelled"])
        ).first()

        if collision:
            return {
                "status": "error",
                "message": f"Requested slot {new_slot_time} on {new_date_str} is already occupied."
            }

        old_start_str = appointment.start_time.strftime("%Y-%m-%d %H:%M")
        appointment.start_time = new_start_dt
        appointment.end_time = new_end_dt
        appointment.status = "rescheduled"
        session.commit()

        # Update Google Calendar
        gcal_update = gcal_client.update_event(
            event_id=f"gcal_{appointment.id}",
            start_time_iso=new_start_dt.isoformat(),
            end_time_iso=new_end_dt.isoformat(),
            description=f"Rescheduled Appointment from {old_start_str} to {new_date_str} {new_slot_time}."
        )

        return {
            "status": "success",
            "message": "Appointment rescheduled successfully.",
            "appointment_id": appointment.id,
            "token_number": appointment.token_number,
            "doctor_name": appointment.practitioner.full_name,
            "previous_time": old_start_str,
            "new_date": new_date_str,
            "new_slot_time": new_slot_time,
            "google_calendar_sync": gcal_update
        }
    except Exception as e:
        session.rollback()
        return {"status": "error", "message": f"Rescheduling error: {str(e)}"}
    finally:
        session.close()


@server.tool()
def cancel_appointment(
    appointment_id: str,
    cancellation_reason: str = "Patient requested cancellation"
) -> Dict[str, Any]:
    """
    Cancels an appointment, updates database status, and removes the Google Calendar entry.
    """
    session = db_session()
    try:
        appointment = session.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appointment:
            return {"status": "error", "message": f"Appointment with ID '{appointment_id}' not found."}

        if appointment.status == "cancelled":
            return {"status": "success", "message": "Appointment was already cancelled."}

        appointment.status = "cancelled"
        appointment.clinical_notes = (appointment.clinical_notes or "") + f"\n[Cancelled]: {cancellation_reason}"
        session.commit()

        # Delete on Google Calendar
        gcal_del = gcal_client.delete_event(event_id=f"gcal_{appointment.id}")

        return {
            "status": "success",
            "message": "Appointment cancelled successfully.",
            "appointment_id": appointment.id,
            "token_number": appointment.token_number,
            "doctor_name": appointment.practitioner.full_name,
            "cancellation_reason": cancellation_reason,
            "google_calendar_sync": gcal_del
        }
    except Exception as e:
        session.rollback()
        return {"status": "error", "message": f"Cancellation error: {str(e)}"}
    finally:
        session.close()


if __name__ == "__main__":
    server.run()
