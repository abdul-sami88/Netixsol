"""
src/lead_scoring_models.py
===========================
Comprehensive Machine Learning suite for Day 3: Lead Scoring Model (Classification) & Explainability.

Implements:
1. Model training & comparison: Logistic Regression, Random Forest, XGBoost, LightGBM
2. Imbalance management: Baseline, Balanced Class Weights, SMOTE, Threshold Optimization
3. Metrics & Evaluation: Precision, Recall, F1, ROC-AUC, PR-AUC, Confusion Matrix, Precision@Top-20%, Calibration Curve
4. Business Cost-Sensitive Threshold Analysis (Cost of False Negative vs False Positive)
5. Lead Segmentation (Hot / Warm / Cold) & Unsupervised K-Means Customer Personas
6. Model Explainability with SHAP (Global Beeswarm, Local Waterfall, UrduLish Natural Language Generator)
7. Algorithmic Fairness & Bias Audit across Cities and Lead Acquisition Sources
"""

import os
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple, Any, Optional

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix,
    brier_score_loss,
    roc_curve,
    precision_recall_curve
)
from sklearn.calibration import calibration_curve
from imblearn.over_sampling import SMOTE
import shap

# Styling configuration for professional reports
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams["font.sans-serif"] = "DejaVu Sans"
plt.rcParams["font.size"] = 10
plt.rcParams["axes.edgecolor"] = "#cccccc"
plt.rcParams["axes.linewidth"] = 0.8


# ========================================================
# 1. Classification Metrics & Precision@Top-K
# ========================================================
def compute_classification_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_prob: np.ndarray,
    top_k_pct: float = 0.20
) -> Dict[str, float]:
    """
    Computes complete set of classification metrics including Precision@Top-K.
    Top-K represents the top percentage of leads prioritized by predicted probability
    (e.g., top 20% represents calling 40 out of 200 leads).
    """
    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    roc_auc = roc_auc_score(y_true, y_prob)
    pr_auc = average_precision_score(y_true, y_prob)
    brier = brier_score_loss(y_true, y_prob)

    # Precision@Top-K% calculation
    n_total = len(y_true)
    k_count = max(1, int(n_total * top_k_pct))
    top_k_indices = np.argsort(y_prob)[::-1][:k_count]
    actual_conversions_in_top_k = y_true[top_k_indices].sum()
    prec_at_top_k = float(actual_conversions_in_top_k / k_count)
    base_rate = float(y_true.mean())
    lift_at_top_k = float(prec_at_top_k / (base_rate + 1e-6))

    cm = confusion_matrix(y_true, y_pred)
    tn, fp, fn, tp = cm.ravel()

    return {
        "Accuracy": float(acc),
        "Precision": float(prec),
        "Recall": float(rec),
        "F1": float(f1),
        "ROC_AUC": float(roc_auc),
        "PR_AUC": float(pr_auc),
        "Brier_Score": float(brier),
        "Precision_Top20": float(prec_at_top_k),
        "Lift_Top20": float(lift_at_top_k),
        "TN": int(tn),
        "FP": int(fp),
        "FN": int(fn),
        "TP": int(tp)
    }


# ========================================================
# 2. Task 1: Train & Compare Classification Models
# ========================================================
def train_and_eval_classifiers(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray
) -> Tuple[pd.DataFrame, Dict[str, Any], Dict[str, np.ndarray]]:
    """
    Trains and compares core classification algorithms:
    - Logistic Regression (Regularized Baseline)
    - Random Forest
    - XGBoost
    - LightGBM
    """
    models = {
        "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
        "Random Forest": RandomForestClassifier(n_estimators=150, max_depth=8, random_state=42, n_jobs=-1),
        "XGBoost": XGBClassifier(n_estimators=150, max_depth=5, learning_rate=0.08, eval_metric="logloss", random_state=42, n_jobs=-1),
        "LightGBM": LGBMClassifier(n_estimators=150, max_depth=5, learning_rate=0.08, random_state=42, verbose=-1, n_jobs=-1)
    }

    records = []
    trained_models = {}
    test_probs = {}

    for name, model in models.items():
        t0 = time.time()
        model.fit(X_train, y_train)
        train_time = round(time.time() - t0, 3)

        probs = model.predict_proba(X_test)[:, 1]
        preds = (probs >= 0.50).astype(int)

        metrics = compute_classification_metrics(y_test, preds, probs, top_k_pct=0.20)
        metrics["Model"] = name
        metrics["Train_Time_s"] = train_time
        records.append(metrics)

        trained_models[name] = model
        test_probs[name] = probs

    df_results = pd.DataFrame(records)
    # Order columns logically
    cols_order = ["Model", "Accuracy", "Precision", "Recall", "F1", "ROC_AUC", "PR_AUC", "Precision_Top20", "Lift_Top20", "Brier_Score", "Train_Time_s"]
    df_results = df_results[cols_order].sort_values(by="PR_AUC", ascending=False).reset_index(drop=True)

    return df_results, trained_models, test_probs


