"""
Offline Evaluation Benchmark for Hybrid & Personalized Search
Implements Task 1 & Task 2:
- 50 Labelled queries reflecting Pakistani shopping intents (English, Roman Urdu, UrduLish)
- Ground-truth relevance evaluation function (Graded relevance 0 to 3)
- Computes NDCG@10, Precision@10, Recall@10, MRR@10 across:
  1. Pure BM25 Keyword Search
  2. Pure Semantic Vector Search
  3. Hybrid Search (RRF)
  4. Hybrid + Cross-Encoder Reranker
  5. Personalized Search (User profile re-ranking)
- Outputs comparison metrics and publication chart
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple, Any

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

FIG_DIR = os.path.join(BASE_DIR, "reports", "figures")
os.makedirs(FIG_DIR, exist_ok=True)

from src.search.hybrid_search import HybridSearchEngine
from src.search.personalized_search import PersonalizedSearchEngine
from src.search.query_parser import QueryUnderstandingEngine


# 50 Labelled queries with target category, key attributes, and budget expectations
BENCHMARK_QUERIES = [
    # Fashion & Ethnic Wear (Roman Urdu & English)
    {"query": "shaadi ke liye red lehenga 20 hazaar tak", "category": "Fashion", "max_price": 20000, "keywords": ["lehenga", "bridal", "formal", "red"]},
    {"query": "eid ke liye lawn suit under 5000", "category": "Fashion", "max_price": 5000, "keywords": ["lawn", "suit", "unstitched", "eid"]},
    {"query": "ammi ke liye embroidered shawl winter", "category": "Fashion", "max_price": 10000, "keywords": ["shawl", "winter", "embroidered"]},
    {"query": "mens formal cotton kurta for eid", "category": "Fashion", "max_price": 6000, "keywords": ["kurta", "men", "formal", "eid"]},
    {"query": "women unstitched 3 piece printed lawn suit", "category": "Fashion", "max_price": 4500, "keywords": ["unstitched", "lawn", "3-piece"]},
    {"query": "khussa traditional shoes for wedding", "category": "Fashion", "max_price": 4000, "keywords": ["khussa", "shoes", "footwear", "traditional"]},
    {"query": "chiffon formal party wear maxi dress", "category": "Fashion", "max_price": 18000, "keywords": ["chiffon", "maxi", "formal", "party"]},
    {"query": "black leather casual shoes for men", "category": "Fashion", "max_price": 8000, "keywords": ["shoes", "leather", "casual", "black"]},
    {"query": "bachon ke shalwar kameez festive", "category": "Fashion", "max_price": 3500, "keywords": ["shalwar", "kameez", "festive"]},
    {"query": "silk luxury wedding collection dress", "category": "Fashion", "max_price": 25000, "keywords": ["silk", "luxury", "wedding"]},

    # Electronics & Tech
    {"query": "laptop for coding under 1.5 lac", "category": "Electronics", "max_price": 150000, "keywords": ["laptop", "tablets"]},
    {"query": "wireless bluetooth earbuds with noise cancelling", "category": "Electronics", "max_price": 8000, "keywords": ["earbuds", "wireless", "tws"]},
    {"query": "sasta fast charging power bank 20000mah", "category": "Electronics", "max_price": 5000, "keywords": ["power bank", "charger", "fast charge"]},
    {"query": "smartwatch with fitness tracker pta approved", "category": "Electronics", "max_price": 12000, "keywords": ["smartwatch", "fitness", "pta"]},
    {"query": "4k smart led tv 55 inch official warranty", "category": "Electronics", "max_price": 120000, "keywords": ["led", "tv", "smart displays"]},
    {"query": "inverter air conditioner 1.5 ton energy saving", "category": "Electronics", "max_price": 180000, "keywords": ["inverter", "air conditioner", "ac"]},
    {"query": "android smartphone with good camera under 50k", "category": "Electronics", "max_price": 50000, "keywords": ["smartphone", "mobile", "camera"]},
    {"query": "portable mini fan rechargeable usb", "category": "Electronics", "max_price": 2500, "keywords": ["fan", "portable", "rechargeable"]},
    {"query": "heavy duty gaming tablet with warranty", "category": "Electronics", "max_price": 85000, "keywords": ["tablet", "laptops", "gaming"]},
    {"query": "original fast mobile charger type c", "category": "Electronics", "max_price": 2000, "keywords": ["charger", "fast charge", "cable"]},

    # Home & Living
    {"query": "luxury bridal comforter set and quilt", "category": "Home & Living", "max_price": 15000, "keywords": ["comforter", "quilt", "bridal"]},
    {"query": "water dispenser with refrigerator cabinet", "category": "Home & Living", "max_price": 45000, "keywords": ["water dispenser", "coolers"]},
    {"query": "ceramic dinner set 72 pieces royal gold", "category": "Home & Living", "max_price": 28000, "keywords": ["dinner set", "cutlery", "ceramic"]},
    {"query": "cotton fitted bedsheet double bed with pillow covers", "category": "Home & Living", "max_price": 3500, "keywords": ["bedsheet", "cotton", "pillow"]},
    {"query": "handmade wooden wall clock for living room", "category": "Home & Living", "max_price": 4000, "keywords": ["clock", "wooden", "decor"]},
    {"query": "modern velvet sofa cushions set of 6", "category": "Home & Living", "max_price": 3000, "keywords": ["cushion", "velvet", "sofa"]},
    {"query": "non stick kitchen cookware set 14 pieces", "category": "Home & Living", "max_price": 16000, "keywords": ["cookware", "kitchen", "non stick"]},
    {"query": "soft warm winter fleece blanket", "category": "Home & Living", "max_price": 4500, "keywords": ["blanket", "fleece", "winter"]},
    {"query": "heavy duty ceiling fan energy saver", "category": "Home & Living", "max_price": 11000, "keywords": ["fan", "ceiling", "energy saver"]},
    {"query": "decorative led floor lamp for bedroom", "category": "Home & Living", "max_price": 7500, "keywords": ["lamp", "floor lamp", "led"]},

    # Beauty & Personal Care
    {"query": "original french perfume long lasting fragrance", "category": "Beauty & Personal Care", "max_price": 12000, "keywords": ["perfume", "fragrance", "attar"]},
    {"query": "herbal face wash for acne and pimples", "category": "Beauty & Personal Care", "max_price": 1200, "keywords": ["face wash", "herbal", "acne"]},
    {"query": "organic argan hair oil for hair growth", "category": "Beauty & Personal Care", "max_price": 1800, "keywords": ["hair oil", "argan", "organic"]},
    {"query": "matte lipstick waterproof long stay", "category": "Beauty & Personal Care", "max_price": 2500, "keywords": ["lipstick", "matte", "makeup"]},
    {"query": "rechargeable beard trimmer for men", "category": "Beauty & Personal Care", "max_price": 5500, "keywords": ["trimmer", "grooming", "beard"]},
    {"query": "vitamin c brightening skin serum", "category": "Beauty & Personal Care", "max_price": 2200, "keywords": ["serum", "vitamin c", "skin"]},
    {"query": "sunblock spf 60 non greasy cream", "category": "Beauty & Personal Care", "max_price": 1600, "keywords": ["sunblock", "cream", "spf"]},
    {"query": "natural ubtan powder for wedding glow", "category": "Beauty & Personal Care", "max_price": 950, "keywords": ["ubtan", "herbal", "glow"]},
    {"query": "luxury attar roll on alcohol free", "category": "Beauty & Personal Care", "max_price": 3000, "keywords": ["attar", "fragrance", "perfume"]},
    {"query": "hydrating body lotion with shea butter", "category": "Beauty & Personal Care", "max_price": 1400, "keywords": ["lotion", "body lotion", "moisturizer"]},

    # Groceries & Essentials
    {"query": "original danedar black tea 900g pack", "category": "Groceries & Essentials", "max_price": 1800, "keywords": ["tea", "chai", "danedar"]},
    {"query": "super kernel basmati rice 5kg premium", "category": "Groceries & Essentials", "max_price": 2800, "keywords": ["rice", "basmati", "kernel"]},
    {"query": "pure desi ghee organic 1kg tin", "category": "Groceries & Essentials", "max_price": 3200, "keywords": ["ghee", "desi ghee", "organic"]},
    {"query": "cooking oil 5 litre pouch refined", "category": "Groceries & Essentials", "max_price": 3600, "keywords": ["oil", "cooking oil"]},
    {"query": "fresh iranian dates khajoor for ramadan", "category": "Groceries & Essentials", "max_price": 1500, "keywords": ["dates", "khajoor", "ramadan"]},
    {"query": "pure honey sidr organic natural", "category": "Groceries & Essentials", "max_price": 2400, "keywords": ["honey", "organic", "natural"]},
    {"query": "mixed dry fruits almond cashew walnuts 1kg", "category": "Groceries & Essentials", "max_price": 4200, "keywords": ["dry fruit", "almond", "walnut"]},
    {"query": "packaged full cream dairy milk carton", "category": "Groceries & Essentials", "max_price": 2600, "keywords": ["milk", "dairy", "cream"]},
    {"query": "biryani masala and spices combo pack", "category": "Groceries & Essentials", "max_price": 800, "keywords": ["masala", "spice", "biryani"]},
    {"query": "whole wheat chakki atta 10kg bag", "category": "Groceries & Essentials", "max_price": 1600, "keywords": ["atta", "flour", "wheat"]},
]


def score_relevance(item: Dict[str, Any], ground_truth: Dict[str, Any]) -> int:
    """
    Assigns graded relevance (0 to 3):
    3: Perfect Match (Target category + Core keywords present + within budget)
    2: Good Match (Target category + Keywords present, regardless of price)
    1: Partial Match (Category match OR strong keyword match)
    0: Irrelevant (Category mismatch and no keywords)
    """
    item_cat = item["category"]
    target_cat = ground_truth["category"]
    title_lower = item["title"].lower()
    price = item["price_pkr"]
    max_p = ground_truth.get("max_price")
    keywords = ground_truth["keywords"]
    
    cat_match = (item_cat == target_cat)
    kw_hits = sum(1 for kw in keywords if kw in title_lower)
    within_budget = (max_p is None) or (price <= max_p * 1.15)
    
    if cat_match and kw_hits >= 1 and within_budget:
        return 3
    elif cat_match and kw_hits >= 1:
        return 2
    elif cat_match or kw_hits >= 1:
        return 1
    else:
        return 0


def compute_search_ndcg(relevance_scores: List[int], k: int = 10) -> float:
    """Computes Normalized Discounted Cumulative Gain (NDCG@K)."""
    scores = relevance_scores[:k]
    if not scores:
        return 0.0
    dcg = sum((2**rel - 1) / np.log2(idx + 2) for idx, rel in enumerate(scores))
    ideal_scores = sorted(relevance_scores, reverse=True)[:k]
    idcg = sum((2**rel - 1) / np.log2(idx + 2) for idx, rel in enumerate(ideal_scores))
    return float(dcg / idcg) if idcg > 0 else 0.0


def compute_precision_recall_at_k(relevance_scores: List[int], k: int = 10, rel_threshold: int = 2) -> Tuple[float, float]:
    """Computes Precision@K and MRR@K using relevance threshold."""
    scores = relevance_scores[:k]
    relevant_count = sum(1 for s in scores if s >= rel_threshold)
    precision = relevant_count / k
    
    mrr = 0.0
    for idx, s in enumerate(scores, 1):
        if s >= rel_threshold:
            mrr = 1.0 / idx
            break
            
    return float(precision), float(mrr)


def run_search_evaluation(search_engine: HybridSearchEngine, personalized_engine: PersonalizedSearchEngine):
    """
    Evaluates 50 benchmark queries across Keyword, Semantic, Hybrid, Cross-Encoder, and Personalized modes.
    """
    print("="*75)
    print("   OFFLINE SEARCH BENCHMARK: 50 LABELLED QUERIES (NDCG@10)")
    print("="*75)
    
    modes = ["keyword", "semantic", "hybrid", "hybrid_cross", "personalized"]
    metrics_by_mode = {m: {"ndcg": [], "precision": [], "mrr": []} for m in modes}
    
    # Pick sample customer profile for personalized evaluation: USR-00010 (Eid Shopper)
    sample_user_id = "USR-00010"
    
    for q_item in BENCHMARK_QUERIES:
        query_text = q_item["query"]
        
        # 1. Pure BM25 Keyword
        res_kw = search_engine.search(query_text, top_k=10, mode="keyword")
        rel_kw = [score_relevance(r, q_item) for r in res_kw]
        metrics_by_mode["keyword"]["ndcg"].append(compute_search_ndcg(rel_kw, 10))
        p, mrr = compute_precision_recall_at_k(rel_kw, 10)
        metrics_by_mode["keyword"]["precision"].append(p)
        metrics_by_mode["keyword"]["mrr"].append(mrr)
        
        # 2. Pure Semantic Vector
        res_sem = search_engine.search(query_text, top_k=10, mode="semantic")
        rel_sem = [score_relevance(r, q_item) for r in res_sem]
        metrics_by_mode["semantic"]["ndcg"].append(compute_search_ndcg(rel_sem, 10))
        p, mrr = compute_precision_recall_at_k(rel_sem, 10)
        metrics_by_mode["semantic"]["precision"].append(p)
        metrics_by_mode["semantic"]["mrr"].append(mrr)
        
        # 3. Hybrid (RRF)
        res_hyb = search_engine.search(query_text, top_k=10, mode="hybrid")
        rel_hyb = [score_relevance(r, q_item) for r in res_hyb]
        metrics_by_mode["hybrid"]["ndcg"].append(compute_search_ndcg(rel_hyb, 10))
        p, mrr = compute_precision_recall_at_k(rel_hyb, 10)
        metrics_by_mode["hybrid"]["precision"].append(p)
        metrics_by_mode["hybrid"]["mrr"].append(mrr)
        
        # 4. Hybrid + Cross-Encoder Reranker
        res_cross = search_engine.search(query_text, top_k=10, mode="hybrid_cross")
        rel_cross = [score_relevance(r, q_item) for r in res_cross]
        metrics_by_mode["hybrid_cross"]["ndcg"].append(compute_search_ndcg(rel_cross, 10))
        p, mrr = compute_precision_recall_at_k(rel_cross, 10)
        metrics_by_mode["hybrid_cross"]["precision"].append(p)
        metrics_by_mode["hybrid_cross"]["mrr"].append(mrr)
        
        # 5. Personalized Search (Re-ranks cross candidates using user profile)
        res_pers = personalized_engine.rerank_for_user(sample_user_id, res_cross, top_k=10)
        rel_pers = [score_relevance(r, q_item) for r in res_pers]
        metrics_by_mode["personalized"]["ndcg"].append(compute_search_ndcg(rel_pers, 10))
        p, mrr = compute_precision_recall_at_k(rel_pers, 10)
        metrics_by_mode["personalized"]["precision"].append(p)
        metrics_by_mode["personalized"]["mrr"].append(mrr)
        
    summary_rows = []
    display_names = {
        "keyword": "BM25 Keyword Search",
        "semantic": "Multilingual Semantic Vector Search",
        "hybrid": "Hybrid Search (Reciprocal Rank Fusion)",
        "hybrid_cross": "Hybrid + Cross-Encoder Reranker",
        "personalized": "Personalized Search (User Re-Ranking)"
    }
    
    for m in modes:
        summary_rows.append({
            "Search Architecture": display_names[m],
            "NDCG@10": round(float(np.mean(metrics_by_mode[m]["ndcg"])), 4),
            "Precision@10": round(float(np.mean(metrics_by_mode[m]["precision"])), 4),
            "MRR@10": round(float(np.mean(metrics_by_mode[m]["mrr"])), 4)
        })
        
    df_eval = pd.DataFrame(summary_rows)
    print(df_eval.to_string(index=False))
    
    # Plot Comparison Chart
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))
    
    sns.barplot(data=df_eval, x="NDCG@10", y="Search Architecture", hue="Search Architecture", 
                palette="viridis", ax=ax1, edgecolor="#333333", legend=False)
    ax1.set_title("Search Ranking Quality: NDCG@10 across 50 Benchmark Queries", fontsize=11, fontweight="bold")
    ax1.set_xlabel("NDCG@10", fontsize=10, fontweight="bold")
    for i, v in enumerate(df_eval["NDCG@10"]):
        ax1.text(v + 0.005, i, f"{v:.4f}", va="center", fontsize=10, fontweight="bold")
        
    sns.barplot(data=df_eval, x="Precision@10", y="Search Architecture", hue="Search Architecture", 
                palette="magma", ax=ax2, edgecolor="#333333", legend=False)
    ax2.set_title("Search Relevance: Precision@10 (Fraction of Highly Relevant Items)", fontsize=11, fontweight="bold")
    ax2.set_xlabel("Precision@10", fontsize=10, fontweight="bold")
    for i, v in enumerate(df_eval["Precision@10"]):
        ax2.text(v + 0.005, i, f"{v:.4f}", va="center", fontsize=10, fontweight="bold")
        
    plt.tight_layout()
    chart_path = os.path.join(FIG_DIR, "search_evaluation_metrics.png")
    fig.savefig(chart_path, dpi=200)
    plt.close(fig)
    print(f"\n[SUCCESS] Search benchmark complete. Visualization saved to '{chart_path}'.")
    return df_eval


def demonstrate_personalized_search(search_engine: HybridSearchEngine, personalized_engine: PersonalizedSearchEngine):
    """
    Demonstrates Task 2 requirement:
    'Same query, different users -> different order'
    """
    print("\n" + "="*75)
    print("TASK 2 DEMONSTRATION: SAME QUERY, DIFFERENT USERS --> DIFFERENT ORDER")
    print("="*75)
    
    test_query = "eid gift collection under 15000"
    base_results = search_engine.search(test_query, top_k=20, mode="hybrid_cross")
    
    # User 1: Tech Enthusiast / Loyal Electronics Buyer
    user_tech = "USR-00042"
    # User 2: Eid & Festive Fashion Shopper
    user_eid = "USR-00746"
    
    recs_tech = personalized_engine.rerank_for_user(user_tech, base_results, top_k=3)
    recs_eid = personalized_engine.rerank_for_user(user_eid, base_results, top_k=3)
    
    print(f"\nQuery: \"{test_query}\"")
    print(f"\nUser A: {user_tech} (Sadia Farooqi - Loyal Tech & Electronics Buyer)")
    print("-" * 65)
    for idx, r in enumerate(recs_tech, 1):
        print(f" {idx}. [{r['category']}] {r['title']} — Rs. {r['price_pkr']:,}")
        print(f"    Personalization Factor: {r['personalization_reason']}")
        
    print(f"\nUser B: {user_eid} (Ahmed Mirza - Eid & Festive Season Fashion Shopper)")
    print("-" * 65)
    for idx, r in enumerate(recs_eid, 1):
        print(f" {idx}. [{r['category']}] {r['title']} — Rs. {r['price_pkr']:,}")
        print(f"    Personalization Factor: {r['personalization_reason']}")


if __name__ == "__main__":
    search_eng = HybridSearchEngine().fit()
    pers_eng = PersonalizedSearchEngine()
    df_eval = run_search_evaluation(search_eng, pers_eng)
    demonstrate_personalized_search(search_eng, pers_eng)

