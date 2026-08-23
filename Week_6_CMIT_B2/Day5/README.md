# Week 6 Day 5 — Capstone: Full AFL Assistant, Evaluation, Deployment & Presentation

This project now includes the full capstone on top of the Day 4 LangGraph
app documented below: API + UI, a comprehensive evaluation suite, hardening
fixes, a monitoring plan, and stakeholder deliverables.

## Day 5 quick start

```bash
pip install -r requirements.txt   # or see "Install dependencies" below + fastapi uvicorn streamlit
python api.py                      # FastAPI backend on http://localhost:8000
streamlit run ui.py                # chat UI (in a second terminal)
python3 tests/test_comprehensive_eval.py   # Task 2: 34-case eval suite -> logs/eval_results.md
python3 build_executive_report.py          # Task 5: regenerates EXECUTIVE_REPORT.pdf
```

## Day 5 deliverables (this capstone's additions)

| Deliverable | File |
|---|---|
| Task 1: hardening (real async timeouts, disclaimer check, abuse tracking, router robustness) | `api.py`, `router.py` -- see "Bugs found & fixed" below |
| Task 2: 34-case evaluation suite + results table | `tests/test_comprehensive_eval.py` → `logs/eval_results.md` |
| Task 3: FastAPI wrapper + Streamlit UI | `api.py`, `ui.py` |
| Task 4: monitoring & maintenance plan | `MONITORING.md` |
| Task 5: executive report (2-page PDF) + demo script | `EXECUTIVE_REPORT.pdf` (via `build_executive_report.py`), `DEMO_SCRIPT.md` |

## Bugs found & fixed during Day 5 hardening

1. **API timeout mechanism was fundamentally broken.** The original
   `api.py` used `signal.alarm()` for request timeouts, which only works in
   the main thread of the main interpreter -- but FastAPI runs synchronous
   route handlers in a worker thread pool by default, so every single
   request raised `ValueError: signal only works in main thread of the
   main interpreter` before the query ever reached the graph. **This is
   very likely the actual cause of "prediction fails / doesn't understand
   the query"** reports -- confirmed by reproducing the crash with
   `TestClient`. Fixed with `asyncio.wait_for` + `asyncio.to_thread`
   (thread-safe, works identically on Windows and Unix, no signal
   dependency at all).