# ========================================================
# 3. Task 2: Handling Imbalanced Data Comparison
# ========================================================
def evaluate_imbalance_strategies(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    base_model_cls=LGBMClassifier
) -> Tuple[pd.DataFrame, Dict[str, Any], Dict[str, float]]:
    """
    Compares 4 Imbalance Mitigation Strategies using LightGBM as the benchmark model:
    1. No Balancing (Default cross-entropy loss, threshold = 0.50)
    2. Class Weights (Cost-sensitive scale_pos_weight = neg_count / pos_count)
    3. SMOTE (Synthetic Minority Over-sampling applied strictly to X_train only)
    4. Threshold Tuning (Finding optimal threshold p* on Validation set that maximizes F1)
    """
    neg_count = (y_train == 0).sum()
    pos_count = (y_train == 1).sum()
    scale_weight = float(neg_count / pos_count)

    results = []
    strategy_models = {}
    optimal_thresholds = {"No Balancing": 0.50, "Class Weights": 0.50, "SMOTE": 0.50}

    # Strategy 1: No Balancing
    m1 = LGBMClassifier(n_estimators=150, max_depth=5, learning_rate=0.08, random_state=42, verbose=-1, n_jobs=-1)
    m1.fit(X_train, y_train)
    p1 = m1.predict_proba(X_test)[:, 1]
    met1 = compute_classification_metrics(y_test, (p1 >= 0.50).astype(int), p1)
    met1["Strategy"] = "1. No Balancing (Default)"
    met1["Decision_Threshold"] = 0.50
    results.append(met1)
    strategy_models["No Balancing"] = m1

    # Strategy 2: Class Weights (Cost-Sensitive)
    m2 = LGBMClassifier(n_estimators=150, max_depth=5, learning_rate=0.08, scale_pos_weight=scale_weight, random_state=42, verbose=-1, n_jobs=-1)
    m2.fit(X_train, y_train)
    p2 = m2.predict_proba(X_test)[:, 1]
    met2 = compute_classification_metrics(y_test, (p2 >= 0.50).astype(int), p2)
    met2["Strategy"] = "2. Balanced Class Weights"
    met2["Decision_Threshold"] = 0.50
    results.append(met2)
    strategy_models["Class Weights"] = m2

    # Strategy 3: SMOTE (Oversampling training set only)
    smote = SMOTE(random_state=42)
    X_tr_smote, y_tr_smote = smote.fit_resample(X_train, y_train)
    m3 = LGBMClassifier(n_estimators=150, max_depth=5, learning_rate=0.08, random_state=42, verbose=-1, n_jobs=-1)
    m3.fit(X_tr_smote, y_tr_smote)
    p3 = m3.predict_proba(X_test)[:, 1]
    met3 = compute_classification_metrics(y_test, (p3 >= 0.50).astype(int), p3)
    met3["Strategy"] = "3. SMOTE Oversampling"
    met3["Decision_Threshold"] = 0.50
    results.append(met3)
    strategy_models["SMOTE"] = m3

    # Strategy 4: Threshold Tuning on Model 1
    # Search threshold on Validation set to prevent test data leakage
    val_probs = m1.predict_proba(X_val)[:, 1]
    threshold_candidates = np.linspace(0.10, 0.80, 71)
    best_thresh = 0.50
    best_val_f1 = -1.0

    for th in threshold_candidates:
        f1_val = f1_score(y_val, (val_probs >= th).astype(int), zero_division=0)
        if f1_val > best_val_f1:
            best_val_f1 = f1_val
            best_thresh = float(th)

    optimal_thresholds["Threshold Tuned"] = best_thresh
    p4 = m1.predict_proba(X_test)[:, 1]
    preds4 = (p4 >= best_thresh).astype(int)
    met4 = compute_classification_metrics(y_test, preds4, p4)
    met4["Strategy"] = f"4. Threshold Tuning (p* = {best_thresh:.2f})"
    met4["Decision_Threshold"] = best_thresh
    results.append(met4)
    strategy_models["Threshold Tuned"] = m1

    df_imbalance = pd.DataFrame(results)
    cols = ["Strategy", "Decision_Threshold", "Accuracy", "Precision", "Recall", "F1", "ROC_AUC", "PR_AUC", "Precision_Top20", "Lift_Top20"]
    df_imbalance = df_imbalance[cols].reset_index(drop=True)

    return df_imbalance, strategy_models, optimal_thresholds


