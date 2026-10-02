"""
run_day1_pipeline.py
====================
Master orchestrator for Day 1: Data Understanding, Cleaning, EDA & Feature Engineering.
Executes end-to-end workflow and produces all required deliverables:
1. Data Cleaning & Imputation
2. Feature Engineering (12+ features)
3. EDA Visualizations (6 charts saved with business insights)
4. Encoding Comparison (One-Hot vs Target Encoding)
5. Stratified Data Splitting (70/15/15)
6. Scikit-learn Reusable Pipelines
"""

import os
import sys
import pandas as pd
import numpy as np

# Ensure src/ is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from data_cleaning import clean_property_data, clean_leads_data
from feature_engineering import engineer_property_features, engineer_leads_features
from eda import run_all_eda
from pipeline import (
    compare_ohe_vs_target_encoding,
    split_data_70_15_15,
    build_property_pipeline,
    build_leads_pipeline,
    LEAKAGE_COLUMNS_PROPERTY,
    LEAKAGE_COLUMNS_LEADS
)


def main():
    print("=" * 80)
    print(" DAY 1: PAKISTAN REAL ESTATE AI VALUATION & LEAD SCORING PIPELINE")
    print("=" * 80)

    # 1. Paths
    prop_raw_path = "Data/property_listings.csv"
    leads_raw_path = "Data/leads_scoring.csv"
    output_fig_dir = "reports/figures"
    output_data_dir = "data_cleaned"

    os.makedirs(output_fig_dir, exist_ok=True)
    os.makedirs(output_data_dir, exist_ok=True)

    # 2. Data Cleaning & Validation
    print("\n[TASK 1 & 2] Cleaning and Normalizing Raw Datasets...")
    df_prop_raw = pd.read_csv(prop_raw_path)
    df_leads_raw = pd.read_csv(leads_raw_path)

    df_prop_clean = clean_property_data(df_prop_raw, handle_outliers_method="winsorize", verbose=True)
    df_leads_clean = clean_leads_data(df_leads_raw, verbose=True)

    # 3. Exploratory Data Analysis
    print("\n[TASK 3] Generating 6 Production-Grade EDA Visualizations...")
    run_all_eda(prop_path=prop_raw_path, leads_path=leads_raw_path, output_dir=output_fig_dir)

    # 4. Feature Engineering
    print("\n[TASK 4] Engineering 12+ Domain Features Across Datasets...")
    df_prop_feat = engineer_property_features(df_prop_clean)
    df_leads_feat = engineer_leads_features(df_leads_clean, df_prop_clean)

    # Persist Clean & Engineered Datasets
    prop_out = os.path.join(output_data_dir, "property_listings_cleaned.csv")
    leads_out = os.path.join(output_data_dir, "leads_scoring_cleaned.csv")
    df_prop_feat.to_csv(prop_out, index=False)
    df_leads_feat.to_csv(leads_out, index=False)
    print(f"Persisted cleaned & engineered property dataset to: {prop_out} ({len(df_prop_feat)} rows, {df_prop_feat.shape[1]} cols)")
    print(f"Persisted cleaned & engineered leads dataset to: {leads_out} ({len(df_leads_feat)} rows, {df_leads_feat.shape[1]} cols)")

    # 5. Encoding, Scaling & Splitting
    print("\n[TASK 5] High-Cardinality Encoder Comparison & Pipeline Assembly...")
    enc_results = compare_ohe_vs_target_encoding(df_prop_feat)

    print("\n>>> HIGH-CARDINALITY LOCATION ENCODING COMPARISON (32 LOCATIONS):")
    print(f" - One-Hot Encoding: {enc_results['one_hot_encoding']['num_features']} Total Features | Val R²: {enc_results['one_hot_encoding']['val_r2']:.4f} | RMSE: {enc_results['one_hot_encoding']['val_rmse_log']:.4f} | Memory: {enc_results['one_hot_encoding']['memory_kb']:.1f} KB")
    print(f" - Target Encoding:  {enc_results['target_encoding']['num_features']} Total Features | Val R²: {enc_results['target_encoding']['val_r2']:.4f} | RMSE: {enc_results['target_encoding']['val_rmse_log']:.4f} | Memory: {enc_results['target_encoding']['memory_kb']:.1f} KB")

    # Stratified Split for Leads
    print("\n>>> STRATIFIED TRAIN / VAL / TEST SPLIT FOR LEADS (70 / 15 / 15):")
    y_leads = df_leads_feat["converted"]
    X_leads = df_leads_feat.drop(columns=LEAKAGE_COLUMNS_LEADS + ["converted"])
    X_tr_l, X_va_l, X_te_l, y_tr_l, y_va_l, y_te_l = split_data_70_15_15(X_leads, y_leads, stratify=y_leads)

    print(f" - Total Leads: {len(df_leads_feat)}")
    print(f" - Train Set:   {len(X_tr_l)} rows (70.0%) | Positive Rate: {y_tr_l.mean()*100:.2f}%")
    print(f" - Val Set:     {len(X_va_l)} rows (15.0%) | Positive Rate: {y_va_l.mean()*100:.2f}%")
    print(f" - Test Set:    {len(X_te_l)} rows (15.0%) | Positive Rate: {y_te_l.mean()*100:.2f}%")

    # Fit Leads Pipeline
    pipeline_leads, lead_feature_cols = build_leads_pipeline()
    X_tr_proc = pipeline_leads.fit_transform(X_tr_l)
    X_va_proc = pipeline_leads.transform(X_va_l)
    X_te_proc = pipeline_leads.transform(X_te_l)
    print(f"\nLeads Feature Matrix Ready: {X_tr_proc.shape[1]} Transformed Features.")

    # Property Valuation Pipeline
    print("\n>>> REUSABLE PROPERTY VALUATION PIPELINE:")
    y_prop = np.log1p(df_prop_feat["price_pkr"])
    X_prop = df_prop_feat.drop(columns=LEAKAGE_COLUMNS_PROPERTY + ["price_pkr"])
    X_tr_p, X_va_p, X_te_p, y_tr_p, y_va_p, y_te_p = split_data_70_15_15(X_prop, y_prop)

    prop_pipeline, prop_feature_cols = build_property_pipeline(encoder_type="target")
    X_tr_p_proc = prop_pipeline.fit_transform(X_tr_p, y_tr_p)
    X_va_p_proc = prop_pipeline.transform(X_va_p)
    X_te_p_proc = prop_pipeline.transform(X_te_p)
    print(f"Property Feature Matrix Ready: {X_tr_p_proc.shape[1]} Transformed Features.")

    print("\n" + "=" * 80)
    print(" DAY 1 PIPELINE EXECUTION COMPLETED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    main()
