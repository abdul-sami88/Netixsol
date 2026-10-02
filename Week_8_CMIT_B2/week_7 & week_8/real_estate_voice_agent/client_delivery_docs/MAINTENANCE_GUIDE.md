# Production Monitoring & Maintenance Plan — RealEstate Hub AI Voice Agent

This document defines operational Service Level Agreements (SLAs), latency thresholds, uptime targets, model retraining schedules, database maintenance, backup strategies, and security review cadences.

---

## 1. Operational SLAs & Performance Targets

| Metric | Target SLA | Critical Threshold Alert | Action on Breach |
| :--- | :--- | :--- | :--- |
| **Average Per-Turn Latency** | $< 1.50$ seconds | $> 2.50$ seconds | Fallback from Gemini to Groq / Mock |
| **p90 Latency** | $< 2.00$ seconds | $> 3.50$ seconds | Auto-scale worker threads |
| **p99 Latency** | $< 5.00$ seconds | $> 8.00$ seconds | Restart Uvicorn workers |
| **System Uptime** | **99.9% High Availability** | $< 99.5\%$ | Trigger Kubernetes container failover |
| **Conversation Success Rate** | $\ge 95.0\%$ | $< 90.0\%$ | Trigger prompt regression audit |
| **Booking Success Rate** | $\ge 98.0\%$ | $< 92.0\%$ | Inspect Calendar & SQLite DB lock |
| **Tool Failure Rate** | **0.0%** | $> 1.0\%$ | Inspect exception log & restart service |
| **RAG Retrieval Accuracy** | $\ge 90.0\%$ | $< 80.0\%$ | Re-index vector knowledge embeddings |
| **Hallucination Rate** | **0.0%** | $> 0.5\%$ | Enforce strict DB SQL status filter |

---

## 2. Model & STT Retraining Schedule

- **Cadence**: **Weekly (Every Sunday 02:00 PKT)**
- **Scope**:
  - Update custom Deepgram STT vocabulary dictionary with new local Pakistani area names (e.g., *DHA Phase 9 Prism*, *Park View City*, *Eighteen Islamabad*).
  - Fine-tune phonetic STT normalization rules in `stt.py` based on un-normalized transcripts logged in `crm_call_transcripts`.

---

## 3. Vector Database Refresh Schedule

- **Cadence**: **Weekly (Every Monday 04:00 PKT)**
- **Scope**:
  - Re-calculate TF-IDF vector embeddings over updated knowledge documents in `knowledge_docs/*.md`.
  - Ingest newly added FAQs from `faqs` database table into `RAGEngine` vector matrix.

---

## 4. System Prompt Review & Auditing

- **Cadence**: **Bi-Weekly**
- **Scope**:
  - Run the Task 2 Security Audit (`prompt_injection_security.py`) to verify prompt injection defenses.
  - Review persona compliance (verify Zara never speaks pre-saved emails or asks for date/time).

---

## 5. Backup & Disaster Recovery Strategy

- **Database Backup**:
  - **Automated Daily Snapshot**: Daily SQLite DB binary backup stored at `/backups/real_estate_YYYYMMDD.db`.
  - **Retention Policy**: 30 rolling daily backups, 12 monthly archives.
  - **Recovery Time Objective (RTO)**: $< 5$ minutes.
  - **Recovery Point Objective (RPO)**: $< 1$ hour.
- **Config & Secret Backup**:
  - Encrypted backup of `.env` files and Google Service Account credentials stored in offsite Azure Blob / AWS S3 key vault.

---

## 6. Security Review Cadence

- **Cadence**: **Monthly**
- **Scope**:
  - Rotate Gmail SMTP App Passwords & API Keys.
  - Run vulnerability scan on Docker container image (`trivy image real-estate-voice-agent:latest`).
  - Audit database access logs & API authentication headers.
