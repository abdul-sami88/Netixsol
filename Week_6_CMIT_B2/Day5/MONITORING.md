# AFL Assistant — Monitoring & Maintenance Plan

## What to track

| Metric | How | Alert threshold | Cadence |
|---|---|---|---|
| **Response latency (p50/p95)** | `latency_sec` in every `/chat` log line (`logs/afl_api.jsonl`); `GET /logs/summary` for a quick rollup | p95 > 5s sustained for 15 min | Real-time / reviewed daily |
| **Tool error rate** | Trace lines containing `EXCEPTION`/`ERROR`, surfaced as `tools_called[].success=false` in the API response and logs | > 2% of requests in a rolling 1-hour window | Real-time / reviewed daily |
| **Predictor availability** | `GET /health` → `components.predict` (`available`/`unavailable`); `day2_interface.is_available()` under the hood | Any transition to `unavailable` | Real-time alert (this should never silently persist -- it means the model artifacts or feature CSVs became unreachable) |
| **Off-topic leak rate** | Category C-style checks (does a response to a known off-topic/injection probe actually answer it?) run as a scheduled synthetic-probe job against the live agent | Any leak at all -- this is a hard gate, not a threshold | Automated synthetic probes daily; manual spot-check weekly |
| **Scope-probing / abuse signal** | `_track_abuse_signal()` in `api.py` — logs a warning when a single `conversation_id` sends 5+ off-topic queries within 5 minutes | Any warning fired | Reviewed daily; escalate if the same signal repeats across many distinct conversation_ids (suggests automated probing, not one confused user) |
| **Disclaimer consistency** | `_check_disclaimer_consistency()` in `api.py` — every prediction response is checked for disclaimer language before being returned | Any `ERROR`-level "DISCLAIMER MISSING" log line | Real-time alert (should be structurally impossible; a hit means a real regression in `nodes.py`) |
| **Prediction accuracy drift** | Compare `predict_match_winner`'s pre-match call (logged) against the real final result once it's known | Rolling 4-week accuracy drops more than 5 points below the 63.4% baseline | Weekly, after each round's results are in |
| **Router intent-classification drift** | Re-run `tests/test_router_accuracy.py` and `tests/test_comprehensive_eval.py` against any router.py change, and spot-check a sample of real production queries' logged `intent` against manual labels | Accuracy < 90% on the fixed regression set | On every router.py change; spot-check sample reviewed weekly |
| **Conversation length / clarification-loop rate** | % of turns with `validation_status=needs_clarification` | > 15% of prediction-intent turns needing clarification (suggests team-name resolution is degrading, e.g. new team names/aliases not covered) | Weekly |

## Alert routing (suggested, adjust to your team's tooling)
- **Page immediately:** predictor availability flips to `unavailable`; a disclaimer-missing error fires; an off-topic leak is confirmed by the synthetic probe job.
- **Notify next business day:** p95 latency or tool error rate breaches threshold; accuracy drift exceeds threshold; router accuracy regression.
- **Weekly digest:** clarification-loop rate, intent distribution shift, abuse-signal summary.

## Weekly retraining / data-refresh loop

1. **After each round's real results are final** (typically Monday, once all weekend matches are confirmed):
   a. Append the new round's rows to the raw match/player source data (the inputs to `AFL_Data_Foundations_Complete.ipynb`'s Task 4 feature engineering).
   b. Re-run the notebook's feature-engineering cells to regenerate `afl_match_features_v2.csv` / `afl_player_features_v2.csv` with the new round included (the `shift(1)` rolling-window logic means the new round's rows now correctly reflect every team's/player's *updated* rolling form for the following round).
   c. Deploy the refreshed CSVs -- `predict.py` reads them directly (see the "root cause" writeup in `README.md`), so no separate snapshot-export step is needed; a new round's data is live for predictions as soon as the CSVs are updated.
2. **Retrain the two models on a fixed cadence, not every week:**
   - **Monthly**, or after every ~4 rounds -- refit `match_winner_pipeline` and `top_player_pipeline` on the accumulated data through the most recent completed round, and re-run the held-out test-set evaluation to confirm accuracy hasn't regressed before promoting the new model.
   - **Immediately, out of cycle**, if the weekly accuracy-drift check (above) shows a >5-point drop -- don't wait for the monthly cycle if something looks broken.
3. **Before promoting any new model or CSV refresh to production:**
   - Re-run `tests/test_comprehensive_eval.py` (Category B in particular) against the new data.
   - Compare new-model accuracy against both the previous model and the naive baselines (56.3% "always home wins" for match winner, 71.9% "last week's leader repeats" for top player) -- a new model should not be promoted if it's worse than the baseline it's meant to beat.
   - Keep the previous model artifacts on hand for one cycle so a regression can be rolled back quickly.

## Known gaps this plan doesn't yet cover (flag for follow-up)
- No real fixture calendar exists in the current data, so "this week" is always resolved to "using each team's latest known state," not tied to an actual upcoming date -- monitoring can't yet distinguish "stale data" from "correctly using last week's numbers because there's no real fixture source." Fixing this requires a real fixture-calendar artifact (see `README.md`'s Task 3 notes).
- The abuse tracker in `api.py` is in-memory and per-process -- it resets on restart and doesn't share state across multiple API instances. Fine for a single-instance demo; needs a shared store (Redis) before any multi-instance production deployment.
