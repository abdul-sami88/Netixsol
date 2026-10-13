"""
Email Confirmation & Notification Channel for City Care Clinics.
Delivers:
1. Instant Appointment Confirmation Emails (HTML & Plaintext with token, clinic directions, doctor details).
2. 24-Hour Prior Appointment Reminders.
3. Post-Consultation Follow-up & Medicine Timetable Emails.
Sender & Default Recipient: samiworkspace11@gmail.com
"""

import os
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from src.mcp_servers.notifications_server import send_email

DEFAULT_RECIPIENT = os.getenv("DEFAULT_RECIPIENT_EMAIL", "samiworkspace11@gmail.com")


def send_appointment_confirmation_email(
    patient_name: str,
    doctor_name: str,
    specialty: str,
    branch_name: str,
    slot_date: str,
    slot_time: str,
    fee_pkr: int = 2500,
    token_number: str = "CC-101",
    recipient_email: str = DEFAULT_RECIPIENT
) -> Dict[str, Any]:
    """
    Sends a formal HTML appointment confirmation email to the patient.
    """
    subject = f"✅ Appointment Confirmed: {doctor_name} at City Care Clinics ({token_number})"

    body_text = f"""
Dear {patient_name},

Your appointment at City Care Clinics has been successfully scheduled.

Details:
- Token Number: {token_number}
- Doctor: {doctor_name} ({specialty})
- Clinic Branch: {branch_name}
- Date: {slot_date}
- Time: {slot_time}
- Consultation Fee: PKR {fee_pkr:,}

Please arrive 15 minutes prior to your scheduled time.
Google Calendar invitation has been synchronized.

Regards,
City Care Clinics Team
UAN: 042-111-CARE-00
"""

    body_html = f"""
<!DOCTYPE html>
<html>
<head>
  <style>
    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #1e293b; background-color: #f8fafc; margin: 0; padding: 20px; }}
    .card {{ max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }}
    .header {{ background: linear-gradient(135deg, #0284c7, #0369a1); color: #ffffff; padding: 24px; text-align: center; }}
    .header h1 {{ margin: 0; font-size: 22px; font-weight: 700; }}
    .header p {{ margin: 6px 0 0 0; font-size: 14px; opacity: 0.9; }}
    .token-badge {{ display: inline-block; background: #e0f2fe; color: #0369a1; padding: 6px 16px; border-radius: 20px; font-weight: 700; font-size: 16px; margin-top: 10px; }}
    .content {{ padding: 24px; }}
    .info-table {{ width: 100%; border-collapse: collapse; margin-top: 16px; }}
    .info-table td {{ padding: 10px 12px; border-bottom: 1px solid #f1f5f9; font-size: 14px; }}
    .label {{ font-weight: 600; color: #64748b; width: 35%; }}
    .value {{ font-weight: 600; color: #0f172a; }}
    .instructions {{ background: #f0fdf4; border-left: 4px solid #16a34a; padding: 14px; margin-top: 20px; border-radius: 4px; font-size: 13px; color: #166534; }}
    .footer {{ background: #f8fafc; padding: 16px; text-align: center; font-size: 12px; color: #94a3b8; border-top: 1px solid #e2e8f0; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="header">
      <h1>City Care Clinics</h1>
      <p>Appointment Confirmation</p>
      <div class="token-badge">Token: {token_number}</div>
    </div>
    <div class="content">
      <p>Assalam-o-Alaikum <strong>{patient_name}</strong>,</p>
      <p>Aap ki appointment kamyabi se book ho chuki hai. Details darj zail hain:</p>
      
      <table class="info-table">
        <tr><td class="label">Attending Doctor</td><td class="value">{doctor_name}</td></tr>
        <tr><td class="label">Specialty</td><td class="value">{specialty}</td></tr>
        <tr><td class="label">Clinic Branch</td><td class="value">{branch_name}</td></tr>
        <tr><td class="label">Date & Time</td><td class="value">{slot_date} at {slot_time}</td></tr>
        <tr><td class="label">Consultation Fee</td><td class="value">PKR {fee_pkr:,}</td></tr>
      </table>

      <div class="instructions">
        <strong>📋 Hidayat (Instructions):</strong><br>
        • Bara-e-meherbani waqt se 15 minute pehle reception par tashreef layen.<br>
        • Apne pichlay lab reports ya prescription sath le kar ayen.<br>
        • Kisi bhi tabdeeli ke liye 042-111-CARE-00 par call karein.
      </div>
    </div>
    <div class="footer">
      City Care Clinics — Healthcare Excellence Across Pakistan<br>
      Automated Healthcare Notification • Confidential Clinical Communication
    </div>
  </div>
</body>
</html>
"""

    return send_email(
        subject=subject,
        body_text=body_text,
        to_email=recipient_email,
        body_html=body_html
    )


def send_followup_reminder_email(
    patient_name: str,
    doctor_name: str,
    reminder_title: str,
    instructions: str,
    medicine_table: Optional[Dict[str, list]] = None,
    recipient_email: str = DEFAULT_RECIPIENT
) -> Dict[str, Any]:
    """
    Sends scheduled follow-up reminder emails (e.g. Day +1 check-in or Day +7 checkup).
    """
    subject = f"🔔 Care Reminder: {reminder_title} — City Care Clinics"

    meds_snippet = ""
    if medicine_table:
        meds_snippet = "\nDaily Medicines:\n"
        for slot, meds in medicine_table.items():
            if meds:
                meds_snippet += f"  - {slot}: {', '.join(meds)}\n"

    body_text = f"""
Assalam-o-Alaikum {patient_name},

This is an automated follow-up reminder from City Care Clinics regarding your consultation with {doctor_name}.

{reminder_title}
{instructions}
{meds_snippet}

Stay healthy!
City Care Clinics Patient Care Team
"""

    med_html = ""
    if medicine_table:
        med_html = "<div style='margin-top:16px; background:#f8fafc; padding:12px; border-radius:8px;'><strong>💊 Medicine Schedule:</strong><ul>"
        for slot, meds in medicine_table.items():
            if meds:
                med_html += f"<li><strong>{slot}:</strong> {', '.join(meds)}</li>"
        med_html += "</ul></div>"

    body_html = f"""
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; color: #334155; line-height: 1.5; padding: 20px;">
  <div style="max-width: 580px; margin: 0 auto; border: 1px solid #cbd5e1; border-radius: 8px; padding: 24px;">
    <h2 style="color: #0284c7; margin-top: 0;">City Care Clinics — Follow-up Reminder</h2>
    <p>Assalam-o-Alaikum <strong>{patient_name}</strong>,</p>
    <div style="background:#eff6ff; border-left:4px solid #3b82f6; padding:12px; margin:16px 0;">
      <strong>{reminder_title}</strong><br>
      {instructions}
    </div>
    {med_html}
    <p style="margin-top:20px; font-size:13px; color:#64748b;">
      Attending Physician: {doctor_name}<br>
      UAN: 042-111-CARE-00
    </p>
  </div>
</body>
</html>
"""

    return send_email(
        subject=subject,
        body_text=body_text,
        to_email=recipient_email,
        body_html=body_html
    )
