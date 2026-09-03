# Troubleshooting & Diagnostics Matrix — RealEstate Hub AI Voice Agent

This document provides a diagnostic troubleshooting matrix for identifying and resolving operational runtime issues.

---

## Diagnostic Matrix

| Issue Symptom | Root Cause | Resolution Procedure |
| :--- | :--- | :--- |
| **Email not arriving in Client Inbox or Sent folder** | Custom domain `From:` header mismatched with authenticated Gmail username causing DMARC/SPF drops. | Ensure `NOTIFICATION_SENDER_EMAIL` in `.env` matches `SMTP_USERNAME` (`samiworkspace11@gmail.com`). Verify `email_service.py` defaults sender to `self.username`. |
| **10 Duplicate Emails sent per call session** | Multiple webhook invocations triggering `book_appointment` without session locking. | Verify `mem.appointment_booked` lock is enabled in `memory.py` and checked in `app.py`. |
| **Zara states saved email aloud or asks for date/time** | Old system prompt instructions active in prompt cache. | Verify `system_prompt.py` rule lines 36-46 forbid stating email and restrict booking questions to Client Name/Email. |
| **Vapi Webhook 500 Internal Server Error** | Missing or invalid API key (`GEMINI_API_KEY` / `GROQ_API_KEY`). | Check `/healthz` and `/readyz` endpoints. The system will automatically fall back to Groq or Mock generator. Update API key in `.env`. |
| **Google Calendar Event creation fails** | Service account JSON missing or Calendar not shared with `client_email`. | Verify `google_ai_service_account.json` exists in project root. Share Google Calendar with service account email giving *Make changes to events* permission. |
| **Deepgram STT returns raw Urdu script (e.g. `جن کا سائیڈ بیز` ) causing intent detection miss** | Intent regex only checking English/Roman Urdu keywords. | Ensure `memory.py` and `nodes.py` include Urdu script keywords (`بک`, `وزٹ`, `سائیڈ`, `سکیجول`, `ای میل`). |
| **SQLite Database Locked Error (`sqlite3.OperationalError`)** | Concurrent write locks on SQLite database file. | Increase SQLite timeout parameter (`sqlite3.connect(db, timeout=20.0)`). In high concurrency deployments, migrate to PostgreSQL. |
| **VS Code displays red squiggly on `langgraph` import** | IDE using global Python interpreter instead of project `.venv`. | Press `Ctrl+Shift+P` $\rightarrow$ `Python: Select Interpreter` $\rightarrow$ choose `.\.venv\Scripts\python.exe`. Reload window. |

---

## Useful Diagnostic Commands

- **Check Service Health & Probes**:
  ```bash
  curl http://localhost:8000/readyz
  ```
- **Inspect Live Telemetry & Monitoring Events**:
  ```bash
  curl http://localhost:8000/api/v1/agent/trace
  ```
- **Run Full Production Verification Suite**:
  ```bash
  .venv\Scripts\python production_eval_and_deployment/run_production_suite.py
  ```
