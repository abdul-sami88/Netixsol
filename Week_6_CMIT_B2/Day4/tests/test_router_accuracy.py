"""
Task 2: routing accuracy test on 15-20 varied queries.

Run: python3 tests/test_router_accuracy.py
Produces a markdown accuracy table in logs/router_accuracy.md
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from router import classify_rule_based  # noqa: E402

# (query, expected_intent)
TEST_CASES = [
    ("who will win Collingwood vs Geelong this week", "prediction_match"),
    ("will the Pies beat the Cats this week", "prediction_match"),
    ("who's going to win the Carlton v Essendon game", "prediction_match"),
    ("predict the winner of Richmond vs Hawthorn", "prediction_match"),
    ("what are the chances of Fremantle winning next round", "prediction_match"),
    ("who will top-score for Collingwood this week", "prediction_player"),
    ("who is the best player likely to top score for the Cats", "prediction_player"),
    ("who's the leading goalkicker going to be for Sydney", "prediction_player"),
    ("what were Collingwood's stats last round", "retrieval"),
    ("how many disposals did Geelong average last round", "retrieval"),
    ("what was Geelong's ladder position last round", "retrieval"),
    ("how many tackles did the Cats get last round", "retrieval"),
    ("what's the highest attendance in AFL grand final history", "factual"),
    ("who has won the most brownlow medals", "factual"),
    ("explain the AFL finals system", "factual"),
    ("what's the weather like today", "off_topic"),
    ("can you write me some python code", "off_topic"),
    ("what's the capital of France", "off_topic"),
    ("tell me a joke", "off_topic"),
    ("predict the exact final score of Collingwood vs Geelong", "unsupported"),
]


def main():
    correct = 0
    rows = []
    for query, expected in TEST_CASES:
        decision = classify_rule_based(query)
        got = decision.intent
        ok = got == expected
        correct += ok
        rows.append((query, expected, got, decision.confidence, "✅" if ok else "❌"))

    total = len(TEST_CASES)
    accuracy = correct / total

    lines = [
        "# Router accuracy report",
        "",
        f"**Accuracy: {correct}/{total} = {accuracy:.0%}**",
        "",
        "| Query | Expected | Predicted | Confidence | Result |",
        "|---|---|---|---|---|",
    ]
    for query, expected, got, conf, mark in rows:
        lines.append(f"| {query} | {expected} | {got} | {conf:.2f} | {mark} |")

    report = "\n".join(lines)
    print(report)

    out_path = Path(__file__).resolve().parent.parent / "logs" / "router_accuracy.md"
    out_path.write_text(report)
    print(f"\nWritten to {out_path}")


if __name__ == "__main__":
    main()
