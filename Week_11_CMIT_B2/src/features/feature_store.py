"""
Feature Engineering & Chronological Dataset Splitting Module
Implements Task 5:
1. User Features (RFM segment, AOV, lifetime spend, favourite category, cart conversion rate)
2. Item Features (category, brand, price band, popularity score, conversion rate, text representation)
3. Chronological Time-Based Split (Train 80% / Val 10% / Test 10%)
4. Isolated Cold-Start Test Sets (Cold Users & Cold Items)
5. Comprehensive documentation on why random splits cause temporal leakage in recommender systems
"""

import os
import duckdb
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "processed", "shopkaro.duckdb")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
SPLITS_DIR = os.path.join(PROCESSED_DIR, "splits")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
os.makedirs(SPLITS_DIR, exist_ok=True)

def build_features_and_splits():
    print("="*60)
    print("RUNNING SHOPKARO FEATURE ENGINEERING & SPLITS (TASK 5)")
    print("="*60)
    
    con = duckdb.connect(DB_PATH)
    ref_date = "2025-12-31"
    
    # ---------------------------------------------------------
    # 1. USER FEATURES TABLE
    # ---------------------------------------------------------
    print("1. Engineering User Features...")
    user_feat_query = f"""
    WITH user_fav_cat AS (
        SELECT 
            e.user_id,
            p.category as favourite_category,
            ROW_NUMBER() OVER(PARTITION BY e.user_id ORDER BY COUNT(*) DESC) as rn
        FROM events e
        JOIN products p ON e.product_id = p.product_id
        GROUP BY e.user_id, p.category
    ),
    user_event_stats AS (
        SELECT 
            user_id,
            COUNT(*) as total_events,
            SUM(CASE WHEN event_type = 'view' THEN 1 ELSE 0 END) as total_views,
            SUM(CASE WHEN event_type = 'add_to_cart' THEN 1 ELSE 0 END) as total_carts,
            SUM(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) as total_purchases,
            MAX(timestamp) as last_interaction_ts
        FROM events
        GROUP BY user_id
    )
    SELECT 
        u.user_id,
        um.user_int_id,
        u.full_name,
        u.city,
        u.preferred_payment,
        u.device_preference,
        COALESCE(us.segment_name, 'Occasional Window Shoppers') as segment_name,
        COALESCE(us.monetary_pkr, 0) as lifetime_spend_pkr,
        COALESCE(us.frequency, 0) as total_completed_orders,
        COALESCE(us.avg_order_value_pkr, 0) as avg_order_value_pkr,
        COALESCE(fc.favourite_category, 'General') as favourite_category,
        COALESCE(ues.total_views, 0) as total_views,
        COALESCE(ues.total_carts, 0) as total_carts,
        COALESCE(ues.total_purchases, 0) as total_purchases,
        ROUND(COALESCE(ues.total_purchases * 1.0 / NULLIF(ues.total_carts, 0), 0), 4) as cart_conversion_rate,
        COALESCE(DATEDIFF('day', ues.last_interaction_ts, DATE '{ref_date}'), 365) as last_active_days_ago
    FROM users u
    JOIN user_mapping um ON u.user_id = um.user_id
    LEFT JOIN user_segments us ON u.user_id = us.user_id
    LEFT JOIN (SELECT user_id, favourite_category FROM user_fav_cat WHERE rn = 1) fc ON u.user_id = fc.user_id
    LEFT JOIN user_event_stats ues ON u.user_id = ues.user_id
    """
    
    df_user_features = con.execute(user_feat_query).fetchdf()
    df_user_features.to_parquet(os.path.join(PROCESSED_DIR, "user_features.parquet"), index=False)
    print(f"User features built: {len(df_user_features):,} users.")
    
    # ---------------------------------------------------------
    # 2. ITEM FEATURES TABLE
    # ---------------------------------------------------------
    print("2. Engineering Item Features...")
    item_feat_query = """
    WITH item_event_stats AS (
        SELECT 
            product_id,
            COUNT(*) as total_events,
            SUM(CASE WHEN event_type = 'view' THEN 1 ELSE 0 END) as view_count,
            SUM(CASE WHEN event_type = 'add_to_cart' THEN 1 ELSE 0 END) as cart_count,
            SUM(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) as purchase_count
        FROM events
        GROUP BY product_id
    )
    SELECT 
        p.product_id,
        im.item_int_id,
        p.sku,
        p.title,
        p.category,
        p.subcategory,
        p.brand,
        p.price_pkr,
        p.cost_pkr,
        ROUND((p.price_pkr - p.cost_pkr) * 1.0 / NULLIF(p.price_pkr, 0), 4) as gross_margin_rate,
        p.price_tier as price_band,
        p.stock_quantity,
        p.rating_avg,
        COALESCE(ies.view_count, 0) as view_count,
        COALESCE(ies.cart_count, 0) as cart_count,
        COALESCE(ies.purchase_count, 0) as purchase_count,
        ROUND(COALESCE(ies.purchase_count * 1.0 / NULLIF(ies.view_count, 0), 0), 4) as conversion_rate,
        -- Continuous Popularity Score: ln(1 + views) + 2*ln(1 + carts) + 5*ln(1 + purchases)
        ROUND(
            LN(1 + COALESCE(ies.view_count, 0)) + 
            2.0 * LN(1 + COALESCE(ies.cart_count, 0)) + 
            5.0 * LN(1 + COALESCE(ies.purchase_count, 0)), 
            4
        ) as popularity_score,
        -- Rich text representation ready for text embeddings (Sentence-Transformers / BGE-M3)
        p.brand || ' ' || p.title || '. Category: ' || p.category || ' > ' || p.subcategory || 
        '. Price: PKR ' || CAST(p.price_pkr AS VARCHAR) || '. Tier: ' || p.price_tier || 
        '. Description: ' || p.description as text_representation
    FROM products p
    JOIN item_mapping im ON p.product_id = im.product_id
    LEFT JOIN item_event_stats ies ON p.product_id = ies.product_id
    """
    
    df_item_features = con.execute(item_feat_query).fetchdf()
    df_item_features.to_parquet(os.path.join(PROCESSED_DIR, "item_features.parquet"), index=False)
    print(f"Item features built: {len(df_item_features):,} items.")
    
    # Ingest into DuckDB
    con.execute("DROP TABLE IF EXISTS user_features")
    con.execute("CREATE TABLE user_features AS SELECT * FROM df_user_features")
    con.execute("DROP TABLE IF EXISTS item_features")
    con.execute("CREATE TABLE item_features AS SELECT * FROM df_item_features")
    
    # ---------------------------------------------------------
    # 3. TIME-BASED CHRONOLOGICAL DATASET SPLIT (80% / 10% / 10%)
    # ---------------------------------------------------------
    print("3. Implementing Time-Based Chronological Splits (80/10/10)...")
    
    df_events = con.execute("SELECT * FROM events ORDER BY timestamp ASC").fetchdf()
    total_events = len(df_events)
    
    # Find timestamp split boundaries
    train_idx = int(total_events * 0.80)
    val_idx = int(total_events * 0.90)
    
    train_cutoff_ts = df_events.iloc[train_idx]["timestamp"]
    val_cutoff_ts = df_events.iloc[val_idx]["timestamp"]
    
    print(f"Chronological Cutoffs:")
    print(f" - Train Window:      {df_events['timestamp'].min()} to {train_cutoff_ts}")
    print(f" - Validation Window: {train_cutoff_ts} to {val_cutoff_ts}")
    print(f" - Test Window:       {val_cutoff_ts} to {df_events['timestamp'].max()}")
    
    df_train = df_events.iloc[:train_idx].copy()
    df_val = df_events.iloc[train_idx:val_idx].copy()
    df_test = df_events.iloc[val_idx:].copy()
    
    df_train.to_parquet(os.path.join(SPLITS_DIR, "train.parquet"), index=False)
    df_val.to_parquet(os.path.join(SPLITS_DIR, "val.parquet"), index=False)
    df_test.to_parquet(os.path.join(SPLITS_DIR, "test.parquet"), index=False)
    
    print(f"Splits saved:")
    print(f" - Train set:      {len(df_train):,} events (80.0%)")
    print(f" - Validation set: {len(df_val):,} events (10.0%)")
    print(f" - Test set:       {len(df_test):,} events (10.0%)")
    
    # ---------------------------------------------------------
    # 4. COLD-START TEST SETS (New Users & New Items)
    # ---------------------------------------------------------
    print("4. Isolating Cold-Start Test Sets...")
    
    train_users = set(df_train["user_id"].unique())
    train_items = set(df_train["product_id"].unique())
    
    # Cold users: Users appearing in test set who had zero interactions in train
    cold_user_events = df_test[~df_test["user_id"].isin(train_users)].copy()
    n_cold_users = cold_user_events["user_id"].nunique()
    cold_user_events.to_parquet(os.path.join(SPLITS_DIR, "test_cold_users.parquet"), index=False)
    
    # Cold items: Products appearing in test set who had zero interactions in train
    cold_item_events = df_test[~df_test["product_id"].isin(train_items)].copy()
    n_cold_items = cold_item_events["product_id"].nunique()
    cold_item_events.to_parquet(os.path.join(SPLITS_DIR, "test_cold_items.parquet"), index=False)
    
    print(f"Cold-Start Test Sets:")
    print(f" - Cold-start Users set: {len(cold_user_events):,} interactions from {n_cold_users:,} unseen users.")
    print(f" - Cold-start Items set: {len(cold_item_events):,} interactions for {n_cold_items:,} unseen products.")
    
    con.close()
    
    # ---------------------------------------------------------
    # 5. DOCUMENTATION: WHY NEVER RANDOM SPLIT IN RECOMMENDERS
    # ---------------------------------------------------------
    generate_splits_report(
        train_events=len(df_train),
        val_events=len(df_val),
        test_events=len(df_test),
        train_cutoff=train_cutoff_ts,
        val_cutoff=val_cutoff_ts,
        n_cold_users=n_cold_users,
        n_cold_items=n_cold_items,
        cold_user_events=len(cold_user_events),
        cold_item_events=len(cold_item_events)
    )
    
    print("\n[SUCCESS] Task 5 complete. Feature tables, chronological splits, and cold-start sets generated.")

