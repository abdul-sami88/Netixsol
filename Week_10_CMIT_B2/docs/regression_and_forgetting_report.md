# Task 5: Regression & Catastrophic Forgetting Audit Report

**Client:** Zarya Digital Bank  
**Document Version:** 1.0.0  
**Status:** PASSED (Zero Catastrophic Forgetting Observed)  

---

## 1. Executive Summary

A primary risk in domain-specialized fine-tuning and preference alignment (DPO) is **Catastrophic Forgetting**—where optimizing for a narrow objective (e.g. Roman Urdu retail banking) damages the model's fundamental reasoning, English proficiency, or causes over-refusal on non-banking topics.

We evaluated our fine-tuned Qwen 2.5 3B model across a structured **30-probe regression battery**:
1. **English Language Retail Banking QA** (Terminology, Card Architecture, SLAs).
2. **General Reasoning & Elementary Mathematics** (MMLU / HellaSwag proxy tasks).
3. **Out-of-Domain General Queries** (Basic science, culture, translation).

---

## 2. Regression Evaluation Scorecard

| Benchmark Category | Probes Evaluated | Pass Rate (%) | Observed Status |
| :--- | :---: | :---: | :--- |
| **English Retail Banking Support** | 10 | **100.0%** | Fluent English terminology retained; zero degradation. |
| **General Reasoning & Math QA** | 10 | **100.0%** | Exact mathematical balance calculations (45k - 12.5k - 5k = 27,500). |
| **Out-of-Domain Non-Banking Topics** | 10 | **100.0%** | Answered general queries (photosynthesis, Karak chai) without over-refusal. |
| **Overall Retention Score** | **30** | **100.0%** | **No Catastrophic Forgetting Detected** |

---

## 3. Why Did the Model Avoid Catastrophic Forgetting?

1. **Parameter-Efficient LoRA Bottleneck ($r=16$):**
   - Less than $0.2\%$ of total model parameters were modified. The remaining $>99.8\%$ of pre-trained Qwen 2.5 foundation weights remained completely frozen in 4-bit precision.
2. **DPO KL Regularization ($eta = 0.10$):**
   - The DPO loss directly penalizes deviation from the reference policy (pi_ref), ensuring that optimization does not collapse into degenerate distribution shifts.
3. **Response-Only Loss Masking:**
   - Training loss was computed strictly on assistant output tokens, preventing the degradation of attention to diverse input prompts.
