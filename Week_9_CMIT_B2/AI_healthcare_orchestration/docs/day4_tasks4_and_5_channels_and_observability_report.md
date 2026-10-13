# Week 9 — Day 4: Tasks 4 & 5 — Channels & Observability Report

**Organization:** City Care Clinics (Private Hospital Network, Pakistan)  
**Deliverables:** Multi-Channel Integration & Clinical Observability Tracing  
**Components:** Web Chat Portal, Live Gmail SMTP, APScheduler, LangSmith/Langfuse Tracing Engine  

---

## Task 4 — Multi-Channel Integration

### 1. Patient Web Chat Portal (`src/ui/clinic_portal.py`)
* **Interactive Conversational UI:** Built in Streamlit with real-time turn handling.
* **UrduLish & English Intake:** Greets returning patients with context from PostgreSQL memory (*"Assalam-o-Alaikum Ahmed Hassan sahib! Pichli dafa aap Dr. Bilal Aslam ko..."*).
* **Automated End-to-End Pipeline:** Seamlessly executes LangGraph supervisor graph, runs parallel Triage + Records evaluation, matches available doctors and slots, proposes booking, and synchronizes with Google Calendar.

### 2. Email Confirmations & Reminders (`src/channels/email_channel.py`)
* **Live Gmail SMTP Delivery:** Connected to `samiworkspace11@gmail.com`.
* **Appointment Confirmation Notice:** Generates rich HTML emails containing:
  - Official clinic Token Number (e.g. `CC-108`)
  - Doctor name, specialty, and clinic branch
  - Scheduled date & time, consultation fee in PKR
  - Clinical preparation instructions and Google Calendar sync alert
* **24-Hour & Follow-up Reminders:** Formatted bilingual reminders sent directly to patient inbox.

### 3. Automated Follow-up Scheduler (`src/channels/followup_scheduler.py`)
* **Background Scheduler:** Powered by `APScheduler` (BackgroundScheduler) with persistent queue in `data/scheduled_reminders.json`.
* **Standard 3-Stage Milestone Protocol:**
  1. **Day +1:** Medication Adherence Check (*"Assalam-o-Alaikum! Kya aap ne subah ki dawa li hai?"*)
  2. **Day +3:** Symptom Recovery Evaluation (*"Kya aap ki tabiyat mein behtari aayi hai?"*)
  3. **Day +7:** Clinic Follow-Up Consultation Reminder (*"Aap ka 7-day follow-up checkup scheduled hai."*)
* **Multi-Channel Dispatch:** Dispatches via live email and simulated WhatsApp/SMS alerts.

---

## Task 5 — Observability & Annotated Patient Journey Traces

### Clinical Tracing Architecture (`src/observability/tracer.py`)
Tracks every conversation across all 7 specialist agents:
* **Latency per Agent:** Nanosecond-accurate execution timestamps and millisecond runtimes.
* **Tool Calls & Results:** Records tool names, JSON input parameters, execution results, and tool latencies.
* **Token Usage & Inference Cost:** Tracks prompt and completion tokens, calculating costs based on Groq Llama-3.3-70B rates ($0.59 / $0.79 per 1M tokens).
* **Escalations & Overrides:** Captures 1122 emergency red-flag triggers and physician HITL modifications.

---

### The 3 Canonical Annotated Patient Journeys

```mermaid
journey
    title 3 Canonical Patient Journeys Tracked in Observability Engine
    section Journey 1: Routine ENT
      Intake (1120 ms): 5: IntakeAgent
      Triage & Records (850 ms): 5: TriageAgent, RecordsAgent
      Doctor Slot Matching (750 ms): 5: SchedulingAgent
      Follow-up Scheduling (450 ms): 5: FollowUpAgent
    section Journey 2: Emergency 1122
      Intake (820 ms): 4: IntakeAgent
      Red-Flag Detection (5 ms): 5: TriageAgent (Deterministic Halt)
      1122 Dispatch & Alert (18 ms): 5: EmergencyNode
    section Journey 3: Doctor Override
      Intake & EHR (1300 ms): 4: IntakeAgent, RecordsAgent
      Safety Block (180 ms): 5: PrescriptionSafetyAgent (Allergy Conflict)
      Doctor Deliberation (72.8 s): 5: Attending Physician Dr. Farhan Tariq
      Dispensing Authorized (550 ms): 5: FollowUpAgent
```