def generate_splits_report(
    train_events: int,
    val_events: int,
    test_events: int,
    train_cutoff,
    val_cutoff,
    n_cold_users: int,
    n_cold_items: int,
    cold_user_events: int,
    cold_item_events: int
):
    report_path = os.path.join(REPORTS_DIR, "feature_store_and_splits.md")
    
    md = f"""# ShopKaro Feature Engineering & Dataset Splitting Strategy

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
    $$\\text{{Popularity}} = \\ln(1 + \\text{{views}}) + 2 \\cdot \\ln(1 + \\text{{carts}}) + 5 \\cdot \\ln(1 + \\text{{purchases}})$$
- **Multilingual Semantic Text Representation:**
  - `text_representation`: Clean standardized text embedding prompt incorporating brand, title, category hierarchy, price tier, and product description ready for Sentence-Transformers, BGE-M3, and CLIP embeddings.

---

## 2. Dataset Splitting Methodology

| Partition | Time Interval | Total Events | Share (%) | Intended Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **Train Set** | 2024-01-01 to {train_cutoff} | **{train_events:,}** | **80.0%** | Model training (collaborative filtering, demand forecasting, ranking) |
| **Validation Set** | {train_cutoff} to {val_cutoff} | **{val_events:,}** | **10.0%** | Hyperparameter tuning, early stopping, threshold calibration |
| **Test Set** | {val_cutoff} to 2025-12-31 | **{test_events:,}** | **10.0%** | Final offline evaluation (Hit@K, NDCG@K, MRR, WAPE) |

---

## 3. Critical Theoretical Imperative: Why NEVER Random Split for Recommendations?

In classical tabular classification (e.g. predicting churn or loan default), random $k$-fold cross-validation is standard. However, **in Recommender Systems and E-Commerce Intelligence, applying a random split is a catastrophic methodology flaw**.

### The Three Reasons Random Split Destroys Recommendation Models:

1. **Catastrophic Temporal Data Leakage ("Future Leaking to Past"):**
   - In production, a recommender system deployed on October 1st can only observe user actions that occurred **before** October 1st.
   - If interactions are randomly shuffled, the training set will contain an item user $U$ bought on November 20th, while the test set attempts to evaluate what to recommend to user $U$ on September 15th.
   - The model learns to "cheat" using future knowledge, producing artificially astronomical offline scores (e.g., $NDCG@10 > 0.65$) that immediately crash when deployed live to production.

2. **User Trajectory Disruption & Lookahead Bias:**
   - E-commerce user behavior is sequential: `view item A` $\to$ `view item B` $\to$ `add item B to cart` $\to$ `purchase item B`.
   - A random split fragments this causal chain, training on the purchase while testing on the prior view. Real recommendation requires predicting **future unobserved actions given historical context**.

3. **Festival Seasonality & Concept Drift:**
   - Pakistani retail experiences dramatic seasonal regime shifts: Ramadan/Eid in Spring, Azadi in August, 11.11 and Blessed Friday in November.
   - A random split averages out these seasonal shocks across train and test, blinding the model to temporal non-stationarity. Chronological splitting forces models to prove they can generalize forward in time across festive spikes.

---

## 4. Cold-Start Evaluation Benchmarks

A real-world production engine must gracefully handle users and products with zero training history. We explicitly carved out two dedicated benchmark test sets from the test window:

| Benchmark | Test Events | Unseen Entities | Evaluation Objective |
| :--- | :--- | :--- | :--- |
| **Cold-Start Users** (`test_cold_users.parquet`) | **{cold_user_events:,}** | **{n_cold_users:,}** new users | Measures demographic priors, trending fallback, and rapid in-session adaptation without user CF history. |
| **Cold-Start Items** (`test_cold_items.parquet`) | **{cold_item_events:,}** | **{n_cold_items:,}** new products | Evaluates content-based semantic matching and text embeddings for novel catalogue arrivals without collaborative ratings. |
"""
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(md)

if __name__ == "__main__":
    build_features_and_splits()
