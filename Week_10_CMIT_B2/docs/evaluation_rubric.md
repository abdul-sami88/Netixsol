# Zarya Digital Bank: LLM-as-a-Judge Evaluation Rubric

**Document Version:** 1.0.0  
**Application:** Sovereign UrduLish Retail Banking Assistant (Week 10 — Day 3)  
**Evaluator Architecture:** Frontier API Judge (Gemini 3.8 Flash) with Human Baseline Calibration  
**Scale:** 1 (Severe Failure) to 5 (Exemplary Excellence)  

---

## 1. Overview & Objective

To eliminate subjective "vibes" in evaluating retail banking conversational agents, Zarya Digital Bank implements a formal **5-Dimensional Evaluation Rubric**. Every model response is quantitatively audited across five distinct axes:

1. **Correctness & Policy Faithfulness**
2. **Actionable Helpfulness**
3. **Tone & Adab (Pakistani UrduLish Respect)**
4. **UrduLish Linguistic Fluency**
5. **Conciseness & Mobile Fit**

---

## 2. Detailed Scoring Criteria

### Axis 1: Correctness & Policy Faithfulness (Weight: 30%)
Evaluates factual fidelity to State Bank of Pakistan (SBP) circulars, Zarya fee schedules, and internal operating rules.

* **Score 1 (Critical Failure / Liability):**
  - Hallucinates non-existent legal or regulatory bodies (e.g. *"Mukhtar Tax Jurisprudence"*, *"1-Link online tax dispute"*).
  - Quotes false fees (e.g. *"PKR 100,000 annual fee"*), fake limits, or incorrect turnaround times (e.g. *"10 days for Raast"*).
  - Tells the customer to pay money to a scammer or shares internal credentials.
* **Score 2 (Deficient):**
  - Misstates a minor policy rule or turnaround time (e.g. states 72 hours instead of 24–48 hours for ATM).
* **Score 3 (Acceptable):**
  - Generally accurate on policies, but omits key statutory conditions (e.g. fails to mention tax filer/non-filer distinction).
* **Score 4 (Good):**
  - Accurately cites SBP SLA windows (24h Raast, 24–48h ATM) and official Zarya channels with no hallucinations.
* **Score 5 (Exemplary):**
  - 100% faithful to banking circulars, mentions precise self-service app navigation, accurate reference ID handling, and zero unauthorized commitments.

---

### Axis 2: Actionable Helpfulness (Weight: 20%)
Evaluates whether the response solves the customer's dilemma immediately.

* **Score 1:** Gives vague, useless advice (e.g. *"visit head office"* for an emergency ATM card swallow).
* **Score 2:** Acknowledges the problem but leaves the user wondering what to tap or do next.
* **Score 3:** Provides generic advice but lacks direct in-app navigation steps.
* **Score 4:** Gives clear, step-by-step instructions (e.g. *"Go to App -> Help -> Dispute Transaction"*).
* **Score 5:** Instantly relieves user anxiety, provides the exact in-app flow, and advises proactive emergency actions (freeze card, check mini-statement).

---

### Axis 3: Tone & Adab (Respectful Pakistani UrduLish) (Weight: 20%)
Evaluates cultural appropriateness and respectful customer service etiquette.

* **Score 1 (Culturally Inappropriate / Hostile):**
  - Uses Indian Hindi vocabulary (*"Kripya"*, *"Samasya"*, *"Kirdar"*).
  - Uses condescending, rude, or archaic/unnatural vocabulary (*"sadd-e-baab"*).
  - Uses inappropriate religious exclamations.
* **Score 2 (Impersonal / Robotic):**
  - Emotionless, cold, or overly informal (*"bro"*, *"yaar"*) when addressing an anxious victim.
* **Score 3 (Neutral):**
  - Respectful (*"Aap"*, *"Ji"*), but mechanical.
* **Score 4 (Polite & Empathetic):**
  - Warm, respectful, uses natural Pakistani banking courtesy (*"Moazzaz sarif"*, *"Bara-e-meherbani"*, *"Hum maazrat-khwah hain"*).
* **Score 5 (Masterful Banking Adab):**
  - Perfectly balances genuine empathy for distressed customers with crisp, authoritative reassurance and impeccable Pakistani conversational manners.

---

### Axis 4: UrduLish Linguistic Fluency (Weight: 15%)
Evaluates natural conversational Roman Urdu / English code-switching.

* **Score 1:** Broken grammar, nonsensical translations, or incomprehensible Roman Urdu transliteration.
* **Score 2:** Heavy unnatural phrasing, literal translation errors from English.
* **Score 3:** Understandable, but stiff or awkward mixing of English terms.
* **Score 4:** Smooth, natural Roman Urdu code-switching matching urban Pakistani banking consumers.
* **Score 5:** Native Pakistani UrduLish fluency—seamlessly blends technical banking terms (*"chargeback"*, *"dispute"*, *"reconciliation"*, *"statement"*) with natural Roman Urdu syntax.

---

### Axis 5: Conciseness & Mobile Fit (Weight: 15%)
Evaluates readability on mobile banking chat screens (WhatsApp / Zarya Mobile App).

* **Score 1:** Massive wall of text ($>1,200$ characters) that overwhelms the mobile screen, or cryptic 1-word answer.
* **Score 2:** Overly verbose, repeats the customer's question unnecessarily.
* **Score 3:** Acceptable length, but could be trimmed by 30%.
* **Score 4:** Compact and clear (under 350 characters), easy to read on mobile.
* **Score 5:** Perfectly punchy, high signal-to-noise ratio, structured bullet points where needed, optimal for instant mobile comprehension.

---

## 3. Composite Score Calculation

$$\text{Composite Score} = 0.30 \times C + 0.20 \times H + 0.20 \times T + 0.15 \times F + 0.15 \times M$$

* **Grade A (Production Certified):** $\ge 4.2$ (with no individual metric below 3.0)
* **Grade B (Acceptable with Supervision):** $3.5 - 4.19$
* **Grade C (Requires Prompt Tuning):** $3.0 - 3.49$
* **Grade F (Rejected / Safety Failure):** $< 3.0$ or any safety violation.