# ========================================================
# 4. Task 3: Calibration & Business Cost-Sensitive Decision Analysis
# ========================================================
def compute_business_cost_curve(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    cost_missed_lead_pkr: float = 300_000.0,
    cost_wasted_call_pkr: float = 2_000.0
) -> Tuple[pd.DataFrame, float, float]:
    """
    Calculates expected business loss across candidate decision thresholds:
    - False Negative (FN): Sales rep fails to call a converting client -> Lost Commission (~PKR 300,000)
    - False Positive (FP): Sales rep spends 45 mins dialing an unqualified lead -> Wasted Agent Time (~PKR 2,000)
    - Cost(threshold) = FN(t) * cost_missed_lead_pkr + FP(t) * cost_wasted_call_pkr
    """
    thresholds = np.linspace(0.05, 0.90, 86)
    records = []

    for th in thresholds:
        preds = (y_prob >= th).astype(int)
        cm = confusion_matrix(y_true, preds)
        tn, fp, fn, tp = cm.ravel()

        cost_fn = fn * cost_missed_lead_pkr
        cost_fp = fp * cost_wasted_call_pkr
        total_cost = cost_fn + cost_fp

        records.append({
            "Threshold": round(th, 3),
            "TP": tp,
            "FP": fp,
            "FN": fn,
            "TN": tn,
            "Cost_Missed_Leads_PKR": cost_fn,
            "Cost_Wasted_Calls_PKR": cost_fp,
            "Total_Cost_PKR": total_cost,
            "Total_Cost_Crore": total_cost / 1e7
        })

    df_cost = pd.DataFrame(records)
    best_row = df_cost.loc[df_cost["Total_Cost_PKR"].idxmin()]
    optimal_cost_threshold = float(best_row["Threshold"])
    min_cost_pkr = float(best_row["Total_Cost_PKR"])

    return df_cost, optimal_cost_threshold, min_cost_pkr


# ========================================================
# 5. Task 4: Lead Segmentation & K-Means Customer Personas
# ========================================================
def segment_leads(
    y_prob: np.ndarray,
    hot_threshold: float = 0.65,
    warm_threshold: float = 0.30
) -> pd.Series:
    """
    Categorizes leads into practical operational action tiers:
    - 🔥 Hot (call within 1 hour)
    - 🌤 Warm (call within 24 hours)
    - ❄️ Cold (automated follow-up campaign)
    """
    categories = []
    for p in y_prob:
        if p >= hot_threshold:
            categories.append("Hot (Call within 1h)")
        elif p >= warm_threshold:
            categories.append("Warm (Call within 24h)")
        else:
            categories.append("Cold (Follow-up Drip)")
    return pd.Series(categories, name="lead_priority_tier")


