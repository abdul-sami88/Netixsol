# Model Card: Inbound Lead Prioritization & Conversion Scoring
## Estate AI Pakistan — Production Model Specification

| Attribute | Details |
| :--- | :--- |
| **Model Name** | LightGBM Binary Classifier (Asymmetric Cost Optimized) |
| **Model Version** | `1.0.0` (Production Champion) |
| **Model Type** | Gradient Boosted Decision Tree Classifier |
| **Task** | Inbound Lead Conversion Probability & Hot/Warm/Cold Tier Prioritization |
| **Date Trained** | October 2026 |
| **License** | Proprietary Enterprise Commercial License |
| **Developer** | Estate AI Pakistan Machine Learning & MLOps Team |

---

## 1. Intended Use & Target Audience
- **Primary Use**: Predicting the probability that an inbound prospective buyer or seller will successfully close a transaction or complete a booked site visit.
- **Actionable Output**: Dynamic triage into:
  - **🔥 Hot Lead** (Probability $\ge 0.70$): 1-hour call SLA assigned to senior broker.
  - **🌤 Warm Lead** (Probability $0.40 - 0.69$): 24-hour follow-up with comps & payment plans.
  - **❄️ Cold Lead** (Probability $< 0.40$): Long-term automated WhatsApp nurturing drip.
- **Target Users**: Agency sales directors, CRM coordinators, tele-sales representatives.

---

## 2. Training Data & Preprocessing
- **Source**: 4,500 historical inbound CRM lead interactions from portals (Zameen, Graana), digital campaigns (Meta/Google), and agency referrals.
- **Class Balance**: 31.4% Converted ($y=1$), 68.6% Non-Converted ($y=0$).
- **Engineered Behavioral Features**:
  - `lead_engagement_score`: Weighted sum of call counts, visit bookings, and duration.
  - `interaction_intensity`: Frequency of touches per day since initial contact.
  - `budget_to_market_ratio`: Comparison of client stated budget vs median market price in target city.
  - `objection_friction_score`: Numerical penalty for objections (Legal issues = high friction; Price = negotiable).
  - `response_speed_category`: Binned agency response time (<1 hr, 1-4 hrs, >4 hrs).

---

## 3. Performance Metrics (Holdout Evaluation)

| Metric | Target SLA | Champion Model Value | Baseline (Logistic Reg) |
| :--- | :--- | :--- | :--- |
| **ROC-AUC (Receiver Operating Characteristic)** | > 0.85 | **0.892** | 0.762 |
| **PR-AUC (Precision-Recall Curve)** | > 0.80 | **0.828** | 0.684 |
| **F1-Score (Optimal Cost Threshold)** | > 0.80 | **0.831** | 0.710 |
| **Hot Lead Precision** | > 85% | **88.4%** | 71.2% |
| **Hot Lead Recall** | > 80% | **84.6%** | 64.0% |

### Asymmetric Cost Decision Threshold:
In real estate sales, the cost of a **False Negative** (ignoring a high-net-worth buyer ready to spend PKR 5 Crore) is approximately **10x higher** than a **False Positive** (a sales agent making a 5-minute phone call to someone not ready).
- By optimizing the decision boundary via expected utility, the optimal threshold was calibrated at $P^* = 0.38$ to prevent any lucrative lead from slipping through the cracks.

---

## 4. Fairness, Bias & Demographic Parity
- **No Protected Attributes**: The model does not ingest demographic attributes (gender, age, marital status, ethnicity, religion, or phone area code).
- **Behavioral Objectivity**: Conversion scoring is driven purely by client engagement signals (frequency of communication, verified budget realism, willingness to attend a physical site visit).

---

## 5. Limitations & Caveats
1. **Seasonal Market Lulls**: During holy months (Ramadan) or monsoon seasons, general engagement scores dip temporarily across all tiers.
2. **Offline Interaction Gaps**: If an agent meets a client in-person at a branch office without logging the interaction in the CRM, the lead's digital engagement score may underestimate actual conversion readiness.
