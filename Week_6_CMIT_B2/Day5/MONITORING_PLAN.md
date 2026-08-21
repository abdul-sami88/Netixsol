# AFL Assistant: Monitoring & Maintenance Plan

**Version:** 1.0  
**Last Updated:** 2024-08-21

---

## Executive Summary

This document outlines the production monitoring strategy for the AFL Assistant (Week 6 Day 5 capstone), including:

- What metrics to track
- Alert thresholds
- Weekly retraining & refresh loop
- Escalation procedures

---

## 1. Core Metrics to Track

### 1.1 System Health

| Metric | Target | Alert Threshold | Cadence | Owner |
|--------|--------|------------------|---------|-------|
| **API Response Latency (p95)** | < 2s | > 5s | Real-time | Platform |
| **API Error Rate** | < 1% | > 5% | Hourly | Platform |
| **Tool Timeout Rate** | < 0.1% | > 1% | Hourly | Platform |
| **Graph Node Failures** | < 0.5% | > 2% | Hourly | Platform |

**Logging Location:** `logs/afl_api.jsonl` (structured JSON logs from FastAPI wrapper)

---

### 1.2 Prediction Model Performance

| Metric | Baseline | Target | Check Cadence | Action |
|--------|----------|--------|----------------|--------|
| **Match Winner Accuracy** | 63.4% | ≥ 61% | Weekly | Retrain if < 61% |
| **Top Player Top-5 Hit Rate** | 63.0% | ≥ 60% | Weekly | Retrain if < 60% |
| **Prediction Calibration (Brier Score)** | 0.223 | < 0.25 | Weekly | Review if drifts |

**Data Source:**  

- Weekly match results are added to `afl_match_features_v2.csv` by external data pipeline
- Player stats auto-update via `afl_player_features_v2.csv`

---

### 1.3 Scope & Safety

| Metric | Target | Alert if | Cadence |
|--------|--------|----------|---------|
| **Off-Topic Leak Rate** | < 2% | > 5% | Daily |
| **Prompt Injection Block Rate** | > 98% | < 95% | Daily |
| **Clarification Loop Rate** | < 10% | > 20% | Daily |
| **Tool Resolution Failure** | < 5% | > 10% | Daily |

**Detection Method:**  

- Sample 50 logs/day; manually review any marked as "error" or "fallback"
- Run guardrail test suite (3+ prompt injection attempts) **weekly**

---

## 2. Alert Thresholds & Escalation

### 2.1 Red Alerts (Immediate Action)

**Trigger:** API error rate > 10% for 15 min  
**Action:** Page on-call engineer; roll back last deployment if applicable

**Trigger:** Match prediction accuracy drops below 50% (vs. baseline 63%)  
**Action:** Flag data quality issue; check if new round results are malformed; hold retraining

**Trigger:** Off-topic leak rate > 10% for 1 hour  
**Action:** Review router logs; check if guardrails have regressed

---

### 2.2 Yellow Alerts (Review Within 1 Hour)

**Trigger:** API latency p95 > 5s for 30 min  
**Action:** Check graph node timing; profile slow path

**Trigger:** Tool resolution failure > 15%  
**Action:** Review entity extraction; check if team/player names have changed

**Trigger:** Prompt injection blocks < 90%  
**Action:** Review guardrail rules; add new patterns

---

### 2.3 Monitoring Checklist (Weekly)

Every Friday EOD, run:

```bash
# 1. Gather logs
python monitoring/analyze_logs.py --week-of-2024-08-21

# 2. Compute performance metrics
python monitoring/compute_metrics.py

# 3. Run guardrail tests
python afl_capstone_hardened.py --guardrails-only

# 4. Check prediction accuracy against new match results
python monitoring/validate_predictions.py

# 5. Generate report
python monitoring/generate_report.py > reports/week_of_2024-08-21.md
```

---

## 3. Weekly Retraining & Model Refresh

### 3.1 Data Refresh Cycle

**When:** Every Friday, 20:00 UTC (post-round weekend matches)

**What updates:**

1. New match results → `afl_match_features_v2.csv`
2. Player stats updated → `afl_player_features_v2.csv`
3. New team rolling states → `artifacts/latest_team_state.parquet`
4. New player rolling states → `artifacts/latest_player_state.parquet`

**Process:**