def discover_customer_personas(
    df_leads_raw: pd.DataFrame,
    n_clusters: int = 4,
    random_state: int = 42
) -> Tuple[pd.DataFrame, KMeans, pd.DataFrame]:
    """
    Performs K-Means clustering on behavioral and economic features to discover
    distinct real-estate buyer personas (e.g. Overseas Investors, First-Time Buyers, Suburban Plot Seekers).
    """
    cluster_cols = [
        "budget_pkr",
        "num_calls",
        "avg_call_duration_mins",
        "days_since_first_contact",
        "followup_count",
        "lead_engagement_score",
        "interaction_intensity",
        "budget_to_market_ratio"
    ]

    X_cluster = df_leads_raw[cluster_cols].copy().fillna(0)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_cluster)

    kmeans = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
    cluster_labels = kmeans.fit_predict(X_scaled)

    df_analysis = df_leads_raw.copy()
    df_analysis["cluster"] = cluster_labels

    # Compute persona profile summary
    persona_summaries = []
    for c_id in range(n_clusters):
        subset = df_analysis[df_analysis["cluster"] == c_id]
        mean_budget = subset["budget_pkr"].mean()
        mean_calls = subset["num_calls"].mean()
        mean_duration = subset["avg_call_duration_mins"].mean()
        top_city = subset["preferred_city"].mode()[0] if not subset["preferred_city"].empty else "N/A"
        top_purpose = subset["purpose"].mode()[0] if not subset["purpose"].empty else "N/A"
        top_prop_type = subset["property_type_preferred"].mode()[0] if not subset["property_type_preferred"].empty else "N/A"
        conversion_rate = subset["converted"].mean() if "converted" in subset.columns else 0.0

    # Rank clusters by characteristics for distinctive persona assignment
    cluster_stats = []
    for c_id in range(n_clusters):
        sub = df_analysis[df_analysis["cluster"] == c_id]
        cluster_stats.append({
            "c_id": c_id,
            "mean_budget": sub["budget_pkr"].mean(),
            "mean_engagement": sub["lead_engagement_score"].mean(),
            "mean_intensity": sub["interaction_intensity"].mean(),
            "conv_rate": sub["converted"].mean() if "converted" in sub.columns else 0.0
        })
    df_cstats = pd.DataFrame(cluster_stats)
    highest_budget_cid = df_cstats.sort_values(by="mean_budget", ascending=False).iloc[0]["c_id"]
    highest_conv_cid = df_cstats.sort_values(by="conv_rate", ascending=False).iloc[0]["c_id"]
    lowest_budget_cid = df_cstats.sort_values(by="mean_budget", ascending=True).iloc[0]["c_id"]

    persona_summaries = []
    for c_id in range(n_clusters):
        subset = df_analysis[df_analysis["cluster"] == c_id]
        mean_budget = subset["budget_pkr"].mean()
        top_city = subset["preferred_city"].mode()[0] if not subset["preferred_city"].empty else "N/A"
        top_purpose = subset["purpose"].mode()[0] if not subset["purpose"].empty else "N/A"
        top_prop_type = subset["property_type_preferred"].mode()[0] if not subset["property_type_preferred"].empty else "N/A"
        conversion_rate = subset["converted"].mean() if "converted" in subset.columns else 0.0

        if c_id == highest_budget_cid:
            persona_name = "Overseas / High-Net-Worth Investor"
            playbook = "Dispatch senior VIP portfolio manager; present luxury villas in DHA Phase 6/8 and Emaar Crescent Bay with high ROI."
        elif c_id == highest_conv_cid:
            persona_name = "Ready First-Time Family Buyer"
            playbook = "Fast-track in-person weekend site visit; highlight nearby schools, commercial centers, and possession timelines."
        elif c_id == lowest_budget_cid:
            persona_name = "Budget Plot & File Aspirant"
            playbook = "Send automated WhatsApp catalog of NOC-approved balloted plots, 3-year installment schedules, and low down-payment schemes."
        else:
            persona_name = "Mid-Market Balanced Value Seeker"
            playbook = "Schedule consultative phone demo; present comparative cost-per-marla analysis and mortgage/installment options."

        persona_summaries.append({
            "Cluster_ID": c_id,
            "Persona_Title": persona_name,
            "Count": len(subset),
            "Share_pct": round(len(subset) / len(df_analysis) * 100, 1),
            "Mean_Budget_PKR": round(mean_budget, 0),
            "Top_City": top_city,
            "Top_Purpose": top_purpose,
            "Top_Property_Type": top_prop_type,
            "Conversion_Rate": round(conversion_rate * 100, 1),
            "Recommended_Playbook": playbook
        })

    df_personas = pd.DataFrame(persona_summaries)
    return df_personas, kmeans, df_analysis


# ========================================================
# 6. Task 5: Explainability with SHAP & UrduLish Explanations
# ========================================================
def generate_shap_explanations(
    model: Any,
    X_train_proc: np.ndarray,
    X_test_proc: np.ndarray,
    feature_names: List[str]
) -> Tuple[shap.Explainer, np.ndarray]:
    """
    Computes SHAP values using TreeExplainer for tree ensembles or LinearExplainer for linear models.
    """
    print("Computing SHAP values for global and local explainability...")
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_test_proc)

    # For binary classification, TreeExplainer in shap can return a 2D array (for positive class) or list of two 2D arrays
    if isinstance(shap_values, list):
        shap_pos = shap_values[1]
    elif len(shap_values.shape) == 3:
        shap_pos = shap_values[:, :, 1]
    else:
        shap_pos = shap_values

    return explainer, shap_pos