2. **Router coverage gaps** found via a 13-phrasing stress test (things
   like "Is Melbourne going to beat Richmond?", "who's favoured in X vs
   Y", "who would win between X and Y", "who will kick the most goals for
   X", "I meant will X beat Y" after a clarification). All 13 originally
   failed to extract team names or misclassified intent; all now pass.
   See `router.py`'s expanded `_LEADING_PHRASES` / `_TRAILING_PHRASES` /
   extraction patterns and hint lists.
3. **Input validation returned 500 instead of 400** for empty/oversized
   messages -- client errors should never be reported as server errors.
   Fixed in `api.py`.
4. **UI: Enter didn't send, and the input box didn't clear after
   sending.** `st.text_area` never submits on Enter (Enter just inserts a
   newline), and the old clearing logic set a session-state variable that
   wasn't actually bound to the widget's displayed value -- a classic
   Streamlit gotcha. Rewrote `ui.py` around `st.chat_input` /
   `st.chat_message`, which submit on Enter and clear themselves
   automatically, eliminating the bug class entirely rather than patching
   around it.

## Honest caveats on the Day 5 evaluation

The 34-case suite (`tests/test_comprehensive_eval.py`) runs offline against
the real prediction models but a **scripted stand-in** for the live
Gemini-backed chat agent (no `GEMINI_API_KEY` in this environment). It
validates routing, fail-closed behavior, and multi-turn state handling
correctly and rigorously -- but **not** live answer quality or live
prompt-injection resistance, which are properties of the real model, not a
stub that approximates its wording. The report and `MONITORING.md` both
flag this explicitly: re-running the suite against the real agent is a
required step before treating any of this as launch-ready, not just a
nice-to-have.

---

# Week 6 Day 4 — LangGraph Integration: Routing Between Chat, Retrieval & Prediction

A LangGraph application that routes an AFL user query to either the Day 2
prediction models (`predict.py`) or the Day 3 chat/retrieval agent
(`ai_chat_afl.py`), with validation and a clarification loop guarding the
prediction path so predictions are always framed probabilistically.

## Setup & Run

### 1. Install dependencies
```bash
pip install langgraph langchain-core langchain langchain-google-genai pydantic pandas scikit-learn joblib pyarrow python-dotenv
```

### 2. Add your real data (replaces the placeholder files shipped here)
| Replace this in the project | With |
|---|---|
| `artifacts/` (keep the two `.joblib` pipelines, replace the rest) | Your `Day2/artifacts/` folder contents |
| `afl_match_features_v2.csv`, `afl_player_features_v2.csv`, `merged_players.csv` | Your real Day 3 CSVs |

See `artifacts/READ_ME_FIRST.txt` and `CSV_DATA_READ_ME_FIRST.txt` for exactly which files are placeholders.

### 3. Set your API key
```bash
export GEMINI_API_KEY=your_key_here
# or put it in a .env file in the project root
```

### 4. Run
```bash
python3 graph.py                          # single demo query
python3 chat_cli.py                       # interactive CLI -- type your own queries
python3 chat_cli.py --stub                # same, but with the offline stub chat agent (no API key needed)
python3 tests/test_router_accuracy.py     # Task 2 deliverable — routing accuracy table
python3 tests/test_e2e.py                 # Task 5 deliverable — 12 full conversations, annotated traces
```

`chat_cli.py` keeps a running conversation (multi-turn follow-ups work),
prints which intent each query was routed to, and supports:
- `trace` — toggle full node-by-node trace printing
- `reset` — start a fresh conversation thread
- `exit` / `quit` / Ctrl-D — leave
- `--thread NAME` — pick a specific thread id up front

`tests/test_e2e.py` uses a stubbed chat agent by default so it runs without
a live API key. To test against the real Gemini-backed agent, delete the
`nodes.set_chat_agent_override(...)` line near the top of `main()`.

No code changes are needed anywhere else after step 2 — `router.py`,
`nodes.py`, `graph.py`, `state.py`, `entity_resolution.py`, and
`day2_interface.py` were built against the real function signatures and
data schemas from the start.

---

## Task 1 — Graph design

### State schema (`state.py`)
```
AFLState
├── messages: list[BaseMessage]        # full conversation history (LangGraph add_messages reducer)
├── user_query: str
├── intent: Intent | None              # factual | retrieval | prediction_match | prediction_player | off_topic | unsupported
├── router_confidence: float | None
├── entities: Entities                 # raw + resolved teams, + failure reason
├── tool_result: ToolResult | None      # {ok, kind, data, error, grounding}
├── validation_status: str | None       # ok | error | needs_clarification | unsupported
├── clarification_question: str | None
├── final_response: str | None
└── trace: list[str]                   # breadcrumb per node, for Task 5 logging
```

### Graph sketch (as actually wired in `graph.py`)
```
START
  |
  v
router
  |                 |                              |
  | prediction_*     | factual/retrieval/off_topic  | unsupported
  v                 v                              v
prediction_tool   chat_agent (real ai_chat_afl)   fallback
  |                 |                              |
  v                 |                              |
validation           |                              |
 |ok   (needs_clarification)-> clarification         |
 v                                                    |
response_formatter <----------------------------------'
  |
  v
 END
```

### Why factual/retrieval/off_topic all delegate to ONE `chat_agent` node

This is the one structural decision I made that goes beyond the original
sketch, once I saw what `ai_chat_afl.py` actually contains: a complete,
already-working Day 3 agent with five structured pandas tools
(`get_team_match_in_round`, `get_top_player_in_match`,
`get_player_match_stats`, `get_player_season_stats`,
`get_team_matches_record`), its own robust scope guardrail (`AGENT_PROMPT`
+ `GUARDRAIL_CASES`), and its own multi-turn memory (`InMemorySaver`).
Rebuilding separate `retrieval_tool` / `direct_answer` / `refusal` nodes in
this graph would just be a worse, duplicate copy of logic that already
exists and is already tested (`run_guardrail_evaluation`). So instead:
**the LangGraph router's only real job is to catch prediction-shaped
queries before they reach that agent**, and hand everything else to it
wholesale.

This is *also* the strongest version of the Task 1 justification for
explicit routing: `ai_chat_afl`'s agent has **no prediction tools at all**.
If a prediction-shaped query reached it directly, it would either refuse
(wrong — we do support predictions) or, worse, answer from "knowledge" and
hallucinate a winner — exactly the failure mode a stats-grounded assistant
can't afford. The router's conditional edge is a hard interception: no
prediction-shaped query can reach the general chat agent, and no
non-prediction query can reach `prediction_node`. That's a structural
guarantee a single free-form agent deciding tool-by-tool cannot give you.

### Why explicit routing (LangGraph) instead of one free-form agent, generally

1. **Structural guarantee on prediction disclaimers.** Every path that
   reaches `prediction_node` is funneled through the same
   `response_formatter_node` branch that hard-codes probability +
   disclaimer text. It's not something a model can forget mid-generation.
2. **Deterministic fail-closed behavior (Task 4).** `entity_resolution.py`
   either returns a canonical team name or `None` + a reason — never a
   guess. `validation_node` is a hard gate: `ok=False` can only reach
   `clarification` or `fallback`, never `response_formatter`.
3. **Debuggability.** `state.trace` gives an exact, reproducible
   node-by-node path per request (see the annotated traces below) — see the
   real bug this caught, in Task 5.
4. **Reuses what's already good.** Rather than a monolithic agent trying to
   own retrieval + prediction + refusal in one prompt, the graph explicitly
   delegates each concern to the component that's already built and tested
   for it.

The tradeoff: the rule-based router is worse at coreference across turns
than a strong general agent would be (see the honest limitation flagged in
Task 5, Run 11). That's why `classify_llm` (Gemini-backed, structured
output) exists as a swappable production path.

