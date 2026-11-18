"""Generate and verify the 5 demo answers for Day 2 Deliverable:
1. Lawyer Scenario: 'Agar consideration unlawful ho to kya contract void hai?' (Contract Act 1872, Sec 23)
2. Criminal Law Statute: 'What is the punishment for qatl-i-amd under Section 302 PPC?' (PPC 1860, Sec 302)
3. Constitutional Law: 'What does Article 25 of the Constitution say about equality of citizens?' (Constitution 1973, Art 25)
4. Supreme Court Judgment: 'What did the Supreme Court hold regarding sudden provocation in criminal petition cases?' (Supreme Court case law)
5. Out-of-Corpus Unanswerable: 'Under California Civil Code, what is the statute of limitations for breach of an oral contract?' ('No sufficient source found')
"""

import json
from pathlib import Path
from rag_pipeline import LegalRAGPipeline
from verify_citations import CitationVerifier


OUT_JSON = Path("outputs/demo_5_verified_answers.json")
OUT_MD = Path("reports/demo_5_verified_answers.md")


DEMO_QUERIES = [
    {
        "id": "demo_01",
        "title": "Scenario 1: Lawyer Contract Question (Roman Urdu)",
        "query": "Agar consideration unlawful ho to kya contract void hai?",
        "expected_act": "Contract Act, 1872",
        "expected_sec": "23",
    },
    {
        "id": "demo_02",
        "title": "Scenario 2: Criminal Law Murder & Qisas (PPC)",
        "query": "What is the punishment for qatl-i-amd under Section 302 PPC?",
        "expected_act": "Pakistan Penal Code, 1860",
        "expected_sec": "302",
    },
    {
        "id": "demo_03",
        "title": "Scenario 3: Constitutional Fundamental Rights",
        "query": "What does Article 25 of the Constitution say about equality of citizens?",
        "expected_act": "Constitution of the Islamic Republic of Pakistan, 1973",
        "expected_sec": "25",
    },
    {
        "id": "demo_04",
        "title": "Scenario 4: Supreme Court Case-Law Judgment",
        "query": "What was held by the Supreme Court in criminal cases regarding sudden provocation and sentence reduction?",
        "expected_court": "Supreme Court of Pakistan",
    },
    {
        "id": "demo_05",
        "title": "Scenario 5: Out-of-Corpus Foreign Law (Unanswerable Guardrail)",
        "query": "Under California Civil Code, what is the statute of limitations for breach of an oral contract?",
        "expected_refusal": True,
    },
]


def main():
    print("Initializing Legal RAG Pipeline and Citation Verifier...")
    rag = LegalRAGPipeline()
    verifier = CitationVerifier()

    demo_results = []
    print("\nProcessing 5 Demo Questions...")

    for spec in DEMO_QUERIES:
        q = spec["query"]
        print(f"\n[{spec['id']}] Query: {q}")
        ans = rag.generate_cited_answer(q)
        ver_res = verifier.verify(ans)
        combined = {
            "id": spec["id"],
            "title": spec["title"],
            "query": q,
            "answer": ans,
            "verification": ver_res,
        }
        demo_results.append(combined)

        print(f"  Short Answer: {ans.get('short_answer')}")
        print(f"  Citation: {ans.get('citation')}")
        print(f"  Status: {ver_res['status']} (Fabrications: {len(ver_res['fabricated_elements'])})")

    # Save JSON output
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(demo_results, ensure_ascii=False, indent=2), encoding="utf-8")

    # Format Markdown Deliverable
    md_lines = [
        "# Day 2: Demo of 5 Citation-Grounded Verified Legal Answers",
        "",
        "This deliverable demonstrates 5 end-to-end legal answers produced by our Advanced RAG pipeline, covering Roman Urdu statutory inquiry, criminal statute penalties, constitutional equality, Supreme Court judgment reasoning, and an out-of-corpus foreign jurisdiction refusal.",
        "",
        "**Target Verification Metric:** 0 Fabricated Citations (100% Citation Grounding).",
        "",
    ]

    for item in demo_results:
        ans = item["answer"]
        ver = item["verification"]
        cit = ans.get("citation") or {}

        cit_str = "None (Refusal)"
        if cit.get("act") and cit.get("section"):
            cit_str = f"**{cit['act']}**, Section {cit['section']}"
        elif cit.get("court"):
            cit_str = f"**{cit['court']}**"

        quote_str = f"> \"{ans.get('quoted_source')}\"" if ans.get("quoted_source") else "*None (Question is unanswerable from corpus)*"

        status_badge = "✅ **VERIFIED**" if "VERIFIED" in ver["status"] else "❌ **FLAGGED**"

        md_lines.extend([
            f"---",
            f"### {item['title']}",
            f"- **Question:** *\"{item['query']}\"*",
            f"- **Verification Status:** {status_badge} (`{ver['status']}`)",
            f"- **Exact Citation:** {cit_str}",
            f"- **Short Answer:** {ans.get('short_answer')}",
            f"- **Legal Explanation:** {ans.get('explanation')}",
            f"- **Verbatim Quoted Source Text:**",
            quote_str,
            f"- **Fabricated Citations Detected:** `{len(ver['fabricated_elements'])}`",
            "",
        ])

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"\nSaved demo answers to {OUT_JSON} and {OUT_MD}")


if __name__ == "__main__":
    main()
