# Khan & Associates — REST API Documentation

**Base URL:** `http://localhost:8000`  
**Interactive Swagger UI:** `http://localhost:8000/docs`  
**OpenAPI Specification:** `http://localhost:8000/openapi.json`

---

## 1. Authentication & Security Headers

Every request to protected endpoints should include user identification and matter context headers for ethical wall enforcement:
- `X-User-ID`: Attorney identifier (e.g. `attorney_ahmed`, `partner_khan`)
- `X-Matter-ID`: Matter docket number (e.g. `KA-MATTER-101`)

---

## 2. Health & Diagnostic Endpoints

### `GET /health`
Returns high-level health status of the application.
```json
{
  "status": "HEALTHY",
  "version": "1.0.0",
  "timestamp": "2026-11-16T12:00:00Z"
}
```

### `GET /health/ready`
Kubernetes/Docker readiness probe; verifies Knowledge Graph and Playbook loading.
```json
{
  "status": "READY",
  "graph_nodes": 2776,
  "playbook_rules": 6
}
```

### `GET /health/live`
Kubernetes/Docker liveness probe.
```json
{
  "status": "LIVE"
}
```

---

## 3. Core Legal Intelligence Endpoints

### `POST /api/research`
Executes cited legal research across Pakistani statutes, Supreme Court judgments, and Knowledge Graph.

**Request Body:**
```json
{
  "query": "Which Supreme Court judgments interpreted Section 23 of the Contract Act, and were any of them later overruled?",
  "matter_id": "KA-MATTER-101",
  "user_id": "attorney_ahmed"
}
```

**Response Body:**
```json
{
  "query": "Which Supreme Court judgments interpreted Section 23 of the Contract Act, and were any of them later overruled?",
  "routed_engine": "GRAPH_RAG",
  "route_confidence": 0.96,
  "short_answer": "The Supreme Court of Pakistan interpreted Section 23 of the Contract Act, 1872 across multiple judgments... Crucially, 1998 SCMR 1120 was later expressly OVERRULED by a 5-member Full Bench in 2021 SCMR 105.",
  "explanation": "Section 23 of the Contract Act, 1872 stipulates that the consideration or object of an agreement is unlawful if it is forbidden by law...\n\n### Precedent Overruling Analysis:\n1998 SCMR 1120 was explicitly OVERRULED by 2021 SCMR 105...",
  "overruled_detected": true,
  "overruled_cases": ["1998 SCMR 1120"],
  "valid_precedents": ["PLD 1990 SC 48", "2015 SCMR 1423", "2021 SCMR 105"]
}
```

---

### `POST /api/review`
Scans contract clauses against the Khan & Associates Playbook and computes risk scores.

**Request Body:**
```json
{
  "contract_title": "Master Services Agreement",
  "matter_id": "KA-MATTER-101",
  "user_id": "attorney_ahmed",
  "clauses": [
    {
      "clause_index": 1,
      "heading": "Governing Law",
      "text": "This Agreement shall be governed by the laws of New York, USA."
    }
  ]
}
```

**Response Body:**
```json
{
  "contract_title": "Master Services Agreement",
  "risk_score": 20,
  "overall_verdict": "LOW_RISK (Generally Acceptable to Proceed)",
  "high_risk_count": 0,
  "medium_risk_count": 1,
  "acceptable_count": 14,
  "missing_clauses": ["Limitation of Liability", "Indemnification", "Force Majeure", "Severability"],
  "clause_evaluations": [...]
}
```

---

### `GET /api/compare`
Compares Baseline Client Draft vs. Counterparty Redline and returns token diffs with legal impacts.

---

### `GET /api/draft/{doc_type}`
Generates autonomous legal drafts stamped with mandatory watermarks.
- Supported `doc_type` parameters: `case_brief`, `legal_notice`, `clauses`.

---

### `POST /api/upload`
Uploads document content for security inspection, PII redaction, and matter ingestion.

