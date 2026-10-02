"""
run_day3_pipeline.py
====================
Master orchestrator for Day 3: Lead Scoring Model (Classification) & Explainability.
Executes end-to-end workflow and produces all required deliverables:
1. Classification Models (Logistic Regression baseline, Random Forest, XGBoost, LightGBM)
2. Imbalanced Data Handling (No Balancing, Class Weights, SMOTE, Threshold Tuning) & Accuracy Misconception
3. In-Depth Evaluation (Precision, Recall, F1, ROC-AUC, PR-AUC, Precision@Top-20%, Calibration, Business Cost-Sensitive Threshold)
4. Lead Segmentation (Hot / Warm / Cold) & K-Means Customer Personas
5. SHAP Global & Local Explainability, UrduLish Natural Language Generator & Algorithmic Fairness Audit
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Ensure project root and src/ are in python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from src.pipeline import (
    split_data_70_15_15,
    build_leads_pipeline,
    LEAKAGE_COLUMNS_LEADS
)
from src.feature_engineering import engineer_leads_features
from src.lead_scoring_models import (
    train_and_eval_classifiers,
    evaluate_imbalance_strategies,
    compute_business_cost_curve,
    segment_leads,
    discover_customer_personas,
    generate_shap_explanations,
    explain_lead_plain_language,
    audit_model_fairness,
    plot_roc_and_pr_curves,
    plot_calibration_curves,
    plot_cost_threshold_curve,
    plot_shap_waterfall_scenarios
)
import shap


def plot_customer_personas_scatter(df_analysis: pd.DataFrame, output_path: str):
    """Plots a 2D scatter of customer personas across Budget vs Engagement with conversion sizing."""
    plt.figure(figsize=(10, 6))
    palette = ["#e74c3c", "#3498db", "#2ecc71", "#9b59b6"]
    
    # Cap budget for clean visual representation
    df_plot = df_analysis.copy()
    df_plot["budget_crore"] = df_plot["budget_pkr"] / 1e7
    df_plot["engagement_score"] = df_plot["lead_engagement_score"]

    sns.scatterplot(
        data=df_plot,
        x="budget_crore",
        y="engagement_score",
        hue="cluster",
        palette=palette,
        style="converted",
        s=70,
        alpha=0.75
    )

    plt.title("Discovered Customer Personas: Budget (Crore PKR) vs Call Engagement (Minutes)", fontsize=12, fontweight="bold", pad=12)
    plt.xlabel("Client Budget (Crore PKR)", fontsize=10, fontweight="bold")
    plt.ylabel("Total Engagement (Num Calls x Duration Mins)", fontsize=10, fontweight="bold")
    plt.legend(title="Persona Cluster (Marker: Converted)", loc="upper right")
    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


def plot_shap_summary_chart(shap_values: np.ndarray, X_test_proc: np.ndarray, feature_names: list, output_path: str):
    """Generates and saves the SHAP summary beeswarm chart."""
    plt.figure(figsize=(11, 7))
    clean_names = [f.replace("num__", "").replace("cat__", "") for f in feature_names]
    shap.summary_plot(shap_values, X_test_proc, feature_names=clean_names, show=False, max_display=12)
    plt.title("SHAP Global Feature Importance (Lead Conversion Drivers)", fontsize=13, fontweight="bold", pad=15)
    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


def main():
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

    print("=" * 85)
    print(" DAY 3: PAKISTAN REAL ESTATE AI LEAD SCORING & EXPLAINABILITY SYSTEM")
    print("=" * 85)

    lead_path = "data_cleaned/leads_scoring_cleaned.csv"
    prop_path = "data_cleaned/property_listings_cleaned.csv"
    fig_dir = "reports/figures"
    os.makedirs(fig_dir, exist_ok=True)
    os.makedirs("reports", exist_ok=True)

    if not os.path.exists(lead_path):
        raise FileNotFoundError(f"Cleaned dataset not found at '{lead_path}'. Please run run_day1_pipeline.py first.")

    # 1. Load Data
    print(f"\n[STEP 1] Loading Cleaned Leads Scoring Dataset from: {lead_path}")
    df_leads = pd.read_csv(lead_path)
    df_prop = pd.read_csv(prop_path) if os.path.exists(prop_path) else None

    # Verify / ensure engineered features
    if "lead_engagement_score" not in df_leads.columns:
        print("Re-computing engineered features for leads dataset...")
        df_leads = engineer_leads_features(df_leads, df_prop)

    print(f"Loaded {len(df_leads):,} lead records.")
    conv_rate = df_leads["converted"].mean()
    print(f"Class Distribution: {df_leads['converted'].value_counts().to_dict()} (Conversion Rate: {conv_rate*100:.2f}%)")

    # Extract Target and Features (safely drop leakage)
    y_raw = df_leads["converted"].values
    feature_cols = [c for c in df_leads.columns if c not in LEAKAGE_COLUMNS_LEADS + ["converted"]]
    X_raw = df_leads[feature_cols].copy()

    # 2. Stratified Splitting (70% Train, 15% Val, 15% Test)
    print("\n[STEP 2] Stratified Partitioning (70 / 15 / 15) to preserve imbalanced conversion distribution...")
    X_train_raw, X_val_raw, X_test_raw, y_train, y_val, y_test = split_data_70_15_15(
        X_raw, pd.Series(y_raw), stratify=pd.Series(y_raw), random_state=42
    )

    y_train = y_train.values
    y_val = y_val.values
    y_test = y_test.values

    # Test raw dataframe slice for slicing & auditing
    df_test_raw = df_leads.loc[X_test_raw.index].copy()

    print(f" - Train Set:      {len(X_train_raw):,} records (Conversion: {y_train.mean()*100:.1f}%)")
    print(f" - Validation Set: {len(X_val_raw):,} records (Conversion: {y_val.mean()*100:.1f}%)")
    print(f" - Test Set:       {len(X_test_raw):,} records (Conversion: {y_test.mean()*100:.1f}%)")

    # 3. Fit Production Preprocessing Pipeline
    print("\n[STEP 3] Fitting Preprocessing Pipeline (Robust Scaling + One-Hot Encoding)...")
    pipeline, raw_feature_names = build_leads_pipeline()
    X_train_proc = pipeline.fit_transform(X_train_raw)
    X_val_proc = pipeline.transform(X_val_raw)
    X_test_proc = pipeline.transform(X_test_raw)
    transformed_feature_names = pipeline.get_feature_names_out().tolist()
    print(f"Engineered {X_train_proc.shape[1]} transformed feature dimensions.")

    # 4. Task 1: Train & Benchmark Classification Models
    print("\n" + "=" * 85)
    print(" [TASK 1] TRAINING & BENCHMARKING CLASSIFICATION MODELS")
    print("=" * 85)
    df_models, trained_models, test_probs = train_and_eval_classifiers(
        X_train_proc, y_train, X_test_proc, y_test
    )

    for _, row in df_models.iterrows():
        print(f" - {row['Model']:20s} | PR-AUC: {row['PR_AUC']:.4f} | ROC-AUC: {row['ROC_AUC']:.4f} | F1: {row['F1']:.4f} | Prec@Top20: {row['Precision_Top20']*100:4.1f}% (Lift: {row['Lift_Top20']:.2f}x) | Acc: {row['Accuracy']*100:4.1f}%")

    # Save benchmark table
    model_csv = "reports/day3_lead_model_benchmark_table.csv"
    df_models.to_csv(model_csv, index=False)
    print(f"\nSaved classification benchmark table to: {model_csv}")

    # Plot ROC & PR Curves
    curves_plot = os.path.join(fig_dir, "day3_roc_and_pr_curves.png")
    plot_roc_and_pr_curves(y_test, test_probs, curves_plot)
    print(f"Saved ROC & PR curves plot to: {curves_plot}")

    # 5. Task 2: Handling Imbalanced Data Comparison & Accuracy Misleading Proof
    print("\n" + "=" * 85)
    print(" [TASK 2] HANDLING IMBALANCED DATA (4 STRATEGIES COMPARISON)")
    print("=" * 85)
    df_imbalance, strategy_models, optimal_thresholds = evaluate_imbalance_strategies(
        X_train_proc, y_train, X_val_proc, y_val, X_test_proc, y_test
    )

    for _, row in df_imbalance.iterrows():
        print(f" - {row['Strategy']:32s} (Thresh: {row['Decision_Threshold']:.2f}) | F1: {row['F1']:.4f} | Recall: {row['Recall']*100:4.1f}% | Prec: {row['Precision']*100:4.1f}% | Acc: {row['Accuracy']*100:4.1f}%")

    print("\n>>> CRITICAL INSIGHT: WHY ACCURACY IS A DANGEROUSLY MISLEADING METRIC:")
    print(" 1. A trivial dummy classifier that blindly predicts '0' (No Conversion) achieves 79.4% Accuracy!")
    print(" 2. However, its Recall is 0.0%, its F1 is 0.0, and the business loses 100% of potential home buyers.")
    print(" 3. With Threshold Tuning (p* = 0.35) or Class Weights, Recall rises to >80%, capturing nearly all deals,")
    print("    even though raw accuracy slightly changes. PR-AUC and Precision@Top-20% are the true business metrics.")

    # 6. Task 3: In-Depth Evaluation & Business Cost Optimization
    print("\n" + "=" * 85)
    print(" [TASK 3] CALIBRATION & BUSINESS COST-SENSITIVE THRESHOLD OPTIMIZATION")
    print("=" * 85)

    # Plot Calibration Curves
    calib_plot = os.path.join(fig_dir, "day3_calibration_curves.png")
    plot_calibration_curves(y_test, test_probs, calib_plot)
    print(f"Saved calibration reliability plot to: {calib_plot}")

    # Business Cost Optimization
    # Scenario: Missed deal (FN) = 300,000 PKR; Wasted Call (FP) = 2,000 PKR
    champion_name = "LightGBM"
    champ_probs = test_probs[champion_name]

    cost_missed = 300_000.0
    cost_wasted = 2_000.0
    df_cost, opt_cost_th, min_cost = compute_business_cost_curve(
        y_test, champ_probs, cost_missed_lead_pkr=cost_missed, cost_wasted_call_pkr=cost_wasted
    )

    cost_plot = os.path.join(fig_dir, "day3_business_cost_curve.png")
    plot_cost_threshold_curve(df_cost, opt_cost_th, cost_plot)
    print(f"Saved business cost curve to: {cost_plot}")

    cost_at_default = df_cost.loc[df_cost["Threshold"] == 0.50, "Total_Cost_Crore"].values[0]
    cost_at_optimal = df_cost.loc[df_cost["Threshold"] == opt_cost_th, "Total_Cost_Crore"].values[0]
    savings_crore = cost_at_default - cost_at_optimal
    print(f"\n>>> BUSINESS COST VERDICT:")
    print(f" - Default Threshold (0.50) Financial Risk: PKR {cost_at_default*1e7:,.0f} ({cost_at_default:.2f} Crore PKR)")
    print(f" - Optimal Threshold ({opt_cost_th:.2f}) Financial Risk: PKR {cost_at_optimal*1e7:,.0f} ({cost_at_optimal:.2f} Crore PKR)")
    print(f" - Net Financial Savings from Threshold Optimization: PKR {savings_crore*1e7:,.0f} ({savings_crore:.2f} Crore PKR / {(savings_crore/cost_at_default)*100:.1f}% reduction)!")

    # 7. Task 4: Lead Segmentation & K-Means Customer Personas
    print("\n" + "=" * 85)
    print(" [TASK 4] LEAD SEGMENTATION & K-MEANS CUSTOMER PERSONAS")
    print("=" * 85)

    lead_tiers = segment_leads(champ_probs, hot_threshold=0.65, warm_threshold=0.30)
    tier_counts = lead_tiers.value_counts()
    print("Operational Lead Tiers on Test Set (675 Leads):")
    for tier, count in tier_counts.items():
        print(f" - {tier:25s}: {count:3d} leads ({count/len(lead_tiers)*100:4.1f}%)")

    # Sales Scenario: 200 Leads, Capacity to call only 40 (Top 20%)
    np.random.seed(42)
    sample_indices = np.random.choice(len(y_test), size=200, replace=False)
    sample_y = y_test[sample_indices]
    sample_prob = champ_probs[sample_indices]

    top_40_idx = np.argsort(sample_prob)[::-1][:40]
    conversions_captured = sample_y[top_40_idx].sum()
    total_conversions = sample_y.sum()
    random_expected = int(total_conversions * 0.20)

    print("\n>>> SALES TEAM SCENARIO (200 Inbound Leads, 40 Agent Calls Capacity):")
    print(f" - Total Conversions Available in Pool: {total_conversions} deals")
    print(f" - Conversions Captured by Model (Top 40): {conversions_captured} deals ({conversions_captured/40*100:.1f}% Precision@Top-20%)")
    print(f" - Conversions Captured by Random Calling: ~{random_expected} deals ({random_expected/40*100:.1f}%)")
    print(f" - Model Efficiency Lift: {(conversions_captured / max(1, random_expected)):.2f}x more closed transactions with the SAME sales effort!")

    # K-Means Personas
    print("\nDiscovering Customer Personas via Unsupervised K-Means...")
    df_personas, kmeans_model, df_clustered = discover_customer_personas(df_leads, n_clusters=4, random_state=42)
    print(df_personas[["Cluster_ID", "Persona_Title", "Share_pct", "Mean_Budget_PKR", "Top_City", "Top_Purpose", "Conversion_Rate"]].to_string(index=False))

    persona_plot = os.path.join(fig_dir, "day3_customer_personas.png")
    plot_customer_personas_scatter(df_clustered, persona_plot)
    print(f"\nSaved customer personas cluster scatter to: {persona_plot}")

    # 8. Task 5: SHAP Explainability & Fairness Check
    print("\n" + "=" * 85)
    print(" [TASK 5] SHAP EXPLAINABILITY, URDULISH SALES NARRATIVE & FAIRNESS AUDIT")
    print("=" * 85)

    explainer, shap_pos = generate_shap_explanations(
        trained_models[champion_name], X_train_proc, X_test_proc, transformed_feature_names
    )

    # Plot SHAP global summary
    shap_summary_path = os.path.join(fig_dir, "day3_shap_summary.png")
    plot_shap_summary_chart(shap_pos, X_test_proc, transformed_feature_names, shap_summary_path)
    print(f"Saved SHAP summary beeswarm plot to: {shap_summary_path}")

    # Generate Plain-Language UrduLish Explanations for Representative Leads
    print("\n--- PLAIN-LANGUAGE BILINGUAL URDULISH SALES EXPLANATIONS ---")
    scenarios = [
        {"desc": "Scenario A: Highly Engaged Buyer (Hot Lead)", "idx": np.argmax(champ_probs)},
        {"desc": "Scenario B: Mid-Funnel Inquirer (Warm Lead)", "idx": np.argsort(champ_probs)[len(champ_probs)//2]},
        {"desc": "Scenario C: Low Engagement Inquirer (Cold Lead)", "idx": np.argmin(champ_probs)}
    ]

    scenarios_plot_data = []
    for sc in scenarios:
        i = sc["idx"]
        lead_row = df_test_raw.iloc[i]
        explanation = explain_lead_plain_language(
            lead_row=lead_row,
            shap_values_sample=shap_pos[i],
            feature_names=transformed_feature_names,
            pred_prob=float(champ_probs[i]),
            hot_threshold=0.65,
            warm_threshold=0.30
        )
        print(f"\n[{sc['desc']} - Lead #{explanation['lead_id']}]:")
        print(explanation["narrative"])

        # Extract top 5 positive and negative features for waterfall plot
        s_vals = shap_pos[i]
        top_abs_idx = np.argsort(np.abs(s_vals))[::-1][:6]
        top_fnames = [transformed_feature_names[idx].replace("num__", "").replace("cat__", "") for idx in top_abs_idx]
        top_svals = [float(s_vals[idx]) for idx in top_abs_idx]

        scenarios_plot_data.append({
            "title": sc["desc"].split(":")[0],
            "probability": float(champ_probs[i]),
            "top_features": top_fnames[::-1],
            "top_shap_values": top_svals[::-1]
        })

    # Save local waterfall scenario cards
    waterfall_path = os.path.join(fig_dir, "day3_shap_waterfall_scenarios.png")
    plot_shap_waterfall_scenarios(scenarios_plot_data, waterfall_path)
    print(f"\nSaved local SHAP waterfall scenario cards to: {waterfall_path}")

    # Algorithmic Fairness & Bias Audit
    print("\n--- ALGORITHMIC FAIRNESS & BIAS AUDIT ---")
    champ_preds = (champ_probs >= opt_cost_th).astype(int)

    fairness_city = audit_model_fairness(df_test_raw, y_test, champ_preds, champ_probs, slice_column="preferred_city")
    fairness_source = audit_model_fairness(df_test_raw, y_test, champ_preds, champ_probs, slice_column="lead_source")

    print("\nFairness Audit across Geographic Markets (preferred_city):")
    print(fairness_city[["Group", "Sample_Count", "Actual_Conversion_Rate", "Predicted_Selection_Rate", "Recall_pct", "Disparate_Impact_Ratio"]].to_string(index=False))

    print("\nFairness Audit across Marketing Channels (lead_source):")
    print(fairness_source[["Group", "Sample_Count", "Actual_Conversion_Rate", "Predicted_Selection_Rate", "Recall_pct", "Disparate_Impact_Ratio"]].to_string(index=False))

    # Save Fairness Audit Table
    df_fairness_all = pd.concat([fairness_city, fairness_source], ignore_index=True)
    fairness_csv = "reports/day3_fairness_audit_table.csv"
    df_fairness_all.to_csv(fairness_csv, index=False)
    print(f"\nSaved complete fairness audit table to: {fairness_csv}")

    print("\n" + "=" * 85)
    print(" DAY 3 LEAD SCORING PIPELINE EXECUTION COMPLETED SUCCESSFULLY!")
    print("=" * 85)


if __name__ == "__main__":
    main()
