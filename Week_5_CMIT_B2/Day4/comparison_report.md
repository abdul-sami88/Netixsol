# Comparison Report: Sequential vs. Hierarchical vs. Single-Agent

**Task:** Research a competitor ("TechNova"), summarize findings into insights, and draft a marketing angle that differentiates our product.
**Frameworks compared:** CrewAI `Process.sequential`, CrewAI `Process.hierarchical`, and a Day-3-style single-agent LangGraph pipeline (plan → retrieve → generate → critique → format).

---

## 1. Setup recap

Three role-scoped agents were used in both CrewAI runs:

| Agent | Responsibility | Tool |
| --- | --- | --- |
| Competitive Researcher | Pull raw competitor facts | `company_lookup` |
| Insights Analyst | Turn facts into ranked, numbered insights | `calculator` |
| Marketing Strategist | Draft one on-brand marketing angle | `brand_voice_guidelines` |

- **Sequential** — tasks pre-assigned to agents, fixed order, `context=[...]` wires each task's output into the next.
- **Hierarchical** — same agents/tools, but tasks are unassigned and a manager agent (`manager_llm`) decides delegation order and reviews sub-agent work.

## 2. Results, from the actual executed run in the notebook

| Metric | Sequential | Hierarchical |
| --- | --- | --- |
| Total tokens | 11,220 | 81,184 |
| Prompt tokens | 10,005 | 69,776 |
| Completion tokens | 1,215 | 11,408 |
| Successful requests | 21 | 100 |
| Est. cost (~$0.30/1M in, ~$2.50/1M out) | **$0.00604** | **$0.04945** |

Hierarchical used **~7x the tokens and ~8x the cost** of sequential for the identical task — almost entirely from the manager's extra planning, delegation, and review calls (100 requests vs. 21).

### Final outputs produced

**Sequential:**
> TechNova just handed small businesses a reason to leave. By hiking their average prices to $1,200 last quarter, they abandoned the budget-conscious operators who built them. We offer a smarter alternative at $650, slipping right into the gap they left wide open.

**Hierarchical:**
> TechNova just handed their small-business customers an 8% price hike last quarter. That greed opened a massive door for us. While they sit fat and happy at a $1,200 average price, we offer the exact same power for $650. Pocket the $550 difference and get back to work.

### Manual scoring (1 = fails, 3 = fully meets)

| Run | Factual grounding | Completeness | Tone |
| --- | --- | --- | --- |
| Sequential | 3 — cites $1,200 and $650 | 2 — pricing only, never surfaces the 9.5-point market-share gap | 3 — short sentences, concrete numbers, no banned jargon |
| Hierarchical | 3 — also cites the computed $550 gap | 2 — same gap: market share never makes it into the final copy | 3 — on-tone, "sit fat and happy" leans further into "irreverent" |

Note: only one run per process was actually executed and captured, so this is n=1 per variant rather than a 3-run sample — treat these as a directional read, not a statistically robust comparison. Both runs share the same real completeness gap: the analyst's insights included the market-share number, but neither Strategist output used it, which points at `marketing_task.expected_output` needing to explicitly require both metrics.

## 3. Sequential vs. hierarchical — pros, cons, when to use each

| | Sequential | Hierarchical |
| --- | --- | --- |
| **Quality** | Consistent — pipeline order is fixed and matches the task's natural dependency chain | Can be *higher* if the manager catches and re-delegates a bad output, but can also be *lower* if it mis-routes or skips a step |
| **Latency / cost** | Low — exactly 3 agent calls, no manager overhead | High — manager planning/review calls stack on top of the 3 worker calls (measured ~8x cost here) |
| **Reliability** | High — same 3 steps every run, easy to debug | Lower — delegation order isn't guaranteed, and a manager mistake compounds downstream |
| **Best fit** | Known, fixed pipeline shape (research → analyze → write) | Task assignment genuinely depends on intermediate results a fixed pipeline can't anticipate |

For *this* task — a completely predictable research → analyze → write pipeline — sequential is the better fit. Hierarchical's manager overhead bought no measurable quality gain here (both runs shared the same completeness gap) while costing ~8x more.

## 4. Where multi-agent CrewAI vs. a single-agent LangGraph pipeline stands

Day 3's single-agent LangGraph workflow (plan → retrieve → generate → critique → format, no separate agents) used the fewest total LLM calls of all three approaches for a comparably-scoped task, since there's no manager and no cross-agent handoff overhead. The cost of "more agents" is close to linear in CrewAI, not free.

The sequential crew's quality edge over a naive single generalist call came specifically from **role separation** — a dedicated "compute the real numbers" step for the Analyst catches arithmetic a generalist agent would otherwise eyeball — not from multi-agent-ness per se. A single well-designed LangGraph agent using the same three tools with explicit state (plan → retrieve → compute → draft) could likely match sequential CrewAI's quality at lower token cost, since it avoids CrewAI's per-agent system-prompt overhead.

## 5. Bottom line

For this specific task:

- **Sequential CrewAI** was worth the added complexity over a single generalist call — role separation produced more clearly grounded output, at low token cost ($0.006/run).
- **Hierarchical CrewAI** added cost (~8x) and unpredictability without a clear quality win — this task's structure was never ambiguous enough to need a manager deciding it at runtime.
- **A single-agent LangGraph pipeline** is likely the strongest cost/quality trade-off overall, since it can capture the same role-separation benefit (explicit plan → retrieve → compute → draft stages) without CrewAI's per-agent and per-manager prompt overhead.
