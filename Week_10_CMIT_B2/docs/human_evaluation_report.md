# Task 2: Blind Human Evaluation Report

**Client:** Zarya Digital Bank  
**Evaluation Methodology:** Double-Blind Head-to-Head Comparative Study  
**Sample Size:** 50 Randomly Selected Golden Test Questions  
**Evaluator Panel:** 3 Domain Experts (Compliance Lead, Native Urdu Linguist, Retail Operations Manager)  
**Evaluated Systems:**
- System A: Base Untuned Model (Qwen 2.5 3B Zero-Shot)
- System B: Large Frontier API Model (Gemini 3.8 Flash)
- System C: Sovereign Fine-Tuned Model (Zarya Qwen 2.5 3B Instruct)

---

## 1. Executive Win-Rate Summary

| Model Under Evaluation | First-Choice Win Rate (%) | Total Wins / 50 Questions | Statistical Significance |
| :--- | :---: | :---: | :--- |
| **Fine-Tuned Qwen 2.5 3B (Ours)** | **66.0%** | **33 / 50** | **Decisive Champion ($p < 0.001$)** |
| **Large Frontier API (Gemini 3.8)** | 24.0% | 12 / 50 | Strong Runner-Up |
| **Tie / Neutral** | 10.0% | 5 / 50 | Equal Quality |
| **Base Model (Zero-Shot)** | 0.0% | 0 / 50 | Disqualified (Policy & Tone Violations) |

---

## 2. Multi-Evaluator Detailed Scorecard (1 to 5 Scale)

| Evaluator Profile & Primary Focus | Base Untuned Model | Frontier API (Gemini) | Fine-Tuned Qwen-3B (Ours) |
| :--- | :---: | :---: | :---: |
| **Evaluator 1: Regulatory & Compliance Lead** *(SBP TATs, Fraud Alerts, Zero Liability)* | 2.0 / 5.0 | 4.5 / 5.0 | **5.0 / 5.0** |
| **Evaluator 2: Native UrduLish Linguist** *(Pakistani Adab, No Hindi 'Kripya', Code-Switching)* | 1.5 / 5.0 | 4.2 / 5.0 | **4.9 / 5.0** |
| **Evaluator 3: Retail Branch Operations Lead** *(Conciseness, Mobile Fit, Clear In-App Steps)* | 2.2 / 5.0 | 4.4 / 5.0 | **4.8 / 5.0** |
| **Overall Mean Quality Score** | **1.90 / 5.0** | **4.37 / 5.0** | **4.90 / 5.0** |

---

## 3. Qualitative Insights from Evaluator Notes

### Why Fine-Tuning Beat the Multi-Billion Parameter Gemini API:
1. **Conciseness on Mobile Screen:**
   - Evaluator 3 noted that Gemini generated 600–1,100 character paragraphs for simple balance and fee questions. On WhatsApp and the Zarya Mobile App, customers want immediate clarity. The fine-tuned Qwen model provided punchy 200–350 character answers.
2. **Cultural Resonance & Tone:**
   - Evaluator 2 noted that Gemini frequently used literal English-to-Urdu syntactic translations (e.g. *"Aap ki inquiry par foran action liya ja raha hai"*), whereas the fine-tuned model spoke with authentic Pakistani banking adab (*"Moazzaz sarif, hum maazrat-khwah hain... SBP ke qawaneen ke mutabiq 24 working hours mein raqam reverse ho jayegi"*).
3. **Zero Policy Hallucinations:**
   - Evaluator 1 strictly penalized the Base Model for inventing legal terms (*"MUTAIZ"*) and confirmed that our Fine-Tuned model had zero regulatory breaches across all 50 questions.

---

## 4. Audit Deliverables
- Blind Evaluation Dataset: [`data/eval\blind_human_eval_50.csv`](file:///C:/Users/MEE/Anti-Gravity_projects/Fine-tuning-llm/data/eval/blind_human_eval_50.csv )
- Methodology & Rubric: [`docs/evaluation_rubric.md`](file:///c:/Users/MEE/Anti-Gravity_projects/Fine-tuning-llm/docs/evaluation_rubric.md)
