"""
export_and_save_models.py
==========================
Trains, evaluates, and serializes all production model artifacts and preprocessing
pipelines for Day 4 serving (FastAPI, LangGraph agent, and Streamlit dashboard).

Artifacts saved into `saved_models/`:
1. valuation_pipeline.joblib: ColumnTransformer for property data
2. valuation_champion_model.joblib: Trained LightGBM regression champion
3. valuation_quantile_engine.joblib: PropertyValuationEngine (range & verdict)
4. valuation_shap_explainer.joblib: SHAP TreeExplainer for price predictions
5. leads_pipeline.joblib: ColumnTransformer for leads scoring data
6. leads_champion_model.joblib: Trained LightGBM classification champion
7. leads_shap_explainer.joblib: SHAP TreeExplainer for lead scoring
8. models_metadata.json: Performance metrics, trained dates, schema, versioning
"""

import os
import sys
import json
import time
from datetime import datetime
import joblib
import numpy as np
import pandas as pd

# Add project root and src/ to path
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, ROOT_DIR)
sys.path.insert(0, os.path.join(ROOT_DIR, "src"))

from src.pipeline import (
    split_data_70_15_15,
    build_property_pipeline,
    build_leads_pipeline,
    LEAKAGE_COLUMNS_PROPERTY,
    LEAKAGE_COLUMNS_LEADS
)
from src.feature_engineering import (
    engineer_property_features,
    engineer_leads_features,
    calculate_amenity_score
)
from src.valuation_models import (
    compute_regression_metrics,
    format_crore_lakh,
    PropertyValuationEngine
)
from src.lead_scoring_models import (
    compute_classification_metrics,
    generate_shap_explanations
)
from lightgbm import LGBMRegressor, LGBMClassifier
import shap


