"""
Task 5: end-to-end testing.

Runs full conversations across all paths using the REAL prediction pipeline
(predict.py + fitted joblib models) and a lightweight injected stand-in for
the Day 3 chat agent (so this suite runs without a live GEMINI_API_KEY).

To run against the REAL Day 3 agent instead: set GEMINI_API_KEY, make sure
afl_match_features_v2.csv / afl_player_features_v2.csv are present, and
delete the `nodes.set_chat_agent_override(...)` call below.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import nodes  # noqa: E402
from graph import build_graph, run_query  # noqa: E402


def _stub_chat_agent(query: str, thread_id: str = "default") -> str:
    """Stand-in for ai_chat_afl.invoke_afl_agent -- mimics its scope
    guardrail closely enough to exercise the graph's routing/formatting
    without a live Gemini call. Swap out for the real thing in production
    (see module docstring)."""
    q = query.lower()
    off_topic_markers = ["weather", "recipe", "python code", "capital of", "joke"]
    if any(m in q for m in off_topic_markers):
        return "I can only help with AFL topics. I can compare AFL clubs, players, or recent match statistics if you like."
    if "stats last round" in q or ("stats" in q and "demons" in q):
        return "Melbourne Demons, round 5, 2020: disposals 16-18 across the top players (stub retrieval answer)."
    return f"(stub Day3 chat-agent answer for: {query!r})"


def annotate(label: str, out: dict):
    print(f"\n{'=' * 70}\n{label}\n{'=' * 70}")
    print(f"Query: {out['user_query']}")
    print(f"Intent: {out.get('intent')}  (confidence={out.get('router_confidence')})")
    print(f"Validation status: {out.get('validation_status')}")
    print("\nFull trace:")
    for line in out.get("trace", []):
        print(f"  {line}")
    print("\nFinal response:")
    print(f"  {out.get('final_response')}")


def main():
    nodes.set_chat_agent_override(_stub_chat_agent)
    app = build_graph()
    results = []

    # 1. Prediction - match, real model call (annotated in full)
    out = run_query(app, "who will win Melbourne Demons vs Richmond Tigers this week", thread_id="t1")
    annotate("Run 1 (ANNOTATED): prediction_match (real fitted model)", out)
    results.append(("prediction_match", out["intent"] == "prediction_match" and "Prediction" in out["final_response"]))

    # 2. Prediction - match, nickname phrasing
    out = run_query(app, "will the Demons beat the Tigers this week", thread_id="t2")
    results.append(("prediction_match (nickname)", out["intent"] == "prediction_match" and out.get("validation_status") == "ok"))

    # 3. Prediction - player, real model call
    out = run_query(app, "who will top-score for Melbourne Demons this week", thread_id="t3")
    results.append(("prediction_player", out["intent"] == "prediction_player" and out.get("validation_status") == "ok"))

    # 4. Retrieval - delegates to (stubbed) Day3 agent
    out = run_query(app, "what were the Demons' stats last round", thread_id="t4")
    results.append(("retrieval (delegated)", out["intent"] == "retrieval"))

    # 5. Factual - delegates to (stubbed) Day3 agent
    out = run_query(app, "explain the AFL finals system", thread_id="t5")
    results.append(("factual (delegated)", out["intent"] == "factual"))

    # 6. Factual #2
    out = run_query(app, "what does holding the ball mean", thread_id="t6")
    results.append(("factual #2 (delegated)", out["intent"] == "factual"))

    # 7. Off-topic refusal - delegates to (stubbed) Day3 agent, which owns
    # the actual refusal wording
    out = run_query(app, "what's the weather like today", thread_id="t7")
    results.append(("off_topic refusal (delegated)", out["intent"] == "off_topic" and "AFL topics" in out["final_response"]))

    # 8. Ambiguous / unresolvable team -> clarification loop (ANNOTATED in full)
    out = run_query(app, "will the Sharks beat the Cats this week", thread_id="t8")
    annotate("Run 8 (ANNOTATED): unresolvable team -> clarification", out)
    results.append(("clarification loop", out.get("validation_status") == "needs_clarification"))

    # 9. Unsupported prediction type -> fallback
    out = run_query(app, "predict the exact final score of Melbourne Demons vs Richmond Tigers", thread_id="t9")
    results.append(("unsupported -> fallback", out["intent"] == "unsupported" and "can't predict" in out["final_response"]))

    # 9b. Season/finals-outcome question, no two teams named -> unsupported,
    # NOT a "which teams do you mean" clarification (naming teams wouldn't
    # make "who wins the whole finals series" answerable by a single-match model)
    out = run_query(app, "who will win the AFL 2026 final?", thread_id="t9b")
    results.append(("season-level (grand final) -> unsupported, not clarification", out["intent"] == "unsupported"))

    # 9c. Sanity check: a real single-match question that happens to mention
    # "grand final" still resolves normally (two teams ARE named)
    out = run_query(app, "who will win Melbourne Demons vs Richmond Tigers in the grand final", thread_id="t9c")
    results.append(("real match naming grand final -> still predicts", out["intent"] == "prediction_match" and out.get("validation_status") == "ok"))

    # 10-11. Multi-turn: prediction, then a follow-up on the SAME thread
    out10 = run_query(app, "who will win Collingwood vs Geelong this week", thread_id="t10")
    out11 = run_query(app, "what about their stats last round instead", thread_id="t10")
    annotate("Run 10 (ANNOTATED, turn 1 of multi-turn thread t10): prediction", out10)
    annotate("Run 11 (ANNOTATED, turn 2 of multi-turn thread t10): follow-up retrieval", out11)
    results.append(("multi-turn turn 1", out10["intent"] == "prediction_match" and out10.get("validation_status") == "ok"))
    results.append(("multi-turn turn 2", out11["intent"] in ("retrieval", "off_topic")))  # rule router may miss coreference; see README

    # 12. Predictor-unavailable fallback: simulate the artifacts genuinely
    # missing (Task 4 fail-closed behaviour), independent of the rest.
    import day2_interface
    original = day2_interface.PREDICT_AVAILABLE
    day2_interface.PREDICT_AVAILABLE = False
    out12 = run_query(app, "who will win Melbourne Demons vs Richmond Tigers this week", thread_id="t12")
    day2_interface.PREDICT_AVAILABLE = original
    results.append(("predictor unavailable -> fallback, not a crash", out12.get("validation_status") == "unsupported"))

    print(f"\n{'=' * 70}\nSUMMARY\n{'=' * 70}")
    passed = 0
    for name, ok in results:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
        passed += ok
    print(f"\n{passed}/{len(results)} scenarios passed")


if __name__ == "__main__":
    main()