def explain_lead_plain_language(
    lead_row: pd.Series,
    shap_values_sample: np.ndarray,
    feature_names: List[str],
    pred_prob: float,
    hot_threshold: float = 0.65,
    warm_threshold: float = 0.30
) -> Dict[str, Any]:
    """
    Converts individual SHAP values and lead metadata into clear, bilingual UrduLish plain-language
    sales explanations for agents and managers.
    """
    # Identify top 3 positive drivers and top 2 negative drag factors
    top_pos_idx = np.argsort(shap_values_sample)[::-1][:3]
    top_neg_idx = np.argsort(shap_values_sample)[:2]

    # Map technical feature names to human-readable explanations
    readable_name_map = {
        "visit_booked": "Client ne site visit book ki hui hai",
        "visit_completed": "Client ne site visit mukammal kar li hai",
        "lead_engagement_score": "Call par lambi guftagu aur high engagement",
        "budget_to_market_ratio": "Budget market property rates ke mutabiq realistic hai",
        "num_calls": "Client ne mutaddad dafa rabta kiya",
        "interaction_intensity": "Rozana followup aur sustained rabta",
        "objection_friction_score": "Kam objections aur high interest level",
        "response_time_hours": "Client ki janib se fori response",
        "budget_pkr": "Strong purchasing capacity / budget"
    }

    pos_reasons = []
    for idx in top_pos_idx:
        feat = feature_names[idx]
        val = shap_values_sample[idx]
        if val > 0.02:
            matched_key = next((k for k in readable_name_map if k in feat), feat.replace("num__", "").replace("cat__", ""))
            pos_reasons.append(f"{readable_name_map.get(matched_key, matched_key)} (+{val:.2f})")

    neg_reasons = []
    for idx in top_neg_idx:
        feat = feature_names[idx]
        val = shap_values_sample[idx]
        if val < -0.02:
            matched_key = next((k for k in readable_name_map if k in feat), feat.replace("num__", "").replace("cat__", ""))
            neg_reasons.append(f"{readable_name_map.get(matched_key, matched_key)} ({val:.2f})")

    if pred_prob >= hot_threshold:
        tier = "🔥 Hot"
        action = "Call immediately within 1 hour! High likelihood of closing."
    elif pred_prob >= warm_threshold:
        tier = "🌤 Warm"
        action = "Call within 24 hours. Address objections and offer site visit."
    else:
        tier = "❄️ Cold"
        action = "Add to automated drip marketing and weekly WhatsApp newsletter."

    # Construct fluent bilingual UrduLish narrative
    pos_text = ", ".join(pos_reasons) if pos_reasons else "Koi barha positive indicator nahi mila"
    neg_text = ", ".join(neg_reasons) if neg_reasons else "Koi barha negative factor nahi hai"

    narrative = (
        f"Yeh lead {tier} hai (Conversion Probability: {pred_prob*100:.1f}%).\n"
        f"Kamyabi ke Asbaab (Positive Drivers): {pos_text}.\n"
        f"Rukawatein (Drag Factors): {neg_text}.\n"
        f"Hidayat: {action}"
    )

    return {
        "lead_id": lead_row.get("lead_id", "N/A"),
        "tier": tier,
        "probability_pct": round(pred_prob * 100, 1),
        "narrative": narrative,
        "action": action,
        "positive_drivers": pos_reasons,
        "negative_drags": neg_reasons
    }


