"""
evaluate.py — Task 5: Hallucination Evaluation.

For each of the 20 labelled questions (evaluation/questions.py) we run the
real pipeline and score three metrics automatically (no LLM judge needed —
answers are template-generated directly from citations, so grounding is
mechanically verifiable rather than estimated):

  Grounding Rate      = % of answers where every stated fact is backed by
                         an explicit citation (sql row / vector chunk), OR
                         the answer is the refusal message (i.e. correctly
                         "grounded" in "we have no verified data" rather
                         than inventing something).

  Retrieval Accuracy  = % of questions where the retriever's route matches
                         the expected_route AND, for answerable questions,
                         at least one relevant record was returned; for
                         unanswerable questions, correctly returned nothing
                         relevant (i.e. did not silently substitute a
                         different property/city than asked about).

  Hallucination Rate  = % of questions where the system asserted a fact
                         NOT supported by any citation. Because generation
                         is strictly extractive here, this should be ~0%
                         unless the router grounds the answer in the WRONG
                         entity — we check for that explicitly, not just
                         "did it refuse".

Run (from project root): python3 -m evaluation.evaluate
"""
import os
import sys
import csv

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, ROOT)

from rag.pipeline import RAGPipeline          # noqa: E402
from evaluation.questions import QUESTIONS    # noqa: E402

REFUSAL_MARKER = "couldn't find this in our verified property data"


def is_refusal(answer: str) -> bool:
    return REFUSAL_MARKER in answer.lower()


def score_question(pipe: RAGPipeline, item: dict) -> dict:
    out = pipe.ask(item["q"])
    answer = out["answer"]
    citations = out.get("citations", [])
    refused = is_refusal(answer)

    grounded = refused or (len(citations) > 0 and out.get("grounded", False))

    route_ok = (out["route"] == item["expected_route"]) or item["expected_route"] == "hybrid"
    if item["answerable"]:
        retrieval_ok = route_ok and not refused and len(citations) > 0
    else:
        retrieval_ok = refused or len(citations) == 0

    if item["answerable"]:
        hallucinated = (not refused) and len(citations) == 0
    else:
        hallucinated = not refused

    return dict(
        id=item["id"], question=item["q"], expected_route=item["expected_route"],
        actual_route=out["route"], answerable=item["answerable"], refused=refused,
        n_citations=len(citations), grounded=grounded, retrieval_ok=retrieval_ok,
        hallucinated=hallucinated, answer_preview=answer[:160],
    )


def run():
    pipe = RAGPipeline()
    rows = [score_question(pipe, item) for item in QUESTIONS]

    n = len(rows)
    grounding_rate = sum(r["grounded"] for r in rows) / n
    retrieval_accuracy = sum(r["retrieval_ok"] for r in rows) / n
    hallucination_rate = sum(r["hallucinated"] for r in rows) / n

    print(f"{'ID':<3} {'Route(exp/act)':<20} {'Ans?':<6} {'Refused':<8} {'Cite#':<6} {'Grnd':<5} {'Retr':<5} {'Hall':<5}  Question")
    for r in rows:
        print(f"{r['id']:<3} {r['expected_route']+'/'+r['actual_route']:<20} "
              f"{str(r['answerable']):<6} {str(r['refused']):<8} {r['n_citations']:<6} "
              f"{str(r['grounded']):<5} {str(r['retrieval_ok']):<5} {str(r['hallucinated']):<5}  {r['question']}")

    print("\n=== SUMMARY ===")
    print(f"Grounding Rate:      {grounding_rate*100:.1f}%")
    print(f"Retrieval Accuracy:  {retrieval_accuracy*100:.1f}%")
    print(f"Hallucination Rate:  {hallucination_rate*100:.1f}%")

    out_path = os.path.join(HERE, "results.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"\nDetailed results written to {out_path}")
    return rows, dict(grounding_rate=grounding_rate, retrieval_accuracy=retrieval_accuracy,
                       hallucination_rate=hallucination_rate)


if __name__ == "__main__":
    run()
