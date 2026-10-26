# Operations Guide & IT Runbook

**Client:** Zarya Digital Bank  
**Document:** Week 10 — Day 5: Enterprise IT Operations & Disaster Recovery  
**Target Audience:** Bank DevOps, SRE, and Core Infrastructure Teams  

---

## 1. System Architecture & Topology

Zarya AI Core runs in a isolated VPC inside the bank's sovereign private cloud or on-premise data center in Karachi/Islamabad:

```
[Mobile App / Internet Banking] ──> [F5 BIG-IP / NGINX Load Balancer]
                                                 │ (TLS 1.3)
                                                 ▼
                               ┌───────────────────────────────────┐
                               │ Docker Cluster (FastAPI AI Core)  │
                               │ - Port: 8000                      │
                               │ - Workers: 2-4                    │
                               │ - Model: Qwen 2.5 3B Q4_K_M GGUF │
                               └─────────────────┬─────────────────┘
                                                 │
                               ┌─────────────────┴─────────────────┐
                               ▼                                   ▼
                   [SQLite / Postgres DB]                 [Policy Docs Storage]
                   (data/zarya_banking.db)                (data/rag/policies)
```

---

## 2. Service Management & Health Monitoring

### Starting the Service via Docker Compose:
```bash
# Build and start container in detached daemon mode
docker-compose up -d --build

# View real-time logs
docker-compose logs -f zarya-ai-core
```

### Health Check Endpoint:
* Automated polling endpoint: `http://localhost:8000/api/health`
* Expected response: HTTP 200 with `"status": "healthy"`.

### Key Metrics to Monitor in Prometheus / Grafana:
* **p95 Latency:** Threshold $< 300\text{ ms}$. If $> 500\text{ ms}$, scale up container replicas.
* **Error Rate:** Threshold $< 0.1\%$.
* **Guardrail Trigger Frequency:** Spike in `SCAM_DETECTION` indicates an active phishing campaign targeting bank customers.

---

## 3. Database Backup & Disaster Recovery

The complaint tickets, feedback events, and masked audit logs are stored in `data/zarya_banking.db`.

### Daily Automated Backup (Cron):
```bash
#!/bin/bash
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
sqlite3 /app/data/zarya_banking.db ".backup '/app/backups/zarya_backup_${TIMESTAMP}.db'"
# Retain backups for 90 days as per SBP Record Retention regulations
find /app/backups/ -type f -name "*.db" -mtime +90 -delete
```

### Restoration Runbook:
```bash
# Stop application container
docker-compose stop zarya-ai-core

# Restore from latest verified backup
cp /app/backups/zarya_backup_TARGET.db /app/data/zarya_banking.db

# Restart container
docker-compose up -d
```

---

## 4. Emergency Incident Response (Kill Switch)

If unexpected model behavior or catastrophic hallucination occurs:

1. **Activate Strict RAG Fallback Mode:**
   Set `FALLBACK_RAG_STRICT=true` in `.env` and restart container. The system bypasses generative creativity and recites policy snippets verbatim.
2. **Immediate Model Rollback:**
   Re-point `MODEL_PATH` in `.env` to the previous stable checkpoint (`zarya_lora_adapter`) and reload.