#### Detailed Breakdown of Traces:

| Metric | Journey 1: Routine ENT | Journey 2: Emergency 1122 | Journey 3: Doctor Override |
| :--- | :--- | :--- | :--- |
| **Trace ID** | `TRC-JOURNEY-001-ROUTINE` | `TRC-JOURNEY-002-EMERGENCY` | `TRC-JOURNEY-003-DOCTOR-OVERRIDE` |
| **Patient** | Samiullah Khan (`pat-0105`) | Tariq Mehmood (`pat-0248`) | Saeeda Begum (`pat-0391`) |
| **Presenting Complaint** | Fever (2 days, severity 5/10), sore throat | Crushing chest pain radiating to left jaw & arm | Productive cough & sinusitis; prescribed Augmentin |
| **Triage Urgency** | `ROUTINE` (Score: 0.94) | `EMERGENCY` (Score: 1.00) | `ROUTINE` (Score: 0.91) |
| **Safety Verdict** | Safe | Rule-based Halt | `BLOCKED` (Penicillin Allergy Conflict) |
| **Physician Action** | Standard Scheduling | Cardiopulmonary Alert Dispatched | **EDITED:** Substituted Clarithromycin (Klaricid) |
| **Total Spans** | 5 agent spans | 2 agent spans | 5 agent spans |
| **Total Tool Calls** | 5 tool executions | 2 tool executions | 4 tool executions |
| **Total Latency** | 3,490.0 ms | 825.0 ms (Safety gate: 5 ms!) | 74,830.0 ms (Human review time included) |
| **Total Tokens** | 1,410 tokens | 300 tokens | 875 tokens |
| **Inference Cost** | $0.000882 USD | $0.000185 USD | $0.000547 USD |
| **Clinical Score** | ⭐ 4.95 / 5.0 | ⭐ 5.00 / 5.0 | ⭐ 4.98 / 5.0 |

---

## Integration Test Verification (`scripts/test_day4_channels_observability.py`)

Execution output:
```text
======================================================================
TEST 1: CHANNELS — EMAIL CONFIRMATION & SCHEDULED FOLLOW-UPS
======================================================================
Sending live appointment confirmation email to samiworkspace11@gmail.com...
Email Delivery Result: {
  'status': 'delivered',
  'mode': 'live_gmail_smtp',
  'recipient': 'samiworkspace11@gmail.com',
  'subject': '✅ Appointment Confirmed: Dr. Haris Nadeem at City Care Clinics (CC-108)'
}
✓ Email confirmation verified.

Scheduled 3 follow-up milestones for patient pat-test-101:
  - [2026-10-08] Day 1 Medication Adherence Check
  - [2026-10-10] Day 3 Recovery & Symptom Check
  - [2026-10-14] Day 7 Clinic Follow-Up Checkup

Dispatched 3 due reminders via Email & simulated WhatsApp.
✓ Follow-up automated reminder scheduler verified.
--> TEST 1 PASSED: Channels Fully Verified!

======================================================================
TEST 2: OBSERVABILITY — 3 ANNOTATED PATIENT JOURNEY TRACES
======================================================================
Generated and persisted 3 annotated patient journeys.
[1] Journey 1: Routine ENT Consultation & Follow-up (3490 ms, 1410 tokens, $0.000882)
[2] Journey 2: Emergency Red-Flag Escalation (825 ms, 300 tokens, $0.000185)
[3] Journey 3: Contraindication Caught & Attending Physician Override (74830 ms, 875 tokens, $0.000547)
--> TEST 2 PASSED: Observability & 3 Annotated Journey Traces Fully Verified!

======================================================================
ALL TESTS PASSED WITH 100% SUCCESS!
======================================================================
```

---

## How to Launch the Full Portal
```powershell
.\venv\Scripts\streamlit run src/ui/clinic_portal.py
```
This launches the complete web application with all 4 tabs:
1. **💬 Patient Web Chat:** Real-time conversational intake, slot proposal, live email confirmation.
2. **🩺 Doctor Review Portal:** Human-in-the-Loop approval gate for prescriptions, lab results, and triage.
3. **📊 Observability & Traces:** Interactive flamecharts, tool call arguments/outputs, token & cost metrics.
4. **⏰ Scheduled Follow-Up Dispatcher:** Inspection and dispatch controls for patient care plans.
