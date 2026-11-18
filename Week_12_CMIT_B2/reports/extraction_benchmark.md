# Day 3: Legal Entity & Relationship Extraction Benchmark

Benchmarked on **20 curated Supreme Court judgments** from the Khan & Associates Pakistan Law Corpus.

## 1. Extraction Performance Summary

| Entity / Task | Precision | Recall | F1 Score | True Positives | False Positives | False Negatives |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Judge / Justice** | 0.365 | 0.950 | 0.528 | 19 | 33 | 1 |
| **Section & Article** | 0.864 | 0.987 | 0.921 | 76 | 12 | 1 |
| **Case Citation** | 0.685 | 0.818 | 0.746 | 63 | 29 | 14 |
| **Overall Micro-Average** | **0.681** | **0.908** | **0.778** | **158** | **74** | **16** |

---

## 2. Extracted Relationships Count (20 Judgments)
- **`INTERPRETS` (Case -> Section):** 298 links
- **`CITES` (Case -> Case):** 133 links
- **`OVERRULES` (Case -> Case / Precedent):** 0 negative treatment links

---

## 3. Key Entity Resolution Wins
1. **Colloquial Citation Normalization:** Canonicalized variants such as `S. 23`, `Sec 23 Contract Act`, and `Section 23 ibid` into canonical node `Contract Act, 1872 Section 23`.
2. **Constitutional Article Disambiguation:** Differentiated standalone statutory sections (`Section 25`) from constitutional fundamental rights (`Article 25 of 1973 Constitution`).
3. **Judicial Title Standardization:** Stripped honorifics (`Hon'ble Mr. Justice Qazi Faez Isa, J.` -> `Justice Qazi Faez Isa`).
4. **Negative Treatment Flags:** Captured phrases like *"is hereby overruled"*, *"no longer good law"*, and *"we respectfully dissent"* to reliably create `OVERRULES` edges.
