# Model Card: Property Valuation & Quantile Range Engine
## Estate AI Pakistan — Production Model Specification

| Attribute | Details |
| :--- | :--- |
| **Model Name** | LightGBM Regressor (Quantile Augmented) |
| **Model Version** | `1.1.100111` (Production Champion) |
| **Model Type** | Gradient Boosted Decision Trees + Quantile Regressors (Pinball Loss) |
| **Task** | Automated Fair Market Valuation & 80% Confidence Interval Estimation |
| **Date Trained** | October 2026 |
| **License** | Proprietary Enterprise Commercial License |
| **Developer** | Estate AI Pakistan Machine Learning & MLOps Team |

---

## 1. Intended Use & Target Audience
- **Primary Use**: Algorithmic estimation of fair market property values across major Pakistani metropolitan cities (Lahore, Karachi, Islamabad, Rawalpindi).
- **Secondary Use**: Construction of statistically bounded 80% trading ranges (P10 to P90) to evaluate investment verdicts (`Underpriced`, `Fair Market Price`, `Overpriced`).
- **Target Users**: Real estate brokers, property investment funds, listing verification officers, and automated valuation platforms.
- **Out-of-Scope / Prohibited Uses**:
  - Official bank mortgage collateral underwriting without physical on-site survey.
  - Court-admissible property dispute valuations without accredited human surveyor appraisal.
  - Speculative extrapolation on unapproved/unverified rural agricultural land.

---

## 2. Training Data & Preprocessing
- **Source**: 6,498 verified, de-duplicated residential and commercial listings across Karachi, Lahore, Islamabad, and Rawalpindi.
- **Feature Set (40 Transformed Features)**:
  - Numerical: `plot_size_marla`, `covered_area_sqft`, `bedrooms`, `bathrooms`, `age_years`, `dist_to_commercial_km`, `weighted_amenity_score`.
  - Engineered: `covered_area_ratio`, `bed_bath_ratio`, `prime_orientation_score`, `society_tier`.
  - Categorical: `city`, `location` (Target-Encoded with Bayesian log-smoothing), `property_type`.
- **Target Variable**: `np.log1p(price_pkr)` (Log-transformed to normalize extreme right-skewed luxury distributions).
- **Train / Validation / Test Split**: 70% Train (4,548), 15% Validation (975), 15% Holdout Test (975).

---

## 3. Performance Metrics (Holdout Evaluation)

| Metric | Target SLA | Champion Model Value | Baseline (OLS) |
| :--- | :--- | :--- | :--- |
| **Mean Absolute Percentage Error (MAPE)** | < 12.0% | **8.37%** | 22.40% |
| **R-Squared ($R^2$) Score** | > 0.90 | **0.9655** | 0.7410 |
| **Mean Absolute Error (MAE)** | < 50 Lakh PKR | **PKR 39.08 Lakh** | PKR 88.50 Lakh |
| **Root Mean Squared Error (RMSE)** | N/A | **PKR 71.40 Lakh** | PKR 145.20 Lakh |
| **Inference Latency** | < 50 ms | **12.4 ms** (p95) | 4.2 ms |

### Quantile Calibration (80% Confidence Interval):
- **Lower Bound ($\alpha = 0.10$)**: Pinball loss calibrated at 10th percentile.
- **Upper Bound ($\alpha = 0.90$)**: Pinball loss calibrated at 90th percentile.
- **Empirical Coverage**: 81.2% of actual transaction prices fall inside the predicted `[P10, P90]` band.

---

## 4. Bias, Fairness & Ethical Considerations
- **Geographic Bias**: High-density sectors (e.g. DHA, Bahria Town, Gulberg) have higher sample representation than peripheral rural localities. Target encoding with minimum sample shrinkage prevents overfitting in sparse locations.
- **Socio-Economic Parity**: The model relies strictly on physical asset characteristics (plot dimensions, covered area, construction age, amenities, road width). No demographic, religious, or ethnic proxy features are included in training.

---

## 5. Limitations & Caveats
1. **Unseen Renovations**: The tabular model evaluates structural age (`age_years`) but cannot visually inspect interior renovations (e.g., imported Italian marble vs standard ceramic tile) without image appraisal (see Future Enhancements).
2. **Rapid Inflation Cycles**: Real estate in Pakistan experiences periodic macro-economic currency devaluations. A static model degrades if inflation exceeds 15%—mitigated by our automated drift monitoring and monthly retraining pipeline.
3. **Out-of-Distribution Bounds**: The model strictly enforces valid ranges (Plot: 1 to 100 Marla; Area: 150 to 25,000 sqft). Outside these bounds, inference is rejected.
