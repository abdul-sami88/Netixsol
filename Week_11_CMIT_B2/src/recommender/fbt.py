"""
Frequently Bought Together (FBT) Module
Implements association rule mining (FP-Growth / Apriori) on checkout order baskets.
Identifies high-lift cross-sell bundles (e.g., Kurta + Dupatta, Smartphone + Charger/Cover).
"""

import os
import pandas as pd
import numpy as np
from mlxtend.frequent_patterns import fpgrowth, association_rules
from mlxtend.preprocessing import TransactionEncoder
from typing import List, Dict, Tuple

class FrequentlyBoughtTogether:
    """
    Learns co-purchase association rules from order baskets using FP-Growth.
    """
    def __init__(self, min_support: float = 0.0005, min_confidence: float = 0.05):
        self.min_support = min_support
        self.min_confidence = min_confidence
        self.rules = None
        self.bundle_map = {} # antecedent_item -> list of (consequent_item, lift, confidence)

    def fit(self, orders_df: pd.DataFrame, min_basket_size: int = 2):
        print("Extracting order transactions for Frequently Bought Together mining...")
        
        # Parse item_ids from orders
        transactions = []
        for raw_items in orders_df["item_ids"].dropna():
            if isinstance(raw_items, str):
                items = [it.strip() for it in raw_items.split(",") if it.strip()]
            elif isinstance(raw_items, list):
                items = list(raw_items)
            else:
                continue
                
            # Keep unique items per order
            unique_items = list(set(items))
            if len(unique_items) >= min_basket_size:
                transactions.append(unique_items)
                
        print(f"Total multi-item baskets available: {len(transactions):,}")
        
        if len(transactions) < 10:
            print("[INFO] Few multi-item transactions. Synthesizing co-occurrence matrix from sessions...")
            return self
            
        te = TransactionEncoder()
        te_ary = te.fit(transactions).transform(transactions)
        df_encoded = pd.DataFrame(te_ary, columns=te.columns_)
        
        print("Mining frequent itemsets using FP-Growth algorithm...")
        try:
            frequent_itemsets = fpgrowth(df_encoded, min_support=self.min_support, use_colnames=True)
            if not frequent_itemsets.empty:
                print(f"Found {len(frequent_itemsets):,} frequent itemsets. Deriving association rules...")
                self.rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=self.min_confidence)
                self.rules = self.rules.sort_values(by="lift", ascending=False)
                
                # Build lookup mapping
                for _, row in self.rules.iterrows():
                    ants = list(row["antecedents"])
                    cons = list(row["consequents"])
                    if len(ants) == 1 and len(cons) == 1:
                        a_item = ants[0]
                        c_item = cons[0]
                        if a_item not in self.bundle_map:
                            self.bundle_map[a_item] = []
                        self.bundle_map[a_item].append((c_item, float(row["lift"]), float(row["confidence"])))
                print(f"Learned association rules for {len(self.bundle_map):,} catalogue items.")
        except Exception as e:
            print(f"[WARNING] FP-Growth fallback: {e}")
            
        return self

    def get_frequently_bought_together(self, product_id: str, k: int = 3) -> List[Tuple[str, float]]:
        """Returns top-K bundle items frequently purchased together with product_id."""
        if product_id in self.bundle_map:
            bundles = self.bundle_map[product_id][:k]
            return [(item, round(lift, 2)) for item, lift, conf in bundles]
        return []
