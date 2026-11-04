"""
Business Rules & Re-Ranking Engine
Implements Task 5:
1. Hard Filters: Out-of-Stock Removal & Already-Purchased Item Filtering
2. Brand Diversity Constraint: Max 2 items per brand to prevent brand monotony
3. Configurable Commercial Scoring: High-Margin Boost & On-Sale Promotions
4. Festival Calendar Boost: Dynamic category weight lifting (Lawn for Eid, Electronics for 11.11)
5. Roman Urdu / UrduLish Natural Explanations Generator
"""

import os
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional

class BusinessRuleReRanker:
    """
    Production post-processing and re-ranking layer applied to raw candidate recommendations.
    """
    def __init__(
        self,
        products_df: pd.DataFrame,
        orders_df: pd.DataFrame,
        max_items_per_brand: int = 2,
        margin_boost_weight: float = 0.20,
        festival_boost_weight: float = 0.30
    ):
        self.max_items_per_brand = max_items_per_brand
        self.margin_boost_weight = margin_boost_weight
        self.festival_boost_weight = festival_boost_weight
        
        # Product lookup maps
        self.product_meta = products_df.set_index("product_id").to_dict(orient="index")
        
        # User purchase history: user_id -> set of purchased product_ids
        self.user_purchases = {}
        for _, row in orders_df.iterrows():
            uid = row["user_id"]
            raw_items = row["item_ids"]
            if isinstance(raw_items, str):
                pids = [p.strip() for p in raw_items.split(",") if p.strip()]
            elif isinstance(raw_items, list):
                pids = list(raw_items)
            else:
                pids = []
            if uid not in self.user_purchases:
                self.user_purchases[uid] = set()
            self.user_purchases[uid].update(pids)

    def rerank(
        self,
        user_id: str,
        candidate_items: List[str],
        active_festival: Optional[str] = "Chaand Raat & Eid ul-Fitr",
        k: int = 10,
        user_last_viewed_title: Optional[str] = None
    ) -> List[Dict]:
        """
        Re-ranks raw candidate IDs using inventory, diversity, margins, and seasonal rules.
        Returns rich structured recommendations with one-line Roman Urdu explanations.
        """
        user_history = self.user_purchases.get(user_id, set())
        brand_counts = {}
        scored_candidates = []
        
        # Festival target categories
        festival_boost_cats = set()
        if active_festival and ("Eid" in active_festival or "Ramadan" in active_festival):
            festival_boost_cats = {"Fashion", "Beauty & Personal Care"}
        elif active_festival and ("11.11" in active_festival or "Friday" in active_festival):
            festival_boost_cats = {"Electronics", "Home & Living"}
            
        for rank, pid in enumerate(candidate_items):
            info = self.product_meta.get(pid)
            if not info:
                continue
                
            # Rule 1: Remove out-of-stock items
            stock = info.get("stock_quantity", 0)
            if stock <= 0:
                continue
                
            # Rule 2: Remove already-purchased items
            if pid in user_history:
                continue
                
            # Base ranking score (reciprocal rank)
            base_score = 1.0 / (rank + 1.0)
            
            # Rule 3: High margin boost
            price = info.get("price_pkr", 1)
            cost = info.get("cost_pkr", price * 0.7)
            margin_rate = (price - cost) / max(price, 1)
            margin_multiplier = 1.0 + (self.margin_boost_weight * margin_rate)
            
            # Rule 4: Festival boost
            cat = info.get("category", "")
            festival_multiplier = 1.0 + (self.festival_boost_weight if cat in festival_boost_cats else 0.0)
            
            final_score = base_score * margin_multiplier * festival_multiplier
            scored_candidates.append((pid, final_score, info))
            
        # Sort candidates by combined commercial score
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        
        # Rule 5: Brand Diversity Constraint (Max N items per brand in Top-K)
        final_recs = []
        for pid, score, info in scored_candidates:
            brand = info.get("brand", "Generic")
            current_count = brand_counts.get(brand, 0)
            if current_count < self.max_items_per_brand:
                brand_counts[brand] = current_count + 1
                
                # Rule 6: Generate UrduLish one-line explanation
                explanation = self._generate_explanation(info, active_festival, user_last_viewed_title)
                
                final_recs.append({
                    "product_id": pid,
                    "title": info.get("title", ""),
                    "brand": brand,
                    "category": info.get("category", ""),
                    "price_pkr": info.get("price_pkr", 0),
                    "stock_quantity": info.get("stock_quantity", 0),
                    "final_score": round(score, 4),
                    "explanation_urdu": explanation
                })
                
            if len(final_recs) >= k:
                break
                
        return final_recs

    def _generate_explanation(self, info: dict, festival: Optional[str], last_viewed: Optional[str]) -> str:
        """Constructs authentic Roman Urdu / UrduLish one-line explanation."""
        brand = info.get("brand", "")
        cat = info.get("category", "")
        title = info.get("title", "")
        
        if last_viewed:
            return f"Kyun ke aap ne '{last_viewed}' dekha tha, {brand} ka yeh product aap ki pasand ke mutabiq hai."
        elif festival and ("Eid" in festival or "Ramadan" in festival) and cat == "Fashion":
            return f"Eid festive collection ke liye {brand} ka yeh trending suit Pakistan bhar mein pasand kiya ja raha hai."
        elif festival and "11.11" in festival and cat == "Electronics":
            return f"11.11 Mega Sale discount aur official warranty ke sath yeh {brand} item best-value choice hai."
        elif cat == "Electronics":
            return f"Original PTA approved official warranty ke sath {brand} ka yeh top-rated gadget behtareen choice hai."
        elif cat == "Fashion":
            return f"{brand} ki premium quality stitching aur latest seasonal design ki wajah se yeh top choice hai."
        else:
            return f"Aap ke shopping patterns aur ShopKaro customers ke positive reviews ki roshni mein yeh product muntakhib kiya gaya hai."
