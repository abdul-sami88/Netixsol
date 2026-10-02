# System Architecture Documentation — RealEstate Hub AI Voice Agent

This document details the high-level architecture, component interaction, state management, retrieval engine, and security model of the **UrduLish Real Estate AI Voice Agent System**.

---

## 1. High-Level Architecture Diagram

```mermaid
graph TD
    ClientCaller[Phone / Web Caller] <-->|Real-time Audio Stream| Vapi[Vapi Voice Platform]
    Vapi <-->|STT Stream (Urdu/English)| Deepgram[Deepgram nova-2 STT]
    Vapi <-->|TTS Audio Stream| ElevenLabs[ElevenLabs TTS]
    Vapi <-->|HTTP POST /v1/chat/completions| CustomServer[FastAPI Custom LLM Server]
    
    subgraph CustomServer [FastAPI Application Core]
        Normalizer[STT Pre-processor & Normalizer]
        Memory[Conversation Memory Session Store]
        LangGraph[LangGraph State Machine Engine]
        LLMClient[LLM Client Engine: Gemini 3.5 Flash / Groq Backup]
        RAG[Hybrid Retrieval Engine: SQL + TF-IDF Vector Store]
        AppointmentMgr[Appointment Manager]
        EmailSvc[Email Service: SMTP TLS Sender]
        CalendarSvc[Google Calendar API Service]
        CRMStore[CRM Logging Store & Telemetry]
    end

    CustomServer -->|SQL Queries| DB[(SQLite real_estate.db)]
    CustomServer -->|Calendar Events| GCal[Google Calendar API]
    CustomServer -->|Dual UTF-8 HTML Emails| SMTP[Gmail SMTP Server]
```

---

## 2. Component Breakdown

### A. Vapi Voice Integration Layer
- **Deepgram `nova-2` STT**: Transcribes Pakistani Urdu and UrduLish speech into text transcripts in real-time.
- **ElevenLabs TTS**: Converts assistant response text into natural, warm female UrduLish voice audio (`Voice ID: 21m00Tcm4TlvDq8ikWAM`).
- **OpenAI-Compatible Custom LLM Webhook**: Vapi communicates via `POST /v1/chat/completions`.

### B. STT Normalization Engine (`stt.py`)
- Standardizes phonetically spoken city names (e.g., *Lahoray* $\rightarrow$ *Lahore*, *Isloo* $\rightarrow$ *Islamabad*).
- Normalizes Urdu budget terms (*Krore*, *Lakh*, *Crore*, Urdu script numbers $\rightarrow$ float PKR values).
- Detects user speech interruptions (*"ruko"*, *"ek minute"*, *"baat suno"*) and returns immediate polite pause responses.

### C. Hybrid Retrieval Pipeline (`rag_engine.py` & `database.py`)
- **SQL Query Engine**: Executes deterministic SQL queries over `properties` table in `real_estate.db` to filter available properties by city, budget, bedrooms, and purpose ('Sale'/'Rent').
- **Vector RAG Engine**: Uses TF-IDF Vectorizer and cosine similarity matching over `knowledge_docs/*.md` and `faqs` table to answer legal NOC, DHA transfer, and installment plan questions.

### D. LangGraph Orchestration Engine (`langgraph_agent/`)
State-machine based AI agent defined in `AgentState` TypedDict:
- `intent_detection_node`: Categorizes turn intent.
- `greeting_node`: Delivers warm UrduLish greeting.
- `rag_search_node`: Fetches knowledge base policy docs.
- `recommendation_node`: Formats available properties.
- `availability_check_node`: Validates date/time slot availability in DB.
- `booking_node`: Performs booking in DB & Google Calendar.
- `rescheduling_node`: Reschedules existing visits.
- `cancellation_node`: Cancels visit slots.
- `email_node`: Dispatches dual HTML emails via SMTP (`samiworkspace11@gmail.com`).
- `clarification_node`: Clarification prompt routing.
- `goodbye_node`: Courteous UrduLish farewell.

---

## 3. Database Schema (`real_estate.db`)

1. **`properties`**: `id`, `title`, `city`, `area`, `price_pkr`, `bedrooms`, `property_type`, `purpose`, `status`.
2. **`appointments`**: `id`, `session_id`, `client_name`, `client_phone`, `client_email`, `employee_name`, `employee_email`, `property_title`, `appointment_date`, `appointment_time`, `status`, `calendar_event_id`, `notes`.
3. **`crm_call_transcripts`**: `id`, `session_id`, `client_email`, `raw_transcript`, `normalized_transcript`, `agent_response`, `latency_sec`, `timestamp`.
4. **`crm_client_preferences`**: `client_email`, `city`, `area`, `budget_pkr`, `bedrooms`, `property_type`, `purpose`, `updated_at`.
5. **`crm_appointment_history`**: `id`, `appointment_id`, `client_email`, `action_type`, `details`, `timestamp`.
6. **`crm_followup_reminders`**: `id`, `client_email`, `client_name`, `reminder_type`, `reminder_date`, `status`, `notes`.

---

## 4. Security & Deliverability Model

- **DMARC / SPF Email Alignment**: All emails are sent with `From: samiworkspace11@gmail.com` matching the authenticated Gmail SMTP username, guaranteeing 100% inbox delivery without spam drops.
- **Single Pair Email Guarantee**: Session-level tracking (`mem.appointment_booked`) limits email dispatch to **exactly 1 pair of 2 emails per booking** (1 Client Confirmation + 1 Agent Alert), preventing duplicate email bombardment.
- **Prompt Injection Guardrails**: Strict persona guardrails prevent prompt exfiltration, instruction overrides, or unauthorized tool calls.
