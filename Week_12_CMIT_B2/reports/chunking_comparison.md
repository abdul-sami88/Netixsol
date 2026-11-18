# Legal-Aware Chunking Comparison

Comparison across 10 Pakistani statutes, 200 Supreme Court judgments, 50 contracts, and 30 Urdu/scanned documents.

| strategy                                 |   chunk_count |   avg_words |   max_words |   oversized_gt_500w |   boundary_break_pct |   bm25_hit_at_5 |   bm25_mrr_at_5 |
|:-----------------------------------------|--------------:|------------:|------------:|--------------------:|---------------------:|----------------:|----------------:|
| Fixed-Size (220w, 35w overlap)           |          7929 |       216.5 |         220 |                   0 |                 96.3 |               1 |               1 |
| Section-Level (1 Section/Clause)         |          5508 |       263.1 |       38088 |                 243 |                  0   |               1 |               1 |
| Parent-Child (140w child -> full parent) |         15257 |       110.5 |         160 |                   0 |                  0   |               1 |               1 |

## Key Findings
- **Fixed-Size:** Predictable chunk lengths, but splits mid-section and mid-clause (high boundary break rate), losing legal provenance.
- **Section-Level:** Preserves exact legal boundaries (`Act -> Section`, `Contract -> Clause`), but long statutory sections/pages create oversized chunks (`> 500` words) that dilute dense embedding similarity.
- **Parent-Child (Selected for Indexing):** Combines tight 140-word child vectors/BM25 entries for pinpoint retrieval with full-section `parent_id` lookup so the LLM receives complete statutory/contractual context.