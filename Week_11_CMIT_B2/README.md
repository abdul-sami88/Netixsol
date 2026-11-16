# 🛍️ ShopKaro — AI Commerce Intelligence Platform
### 5-Day Production-Grade E-Commerce AI System

Production-ready e-commerce intelligence system designed for **ShopKaro**, Pakistan's premier multi-category digital marketplace (Fashion, Electronics, Home & Living, Beauty, and Groceries).

---

## 🏗️ Architecture & Project Structure

```
AI_E-Commerce_Intelligence_Platform/
├── data/
│   ├── datasources.md               # Source provenance & adaptation notes
│   ├── raw/                         # Raw clickstream, catalogue, users & reviews
│   │   ├── products.csv             # 50,000 Pakistani SKUs in PKR
│   │   ├── users.csv                # 25,000 registered users across 10 cities
│   │   ├── events_raw.csv           # 655,750 raw interactions (with synthetic noise)
│   │   ├── calendar.csv             # 2-year Pakistani festival retail calendar
│   │   └── reviews.csv              # 6,000 multilingual reviews (Urdu, Roman Urdu, English)
│   └── processed/
│       ├── shopkaro.duckdb          # High-speed analytical database with 12 indexed tables
│       ├── events_cleaned.parquet   # 530,352 cleaned clickstream events
│       ├── sessions.parquet         # 527,603 sessionized visits (30-min inactivity rule)
│       ├── orders.parquet           # 37,154 completed checkout transactions (Rs. 1.74B GMV)
│       ├── user_features.parquet    # User feature store (RFM segment, AOV, category affinity)
│       ├── item_features.parquet    # Item feature store (popularity score, margins, embeddings text)
│       └── splits/                  # Chronological & cold-start benchmark partitions
│           ├── train.parquet        # 80.0% chronological train set (424,281 events)
│           ├── val.parquet          # 10.0% validation set (53,035 events)
│           ├── test.parquet         # 10.0% test set (53,036 events)
│           ├── test_cold_users.parquet # Isolated cold-start unseen users
│           └── test_cold_items.parquet # Isolated cold-start unseen products
├── src/
│   ├── data_pipeline/               # Day 1: Generator, Cleaner, Sessionizer, DB Loaders
│   ├── eda/                         # Day 1: Exploratory Data Analysis
│   ├── segmentation/                # Day 1: RFM & K-Means 5-Persona Clustering
│   ├── retention/                   # Day 1: Cohort retention, 90-day churn, CLV
│   ├── features/                    # Day 1: User & Item Feature Stores, Splits
│   ├── recommender/                 # Day 2: Industrial Recommendation Engine
│   │   ├── baselines.py             # Popularity, Category Popular, 7-Day Trending
│   │   ├── collaborative.py         # Item-Item Cosine & Implicit ALS with Tuning
│   │   ├── content_hybrid.py        # TF-IDF Text Embeddings & PyTorch Neural Two-Tower
│   │   ├── metrics.py               # Precision@K, Recall@K, Hit Rate, NDCG, MAP, Coverage, Diversity, Novelty
│   │   ├── fbt.py                   # Frequently Bought Together via FP-Growth
│   │   ├── reranker.py              # Business Rules Re-Ranking Layer & Roman Urdu Explanations
│   │   └── evaluate.py              # Full Offline Evaluation Benchmark Harness
│   ├── forecasting/                 # Day 3: Demand Forecasting & Inventory Intelligence
│   │   ├── analysis.py              # Time-series decomposition, moving Islamic festival shifts, ADF, Croston
│   │   ├── models.py                # Naive, Seasonal Naive, ARIMA, ETS, Prophet (holidays), LightGBM, Neural MLP
│   │   ├── backtest.py              # 4-Fold rolling-origin backtest, WAPE, MAPE breakdown, festival accuracy
│   │   ├── probabilistic.py         # Multi-quantile LightGBM (P10, P50, P90), empirical calibration, fan chart
│   │   └── inventory.py             # Safety stock, ROP, 14-day stockout alerts, overstock engine, simulation
│   ├── search/                      # Day 4: Smart Search Engine
│   │   ├── query_parser.py          # Pakistani currency parsing ("1.5 lac"), Roman Urdu spelling normalization
│   │   ├── hybrid_search.py         # BM25 + Semantic Vector Search + RRF (k=60) + Cross-Encoder reranking
│   │   ├── personalized_search.py   # Multi-persona search reranking using Day 2 customer profiles
│   │   └── evaluate_search.py       # 50-Query offline evaluation benchmark (NDCG@10, Precision@10, MRR@10)
│   ├── assistant/                   # Day 4: UrduLish Shopping Assistant
│   │   └── shopping_assistant.py    # Zero-hallucination agent grounded with 6 DuckDB tool APIs
│   ├── review_intelligence/         # Day 4: Multilingual Reviews & Management Insights
│   │   ├── sentiment_absa.py        # Multilingual sentiment & 6-aspect ABSA extraction + Product summary
│   │   ├── topic_and_spam.py        # NMF topic discovery & fake/spam review burst detector
│   │   └── management_insights.py   # Category/seller complaints, sentiment degradation, weekly executive report
│   ├── serving/                     # Day 5: Real-Time Serving API & Cache Layer
│   │   ├── api.py                   # Production FastAPI REST backend (Recommendations, Search, Chat, Forecast)
│   │   └── cache.py                 # Multi-tier Redis + in-memory LRU cache (< 10ms serving)
│   ├── experimentation/             # Day 5: A/B Testing & Statistical Inference
│   │   └── ab_test.py               # Power analysis, 50k traffic simulation, CVR/RPV z/t-tests, Ship decision
│   └── demo/                        # Day 5: Executive Stakeholder Live Demonstration
│       └── run_demo.py              # 10-Minute CEO live walkthrough script
├── dashboard/                       # Day 5: Interactive Web Dashboard (HTML5 / CSS3 / JavaScript)
│   ├── index.html                   # Single-page UI with Customer, Operations, and Management tabs
│   ├── styles.css                   # Responsive dark-theme styling with KPI cards and tables
│   └── app.js                       # Real-time API bindings and in-session dynamic click update
├── reports/
│   ├── figures/                     # Publication-quality charts (PNG)
│   ├── er_diagram.md                # Entity-Relationship diagram & data model
│   ├── eda_insights.md              # Exploratory data analysis insights
│   ├── customer_personas.md         # 5 Pakistani customer personas & strategies
│   ├── cohort_clv_report.md         # Cohort retention, churn & CLV model
│   ├── feature_store_and_splits.md  # Feature engineering & temporal split methodology
│   ├── recommender_system_report.md # Day 2 Offline evaluation & production choice
│   ├── demand_forecasting_report.md # Day 3 Demand forecasting & inventory optimization report
│   ├── weekly_seller_management_report.md # Day 4 Automated executive management report
│   ├── day4_explanation.md          # Day 4 Technical reference documentation
│   ├── ab_test_report.md            # Day 5 Executive A/B testing decision report (Ship verdict)
│   ├── stakeholder_presentation.md  # Day 5 10-slide executive slide deck & presentation
│   ├── model_cards.md               # Day 5 Production model cards (Recommender, Forecaster, Reviews)
│   ├── user_guides.md               # Day 5 Operational user guides (Marketing, Operations, Management)
│   └── day5_explanation.md          # Day 5 Technical reference 
├── main_day1.py                     # Master orchestration script: Day 1
├── main_day2.py                     # Master orchestration script: Day 2
├── main_day3.py                     # Master orchestration script: Day 3
├── main_day4.py                     # Master orchestration script: Day 4
├── main_day5.py                     # Master orchestration script: Day 5 (Capstone)
├── Dockerfile                       # Multi-stage production container
├── docker-compose.yml               # Service orchestration (API, Redis, DB volume)
├── .env.example                     # Environment variables template
├── .github/workflows/ci.yml         # Automated GitHub Actions CI workflow
└── README.md
```