def train_and_save_property_models(save_dir: str):
    print("\n" + "=" * 80)
    print(">>> [1/2] TRAINING & SERIALIZING PROPERTY VALUATION ARTIFACTS")
    print("=" * 80)
    
    clean_prop_path = os.path.join(ROOT_DIR, "data_cleaned", "property_listings_cleaned.csv")
    if not os.path.exists(clean_prop_path):
        raise FileNotFoundError(f"Cleaned property dataset not found at: {clean_prop_path}")
        
    df_prop = pd.read_csv(clean_prop_path)
    print(f"Loaded {len(df_prop):,} property records.")

    y_pkr = df_prop["price_pkr"].values
    y_log = np.log1p(y_pkr)
    feature_cols = [c for c in df_prop.columns if c not in LEAKAGE_COLUMNS_PROPERTY + ["price_pkr"]]
    X_raw = df_prop[feature_cols].copy()

    X_train_raw, X_val_raw, X_test_raw, y_train_log, y_val_log, y_test_log = split_data_70_15_15(
        X_raw, pd.Series(y_log), random_state=42
    )
    y_test_pkr = np.expm1(y_test_log.values)

    # 1. Pipeline
    print("Fitting ColumnTransformer pipeline (TargetEncoder for location)...")
    pipeline, raw_feature_names = build_property_pipeline(encoder_type="target")
    X_train_proc = pipeline.fit_transform(X_train_raw, y_train_log.values)
    X_test_proc = pipeline.transform(X_test_raw)
    transformed_feature_names = pipeline.get_feature_names_out().tolist()

    # 2. Champion Regression Model (Tuned LightGBM from Day 2)
    print("Training Champion LightGBM Regressor...")
    champion_model = LGBMRegressor(
        n_estimators=300,
        learning_rate=0.06,
        max_depth=7,
        num_leaves=40,
        subsample=0.85,
        colsample_bytree=0.85,
        reg_alpha=0.1,
        reg_lambda=1.0,
        random_state=42,
        n_jobs=-1,
        verbose=-1
    )
    champion_model.fit(X_train_proc, y_train_log.values)

    # Evaluate
    test_preds_pkr = np.expm1(champion_model.predict(X_test_proc))
    val_metrics = compute_regression_metrics(y_test_pkr, test_preds_pkr)
    print(f"Test Evaluation -> MAE: {format_crore_lakh(val_metrics['MAE_PKR'])} | R²: {val_metrics['R2']:.4f} | MAPE: {val_metrics['MAPE_pct']:.2f}%")

    # 3. Quantile Valuation Engine (80% Confidence Interval)
    print("Training Quantile Valuation Engine for Range & Investment Verdict...")
    quantile_engine = PropertyValuationEngine(confidence_level=0.80)
    quantile_engine.fit(X_train_proc, y_train_log.values)

    # 4. SHAP Explainer
    print("Building SHAP TreeExplainer for valuation model...")
    valuation_explainer = shap.TreeExplainer(champion_model)

    # Save to disk
    pipe_path = os.path.join(save_dir, "valuation_pipeline.joblib")
    model_path = os.path.join(save_dir, "valuation_champion_model.joblib")
    engine_path = os.path.join(save_dir, "valuation_quantile_engine.joblib")
    shap_path = os.path.join(save_dir, "valuation_shap_explainer.joblib")

    joblib.dump(pipeline, pipe_path)
    joblib.dump(champion_model, model_path)
    joblib.dump(quantile_engine, engine_path)
    joblib.dump(valuation_explainer, shap_path)

    print(f"Saved valuation pipeline to: {pipe_path}")
    print(f"Saved champion valuation model to: {model_path}")
    print(f"Saved valuation quantile engine to: {engine_path}")
    print(f"Saved valuation SHAP explainer to: {shap_path}")

    metadata = {
        "model_name": "LightGBM Regressor (Quantile Augmented)",
        "version": "1.0.0",
        "task": "Property Valuation (Regression & Quantile Range)",
        "trained_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "metrics": {
            "MAE_PKR": round(val_metrics["MAE_PKR"], 2),
            "MAE_formatted": format_crore_lakh(val_metrics["MAE_PKR"]),
            "RMSE_PKR": round(val_metrics["RMSE_PKR"], 2),
            "R2": round(val_metrics["R2"], 4),
            "MAPE_pct": round(val_metrics["MAPE_pct"], 2)
        },
        "raw_feature_names": raw_feature_names,
        "transformed_feature_names": transformed_feature_names,
        "supported_cities": sorted(df_prop["city"].unique().tolist()),
        "supported_locations": sorted(df_prop["location"].unique().tolist()),
        "supported_property_types": sorted(df_prop["property_type"].unique().tolist())
    }
    return metadata