---

## Task 2 — Router node + accuracy

`router.py` implements `classify_rule_based` (default, offline,
deterministic — used for the accuracy table below) and `classify_llm`
(**Gemini 3.5 Flash Lite** via `langchain_google_genai`, structured output,
same `GEMINI_API_KEY` used by the Day 3 agent) behind a shared
`classify()` entrypoint gated by `USE_LLM_ROUTER=1`, so `router_node`
doesn't care which is active.

Team-name extraction for the rule-based router doesn't use a hardcoded
alias dict — it scans free text against the REAL canonical team list
(`ai_chat_afl._canonical_teams()`, sourced from `afl_match_features_v2.csv`)
using the same nickname-stripping convention (`"Geelong Cats"` →
`"cats"`) that `_resolve_team_name` already uses, so extraction and
resolution can never disagree.

**Result: 21/21 (100%)** on the current test set — full table in
[`logs/router_accuracy.md`](logs/router_accuracy.md) (regenerate with
`python3 tests/test_router_accuracy.py`). Test-case team names match the
synthetic CSV shipped here (Melbourne Demons, Richmond Tigers, Collingwood
Magpies, Geelong Cats, Carlton Blues) — swap in real team names once you
drop in the real CSV, no code changes needed.

Two categories of fix were needed to get here (both are the kind of thing
this task explicitly asks you to find and fix):
- **Hint-list gaps:** `"what are the chances of X winning next round"` and
  `"predict the exact final score of X vs Y"` initially misrouted — fixed
  by widening `_PREDICTION_MATCH_HINTS` / `_UNSUPPORTED_HINTS`.
- **Extraction regex gaps:** the "X vs Y" splitter wasn't stripping leading
  question phrases ("who will win ...") or trailing time phrases ("...
  this week"), so team names came out dirty (`"who will win collingwood"` /
  `"geelong this week"`). Fixed with `_strip_leading_phrase` /
  `_strip_trailing_phrase`.

---

## Task 3 — Prediction tools + input resolution

`prediction_node` (`nodes.py`) calls `predict.py` through a
thin adapter (`day2_interface.py`) that:
1. Imports `predict.py` defensively — `predict.py` raises at import time if
   `artifacts/` is incomplete; the adapter catches that so the rest of the
   graph still runs and reports a clear tool error instead of crashing the
   whole app (see Task 4, Run 12 in the e2e log).
2. Adds grounding: `predict.py` returns a prediction but no "why" — the
   adapter reads the same `_latest_team_state` / `_latest_player_state`
   tables `predict.py` already loaded and produces 2–3 human-readable
   comparison bullets (recent form win-rate, ladder position, season wins
   for matches; recent disposal/fantasy-point form for players). These are
   simple rule-based comparisons on the same features the model saw, not a
   SHAP explanation of the model's internals — the formatted response says
   so explicitly.

