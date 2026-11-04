"""
Baseline Recommendation Models
Implements Task 1:
1. Most Popular Overall (Global popularity)
2. Category Popular (Most popular in user's favourite category)
3. Recently Trending (Velocity in final 7 days of training set)
"""

import os
import pandas as pd
import numpy as np
from typing import List, Dict

class MostPopularRecommender:
    """Recommends the top-K globally most interacted items in training data."""
    def __init__(self):
        self.popular_items = []
        
    def fit(self, train_events: pd.DataFrame):
        # Weight events: view=1, cart=2, purchase=5
        weights = {"view": 1.0, "add_to_cart": 2.0, "purchase": 5.0}
        df = train_events.copy()
        df["weight"] = df["event_type"].map(weights).fillna(1.0)
        
        item_scores = df.groupby("product_id")["weight"].sum().sort_values(ascending=False)
        self.popular_items = item_scores.index.tolist()
        return self
        
    def recommend(self, user_id: str, k: int = 10, exclude_items: set = None) -> List[str]:
        exclude = exclude_items or set()
        recs = [item for item in self.popular_items if item not in exclude]
        return recs[:k]


class CategoryPopularRecommender:
    """Recommends top-K popular items within each user's favourite category."""
    def __init__(self):
        self.category_popular = {} # category -> list of product_ids
        self.user_fav_cat = {}     # user_id -> category
        self.global_popular = []
        
    def fit(self, train_events: pd.DataFrame, user_features: pd.DataFrame, item_features: pd.DataFrame):
        # 1. Map user to favourite category
        if "favourite_category" in user_features.columns:
            self.user_fav_cat = dict(zip(user_features["user_id"], user_features["favourite_category"]))
            
        # 2. Merge category to train_events
        item_cat_map = dict(zip(item_features["product_id"], item_features["category"]))
        df = train_events.copy()
        df["category"] = df["product_id"].map(item_cat_map).fillna("Unknown")
        
        weights = {"view": 1.0, "add_to_cart": 2.0, "purchase": 5.0}
        df["weight"] = df["event_type"].map(weights).fillna(1.0)
        
        # Global fallback
        self.global_popular = df.groupby("product_id")["weight"].sum().sort_values(ascending=False).index.tolist()
        
        # Per category ranking
        cat_grouped = df.groupby(["category", "product_id"])["weight"].sum().reset_index()
        for cat, group in cat_grouped.groupby("category"):
            ranked = group.sort_values(by="weight", ascending=False)["product_id"].tolist()
            self.category_popular[cat] = ranked
            
        return self
        
    def recommend(self, user_id: str, k: int = 10, exclude_items: set = None) -> List[str]:
        exclude = exclude_items or set()
        fav_cat = self.user_fav_cat.get(user_id, "General")
        cat_items = self.category_popular.get(fav_cat, self.global_popular)
        
        recs = [item for item in cat_items if item not in exclude]
        if len(recs) < k:
            fallback = [item for item in self.global_popular if item not in exclude and item not in recs]
            recs.extend(fallback)
        return recs[:k]


class RecentlyTrendingRecommender:
    """Recommends items exhibiting peak velocity in the final 7 days of training window."""
    def __init__(self, window_days: int = 7):
        self.window_days = window_days
        self.trending_items = []
        self.global_fallback = []
        
    def fit(self, train_events: pd.DataFrame):
        df = train_events.copy()
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        max_ts = df["timestamp"].max()
        cutoff_ts = max_ts - pd.Timedelta(days=self.window_days)
        
        weights = {"view": 1.0, "add_to_cart": 2.0, "purchase": 5.0}
        df["weight"] = df["event_type"].map(weights).fillna(1.0)
        
        self.global_fallback = df.groupby("product_id")["weight"].sum().sort_values(ascending=False).index.tolist()
        
        # Filter final 7 days
        recent_df = df[df["timestamp"] >= cutoff_ts]
        recent_scores = recent_df.groupby("product_id")["weight"].sum().sort_values(ascending=False)
        self.trending_items = recent_scores.index.tolist()
        return self
        
    def recommend(self, user_id: str, k: int = 10, exclude_items: set = None) -> List[str]:
        exclude = exclude_items or set()
        recs = [item for item in self.trending_items if item not in exclude]
        if len(recs) < k:
            fallback = [item for item in self.global_fallback if item not in exclude and item not in recs]
            recs.extend(fallback)
        return recs[:k]