```
1. Data Validation (10 min)
   ├─ Check for duplicate rows
   ├─ Verify column types & ranges
   └─ Confirm all expected teams present

2. Feature Engineering (15 min)
   ├─ Recompute rolling averages (form_last5, season totals)
   ├─ Update team ladder positions
   └─ Regenerate feature tables

3. Model Retraining (20 min)
   ├─ Retrain match_winner_pipeline.joblib on updated data
   ├─ Retrain top_player_pipeline.joblib on updated data
   ├─ Compute new performance metrics
   └─ Save as artifacts/*.joblib_backup (for rollback)

4. Validation (10 min)
   ├─ Compute accuracy on held-out test set
   ├─ Compare Brier score vs. baseline
   ├─ Check calibration
   └─ HOLD if accuracy drops > 5%; notify data team

5. Deployment (5 min)
   ├─ Swap old artifacts/ → artifacts/_old_YYYY-MM-DD/
   ├─ Deploy new models to prediction service
   └─ Run smoke tests
```

**Responsible:** Data Science team  
**Rollback Plan:** If accuracy drops below 61%, revert to previous week's models from `artifacts/_old_*/`

---

### 3.2 Monthly Model Review (1st Friday of month)

- Full retraining from scratch (not incremental updates)
- Hyperparameter tuning (grid search over key params)
- Class balance review (SMOTE / sampling strategy)
- Feature importance analysis (SHAP, permutation)
- Guardrail effectiveness review (sample 100 logs for scope leaks)

**Output:** `reports/monthly_review_YYYY-MM.md`

---

## 4. Key Metrics Dashboard

Create a simple dashboard (or script output) that shows:

```
┌─ AFL ASSISTANT METRICS DASHBOARD ─────────────────────────┐
│                                                              │
│  System Health                                              │
│  ├─ API Latency (p95)      : 1.23s    ✓                   │
│  ├─ Error Rate             : 0.3%     ✓                   │
│  ├─ Tool Timeout Rate      : 0.05%    ✓                   │
│  └─ Uptime (7d)            : 99.8%    ✓                   │
│                                                              │
│  Prediction Models                                          │
│  ├─ Match Winner Accuracy  : 62.1%    ✓ (target: ≥61%)   │
│  ├─ Top Player Hit Rate    : 61.8%    ✓ (target: ≥60%)   │
│  ├─ Brier Score (calib)    : 0.224    ✓ (target: <0.25)  │
│  └─ Last Retrain           : 2024-08-18                   │
│                                                              │
│  Safety & Scope                                             │
│  ├─ Off-Topic Leak Rate    : 1.2%     ✓ (target: <2%)    │
│  ├─ Prompt Inj Block Rate  : 99.2%    ✓ (target: >98%)   │
│  ├─ Clarification Rate     : 8.1%     ✓ (target: <10%)   │
│  └─ Guardrail Tests Passed : 7/7      ✓                   │
│                                                              │
│  Volume & Engagement                                        │
│  ├─ Queries / Hour         : 87                            │
│  ├─ Avg Conversation Length: 2.3 turns                    │
│  ├─ Intent Distribution                                    │
│  │  ├─ Prediction (match)  : 34%                          │
│  │  ├─ Factual            : 28%                           │
│  │  ├─ Retrieval          : 22%                           │
│  │  └─ Other              : 16%                           │
│  └─ Top Query Categories  : Match prediction, Team stats │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 5. Known Limitations & Future Improvements

### 5.1 Current Limitations

1. **Data Recency**
   - Models retrain only weekly (1-2 day lag on latest results)
   - Fixture calendar not integrated (can't predict "next round")

2. **Model Accuracy**
   - Match winner: 63.4% (vs. 56.3% baseline); still ~1/3 wrong
   - Top player: 63% top-5 hit rate (vs. 71.9% "last week repeats" baseline)
   - Single-feature models (rolling form, ladder position) only

3. **Scope Limitations**
   - Exact score/margin predictions not supported
   - Multi-team comparisons not implemented
   - Historical counterfactuals ("What if X played Y in 2020?") not supported

### 5.2 Recommended Improvements (Roadmap)

| Priority | Improvement | Effort | Impact |
|----------|-------------|--------|--------|
| **High** | Integrate fixture calendar for "next round" prediction | 2 days | +10% query coverage |
| **High** | Add ensemble models (blend LR + GBM + random forest) | 3 days | +3-5% accuracy |
| **High** | Implement SHAP explanations for predictions | 2 days | Better user trust |
| **Medium** | Add injury/suspension data to features | 1 week | +2% accuracy |
| **Medium** | Support multi-match scenario ("if X beats Y and A beats B...") | 3 days | +5% engagement |
| **Medium** | Player-level prediction (not just team) | 1 week | New capability |
| **Low** | Add historical comparison tool ("X's form in 2020 vs. now") | 2 days | Engagement |

---

## 6. Runbooks & Escalation

### 6.1 Model Accuracy Drops Unexpectedly

**Symptom:** Match winner accuracy drops from 62% to 55% overnight  
**Root Cause Check:**

1. Did data schema change? (new/removed columns, renamed teams?)
2. Is new match data malformed? (wrong types, out-of-range values?)
3. Have team rules changed? (e.g., Melbourne moved to a new home ground?)
4. Feature drift? (e.g., form_last5 distribution shifted)

**Action:**

1. Compare feature distributions: `monitoring/compare_distributions.py`
2. Review last week's new matches for quality issues
3. If data is bad, hold retraining and notify data team
4. If feature shift, consider re-fitting with recent data only (sliding window)

---

### 6.2 High Rate of Guardrail Failures (Off-Topic Leaking)

**Symptom:** Guardrail tests show <90% block rate  
**Check:**

1. Are new variants of prompt injection appearing? (run full test suite)
2. Did router rules change? (check git history)
3. Is LLM-based router (if enabled) drifting? (check model version)

**Action:**

1. Add new patterns to `router.py` rule-based classifier
2. If using LLM router, retune system prompt
3. Run guardrail tests again after fix
4. Document new attack vector for future reference

---

### 6.3 Tool Failures: Entity Resolution Not Finding Teams

**Symptom:** "couldn't identify both teams" errors on valid AFL team names  
**Check:**

1. Did team names change in `afl_match_features_v2.csv`? (e.g., "GWS" → "Greater Western Sydney"?)
2. Are users entering non-canonical nicknames? (e.g., "Hawthorn Hawks" vs. just "Hawks"?)
3. Did `ai_chat_afl._canonical_teams()` fail to load the CSV?

**Action:**

1. Verify team list: `python entity_resolution.py --check-teams`
2. Add new nicknames to resolver
3. Log unresolved queries for manual review
4. Update MONITORING_PLAN if new convention discovered

---

## 7. Stakeholder Reporting

### 7.1 Weekly Report Template (Friday EOD)

**To:** Stakeholders  
**Subject:** AFL Assistant Weekly Status (Week of YYYY-MM-DD)

```
## Summary
- Uptime: 99.8%
- Queries: 612 (avg 87/hour)
- Avg Response Time: 1.2s
- Error Rate: 0.3%

