# OpenAPI & REST API Specification — RealEstate Hub AI Voice Agent

This document provides complete API reference documentation for the Vapi Custom LLM Webhook, REST Chat API, LangGraph AI Agent API, CRM Store endpoints, and Kubernetes Health Probes.

---

## 1. Vapi Custom LLM Webhook Endpoint

### `POST /v1/chat/completions`
Standard OpenAI-compatible completions endpoint designed specifically for Vapi Webhook integration.

#### Headers
- `Content-Type`: `application/json`
- `x-vapi-call-id` / `x-call-id`: Unique Vapi call session identifier

#### Request Payload
```json
{
  "model": "urdu-real-estate-llm",
  "messages": [
    {"role": "user", "content": "Assalam-o-Alaikum, mujhe Lahore DHA Phase 6 mein house book karna hai"}
  ],
  "stream": false,
  "temperature": 0.6,
  "max_tokens": 300
}
```

#### Response Payload (`200 OK`)
```json
{
  "id": "chatcmpl-1788260472",
  "object": "chat.completion",
  "created": 1788260472,
  "model": "urdu-real-estate-llm",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Assalam-o-Alaikum sir! Main ne aap ke email par confirmation mail bhej di hai aur Google Calendar invite schedule kar diya hai."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {"prompt_tokens": 120, "completion_tokens": 45, "total_tokens": 165},
  "meta": {
    "latency_sec": 1.25,
    "retrieved_properties_count": 2,
    "stt_normalized_text": "Assalam-o-Alaikum, mujhe Lahore DHA Phase 6 mein house book karna hai"
  }
}
```

---

## 2. REST & Web Dashboard Endpoints

### `POST /api/v1/chat`
Main web chat endpoint for web dashboard client.

#### Request Payload
```json
{
  "session_id": "web_session_101",
  "message": "Lahore mein 3 Crore ka ghar dikhayen",
  "stream": false
}
```

#### Response Payload (`200 OK`)
```json
{
  "session_id": "web_session_101",
  "reply": "Acha... Lahore mein 3 Crore ke budget mein hamare paas Lake City Sector M mein 10 Marla house 3.22 Crore ka available hai.",
  "memory_summary": "City: Lahore, Max Budget: 3.22 Crore",
  "matched_properties": [...],
  "assigned_agent": {"name": "Tariq Mahmood", "phone": "+92-300-8451199"},
  "stt_normalized_text": "Lahore mein 3 Crore ka ghar dikhayen",
  "booked_appointment": null
}
```

---

## 3. LangGraph AI Agent Endpoints

### `POST /api/v1/agent/chat`
Executes full LangGraph Agent state machine orchestration with state tracking, intent routing, tool calling, and validation guardrails.

#### Request Payload
```json
{
  "session_id": "langgraph_demo_session",
  "message": "DHA transfer procedure requirements kya hain?"
}
```

#### Response Payload (`200 OK`)
```json
{
  "session_id": "langgraph_demo_session",
  "reply": "Ji bilkul sir! DHA transfer ke liye CNIC copies, Allotment Letter, NDC, aur tax paid challans darkaar hotay hain.",
  "intent": "rag",
  "user_profile": {"session_id": "langgraph_demo_session", "client_email": "samiworkspace11@gmail.com"},
  "property_preferences": {"city": "Lahore"},
  "appointment_status": {"status": null, "is_available": true},
  "execution_trace": [
    {"node": "intent_detection_node", "timestamp": "2026-09-01T17:25:08Z", "intent": "rag"},
    {"node": "rag_search_node", "timestamp": "2026-09-01T17:25:11Z", "intent": "rag"}
  ]
}
```

### `GET /api/v1/agent/trace`
Returns annotated execution traces of node transitions (Task 5).

#### Query Parameters
- `session_id` (optional): Filter trace events for a specific session ID.

---

## 4. Appointment Management Endpoints

- `POST /api/v1/appointments/book`: Book appointment directly.
- `POST /api/v1/appointments/reschedule`: Reschedule existing appointment ID.
- `POST /api/v1/appointments/cancel`: Cancel existing appointment ID.
- `GET /api/v1/appointments`: List latest 50 appointment records.

---

## 5. CRM Store Endpoints

- `GET /api/v1/crm/transcripts`: Fetch logged call transcripts.
- `GET /api/v1/crm/preferences`: Fetch client preference profiles.
- `GET /api/v1/crm/history`: Fetch appointment audit history.
- `GET /api/v1/crm/followups`: Fetch auto-generated follow-up call reminders.

---

## 6. Health & Readiness Probes

- `GET /healthz`: Basic Liveness Probe (`{"status": "UP"}`).
- `GET /livez`: Runtime Process Probe.
- `GET /readyz`: Deep Readiness Probe verifying SQLite DB, Gemini/Groq API keys, and SMTP server reachability.
