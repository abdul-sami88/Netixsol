"""
test_day3_lead_cases.py
=======================
Demonstration of 3 Realistic Production Test Cases for Lead Scoring & Explainability.
Simulates new incoming client leads evaluated by the trained Day 3 Classification & SHAP engine.
"""

import os
import sys
import numpy as np
import pandas as pd

# Ensure project root and src/ are in path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from src.pipeline import (
    split_data_70_15_15,
    build_leads_pipeline,
    LEAKAGE_COLUMNS_LEADS
)
from src.feature_engineering import engineer_leads_features
from src.lead_scoring_models import (
    generate_shap_explanations,
    explain_lead_plain_language,
    segment_leads
)
from lightgbm import LGBMClassifier


def run_test_cases():
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

    print("=" * 85)
    print(" DAY 3: EXECUTING 3 REALISTIC CLIENT LEAD SCORING TEST CASES")
    print("=" * 85)

    lead_path = "data_cleaned/leads_scoring_cleaned.csv"
    prop_path = "data_cleaned/property_listings_cleaned.csv"

    df_leads = pd.read_csv(lead_path)
    df_prop = pd.read_csv(prop_path) if os.path.exists(prop_path) else None

    # Separate features and target
    y_raw = df_leads["converted"].values
    feature_cols = [c for c in df_leads.columns if c not in LEAKAGE_COLUMNS_LEADS + ["converted"]]
    X_raw = df_leads[feature_cols].copy()

    # Stratified Split (70/15/15)
    X_train_raw, X_val_raw, X_test_raw, y_train, y_val, y_test = split_data_70_15_15(
        X_raw, pd.Series(y_raw), stratify=pd.Series(y_raw), random_state=42
    )

    # Fit Pipeline
    pipeline, raw_feature_names = build_leads_pipeline()
    X_train_proc = pipeline.fit_transform(X_train_raw)
    X_test_proc = pipeline.transform(X_test_raw)
    feature_names = pipeline.get_feature_names_out().tolist()

    # Fit Champion Model (LightGBM with Class Weights for optimal Recall)
    neg_count = (y_train.values == 0).sum()
    pos_count = (y_train.values == 1).sum()
    scale_weight = float(neg_count / pos_count)

    model = LGBMClassifier(
        n_estimators=150,
        max_depth=5,
        learning_rate=0.08,
        scale_pos_weight=scale_weight,
        random_state=42,
        verbose=-1,
        n_jobs=-1
    )
    model.fit(X_train_proc, y_train.values)

    # Compute SHAP explainer
    explainer, _ = generate_shap_explanations(model, X_train_proc, X_test_proc[:10], feature_names)

    # ========================================================
    # 3 INCOMING NEW CLIENT LEADS (TEST CASES)
    # ========================================================
    test_cases_raw = pd.DataFrame([
        {
            # TEST CASE 1: High-Net-Worth VIP Investor
            "lead_id": "TEST-LEAD-HOT-01",
            "lead_source": "Referral / Network",
            "budget_pkr": 65_000_000.0,
            "preferred_city": "Lahore",
            "purpose": "Buy (Investment)",
            "property_type_preferred": "House",
            "num_calls": 4,
            "avg_call_duration_mins": 14.5,
            "response_time_hours": 0.5,
            "visit_booked": "Yes",
            "visit_completed": "Yes",
            "days_since_first_contact": 5,
            "objection_raised": "None",
            "followup_count": 4,
            "inquiry_date": "2026-09-28"
        },
        {
            # TEST CASE 2: Middle-Class Value Seeker with Price Objection
            "lead_id": "TEST-LEAD-WARM-02",
            "lead_source": "Facebook Ads",
            "budget_pkr": 24_000_000.0,
            "preferred_city": "Islamabad",
            "purpose": "Buy (Own Use)",
            "property_type_preferred": "House",
            "num_calls": 2,
            "avg_call_duration_mins": 4.0,
            "response_time_hours": 3.0,
            "visit_booked": "Yes",
            "visit_completed": "No",
            "days_since_first_contact": 12,
            "objection_raised": "Price / Budget Constraint",
            "followup_count": 2,
            "inquiry_date": "2026-09-20"
        },
        {
            # TEST CASE 3: Low-Intent Casual Inquirer / Unrealistic Budget
            "lead_id": "TEST-LEAD-COLD-03",
            "lead_source": "Zameen / Graana Portal",
            "budget_pkr": 5_000_000.0,
            "preferred_city": "Karachi",
            "purpose": "Buy (Own Use)",
            "property_type_preferred": "Flat",
            "num_calls": 1,
            "avg_call_duration_mins": 1.2,
            "response_time_hours": 28.0,
            "visit_booked": "No",
            "visit_completed": "No",
            "days_since_first_contact": 30,
            "objection_raised": "Not Interested / Window Shopping",
            "followup_count": 0,
            "inquiry_date": "2026-08-30"
        }
    ])

    # Feature Engineering on Test Cases
    test_cases_feat = engineer_leads_features(test_cases_raw, df_prop)
    X_cases_raw = test_cases_feat[feature_cols].copy()
    X_cases_proc = pipeline.transform(X_cases_raw)

    # Model Inference
    probs = model.predict_proba(X_cases_proc)[:, 1]
    shap_vals = explainer.shap_values(X_cases_proc)
    if isinstance(shap_vals, list):
        shap_cases = shap_vals[1] if len(shap_vals) > 1 else shap_vals[0]
    elif len(shap_vals.shape) == 3:
        shap_cases = shap_vals[:, :, 1]
    else:
        shap_cases = shap_vals

    # Format Output Reports
    case_headers = [
        "TEST CASE 1: High-Net-Worth VIP Investor (DHA / Prime Commercial Deal)",
        "TEST CASE 2: Middle-Class Value Seeker (Family Homebuyer with Budget Constraint)",
        "TEST CASE 3: Low-Intent Portal Clicker (Unrealistic Budget / Window Shopping)"
    ]

    for idx in range(len(test_cases_raw)):
        lead_meta = test_cases_raw.iloc[idx]
        p_val = float(probs[idx])
        s_val = shap_cases[idx]

        exp = explain_lead_plain_language(
            lead_row=lead_meta,
            shap_values_sample=s_val,
            feature_names=feature_names,
            pred_prob=p_val,
            hot_threshold=0.65,
            warm_threshold=0.30
        )

        print("\n" + "=" * 85)
        print(f" {case_headers[idx]}")
        print("=" * 85)
        print(f" Lead ID:          {lead_meta['lead_id']}")
        print(f" Marketing Source: {lead_meta['lead_source']}")
        print(f" Client Budget:    PKR {lead_meta['budget_pkr']:,.0f} ({lead_meta['budget_pkr']/1e7:.2f} Crore) in {lead_meta['preferred_city']}")
        print(f" Interaction:      {lead_meta['num_calls']} calls ({lead_meta['avg_call_duration_mins']} mins avg) | Response Time: {lead_meta['response_time_hours']}h")
        print(f" Visit Status:     Booked: {lead_meta['visit_booked']} | Completed: {lead_meta['visit_completed']}")
        print(f" Objections:       {lead_meta['objection_raised']}")
        print("-" * 85)
        print(f" >>> PREDICTED CONVERSION PROBABILITY: {p_val*100:.1f}%")
        print(f" >>> OPERATIONAL PRIORITY CATEGORY:    {exp['tier']}")
        print(f" >>> RECOMMENDED SALES ACTION / SLA:   {exp['action']}")
        print("-" * 85)
        print(" [SHAP FEATURE ATTRIBUTION]:")
        print("   Positive Drivers: " + (", ".join(exp['positive_drivers']) if exp['positive_drivers'] else "None"))
        print("   Drag Factors:     " + (", ".join(exp['negative_drags']) if exp['negative_drags'] else "None"))
        print("-" * 85)
        print(" [BILINGUAL URDULISH NARRATIVE FOR SALES AGENT]:")
        print(f" \"{exp['narrative']}\"")

    print("\n" + "=" * 85)
    print(" ALL 3 TEST CASES EVALUATED SUCCESSFULLY!")
    print("=" * 85)


if __name__ == "__main__":
    run_test_cases()
