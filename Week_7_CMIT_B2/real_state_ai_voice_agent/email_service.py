import smtplib
import urllib.parse
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from typing import Dict, Any, Optional
from config import config

# Primary hardcoded receiving email by user for testing
HARDCODED_RECEIVER_EMAIL = "yourmail@gmail.com"

class EmailService:
    def __init__(self):
        self.server = config.SMTP_SERVER
        self.port = config.SMTP_PORT
        self.username = config.SMTP_USERNAME
        self.password = config.SMTP_PASSWORD
        
        # Sender must align with SMTP authenticated username to pass SPF/DMARC checks on Gmail SMTP
        self.sender = self.username or config.NOTIFICATION_SENDER_EMAIL or HARDCODED_RECEIVER_EMAIL

    def _generate_google_calendar_url(self, title: str, details: str, location: str, date_str: str, time_str: str) -> str:
        """Generates a 1-click Google Calendar Add-to-Calendar URL."""
        now = datetime.now() + timedelta(days=1)
        start_dt = now.replace(hour=10, minute=0, second=0)
        end_dt = start_dt + timedelta(hours=1)
        
        start_iso = start_dt.strftime("%Y%m%dT%H%M%SZ")
        end_iso = end_dt.strftime("%Y%m%dT%H%M%SZ")

        params = {
            "action": "TEMPLATE",
            "text": f"Real Estate Visit: {title}",
            "details": details,
            "location": location,
            "dates": f"{start_iso}/{end_iso}"
        }
        return "https://calendar.google.com/calendar/render?" + urllib.parse.urlencode(params)

    def _send_single_email(self, recipient: str, subject: str, html_content: str) -> bool:
        """Helper to dispatch an individual UTF-8 encoded email via SMTP."""
        if not (self.username and self.password and "your_" not in self.username):
            print(f"[Email Service SIMULATION] Logger: Sent to {recipient} | Subject: {subject}")
            return True

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = Header(subject, "utf-8")
            msg["From"] = self.sender or self.username
            msg["To"] = recipient
            msg.attach(MIMEText(html_content, "html", "utf-8"))

            server = smtplib.SMTP(self.server, self.port)
            server.starttls()
            server.login(self.username, self.password)
            server.sendmail(self.sender or self.username, [recipient], msg.as_string().encode("utf-8"))
            server.quit()
            print(f"[Email Service] LIVE EMAIL sent successfully to {recipient} | Subject: {subject}")
            return True
        except Exception as e:
            print(f"[Email Service] Failed sending email to {recipient}: {e}")
            return False

    def send_appointment_notification(
        self,
        action_type: str, # 'BOOKING', 'RESCHEDULING', 'CANCELLATION'
        client_name: str,
        client_email: str,
        client_phone: str,
        employee_name: str,
        employee_email: str,
        property_title: str,
        appointment_date: str,
        appointment_time: str,
        requirements_summary: str = ""
    ) -> Dict[str, Any]:
        """
        Sends TWO DISTINCT SEPARATE EMAILS to HARDCODED_RECEIVER_EMAIL (samiworkspace11@gmail.com):
        1. Client Confirmation Email (Supporting BOOKING, RESCHEDULING, CANCELLATION)
        2. Assigned Agent / Manager Notification Email (Supporting BOOKING, RESCHEDULING, CANCELLATION)
        Both include a 1-Click 'Add to Google Calendar' button!
        """
        details_text = (
            f"Client Name: {client_name}\n"
            f"Client Email: {client_email or HARDCODED_RECEIVER_EMAIL}\n"
            f"Phone: {client_phone}\n"
            f"Assigned Manager: {employee_name}\n"
            f"Property: {property_title}\n"
            f"Meeting Time: {appointment_date} at {appointment_time}\n"
            f"Notes: {requirements_summary or 'Site Visit Consultation'}"
        )
        
        gcal_url = self._generate_google_calendar_url(
            title=property_title,
            details=details_text,
            location=property_title,
            date_str=appointment_date,
            time_str=appointment_time
        )

        # ----------------------------------------------------
        # EMAIL #1: CLIENT CONFIRMATION EMAIL
        # ----------------------------------------------------
        client_subject = f"[CLIENT CONFIRMATION] Your Appointment for {property_title} is {action_type.title()}!"
        client_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #1f2937; line-height: 1.6; background-color: #f3f4f6; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                <div style="background-color: #064e3b; padding: 25px; text-align: center; color: white;">
                    <h2 style="margin: 0; font-size: 22px;">RealEstate Hub Pakistan</h2>
                    <p style="margin: 5px 0 0 0; font-size: 14px; color: #a7f3d0;">Client Appointment Confirmation Notice</p>
                </div>
                
                <div style="padding: 30px;">
                    <h3 style="color: #065f46; margin-top: 0;">Dear {client_name},</h3>
                    <p style="font-size: 15px;">Your appointment has been successfully <strong>{action_type.lower()}</strong>. Details are below:</p>
                    
                    <table style="width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 14px; border: 1px solid #e5e7eb;">
                        <tr style="background: #f9fafb;"><th style="padding: 10px; text-align: left; border: 1px solid #e5e7eb;">Booking Field</th><th style="padding: 10px; text-align: left; border: 1px solid #e5e7eb;">Confirmation Details</th></tr>
                        <tr><td style="padding: 10px; border: 1px solid #e5e7eb;"><strong>Action Status</strong></td><td style="padding: 10px; border: 1px solid #e5e7eb; color: #059669;"><strong>{action_type.title()}</strong></td></tr>
                        <tr><td style="padding: 10px; border: 1px solid #e5e7eb;"><strong>Property</strong></td><td style="padding: 10px; border: 1px solid #e5e7eb;">{property_title}</td></tr>
                        <tr><td style="padding: 10px; border: 1px solid #e5e7eb;"><strong>Meeting Date & Time</strong></td><td style="padding: 10px; border: 1px solid #e5e7eb; color: #059669;"><strong>{appointment_date} at {appointment_time}</strong></td></tr>
                        <tr><td style="padding: 10px; border: 1px solid #e5e7eb;"><strong>Assigned Senior Executive</strong></td><td style="padding: 10px; border: 1px solid #e5e7eb;">{employee_name} ({HARDCODED_RECEIVER_EMAIL})</td></tr>
                        <tr><td style="padding: 10px; border: 1px solid #e5e7eb;"><strong>Consultation Notes</strong></td><td style="padding: 10px; border: 1px solid #e5e7eb;">{requirements_summary or 'Site Visit & Layout Consultation'}</td></tr>
                    </table>

                    <div style="text-align: center; margin: 30px 0 10px 0;">
                        <a href="{gcal_url}" target="_blank" style="background-color: #10b981; color: #ffffff; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 15px; display: inline-block; box-shadow: 0 4px 6px rgba(16,185,129,0.3);">
                            Click Here to Add Event to Your Google Calendar
                        </a>
                    </div>
                </div>

                <div style="background-color: #f9fafb; padding: 15px; text-align: center; border-top: 1px solid #e5e7eb; font-size: 12px; color: #6b7280;">
                    RealEstate Hub Customer Service Team &bull; Senior Executive Zara
                </div>
            </div>
        </body>
        </html>
        """

        # ----------------------------------------------------
        # EMAIL #2: AGENT / MANAGER NOTIFICATION EMAIL
        # ----------------------------------------------------
        agent_subject = f"[AGENT ALERT] New Client Appointment {action_type.title()}: {client_name} - {property_title}"
        agent_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #1f2937; line-height: 1.6; background-color: #f3f4f6; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                <div style="background-color: #1e3a8a; padding: 25px; text-align: center; color: white;">
                    <h2 style="margin: 0; font-size: 22px;">RealEstate Hub CRM Agent Alert</h2>
                    <p style="margin: 5px 0 0 0; font-size: 14px; color: #93c5fd;">Internal Assigned Client Notification</p>
                </div>
                
                <div style="padding: 30px;">
                    <h3 style="color: #1e40af; margin-top: 0;">Hello Agent {employee_name},</h3>
                    <p style="font-size: 15px;">A client appointment update has occurred. Status: <strong>{action_type}</strong>.</p>
                    
                    <table style="width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 14px; border: 1px solid #e5e7eb;">
                        <tr style="background: #eff6ff;"><th style="padding: 10px; text-align: left; border: 1px solid #e5e7eb;">Field</th><th style="padding: 10px; text-align: left; border: 1px solid #e5e7eb;">Client Lead Info</th></tr>
                        <tr><td style="padding: 10px; border: 1px solid #e5e7eb;"><strong>Action Status</strong></td><td style="padding: 10px; border: 1px solid #e5e7eb; color: #1d4ed8;"><strong>{action_type}</strong></td></tr>
                        <tr><td style="padding: 10px; border: 1px solid #e5e7eb;"><strong>Client Name</strong></td><td style="padding: 10px; border: 1px solid #e5e7eb;"><strong>{client_name}</strong></td></tr>
                        <tr><td style="padding: 10px; border: 1px solid #e5e7eb;"><strong>Client Email</strong></td><td style="padding: 10px; border: 1px solid #e5e7eb;">{client_email or HARDCODED_RECEIVER_EMAIL}</td></tr>
                        <tr><td style="padding: 10px; border: 1px solid #e5e7eb;"><strong>Client Phone</strong></td><td style="padding: 10px; border: 1px solid #e5e7eb;">{client_phone}</td></tr>
                        <tr><td style="padding: 10px; border: 1px solid #e5e7eb;"><strong>Target Property</strong></td><td style="padding: 10px; border: 1px solid #e5e7eb;">{property_title}</td></tr>
                        <tr><td style="padding: 10px; border: 1px solid #e5e7eb;"><strong>Meeting Time</strong></td><td style="padding: 10px; border: 1px solid #e5e7eb; color: #1d4ed8;"><strong>{appointment_date} at {appointment_time}</strong></td></tr>
                        <tr><td style="padding: 10px; border: 1px solid #e5e7eb;"><strong>Client Requirements</strong></td><td style="padding: 10px; border: 1px solid #e5e7eb;">{requirements_summary or 'Standard Site Visit & Investment Consultation'}</td></tr>
                    </table>

                    <div style="text-align: center; margin: 30px 0 10px 0;">
                        <a href="{gcal_url}" target="_blank" style="background-color: #2563eb; color: #ffffff; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 15px; display: inline-block; box-shadow: 0 4px 6px rgba(37,99,235,0.3);">
                            Click Here to Add Client Event to Google Calendar
                        </a>
                    </div>
                </div>

                <div style="background-color: #f9fafb; padding: 15px; text-align: center; border-top: 1px solid #e5e7eb; font-size: 12px; color: #6b7280;">
                    RealEstate Hub Internal Business Automation &bull; Agent Notification System
                </div>
            </div>
        </body>
        </html>
        """

        # Determine actual recipients for client and agent notifications
        client_recipient = client_email.strip() if (client_email and "@" in client_email) else HARDCODED_RECEIVER_EMAIL
        agent_recipient = employee_email.strip() if (employee_email and "@" in employee_email) else HARDCODED_RECEIVER_EMAIL
        
        print(f"[Email Service] Dispatching Email #1 ({action_type} - Client Confirmation) to {client_recipient}...")
        res1 = self._send_single_email(client_recipient, client_subject, client_html)

        print(f"[Email Service] Dispatching Email #2 ({action_type} - Agent Alert) to {agent_recipient}...")
        res2 = self._send_single_email(agent_recipient, agent_subject, agent_html)

        return {
            "success": (res1 and res2),
            "mode": "LIVE_SMTP" if (self.username and self.password and "your_" not in self.username) else "SIMULATION_LOGGER",
            "emails_sent_count": 2,
            "client_recipient": client_recipient,
            "agent_recipient": agent_recipient,
            "subjects": [client_subject, agent_subject],
            "gcal_url": gcal_url
        }

email_service = EmailService()
