# 📋 ShopKaro Production Model Cards
**Document Version:** 1.0.0  
**Compliance Standard:** Google / Mitchell et al. Model Card Specifications  
**Environment:** ShopKaro Production AI Infrastructure  

---

## 1. 🛍️ Model Card: Recommender Engine (Two-Tower PyTorch + ALS + Re-Ranker)

### Model Details
* **Developer:** ShopKaro AI Engineering Team
* **Model Type:** Hybrid Two-Tower Deep Neural Network + Hu-Koren-Volinsky Implicit Alternating Least Squares (ALS) + Business Rule Re-Ranking Layer.
* **Release Date:** November 2026.
* **Input Features:** 
  * *User Tower:* User ID embedding, historical category affinity distribution, Average Order Value (AOV), RFM Persona cluster.
  * *Item Tower:* Item ID embedding, title sublinear TF-IDF text features, price tier, category, brand, profit margin.
* **Output:** Ranked vector of top-K product recommendations with transparent Roman Urdu explanations.

### Intended Use
* **Primary Use Case:** Real-time homepage "Recommended for You" feed, cart cross-sells, and post-checkout bundles.
* **Out-of-Scope Uses:** Autonomous dynamic re-pricing without human guardrails.

### Performance & Evaluation
* **Offline Ranking Metrics:**
  * NDCG@10: 0.1249 (Collaborative) | Hit Rate: 0.7273 on Cold-Start Users.
  * Catalog Coverage: 88.7% (eliminating extreme bestseller star bias).
* **Online Serving Latency:** 
  * In-Memory / Redis Cached: **1.2 ms**
  * Cold Real-time Compute: **28 ms** (Target: < 100 ms).
* **Online Business Lift (A/B Test EXP-2026-REC-001):**
  * **+21.1% Conversion Rate (CVR)** ($p < 0.001$)
  * **+36.4% Revenue Per Visitor (RPV)** ($p < 0.001$)

### Ethical Considerations & Guardrails
* **Fairness:** Maximum of 2 items per brand per recommendation slate to prevent vendor monopolies.
* **Stock Guardrail:** Out-of-stock items ($stock \le 0$) strictly purged prior to serving.

---

## 2. 📈 Model Card: Demand Forecaster (Global LightGBM + Custom Prophet)

### Model Details
* **Developer:** ShopKaro Supply Chain & Forecasting Team
* **Model Type:** Multi-Quantile Gradient Boosted Trees (LightGBM) + Additive Holiday-Adjusted Prophet.
* **Input Features:** 
  * Lagged demand ($t-1, t-7, t-14, t-28$), rolling means, standard deviations, min/max windows.
  * Moving Islamic festival calendars (Eid-ul-Fitr, Eid-ul-Adha, Ramadan, 11.11, Blessed Friday).
  * Day of week, month, day of month sinusoidal encodings.
* **Output:** Point forecasts (P50 Median) and prediction intervals (P10 Conservative, P90 Festival Surge).

### Performance & Evaluation
* **Metrics:** 
  * Weighted Absolute Percentage Error (WAPE): **27.3% (Prophet)** and **28.4% (LightGBM)**, substantially outperforming Seasonal Naive (47.1% WAPE) and Naive (66.0% WAPE).
  * **P90 Calibration Coverage:** Reality fell below P90 forecast **92.1% of the time** on unseen test periods (Target: 90%).

### Intended Actionable Outputs
* Dynamic Safety Stock ($SS$) and Reorder Points ($ROP$).
* 14-day stockout alerts (prevented 3,724 stockouts, protecting Rs. 131.3M GMV).
* Dead capital overstock liquidation tags (40,266 SKUs flagged for markdown).

---

## 3. 💬 Model Card: Review Intelligence & Multilingual ABSA Engine

### Model Details
* **Developer:** ShopKaro Trust & Safety Team
* **Model Type:** Hybrid Lexical-Semantic Aspect-Based Sentiment Analysis (ABSA) + Non-Negative Matrix Factorization (NMF) + Heuristic Fraud Burst Detector.
* **Languages Supported:** English, Roman Urdu (Urdu written in Latin script), and Urdu script.
* **Aspects Evaluated:** 
  1. Quality & Fabric Durability
  2. Price & Value for Money
  3. Delivery & Courier Performance
  4. Size & Fit Accuracy
  5. Packaging & Transit Condition
  6. Seller & Customer Support Behaviour

### Performance & Limitations
* **Accuracy:** 91.4% classification alignment on annotated multilingual customer feedback.
* **Spam Detection:** Effectively flags repetitive copy-paste astroturfing, sudden velocity bursts (>3 reviews/day on single SKU), and severe rating-sentiment dissonance (5-star with "fazool/kharab").

