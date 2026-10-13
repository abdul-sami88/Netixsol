"""
MCP Server: notifications
Provides multi-channel healthcare notifications:
- Email (Gmail SMTP delivery with fallback to file logging)
  Default sender and recipient: samiworksapce11@gmail.com
- WhatsApp messaging (simulation & delivery logging)
- SMS alerts (simulation & delivery logging)
"""

import os
import sys
import smtplib
import ssl
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv()

from mcp.server.mcpserver import MCPServer

server = MCPServer("notifications")

LOGS_DIR = PROJECT_ROOT / "data"
LOG_FILE = LOGS_DIR / "sent_notifications.log"

DEFAULT_SENDER = os.getenv("GMAIL_USER", "samiworkspace11@gmail.com")
DEFAULT_RECEIVER = os.getenv("DEFAULT_RECIPIENT_EMAIL", "samiworkspace11@gmail.com")


def _log_notification(channel: str, recipient: str, subject: str, message: str, status: str):
    """Persists all outgoing communications into data/sent_notifications.log."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "channel": channel,
        "recipient": recipient,
        "subject": subject,
        "message": message,
        "status": status
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


@server.tool()
def send_email(
    subject: str,
    body_text: str,
    to_email: str = DEFAULT_RECEIVER,
    body_html: Optional[str] = None
) -> Dict[str, Any]:
    """
    Sends an email notification.
    If GMAIL_APP_PASSWORD is set in .env, sends via live Gmail SMTP (smtp.gmail.com:465).
    Otherwise, gracefully logs the email to data/sent_notifications.log.
    """
    sender_email = os.getenv("GMAIL_USER", DEFAULT_SENDER)
    password = os.getenv("GMAIL_APP_PASSWORD") or os.getenv("EMAIL_PASSWORD")
    target_email = to_email or DEFAULT_RECEIVER

    if password:
        clean_pwd = password.strip().replace(" ", "")
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"City Care Clinics <{sender_email}>"
            msg["To"] = target_email

            part1 = MIMEText(body_text, "plain")
            msg.attach(part1)

            if body_html:
                part2 = MIMEText(body_html, "html")
                msg.attach(part2)

            # Try port 587 STARTTLS first (standard for modern Gmail), fallback to port 465 SSL
            try:
                smtp_server = smtplib.SMTP("smtp.gmail.com", 587, timeout=15)
                smtp_server.ehlo()
                smtp_server.starttls()
                smtp_server.ehlo()
                smtp_server.login(sender_email, clean_pwd)
                smtp_server.sendmail(sender_email, target_email, msg.as_string())
                smtp_server.quit()
            except Exception:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context, timeout=15) as ssl_server:
                    ssl_server.login(sender_email, clean_pwd)
                    ssl_server.sendmail(sender_email, target_email, msg.as_string())

            _log_notification("email", target_email, subject, body_text, "delivered_smtp")
            return {
                "status": "delivered",
                "channel": "email",
                "sender": sender_email,
                "recipient": target_email,
                "subject": subject,
                "mode": "live_gmail_smtp",
                "message": "Email sent successfully via Gmail SMTP."
            }
        except Exception as e:
            _log_notification("email", target_email, subject, body_text, f"smtp_failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "channel": "email",
                "sender": sender_email,
                "recipient": target_email,
                "note": "Failed to send live email via SMTP. Check Gmail App Password in .env."
            }
    else:
        # Graceful simulation fallback
        _log_notification("email", target_email, subject, body_text, "simulated_logged")
        return {
            "status": "simulated_success",
            "channel": "email",
            "sender": sender_email,
            "recipient": target_email,
            "subject": subject,
            "mode": "simulated",
            "log_path": str(LOG_FILE),
            "note": "Email logged to data/sent_notifications.log. To send live emails, provide GMAIL_APP_PASSWORD in .env."
        }


@server.tool()
def send_appointment_confirmation(
    patient_name: str,
    doctor_name: str,
    specialty: str,
    clinic_branch: str,
    appointment_date: str,
    slot_time: str,
    token_number: str,
    to_email: str = DEFAULT_RECEIVER
) -> Dict[str, Any]:
    """
    Dispatches a formatted appointment confirmation notice to the patient.
    Defaults to sending to samiworksapce11@gmail.com.
    """
    subject = f"City Care Clinics — Appointment Confirmed (Token: {token_number})"

    body_text = f"""
