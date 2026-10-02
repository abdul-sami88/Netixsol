# API Documentation: Pakistan Real Estate AI & MLOps Engine
## RESTful Endpoints Specification (FastAPI Backend)

Base URL: `http://localhost:8000` (Local) / `https://estate-ai-api.onrender.com` (Production)  
Interactive OpenAPI Swagger Docs: `/docs`  
ReDoc Documentation: `/redoc`

---

## 1. System & Health Endpoints

### `GET /health`
Verifies service uptime, database connectivity, deployed champion model version, and continuous drift status.

**Response `200 OK`**:
```json
{
  "status": "healthy",
  "service": "Pakistan Real Estate AI Valuation & Lead Scoring API",
  "timestamp": "2026-10-01T11:00:00.000Z",
  "database_connected": true,
  "active_model_version": "1.1.100111",
  "latest_drift_status": "STABLE",
  "models_loaded": {
    "valuation_champion": "LightGBM Regressor (Quantile Augmented)",
    "lead_scoring_champion": "LightGBM Classifier",
    "quantile_valuation_engine": "Active (80% Confidence Interval)",
    "shap_explainers": "Active"
  }
}
```

---

### `GET /model/info`
Returns full model metadata, training dates, hyperparameters, holdout test metrics, and supported categorical domains.

---

## 2. Core Machine Learning Serving Endpoints

### `POST /predict/price`
Calculates fair market property valuation, statistically bounded 80% confidence interval, investment verdict, and legal disclaimer.

**Request Payload (`application/json`)**:
```json
{
  "plot_size_marla": 20.0,
  "covered_area_sqft": 4500.0,
  "bedrooms": 5,
  "bathrooms": 6,
  "age_years": 3.0,
  "city": "Lahore",
  "location": "DHA Phase 6",
  "property_type": "House",
  "is_corner": 1,
  "is_park_facing": 1,
  "is_main_boulevard": 1,
  "amenities": "luxury",
  "listed_price_pkr": 62000000.0
}
```

**Response `200 OK`**:
```json
{
  "status": "success",
  "is_ood": false,
  "property_summary": "20.0 Marla House in DHA Phase 6, Lahore",
  "fair_market_price_pkr": 58500000.0,
  "fair_market_price_formatted": "5.85 crore",
  "confidence_interval_80": {
    "lower_bound_pkr": 54800000.0,
    "lower_bound_formatted": "5.48 crore",
    "upper_bound_pkr": 62200000.0,
    "upper_bound_formatted": "6.22 crore",
    "confidence_level": "80%"
  },
  "investment_verdict": {
    "verdict": "Fair Market Price",
    "listed_price_pkr": 62000000.0,
    "listed_price_formatted": "6.20 crore",
    "client_narrative": "Asking price is well-aligned within normal market trading range."
  },
  "disclaimer": "Disclaimer: All property valuations and price ranges provided are algorithmic statistical estimates based on historical market trends and do not constitute an official FBR, bank-certified, or legal appraisal."
}
```

**Error Responses**:
- `422 Unprocessable Entity`: Triggered if `plot_size_marla < 1.0` or `> 100.0`, or if `covered_area_sqft < 150.0` or `> 25000.0` (Out-of-Distribution Guardrail).

---

### `POST /predict/lead-score`
Calculates conversion probability and priority tier for sales teams.

**Request Payload (`application/json`)**:
```json
{
  "budget_pkr": 50000000.0,
  "num_calls": 4,
  "avg_call_duration_mins": 6.5,
  "response_time_hours": 1.5,
  "days_since_first_contact": 7.0,
  "followup_count": 3,
  "lead_source": "Direct Referral",
  "preferred_city": "Islamabad",
  "purpose": "Buy",
  "property_type_preferred": "House",
  "visit_booked": "Yes",
  "visit_completed": "Yes",
  "objection_raised": "None"
}
```

**Response `200 OK`**:
```json
{
  "conversion_probability_pct": 87.42,
  "priority_tier": "🔥 Hot",
  "recommended_sales_action": "Call immediately within 1 hour! Highly engaged prospect ready to convert.",
  "optimal_cost_threshold": 0.38,
  "lead_summary": "Client budget 5.00 crore for House in Islamabad (Direct Referral)"
}
```

---

### `POST /explain/price`
Returns local SHAP feature attributions ranking the top positive drivers and drag factors influencing the property's valuation.

---

### `POST /explain/lead`
Returns local SHAP attributions and a natural **UrduLish narrative** for sales agents to understand the buyer's psychology.

---

### `POST /predict/batch`
High-throughput batch CSV file processing. Accepts a multipart `.csv` upload and returns predictions for thousands of listings in seconds.

---

## 3. MLOps & Continuous Lifecycle Endpoints

### `GET /monitoring/drift`
Returns the latest drift audit status, feature-level PSI/KS tests, and whether automated retraining is mandated.

---

### `POST /monitoring/run-drift-check?drift_pct=0.15`
Runs a real-time drift evaluation on production batches.

---

### `POST /retrain/trigger`
Executes `retraining_pipeline.py`, benchmarks Challenger vs Champion on the holdout set, promotes Challenger if superior, and hot-reloads model memory.

---

### `POST /model/rollback`
Immediately restores the previous champion model snapshot from `saved_models/rollback/` and hot-reloads memory.

---

### `GET /audit/inferences?limit=25`
Retrieves recent inference logs from SQLite database for compliance and SLA auditing.
