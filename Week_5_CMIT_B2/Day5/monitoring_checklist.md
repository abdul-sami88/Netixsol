# Production Monitoring Checklist — Client Intake & Proposal Agent

## What to Track

| Metric | How | Why |
|---|---|---|
| **Error rate** | % of `/inquiry` and `/approve` calls returning 5xx, from `agent_api.log` | Signals LLM API outages, tool failures, or code regressions |
| **Latency (p50/p95/p99)** | `latency_ms` field logged per request | Catches slow LLM calls, currency API slowness, or graph loops |
| **Category distribution drift** | Rolling daily count of category outcomes | A sudden jump in "Spam" or "Invalid" often means the fallback classifier is misfiring (see eval failure pattern) |
| **Fallback trigger rate** | Count of `conversion_note` containing "unavailable"/"Estimated" | Tracks how often the currency API tool degrades — sustained high rate = investigate the external dependency |
| **Human-approval queue depth & turnaround** | Count of `Pending_Human_Approval` state + time to `/approve` call | A backlog here delays real client proposals — direct business impact |
| **Cost drift** | Estimated token cost per run, aggregated daily/weekly | Detects prompt bloat, retries, or usage spikes |
| **Output quality drift** | Periodic manual/LLM-graded sample of drafted proposals (tone, accuracy) | LLM or prompt changes can silently degrade tone over time |
| **Safety incidents** | Count of `Malicious` classifications + spot-check for injection attempts that slipped through | Security signal — should always be near-zero false negatives |

## Alert Thresholds (starting points — tune with real traffic)

- Error rate > 2% over a rolling 15-minute window → page on-call
- p95 latency > 5s (LLM path) → warn; > 15s → page
- Fallback trigger rate > 20% of New Project inquiries in a day → investigate currency API health
- Human-approval queue > 25 pending or > 4 hours average turnaround → notify sales ops
- Any `Malicious` category with `safety_pass == False` in eval replay → immediate review (should never happen)
- Daily cost > 3x trailing 7-day average → investigate for prompt/loop regression

## Re-evaluation Cadence

- **Weekly:** re-run the 10-case regression suite (`run_evaluation.py`) against the current deployed prompt/model — catches silent drift from model version upgrades.
- **On every prompt or model change:** full evaluation suite + manual review of 20 recent production transcripts before rollout.
- **Monthly:** expand the test set with real (anonymized) production edge cases that caused confusion, so the suite grows with actual usage.
- **Quarterly:** review the rate card, currency fallback rates, and injection-pattern list for staleness.
