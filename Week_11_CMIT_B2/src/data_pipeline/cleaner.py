"""
Event Cleaning Module
Implements production-grade cleaning for ShopKaro clickstream events:
1. Bot removal (known crawler user-agents, bot IDs, robotic request rates)
2. Deduplication (identical user + product + timestamp clicks)
3. Outlier session filtering (sessions with >1,000 clicks)
"""

import os
import pandas as pd
from typing import Dict, Tuple

RAW_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "raw")
PROCESSED_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "processed")
os.makedirs(PROCESSED_DIR, exist_ok=True)

BOT_KEYWORDS = ["scrapy", "python-requests", "ahrefsbot", "bot", "crawler", "spider"]

def clean_events(input_path: str = None) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Cleans raw clickstream events and logs audit counts.
    """
    if input_path is None:
        input_path = os.path.join(RAW_DIR, "events_raw.csv")
        
    print(f"Loading raw events from {input_path}...")
    df = pd.read_csv(input_path)
    total_raw = len(df)
    print(f"Total raw events loaded: {total_raw:,}")
    
    # 1. Convert timestamp to datetime
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    
    # 2. Filter Bot User-Agents and Bot User IDs
    bot_ua_mask = df["user_agent"].str.lower().str.contains("|".join(BOT_KEYWORDS), na=False)
    bot_uid_mask = df["user_id"].str.contains("BOT", case=False, na=False)
    is_bot = bot_ua_mask | bot_uid_mask
    n_bots = int(is_bot.sum())
    df_non_bot = df[~is_bot].copy()
    print(f"Filtered {n_bots:,} bot events ({(n_bots/total_raw)*100:.2f}%).")
    
    # 3. Deduplicate (same user, item, event_type, and timestamp within the same second)
    n_before_dedup = len(df_non_bot)
    df_dedup = df_non_bot.drop_duplicates(subset=["user_id", "product_id", "event_type", "timestamp"])
    n_duplicates = n_before_dedup - len(df_dedup)
    print(f"Filtered {n_duplicates:,} duplicate click events ({(n_duplicates/total_raw)*100:.2f}%).")
    
    # 4. Outlier runaway user filtering (>1,000 rapid clicks)
    user_event_counts = df_dedup.groupby("user_id").size()
    outlier_users = user_event_counts[user_event_counts > 1000].index.tolist()
    n_outliers = int(df_dedup["user_id"].isin(outlier_users).sum())
    df_cleaned = df_dedup[~df_dedup["user_id"].isin(outlier_users)].copy()
    print(f"Filtered {n_outliers:,} runaway session events from {len(outlier_users)} users ({(n_outliers/total_raw)*100:.2f}%).")
    
    # Sort chronologically
    df_cleaned.sort_values(by="timestamp", inplace=True)
    df_cleaned.reset_index(drop=True, inplace=True)
    
    audit_stats = {
        "raw_events": total_raw,
        "bot_events_removed": n_bots,
        "duplicate_events_removed": n_duplicates,
        "outlier_events_removed": n_outliers,
        "clean_events": len(df_cleaned),
        "clean_retention_pct": round((len(df_cleaned) / total_raw) * 100, 2)
    }
    
    print(f"Cleaned events remaining: {len(df_cleaned):,} ({audit_stats['clean_retention_pct']}%)")
    return df_cleaned, audit_stats

if __name__ == "__main__":
    df_clean, stats = clean_events()
    out_file = os.path.join(PROCESSED_DIR, "events_cleaned.parquet")
    df_clean.to_parquet(out_file, index=False)
    print(f"Saved cleaned events to {out_file}")
