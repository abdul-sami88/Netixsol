# Pakistan Real Estate AI Ecosystem
## Enterprise Voice Agent, Automated Valuation, Lead Scoring & Continuous MLOps Platform

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-FF4B4B.svg)](https://streamlit.io)
[![MLflow](https://img.shields.io/badge/MLflow-Tracking-0194E2.svg)](https://mlflow.org)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)]()

---

## 🏛️ Repository Architecture

This repository hosts the end-to-end **Pakistan Real Estate AI & Commercial Sales Platform** developed across Weeks 7 and 8:

```
week_7 & week_8/
│
├── AI_property_valuation_lead_scoring/      <-- [Week 8 Capstone] Machine Learning & MLOps
│   ├── data_cleaned/                        # Cleaned listings (6.5k) & CRM leads (4.5k)
│   ├── saved_models/                        # Serialized Champion models, quantile engines & SHAP
│   │   ├── archive/                         # Versioned immutable deployment snapshots
│   │   └── rollback/                        # Instant 15-second restore mirror
│   ├── reports/                             # Interactive HTML drift reports & retraining logs
│   ├── docs/                                # Model Cards, API specs, User & Maintenance guides
│   ├── src/                                 # Feature engineering, pipeline & modeling source
│   ├── serving_api.py                       # Production FastAPI model serving engine
│   ├── dashboard.py                         # 6-Tab Streamlit Interactive Dashboard
│   ├── drift_monitoring.py                  # Statistical KS/PSI drift detection engine
│   ├── retraining_pipeline.py               # Automated holdout benchmark & gated promotion
│   ├── database.py                          # SQLite/PostgreSQL inference audit logging
│   ├── Dockerfile                           # Production container specification
│   ├── docker-compose.yml                   # Multi-service container orchestration
│   ├── RENDER_DEPLOYMENT_GUIDE.md           # Step-by-step Render.com deployment manual
│   ├── Capstone_Stakeholder_Presentation.pptx # 10-slide executive widescreen slide deck
│   └── STAKEHOLDER_DEMO_GUIDE.md            # Minute-by-minute live presentation script
│
└── real_estate_voice_agent/                 <-- [Week 7] Conversational AI Voice Agent & CRM
    ├── app.py                               # Voice agent FastAPI server (Vapi/Deepgram compatible)
    ├── database.py                          # CRM database manager (clients, calls, appointments)
    ├── real_estate.db                       # Active SQLite database with verified comps & logs
    ├── client_delivery_docs/                # Week 7 handover & architecture documentation
    └── RealEstate_Hub_AI_Voice_Agent_Handover.pptx # Week 7 presentation deck
```

---

## 🚀 Key Highlights & Deliverables

### 1. Property Valuation & Quantile Engine (MAPE 8.37% vs Baseline 22.4%)
- **Champion LightGBM Model**: Trained on 6,498 listings with Target Encoding and Bayesian smoothing.
- **80% Statistical Trading Range**: Pinball loss quantile regression ($\alpha=0.10, \alpha=0.90$) generating Lower Bound, Fair Market Price, and Upper Bound.
- **Automated Investment Verdicts**: Classifies listings into `Underpriced`, `Fair Market Price`, or `Overpriced`.

### 2. Inbound Lead Prioritization (ROC-AUC 0.892, PR-AUC 0.828)
- **Asymmetric Cost Matrix ($P^* = 0.38$)**: Prioritizes recall to eliminate missed high-value property buyers.
- **Dynamic Tiering**:
  - **🔥 Hot Lead** ($\ge 70\%$): 1-hour call SLA assigned to senior broker.
  - **🌤 Warm Lead** ($40\% - 69\%$): 24-hour follow-up with comps & payment plans.
  - **❄️ Cold Lead** ($< 40\%$): Drip nurture via automated WhatsApp campaigns.

### 3. Transparent Explainability in UrduLish
- **SHAP TreeExplainer**: Waterfall attribution ranking positive price drivers and drag factors.
- **Bilingual Narratives**: Natural Roman Urdu talking points for sales brokers (*"Location DHA Phase 6 aur corner plot hone ki wajah se value mein 1.0 Crore ka premium shamil hai"*).

### 4. Continuous MLOps: Drift Detection & Automated Retraining
- **Statistical Drift Engine**: Kolmogorov-Smirnov 2-sample tests, Wasserstein distance, and Population Stability Index (PSI with 10 quantile bins).
- **Automated SLA Threshold**: Triggered when **MAPE > 15.0%** or **PSI $\ge$ 0.25**.
- **Gated Retraining**: Promotes Challenger only if it beats the Champion on a fixed holdout set.
- **Instant Rollback**: 1-click restoration from `saved_models/rollback/` in under 15 seconds.

---

## 🌐 Deploying on Render.com (Using Root Directory)

Because both projects live in this repository, you use Render's **Root Directory** setting to deploy cleanly without moving any files:

### Deploying the FastAPI Backend:
1. In [Render Dashboard](https://dashboard.render.com), click **New +** $\rightarrow$ **Web Service**.
2. Connect your Git repository.
3. Configure settings:
   - **Root Directory**: `AI_property_valuation_lead_scoring`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt`
   - **Start Command**: `uvicorn serving_api:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path**: `/health`

### Deploying the Streamlit Dashboard:
1. Click **New +** $\rightarrow$ **Web Service**.
2. Connect the same repository.
3. Configure settings:
   - **Root Directory**: `AI_property_valuation_lead_scoring`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt`
   - **Start Command**: `streamlit run dashboard.py --server.port $PORT --server.address 0.0.0.0 --server.headless true`
   - **Environment Variables**: `API_URL=https://estate-ai-api.onrender.com`

---

## 🧪 Testing & Verification

Run the automated test suite locally:
```bash
cd AI_property_valuation_lead_scoring
pytest test_serving_api.py test_day5_capstone.py -v
```
All 15 automated test cases pass with 100% green.