## Model Performance
- Match Winner Accuracy: 62.1% (target: ≥61%) ✓
- Top Player Hit Rate: 61.8% (target: ≥60%) ✓

## Safety & Scope
- Off-Topic Leak: 1.2% ✓
- Prompt Injection Block: 99.2% ✓

## Issues & Actions
- None critical
- [Any yellow alerts, resolutions]

## Next Week
- Scheduled data refresh: 2024-08-25 20:00 UTC
- No breaking changes planned
```

---

## 8. Contact & Escalation

| Role | Contact | On-Call |
|------|---------|---------|
| **Platform Engineer** | platform-team@company.com | Yes (M-F 9-5) |
| **Data Scientist** | ds-team@company.com | Yes (on rotation) |
| **Product Manager** | pm@company.com | No |

**Escalation Path:**

1. First alert → Platform Engineer (30 min response)
2. No fix in 1 hour → Page Data Scientist
3. No fix in 2 hours → Escalate to PM (possible feature rollback)

---

## Appendix A: Monitoring Scripts

### A.1 `monitoring/analyze_logs.py`

```python
# Pseudo-code
import json
from pathlib import Path
from collections import defaultdict

def analyze_logs(week_start_date: str):
    log_file = Path("logs/afl_api.jsonl")
    
    stats = {
        "total_queries": 0,
        "intent_dist": defaultdict(int),
        "error_count": 0,
        "avg_latency": 0.0,
    }
    
    latencies = []
    with open(log_file) as f:
        for line in f:
            record = json.loads(line)
            if is_in_week(record["timestamp"], week_start_date):
                stats["total_queries"] += 1
                if "intent" in record:
                    stats["intent_dist"][record["intent"]] += 1
                if record["level"] == "ERROR":
                    stats["error_count"] += 1
                if "latency_sec" in record:
                    latencies.append(record["latency_sec"])
    
    stats["avg_latency"] = sum(latencies) / len(latencies) if latencies else 0
    return stats
```

---

**End of Document**