---

## 📊 Summary of Day 1: Data Foundation & Analytics

| Task | Core Objective | Key Deliverable & Metric | Status |
| :--- | :--- | :--- | :--- |
| **Task 1: Data Pipeline** | Clean clickstream, 30-min sessions, DuckDB database | • 655,750 raw events cleaned $\to$ **530,352 clean events**<br>• 120,898 bot/runaway clicks filtered<br>• **527,603 sessions** built via 30-min inactivity rule | ✅ Complete |
| **Task 2: Exploratory Analysis** | Funnel, Pareto 80/20, temporal/festival trends, sparsity | • View $\to$ Cart: **24.0%**, Cart $\to$ Purchase: **38.9%**, Overall: **9.4%**<br>• Extreme Pareto: **0.01%** of SKUs drive 80% of sales<br>• Matrix Sparsity: **99.9743%** | ✅ Complete |
| **Task 3: Customer Segmentation** | RFM scoring + K-Means clustering into 5 retail personas | • 5 personas: **Eid Shoppers, Loyal Tech Buyers, Routine Replenishers, Bargain Hunters, Window Shoppers** | ✅ Complete |
| **Task 4: Cohort & Retention** | Monthly cohort retention heatmap, repeat rate, churn, CLV | • **48.47% Repeat Purchase Rate** (6,951 repeat buyers)<br>• **Customer Lifetime Value (CLV):** **Rs. 18,338.19** | ✅ Complete |
| **Task 5: Feature Store & Splits** | User/item feature tables, chronological 80/10/10 split | • User & Item Feature Stores<br>• Strict Chronological Train (80%) / Val (10%) / Test (10%)<br>• Dedicated **Cold-Start Users** & **Cold-Start Items** test sets | ✅ Complete |

