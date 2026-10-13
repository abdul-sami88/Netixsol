# Week 9 — Day 5: Task 3 — Production Deployment, Health Monitoring & Clinical Audit Trail

## 1. Executive Summary
This document outlines the deployment architecture for City Care Clinics' Multi-Agent Healthcare Platform on Render. To enable immediate zero-latency deployment without dependency on external cloud database services (e.g. Supabase / AWS RDS), the application utilizes a self-contained, pre-seeded SQLite relational database alongside an embedded ChromaDB vector store.

---

## 2. Architecture & Containerization

### Dockerfile Specification
- **Base Image:** `python:3.11-slim`
- **Dynamic Port Support:** Configured for Render’s dynamic `$PORT` environment variable via `CMD ["sh", "-c", "uvicorn src.server.app:app --host 0.0.0.0 --port ${PORT:-8000}"]`.
- **Pre-seeded Relational Store:** `data/city_care_clinics.db` (SQLite containing 5 clinic branches, 30 doctors, 500 patients, conditions, prescriptions, and appointments).
- **Embedded Vector Knowledge Base:** `data/chroma_db/chroma.sqlite3` (Medical RAG embeddings for clinical guidelines and protocols).
- **Environment Fallback:** Defaults `DATABASE_URL` to `sqlite:///data/city_care_clinics.db` if not specified.

---

## 3. Health Check & Observability Endpoint

A production `/health` endpoint has been added to [src/server/app.py](file:///c:/Users/MEE/Anti-Gravity_projects/AI_healthcare_orchestration/src/server/app.py):

### Endpoint: `GET /health`
```json
{
  "status": "healthy",
  "service": "City Care Clinics Multi-Agent Healthcare Platform",
  "timestamp": "2026-10-13T04:58:11.374344Z",
  "database": {
    "type": "sqlite",
    "status": "connected",
    "branches": 5,
    "practitioners": 30
  },
  "knowledge_rag": {
    "type": "chromadb",
    "status": "connected",
    "file_size_kb": 764.0
  },
  "agents": {
    "supervisor": "ready",
    "triage": "ready",
    "prescription_safety": "ready",
    "clinical_summary": "ready"
  }
}
```
**Verification:** Tested and verified returning `200 OK` in under 42ms.

---

## 4. Clinical Audit Trail Logging

Every HTTP transaction (excluding static assets) passes through the `audit_logging_middleware`:
- **File Target:** `data/audit_trail.log`
- **Standard Output:** Structured console logging for Render log streaming.
- **Audit Schema:**
  - `timestamp`: UTC ISO-8601 timestamp.
  - `client_ip`: Origin IP address.
  - `method`: HTTP method (`GET`, `POST`, etc.).
  - `path`: Accessed route.
  - `status_code`: HTTP response status code.
  - `duration_ms`: Total transaction processing latency.

---

## 5. Render Quick-Start Deployment Instructions

1. **Initialize Git & Commit:**
   ```bash
   git init
   git add .
   git commit -m "feat: complete day 5 capstone with SQLite, ChromaDB, and Dockerfile"
   ```
2. **Push to GitHub:**
   ```bash
   git remote add origin https://github.com/<YOUR_USERNAME>/<YOUR_REPO>.git
   git branch -M main
   git push -u origin main
   ```
3. **Deploy on Render:**
   - Log into [Render Dashboard](https://dashboard.render.com).
   - Click **New +** -> **Web Service**.
   - Select your GitHub repository.
   - Choose **Docker** as the Runtime (Render will automatically detect `Dockerfile`).
   - Add Environment Variables in Render:
     - `GROQ_API_KEY`: `<Your Groq API Key>`
     - `GEMINI_API_KEY`: `<Your Google Gemini API Key>`
   - Click **Deploy Web Service**.
   - Your live clinic portal will be available at `https://<service-name>.onrender.com`.
