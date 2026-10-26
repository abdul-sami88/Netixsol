---
language:
- ur
- en
license: apache-2.0
tags:
- retail-banking
- urdulish
- qwen2.5
- lora
- dpo
- text-generation
- finance
datasets:
- zarya-banking-master-2500
- zarya-dpo-preference-500
base_model: Qwen/Qwen2.5-3B-Instruct
pipeline_tag: text-generation
---

# Model Card: Zarya-Qwen2.5-3B-UrduLish-Banking (v1.0.0)

**Organization:** Zarya Digital Bank (Pakistan)  
**Developed by:** AI/ML Sovereign Engineering Team  
**Model Type:** Autoregressive Instruction-Tuned & DPO Aligned Decoder-Only Language Model  
**Base Architecture:** `Qwen/Qwen2.5-3B-Instruct`  
**License:** Apache 2.0  
**Release Date:** October 2026  

---

## 1. Model Description

`Zarya-Qwen2.5-3B-UrduLish-Banking` is a specialized, sovereign retail banking language model fine-tuned to converse fluently in authentic **Pakistani UrduLish** (Latin-script Urdu interleaved with English banking terminology). 

The model was developed to replace reliance on foreign commercial APIs, providing 100% compliance with State Bank of Pakistan (SBP) data sovereignty requirements, strict refusal of credential phishing/vishing attempts, and structured JSON output for automated dispute resolution.

* **Parameters:** 3.09 Billion
* **Quantization Formats:** FP16, 8-bit GGUF (Q8_0), 4-bit GGUF (Q4_K_M)
* **Context Length:** 2,048 tokens
* **Primary Languages:** Pakistani UrduLish, Urdu, Pakistani English

---

## 2. Intended Use & Capabilities

### Primary Intended Uses:
* **Digital Retail Banking Inquiries:** Account opening guidelines (Asaan, Freelancer), Raast P2P transfers, 1LINK Interbank Fund Transfers (IBFT), debit card activation, and Schedule of Bank Charges (SOC).
* **Automated Dispute Intake:** Parsing customer complaints into structured JSON schemas with automated regulatory Turnaround Time (TAT) computation.
* **Security & Anti-Scam Advisory:** Educating customers against lottery scams (*Jeeto Pakistan*), fake tax transfers, and money mule recruitment.

### Out-of-Scope & Prohibited Uses:
* Providing investment, equity trading, or speculative financial advice.
* Collecting, processing, or transmitting raw passwords, PINs, OTPs, or CVVs.
* Processing binding loan contracts without human credit officer approval.

---

## 3. Training Data & Alignment Methodology

### Supervised Fine-Tuning (SFT) - Day 2:
* **Dataset:** 2,500 sovereign synthetic dialogues across 10 retail banking intents.
* **Formatting:** ChatML format (`<|im_start|>user`, `<|im_start|>assistant`).
* **Hardware:** Tesla T4 GPU on Google Colab (QLoRA 4-bit, Rank $r=16$, Alpha $\alpha=32$, All-Linear projections).
* **Final SFT Loss:** $0.628$ across 3 epochs.

### Direct Preference Optimization (DPO) - Day 3:
* **Dataset:** 500 contrastive triples (`prompt`, `chosen`, `rejected`) targeting SFT edge-case failure modes (vishing compliance, Indian Hindi vocabulary drift, aggressive tone).
* **Hyperparameters:** $\beta = 0.10$, Learning Rate $= 5.0 \times 10^{-5}$, Linear decay.
* **Implicit Reward Margin:** $+12.8966$ with $100\%$ preference discrimination accuracy.

---

## 4. Benchmark Performance & Evaluation

| Benchmark / Evaluation Dimension | Baseline Zero-Shot | Gemini 1.5 Flash API | Zarya-Qwen-3B SFT | Zarya-Qwen-3B SFT + DPO (Final) |
| :--- | :--- | :--- | :--- | :--- |
| **Golden Test 200 Policy Accuracy** | 32.5% | 88.0% | 91.5% | **94.5% (FP16) / 92.4% (Q4_K_M)** |
| **Double-Blind 3-Evaluator Win Rate** | 0.0% | 24.0% | 58.0% | **66.0% (Clean Win)** |
| **Scam / Money Mule Refusal Rate** | 12.0% | 84.0% | 88.0% | **100.0% (Zero Compliance)** |
| **Credential Phishing Refusal** | 45.0% | 90.0% | 94.0% | **100.0% (Zero Leakage)** |
| **UrduLish Naturalness Rubric (1-5)** | 2.1 / 5.0 | 3.8 / 5.0 | 4.6 / 5.0 | **4.9 / 5.0** |
| **Catastrophic Forgetting Retention** | 100% | N/A | 100% | **100% (30/30 Probes Intact)** |

---

## 5. Ethical Considerations & Safety Guardrails

1. **Zero Real Customer PII:** The training pipeline utilized 100% synthetic dialogues generated under deterministic Pakistani banking personas.
2. **Deterministic Middleware:** The model is deployed behind [`src/guardrails.py`](file:///c:/Users/MEE/Anti-Gravity_projects/Fine-tuning-llm/src/guardrails.py) which intercepts prompt injections and redacts CNICs, card numbers, and phone numbers.
3. **Automated Human Escalation:** Any dispute involving $\ge \text{Rs. } 50,000$ or potential fraud is routed directly to a human specialist.
