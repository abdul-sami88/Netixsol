# Administrator Deployment & Operations Guide — RealEstate Hub AI Voice Agent

This guide walks system administrators through deploying, configuring, and operating the **UrduLish Real Estate AI Voice Agent System**.

---

## 1. System Requirements

- **Operating System**: Linux (Ubuntu 22.04 LTS recommended) / Windows Server 2022 / macOS
- **Python Runtime**: Python 3.11+ (or Docker Engine 24.0+)
- **Memory**: Minimum 4 GB RAM (8 GB recommended)
- **Disk**: 10 GB free storage

---

## 2. Environment Configuration (`.env`)

Create `.env` file in the project root based on [.env.production.template](file:///c:/Users/MEE/Anti-Gravity_projects/Real_estate_voice_agent/production_eval_and_deployment/deployment/.env.production.template):

```ini
# LLM Providers
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-3.5-flash
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile

# Speech Engine Providers
DEEPGRAM_API_KEY=your_deepgram_api_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM

# Vapi Integration
VAPI_API_KEY=your_vapi_api_key
VAPI_ASSISTANT_ID=your_vapi_assistant_id

# Server & Database Configuration
HOST=0.0.0.0
PORT=8000
DATABASE_URL=sqlite:///real_estate.db

# Google Calendar Integration
GOOGLE_CALENDAR_ID=primary
GOOGLE_SERVICE_ACCOUNT_FILE=google_ai_service_account.json
GOOGLE_CALENDAR_TIMEZONE=Asia/Karachi

# SMTP Email Dispatch Settings
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=samiworkspace11@gmail.com
SMTP_PASSWORD=your_gmail_app_password
NOTIFICATION_SENDER_EMAIL=samiworkspace11@gmail.com
```

---

## 3. Vapi Dashboard Portal Setup

1. Log into your [Vapi Dashboard](https://dashboard.vapi.ai).
2. Go to **Assistants** $\rightarrow$ **Create Assistant**.
3. Configure the following parameters:
   - **Name**: `RealEstate Hub UrduLish Executive (Zara)`
   - **Transcriber (STT)**:
     - Provider: `deepgram`
     - Model: `nova-2`
     - Language: `ur` (Urdu / UrduLish optimized)
   - **Model (Custom LLM Webhook)**:
     - Provider: `custom-llm`
     - URL: `https://your-domain.com/v1/chat/completions`
   - **Voice (TTS)**:
     - Provider: `elevenlabs`
     - Voice ID: `21m00Tcm4TlvDq8ikWAM` (Rachel / Warm Female)

---

## 4. Google Service Account & Calendar Setup

1. Create a Google Cloud Platform (GCP) project and enable **Google Calendar API**.
2. Create a Service Account and download the JSON key file. Save it as `google_ai_service_account.json` in the root directory.
3. Open your Google Calendar settings and share your calendar with the service account client email address (`client_email` in JSON) giving **Make changes to events** permission.

---

## 5. Gmail SMTP App Password Setup

1. Enable 2-Factor Authentication (2FA) on the sender Gmail account (`samiworkspace11@gmail.com`).
2. Generate an **App Password** (Select App: *Mail*, Device: *Other*).
3. Paste the generated 16-character App Password into `.env` under `SMTP_PASSWORD`.
4. Ensure `NOTIFICATION_SENDER_EMAIL` matches `samiworkspace11@gmail.com` to pass SPF/DMARC checks.

---

## 6. Docker Container Production Deployment

Run Docker Compose from project root:

```bash
docker-compose -f production_eval_and_deployment/deployment/docker-compose.yml up -d --build
```

Verify deployment health:
```bash
curl http://localhost:8000/readyz
```
Expected output: `{"status": "READY", "probe": "readiness", "ready_checks": {"database": true, "llm_api": true, "smtp": true}}`
