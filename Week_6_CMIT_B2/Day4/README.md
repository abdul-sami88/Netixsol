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

### 2. verify dependencies

### 3. Set your API key

```bash
export GEMINI_API_KEY=your_key_here
# or put it in a .env file in the project root
```

### 4. Run

```bash
python3 graph.py                          # single demo query
python3 tests/test_router_accuracy.py     # Task 2 deliverable — routing accuracy table
python3 tests/test_e2e.py                 # Task 5 deliverable — 12 full conversations, annotated traces
```

---

## Task 1 — Graph design

### State schema (`state.py`)

```text
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

```text
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

+ **Hint-list gaps:** `"what are the chances of X winning next round"` and
  `"predict the exact final score of X vs Y"` initially misrouted — fixed
  by widening `_PREDICTION_MATCH_HINTS` / `_UNSUPPORTED_HINTS`.
+ **Extraction regex gaps:** the "X vs Y" splitter wasn't stripping leading
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

```text
**Prediction (not a certainty):** Melbourne Demons (88% estimated win probability, high confidence)

Key factors:
- better recent form: Melbourne Demons won 80% of their last 5 vs Richmond Tigers's 40%
- higher on the ladder: Melbourne Demons is 2 vs Richmond Tigers's 9
- more wins this season: Melbourne Demons has 14 vs Richmond Tigers's 7

_Model: Logistic Regression, ~63% test accuracy. This is a statistical estimate, not a guarantee -- upsets happen._
```

---

## Task 4 — Self-correction & fallbacks

+ **`validation_node`**: `tool_result["ok"] == True` → format the response.
  `False` → look at `entities["unresolved_reason"]` and route to
  `clarification_node`, which asks the user directly instead of guessing.
+ **`fallback_node`**: reached for `intent == "unsupported"` (prediction-shaped
  but outside modeled scope, e.g. exact score/margin) *and* as validation's
  catch-all when the predictor itself is unavailable (missing artifacts) —
  states plainly what's out of scope rather than hallucinating a number.
+ **Predictor-unavailable is fail-closed, not a crash.** `day2_interface.py`
  catches `predict.py`'s import-time `FileNotFoundError` and exposes
  `PREDICT_AVAILABLE = False` instead of letting it propagate; `prediction_node`
  checks this before doing anything else and routes straight to a clear
  "predictor not available" tool error → `fallback`. Verified in the e2e
  suite (Run 12) by toggling `day2_interface.PREDICT_AVAILABLE = False` at
  runtime and confirming the graph degrades gracefully instead of crashing.
+ All model calls are wrapped in `try/except` so a raw exception from
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

```text
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

```text
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

```text
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