---

## 🛍️ Summary of Day 2: Recommendation Engine

| Task | Core Objective | Key Deliverable & Metric | Status |
| :--- | :--- | :--- | :--- |
| **Task 1: Baselines** | Implement Most Popular Overall, Category Popular, 7-Day Trending | • Baseline benchmarks established on chronological test set<br>• Category Popular achieves **0.7273 Hit Rate** on cold users | ✅ Complete |
| **Task 2: Collaborative Filtering** | Item-Item Cosine, Implicit ALS matrix factorization & tuning | • Fast Item-Item Cosine Similarity (**NDCG@10: 0.1249**)<br>• Hu-Koren-Volinsky Implicit ALS tuned (**factors=128, reg=0.05, iter=15**)<br>• Explicit vs. Implicit theoretical comparison documented | ✅ Complete |
| **Task 3: Content & Hybrid** | TF-IDF text embeddings & PyTorch Neural Two-Tower | • Sublinear TF-IDF (4,718 features) embeddings in 6ms<br>• PyTorch Two-Tower (User + Item Side Features) with precomputed item tower vectors<br>• User & Item cold-start mitigation | ✅ Complete |
| **Task 4: Offline Evaluation** | P@10, R@10, Hit Rate, NDCG@10, MAP, Coverage, Diversity, Novelty | • Rigorous benchmark across 500 active test users<br>• Model comparison table & chart ([`reports/figures/model_comparison_metrics.png`](file:///c:/Users/MEE/Anti-Gravity_projects/AI_E-Commerce_Intelligence_Platform/reports/figures/model_comparison_metrics.png))<br>• Production model chosen: **Hybrid Two-Tower + Cosine Retrieval + Re-Ranker** | ✅ Complete |
| **Task 5: Business Re-Ranking** | Stock/Repeat filters, Brand Diversity, Margin/Festival boost, FP-Growth, Roman Urdu | • Out-of-stock & repeat filters applied<br>• Max 2 items per brand enforced<br>• +20% High-margin boost & +35% Chaand Raat/Eid boost<br>• Frequently Bought Together bundles mined via FP-Growth<br>• Transparent one-line Roman Urdu explanations | ✅ Complete |

---

## 📦 Summary of Day 3: Demand Forecasting & Inventory Intelligence

| Task | Core Objective | Key Deliverable & Metric | Status |
| :--- | :--- | :--- | :--- |
| **Task 1: Time-Series Analysis** | Trend/seasonal decomposition, moving Islamic festival shifts, ADF tests, intermittent demand | • 7-day weekly decomposition & ADF stationarity confirmed ($p < 0.001$)<br>• Islamic festival lunar calendar drift (10-11 days shift/year) modeled<br>• Syntetos-Boylan-Croston (SBC) grid: 3,889 intermittent SKUs analyzed with Croston's method | ✅ Complete |
| **Task 2: Forecasting Models** | Baselines, ARIMA, ETS, Prophet with Pakistan holidays, Global LightGBM, Neural MLP | • Naive, Seasonal Naive, ARIMA, ETS implemented<br>• Prophet with custom Pakistani holiday surge windows (-2 days to +1 day)<br>• Global LightGBM trained with lags, rolling statistics, calendar encodings | ✅ Complete |
| **Task 3: Rolling Backtest** | 4-fold expanding window backtest, MAE/RMSE/WAPE, festival accuracy, volume tiers | • 4 temporal folds across Q4 2025 (11.11 & Blessed Friday)<br>• **Prophet (27.3% WAPE)** & **LightGBM (28.4% WAPE)** beat baselines (47-66% WAPE)<br>• Mathematical explanation of why standard MAPE breaks on low-volume items vs. WAPE | ✅ Complete |
| **Task 4: Probabilistic Forecasts** | Multi-quantile regression (P10, P50, P90), empirical calibration, fan charts | • LightGBM quantile regression models fitted for P10, P50, P90<br>• Calibration check: **P90 achieved 92.1% empirical test coverage** (target 90%)<br>• Prediction interval ribbon chart generated | ✅ Complete |
| **Task 5: Inventory Optimization** | Safety Stock, Dynamic ROP, 14-day stockout alerts, overstock engine, simulation | • Dynamic $SS = Z \sqrt{L \sigma_D^2 + D^2 \sigma_L^2}$ & $ROP = D \cdot L + SS$ (95% service level)<br>• **3,847 SKUs flagged** with imminent 14-day stockout risk alerts & reorder units<br>• **40,266 overstocked SKUs** identified with markdown tiers<br>• Counterfactual Simulation: **3,724 stockouts prevented (85% reduction)**, **Rs. 131.3M GMV protected**, **Rs. 5.05M annual holding costs saved** | ✅ Complete |

---

## 🔍 Summary of Day 4: Smart Search, Shopping Assistant & Review Intelligence

| Task | Core Objective | Key Deliverable & Metric | Status |
| :--- | :--- | :--- | :--- |
| **Task 1: Hybrid Search** | BM25, Semantic vector search, RRF (k=60), Cross-Encoder reranking, Query understanding | • Query understanding: Pakistani currency ("20 hazaar" $\to$ 20k, "1.5 lac" $\to$ 150k), colors, occasions, Roman Urdu synonyms<br>• 50 labelled queries benchmark: **Hybrid RRF achieves 0.7391 NDCG@10 & 0.9483 MRR@10**; Cross-Encoder achieves **0.6420 Precision@10** | ✅ Complete |
| **Task 2: Personalised Search** | Re-rank search candidates using Day 2 customer profile (affinity, AOV, loyalty) | • Same query ("eid gift collection under 15000") delivers **Sadia (Tech Enthusiast) $\to$ Smart Watches** vs. **Ahmed (Eid Shopper) $\to$ Embroidered Kurtas** | ✅ Complete |
| **Task 3: UrduLish Assistant** | Conversational shopping agent with 6 verified tools & zero hallucination policy | • 6 tools grounded in DuckDB: `search_products`, `get_recommendations`, `compare_products`, `add_to_cart`, `get_order_status`, `get_review_summary`<br>• Verified Pakistani retail dialogues ("Ammi ke liye Eid gift 3000 tak") | ✅ Complete |
| **Task 4: Review Intelligence** | Multilingual sentiment, 6-aspect ABSA, NMF topic discovery, fake review detection | • Multilingual sentiment & 6-aspect ABSA (Quality, Price, Delivery, Size/Fit, Packaging, Seller)<br>• NMF discovered 5 retail themes across 6,000 reviews<br>• Fake review detection: flagged duplicate texts, velocity bursts, rating dissonance | ✅ Complete |
| **Task 5: Seller & Management Insights** | Category/seller complaint distribution, falling sentiment detection, weekly report | • Surfaces top complaints by category (e.g. Size/Fit in Apparel, Delivery in Groceries)<br>• Automated detection of SKUs with severe sentiment degradation (>25% drop)<br>• Generates [`reports/weekly_seller_management_report.md`](file:///c:/Users/MEE/Anti-Gravity_projects/AI_E-Commerce_Intelligence_Platform/reports/weekly_seller_management_report.md) | ✅ Complete |

---

## 🏆 Summary of Day 5 (Capstone): Real-Time Serving, A/B Testing, Deployment & Handover

| Task | Core Objective | Key Deliverable & Metric | Status |
| :--- | :--- | :--- | :--- |
| **Task 1: Real-Time Serving** | FastAPI endpoints, Redis/In-memory caching (< 100ms target), in-session click streams | • 10 REST endpoints (`/recommendations`, `/similar`, `/bought-together`, `/search`, `/assistant/chat`, `/forecast`, `/inventory/alerts`, `/reviews/summary`, `/events/click`, `/health`)<br>• Serving latency: **1.2 ms (Cached) / 28 ms (Cold Compute)** (Target < 100 ms)<br>• Real-time in-session click ingestion updating recommendation feed instantly | ✅ Complete |
| **Task 2: A/B Testing** | Power analysis, 50k traffic simulation, CVR/RPV hypothesis testing, Ship report | • Power analysis: 17,050 users/variant (34,100 total), 14 days<br>• CVR lift: **+21.1%** ($p = 1.95 \times 10^{-6}$); RPV lift: **+36.4%** ($p = 1.54 \times 10^{-11}$)<br>• Cart abandonment reduced from 65.0% to 54.0%; Complaint rate stable at 1.9%<br>• Executive Decision: **`SHIP TO 100% PRODUCTION`** ([`reports/ab_test_report.md`](file:///c:/Users/MEE/Anti-Gravity_projects/AI_E-Commerce_Intelligence_Platform/reports/ab_test_report.md)) | ✅ Complete |
| **Task 3: Dashboard & Deployment** | Single-page HTML/CSS/JS dashboard, Dockerfile, docker-compose, CI workflow | • Modern, responsive HTML5/CSS3/JS dashboard (`dashboard/index.html`) with Customer, Operations, and Management tabs<br>• Multi-stage `Dockerfile`, `docker-compose.yml` (API, Redis, DB volume), `.env.example`, and `.github/workflows/ci.yml` CI pipeline | ✅ Complete |
| **Task 4: Stakeholder Demo** | 10-Minute CEO live walkthrough script & executive slide deck | • Executive live demo script (`src/demo/run_demo.py`) executing 8 core workflows<br>• 10-slide executive presentation deck ([`reports/stakeholder_presentation.md`](file:///c:/Users/MEE/Anti-Gravity_projects/AI_E-Commerce_Intelligence_Platform/reports/stakeholder_presentation.md))<br>• Projected commercial impact: **+Rs. 1.15 Billion PKR** annualized revenue uplift | ✅ Complete |
| **Task 5: Documentation & Handover** | Model cards, user guides, future roadmap, minimum targets audit | • Google/Mitchell specification model cards ([`reports/model_cards.md`](file:///c:/Users/MEE/Anti-Gravity_projects/AI_E-Commerce_Intelligence_Platform/reports/model_cards.md))<br>• Operational guides for Marketing, Operations, and Management ([`reports/user_guides.md`](file:///c:/Users/MEE/Anti-Gravity_projects/AI_E-Commerce_Intelligence_Platform/reports/user_guides.md))<br>• 100% pass across all Capstone minimum targets | ✅ Complete |

---

## 🚀 How to Run

### Day 1 Pipeline: Data Foundation & Analytics
```bash
.venv\Scripts\python.exe main_day1.py
```

### Day 2 Pipeline: Recommendation Engine
```bash
.venv\Scripts\python.exe main_day2.py
```

### Day 3 Pipeline: Demand Forecasting & Inventory Intelligence
```bash
.venv\Scripts\python.exe main_day3.py
```

### Day 4 Pipeline: Smart Search, Shopping Assistant & Review Intelligence
```bash
.venv\Scripts\python.exe main_day4.py
```

### Day 5 (Capstone): Full Verification Suite
```bash
.venv\Scripts\python.exe main_day5.py
```

### Executive 10-Minute Stakeholder Demonstration
```bash
.venv\Scripts\python.exe src/demo/run_demo.py
```

### Launch the Live Production Serving Server & Dashboard
```bash
.venv\Scripts\python.exe -m uvicorn src.serving.api:app --host 0.0.0.0 --port 8000
```
*Open **`http://localhost:8000/`** in your browser to interact with the full Customer, Operations, and Management platform.*

---

## 🐳 Running with Docker & Redis

```bash
docker-compose up --build
```
*Spins up the FastAPI serving API on port 8000, Redis cache on port 6379, and mounts persistent database volumes with automated health checks.*

---

## ☁️ Deploying to Render (Cloud Hosting)

The platform includes [`render.yaml`](file:///c:/Users/MEE/Anti-Gravity_projects/AI_E-Commerce_Intelligence_Platform/render.yaml) and [`Dockerfile`](file:///c:/Users/MEE/Anti-Gravity_projects/AI_E-Commerce_Intelligence_Platform/Dockerfile) pre-configured for 1-click cloud deployment on [Render.com](https://render.com):

1. Push this repository to GitHub.
2. In the Render Dashboard, select **New +** $\to$ **Web Service**.
3. Connect your GitHub repository and select **Runtime: Docker**.
4. Set **Health Check Path** to `/health` and deploy!
*(See [`reports/render_deployment_guide.md`](file:///c:/Users/MEE/Anti-Gravity_projects/AI_E-Commerce_Intelligence_Platform/reports/render_deployment_guide.md) for full step-by-step instructions).*

---

## 🐘 Optional: Exporting Data to PostgreSQL

If you wish to mirror all 12 analytical tables from DuckDB into your local or cloud PostgreSQL instance:

```bash
# Export using default credentials (localhost:5432, user: postgres, db: shopkaro)
.venv\Scripts\python.exe src\data_pipeline\postgres_exporter.py

# Or specify custom credentials directly via CLI flags:
.venv\Scripts\python.exe src\data_pipeline\postgres_exporter.py --host localhost --port 5432 --user postgres --password YOUR_PASSWORD --db shopkaro
```
*(The script automatically verifies if the `shopkaro` database exists, creates it if missing, migrates all 12 tables in batches, and indexes key columns for high-speed queries).*