def train_and_save_leads_models(save_dir: str):
    print("\n" + "=" * 80)
    print(">>> [2/2] TRAINING & SERIALIZING LEAD SCORING ARTIFACTS")
    print("=" * 80)

    clean_lead_path = os.path.join(ROOT_DIR, "data_cleaned", "leads_scoring_cleaned.csv")
    clean_prop_path = os.path.join(ROOT_DIR, "data_cleaned", "property_listings_cleaned.csv")

    df_leads = pd.read_csv(clean_lead_path)
    df_prop = pd.read_csv(clean_prop_path) if os.path.exists(clean_prop_path) else None

    if "lead_engagement_score" not in df_leads.columns:
        df_leads = engineer_leads_features(df_leads, df_prop)

    y_raw = df_leads["converted"].values
    feature_cols = [c for c in df_leads.columns if c not in LEAKAGE_COLUMNS_LEADS + ["converted"]]
    X_raw = df_leads[feature_cols].copy()

    X_train_raw, X_val_raw, X_test_raw, y_train, y_val, y_test = split_data_70_15_15(
        X_raw, pd.Series(y_raw), stratify=pd.Series(y_raw), random_state=42
    )

    y_train = y_train.values
    y_test = y_test.values

    # 1. Pipeline
    print("Fitting ColumnTransformer pipeline for leads...")
    pipeline, raw_feature_names = build_leads_pipeline()
    X_train_proc = pipeline.fit_transform(X_train_raw)
    X_test_proc = pipeline.transform(X_test_raw)
    transformed_feature_names = pipeline.get_feature_names_out().tolist()

    # 2. Champion Classifier (LightGBM from Day 3)
    print("Training Champion LightGBM Classifier...")
    champion_classifier = LGBMClassifier(
        n_estimators=180,
        max_depth=5,
        learning_rate=0.07,
        random_state=42,
        verbose=-1,
        n_jobs=-1
    )
    champion_classifier.fit(X_train_proc, y_train)

    # Evaluate
    test_probs = champion_classifier.predict_proba(X_test_proc)[:, 1]
    optimal_cost_threshold = 0.35  # Calculated in Day 3 cost-sensitive optimization
    test_preds = (test_probs >= optimal_cost_threshold).astype(int)

    cls_metrics = compute_classification_metrics(y_test, test_preds, test_probs, top_k_pct=0.20)
    print(f"Test Evaluation -> ROC-AUC: {cls_metrics['ROC_AUC']:.4f} | PR-AUC: {cls_metrics['PR_AUC']:.4f} | F1: {cls_metrics['F1']:.4f} | Precision@Top20: {cls_metrics['Precision_Top20']*100:.1f}%")

    # 3. SHAP Explainer
    print("Building SHAP TreeExplainer for lead classifier...")
    lead_explainer = shap.TreeExplainer(champion_classifier)

    # Save artifacts
    pipe_path = os.path.join(save_dir, "leads_pipeline.joblib")
    model_path = os.path.join(save_dir, "leads_champion_model.joblib")
    shap_path = os.path.join(save_dir, "leads_shap_explainer.joblib")

    joblib.dump(pipeline, pipe_path)
    joblib.dump(champion_classifier, model_path)
    joblib.dump(lead_explainer, shap_path)

    print(f"Saved leads pipeline to: {pipe_path}")
    print(f"Saved champion lead scoring model to: {model_path}")
    print(f"Saved leads SHAP explainer to: {shap_path}")

    metadata = {
        "model_name": "LightGBM Classifier",
        "version": "1.0.0",
        "task": "Lead Scoring & Conversion Probability (Classification)",
        "trained_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "optimal_cost_threshold": optimal_cost_threshold,
        "hot_threshold": 0.65,
        "warm_threshold": 0.30,
        "metrics": {
            "ROC_AUC": round(cls_metrics["ROC_AUC"], 4),
            "PR_AUC": round(cls_metrics["PR_AUC"], 4),
            "F1": round(cls_metrics["F1"], 4),
            "Recall": round(cls_metrics["Recall"], 4),
            "Precision": round(cls_metrics["Precision"], 4),
            "Precision_Top20_pct": round(cls_metrics["Precision_Top20"] * 100, 2),
            "Lift_Top20": round(cls_metrics["Lift_Top20"], 2),
            "Brier_Score": round(cls_metrics["Brier_Score"], 4)
        },
        "raw_feature_names": raw_feature_names,
        "transformed_feature_names": transformed_feature_names,
        "supported_lead_sources": sorted(df_leads["lead_source"].dropna().unique().tolist()),
        "supported_cities": sorted(df_leads["preferred_city"].dropna().unique().tolist())
    }
    return metadata


def main():
    save_dir = os.path.join(ROOT_DIR, "saved_models")
    os.makedirs(save_dir, exist_ok=True)

    print("=" * 80)
    print(" SAVING PRODUCTION ARTIFACTS FOR FASTAPI, LANGGRAPH & DASHBOARD")
    print(f" Destination Directory: {save_dir}")
    print("=" * 80)

    val_meta = train_and_save_property_models(save_dir)
    lead_meta = train_and_save_leads_models(save_dir)

    all_metadata = {
        "system_name": "Pakistan Real Estate AI & Valuation Engine",
        "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "property_valuation": val_meta,
        "lead_scoring": lead_meta
    }

    meta_file = os.path.join(save_dir, "models_metadata.json")
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(all_metadata, f, indent=2)

    print(f"\nSaved master model metadata to: {meta_file}")
    print("\n>>> ALL MODELS & PIPELINES SUCCESSFULLY SERIALIZED TO DISK! <<<")


if __name__ == "__main__":
    main()