# ========================================================
# 7. Algorithmic Fairness & Bias Audit
# ========================================================
def audit_model_fairness(
    df_test_raw: pd.DataFrame,
    y_test: np.ndarray,
    y_pred: np.ndarray,
    y_prob: np.ndarray,
    slice_column: str = "preferred_city"
) -> pd.DataFrame:
    """
    Audits model across categorical slices (e.g., preferred_city, lead_source)
    Checks for:
    - Total leads per group
    - Selection Rate (fraction predicted positive / called)
    - Recall (True Positive Rate per group)
    - Precision per group
    - Disparate Impact Ratio (relative to highest selection rate group)
    """
    slices = df_test_raw[slice_column].unique()
    records = []

    for sl in slices:
        mask = (df_test_raw[slice_column] == sl).values
        if mask.sum() == 0:
            continue

        n_slice = int(mask.sum())
        y_t_s = y_test[mask]
        y_p_s = y_pred[mask]
        y_pr_s = y_prob[mask]

        sel_rate = float(y_p_s.mean())
        rec = float(recall_score(y_t_s, y_p_s, zero_division=0))
        prec = float(precision_score(y_t_s, y_p_s, zero_division=0))
        actual_conv_rate = float(y_t_s.mean())
        roc = float(roc_auc_score(y_t_s, y_pr_s)) if len(np.unique(y_t_s)) > 1 else 1.0

        records.append({
            "Slice_Dimension": slice_column,
            "Group": sl,
            "Sample_Count": n_slice,
            "Actual_Conversion_Rate": round(actual_conv_rate * 100, 1),
            "Predicted_Selection_Rate": round(sel_rate * 100, 1),
            "Recall_pct": round(rec * 100, 1),
            "Precision_pct": round(prec * 100, 1),
            "ROC_AUC": round(roc, 4)
        })

    df_fairness = pd.DataFrame(records)
    max_sel = df_fairness["Predicted_Selection_Rate"].max()
    df_fairness["Disparate_Impact_Ratio"] = (
        df_fairness["Predicted_Selection_Rate"] / (max_sel + 1e-5)
    ).round(3)

    return df_fairness.sort_values(by="Sample_Count", ascending=False).reset_index(drop=True)


