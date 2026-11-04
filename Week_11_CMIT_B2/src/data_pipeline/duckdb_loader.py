"""
DuckDB Loader & Schema Builder
Orchestrates:
1. Event cleaning (cleaner.py)
2. Sessionization with 30-min rule (sessionizer.py)
3. Contiguous Integer ID mapping for Users and Items
4. Orders generation from purchases (with real PKR prices)
5. DuckDB persistent database ingestion (shopkaro.duckdb)
6. Parquet exports for rapid analytics
"""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
import duckdb
import pandas as pd
import numpy as np
from cleaner import clean_events
from sessionizer import build_sessions

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
DB_PATH = os.path.join(PROCESSED_DIR, "shopkaro.duckdb")

def create_id_mappings(df_users: pd.DataFrame, df_prod: pd.DataFrame):
    """
    Creates contiguous 0-indexed integer IDs for users and items.
    Essential for Matrix Factorization (ALS/BPR) and Neural Two-Tower embeddings.
    """
    print("Generating contiguous user and item ID mappings...")
    
    # User ID mapping
    user_map = pd.DataFrame({
        "user_id": df_users["user_id"].unique()
    }).reset_index().rename(columns={"index": "user_int_id"})
    
    # Item ID mapping
    item_map = pd.DataFrame({
        "product_id": df_prod["product_id"].unique()
    }).reset_index().rename(columns={"index": "item_int_id"})
    
    user_map.to_parquet(os.path.join(PROCESSED_DIR, "user_mapping.parquet"), index=False)
    item_map.to_parquet(os.path.join(PROCESSED_DIR, "item_mapping.parquet"), index=False)
    
    print(f"Mapped {len(user_map):,} users and {len(item_map):,} products to integer IDs.")
    return user_map, item_map

def generate_orders_from_purchases(df_events: pd.DataFrame, df_prod: pd.DataFrame) -> pd.DataFrame:
    """
    Constructs an Orders & Order Items table from purchase events.
    """
    print("Constructing orders table from purchase events...")
    purchases = df_events[df_events["event_type"] == "purchase"].copy()
    
    # Merge price
    purchases = purchases.merge(df_prod[["product_id", "price_pkr", "cost_pkr", "category"]], on="product_id", how="left")
    
    # Each session purchase event can be part of an order
    purchases["quantity"] = np.random.choice([1, 2, 3, 4], size=len(purchases), p=[0.75, 0.18, 0.05, 0.02])
    purchases["item_total_pkr"] = purchases["quantity"] * purchases["price_pkr"]
    purchases["item_margin_pkr"] = purchases["quantity"] * (purchases["price_pkr"] - purchases["cost_pkr"])
    
    # Group by session_id to form distinct orders
    order_groups = purchases.groupby("session_id").agg(
        user_id=("user_id", "first"),
        order_date=("timestamp", "first"),
        total_items=("quantity", "sum"),
        order_total_pkr=("item_total_pkr", "sum"),
        order_margin_pkr=("item_margin_pkr", "sum"),
        item_ids=("product_id", lambda x: list(x))
    ).reset_index()
    
    order_groups["order_id"] = [f"ORD-{i+1:07d}" for i in range(len(order_groups))]
    order_groups["payment_status"] = "Completed"
    order_groups["shipping_method"] = np.random.choice(
        ["Standard Courier (Trax/TCS)", "Express Delivery (Lahore/Karachi)", "Postal Service"],
        size=len(order_groups),
        p=[0.70, 0.25, 0.05]
    )
    
    print(f"Generated {len(order_groups):,} completed orders totaling Rs. {order_groups['order_total_pkr'].sum():,}.")
    return order_groups

