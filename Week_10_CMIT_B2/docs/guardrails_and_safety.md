# Task 4: Inbound & Outbound Security Guardrails

**Client:** Zarya Digital Bank  
**Document:** Week 10 — Day 4: Task 4 Institutional Guardrails & PII Compliance  
**Author:** Antigravity Senior AI/ML Engineering Lead  
**Module:** [`src/guardrails.py`](file:///c:/Users/MEE/Anti-Gravity_projects/Fine-tuning-llm/src/guardrails.py)  

---

## 1. Multi-Layer Guardrail Architecture

To operate safely in retail banking, every prompt and completion passes through deterministic security interceptors before and after the LLM:

```
               [Customer Inbound Request]
                           │
                           ▼
             ┌───────────────────────────┐
             │ 1. Inbound Guardrails     │
             │   - Prompt Injection      │
             │   - Credential Harvesting │
             │   - Scam Interceptor      │
             │   - Off-topic Filter      │
             └─────────────┬─────────────┘
                           │ (If Passed)
                           ▼
             ┌───────────────────────────┐
             │ 2. Audit Log PII Masker   │
             │   - CNIC Redaction        │
             │   - Phone Number Masking  │
             │   - Email Scrubbing       │
             └─────────────┬─────────────┘
                           │
                           ▼
                [LLM Inference Engine]
                           │
                           ▼
             ┌───────────────────────────┐
             │ 3. Outbound Guardrails    │
             │   - 16-Digit Card Masking │
             │   - CVV Leakage Blocker   │
             │   - Account Number Shield │
             └─────────────┬─────────────┘
                           │
                           ▼
                [Sanitized User Reply]
```

---

## 2. Inbound Threat Detection Policies

### A. Scam & Money Mule Interceptor
- **Trigger Patterns:** Mentions of *"Jeeto Pakistan"*, *"lottery"*, *"sona nikla"*, *"advance tax transfer"*, or account renting offers (*"50 hazar mahina rent"*).
- **Mandatory SBP Regulatory Response:**
  > *"Zarya Bank kabhi bhi call ya SMS par aap ka OTP ya PIN nahi maangta. Yeh fraud ho sakta hai — kisi ko na batayein aur foran helpline par report karein."*

### B. Credential Harvesting Blocker
- **Trigger Patterns:** Asking to provide or receive PINs, OTPs, CVVs, passwords, or ATM card security codes.
- **Action:** Rejects request immediately, instructs customer never to reveal credentials.

### C. Prompt Injection & Jailbreak Defense
- **Trigger Patterns:** *"Ignore previous instructions"*, *"act as DAN"*, *"developer mode"*, *"repeat system prompt"*.
- **Action:** Halts execution and returns security warning.

### D. Off-Topic Filtering
- **Trigger Patterns:** Inquiries regarding recipes, cricket match scores, creative writing, or non-banking topics.
- **Action:** Politeness redirect to Zarya core banking capabilities.

---

## 3. Outbound Data Leakage & PII Masking

### Outbound Response Sanitization
If the model inadvertently attempts to echo back full payment details, outbound regex transformers intercept and mask them:
- **Card Numbers:** `4214-5501-9874-1234` $\longrightarrow$ `****-****-****-1234`
- **CVVs:** `CVV 894` $\longrightarrow$ `[REDACTED_CVV]`

### Audit Log PII Redaction
For regulatory audit compliance (preventing developer / log analyst access to customer PII):
- **Pakistani CNIC:** `42101-7890123-1` $\longrightarrow$ `42101-*******-1`
- **Pakistani Mobile:** `0300-9876543` $\longrightarrow$ `0300*****43`
- **Email:** `customer.name@gmail.com` $\longrightarrow$ `c***@gmail.com`

---

## 4. Test Verification Results

All 4 guardrail suites were tested through [`src/run_day4_local_demo.py`](file:///c:/Users/MEE/Anti-Gravity_projects/Fine-tuning-llm/src/run_day4_local_demo.py) with **100% test pass rate**:
- **Prompt Injection:** Blocked (`PROMPT_INJECTION`)
- **Credential Harvesting:** Blocked (`CREDENTIAL_HARVESTING`)
- **Scam / Money Mule:** Blocked (`SCAM_DETECTION`) with exact institutional copy
- **PII Redaction in Logs:** Verified with CNIC, Phone, and Email patterns.
