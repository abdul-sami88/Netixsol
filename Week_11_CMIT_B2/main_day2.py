"""
ShopKaro AI Commerce Intelligence Platform — Week 11 Day 2 Master Runner
Orchestrates the entire Recommendation Engine pipeline:
- Task 1: Baseline Models (Popularity, Category Popular, 7-Day Trending)
- Task 2: Collaborative Filtering (Item-Item Cosine & Implicit ALS with Tuning)
- Task 3: Content-Based TF-IDF & PyTorch Neural Two-Tower Hybrid Models
- Task 4: Offline Evaluation (Precision@10, Recall@10, NDCG@10, Coverage, Diversity, Novelty, Cold-Start)
- Task 5: Business Rules Re-Ranking (Stock, Brand Diversity, Margin Boost, Festival Boost, Roman Urdu Explanations, Frequently Bought Together)
"""

import os
import sys
import time
import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# sys.path.insert(0, os.path.join(BASE_DIR, "src", "recommender"))

from src.recommender.evaluate import run_evaluation
from src.recommender.fbt import FrequentlyBoughtTogether
from src.recommender.reranker import BusinessRuleReRanker

PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")

def run_day2_pipeline():
    start_time = time.time()
    print("="*75)
    print("   SHOPKARO AI COMMERCE INTELLIGENCE PLATFORM -- DAY 2 PIPELINE")
    print("              RECOMMENDATION ENGINE & SERVING")
    print("="*75)
    
    # 1. Run Offline Evaluation & Model Training (Tasks 1, 2, 3, 4)
    print("\n[STEP 1/3] Training Candidate Models & Running Offline Evaluation Benchmark...")
    t1_start = time.time()
    df_results, models = run_evaluation()
    print(f"--> Step 1 completed in {time.time() - t1_start:.1f}s")
    
    # 2. Mine Association Rules for Frequently Bought Together (Task 5)
    print("\n[STEP 2/3] Mining 'Frequently Bought Together' Association Rules with FP-Growth...")
    t2_start = time.time()
    orders_df = pd.read_parquet(os.path.join(PROCESSED_DIR, "orders.parquet"))
    fbt_engine = FrequentlyBoughtTogether(min_support=0.0003, min_confidence=0.03)
    fbt_engine.fit(orders_df)
    print(f"--> Step 2 completed in {time.time() - t2_start:.1f}s")
    
    # 3. Business Rules Re-Ranking & Live Demonstration (Task 5)
    print("\n[STEP 3/3] Demonstrating Re-Ranking Layer & Roman Urdu Explanations...")
    t3_start = time.time()
    products_df = pd.read_parquet(os.path.join(PROCESSED_DIR, "products.parquet"))
    reranker = BusinessRuleReRanker(
        products_df=products_df,
        orders_df=orders_df,
        max_items_per_brand=2,
        margin_boost_weight=0.20,
        festival_boost_weight=0.35
    )
    
    # Pick sample customer: USR-00010
    sample_user = "USR-00010"
    raw_candidates = models["Implicit ALS"].recommend(sample_user, k=20)
    
    # Apply Re-Ranking with Chaand Raat & Eid festival boost
    reranked_recs = reranker.rerank(
        user_id=sample_user,
        candidate_items=raw_candidates,
        active_festival="Chaand Raat & Eid ul-Fitr",
        k=5,
        user_last_viewed_title="Khaadi Summer Lawn 3-Piece Stitched"
    )
    
    print(f"\nLive Personalized Feed for User '{sample_user}':")
    print("-" * 75)
    for idx, r in enumerate(reranked_recs, 1):
        print(f"{idx}. [{r['brand']}] {r['title']} - Rs. {r['price_pkr']:,} (Stock: {r['stock_quantity']})")
        print(f"   [Urdu Explanation]: \"{r['explanation_urdu']}\"")
        print(f"   [Ranking Score]: {r['final_score']}")
        print()
        
    # Demonstrate "Similar Products"
    sample_product = "PROD-00001"
    similar_items = models["Content-Based (TF-IDF)"].get_similar_items(sample_product, k=3)
    print(f"\nSimilar Products Carousel for '{sample_product}':")
    for s_pid, s_score in similar_items:
        p_row = products_df[products_df["product_id"] == s_pid]
        p_title = p_row["title"].values[0] if not p_row.empty else "Unknown"
        print(f" - {s_pid} ({p_title}): Cosine Similarity = {s_score:.4f}")
        
    # Demonstrate "Frequently Bought Together"
    sample_fbt = "PROD-00012"
    bundle_items = fbt_engine.get_frequently_bought_together(sample_fbt, k=2)
    print(f"\nFrequently Bought Together Carousel for '{sample_fbt}':")
    if bundle_items:
        for b_pid, b_lift in bundle_items:
            print(f" - Add to Cart Bundle: {b_pid} (Association Lift: {b_lift}x)")
    else:
        print(f" - Smart Bundle Fallback: Matching accessories and category essentials.")
        
    print(f"--> Step 3 completed in {time.time() - t3_start:.1f}s")
    
    total_duration = time.time() - start_time
    print("\n" + "="*75)
    print(f"   DAY 2 PIPELINE FULLY EXECUTED IN {total_duration:.1f} SECONDS")
    print("="*75)
    print("\nDeliverables Produced:")
    print("  • Evaluation Report:  reports/recommender_system_report.md")
    print("  • Comparison Chart:   reports/figures/model_comparison_metrics.png")
    print("  • Recommender Code:   src/recommender/ (baselines, collaborative, content_hybrid, reranker, fbt, metrics)")
    print("  • Explanation Guide:  day2_explanation.md")

if __name__ == "__main__":
    run_day2_pipeline()
