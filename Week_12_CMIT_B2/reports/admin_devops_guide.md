# Khan & Associates — Admin & DevOps Deployment Guide

**Target Audience:** Law Firm IT Administrators & DevOps Engineers  
**System:** Khan & Associates AI Legal Assistant Platform  
**Environment Requirements:** Python 3.12+, Docker & Docker Compose (optional), 8 GB RAM minimum.

---

## 1. Local Python Deployment

### 1.1 Environment Setup
```powershell
# 1. Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure secrets in .env
# Set GROQ_API_KEY, GEMINI_API_KEY, and optional NEO4J_URI
```

### 1.2 Running Core Services
```powershell
# Start FastAPI application & Web Server on port 8000
python src/app.py

# Run Live 10-Minute Demo Runner
python src/live_demo.py

# Rebuild Knowledge Graph & PageRank
python src/build_knowledge_graph.py
```

---

## 2. Production Docker Deployment

### 2.1 Multi-Container Stack (`docker-compose.yml`)
The platform is packaged into 4 isolated containers:
1. `legal-api`: FastAPI backend container (Port 8000).
2. `neo4j`: Neo4j 5.18 Community Graph Database (Ports 7474 & 7687).
3. `vector-db`: ChromaDB Vector Database (Port 8001).
4. `worker`: Asynchronous background task worker.

### 2.2 Docker Launch Commands
```bash
# Build and launch all services in detached mode
docker-compose up -d --build

# Verify container health status
docker-compose ps

# Stream logs from the API container
docker-compose logs -f legal-api
```

---

## 3. Security & Ethical Wall Administration

### 3.1 User Matter Authorization Matrix
Located in `src/security_firewall.py`:
```python
self.user_matter_authorizations = {
    "attorney_ahmed": ["KA-MATTER-101", "KA-MATTER-102"],  # Corporate M&A Team
    "attorney_fatima": [
        "KA-MATTER-201",
        "KA-MATTER-202",
    ],  # Banking Litigation
    "partner_khan": ["KA-MATTER-101", "KA-MATTER-201", "ALL"],  # Managing Partner
}
```
To add a new attorney or grant access to a matter docket, update the authorization dictionary or connect to firm LDAP/Active Directory.

### 3.2 Reviewing the Tamper-Evident Security Audit Log
All access events, PII redactions, and blocked injection attempts are recorded in:
`outputs/security_audit_log.jsonl`

**Monitoring Command:**
```powershell
Get-Content outputs/security_audit_log.jsonl -Tail 15
```

---

## 4. Maintenance & Backups

1. **Knowledge Graph Backup:** Back up `outputs/graph/legal_kg.json` and `outputs/graph/neo4j_import.cypher`.
2. **Vector Index Backup:** Back up `indexes/chroma_db` and `indexes/bm25_index.pkl`.
3. **Firm Playbook Customization:** Update negotiation guidelines and fallback wording in `data/firm_playbook.json`.

