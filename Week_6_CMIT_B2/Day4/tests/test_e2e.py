"""
Task 5: end-to-end testing.

Runs 10+ full conversations across all paths:
  1-2: prediction (match)
  3:   prediction (player)
  4-5: retrieval
  6-7: factual
  8:   off_topic refusal
  9:   ambiguous input -> clarification loop
  10:  unsupported -> fallback
  11-12: multi-turn follow-up (same thread_id across two calls)

Prints a full annotated trace for runs #1, #9, #11-12 (the 3 "representative"
runs Task 5 asks for) and a compact pass/fail summary for the rest.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from graph import build_graph, run_query  # noqa: E402


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
    app = build_graph()
    results = []

    # 1. Prediction - match (annotated in full)
    out = run_query(app, "who will win Collingwood vs Geelong this week", thread_id="t1")
    annotate("Run 1 (ANNOTATED): prediction_match", out)
    results.append(("prediction_match", out["intent"] == "prediction_match" and "Prediction" in out["final_response"]))

    # 2. Prediction - match, alias phrasing
    out = run_query(app, "will the Pies beat the Cats this week", thread_id="t2")
    results.append(("prediction_match (alias)", out["intent"] == "prediction_match"))

    # 3. Prediction - player
    out = run_query(app, "who will top-score for Collingwood this week", thread_id="t3")
    results.append(("prediction_player", out["intent"] == "prediction_player"))

    # 4. Retrieval - known team/round in stub DB
    out = run_query(app, "what were Collingwood's stats last round", thread_id="t4")
    results.append(("retrieval (found)", out.get("validation_status") == "ok"))

    # 5. Retrieval - team not in stub DB -> should fail validation gracefully
    out = run_query(app, "what were the Suns' stats last round", thread_id="t5")
    results.append(("retrieval (not found -> clarification)", out.get("validation_status") == "needs_clarification"))

    # 6. Factual
    out = run_query(app, "explain the AFL finals system", thread_id="t6")
    results.append(("factual", out["intent"] == "factual"))

    # 7. Factual
    out = run_query(app, "who has won the most brownlow medals", thread_id="t7")
    results.append(("factual #2", out["intent"] == "factual"))

    # 8. Off-topic refusal
    out = run_query(app, "what's the weather like today", thread_id="t8")
    results.append(("off_topic refusal", out["intent"] == "off_topic" and "AFL assistant" in out["final_response"]))

    # 9. Ambiguous / unresolvable team -> clarification loop (ANNOTATED in full)
    out = run_query(app, "will the Sharks beat the Cats this week", thread_id="t9")
    annotate("Run 9 (ANNOTATED): unresolvable team -> clarification", out)
    results.append(("clarification loop", out.get("validation_status") == "needs_clarification"))

    # 10. Unsupported prediction type -> fallback
    out = run_query(app, "predict the exact final score of Collingwood vs Geelong", thread_id="t10")
    results.append(("unsupported -> fallback", out["intent"] == "unsupported" and "don't have a model" in out["final_response"]))

    # 11-12. Multi-turn follow-up on the SAME thread (shared checkpointer state)
    out11 = run_query(app, "who will win Carlton vs Essendon this week", thread_id="t11")
    out12 = run_query(app, "what about their last round stats instead", thread_id="t11")
    annotate("Run 11 (ANNOTATED, turn 1 of multi-turn thread t11): prediction", out11)
    annotate("Run 12 (ANNOTATED, turn 2 of multi-turn thread t11): follow-up retrieval", out12)
    results.append(("multi-turn turn 1", out11["intent"] == "prediction_match"))
    results.append(("multi-turn turn 2", out12["intent"] == "retrieval"))

    print(f"\n{'=' * 70}\nSUMMARY\n{'=' * 70}")
    passed = 0
    for name, ok in results:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
        passed += ok
    print(f"\n{passed}/{len(results)} scenarios passed")


if __name__ == "__main__":
    main()
