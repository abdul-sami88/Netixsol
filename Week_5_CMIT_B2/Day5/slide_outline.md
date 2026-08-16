# Slide Outline — Freelance Client Intake & Proposal Agent
*(5–7 minute stakeholder walkthrough)*

**Slide 1 — The Problem (45s)**
- Inbound leads/questions/spam all land in one inbox
- Response time and quote consistency vary by whoever picks it up
- Goal: automate first response, keep pricing decisions human-owned

**Slide 2 — What We Built (45s)**
- A LangGraph agent that classifies every inbound message and:
  - Drafts priced proposals for genuine leads
  - Answers existing-client status questions
  - Auto-archives spam
  - Rejects malicious/invalid input
- Wrapped behind a FastAPI service with structured logging

**Slide 3 — Architecture (1 min)**
- [Show the diagram: classify → 4 branches → human checkpoint → dispatch]
- Local rate card (file) + live currency API (real external tool)
- Human approval gate before any priced quote goes out

**Slide 4 — Why LangGraph (45s)**
- Fixed decision tree, not open-ended multi-agent collaboration → CrewAI not needed
- Native support for pausing execution for human approval and resuming later from persisted state
- A raw loop would mean re-building persistence and routing by hand

**Slide 5 — It Handles Failure Gracefully (1 min)**
- Bad/empty input → rejected before wasting a model call
- Prompt injection → caught by a filter before it ever reaches the LLM
- Currency API down → falls back to a static rate table, proposal still goes out
- No LLM key/outage → deterministic templates keep the system running

**Slide 6 — Evaluation Results (1 min)**
- 10 test cases incl. 2 adversarial + 2 edge cases
- 100% task success, 100% safety pass rate, 5.0/5 tone quality (after one fix)
- Found and fixed a real bug: fallback classifier misrouted a consulting lead as spam

**Slide 7 — What's Next (45s)**
- Persistent checkpointer + paid FX provider before production traffic
- API auth/rate limiting
- Weekly re-evaluation cadence to catch model/prompt drift
- Keep the human approval gate — consider a second threshold-based gate as volume grows

**Slide 8 — Questions**