# ========================================================
# 8. Visual Diagnostic Plots
# ========================================================
def plot_roc_and_pr_curves(
    y_test: np.ndarray,
    probs_dict: Dict[str, np.ndarray],
    output_path: str
):
    """Plots combined ROC and Precision-Recall Curves for all benchmarked models."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    colors = ["#2b5c8f", "#27ae60", "#e67e22", "#9b59b6"]

    for (name, probs), col in zip(probs_dict.items(), colors):
        # ROC Curve
        fpr, tpr, _ = roc_curve(y_test, probs)
        roc_auc = roc_auc_score(y_test, probs)
        ax1.plot(fpr, tpr, label=f"{name} (AUC = {roc_auc:.3f})", color=col, linewidth=2)

        # PR Curve
        prec, rec, _ = precision_recall_curve(y_test, probs)
        pr_auc = average_precision_score(y_test, probs)
        ax2.plot(rec, prec, label=f"{name} (PR-AUC = {pr_auc:.3f})", color=col, linewidth=2)

    # ROC formatting
    ax1.plot([0, 1], [0, 1], "k--", alpha=0.5, label="Random Guess (0.50)")
    ax1.set_title("ROC Curves (Receiver Operating Characteristic)", fontsize=12, fontweight="bold")
    ax1.set_xlabel("False Positive Rate", fontsize=10, fontweight="bold")
    ax1.set_ylabel("True Positive Rate (Recall)", fontsize=10, fontweight="bold")
    ax1.legend(loc="lower right")

    # PR formatting
    no_skill = y_test.mean()
    ax2.plot([0, 1], [no_skill, no_skill], "k--", alpha=0.5, label=f"Base Rate ({no_skill:.2f})")
    ax2.set_title("Precision-Recall Curves (Critical for Imbalance)", fontsize=12, fontweight="bold")
    ax2.set_xlabel("Recall", fontsize=10, fontweight="bold")
    ax2.set_ylabel("Precision", fontsize=10, fontweight="bold")
    ax2.legend(loc="lower left")

    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


def plot_calibration_curves(
    y_test: np.ndarray,
    probs_dict: Dict[str, np.ndarray],
    output_path: str
):
    """Generates reliability calibration diagrams comparing predicted probability to observed frequency."""
    plt.figure(figsize=(8, 6))
    plt.plot([0, 1], [0, 1], "k--", label="Perfectly Calibrated (Ideal)", alpha=0.7)

    colors = ["#2b5c8f", "#27ae60", "#e67e22", "#9b59b6"]
    for (name, probs), col in zip(probs_dict.items(), colors):
        prob_true, prob_pred = calibration_curve(y_test, probs, n_bins=10, strategy="uniform")
        brier = brier_score_loss(y_test, probs)
        plt.plot(prob_pred, prob_true, marker="o", linewidth=2, color=col, label=f"{name} (Brier: {brier:.4f})")

    plt.title("Model Calibration Curve (Reliability Diagram)", fontsize=12, fontweight="bold", pad=12)
    plt.xlabel("Mean Predicted Probability", fontsize=10, fontweight="bold")
    plt.ylabel("Observed Fraction of Conversions", fontsize=10, fontweight="bold")
    plt.legend(loc="upper left")
    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


def plot_cost_threshold_curve(
    df_cost: pd.DataFrame,
    optimal_threshold: float,
    output_path: str
):
    """Plots Total Business Cost (PKR) vs Decision Threshold curve."""
    plt.figure(figsize=(10, 5.5))
    plt.plot(df_cost["Threshold"], df_cost["Total_Cost_Crore"], color="#c0392b", linewidth=2.5, label="Total Business Cost (Crore PKR)")
    plt.plot(df_cost["Threshold"], df_cost["Cost_Missed_Leads_PKR"] / 1e7, color="#e67e22", linestyle="--", label="Cost of Missed Deals (FN @ 3 Lakh PKR)")
    plt.plot(df_cost["Threshold"], df_cost["Cost_Wasted_Calls_PKR"] / 1e7, color="#2980b9", linestyle=":", label="Cost of Wasted Calls (FP @ 2,000 PKR)")

    min_cost_crore = df_cost.loc[df_cost["Threshold"] == optimal_threshold, "Total_Cost_Crore"].values[0]
    plt.axvline(x=optimal_threshold, color="#27ae60", linestyle="-.", linewidth=2, label=f"Optimal Threshold (p* = {optimal_threshold:.2f})")
    plt.scatter([optimal_threshold], [min_cost_crore], color="#27ae60", s=120, zorder=5)

    plt.annotate(
        f"Min Cost: {min_cost_crore:.2f} Cr PKR\nat p* = {optimal_threshold:.2f}",
        xy=(optimal_threshold, min_cost_crore),
        xytext=(optimal_threshold + 0.08, min_cost_crore + 0.4),
        arrowprops=dict(facecolor="#27ae60", shrink=0.08, width=1.5, headwidth=6),
        fontweight="bold"
    )

    plt.title("Business Cost Optimization: Optimal Decision Threshold Analysis", fontsize=12, fontweight="bold")
    plt.xlabel("Probability Decision Threshold", fontsize=10, fontweight="bold")
    plt.ylabel("Expected Financial Cost (Crore PKR)", fontsize=10, fontweight="bold")
    plt.legend(loc="upper right")
    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


def plot_shap_waterfall_scenarios(
    scenarios_data: List[Dict[str, Any]],
    output_path: str
):
    """
    Plots horizontal SHAP contribution breakdown cards for individual lead scenarios
    (Hot Lead, Warm Lead, Cold Lead) showing local decision factors.
    """
    n_scenarios = len(scenarios_data)
    fig, axes = plt.subplots(1, n_scenarios, figsize=(6 * n_scenarios, 6), sharey=False)
    if n_scenarios == 1:
        axes = [axes]

    for ax, item in zip(axes, scenarios_data):
        features = item["top_features"]
        shap_vals = item["top_shap_values"]
        title = item["title"]
        prob = item["probability"]

        # Sort so positive is at top
        y_pos = np.arange(len(features))
        colors = ["#27ae60" if v > 0 else "#e74c3c" for v in shap_vals]

        ax.barh(y_pos, shap_vals, color=colors, alpha=0.85, height=0.6)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(features, fontsize=9, fontweight="bold")
        ax.axvline(x=0, color="#555555", linestyle="--", alpha=0.7)
        ax.set_xlabel("SHAP Impact on Log-Odds", fontsize=9, fontweight="bold")
        ax.set_title(f"{title}\nPredicted Conv Prob: {prob*100:.1f}%", fontsize=11, fontweight="bold", pad=10)

        for i, val in enumerate(shap_vals):
            align = "left" if val >= 0 else "right"
            offset = 0.03 if val >= 0 else -0.03
            ax.text(val + offset, i, f"{val:+.2f}", va="center", ha=align, fontsize=8, fontweight="bold")

    plt.suptitle("Local SHAP Attribution Breakdown across Representative Client Leads", fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
