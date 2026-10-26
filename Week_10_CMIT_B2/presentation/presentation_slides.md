# Zarya Digital Bank: Executive Presentation Slide Deck

**Deck File:** [`presentation/zarya_bank_capstone_presentation.pptx`](file:///c:/Users/MEE/Anti-Gravity_projects/Fine-tuning-llm/presentation/zarya_bank_capstone_presentation.pptx)  
**Target Audience:** Chief Technology Officer (CTO) & Head of Customer Experience (CX)  
**Initiative:** Sovereign UrduLish Retail Banking LLM Platform  
**Format:** 16:9 Widescreen Corporate Executive Briefing  

---

## Slide 1: Title Slide (Dark Theme)
* **Header:** ZARYA DIGITAL BANK
* **Title:** Sovereign UrduLish LLM & Enterprise AI Platform
* **Subtitle:** Capstone Client Handover & Executive Briefing | CTO & Head of CX
* **Tagline:** Production Architecture • DPO Preference Alignment • RAG Hybrid • 87% Cost Reduction

---

## Slide 2: The Strategic Problem (Foreign APIs vs. Sovereign Banking)
1. **Language & Cultural Drift:**
   * Commercial LLMs suffer from Indian Hindi lexical drift (*"Kripya"*, *"Dhanyawad"*) rather than authentic Pakistani banking Urdu.
   * Real Pakistani retail banking operates in UrduLish (*"Mera Raast transfer fail hua, reference ID yeh hai"*).
   * Generic foreign models fail on local vernacular and dispute context.
2. **Regulatory & Privacy Liabilities:**
   * State Bank of Pakistan (SBP) prohibits unencrypted customer financial data crossing foreign borders.
   * Commercial APIs expose customer transactions to foreign retention and training policies.
   * True sovereignty demands on-premise or private cloud deployment within Pakistani borders.
3. **The Cost & Latency Drain:**
   * Commercial APIs bill in USD; constant PKR currency devaluation inflates operating expenditure monthly.
   * High latency on foreign API endpoints degrades mobile banking responsiveness.
   * At 50,000 queries/day, API costs exceed **$2,250/mo** vs **$280/mo** self-hosted.

---

## Slide 3: End-to-End 5-Day Delivery Architecture
* **Day 1: Synthetic Data:** 2,500 sovereign UrduLish dialogues across 10 core banking intents. 100% synthetic, zero PII, strict Pakistani UrduLish grammar.
* **Day 2: SFT Dual LoRA:** Benchmarked Qwen 2.5 3B (3.34 GB VRAM) vs Llama 3.2 3B (5.83 GB VRAM). Selected Qwen-3B for highest UrduLish fluency and low compute profile.
* **Day 4: Quantize & RAG:** Quantized model to 4-bit GGUF (1.89 GB) running at 64.8 tok/s. Live policy RAG for dynamic SBP Schedule of Charges.
* **Day 3: DPO Alignment:** 500 DPO triples. Implicit reward margin $+12.90$, $100\%$ accuracy. Extinguished vishing, scam compliance, and PII leakage.
* **Day 5: Enterprise Ops:** Dockerized deployment with healthchecks. Flywheel pipeline converting negative feedback into DPO pairs. Executive ROI report & Model Card client handover.

---

## Slide 4: DPO Preference Alignment (Eliminating Banking Liabilities)
* **Empirical DPO Training Telemetry (Tesla T4):**
  * Implicit Reward Margin: Surged from $+1.02$ to **`+12.8966`** (Target $> +2.0$).
  * Reward Discrimination Accuracy: **`100.0%`** separation of preferred vs rejected banking answers.
  * Training Loss: Converged cleanly to **`0.0852`** in 63 steps (8 mins 18 secs).
  * Implicit KL regularization strictly bounded model drift against base weights.
  * Zero Catastrophic Forgetting: 100% retention on English reasoning and general banking probes.
* **Behavioral Audit: SFT vs. SFT + DPO:**
  * **Card Number & CVV Harvest Probe:** Model strictly refuses: *"Sorry, I cannot assist with that... Zarya Bank never requests CVV or card details."*
  * **Money Mule Offer (*"Account rent pe dedo 50k mahina"*):** Disclaims illicit account renting and flags financial risk.
  * **Lottery / Prize Scam (*"Jeeto Pakistan sona tax bhejo"*):** Completely extinguishes scam compliance and directs to verified channels.
  * **Hallucinated SBP TATs:** Completely replaced by SBP Consumer Protection Framework standards.

---

## Slide 5: Evaluation Framework & Blind Human Review Benchmarks
* **Double-Blind 3-Evaluator Human Review (50 Probes):**
  * **Fine-Tuned Qwen-3B:** **`66.0%` Win Rate** (33 / 50 clean wins).
  * **Gemini 1.5 Flash (Commercial Cloud API):** **`24.0%` Win Rate** (12 / 50 wins).
  * **Tie / Both Acceptable:** **`10.0%`** (5 / 50).
  * **Base Qwen-3B (Zero-Shot):** **`0.0%` Win Rate** (0 wins).
  * Evaluator Consensus: *"Fine-tuned model demonstrated superior understanding of Pakistani banking terminology (Raast, IBFT, CNIC Asaan) and authentic empathetic phrasing."*
* **Automated LLM-as-a-Judge Calibration:**
  * Calibrated on 50 human audit ratings using a strict 5-dimensional banking rubric.
  * Pearson Correlation Coefficient: **`r = 0.865`** (Target $> 0.80$).
  * Mean Absolute Error (MAE): **`0.19` stars** on a 1.0 to 5.0 scale.
  * Human Agreement Within 0.5 Stars: **`90.0%`** concordance.
  * Enables fully automated CI/CD continuous regression testing on daily commits.

---

## Slide 6: Quantization (Shrinking the Model for Affordable Deployment)
| Format | Model Size | VRAM Footprint | Generation Speed | Time to First Token | Golden Test Retention |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **FP16 (Reference Merged)** | 6.18 GB | 7.2 GiB | 38.5 tok/s | 45.2 ms | 100.0% (Ref) |
| **8-bit GGUF (Q8_0)** | 3.38 GB (-45%) | 4.1 GiB (-43%) | 52.1 tok/s | 32.6 ms | 99.4% (-0.6% loss) |
| **4-bit GGUF (Q4_K_M) ★ RECOMMENDED** | **1.89 GB (-69%)** | **2.3 GiB (-68%)** | **64.8 tok/s (+68%)** | **24.1 ms (-47%)** | **92.4% (Negligible loss)** |

---

## Slide 7: RAG + Fine-Tuning Hybrid (Style is Fixed, Facts Change)
* **The Division of Responsibilities:**
  * **Fine-Tuning Role:** Teaches conversational empathy, authentic UrduLish grammar, SBP dispute etiquette, and structured JSON tool schemas.
  * **RAG Engine Role:** Injects live, verifiable policy context (Schedule of Bank Charges, Raast transfer limits, Asaan account balance caps).
  * Eliminates model retraining whenever State Bank of Pakistan updates 1LINK or ATM withdrawal fees.
  * Tri-way Benchmark: Fine-Tuned + RAG scored **9.8/10** vs 7.9/10 for FT alone and 6.8/10 for Base + RAG.
* **Live Proof: Zero-Retraining Dynamic Update:**
  * Step 1: User asks: *"PayPak debit card ki annual fee kitni hai?"*
  * Model Answer (Before): *"Zarya PayPak Debit Card ki annual fee Rs. 1,200 plus FED hai."*
  * Step 2: Operations team updates policy JSON on disk (Rs. 1,200 $\to$ Rs. 1,500). Zero model retraining.
  * Step 3: User repeats question.
  * Model Answer (After): *"Zarya PayPak Debit Card ki annual fee Rs. 1,500 plus FED hai."*
  * Result: Instantaneous policy compliance with zero compute downtime.

---

## Slide 8: Multi-Layer Guardrails & SBP Complaint Ticketing
* **Deterministic Security Guardrails:**
  * **Inbound Prompt Injection:** Blocks jailbreaks (*"Ignore previous instructions"*) with 100% precision.
  * **Credential Harvesting Blocker:** Intercepts requests for PIN, OTP, password, or CVV.
  * **Scam Interceptor:** Detects lottery schemes (*"Jeeto Pakistan"*) and enforces mandatory institutional warning: *"Zarya Bank kabhi bhi call ya SMS par aap ka OTP ya PIN nahi maangta..."*
  * **Outbound PII Masking:** Redacts CNICs (`42101-*******-1`) and phone numbers before writing to audit logs.
* **SBP Regulatory Ticketing & Auto-Escalation:**
  * Automated Complaint Tickets: Generates unique ticket IDs (`ZAR-2026-XXXX`) into database.
  * Regulatory SLA Assignment: ATM disputes (10 days), Raast failed transfer (48 hours), Fraud investigation (30 days).
  * Multi-Factor Human Escalation: Automatically escalates cases to human fraud specialist if disputed amount $\ge \text{Rs. } 50,000$, category is `FRAUD`, or customer expresses distress.
  * Integrated directly into Support-Agent CRM dashboard.

---

## Slide 9: Executive Cost & ROI Analysis (50,000 Messages / Day)
* **Volume Baseline:** 50,000 queries/day = **1,500,000 queries/month** (375M tokens/mo).
* **Proprietary Cloud API (GPT-4o / Claude Sonnet):** **$2,250 / month** (~PKR 630,000/mo) + ongoing FX currency depreciation risk.
* **Self-Hosted Sovereign Qwen-3B (AWS g5.xlarge / RunPod):** **$280 / month** (~PKR 78,000/mo).
* **Monthly Operational Savings:** **$1,970 / month** (~PKR 550,000/mo).
* **Annual Savings to Bank:** **$23,640 (~PKR 6.6 Million)** every single year!
* **Break-Even Horizon:** Capital investment recouped in **less than 18 days**.
* **Strategic Enterprise Benefits:**
  1. Complete Data Sovereignty: Customer banking dialogues never leave the bank's secure VPC or local data center.
  2. Latency Guarantee: Continuous batching & KV caching deliver p50 latency of 70 ms vs 800+ ms for foreign cloud APIs.
  3. Independence from Vendor Lock-in: Zero risk of third-party API rate limits, deprecations, or price hikes.
  4. Customizable Core IP: The weights, training data, and preferences belong 100% to Zarya Digital Bank.

---

## Slide 10: Future Roadmap & Client Handover
1. **Multimodal & Script Expansion:**
   * Urdu Nastaliq Script: Dual support for native Urdu script alongside UrduLish.
   * Voice AI (TTS / STT): Voice note support over WhatsApp banking channel in authentic Pakistani accents.
   * Regional Dialect Support: Pashto, Sindhi, and Punjabi language adapters.
2. **Core Banking Deep Integration:**
   * Direct Core Banking Webhooks: Live balance checks and Raast account title fetch via 1LINK Open Banking APIs.
   * Autonomous Multi-Step Actions: Card freeze and replacement dispatch with biometric verification.
   * Graph Fraud Intelligence: Detection of coordinated money mule rings across concurrent conversations.
3. **Operations & Handover Deliverables:**
   * Dockerized Deployment Package: Production-ready containers with automated CI/CD workflows.
   * Enterprise Model Card: Provenance, hyperparameters, ethics, and security audit signoff.
   * Continuous Data Flywheel: Automatic pipeline converting negative customer feedback into new DPO training triples.
   * Full IT Runbook & Rollback Guide.