def load_all_to_duckdb():
    """
    Main orchestration function to clean, process, and load everything into DuckDB.
    """
    print("="*60)
    print("STARTING SHOPKARO DUCKDB DATA PIPELINE")
    print("="*60)
    
    # 1. Clean events
    df_clean_events, audit_stats = clean_events(os.path.join(RAW_DIR, "events_raw.csv"))
    
    # 2. Build sessions
    df_clean_events, df_sessions = build_sessions(df_clean_events)
    
    # 3. Load base metadata tables
    print("Loading base CSVs...")
    df_users = pd.read_csv(os.path.join(RAW_DIR, "users.csv"))
    df_prod = pd.read_csv(os.path.join(RAW_DIR, "products.csv"))
    df_cal = pd.read_csv(os.path.join(RAW_DIR, "calendar.csv"))
    df_rev = pd.read_csv(os.path.join(RAW_DIR, "reviews.csv"))
    
    # 4. Generate user & item integer mappings
    user_map, item_map = create_id_mappings(df_users, df_prod)
    
    # Add integer IDs to events
    df_clean_events = df_clean_events.merge(user_map, on="user_id", how="left")
    df_clean_events = df_clean_events.merge(item_map, on="product_id", how="left")
    
    # 5. Build orders
    df_orders = generate_orders_from_purchases(df_clean_events, df_prod)
    
    # 6. Save Parquet tables
    print("Exporting processed tables to Parquet...")
    df_clean_events.to_parquet(os.path.join(PROCESSED_DIR, "events_cleaned.parquet"), index=False)
    df_sessions.to_parquet(os.path.join(PROCESSED_DIR, "sessions.parquet"), index=False)
    df_users.to_parquet(os.path.join(PROCESSED_DIR, "users.parquet"), index=False)
    df_prod.to_parquet(os.path.join(PROCESSED_DIR, "products.parquet"), index=False)
    df_cal.to_parquet(os.path.join(PROCESSED_DIR, "calendar.parquet"), index=False)
    df_rev.to_parquet(os.path.join(PROCESSED_DIR, "reviews.parquet"), index=False)
    
    # Order items representation (string list for parquet compatibility)
    df_orders_to_save = df_orders.copy()
    df_orders_to_save["item_ids"] = df_orders_to_save["item_ids"].apply(lambda l: ",".join(l))
    df_orders_to_save.to_parquet(os.path.join(PROCESSED_DIR, "orders.parquet"), index=False)
    
    # 7. Ingest into DuckDB
    print(f"Connecting to DuckDB database at: {DB_PATH}")
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
        except Exception:
            pass
            
    con = duckdb.connect(DB_PATH)
    
    print("Creating tables in DuckDB...")
    con.execute("CREATE TABLE users AS SELECT * FROM df_users")
    con.execute("CREATE TABLE products AS SELECT * FROM df_prod")
    con.execute("CREATE TABLE calendar AS SELECT * FROM df_cal")
    con.execute("CREATE TABLE events AS SELECT * FROM df_clean_events")
    con.execute("CREATE TABLE sessions AS SELECT * FROM df_sessions")
    con.execute("CREATE TABLE orders AS SELECT * FROM df_orders_to_save")
    con.execute("CREATE TABLE reviews AS SELECT * FROM df_rev")
    con.execute("CREATE TABLE user_mapping AS SELECT * FROM user_map")
    con.execute("CREATE TABLE item_mapping AS SELECT * FROM item_map")
    
    # Create indexes for speed
    print("Creating indexes on key analytical columns...")
    con.execute("CREATE INDEX idx_events_user ON events(user_id)")
    con.execute("CREATE INDEX idx_events_product ON events(product_id)")
    con.execute("CREATE INDEX idx_events_timestamp ON events(timestamp)")
    con.execute("CREATE INDEX idx_orders_user ON orders(user_id)")
    con.execute("CREATE INDEX idx_reviews_product ON reviews(product_id)")
    
    # Verify counts
    tables = ["users", "products", "calendar", "events", "sessions", "orders", "reviews", "user_mapping", "item_mapping"]
    print("\nDuckDB Table Verification:")
    for t in tables:
        count = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f" - {t:15s}: {count:>10,} rows")
        
    con.close()
    print("\n[SUCCESS] DuckDB data foundation initialized successfully.")
    return audit_stats

if __name__ == "__main__":
    load_all_to_duckdb()
