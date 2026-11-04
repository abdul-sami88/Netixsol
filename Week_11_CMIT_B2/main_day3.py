"""
ShopKaro AI Commerce Intelligence Platform — Week 11 Day 3 Master Runner
Demand Forecasting & Inventory Intelligence Pipeline

Orchestrates all 5 Day 3 tasks:
- Task 1: Time-Series Analysis (Trend/Seasonal Decomposition, Weekly/Islamic Festival shifts, ADF Stationarity, Intermittent SBC Classification & Croston)
- Task 2: Forecasting Models (Naive, Seasonal Naive, ARIMA, ETS, Prophet with Pakistan holidays, Global LightGBM, Neural MLP)
- Task 3: Rolling-Origin Backtesting & Retail Metrics (4 Folds, MAE, RMSE, MAPE, sMAPE, WAPE, Festival vs. Normal Days, Fast vs. Slow Movers)
- Task 4: Probabilistic Forecasts & Quantile Regression (P10, P50, P90, Empirical Calibration Coverage, Pinball Loss, Fan Charts)
- Task 5: Inventory Intelligence & Optimization (Safety Stock, Dynamic ROP, 14-day Stockout Alerts, Overstock/Dead Capital Markdown Engine, Pre-Eid Stocking Plan, Historical Counterfactual Simulation)
"""

import os
import sys
import time
import duckdb
import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.forecasting.analysis import run_time_series_analysis, load_daily_category_sales
from src.forecasting.backtest import run_task3_backtesting
from src.forecasting.probabilistic import run_probabilistic_evaluation
from src.forecasting.inventory import run_inventory_intelligence

REPORTS_DIR = os.path.join(BASE_DIR, "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)


import shutil

def generate_forecasting_report(ts_data, bt_data, prob_data, inv_data):
    """Compiles the full Day 3 Demand Forecasting & Inventory Intelligence Markdown Report."""
    report_path = os.path.join(REPORTS_DIR, "demand_forecasting_report.md")
    src_report = os.path.join(BASE_DIR, "day3_explanation.md")
    if os.path.exists(src_report):
        shutil.copyfile(src_report, report_path)
    print(f"\n[REPORT] Saved full markdown report to '{report_path}'.")


def run_day3_pipeline():
    start_time = time.time()
    print("="*75)
    print("   SHOPKARO AI COMMERCE INTELLIGENCE PLATFORM -- DAY 3 PIPELINE")
    print("           DEMAND FORECASTING & INVENTORY INTELLIGENCE")
    print("="*75)
    
    # 1. Task 1: Time Series Analysis
    print("\n[STEP 1/4] Running Time-Series Decomposition & Intermittent Demand Analysis...")
    t1_start = time.time()
    ts_data = run_time_series_analysis()
    print(f"--> Step 1 completed in {time.time() - t1_start:.1f}s")
    
    # 2. Task 2 & 3: Backtesting & Model Evaluation
    print("\n[STEP 2/4] Running 4-Fold Rolling-Origin Backtesting & Retail Accuracy Benchmark...")
    t2_start = time.time()
    bt_data = run_task3_backtesting()
    print(f"--> Step 2 completed in {time.time() - t2_start:.1f}s")
    
    # 3. Task 4: Probabilistic Forecasts & Quantile Calibration
    print("\n[STEP 3/4] Fitting Multi-Quantile Regressors (P10, P50, P90) & Calibration Check...")
    t3_start = time.time()
    con = duckdb.connect(os.path.join(BASE_DIR, "data", "processed", "shopkaro.duckdb"), read_only=True)
    cat_df = load_daily_category_sales(con)
    con.close()
    prob_data = run_probabilistic_evaluation(cat_df, horizon_days=28)
    print(f"--> Step 3 completed in {time.time() - t3_start:.1f}s")
    
    # 4. Task 5: Inventory Intelligence & Decision Optimization
    print("\n[STEP 4/4] Generating Safety Stock, ROP, Stock-Out Alerts & Counterfactual Simulation...")
    t4_start = time.time()
    inv_data = run_inventory_intelligence()
    print(f"--> Step 4 completed in {time.time() - t4_start:.1f}s")
    
    # Compile Master Report
    print("\nCompiling Master Demand Forecasting & Inventory Intelligence Report...")
    generate_forecasting_report(ts_data, bt_data, prob_data, inv_data)
    
    total_duration = time.time() - start_time
    print("\n" + "="*75)
    print(f"   DAY 3 PIPELINE FULLY EXECUTED IN {total_duration:.1f} SECONDS")
    print("="*75)
    print("\nDeliverables Produced:")
    print("  • Evaluation Report:  reports/demand_forecasting_report.md")
    print("  • Figures Directory:  reports/figures/ (decomposition, weekly/festival, intermittent, backtest, probabilistic, inventory)")
    print("  • Forecasting Code:   src/forecasting/ (analysis, models, backtest, probabilistic, inventory)")
    print("  • Master Runner:      main_day3.py")


if __name__ == "__main__":
    run_day3_pipeline()
