"""
ShopKaro AI Commerce Intelligence Platform — Week 11 Day 4 Master Runner
Smart Search, Shopping Assistant & Review Intelligence Pipeline

Orchestrates all 5 Day 4 tasks:
- Task 1: Hybrid Search (BM25 + Multilingual Semantic Vectors + RRF + Cross-Encoder Candidate Reranker + Query Understanding + 50-Query Benchmark)
- Task 2: Personalized Search (Day 2 user profile re-ranking: Category Affinity, Price Proximity, Segment Boost, Brand History)
- Task 3: UrduLish Shopping Assistant (Grounding Agent with 6 verified tools: zero-hallucination policy)
- Task 4: Review Intelligence (Multilingual Sentiment Classification, 6-Aspect ABSA, NMF Topic Discovery, Fake/Spam Review Detection)
- Task 5: Seller & Management Insights (Category/Seller Complaint Drivers, Falling Sentiment Degradation, Delivery Bottlenecks, Weekly Report)
"""


import os
import sys
import time
import shutil
import duckdb
import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.search.query_parser import QueryUnderstandingEngine
from src.search.hybrid_search import HybridSearchEngine
from src.search.personalized_search import PersonalizedSearchEngine
from src.search.evaluate_search import run_search_evaluation
from src.assistant.shopping_assistant import UrduLishShoppingAssistant
from src.review_intelligence.sentiment_absa import ReviewIntelligenceEngine
from src.review_intelligence.topic_and_spam import TopicDiscoveryEngine, FakeReviewDetector
from src.review_intelligence.management_insights import ManagementInsightsEngine

