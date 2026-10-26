# Task 2: Monitoring, Telemetry & Continuous Improvement Flywheel

**Client:** Zarya Digital Bank  
**Document:** Week 10 — Day 5: Task 2 Operations & Continuous Improvement  
**Author:** Antigravity Senior AI/ML Engineering Lead  
**Module:** [`src/feedback_pipeline.py`](file:///c:/Users/MEE/Anti-Gravity_projects/Fine-tuning-llm/src/feedback_pipeline.py)  

---

## 1. Real-Time Telemetry & PII-Masked Logging

Every conversation flowing through Zarya AI Core records a structured audit event into `data/zarya_banking.db`.

```
[Customer Interaction] ──> [PII Scrubber] ──> [Audit Telemetry DB] ──> [Grafana / Kibana Dashboard]
```

### Log Schema & Sanitization
* **Inbound Prompt:** Scrubbed of CNICs (`42101-*******-1`), Pakistani mobile numbers (`0300*****67`), and emails.
* **Latency (ms):** End-to-end processing time (guardrail check + RAG search + generation).
* **Guardrail Status:** Flagged as `PASSED`, `PROMPT_INJECTION`, `CREDENTIAL_HARVESTING`, or `SCAM_DETECTION`.
* **RAG Retained Docs:** IDs of banking policies cited in the generation.

---

## 2. Customer Feedback & Flywheel Architecture

In the customer chat UI, every assistant response includes an interactive **👍 Useful** and **👎 Poor** action.

```
       [Customer Feedback: 👎 Poor]
                     │
                     ▼
       ┌───────────────────────────┐
       │ 1. Feedback Queue Store   │
       │    (data/feedback_queue)  │
       └─────────────┬─────────────┘
                     │ (Filter Negative + Agent Review)
                     ▼
       ┌───────────────────────────┐
       │ 2. DPO Triplet Generator  │
       │    - Prompt = User input  │
       │    - Chosen = Approved    │
       │    - Rejected = Bad reply │
       └─────────────┬─────────────┘
                     │
                     ▼
       ┌───────────────────────────┐
       │ 3. Next-Cycle DPO Dataset │
       │    (dpo_flywheel_candidates)
       └───────────────────────────┘
```

1. When an agent or customer flags a response as poor, the conversation is routed to the **Feedback Queue**.
2. Support team members or senior prompt reviewers supply the corrected banking response.
3. The pipeline automatically pairs the user prompt with the corrected answer (`chosen`) and the rejected model answer (`rejected`), appending it directly to `dpo_flywheel_candidates.jsonl`.

---

## 3. Retraining Schedule & Cadence

| Cadence | Activity | Trigger Threshold | Compute Resource |
| :--- | :--- | :--- | :--- |
| **Daily (Automated)** | Feedback Ingestion & PII Audit | Automatic via `/api/feedback` | Background cron |
| **Bi-Weekly (Sprint)** | DPO Alignment Run | Accumulated $\ge 200$ verified preference pairs | Single Tesla T4 GPU (Colab / AWS) |
| **Monthly (Major)** | Full Evaluation Harness & SBP SOC Refresh | SBP Regulatory Circulars or major policy shifts | Dual GPU evaluation suite |

---

## 4. Model Versioning & Rollback Strategy

Zarya AI Core enforces a **Blue-Green Deployment** policy using semantic versioning (`v1.0.0`, `v1.1.0`):

```
                       [Incoming Customer Traffic]
                                    │
                                    ▼
                 ┌──────────────────────────────────────┐
                 │ NGINX / Reverse Proxy Active Pointer │
                 └──────────────────┬───────────────────┘
                                    │
                  ┌─────────────────┴─────────────────┐
                  ▼                                   ▼
          ┌───────────────┐                   ┌───────────────┐
          │ Active (Blue) │                   │ Staged (Green)│
          │ Model v1.0.0  │                   │ Model v1.1.0  │
          └───────────────┘                   └───────────────┘
```

### Rollback Procedure:
1. **Automated Smoke Test:** Prior to switching traffic to `v1.1.0`, the system automatically executes [`src/run_day4_local_demo.py`](file:///c:/Users/MEE/Anti-Gravity_projects/Fine-tuning-llm/src/run_day4_local_demo.py) (30 catastrophic forgetting probes + 4 security tests).
2. **Instant Rollback Trigger:** If the Pearson correlation on the golden test drops below $r < 0.80$ or if safety refusal drops below $100\%$, traffic remains locked to `v1.0.0`.
3. **Rollback CLI Command:**
   ```bash
   python scripts/rollback_model.py --target v1.0.0
   ```
   Re-links the active Docker container to the `v1.0.0` weights within **5 seconds** without server downtime.