**Input resolution** (`entity_resolution.py`): team nicknames are resolved
via `ai_chat_afl._resolve_team_name` — no reimplementation of nickname matching.
For prediction requests specifically, the resolved name is additionally
cross-checked against `predict.py`'s own `valid_teams` (from Day 2's
`artifacts/valid_teams.joblib`), since the models can only score teams they
were trained on; this is a safety net in case the two datasets' naming ever
drifts, and falls back to a direct fuzzy match against `predict.py`'s own
team list if needed.

**"This week" / fixture resolution:** the match-feature CSVs described in
this project are completed-match records (every row has a final score), so
there's no future-fixture calendar to resolve "this week" against — and
`predict.py` doesn't need one either, since it always predicts against each
team's *latest known rolling state* ("if these two played next"). So
`resolve_when()` is intentionally a no-op passthrough for now; if the
artifacts later include a fixture calendar, that's the one place to wire it in.

Every prediction response (`response_formatter_node`) includes the
estimated probability, 2–3 grounding bullets, the model name + headline
accuracy metric (pulled straight from `predict.py`'s own docstring numbers:
63.4% test accuracy / 63.0% top-5 hit rate), and an explicit disclaimer.
Real output against the fitted model:
```
**Prediction (not a certainty):** Melbourne Demons (88% estimated win probability, high confidence)

Key factors:
- better recent form: Melbourne Demons won 80% of their last 5 vs Richmond Tigers's 40%
- higher on the ladder: Melbourne Demons is 2 vs Richmond Tigers's 9
- more wins this season: Melbourne Demons has 14 vs Richmond Tigers's 7

_Model: Logistic Regression, ~63% test accuracy. This is a statistical estimate, not a guarantee -- upsets happen._
```

---

## Task 4 — Self-correction & fallbacks

- **`validation_node`**: `tool_result["ok"] == True` → format the response.
  `False` → look at `entities["unresolved_reason"]` and route to
  `clarification_node`, which asks the user directly instead of guessing.
- **`fallback_node`**: reached for `intent == "unsupported"` (prediction-shaped
  but outside modeled scope, e.g. exact score/margin) *and* as validation's
  catch-all when the predictor itself is unavailable (missing artifacts) —
  states plainly what's out of scope rather than hallucinating a number.
- **Predictor-unavailable is fail-closed, not a crash.** `day2_interface.py`
  catches `predict.py`'s import-time `FileNotFoundError` and exposes
  `PREDICT_AVAILABLE = False` instead of letting it propagate; `prediction_node`
  checks this before doing anything else and routes straight to a clear
  "predictor not available" tool error → `fallback`. Verified in the e2e
  suite (Run 12) by toggling `day2_interface.PREDICT_AVAILABLE = False` at
  runtime and confirming the graph degrades gracefully instead of crashing.
- All model calls are wrapped in `try/except` so a raw exception from
  `predict.py` never leaks to the user as a stack trace.

### A real bug this caught (worth calling out)

Building the multi-turn e2e test (Task 5) surfaced an actual bug, not a
hypothetical one: on a **second turn of the same conversation thread**
(prediction, then a follow-up retrieval question), the follow-up's
formatted response was silently reusing the **previous turn's** prediction
data. Cause: LangGraph's `MemorySaver` checkpointer persists state across
invocations on a `thread_id`, and `tool_result` isn't a message-list field
with its own reducer — any key a given turn's nodes don't explicitly touch
just keeps its last value from the checkpoint. Turn 2 went through
`chat_agent`, which never sets `tool_result`, so `response_formatter_node`
was still looking at turn 1's `{"kind": "match_prediction", ...}`.

**Fix:** `router_node` (which runs first on every turn, regardless of
intent) now explicitly resets the per-turn volatile fields
(`tool_result`, `validation_status`, `clarification_question`,
`final_response`) to `None` before the rest of the turn runs. This is
exactly the kind of failure mode Task 4's "validate before trusting a tool
result" spirit is meant to guard against, just one level up — the trace
log below (Run 11) is what surfaced it.

---

## Task 5 — End-to-end testing

