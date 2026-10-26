# API Documentation: Zarya Digital Bank AI Core

**Client:** Zarya Digital Bank  
**Service Version:** `1.0.0`  
**Base URL:** `http://localhost:8000`  
**Interactive Swagger UI:** `http://localhost:8000/docs`  

---

## 1. Health & Readiness

### `GET /api/health`
Returns system status, active RAG document count, and database connectivity.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "Zarya Digital Bank AI Engine",
  "guardrails": "active",
  "rag_indexed_docs": 7,
  "db": "connected"
}
```

---

## 2. Customer Banking Chat

### `POST /api/chat`
Main conversational endpoint protected by inbound/outbound guardrails and RAG context augmentation.

**Request Payload:**
```json
{
  "message": "Raast transfer ke daily limits aur charges bata dein?",
  "customer_phone": "0300-1234567",
  "include_rag": true
}
```

**Response (200 OK):**
```json
{
  "reply": "Zarya Digital Bank ki official policy ke mutabiq: Raast P2P transfers bilkul muft (Rs. 0) hain aur rozana limit Rs. 500,000 hai...",
  "guardrails_passed": true,
  "blocked_reason": null,
  "rag_used": true,
  "retrieved_policies": [
    "Daily Digital & ATM Limits",
    "Schedule of Bank Charges (SOC) - Digital Transfers & 1LINK"
  ],
  "created_ticket": null
}
```

**Response when Guardrail is Triggered (Scam / Phishing):**
```json
{
  "reply": "Zarya Bank kabhi bhi call ya SMS par aap ka OTP ya PIN nahi maangta. Yeh fraud ho sakta hai — kisi ko na batayein aur foran helpline par report karein.",
  "guardrails_passed": false,
  "blocked_reason": "SCAM_DETECTION",
  "rag_used": false,
  "retrieved_policies": [],
  "created_ticket": null
}
```

---

## 3. Complaint Ticketing & Tool Calling

### `POST /api/tickets`
Creates a formal dispute ticket with automated State Bank of Pakistan (SBP) SLA turnaround time calculation.

**Request Payload:**
```json
{
  "category": "ATM_DISPUTE",
  "priority": "MEDIUM",
  "amount": 25000.0,
  "reference_id": "TXN-984210",
  "summary": "ATM se cash deduct hua lekin machine se nahi nikla",
  "customer_details": "HBL ATM Saddar branch Karachi",
  "customer_phone": "0300-9876543"
}
```

**Response (200 OK):**
```json
{
  "ticket_id": "ZAR-2026-508817",
  "category": "ATM_DISPUTE",
  "priority": "MEDIUM",
  "amount": 25000.0,
  "reference_id": "TXN-984210",
  "tat_days": 10,
  "status": "OPEN",
  "escalated_to_human": false,
  "escalation_reason": null,
  "customer_message_ur": "Aap ki shikayat darj kar li gayi hai. Ticket ID: ZAR-2026-508817. SBP regulations ke mutabiq is category ka resolution time 10 working days hai."
}
```

---

## 4. Customer Feedback & Continuous Improvement

### `POST /api/feedback`
Captures 👍/👎 ratings and reviewer corrections for automated DPO preference pair generation.

**Request Payload:**
```json
{
  "score": 0,
  "comment": "Vague response regarding debit card international e-commerce activation",
  "timestamp": "2026-10-26T12:00:00Z"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "recorded": true,
  "message": "Feedback ingested into continuous improvement queue"
}
```

---

## 5. Dynamic RAG Policy Updating

### `POST /api/rag/update`
Allows bank operations officers to update fee schedules in real-time without retraining the model.

**Request Payload:**
```json
{
  "doc_id": "SOC-2026-002",
  "content_ur": "Zarya PayPak Debit Card ki annual renewal fee Rs. 1,500 plus FED hai.",
  "content_en": "Zarya PayPak Debit Card annual renewal fee is PKR 1,500 plus FED."
}
```
