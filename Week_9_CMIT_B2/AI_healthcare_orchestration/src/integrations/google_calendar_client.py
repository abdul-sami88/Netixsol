"""
Google Calendar Client for Clinic Appointment Scheduling.
Supports:
1. Live Google Calendar API integration via Service Account or OAuth 2.0.
2. Custom Calendar ID isolation (dedicated clinic calendar to avoid conflict with personal calendar).
3. Zero-crash graceful fallback simulation when credentials.json is pending.
"""

import os
import json
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_CREDENTIALS_FILE = PROJECT_ROOT / "credentials.json"
DEFAULT_TOKEN_FILE = PROJECT_ROOT / "token.json"

SCOPES = ["https://www.googleapis.com/auth/calendar"]

logger = logging.getLogger("GoogleCalendarClient")
logging.basicConfig(level=logging.INFO)


class GoogleCalendarClient:
    def __init__(self, credentials_path: Optional[str] = None, calendar_id: Optional[str] = None):
        self.credentials_path = Path(credentials_path or os.getenv("GOOGLE_CREDENTIALS_PATH", str(DEFAULT_CREDENTIALS_FILE)))
        self.token_path = Path(os.getenv("GOOGLE_TOKEN_PATH", str(DEFAULT_TOKEN_FILE)))
        self.calendar_id = calendar_id or os.getenv("GOOGLE_CALENDAR_ID", "primary")
        self._service = None
        self._init_service()

    def _init_service(self):
        """Attempts to initialize the Google Calendar API service."""
        if not self.credentials_path.exists():
            logger.info("Google Calendar credentials file (%s) not found. Running in simulated fallback mode.", self.credentials_path)
            self._service = None
            return

        try:
            # Check if it is a Service Account file
            with open(self.credentials_path, "r", encoding="utf-8") as f:
                creds_data = json.load(f)

            if creds_data.get("type") == "service_account":
                from google.oauth2 import service_account
                from googleapiclient.discovery import build

                creds = service_account.Credentials.from_service_account_file(
                    str(self.credentials_path), scopes=SCOPES
                )
                self.is_service_account = True
                self._service = build("calendar", "v3", credentials=creds)
                logger.info("Google Calendar Service Account client initialized successfully.")
                return

            self.is_service_account = False

            # Otherwise treat as OAuth 2.0 Client Secrets
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build

            creds = None
            if self.token_path.exists():
                creds = Credentials.from_authorized_user_file(str(self.token_path), SCOPES)

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(str(self.credentials_path), SCOPES)
                    creds = flow.run_local_server(port=0)
                with open(self.token_path, "w", encoding="utf-8") as token_file:
                    token_file.write(creds.to_json())

            self._service = build("calendar", "v3", credentials=creds)
            logger.info("Google Calendar OAuth client initialized successfully.")

        except Exception as e:
            logger.warning("Failed to initialize live Google Calendar service (%s). Falling back to simulation.", str(e))
            self._service = None

    @property
    def is_live(self) -> bool:
        return self._service is not None

    def create_event(
        self,
        summary: str,
        description: str,
        start_time_iso: str,
        end_time_iso: str,
        location: str = "City Care Clinics",
        attendee_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Creates an appointment event in Google Calendar.
        If credentials are not yet configured, returns a simulated event response.
        """
        if not self.is_live:
            event_id = f"sim_gcal_{uuid.uuid4().hex[:12]}"
            return {
                "status": "simulated",
                "event_id": event_id,
                "summary": summary,
                "calendar_id": self.calendar_id,
                "start": start_time_iso,
                "end": end_time_iso,
                "location": location,
                "note": "Simulated Google Calendar event. Place credentials.json in project root to sync live with Google Calendar."
            }

        body = {
            "summary": summary,
            "description": description,
            "location": location,
            "start": {"dateTime": start_time_iso, "timeZone": "Asia/Karachi"},
            "end": {"dateTime": end_time_iso, "timeZone": "Asia/Karachi"},
        }
        if attendee_email:
            if getattr(self, "is_service_account", False):
                body["description"] = f"{description}\n\nPatient Email: {attendee_email}"
            else:
                body["attendees"] = [{"email": attendee_email}]

        try:
            event = self._service.events().insert(
                calendarId=self.calendar_id,
                body=body
            ).execute()
            return {
                "status": "synced",
                "event_id": event.get("id"),
                "html_link": event.get("htmlLink"),
                "summary": summary,
                "calendar_id": self.calendar_id
            }
        except Exception as e:
            logger.error("Error creating Google Calendar event: %s", str(e))
            return {
                "status": "error",
                "message": str(e),
                "fallback_simulated_id": f"sim_gcal_{uuid.uuid4().hex[:12]}"
            }

    def update_event(
        self,
        event_id: str,
        start_time_iso: str,
        end_time_iso: str,
        summary: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Updates an existing calendar event (e.g. for rescheduling)."""
        if not self.is_live or event_id.startswith("sim_gcal_"):
            return {
                "status": "simulated_updated",
                "event_id": event_id,
                "new_start": start_time_iso,
                "new_end": end_time_iso,
                "calendar_id": self.calendar_id,
                "note": "Simulated event updated successfully."
            }

        try:
            patch_body = {
                "start": {"dateTime": start_time_iso, "timeZone": "Asia/Karachi"},
                "end": {"dateTime": end_time_iso, "timeZone": "Asia/Karachi"}
            }
            if summary:
                patch_body["summary"] = summary
            if description:
                patch_body["description"] = description

            updated_event = self._service.events().patch(
                calendarId=self.calendar_id,
                eventId=event_id,
                body=patch_body
            ).execute()
            return {
                "status": "synced_updated",
                "event_id": updated_event.get("id"),
                "calendar_id": self.calendar_id
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def delete_event(self, event_id: str) -> Dict[str, Any]:
        """Deletes/cancels an event on Google Calendar."""
        if not self.is_live or event_id.startswith("sim_gcal_"):
            return {
                "status": "simulated_deleted",
                "event_id": event_id,
                "note": "Simulated event cancelled successfully."
            }

        try:
            self._service.events().delete(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            return {"status": "synced_deleted", "event_id": event_id}
        except Exception as e:
            return {"status": "error", "message": str(e)}