`tests/test_e2e.py` runs 12 full conversations against the **real**
prediction pipeline, with an injected stand-in for the Day 3 chat agent
(`nodes.set_chat_agent_override`) so the suite runs without a live
`GEMINI_API_KEY`. Delete that override line to run against the real agent.

**Result: 12/12 scenarios pass.** Full output: [`logs/e2e_run.log`](logs/e2e_run.log).

### Annotated trace 1 — clean prediction, real model (Run 1)
```
Query: who will win Melbourne Demons vs Richmond Tigers this week
[router] intent=prediction_match confidence=0.80 team_a_raw='melbourne demons' team_b_raw='richmond tigers'
[prediction_tool] predict_match_winner(Melbourne Demons, Richmond Tigers) -> winner=Melbourne Demons p=0.883 confidence=high
[validation] tool_result ok
[response_formatter] kind=match_prediction
```
Router correctly identifies both full team names → resolved against the
real `ai_chat_afl` team list → `predict.py`'s actual fitted
`LogisticRegression` pipeline called → validation passes → formatter
attaches probability + real grounding bullets (recent form / ladder /
season wins, pulled from `predict._get_team_features`) + disclaimer.

### Annotated trace 2 — clarification loop (Run 8)
```
Query: will the Sharks beat the Cats this week
[router] intent=prediction_match confidence=0.80 team_a_raw='sharks' team_b_raw='cats'
[prediction_tool] team resolution failed: No team matching 'sharks' was found. Known teams: Collingwood Magpies, Geelong Cats, Melbourne Demons, Richmond Tigers.
[validation] tool_result failed (...) -> needs_clarification
[clarification] asking user instead of guessing
```
"Sharks" is an NRL team, not AFL — a deliberately adversarial test case.
`ai_chat_afl._resolve_team_name` correctly returns `None` with an
enumerated list of known teams rather than fuzzy-matching to something
plausible-but-wrong; `validation_node` routes to `clarification_node`
instead of `response_formatter` — the Task 4 "loop back instead of
guessing" requirement, working against the real resolver.

### Annotated trace 3 — multi-turn follow-up (Runs 10→11), incl. the bug fix above
```
Turn 1: "who will win Collingwood vs Geelong this week"
[router] intent=prediction_match team_a_raw='collingwood' team_b_raw='geelong'
[prediction_tool] predict_match_winner(Collingwood Magpies, Geelong Cats) -> winner=Collingwood Magpies p=0.600
[validation] tool_result ok -> formatted prediction returned

Turn 2 (same thread_id): "what about their stats last round instead"
[router] intent=retrieval team_a_raw=None team_b_raw=None
[chat_agent] delegating to ai_chat_afl (intent=retrieval)
[response_formatter] kind=None -> "Melbourne Demons, round 5, 2020: disposals 16-18 ..." (stub retrieval answer)
```
Two things worth noting here. First, the router correctly re-classifies
turn 2 as `retrieval` even though the rule-based classifier has no
coreference resolution ("their" isn't resolved back to Collingwood/Geelong
— it just recognizes the retrieval-shaped phrasing). Second, and more
important: this is the exact scenario that surfaced the state-leak bug
described in Task 4 — before the fix, this turn's response would have
silently repeated turn 1's Collingwood/Geelong prediction instead of
delegating to the chat agent. Post-fix, `tool_result` correctly resets to
`None` each turn and the response comes from the right place.

