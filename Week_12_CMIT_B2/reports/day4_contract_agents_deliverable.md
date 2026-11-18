# Day 4 Capstone Deliverable: Contract Review, Comparison & Drafting Agents

**Client:** Khan & Associates (Pakistani Law Firm)  
**Scenario:** A client sends a 60-page agreement at 6:00 pm needing comments by morning. We deploy autonomous agents to review against the firm playbook, compare redlines, and draft responses so the lawyer only has to approve.

---

## 1. Executive Summary of Deliverables

| Deliverable | File Path | Format | Status & Highlights |
| :--- | :--- | :---: | :--- |
| **Playbook Review Report** | [outputs/contract_review_report.docx](file:///c:/Users/MEE/Anti-Gravity_projects/AI_Legal_assistant/outputs/contract_review_report.docx) | `.docx` | Formatted Word document with executive summary, missing clauses, risk badges (:white_check_mark:, :warning:, :x:), reviewer notes & suggested redlines. |
| **Contract Redline & Diff** | [outputs/contract_comparison_diff.json](file:///c:/Users/MEE/Anti-Gravity_projects/AI_Legal_assistant/outputs/contract_comparison_diff.json)<br>[reports/contract_comparison_report.md](file:///c:/Users/MEE/Anti-Gravity_projects/AI_Legal_assistant/reports/contract_comparison_report.md) | `.json` / `.md` | Full token & clause-level diff with plain-language legal impact analysis for each change. |
| **Drafted Case Brief** | [outputs/drafted_case_brief.md](file:///c:/Users/MEE/Anti-Gravity_projects/AI_Legal_assistant/outputs/drafted_case_brief.md) | `.md` | Full brief on *2021 SCMR 105* (5-Judge Full Bench), stamped **"DRAFT — for lawyer review"**. |
| **Drafted Legal Notice** | [outputs/drafted_legal_notice.md](file:///c:/Users/MEE/Anti-Gravity_projects/AI_Legal_assistant/outputs/drafted_legal_notice.md) | `.md` | Formal Advocate's notice under Contract Act Sections 73-74 & CPC, stamped **"DRAFT — for lawyer review"**. |
| **Drafted Contract Clauses** | [outputs/drafted_contract_clauses.md](file:///c:/Users/MEE/Anti-Gravity_projects/AI_Legal_assistant/outputs/drafted_contract_clauses.md) | `.md` | Bespoke Pakistani clauses (Arbitration, Indemnity, Liquidated Damages) with statutory annotations, stamped **"DRAFT — for lawyer review"**. |
| **Clause Classification Benchmark** | [reports/clause_classification_comparison.md](file:///c:/Users/MEE/Anti-Gravity_projects/AI_Legal_assistant/reports/clause_classification_comparison.md)<br>[outputs/clause_classification_benchmark.csv](file:///c:/Users/MEE/Anti-Gravity_projects/AI_Legal_assistant/outputs/clause_classification_benchmark.csv) | `.md` / `.csv` | CUAD taxonomy benchmark: LLM (Macro F1: 0.754) vs Fine-Tuned Legal Model (Macro F1: 0.624, 5x faster). |
| **Long-Context vs RAG Benchmark** | [reports/long_context_vs_rag.md](file:///c:/Users/MEE/Anti-Gravity_projects/AI_Legal_assistant/reports/long_context_vs_rag.md)<br>[outputs/long_context_vs_rag.csv](file:///c:/Users/MEE/Anti-Gravity_projects/AI_Legal_assistant/outputs/long_context_vs_rag.csv) | `.md` / `.csv` | 10-contract benchmark: Long-context achieves 92.8% accuracy (zero boundary cuts) while RAG offers 10x faster speed and 94% cost savings. |

---

## 2. Task 1: Clause Classification (CUAD Taxonomy Benchmark)

Tested over **256 test clauses** from commercial agreements and Pakistani-law contracts across 9 CUAD categories:
- **LLM Zero-Shot Classifier:** Macro F1 **0.7535**, Micro F1 **0.8398**. Excels on complex, multi-sentence clauses and ambiguous boilerplate.
- **Small Fine-Tuned Legal Model:** Macro F1 **0.6244**, Micro F1 **0.7734**. Achieves **95.8% F1 on Indemnification** and **94.9% F1 on Governing Law**, running locally on CPU in **0.54s** (~5x faster) with zero data leaving the firm.

---

## 3. Task 2: Playbook Risk Review & Word (.docx) Export

The Playbook Review Agent evaluated incoming agreements against the **Khan & Associates Playbook** (`data/firm_playbook.json`):
- **Risk Badges:** Each clause is categorized as ✅ Approved, ⚠️ Medium Risk, or ❌ High Risk.
- **Missing Clause Detection:** Proactively flags missing protections (e.g. Missing Data Protection, Missing Force Majeure, Missing Severability).
- **Redline Suggestions:** Generates fallback wording compliant with Pakistani statutes (Arbitration Act 1940, Section 23/74 Contract Act).
- **Word Export (`outputs/contract_review_report.docx`):** Fully styled .docx document featuring executive tables, colored callout boxes, and reviewer redline notes.

---

## 4. Task 3: Contract Comparison & Plain-Language Legal Impact

Compares Version 1 (Client Standard) against Version 2 (Counterparty Aggressive Markup):
1. **Governing Law:** Counterparty substituted Pakistani law with Delaware state courts.
   - *Plain-Language Impact:* Escalates litigation expenses and forces client to hire foreign US counsel.
2. **Limitation of Liability:** Slashing Vendor liability to 1 month while leaving Client liability uncapped.
   - *Plain-Language Impact:* Client faces unlimited exposure for consequential damages, while counterparty holds zero financial skin in the game.
3. **Payment & Interest:** Imposing 3% monthly compound interest (42.6% APR).
   - *Plain-Language Impact:* Unlawful penalty clause under Section 74 of the Contract Act, 1872.

---

## 5. Task 4: Autonomous Drafting Agent

Produced three instruments, each stamped with the mandatory watermark:
> ⚠️ **DRAFT — FOR LAWYER REVIEW ONLY**  
> *This document has been generated by the AI Legal Assistant for Khan & Associates. It does not constitute final legal advice or a binding instrument and must be reviewed, verified, and approved by a licensed Advocate of the High Court / Supreme Court of Pakistan prior to issuance or execution.*

1. **Case Brief:** [outputs/drafted_case_brief.md](file:///c:/Users/MEE/Anti-Gravity_projects/AI_Legal_assistant/outputs/drafted_case_brief.md) (*2021 SCMR 105*).
2. **Legal Notice:** [outputs/drafted_legal_notice.md](file:///c:/Users/MEE/Anti-Gravity_projects/AI_Legal_assistant/outputs/drafted_legal_notice.md) (Under Section 73-74 Contract Act).
3. **Contract Clauses:** [outputs/drafted_contract_clauses.md](file:///c:/Users/MEE/Anti-Gravity_projects/AI_Legal_assistant/outputs/drafted_contract_clauses.md) (Arbitration, Indemnification, Liquidated Damages).

---

## 6. Task 5: Long-Context vs. RAG Benchmark on 10 Contracts

| Metric | Long-Context Window | RAG Architecture | Recommendation |
| :--- | :---: | :---: | :--- |
| **Accuracy** | **92.8%** | 84.4% | Use Long-Context for high-stakes 60-page M&A closings |
| **Missed Clauses** | **2 total** | 13 total | Long-context avoids chunk boundary slicing errors |
| **Latency** | 13.16s | **1.38s** | RAG is ~10x faster for interactive attorney inquiries |
| **Cost / 1k Contracts** | \$16.89 | **\$0.90** | RAG saves **94% in operational inference cost** |
"""
    with open("reports/day4_contract_agents_deliverable.md", "w", encoding="utf-8") as f:
        f.write(Content)
    print("Consolidated Day 4 deliverable written to reports/day4_contract_agents_deliverable.md")


if __name__ == "__main__":
    pass