REPORTS_DIR = os.path.join(BASE_DIR, "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)


def run_day4_pipeline():
    start_time = time.time()
    print("=" * 80)
    print("      SHOPKARO AI COMMERCE INTELLIGENCE PLATFORM -- DAY 4 PIPELINE")
    print("      SMART SEARCH, SHOPPING ASSISTANT & REVIEW INTELLIGENCE")
    print("=" * 80)

    # ---------------------------------------------------------
    # STEP 1: TASK 1 — HYBRID SEARCH & 50-QUERY BENCHMARK
    # ---------------------------------------------------------
    print("\n[STEP 1/5] Task 1: Evaluating Hybrid Search Engine & Query Understanding...")
    t1_start = time.time()
    
    search_engine = HybridSearchEngine().fit()
    pers_engine = PersonalizedSearchEngine()
    
    # Run 50 labelled queries benchmark
    benchmark_df = run_search_evaluation(search_engine, pers_engine)
    print(f"\n--> Step 1 completed in {time.time() - t1_start:.1f}s")

    # ---------------------------------------------------------
    # STEP 2: TASK 2 — PERSONALISED SEARCH DEMONSTRATION
    # ---------------------------------------------------------
    print("\n" + "=" * 80)
    print("[STEP 2/5] Task 2: Personalised Search Demonstration Across User Profiles...")
    t2_start = time.time()
    
    test_query = "eid gift collection under 15000"
    base_results = search_engine.search(test_query, top_k=50, mode="hybrid_cross")
    
    user_a = "USR-00042"  # Sadia Farooqi (Loyal Tech Buyer)
    user_b = "USR-00746"  # Ahmed Mirza (Eid Shopper - Fashion)

    print(f"\nQuery: '{test_query}'")
    print("-" * 75)
    
    for uid in [user_a, user_b]:
        if uid in pers_engine.user_features.index:
            u_prof = pers_engine.user_features.loc[uid]
            u_seg = u_prof.get("segment_name", "General")
            u_fav = u_prof.get("favourite_category", "None")
        else:
            u_seg = "General"
            u_fav = "None"
            
        print(f"\n👤 User: {uid} | Segment: {u_seg} | Fav Category: {u_fav}")
        res = pers_engine.rerank_for_user(uid, base_results, top_k=3)
        for idx, item in enumerate(res, 1):
            print(f"  {idx}. [{item['category']}] {item['title'][:42]}... | Rs. {item['price_pkr']:,} | Score: {item['personalized_score']}")
            print(f"     Reason: {item['personalization_reason']}")

    print(f"\n--> Step 2 completed in {time.time() - t2_start:.1f}s")

    # ---------------------------------------------------------
    # STEP 3: TASK 3 — URDULISH SHOPPING ASSISTANT DEMO
    # ---------------------------------------------------------
    print("\n" + "=" * 80)
    print("[STEP 3/5] Task 3: UrduLish Conversational Shopping Assistant (Zero-Hallucination)...")
    t3_start = time.time()
    
    from src.assistant.shopping_assistant import ShoppingAssistantTools
    assistant_tools = ShoppingAssistantTools(search_engine=search_engine)
    bot = UrduLishShoppingAssistant(tools=assistant_tools)
    
    sample_dialogue = [
        "Ammi ke liye Eid gift chahiye, 3000 tak.",
        "PROD-00001 kaisa hai? Reviews batayein.",
        "PROD-00001 ko cart mein add kardo",
        "Mera order status check karo."
    ]
    
    simulated_user = "USR-00746"
    for user_msg in sample_dialogue:
        print(f"\n🗣️ Customer: \"{user_msg}\"")
        reply = bot.chat(user_msg, user_id=simulated_user)
        print(f"🤖 Assistant:\n{reply}")

    print(f"\n--> Step 3 completed in {time.time() - t3_start:.1f}s")

    # ---------------------------------------------------------
    # STEP 4: TASK 4 — REVIEW INTELLIGENCE (SENTIMENT, ABSA, TOPICS, SPAM)
    # ---------------------------------------------------------
    print("\n" + "=" * 80)
    print("[STEP 4/5] Task 4: Multilingual Review Intelligence, ABSA, Topics & Spam...")
    t4_start = time.time()
    
    rev_engine = ReviewIntelligenceEngine()
    topic_engine = TopicDiscoveryEngine(n_topics=5)
    spam_detector = FakeReviewDetector()
    
    # Load sample reviews from DuckDB
    conn = duckdb.connect(os.path.join(BASE_DIR, "data", "processed", "shopkaro.duckdb"), read_only=True)
    df_rev = conn.execute("SELECT review_id, product_id, user_id, rating, review_text, sentiment, created_at FROM reviews").df()
    conn.close()
    
    print(f"Loaded {len(df_rev):,} multilingual customer reviews (English, Roman Urdu, Urdu script).")
    
    # A. Aspect-Based Sentiment Analysis on Sample Customer Reviews
    print("\n--- Aspect-Based Sentiment Analysis (ABSA) Examples ---")
    test_texts = [
        "Kapre ki quality bohot zabardast hai lekin delivery 4 din late thi aur packing phati hui thi.",
        "Bohat bekar product hai, screen kharab thi aur seller ne koi reply nahi diya.",
        "Original sound quality, fast shipping, paisa wasool product!"
    ]
    for txt in test_texts:
        sent, conf = rev_engine.classify_sentiment(txt)
        aspects = rev_engine.extract_aspect_sentiment(txt)
        active_aspects = {k: v["sentiment"] for k, v in aspects.items() if v["mentioned"]}
        print(f"\nText: \"{txt}\"")
        print(f"Sentiment: {sent.upper()} (Confidence: {conf})")
        print(f"Extracted Aspects: {active_aspects}")

    # B. Topic Discovery with NMF
    print("\n--- Latent Review Topics Discovered via NMF ---")
    topics = topic_engine.fit_topics(df_rev)
    for top in topics:
        print(f"Topic {top['topic_id']}: {top['topic_name']} ({top['prevalence_pct']}% prevalence)")
        print(f"  Keywords: {', '.join(top['top_keywords'][:6])}")

    # C. Fake & Spam Review Detection
    print("\n--- Fake & Spam Review Detection ---")
    spam_results = spam_detector.detect_spam(df_rev)
    spam_flagged = spam_results[spam_results["is_spam"]]
    print(f"Total Reviews Evaluated: {len(df_rev):,}")
    print(f"Suspicious / Fraudulent Reviews Flagged: {len(spam_flagged):,} ({len(spam_flagged)/len(df_rev)*100:.1f}%)")
    if not spam_flagged.empty:
        sample_spam = spam_flagged.iloc[0]
        print(f"Sample Flagged Text: \"{sample_spam['review_text']}\"")
        print(f"Reasons: {sample_spam['spam_reason']}")

    # D. Auto-Generated 'What Customers Say' Summary
    print("\n--- Auto-Generated 'What Customers Say' Summary ---")
    prod_sample_id = "PROD-00001"
    prod_revs = df_rev[df_rev["product_id"] == prod_sample_id]
    summary_text = rev_engine.generate_product_summary(prod_revs, product_title="Khaadi Classic Lawn Kurti")
    print(summary_text)

    print(f"\n--> Step 4 completed in {time.time() - t4_start:.1f}s")

    # ---------------------------------------------------------
    # STEP 5: TASK 5 — SELLER & MANAGEMENT INSIGHTS REPORT
    # ---------------------------------------------------------
    print("\n" + "=" * 80)
    print("[STEP 5/5] Task 5: Generating Seller & Management Insights Report...")
    t5_start = time.time()
    
    mgmt_engine = ManagementInsightsEngine()
    report_file = mgmt_engine.generate_weekly_report()
    
    print(f"\nTop Category Complaints:")
    top_cat = mgmt_engine.get_top_complaints_by_category(top_n=3)
    print(top_cat[["category", "total_reviews", "Delivery Complaint %", "Size Fit Complaint %"]])
    
    print(f"\nTop Delivery Bottleneck Sellers:")
    deliv_bottlenecks = mgmt_engine.detect_delivery_bottlenecks(top_n=3)
    print(deliv_bottlenecks[["brand", "total_reviews", "delivery_complaint_rate_%", "avg_rating"]])

    print(f"\nWeekly Management Report successfully generated at: {report_file}")
    print(f"--> Step 5 completed in {time.time() - t5_start:.1f}s")

    # Copy report & explanation
    src_exp = os.path.join(BASE_DIR, "day4_explanation.md")
    dest_exp = os.path.join(REPORTS_DIR, "day4_explanation.md")
    if os.path.exists(src_exp):
        shutil.copyfile(src_exp, dest_exp)
        print(f"Copied explanation guide to: {dest_exp}")

    total_duration = time.time() - start_time
    print("\n" + "=" * 80)
    print(f"DAY 4 PIPELINE COMPLETED SUCCESSFULLY IN {total_duration:.1f} SECONDS!")
    print("=" * 80)


if __name__ == "__main__":
    run_day4_pipeline()