The **coreference gap** ("their" not resolving to a specific team so the
delegated agent can't actually answer "their" stats precisely) is a real,
honestly-flagged limitation of the rule-based router — exactly what
`classify_llm` (Gemini, given `history_summary`) is meant to close in
production, per the Task 2 design.

### LangGraph orchestration vs. a monolithic agent — what actually improved

Building this against real files rather than mocks made the difference
concrete. `ai_chat_afl`'s agent, on its own, has zero prediction tools —
handed a prediction-shaped query directly, it would have to either refuse
incorrectly or hallucinate a winner from its language-model "knowledge",
which is precisely the failure mode a stats-grounded assistant exists to
avoid. The router's conditional edge makes that structurally impossible:
no prediction-shaped query can reach the chat agent, full stop. Separately,
the multi-turn state-leak bug is a good illustration of *why* explicit,
inspectable state matters even when using LangGraph: it was catchable
specifically because `state.trace` made the wrong data source visible
line-by-line, whereas a single ReAct-style agent's freeform transcript
would have made the same bug much harder to pin down to a specific state
field. The cost is real too — the rule-based router's lack of coreference
resolution is a genuine capability gap versus a strong general agent, which
is exactly why the design keeps the LLM router swappable while keeping the
safety-critical parts (validation, disclaimers, fail-closed fallback)
outside the LLM's discretion entirely.

---

## Prediction pipeline bug found and fixed (added after initial submission)

Testing revealed that `predict.py`'s match/player predictions were producing
suspiciously flat, unconvincing results. This turned out to have a deeper
root cause than an inference-time bug alone -- confirmed against
`AFL_Data_Foundations_Complete.ipynb`, the notebook that actually built the
training features.

### The real root cause: a lossy artifact-export step, not bad feature engineering

The notebook's feature engineering (Task 4) is genuinely solid: all 9 team
features (win streak, both score averages, form win rate, days rest, season
wins, ladder position, venue win rate, venue games played) and all 8 player
features are computed correctly with proper `shift(1)` rolling windows (no
leakage), saved to `afl_match_features_v2.csv` / `afl_player_features_v2.csv`
-- the same files `ai_chat_afl.py` already uses for retrieval.

But `predict.py`'s inference-time snapshots (`latest_team_state.parquet`,
`latest_player_state.parquet`, `match_history.parquet`) -- built by a
separate, not-provided notebook -- only carried forward **3 of the 9** team
columns and **1 of the 8** player columns. The rich, correctly-computed data
existed; it just never made it into the snapshot files `predict.py` actually
depends on at prediction time. Two compounding bugs made this worse:

**1. Team lookup silently failed for every team.** `_get_team_features()`
checked `if team in _latest_team_state.index`, which only works if `team`
is the DataFrame's index. In the real artifacts, `team` is a plain column.
That check evaluated `False` for every team, every time, so every
prediction fell back to identical hardcoded defaults
(`form_last5_win_rate=0.5`, `ladder_position=10.0`, `season_wins=0.0`) --
team identity was almost entirely ignored. Confirmed empirically: the
original code predicted a 12th-placed team (30% recent form) to beat a
3rd-placed team (70% recent form) just because the weaker team was listed
as home.

**2. Thirteen of the model's 19 trained numeric features were hardcoded to
`0.0`** (win streak, recent score averages, days rest, venue stats,
head-to-head win rate) regardless of matchup, rather than `NaN`. Both
fitted pipelines already include a `SimpleImputer(strategy='median')` as
their first step specifically to handle missing values sensibly -- but
`0.0` isn't treated as missing, so the imputer never got a chance to act,
and the model was fed a fixed, wildly out-of-distribution value every time
(e.g. `form_last5_score_avg` has a training median of ~94; `0.0` is roughly
5.7 standard deviations away from anything the model saw in training).

### The fix: stop depending on the lossy snapshots, read the full feature tables directly

Rather than patch the impoverished snapshot files, `predict.py` now reads
team/player "current state" directly from `afl_match_features_v2.csv` /
`afl_player_features_v2.csv` (via `ai_chat_afl`'s own cached readers --
one copy of this data in memory, not two), taking each team's/player's most
recent row:

- `_get_team_features()` pulls all 9 real trained features from that team's
  most recent match row (correctly reading the `home_*` or `away_*`
  prefixed columns depending on which side they were actually on that day).
- `_h2h_win_rate()` computes actual head-to-head history between the two
  specific teams from the full match table, instead of a hardcoded `0.0`.
- `predict_top_player` reads all 8 real trained player features directly
  from each player's most recent row, instead of defaulting 7 of them.
  Gained an optional `opponent` parameter so `opponent_ladder_position` can
  be filled in for real when the opponent is known.
- Anything genuinely still unavailable (e.g. a brand-new team with no
  match history yet) is passed as `NaN`, not `0.0`, so the pipeline's own
  trained median imputer handles it correctly.
- A legacy fallback path (reading the old parquet snapshots) is kept only
  so the module doesn't hard-crash if the full feature CSVs aren't
  reachable in some environment -- predictions are materially weaker on
  that path and it should not be relied on.

