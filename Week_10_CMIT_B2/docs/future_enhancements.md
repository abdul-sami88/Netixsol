# Strategic Future Roadmap & Technical Enhancements

**Client:** Zarya Digital Bank  
**Document:** Week 10 — Day 5: Horizon 2 & Horizon 3 Innovation Roadmap  
**Author:** Antigravity Senior AI/ML Engineering Lead  

---

## 1. Native Urdu-Script (Nastaliq) & Voice Banking (TTS / STT)

* **Nastaliq Script Support:**  
  Extend tokenization and chat templates to seamlessly accept and render native Urdu Nastaliq typography (اردو رسم الخط). Allows financial inclusion for non-English literate populations across Pakistan.
* **Voice AI Engine (WhatsApp Banking Channel):**  
  Integrate local speech-to-text (Whisper fine-tuned on Pakistani accents) and lightweight neural text-to-speech (TTS) to allow customers to send and receive voice notes via WhatsApp and mobile banking.

---

## 2. On-Device Distillation for Mobile (1.5B & 0.5B Models)

* **Knowledge Distillation:**  
  Use the 3B sovereign model as a teacher to distill domain banking capabilities into **Qwen 2.5 1.5B** or **0.5B**.
* **Zero-Latency On-Device Inference:**  
  Quantize the 0.5B model to 3-bit GGUF (~380 MB footprint) capable of running directly on iOS and Android devices via MediaPipe or llama.cpp mobile SDKs, allowing basic balance queries and FAQ support completely offline.

---

## 3. Function-Calling to Live Core Banking Systems

* **Core Banking Webhooks (Temenos T24 / 1LINK):**  
  Implement JSON Schema function-calling so the model can securely initiate real banking micro-actions upon customer biometric approval:
  1. `check_account_balance(account_number, session_token)`
  2. `freeze_debit_card(card_id, reason)`
  3. `fetch_raast_title(raast_id)`
  4. `dispute_atm_transaction(transaction_ref, branch_code)`

---

## 4. Regional Language Expansion (Pakistani Vernaculars)

* **Multilingual Fine-Tuning Adapters:**  
  Train LoRA adapters for Pakistan's major regional languages:
  - **Punjabi (پنجابی / Gurmukhi)**
  - **Sindhi (سنڌي)**
  - **Pashto (پښتو)**
  - **Balochi (بلوچی)**
* Ensures banking access for unbanked and semi-urban retail customers across all four provinces.

---

## 5. Automated Online DPO from Live Telemetry

* **Closed-Loop Alignment:**  
  Replace manual batch retraining with an automated online DPO pipeline.
* Whenever a customer taps **👎 Poor** and an operations officer confirms the correct response in the CRM, the pair is automatically queued for low-rank continuous gradient updates during off-peak hours (3:00 AM PKT).

---

## 6. Coordinated Fraud & Mule Graph Intelligence

* **Cross-Conversation Fraud Graph:**  
  Deploy graph anomaly detection across incoming customer conversations to identify coordinated money mule rings.
* If multiple accounts query identical third-party account numbers within short time intervals or share similar dispute scripts, the system automatically flags the ring and notifies the bank's Anti-Money Laundering (AML) / Fraud Risk Department in real-time.
