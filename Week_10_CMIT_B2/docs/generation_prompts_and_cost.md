# Synthetic Data Generation: Prompts, Architecture & Cost Analysis

**Target Institution:** Zarya Digital Bank  
**Dataset Goal:** 3,000+ Curated UrduLish Banking Training Examples  
**Document Version:** 1.0.0  

---

## 1. Teacher LLM Generation Methodology

To ensure maximum linguistic diversity, emotional variance, and strict policy grounding, data generation followed a **Seed-Conditioned Multi-Agent Expansion** pipeline:

1. **Curated Seed Ingestion (128 Seeds):** Banking domain experts created 128 foundational ground-truth dialogues covering Raast transfers, 1-Link ATM faults, Card security, Fraud/Vishing, General FAQs, Multi-turn problem resolutions, and Structured JSON ticketing tasks.
2. **Context & Persona Conditioning:** Every generation run was conditioned on 5 distinct consumer personas:
   - *Anxious / Frustrated:* High emotional urgency, demanding immediate resolution, mentions of financial distress.
   - *Gen Z Youth / Student:* Informal greetings (*"Yo", "Bro", "Aoa"*), modern tech terms, abbreviations (*"plz", "glitch"*).
   - *Formal / Respectful Elder:* Traditional polite phrasing (*"As-salamu alaykum", "Janab", "Nawazish hogi"*).
   - *Panicked Fraud Victim:* Acute panic regarding stolen OTPs or unauthorized debit notifications.
   - *Busy Merchant / Freelancer:* Commercial urgency regarding suppliers, foreign remittances, and FBR tax withholding.
3. **Phonetic & Typo Emulation Engine:** Real-world Roman Urdu lacks standardized orthography. The engine injected controlled phonetic substitutions (*pese/paise*, *nhi/nahi*, *kat gye/cut gaye*, *krdo/karo*) to simulate natural mobile keyboard input.

---

## 2. Teacher Prompt Templates

### 2.1 Multi-Turn Dialogue Expansion Prompt
```text
[SYSTEM]
You are a senior banking conversational architect specializing in Pakistani digital banking (UrduLish / Roman Urdu).
Your task is to take a foundational seed dialogue between a Zarya Digital Bank customer and customer support, and synthesize a realistic, high-fidelity multi-turn conversation (2 to 4 turns).

Guidelines:
1. Target Persona: {persona} (reflect authentic emotional state, vocabulary, and pacing).
2. Setting: Customer is reaching out regarding {category} - {sub_category}.
3. Tone & Banking Rules:
   - Bank assistant must ALWAYS use polite pronouns ("Aap", "Ji"), express immediate empathy ("Maazrat chahtay hain"), and adhere to State Bank of Pakistan (SBP) timelines:
     * Failed Raast / IBFT transfers: 24 working hours auto-reversal SLA.
     * ATM cash dispense failure: 24-48 working hours 1-Link reconciliation SLA.
     * Debit card compromised: Immediate permanent freeze.
     * Fraud calls / OTP solicitation: HARD REFUSAL, remind that bank staff NEVER asks for OTP/CVV.
4. Language: Colloquial UrduLish (mix of Roman Urdu and Pakistani banking English loanwords). Emulate realistic mobile typing patterns.
5. Format: Strict Qwen2.5 ChatML format.

[SEED DIALOGUE]
User: {seed_user}
Assistant: {seed_assistant}

[OUTPUT FORMAT]
<|im_start|>system
...
<|im_end|>
<|im_start|>user
...
<|im_end|>
<|im_start|>assistant
...
<|im_end|>
```

### 2.2 Structured JSON Ticket Generation Prompt
```text
[SYSTEM]
You are Zarya Digital Bank's automated complaint triage engine.
Given a customer's raw conversational complaint in UrduLish, extract structured metadata and output a valid JSON document conforming to the ZaryaSupportTicket JSON Schema.

Schema Constraints:
- intent: Must be one of [TRANSACTION_FAILED_DISPUTE, ATM_CASH_DISPENSE_FAILURE, CARD_BLOCK_REQUEST, CARD_UNBLOCK_REQUEST, FRAUD_ALERT_REPORT, ACCOUNT_STATEMENT_INQUIRY, RAAST_ID_MANAGEMENT, FEE_TAX_DISPUTE, GENERAL_BANKING_FAQ, SECURITY_REFUSAL_ESCALATION]
- urgency: LOW | MEDIUM | HIGH | CRITICAL
- sentiment: CALM | ANXIOUS | FRUSTRATED | ANGRY
- extracted_entities: { channel, amount_pkr, reference_id, atm_location, phone_number_masked }
- recommended_action: AUTO_REVERSAL_QUEUE_24H | IMMEDIATE_CARD_FREEZE | ESCALATE_TO_FRAUD_OPS | SEND_ACCOUNT_STATEMENT | RESOLVED_INFORMATIONAL
- customer_facing_response: Empathetic, polite UrduLish response.

[INPUT]
Customer Complaint: "{user_complaint}"

[OUTPUT]
Provide ONLY raw JSON without markdown codeblock wrappers.
```

---

## 3. Token Economics & Cost Calculation

Generation of the complete dataset (3,252 raw examples) is analyzed across frontier commercial APIs and self-hosted open-source teacher architectures:

### 3.1 Token Consumption Profile
| Parameter | Average per Example | Dataset Total (3,252 Examples) |
| :--- | :--- | :--- |
| **Input Tokens (Prompt + Few-shot Seeds)** | ~140 tokens (amortized across batch) | ~455,280 tokens |
| **Output Tokens (Dialogue / JSON Payload)** | ~220 tokens | ~715,440 tokens |
| **Total Tokens** | **~360 tokens** | **~1,170,720 tokens (~1.17M tokens)** |

### 3.2 Cost Comparison Across Teacher Models

| Model Provider | Input Price / 1M Tokens | Output Price / 1M Tokens | Total Cost (USD) | Total Cost (PKR @ 280) |
| :--- | :--- | :--- | :--- | :--- |
| **OpenAI GPT-4o (`gpt-4o-2024-08-06`)** | $2.50 | $10.00 | **$8.29** | **PKR 2,321** |
| **Anthropic Claude 3.5 Sonnet** | $3.00 | $15.00 | **$12.10** | **PKR 3,388** |
| **OpenAI GPT-4o-mini** | $0.15 | $0.60 | **$0.50** | **PKR 140** |
| **Self-Hosted Qwen2.5-72B-Instruct (vLLM on 2x A100)** | N/A (Cloud rental ~$2.60/hr) | N/A (~45 min runtime) | **$1.95** | **PKR 546** |

### 3.3 Key Takeaway
High-quality synthetic dataset generation of 3,200+ nuanced UrduLish banking examples is remarkably cost-effective. Even with top-tier teacher models (GPT-4o), total data generation cost is **under $10 USD (PKR 2,500)**, demonstrating extraordinary ROI compared to traditional human annotation workflows (which would take weeks and cost thousands of dollars).
