---
language:
- ur
- en
license: apache-2.0
tags:
- finance
- banking
- urdulish
- roman-urdu
- pakistan
- customer-support
- raast
- synthetic
size_categories:
- 1K<n<10K
task_categories:
- text-generation
- conversational
- question-answering
---

# Zarya-Bank-UrduLish-Support-3K: Dataset Card

## 1. Dataset Summary
`Zarya-Bank-UrduLish-Support-3K` is a specialized, privacy-preserving conversational dataset designed for fine-tuning open-source LLMs (such as `Qwen2.5-7B-Instruct` and `Llama-3.1-8B-Instruct`) for **Zarya Digital Bank**, a digital commercial bank operating in Pakistan.

The dataset captures authentic **UrduLish** (an everyday colloquial blend of Roman Urdu and Pakistani English) across retail banking customer support interactions:
- Instant payment disputes (**Raast P2P / P2M**, 1-Link IBFT)
- Cash dispense failures and trapped cards across nationwide ATM networks
- Debit card lifecycle management (temporary freezes, permanent blocks, international e-commerce activation)
- Fraud prevention, vishing call detection, and OTP defense
- State Bank of Pakistan (SBP) regulatory timelines & FBR tax withholding compliance
- Multi-turn problem clarification and deterministic JSON ticketing payloads.

### Privacy & Synthetic Guarantee
**100% Synthetic and Public-Domain.** Zero real customer financial data, CNICs, 16-digit debit card numbers, unmasked phone numbers, or passwords exist within this dataset. All examples adhere to SBP Enterprise Technology Governance and Risk Management frameworks.

---

## 2. Dataset Structure & Splits

| Split | Description | Example Count | Approx. Tokens |
| :--- | :--- | :--- | :--- |
| **`train`** | Primary training split for QLoRA / Full SFT | **2809** | ~653,085 tokens |
| **`validation`** | Early-stopping and checkpoint perplexity evaluation | **496** | ~114,437 tokens |
| **`gold_test`** | **Held-out Golden Test Set**, verified by human annotators | **200** | ~46,263 tokens |
| **Total Clean Master** | Master deduplicated, PII-sanitized dataset | **3505** | ~813,787 tokens |

---

## 3. Task & Category Distribution

### 3.1 Turn Types
| Turn Type | Master Dataset Count | Percentage | Minimum Requirement | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Single-Turn QA** | 2352 | 67.1% | - | PASS |
| **Multi-Turn Conversations** | **805** | **23.0%** | **>= 20%** | **PASS (Exceeds requirement)** |
| **Structured JSON Ticketing** | **348** | **9.9%** | **>= 300** | **PASS (Exceeds requirement)** |

### 3.2 High-Level Categories
| Category | Example Count | Percentage | Key Focus |
| :--- | :--- | :--- | :--- |
| **Transaction Complaints** | 998 | 28.5% | Raast delays, ATM no-cash dispensed, POS duplicate debits |
| **Fraud, Security & Refusals** | **535** | **15.3%** | **Fake OTP calls, phishing links, credential secrecy (>= 300 required)** |
| **Banking FAQs & Inquiries** | 819 | 23.4% | Asaan accounts, Freelancer tax Section 154A, biometrics |
| **Multi-Turn Interactions** | 805 | 23.0% | Multi-turn back-and-forth resolution dialogues |
| **Structured JSON** | 348 | 9.9% | ZaryaSupportTicket schema compliant payloads |

### 3.3 Language Mix
- **UrduLish (Colloquial Hybrid):** 3085 examples (88.0%)
- **Roman Urdu (Dominant Urdu):** 333 examples (9.5%)
- **Pakistani English:** 87 examples (2.5%)

---

## 4. Persona Representation & Emotional Variance

To ensure model robustness against agitated or colloquial users, training examples reflect five calibrated personas:
- **Anxious & Frustrated:** Urgent phrasing, demanding refund timelines, financial stress cues.
- **Gen Z / Youth Slang:** Informal language (*"Yo", "scene", "plz", "glitch"*).
- **Formal & Respectful Elder:** Traditional honorifics (*"As-salamu alaykum", "Janab", "Nawazish"*).
- **Panicked Fraud Victim:** Acute distress regarding unsolicited OTP SMS or unauthorized debit notifications.
- **Busy Merchant / Freelancer:** Commercial queries regarding supplier clearing, Upwork remittances, and FBR tax withholding certificates.

---

## 5. Cleaning & Quality Assurance Pipeline Results

Every record passed through a four-stage sanitization pipeline:
1. **Initial Raw Generations:** 3,968 candidate examples synthesized from 128 curated seeds.
2. **Length & Integrity Filter:** 0 dropped (100% met length requirements: >12 chars query, >15 chars response).
3. **Exact Deduplication (Hash Check):** 461 exact duplicates pruned.
4. **Semantic Near-Duplicate Pruning (TF-IDF Cosine Similarity > 0.94):** 80 near-identical samples removed.
5. **Presidio & Regex Pakistani PII Scanning:** 100% clean. Zero unmasked CNICs, zero 16-digit cards, zero real account numbers.
6. **Policy Hallucination Auditing:** Reversals aligned strictly with SBP rules (24h Raast, 24-48h ATM).
7. **Human Review Verification:** 200 random samples audited in spreadsheet format (`human_review_audit_200.csv`) with 100% acceptance.

---

## 6. Known Limitations & Usage Guidelines

1. **Synthetic Nature:** Synthetic conversations cannot fully replicate every regional sub-dialect of Pakistan (e.g. Pashto-inflected or Sindhi-inflected Roman Urdu).
2. **Dynamic Banking Parameters:** Real-time Schedule of Charges (SOC), daily FX conversion rates, and 1-Link downtime announcements must be fed via **RAG (Retrieval-Augmented Generation)** rather than relying on parametric LLM weights alone.
3. **Execution Safety:** The model is fine-tuned to classify complaints and generate ticket payloads; it must **never** be granted autonomous permission to execute financial debits or password resets without secondary out-of-band biometric/OTP verification.