**Verified:** with the fix, Melbourne Demons (a 4-game win streak, 1st on
the ladder, 100% win rate at their home venue) is correctly favoured over
Carlton Blues (1-game streak, 3rd, 50% venue win rate) in both home/away
configurations -- the opposite of what the original buggy code produced
for equivalent inputs.

**Two more bugs surfaced by manually testing predictions through `chat_cli.py`**,
both in how the winning side's probability was reported (fixed in
`predict.py`, not just the display layer):
- `probability` in the original result is always P(home team wins),
  regardless of who ends up predicted as the winner. When the away team
  won, the LangGraph formatter was displaying that home-side number
  directly next to the away team's name (e.g. showing "Geelong Cats: 17%"
  when Geelong's actual win probability was 82%). Fixed by adding a
  `winner_probability` field to `predict_match_winner`'s return dict --
  the probability of whichever outcome was actually predicted -- and
  having the formatter use that instead.
- `confidence` was bucketed directly from `win_prob` (P(home wins)), so a
  confidently-predicted **away** win (a low `win_prob`, e.g. 0.17) was
  mislabeled "low confidence" instead of "high confidence" -- confidence
  should reflect how far the *winning* side's probability is from a
  toss-up, not which side happens to be home. Fixed to bucket on the
  winning outcome's own probability.

The original file is kept as `predict_original_backup.py` for comparison.
This is a meaningful change to Day 2's model code, not just the LangGraph
wrapper -- review it before adopting, and re-point `_get_team_features` /
`_team_derived_features` at your real `latest_team_state.parquet` /
`match_history.parquet` schemas if they differ from what's described here.

## Player season-stat tool (added after initial submission)

Two additional tools are wired into the Day 3 agent's tool list for
multi-year totals and head-to-head player comparisons:

- `get_player_season_stat_total(player, stat, years)` — e.g. "how many
  total tackles did Sam Walsh get across 2022 and 2023 combined"
- `compare_players_season_stat(player_a, player_b, stat, year, per_game)` —
  e.g. "compare disposals between Sam Walsh and Lachie Neale in 2024" or
  "who had more kicks per game, Patrick Cripps or Clayton Oliver, in 2023"

Both are thin wrappers around `player_stats_query.py` (a standalone script
that also runs on its own — see its module docstring for CLI usage), reading
`merged_players.csv`, the player-season aggregate file (one row per
player per year, sometimes split into a regular-season row and a finals row
via `is_finals`). Per-game comparisons are games-weighted
(`sum(stat) / sum(games_played)` across any split rows), not a naive
average of two precomputed rates. Both fail closed on an unresolved player
or stat name — same philosophy as the rest of this project — rather than
guessing.

`merged_players.csv` at the project root is a placeholder (a handful of
made-up rows for Sam Walsh / Lachie Neale / Patrick Cripps / Clayton
Oliver) — replace it with the real file, no code changes needed; both
the name-lookup use (`_id_to_name`) and the new stat tools read the same file.

## File map
```
predict.py                 Day 2 — prediction module, unmodified
ai_chat_afl.py               Day 3 — chat/retrieval agent, extended with 2 new stat tools
player_stats_query.py        standalone player season-stat query tool (also usable on its own)
artifacts/                   Day 2 artifacts (2 real joblib pipelines + placeholder rest -- see artifacts/READ_ME_FIRST.txt)
afl_match_features_v2.csv    placeholder for Day 3 data -- see CSV_DATA_READ_ME_FIRST.txt
afl_player_features_v2.csv   placeholder for Day 3 data
merged_players.csv           placeholder for Day 3 data (player names + full season stats)

state.py                    Task 1 — State schema
day2_interface.py           Task 3 — adapter over predict.py (grounding + graceful degradation)
entity_resolution.py        Task 3 — team resolution, reuses ai_chat_afl's team resolver
router.py                   Task 2 — router node, rule-based + Gemini-based classifiers
nodes.py                    Task 3/4 — prediction tool, chat_agent delegation, validation, clarification, fallback, formatting
graph.py                    Task 1 — StateGraph assembly + run_query() helper

tests/test_router_accuracy.py   Task 2 — 21-query accuracy table
tests/test_e2e.py               Task 5 — 12 full conversations, annotated traces
logs/router_accuracy.md         Task 2 deliverable (generated)
logs/e2e_run.log                Task 5 deliverable (generated)
```
