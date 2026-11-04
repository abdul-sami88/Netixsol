"""
Personalized Search Re-Ranking Engine for ShopKaro
Implements Task 2:
- Re-ranks search candidate results using the user's Day 2 customer profile
- Incorporates category affinity, price sensitivity (AOV proximity), customer segment, and past brand purchases
- Demonstrates: Same query, different users -> completely personalized ranking order
"""

import os
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
USER_FEATS_PATH = os.path.join(BASE_DIR, "data", "processed", "user_features.parquet")
ORDERS_PATH = os.path.join(BASE_DIR, "data", "processed", "orders.parquet")
PRODUCTS_PATH = os.path.join(BASE_DIR, "data", "processed", "products.parquet")


class PersonalizedSearchEngine:
    """
    Personalizes search candidate feeds based on the customer's historical profile and behavioral segment.
    """
    def __init__(self, user_features_df: Optional[pd.DataFrame] = None):
        if user_features_df is None and os.path.exists(USER_FEATS_PATH):
            self.user_features = pd.read_parquet(USER_FEATS_PATH).set_index("user_id")
        else:
            self.user_features = user_features_df

        # Cache user purchased brands
        self.user_brand_history = {}
        if os.path.exists(ORDERS_PATH) and os.path.exists(PRODUCTS_PATH):
            try:
                orders_df = pd.read_parquet(ORDERS_PATH)
                prods_df = pd.read_parquet(PRODUCTS_PATH)[["product_id", "brand"]].set_index("product_id")
                
                # Explode items in orders
                for _, row in orders_df.iterrows():
                    uid = row["user_id"]
                    item_ids_str = str(row.get("item_ids", ""))
                    pids = [p.strip() for p in item_ids_str.split(",") if p.strip()]
                    if uid not in self.user_brand_history:
                        self.user_brand_history[uid] = set()
                    for p in pids:
                        if p in prods_df.index:
                            b = prods_df.loc[p, "brand"]
                            self.user_brand_history[uid].add(b)
            except Exception:
                pass

    def rerank_for_user(self, user_id: str, search_results: List[Dict[str, Any]], top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Re-ranks an unpersonalized list of search results according to the user's profile:
        Final_Score = Search_Score * Category_Multiplier * Price_Multiplier * Segment_Multiplier * Brand_Multiplier
        """
        if user_id not in self.user_features.index:
            # Cold-start or guest user: return search results as-is
            for r in search_results:
                r["personalization_reason"] = "Standard Relevance (Guest User)"
            return search_results[:top_k]

        u_prof = self.user_features.loc[user_id]
        fav_cat = u_prof.get("favourite_category", "General")
        aov = float(u_prof.get("avg_order_value_pkr", 0.0) or 0.0)
        segment = str(u_prof.get("segment_name", "General"))
        user_brands = self.user_brand_history.get(user_id, set())
        
        personalized_items = []
        for item in search_results:
            base_score = float(item.get("cross_score", item.get("score", 1.0)))
            item_cat = item["category"]
            item_price = float(item["price_pkr"])
            item_brand = item["brand"]
            
            reasons = []
            
            # 1. Category Affinity Multiplier
            cat_mult = 1.0
            if fav_cat and fav_cat != "General":
                if item_cat == fav_cat:
                    cat_mult = 1.35
                    reasons.append(f"Matches your favourite category ({fav_cat})")
                else:
                    cat_mult = 0.90
                    
            # 2. Price Affinity / AOV Multiplier
            price_mult = 1.0
            if aov > 0:
                # Gaussian proximity to user's typical spending power
                rel_diff = abs(item_price - aov) / max(aov, 1000.0)
                price_mult = float(np.exp(-0.35 * rel_diff))
                # Bound between 0.75 and 1.25
                price_mult = np.clip(price_mult, 0.75, 1.25)
                if price_mult > 1.05:
                    reasons.append("Matches your typical budget")
                    
            # 3. Customer Persona Segment Boost
            seg_mult = 1.0
            if "Loyal Electronics Buyers" in segment or "Loyal Tech" in segment:
                if item_cat == "Electronics":
                    seg_mult = 1.30
                    reasons.append("Top pick for Tech Enthusiasts")
            elif "Eid Shoppers" in segment:
                if item_cat == "Fashion":
                    seg_mult = 1.30
                    reasons.append("Curated for Eid & Festive Shoppers")
            elif "Bargain Hunters" in segment:
                if item_price < 3000:
                    seg_mult = 1.25
                    reasons.append("Great value deal for Bargain Shoppers")
            elif "Routine Replenishers" in segment:
                if item_cat in ["Groceries & Essentials", "Beauty & Personal Care"]:
                    seg_mult = 1.25
                    reasons.append("Essential replenishment staple")
                    
            # 4. Brand Loyalty Multiplier
            brand_mult = 1.0
            if item_brand in user_brands:
                brand_mult = 1.20
                reasons.append(f"From a brand you frequently trust ({item_brand})")
                
            personalized_score = base_score * cat_mult * price_mult * seg_mult * brand_mult
            
            item_copy = dict(item)
            item_copy["personalized_score"] = round(float(personalized_score), 4)
            item_copy["personalization_reason"] = " • ".join(reasons) if reasons else "High marketplace relevance"
            personalized_items.append(item_copy)
            
        personalized_items.sort(key=lambda x: x["personalized_score"], reverse=True)
        return personalized_items[:top_k]