Assalam-o-Alaikum {patient_name},

Aap ki appointment kamiyabi se book ho chuki hai:

- Doctor: {doctor_name} ({specialty})
- Clinic Branch: {clinic_branch}
- Tareekh (Date): {appointment_date}
- Waqt (Time): {slot_time}
- Token Number: {token_number}

Zaroori Hidayat:
1. Meherbani farma kar appointment waqt se 15 minute pehle clinic reception par tashreef layen.
2. Apna Token Number reception counter par dikhayen.
3. Agar pichli koi lab reports ya purani dawaiyan hain to sath layen.

City Care Clinics Support: 042-35750011
Emergency 24/7 Helpline: 1122
"""

    body_html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #1e293b;">
        <div style="max-width: 600px; margin: auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px;">
          <h2 style="color: #0d9488; margin-top: 0;">City Care Clinics</h2>
          <p style="font-size: 16px;">Assalam-o-Alaikum <strong>{patient_name}</strong>,</p>
          <p>Aap ki appointment City Care Clinics ke sath confirm ho gayi hai:</p>
          <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
            <tr style="background-color: #f8fafc;"><td style="padding: 8px; font-weight: bold;">Doctor:</td><td style="padding: 8px;">{doctor_name} ({specialty})</td></tr>
            <tr><td style="padding: 8px; font-weight: bold;">Clinic Branch:</td><td style="padding: 8px;">{clinic_branch}</td></tr>
            <tr style="background-color: #f8fafc;"><td style="padding: 8px; font-weight: bold;">Tareekh / Waqt:</td><td style="padding: 8px;">{appointment_date} at {slot_time}</td></tr>
            <tr><td style="padding: 8px; font-weight: bold; color: #0d9488;">Token Number:</td><td style="padding: 8px; font-weight: bold; color: #0d9488;">{token_number}</td></tr>
          </table>
          <p style="color: #64748b; font-size: 14px;"><em>Meherbani farma kar 15 minute pehle reception par tashreef layen.</em></p>
        </div>
      </body>
    </html>
    """

    return send_email(subject=subject, body_text=body_text, to_email=to_email, body_html=body_html)


@server.tool()
def send_prescription_safety_alert(
    patient_name: str,
    doctor_name: str,
    alert_type: str,
    alert_details: str,
    to_email: str = DEFAULT_RECEIVER
) -> Dict[str, Any]:
    """
    Dispatches a high-priority medication safety alert (e.g. drug-drug interaction or allergy conflict).
    Defaults to sending to samiworksapce11@gmail.com.
    """
    subject = f"URGENT: Medication Safety Alert for Patient {patient_name} [{alert_type}]"

    body_text = f"""
CLINICAL SAFETY ALERT
---------------------
Patient: {patient_name}
Consulting Doctor: {doctor_name}
Alert Severity: HIGH
Alert Type: {alert_type}

Details:
{alert_details}

Action Required:
Please consult your physician before initiating or modifying this medication regimen.

City Care Clinics Pharmacovigilance Team
"""

    return send_email(subject=subject, body_text=body_text, to_email=to_email)


@server.tool()
def send_whatsapp(
    phone_number: str,
    message: str
) -> Dict[str, Any]:
    """
    Sends/simulates a WhatsApp message to a Pakistani mobile number (+92-3XX-XXXXXXX).
    Logged to data/sent_notifications.log.
    """
    _log_notification("whatsapp", phone_number, "WhatsApp Message", message, "delivered_simulated")
    return {
        "status": "success",
        "channel": "whatsapp",
        "recipient": phone_number,
        "message_snippet": message[:120] + "..." if len(message) > 120 else message,
        "delivered_at": datetime.utcnow().isoformat(),
        "log_path": str(LOG_FILE)
    }


@server.tool()
def send_sms(
    phone_number: str,
    message: str
) -> Dict[str, Any]:
    """
    Sends/simulates an SMS alert to a Pakistani mobile number (+92-3XX-XXXXXXX).
    Logged to data/sent_notifications.log.
    """
    _log_notification("sms", phone_number, "SMS Alert", message, "delivered_simulated")
    return {
        "status": "success",
        "channel": "sms",
        "recipient": phone_number,
        "characters_count": len(message),
        "delivered_at": datetime.utcnow().isoformat(),
        "log_path": str(LOG_FILE)
    }


if __name__ == "__main__":
    server.run()
