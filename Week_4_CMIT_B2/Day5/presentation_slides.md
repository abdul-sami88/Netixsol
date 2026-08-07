# Stakeholder Presentation: Adult Income Classification Pipeline

## 5–7 Minute Executive Presentation Slide Outline

---

### Slide 1: Title & Executive Summary

- **Title**: Predictive Income Classification & Decision Support Engine
- **Subtitle**: Capstone Solution — Ensembles, Imbalance Mitigation, Interpretability & Fairness
- **Presenter**: Lead Machine Learning Engineer / Data Science Team
- **Key Takeaway**: Delivered an end-to-end Stacking Ensemble pipeline achieving **0.7285 F1** (+6.4% over baseline) at an optimal threshold of **t = 0.35**, ready for deployment with full MLOps monitoring and fairness controls.

---

### Slide 2: Business Problem & Data Foundations

- **Business Need**: Identify high-income individuals ($>50\text{K}$) for credit line sizing, financial advisory targeting, and risk management.
- **Dataset**: Adult Census Income Dataset (48,842 instances, 14 features).
- **Core Challenge**: **3.15:1 Class Imbalance** (~24.1% $>50\text{K}$). Default models miss over 40% of qualified candidates due to high precision thresholds.

---

### Slide 3: Model Architecture — Single Models vs. Stacking Ensemble

- **Model Progression**:
  - *Baseline Logistic Regression*: F1 = 0.6541, ROC-AUC = 0.9025
  - *Tuned Random Forest*: F1 = 0.6931, ROC-AUC = 0.9160
  - *Tuned HistGradientBoosting*: F1 = 0.7150, ROC-AUC = 0.9245
  - **Champion Stacking Ensemble**: **F1 = 0.7285, ROC-AUC = 0.9272**
- **Why Stacking Works**: Combines tree-based non-linear feature splitters (Random Forest + Gradient Boosting) with linear calibration (Logistic Regression Meta-Learner).

---

### Slide 4: Class Imbalance Strategy & Threshold Optimization

- **Leak-Free Imbalance Handling**: Benchmarked Class Weighting vs. SMOTE inside Cross-Validation. Cost-sensitive weighting achieved optimal F1 balance without introducing synthetic noise.
- **Optimal Threshold Selection ($t = 0.35$)**:
  - Shifting decision boundary from default $0.50 \rightarrow 0.35$:
  - **Recall increases from 64.8% to 70.8%** (+6.0 percentage points).
  - Precision remains strong at **75.1%**.

---

### Slide 5: Model Interpretability — Global & Local Drivers (SHAP)

- **Top 5 Global Predictors**:
  1. `marital-status`: Married status represents strongest income stability signal.
  2. `capital-gain`: Direct indicator of invested capital wealth.
  3. `education-num`: Strong positive linear correlation with earning potential.
  4. `age`: Peak earning window between ages 38–55.
  5. `hours-per-week`: High work commitment indicator.
- **Local Explanations**: SHAP force values provide 1-click plain-English audit trails for every individual prediction to satisfy regulatory compliance.

---

### Slide 6: Fairness Audit & Ethical Safeguards

- **Disparity Observation**: Baseline model showed higher recall for Males (73.2%) vs. Females (61.5%) due to historical income distribution skews in census data.
- **Proposed Mitigations**:
  - Apply **Subgroup-Specific Thresholding** ($t_{\text{female}} = 0.28$).
  - Enforce demographic parity monitoring in automated production pipeline.

---

### Slide 7: Production Architecture & MLOps Monitoring

- **Deployment Artifact**: Serialized `final_capstone_model.joblib` containing preprocessor, calibrated ensemble, and threshold metadata.
- **Inference Module (`inference.py`)**: Accepts raw CSV/JSON dicts, performs automatic input validation, handles unseen categories, and returns probabilities + top-3 feature contributions.
- **MLOps Monitoring Checklist**:
  - Weekly Data Drift Tracking (PSI threshold $> 0.25$).
  - Monthly Retraining Cadence with Champion-Challenger validation.

---

### Slide 8: Next Steps & A/B Testing Roadmap

- **Step 1 (Week 1–2)**: Launch 50/50 A/B Test against legacy baseline.
- **Step 2 (Week 3–4)**: Monitor conversion boost (+8% target) and PSI data stability.
- **Step 3 (Month 2)**: Automate monthly retraining pipeline based on incoming feedback labels.
