"""
Session Building Module (High-Performance Vectorized)
Implements the 30-minute inactivity rule for sessionization:
Events occurring within 30 minutes of a previous user action belong to the same session.
If inactivity > 30 minutes occurs, a new session is started.
"""

import os
from typing import Tuple
import pandas as pd
import numpy as np

PROCESSED_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "processed")

def build_sessions(df_events: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Groups cleaned events into sessions using the 30-minute inactivity rule.
    Ultra-fast vectorized implementation for 600k+ rows.
    """
    print("Building sessions based on 30-minute inactivity rule (vectorized)...")
    # 1. Sort strictly by user_id and timestamp
    df = df_events.sort_values(by=["user_id", "timestamp"]).reset_index(drop=True)
    
    # 2. Vectorized consecutive differences
    is_new_user = (df["user_id"] != df["user_id"].shift(1))
    time_diff_sec = (df["timestamp"] - df["timestamp"].shift(1)).dt.total_seconds()
    
    # 3. New session condition: changed user OR time gap > 30 min (1800s) OR first row
    is_new_session = is_new_user | (time_diff_sec > 1800) | (time_diff_sec.isna())
    
    # Cumulative sum assigns an integer session ID to every event
    session_int_id = is_new_session.cumsum()
    df["session_id"] = "SES-" + session_int_id.astype(str)
    
    # Pre-encode indicator columns for instant C-speed aggregation
    df["is_view"] = (df["event_type"] == "view").astype(np.int32)
    df["is_cart"] = (df["event_type"] == "add_to_cart").astype(np.int32)
    df["is_purchase"] = (df["event_type"] == "purchase").astype(np.int32)
    
    print("Aggregating session metrics...")
    session_agg = df.groupby("session_id", as_index=False).agg(
        user_id=("user_id", "first"),
        session_start=("timestamp", "min"),
        session_end=("timestamp", "max"),
        event_count=("event_id", "count"),
        views_count=("is_view", "sum"),
        carts_count=("is_cart", "sum"),
        purchases_count=("is_purchase", "sum"),
        unique_items_interacted=("product_id", "nunique")
    )
    
    session_agg["duration_minutes"] = (
        (session_agg["session_end"] - session_agg["session_start"]).dt.total_seconds() / 60.0
    ).round(2)
    session_agg["is_converted"] = session_agg["purchases_count"] > 0
    
    # Cleanup temporary indicators
    df.drop(columns=["is_view", "is_cart", "is_purchase"], inplace=True)
    
    print(f"Total sessions built: {len(session_agg):,}")
    print(f"Converted sessions: {session_agg['is_converted'].sum():,} ({(session_agg['is_converted'].mean()*100):.2f}%)")
    
    return df, session_agg

if __name__ == "__main__":
    cleaned_path = os.path.join(PROCESSED_DIR, "events_cleaned.parquet")
    df_clean = pd.read_parquet(cleaned_path)
    df_events_sessioned, df_sessions = build_sessions(df_clean)
    
    df_events_sessioned.to_parquet(cleaned_path, index=False)
    df_sessions.to_parquet(os.path.join(PROCESSED_DIR, "sessions.parquet"), index=False)
    print("Sessionization complete and saved.")
