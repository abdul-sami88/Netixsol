# ShopKaro Feature Engineering & Dataset Splitting Strategy

This document details the engineered feature stores for users and items, the chronological time-based dataset splitting methodology, and the isolated cold-start evaluation benchmarks.

---

## 1. Feature Store Overview

### User Feature Store (`data/processed/user_features.parquet`)
- **Key Identifiers:** `user_id` (string), `user_int_id` (contiguous integer for matrix factorization)
- **Demographics & Profile:** `full_name`, `city`, `preferred_payment`, `device_preference`
- **Behavioral Persona:** `segment_name` ("Eid Shoppers", "Loyal Tech Buyers", "Bargain Hunters", etc.)
- **Monetary & Engagement Signals:**
  - `lifetime_spend_pkr`: Total historical GMV spend
  - `total_completed_orders`: Order frequency
  - `avg_order_value_pkr`: Mean basket checkout size
  - `favourite_category`: Most frequently interacted/purchased product department
  - `total_views`, `total_carts`, `total_purchases`
  - `cart_conversion_rate`: Add-to-cart to purchase conversion ratio
  - `last_active_days_ago`: Inactivity recency counter

### Item Feature Store (`data/processed/item_features.parquet`)
- **Key Identifiers:** `product_id` (string), `item_int_id` (contiguous integer)
- **Catalogue Metadata:** `sku`, `title`, `brand`, `category`, `subcategory`
- **Economics:** `price_pkr`, `cost_pkr`, `gross_margin_rate`, `price_band` (Budget, Mid-Range, Premium, Luxury)
- **Inventory & Quality:** `stock_quantity`, `rating_avg`
- **Popularity Signals:**
  - `view_count`, `cart_count`, `purchase_count`
  - `conversion_rate`: View-to-purchase efficiency
  - `popularity_score`: Continuous log-weighted engagement score:
    $$\text{Popularity} = \ln(1 + \text{views}) + 2 \cdot \ln(1 + \text{carts}) + 5 \cdot \ln(1 + \text{purchases})$$
- **Multilingual Semantic Text Representation:**
  - `text_representation`: Clean standardized text embedding prompt incorporating brand, title, category hierarchy, price tier, and product description ready for Sentence-Transformers, BGE-M3, and CLIP embeddings.

---

## 2. Dataset Splitting Methodology

| Partition | Time Interval | Total Events | Share (%) | Intended Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **Train Set** | 2024-01-01 to 2025-08-18 12:06:34 | **424,281** | **80.0%** | Model training (collaborative filtering, demand forecasting, ranking) |
| **Validation Set** | 2025-08-18 12:06:34 to 2025-11-08 11:44:09 | **53,035** | **10.0%** | Hyperparameter tuning, early stopping, threshold calibration |
| **Test Set** | 2025-11-08 11:44:09 to 2025-12-31 | **53,036** | **10.0%** | Final offline evaluation (Hit@K, NDCG@K, MRR, WAPE) |

---

## 3. Critical Theoretical Imperative: Why NEVER Random Split for Recommendations?

In classical tabular classification (e.g. predicting churn or loan default), random $k$-fold cross-validation is standard. However, **in Recommender Systems and E-Commerce Intelligence, applying a random split is a catastrophic methodology flaw**.

### The Three Reasons Random Split Destroys Recommendation Models:

1. **Catastrophic Temporal Data Leakage ("Future Leaking to Past"):**
   - In production, a recommender system deployed on October 1st can only observe user actions that occurred **before** October 1st.
   - If interactions are randomly shuffled, the training set will contain an item user $U$ bought on November 20th, while the test set attempts to evaluate what to recommend to user $U$ on September 15th.
   - The model learns to "cheat" using future knowledge, producing artificially astronomical offline scores (e.g., $NDCG@10 > 0.65$) that immediately crash when deployed live to production.

2. **User Trajectory Disruption & Lookahead Bias:**
   - E-commerce user behavior is sequential: `view item A` $	o$ `view item B` $	o$ `add item B to cart` $	o$ `purchase item B`.
   - A random split fragments this causal chain, training on the purchase while testing on the prior view. Real recommendation requires predicting **future unobserved actions given historical context**.

3. **Festival Seasonality & Concept Drift:**
   - Pakistani retail experiences dramatic seasonal regime shifts: Ramadan/Eid in Spring, Azadi in August, 11.11 and Blessed Friday in November.
   - A random split averages out these seasonal shocks across train and test, blinding the model to temporal non-stationarity. Chronological splitting forces models to prove they can generalize forward in time across festive spikes.

---

## 4. Cold-Start Evaluation Benchmarks

A real-world production engine must gracefully handle users and products with zero training history. We explicitly carved out two dedicated benchmark test sets from the test window:

| Benchmark | Test Events | Unseen Entities | Evaluation Objective |
| :--- | :--- | :--- | :--- |
| **Cold-Start Users** (`test_cold_users.parquet`) | **13** | **11** new users | Measures demographic priors, trending fallback, and rapid in-session adaptation without user CF history. |
| **Cold-Start Items** (`test_cold_items.parquet`) | **1,344** | **1,284** new products | Evaluates content-based semantic matching and text embeddings for novel catalogue arrivals without collaborative ratings. |
