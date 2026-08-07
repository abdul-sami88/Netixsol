# Model Monitoring & Maintenance Checklist
## Adult Census Income Classification Pipeline (Production Environment)

---

### 1. Executive Summary & Monitoring Objectives
Post-deployment, machine learning models degrade over time due to covariate shift (data drift), concept shift (relationship changes between features and target income), and pipeline schema alterations. This checklist establishes operational procedures, quantitative metrics, alert thresholds, and automated retraining triggers to maintain target performance ($\text{F1} \ge 0.70$, $\text{ROC-AUC} \ge 0.90$, $\text{Brier Score} \le 0.10$).

---

### 2. Core Monitoring Pillars

#### A. Input Data Drift (Covariate Shift)
Monitor numerical distributions and categorical frequency distributions against baseline training distributions ($X_{\text{train}}$).
- **Population Stability Index (PSI)**: Computed weekly for numerical features (`age`, `capital-gain`, `hours-per-week`, `education-num`).
  - $\text{PSI} = \sum \left( \% \text{Actual} - \% \text{Expected} \right) \times \ln\left( \frac{\% \text{Actual}}{\% \text{Expected}} \right)$
- **Kolmogorov-Smirnov (KS) Test**: Daily statistical distance checks on continuous feature distributions.
- **Categorical Schema Checks**: Track percentage of unseen categories (e.g. new `occupation` or `native-country` strings).

#### B. Model Output & Prediction Drift
Track changes in inference score distributions prior to receiving ground-truth labels.
- **Positive Selection Rate (PSR)**: Percentage of production inferences classified as $>50\text{K}$ at threshold $t = 0.35$ (Baseline: ~28.5%).
- **Score Distribution Metrics**: Weekly monitoring of mean, median, standard deviation, and 90th percentile of predicted positive probabilities $P(Y=1 \mid X)$.

#### C. Model Performance & Calibration (Ground-Truth Feedback)
Evaluated monthly as verified tax/income verification labels become available.
- **F1-Score & Recall Tracking**: Primary business metrics evaluated on production ground-truth samples.
- **Calibration & Brier Score**: Reliability diagram drift check to ensure predicted probabilities remain well-calibrated probabilities.
- **Subgroup Fairness Metrics**: Monitor parity ratios across `sex` and `race` subgroups to prevent bias amplification.

---

### 3. Metric Thresholds & Alert Matrix

| Metric Category | Target Indicator | Green (Healthy) | Yellow (Warning) | Red (Critical Alert) | Action Required |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Data Drift** | Feature PSI | $\text{PSI} < 0.10$ | $0.10 \le \text{PSI} < 0.25$ | $\text{PSI} \ge 0.25$ | Retrain pipeline on recent window |
| **Unseen Categories** | Unknown Levels % | $< 0.5\%$ | $0.5\% - 2.0\%$ | $> 2.0\%$ | Update OneHotEncoder / Imputer |
| **Prediction Drift** | Positive Class Rate | $25\% - 32\%$ | $20\%-25\%$ or $32\%-38\%$ | $< 20\%$ or $> 38\%$ | Inspect macro-economic shifts |
| **Performance** | Hold-out F1 Score | $\text{F1} \ge 0.70$ | $0.65 \le \text{F1} < 0.70$ | $\text{F1} < 0.65$ | Trigger emergency retraining |
| **Calibration** | Brier Score | $\le 0.10$ | $0.10 - 0.13$ | $> 0.13$ | Recalibrate probabilities (Isotonic/Sigmoid) |
| **Fairness** | Subgroup F1 Ratio | $\ge 0.85$ | $0.75 - 0.85$ | $< 0.75$ | Re-weight training samples or adjust threshold |

---

### 4. Incident Response & Retraining Strategy

1. **Automated Warning Trigger (Yellow)**:
   - Notify MLOps team via Slack/PagerDuty.
   - Run diagnostic drift attribution scripts to isolate specific drifting features (e.g. shifts in `capital-gain` during tax season).

2. **Automated Retraining Trigger (Red Alert / Cadence)**:
   - **Scheduled Cadence**: Re-fit pipeline monthly using a rolling 12-month window of data.
   - **Event-Driven Trigger**: Triggered automatically when $\text{PSI} \ge 0.25$ or $\text{F1}$ drops below $0.65$.
   - **Shadow Deployment & Champion-Challenger Test**: Validate newly trained model against current champion model on hold-out data. Require minimum $+2\%$ F1 boost or significant drift reduction before automated promotion to production.
