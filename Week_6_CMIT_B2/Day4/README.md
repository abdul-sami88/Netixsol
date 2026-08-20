# Week 6 Day 4 — LangGraph Integration: Routing Between Chat, Retrieval & Prediction

A working LangGraph app that routes an AFL user query to one of: a direct
factual answer, a stat-retrieval tool, a prediction tool (match winner /
top scorer), a refusal (off-topic), or a fallback (unsupported), with
validation and a clarification loop in between.

**Run it:**

```bash
pip install langgraph langchain-core pydantic
python3 graph.py                          # single demo query
python3 tests/test_router_accuracy.py     # Task 2 deliverable
python3 tests/test_e2e.py                 # Task 5 deliverable
```

## ⚠️ Integration point — read this first

I don't have your actual Day 2 files (models, dataset, team-key encoding),
so this repo ships with **deterministic stand-ins** that make the whole
graph runnable and testable end-to-end right now. There is exactly **one
file** you need to edit to plug in your real work:

| File | What to replace |
|---|---|
| `day2_interface.py` | `predict_match_winner`, `predict_top_player`, `get_player_stats` — swap the bodies for your real model calls. Keep the function signatures and return-dict shapes identical (documented in the file's docstring) and nothing else in the graph needs to change. |
| `entity_resolution.py` | `CANONICAL_TEAMS` / `TEAM_ALIASES` — replace with your dataset's exact team key strings. `_get_fixtures()` — replace with a real fixture-table lookup. |

Everything else (`state.py`, `router.py`, `nodes.py`, `graph.py`) is
model-agnostic and shouldn't need changes.

---

## Task 1 — Graph design

### State schema (`state.py`)

```text
AFLState
├── messages: list[BaseMessage]        # full conversation history (LangGraph add_messages reducer)
├── user_query: str
├── intent: Intent | None              # factual | retrieval | prediction_match | prediction_player | off_topic | unsupported
├── router_confidence: float | None
├── entities: Entities                 # raw + resolved teams/players/dates, + failure reason
├── tool_result: ToolResult | None      # {ok, kind, data, error, grounding}
├── validation_status: str | None       # ok | error | needs_clarification | unsupported
├── clarification_question: str | None
├── final_response: str | None
└── trace: list[str]                   # breadcrumb per node, for Task 5 logging
```

### Graph sketch

```text
START
  |
  v
router --------------------------------------------------.
  | factual      | retrieval      | prediction_*    | off_topic/unsupported
  v               v                v                     v
direct_answer  retrieval_tool  prediction_tool     refusal / fallback
  |               |                |                     |
  |               v                v                     |
  |             validation ----------                     |
  |               |ok      \__needs_clarification__> clarification
  |               v                                       |
  '--------> response_formatter <---------------------------'
                  |
                  v
                 END
```

Implemented 1:1 in `graph.py` using `StateGraph` + `add_conditional_edges`.

### Why explicit routing (LangGraph) instead of one free-form agent

1. **Structural guarantee on prediction disclaimers.** The spec requires
   predictions to *always* be framed probabilistically. With a single
   generic agent deciding turn-by-turn which tool to call and how to word
   the answer, "always include a disclaimer" is a prompting hope that can
   silently drift or get dropped on some phrasings. Here, *every* path
   that reaches `prediction_node` is funneled through the same
   `response_formatter_node` branch that hard-codes the probability +
   disclaimer text — it's not something the model can "forget" mid-generation.

2. **Deterministic fail-closed behavior.** Task 4 requires that
   unresolvable teams/players loop back to ask the user rather than
   guessing. A free agent can rationalize a fuzzy match ("Sharks" → some
   plausible-sounding AFL team) because nothing stops it. Here,
   `entity_resolution.py` either returns a canonical key or `None` +
   reason, and `validation_node` is a hard gate: `ok=False` can *only*
   reach `clarification` or `fallback`, never `response_formatter`.

3. **Debuggability / auditability.** Because each node's job is narrow and
   explicit, `state.trace` gives an exact, reproducible node-by-node path
   per request (see Task 5 logs below). A ReAct-style single agent's
   freeform tool-call transcript is harder to audit and harder to unit
   test in isolation (you can't easily test "the router" separately from
   "the disclaimer wording" when they're the same LLM call).

4. **Cheaper and more reliable for the easy branches.** Off-topic refusal
   and "unsupported stat type" don't need an LLM turn at all in this
   design — they're direct dict returns. A monolithic agent pays an LLM
   call (and a chance of misbehaving) for every branch, including the
   trivial ones.

The tradeoff: explicit graphs are less flexible for genuinely novel
phrasing than a strong general agent. That's why the router is built with
a swappable LLM-based classifier (`classify_llm` in `router.py`) for
production use — you get the routing *structure's* safety guarantees while
still using an LLM for the part (natural-language understanding) it's
actually good at.

---

## Task 2 — Router node + accuracy

`router.py` implements `classify_rule_based` (default, offline,
deterministic — used for the accuracy table below) and `classify_llm`
(structured-output Anthropic call, toggle with `USE_LLM_ROUTER=1`) behind
a shared `classify()` entrypoint, so `router_node` doesn't care which is active.

**Initial run: 18/20 (90%).** Two misroutes found and fixed:

- *"what are the chances of Fremantle winning next round"* → routed
  `off_topic` (no hint phrase matched "chances of X winning"). **Fix:**
  added `"chances of"` / `"winning next round"` to the prediction-match
  hint list.
- *"predict the exact final score of Collingwood vs Geelong"* → routed
  `prediction_match` (matched on `"predict"` / `" vs "` before the
  unsupported check could catch it). **Fix:** broadened `_UNSUPPORTED_HINTS`
  to include `"final score"`, since "exact score" alone didn't match
  "exact **final** score" as a substring.

**Final run: 20/20 (100%).** Full table in [`logs/router_accuracy.md`](logs/router_accuracy.md)
(regenerate with `python3 tests/test_router_accuracy.py`).

While fixing these I also found and fixed a downstream **entity-extraction**
bug (not a routing bug, but surfaced by the e2e tests in Task 5): the
regex for splitting "X vs Y" wasn't stripping leading question phrases
("who will win ...") or trailing time phrases ("... this week"), so
`team_a`/`team_b` came out as `"who will win collingwood"` /
`"geelong this week"` instead of clean team names. Fixed with
`_strip_leading_phrase` / `_strip_trailing_phrase` in `router.py`.

---

## Task 3 — Prediction tools + input resolution

`prediction_node` (in `nodes.py`) calls `predict_match_winner` /
`predict_top_player` from `day2_interface.py`. Before calling either:

1. **Team alias resolution** (`entity_resolution.resolve_team`): maps
   nicknames ("Pies", "the Cats") → canonical dataset key, via an exact
   alias dict first, then a high-cutoff fuzzy match for typos — but it
   **never** silently guesses between two plausible teams; ambiguity
   returns `None` + reason instead.
2. **Fixture/date resolution** (`entity_resolution.resolve_fixture`):
   resolves "this week" / "next round" + two resolved teams to a concrete
   fixture id and round number.

Every prediction response (`response_formatter_node`) includes:

- the estimated **probability** (`{data['probability']:.0%}`)
- **2–3 grounding features** (`tool_result["grounding"]`, sourced from
  `predict_*`'s `top_features`)
- an explicit **disclaimer** ("statistical estimate, not a guarantee")

Example (from `graph.py`'s demo run):

```text
**Prediction (not a certainty):** Collingwood is favoured to win (71% estimated probability), round 99.

Key factors:
- home ground advantage
- opponent missing key forward (injury list)
- better inside-50 efficiency this season

_This is a statistical estimate, not a guarantee -- upsets happen._
```

---

## Task 4 — Self-correction & fallbacks

- **`validation_node`**: checks `tool_result["ok"]`. `True` → format the
  response. `False` → look at `entities["unresolved_reason"]` (set by
  entity resolution) and route to **`clarification_node`**, which asks
  the user directly instead of guessing (e.g. *"'sharks' didn't match any
  known team or nickname. Could you clarify which team/player you
  mean?"*) — see Run 9 in the annotated traces below.
- **`fallback_node`**: reached for `intent == "unsupported"` (queries the
  router recognizes as AFL-prediction-shaped but outside modeled scope,
  e.g. exact score/margin) *and* as validation's catch-all for anything
  that isn't a clean "ask the user to disambiguate" case. It states
  plainly what's out of scope rather than hallucinating a number.
- All tool calls in `nodes.py` are wrapped in `try/except` so a raw model
  exception never leaks to the user as a stack trace — it's converted to
  a validation `error` and handled the same way as any other failure.

---

## Task 5 — End-to-end testing

`tests/test_e2e.py` runs 12 full conversations covering every path:
match prediction (x2, incl. alias phrasing), player prediction, retrieval
(found + not-found), factual (x2), off-topic refusal, ambiguous-team
clarification loop, unsupported→fallback, and a 2-turn follow-up on a
shared `thread_id` (exercises the `MemorySaver` checkpointer).

**Result: 12/12 scenarios pass.** Full output: [`logs/e2e_run.log`](logs/e2e_run.log).

### Annotated trace 1 — clean prediction (Run 1)

```text
Query: who will win Collingwood vs Geelong this week
[router] intent=prediction_match confidence=0.80 team_a_raw='collingwood' team_b_raw='geelong'
[prediction_tool] predict_match_winner(Collingwood, Geelong) -> winner=Collingwood p=0.71
[validation] tool_result ok
[response_formatter] kind=match_prediction
```

Router correctly identifies intent + both teams → alias resolution passes →
model called → validation passes (`ok=True`) → formatter attaches
probability + grounding + disclaimer. Straight line through the "happy path".

### Annotated trace 2 — clarification loop (Run 9)

```text
Query: will the Sharks beat the Cats this week
[router] intent=prediction_match confidence=0.80 team_a_raw='sharks' team_b_raw='cats'
[prediction_tool] team resolution failed: 'sharks' didn't match any known team or nickname
[validation] tool_result failed (...) -> needs_clarification
[clarification] asking user instead of guessing
```

"Sharks" isn't an AFL team (it's an NRL team — a deliberately adversarial
test case). `resolve_team` correctly returns `None` rather than fuzzy-matching
to something plausible-but-wrong; `validation_node` catches `ok=False` and
routes to `clarification_node` instead of `response_formatter` — this is
the Task 4 "loop back instead of guessing" requirement working as designed.

### Annotated trace 3 — multi-turn follow-up (Runs 11→12), with an honest limitation

```text
Turn 1: "who will win Carlton vs Essendon this week"
[router] intent=prediction_match team_a_raw='carlton' team_b_raw='essendon'
[prediction_tool] predict_match_winner(Carlton, Essendon) -> winner=Essendon p=0.75
[validation] tool_result ok  ->  formatted prediction returned

Turn 2 (same thread_id): "what about their last round stats instead"
[router] intent=retrieval team_a_raw=None team_b_raw=None
[retrieval_tool] team resolution failed: no team text was extracted from the query
[validation] tool_result failed (...) -> needs_clarification
```

The router correctly re-classifies turn 2 as `retrieval` (good), but the
**rule-based** classifier doesn't resolve "their" back to Carlton/Essendon
from turn 1 — it has no coreference resolution, so it asks for
clarification rather than silently guessing (which is at least the safe
failure mode). This is precisely the gap the LLM-based router
(`classify_llm`, which is passed a `history_summary`) is meant to close in
production — flagged here rather than hidden, per the "don't hallucinate"
spirit of Task 4.

### LangGraph orchestration vs. a monolithic agent — what actually improved

Building this made the difference concrete rather than theoretical: with
one generic agent I'd have to trust it to (a) always attach the prediction
disclaimer, (b) never guess an unresolved team, and (c) never hallucinate
a stat it doesn't have — three separate "hope the prompt held" bets on
every single turn. Here, (a) is structural (only one code path formats
predictions), (b) is a hard gate in `validation_node` (an `ok=False`
result *cannot* reach the formatter), and (c) fails closed because
`get_player_stats` returning `None` is treated identically to any other
tool error. The cost is real too: the rule-based router is measurably
worse at coreference ("their" in Run 12) than a good general agent would
be — which is exactly why the design keeps the LLM swappable at the router
step while keeping the safety-critical parts (validation, disclaimers,
fallback wording) outside the LLM's discretion entirely.

---

## File map

```text
state.py                 Task 1 — State schema
entity_resolution.py      Task 3 — team alias + fixture resolution
day2_interface.py         Task 3 — INTEGRATION POINT for your real models
router.py                 Task 2 — router node + rule-based/LLM classifiers
nodes.py                  Task 3/4 — tool nodes, validation, clarification, fallback, formatting
graph.py                  Task 1 — StateGraph assembly + run_query() helper
tests/test_router_accuracy.py   Task 2 — 20-query accuracy table
tests/test_e2e.py               Task 5 — 12 full conversations, annotated traces
logs/router_accuracy.md         Task 2 deliverable (generated)
logs/e2e_run.log                Task 5 deliverable (generated)
```
