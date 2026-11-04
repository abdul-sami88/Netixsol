"""
ShopKaro AI Commerce Intelligence Platform — Week 11 Day 1 Master Runner
Orchestrates the entire Data Foundation, Analytics & Segmentation pipeline:
- Task 1: Data Pipeline, Cleaning, 30-min Sessionization & DuckDB Ingestion
- Task 2: Exploratory Data Analysis (Funnel, Top Brands, Pareto 80/20, Sparsity)
- Task 3: Customer Segmentation (RFM + K-Means 5 Personas)
- Task 4: Cohort Retention Heatmap, Repeat Purchase Rate, 90-day Churn & CLV
- Task 5: User & Item Feature Stores, Chronological Splits & Cold-Start Sets
"""

import os
import sys
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# sys.path.insert(0, os.path.join(BASE_DIR, "src", "data_pipeline"))
# sys.path.insert(0, os.path.join(BASE_DIR, "src", "eda"))
# sys.path.insert(0, os.path.join(BASE_DIR, "src", "segmentation"))
# sys.path.insert(0, os.path.join(BASE_DIR, "src", "retention"))
# sys.path.insert(0, os.path.join(BASE_DIR, "src", "features"))

from src.data_pipeline.duckdb_loader import load_all_to_duckdb
from src.eda.analysis import run_eda
from src.segmentation.rfm_clustering import run_segmentation
from src.retention.cohort_analysis import run_cohort_analysis
from src.features.feature_store import build_features_and_splits

def run_day1_pipeline():
    start_time = time.time()
    print("="*75)
    print("   SHOPKARO AI COMMERCE INTELLIGENCE PLATFORM — DAY 1 PIPELINE")
    print("="*75)
    
    # Task 1: Data Foundation & Ingestion
    print("\n[STEP 1/5] Executing Task 1: Data Pipeline & DuckDB Ingestion...")
    t1_start = time.time()
    load_all_to_duckdb()
    print(f"--> Step 1 completed in {time.time() - t1_start:.1f}s")
    
    # Task 2: Exploratory Data Analysis
    print("\n[STEP 2/5] Executing Task 2: Exploratory Data Analysis & Visualizations...")
    t2_start = time.time()
    run_eda()
    print(f"--> Step 2 completed in {time.time() - t2_start:.1f}s")
    
    # Task 3: Customer Segmentation (RFM + K-Means)
    print("\n[STEP 3/5] Executing Task 3: Customer Segmentation & Personas...")
    t3_start = time.time()
    run_segmentation()
    print(f"--> Step 3 completed in {time.time() - t3_start:.1f}s")
    
    # Task 4: Cohort & Retention Analysis
    print("\n[STEP 4/5] Executing Task 4: Cohort Retention, Repeat Rates & CLV...")
    t4_start = time.time()
    run_cohort_analysis()
    print(f"--> Step 4 completed in {time.time() - t4_start:.1f}s")
    
    # Task 5: Feature Engineering & Splits
    print("\n[STEP 5/5] Executing Task 5: Feature Stores, Chronological & Cold-Start Splits...")
    t5_start = time.time()
    build_features_and_splits()
    print(f"--> Step 5 completed in {time.time() - t5_start:.1f}s")
    
    total_duration = time.time() - start_time
    print("\n" + "="*75)
    print(f"   DAY 1 PIPELINE FULLY EXECUTED IN {total_duration:.1f} SECONDS")
    print("="*75)
    print("\nDeliverables Produced:")
    print("  • Database:   data/processed/shopkaro.duckdb (9 indexed tables)")
    print("  • Figures:    reports/figures/ (5 high-resolution analytical PNG charts)")
    print("  • Reports:    reports/er_diagram.md")
    print("                reports/eda_insights.md")
    print("                reports/customer_personas.md")
    print("                reports/cohort_clv_report.md")
    print("                reports/feature_store_and_splits.md")
    print("  • Datasets:   data/processed/splits/ (train, val, test, cold-users, cold-items)")

if __name__ == "__main__":
    run_day1_pipeline()
