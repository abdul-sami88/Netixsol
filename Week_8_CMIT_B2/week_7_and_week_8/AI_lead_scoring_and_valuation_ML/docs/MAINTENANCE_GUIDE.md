# System Maintenance & Operations Manual
## Estate AI Pakistan — Production MLOps Runbook

---

## 1. System Architecture Overview

The system consists of:
1. **Model Serving API (`serving_api.py`)**: FastAPI service running on port `8000`.
2. **Interactive Dashboard (`dashboard.py`)**: Streamlit web application running on port `8501`.
3. **MLOps Drift Engine (`drift_monitoring.py`)**: Automated statistical monitoring (KS test, PSI, MAPE).
4. **Retraining Pipeline (`retraining_pipeline.py`)**: Gated Challenger vs Champion evaluation and rollback.
5. **Database Layer (`database.py`)**: SQLite (`production_audit.db`) or PostgreSQL instance for audit trails.

---

## 2. Health Monitoring & Routine Checks

### Quick Health Verification
```bash
curl -s http://localhost:8000/health | jq
```
Expected output: `"status": "healthy"`, `"database_connected": true`, `"latest_drift_status": "STABLE"`.

### Inspecting Inference Logs
```bash
curl -s "http://localhost:8000/audit/inferences?limit=10" | jq
```

---

## 3. Drift Alert Response Runbook

When `GET /monitoring/drift` or the Streamlit Dashboard displays:
`🔴 RETRAIN_TRIGGERED (MAPE > 15.0% or PSI >= 0.25)`

Follow this 3-step remediation procedure:

### Step 1: Inspect Drift Report
Open `reports/drift_report.html` in a web browser or read `reports/drift_report.json`:
- Check which features have drifted (e.g., `price_pkr` mean shift, `plot_size_marla` demand shift).
- Note current production MAPE vs 15.0% SLA threshold.

### Step 2: Trigger Retraining Pipeline
Run the retraining pipeline from terminal:
```bash
python retraining_pipeline.py --new-data data_cleaned/property_listings_drifted_simulated.csv
```
Or trigger via REST API:
```bash
curl -X POST "http://localhost:8000/retrain/trigger"
```

The pipeline will:
1. Fit a Challenger LightGBM model on latest data.
2. Evaluate Challenger vs Champion on the holdout test set.
3. Automatically archive a pre-retrain snapshot to `saved_models/archive/snapshot_<timestamp>/`.
4. If Challenger MAPE < Champion MAPE, promote to Champion and reload memory.

### Step 3: Verify Post-Deployment Health
```bash
curl -s http://localhost:8000/health | jq
```
Verify `"active_model_version"` has incremented and `"latest_drift_status"` has normalized.

---

## 4. Emergency Rollback Protocol

If a newly deployed model exhibits erratic predictions or unexpected behavior, execute an immediate rollback:

### Method A: Via CLI (Fastest)
```bash
python retraining_pipeline.py --rollback
```

### Method B: Via API Endpoint
```bash
curl -X POST "http://localhost:8000/model/rollback"
```

This immediately restores the exact `.joblib` model binaries and metadata from `saved_models/rollback/` and hot-reloads memory in under 15 seconds.

---

## 5. Scheduled Maintenance & Cron Configuration

### Monthly Retraining Cadence
Real estate price movements in Pakistan align with monthly cycles. Retraining is scheduled on the 1st of every month at 02:00 AM UTC:
```cron
0 2 1 * * cd /app && python retraining_pipeline.py >> /var/log/estate_retrain.log 2>&1
```

### Database Backup
Back up the SQLite audit database daily:
```bash
sqlite3 production_audit.db ".backup 'production_audit_backup_$(date +%F).db'"
```
