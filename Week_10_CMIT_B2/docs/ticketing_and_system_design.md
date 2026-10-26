# Task 5: Ticketing Tools, Regulatory Escalation & FastAPI Architecture

**Client:** Zarya Digital Bank  
**Document:** Week 10 — Day 4: Task 5 System Design & Complaint Escalation  
**Author:** Antigravity Senior AI/ML Engineering Lead  
**Backend Framework:** FastAPI / SQLite / Pydantic  
**Core Endpoints:** [`src/app.py`](file:///c:/Users/MEE/Anti-Gravity_projects/Fine-tuning-llm/src/app.py)  

---

## 1. End-to-End System Pipeline

The production service connects all Day 4 components into a unified, secure microservice:

```
[Customer Mobile / Web App]
            │
            ▼ (POST /api/chat)
+-----------------------------------------------------------+
| 1. Inbound Guardrails (Scam / Credential / Injection)     |
+-----------------------------------------------------------+
            │ (Pass)
            ▼
+-----------------------------------------------------------+
| 2. PII Masker (Redacts CNIC / Phone before Logging)       |
+-----------------------------------------------------------+
            │
            ▼
+-----------------------------------------------------------+
| 3. Intent & Dispute Detector                              |
|    - Is customer reporting a dispute / fraud?             |
|    - If YES: Invokes Ticketing Tool                       |
+-----------------------------------------------------------+
            │
            ├─────────────────────────────────────────┐
            ▼                                         ▼
+-----------------------------------+   +-----------------------------------+
| 4. Multilingual RAG Retrieval     |   | 5. Automated SBP Ticketing Engine |
|    - Retrieves relevant SOC rules |   |    - Computes Regulatory TAT      |
|    - Injects into LLM prompt      |   |    - Assesses Human Escalation    |
+-----------------------------------+   +-----------------------------------+
            │                                         │
            ▼                                         ▼
+-----------------------------------------------------------+
| 6. Qwen 2.5 3B Sovereign Inference Engine                 |
|    - Generates empathetic UrduLish response               |
+-----------------------------------------------------------+
            │
            ▼
+-----------------------------------------------------------+
| 7. Outbound Guardrails (Card & CVV Redaction)             |
+-----------------------------------------------------------+
            │
            ▼
[Customer Response + Ticket ID + SBP SLA Turnaround Time]
```

---

## 2. Regulatory Complaint TAT & SBP SLAs

Turnaround times are hardcoded to match the **State Bank of Pakistan Consumer Protection Framework**:

| Complaint Category | SBP Regulatory TAT | Priority Default | Escalation Criteria |
| :--- | :--- | :--- | :--- |
| **ATM Cash Not Dispensed** | **10 Business Days** | MEDIUM / HIGH | If amount $> \text{Rs. } 50,000$ |
| **Raast Failed Transfer Reversal** | **2 Business Days** (48 Hours) | MEDIUM | If unreversed $> 48\text{ hrs}$ |
| **Interbank Transfer (IBFT)** | **15 Business Days** | HIGH | Multi-bank routing failure |
| **Unauthorized Fraud / Skimming** | **30 Business Days** | **CRITICAL** | **Always Escalate to Fraud Desk** |
| **Debit Card Issues** | **7 Business Days** | LOW / MEDIUM | Stolen / Blocked card |

---

## 3. Human Escalation Heuristics

The ticketing engine evaluates 4 independent escalation triggers:
1. **Financial Threshold:** Disputed amount $\ge \text{Rs. } 50,000$.
2. **Category Risk:** Any case tagged as `UNAUTHORIZED_TRANSACTION` or `FRAUD`.
3. **Assigned SLA Priority:** Priority flagged as `HIGH` or `CRITICAL`.
4. **Distress Sentiment:** Inbound message contains escalation keywords (*"police"*, *"court"*, *"lout liya"*, *"barbaad"*, *"sbp complaint"*).

When escalated:
- Ticket status is marked as `ESCALATED_HUMAN_QUEUE`.
- Detailed escalation reasoning is attached.
- Customer is informed that a senior fraud / operations specialist is assigned.

---

## 4. FastAPI Endpoints Reference

| Endpoint | Method | Purpose | Input / Output |
| :--- | :--- | :--- | :--- |
| `/api/health` | `GET` | Health check & service readiness | Returns active RAG document count and DB status |
| `/api/chat` | `POST` | Core chatbot interaction with Guardrails + RAG | Ingests `{message, customer_phone}`, returns `{reply, guardrails_passed, created_ticket}` |
| `/api/tickets` | `POST` | Direct complaint ticket generation tool | Ingests ticket schema, creates record with SBP TAT |
| `/api/tickets/{ticket_id}`| `GET` | Ticket status and SLA tracking | Returns ticket metadata and escalation status |
| `/api/rag/update` | `POST` | Dynamic policy update without retraining | Ingests `{doc_id, content_ur, content_en}`, re-indexes on disk |
