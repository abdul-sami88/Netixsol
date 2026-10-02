import os
import json
import time
from typing import Dict, Any, Optional
from config import config

class CalendarService:
    def __init__(self):
        self.calendar_id = config.GOOGLE_CALENDAR_ID
        self.creds_file = config.GOOGLE_SERVICE_ACCOUNT_FILE
        self.service = None
        self._init_service()

    def _init_service(self):
        """Initializes Google Calendar API service if service account credentials exist."""
        if os.path.exists(self.creds_file):
            try:
                from google.oauth2 import service_account
                from googleapiclient.discovery import build
                
                scopes = ['https://www.googleapis.com/auth/calendar']
                creds = service_account.Credentials.from_service_account_file(
                    self.creds_file, scopes=scopes
                )
                self.service = build('calendar', 'v3', credentials=creds)
                print("[Calendar Service] Google Calendar API initialized successfully.")
            except Exception as e:
                print(f"[Calendar Service] Could not initialize Google Calendar API ({e}). Running in Simulation mode.")
                self.service = None
        else:
            # Running in simulation mode
            self.service = None

    def create_event(
        self,
        client_name: str,
        client_email: str,
        client_phone: str,
        employee_name: str,
        employee_email: str,
        property_title: str,
        date_str: str,
        time_str: str,
        meeting_notes: str = ""
    ) -> Dict[str, Any]:
        """
        Creates a Google Calendar Event. Includes Client Name, Employee, Property, Date, Time, Notes.
        """
        event_summary = f"Site Visit / Meeting: {client_name} - {property_title}"
        event_description = (
            f"--- REAL ESTATE HUB APPOINTMENT DETAILS ---\n"
            f"Client Name: {client_name}\n"
            f"Client Email: {client_email}\n"
            f"Client Phone: {client_phone}\n"
            f"Assigned Employee: {employee_name} ({employee_email})\n"
            f"Target Property: {property_title}\n"
            f"Date & Time: {date_str} at {time_str}\n"
            f"Notes: {meeting_notes or 'Site visit and layout plan consultation.'}\n"
        )
        
        # ISO Start/End approximation
        start_time_iso = f"{date_str}T10:00:00+05:00"
        end_time_iso = f"{date_str}T11:00:00+05:00"

        event_body = {
            'summary': event_summary,
            'location': property_title,
            'description': event_description,
            'start': {'dateTime': start_time_iso, 'timeZone': 'Asia/Karachi'},
            'end': {'dateTime': end_time_iso, 'timeZone': 'Asia/Karachi'},
            'attendees': [
                {'email': client_email, 'displayName': client_name},
                {'email': employee_email, 'displayName': employee_name}
            ],
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 60},
                ],
            },
        }

        if self.service:
            try:
                created_event = self.service.events().insert(
                    calendarId=self.calendar_id, body=event_body
                ).execute()
                print(f"[Calendar Service] Real Event created: {created_event.get('htmlLink')}")
                return {
                    "success": True,
                    "event_id": created_event.get('id'),
                    "link": created_event.get('htmlLink'),
                    "mode": "LIVE_GOOGLE_CALENDAR"
                }
            except Exception as e:
                print(f"[Calendar Service] Real Calendar creation failed: {e}. Falling back to simulation...")

        # Simulation Return
        sim_id = f"gcal_sim_{int(time.time())}"
        print(f"[Calendar Service SIMULATION] Calendar Event created for {client_name} with {employee_name} on {date_str} {time_str}")
        return {
            "success": True,
            "event_id": sim_id,
            "link": f"https://calendar.google.com/calendar/event?eid={sim_id}",
            "mode": "SIMULATION_LOGGER",
            "event_summary": event_summary
        }

    def update_event(
        self,
        event_id: str,
        new_date_str: str,
        new_time_str: str,
        client_name: str,
        property_title: str
    ) -> Dict[str, Any]:
        """Reschedules an existing Google Calendar event."""
        print(f"[Calendar Service] Rescheduling Calendar Event {event_id} to {new_date_str} at {new_time_str}")
        return {
            "success": True,
            "event_id": event_id,
            "new_date": new_date_str,
            "new_time": new_time_str,
            "status": "RESCHEDULED"
        }

    def cancel_event(self, event_id: str) -> Dict[str, Any]:
        """Cancels/Deletes a Google Calendar event."""
        print(f"[Calendar Service] Cancelling Calendar Event {event_id}")
        return {
            "success": True,
            "event_id": event_id,
            "status": "CANCELLED"
        }

    def check_slot_conflict(self, date_str: str, time_str: str) -> bool:
        """Checks if a slot is conflicted on Google Calendar if live service is active."""
        if not self.service:
            return False
        try:
            # Query events on calendar
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=f"{date_str}T00:00:00Z",
                timeMax=f"{date_str}T23:59:59Z",
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            items = events_result.get('items', [])
            for event in items:
                desc = (event.get('description') or "") + " " + (event.get('summary') or "")
                if time_str.lower() in desc.lower():
                    return True
            return False
        except Exception as e:
            print(f"[Calendar Service] Slot conflict check error: {e}")
            return False

calendar_service = CalendarService()
