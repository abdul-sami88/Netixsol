"""
src/pipeline.py
===============
Reusable Scikit-learn preprocessing pipelines, high-cardinality encoder comparison
(One-Hot vs Target Encoding), data leakage prevention, and reproducible 70/15/15 train/val/test splitting.
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple, List, Optional
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.model_selection import train_test_split, cross_val_score, KFold, StratifiedKFold
from sklearn.preprocessing import StandardScaler, RobustScaler, OneHotEncoder, TargetEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.metrics import root_mean_squared_error, r2_score, roc_auc_score, f1_score


# ========================================================
# 1. Data Leakage Documentation & Dropper
# ========================================================
LEAKAGE_COLUMNS_PROPERTY = [
    "property_id",            # Non-predictive unique ID
    "listing_date",           # Raw timestamp (temporal leakage)
    "plot_size_unit",         # Redundant metadata string
    "plot_size_display",      # Redundant metadata string
    "amenities",              # Raw text string superseded by weighted_amenity_score
    "price_per_marla",        # TARGET LEAKAGE: Derived directly from target price_pkr!
]

LEAKAGE_COLUMNS_LEADS = [
    "lead_id",                # Non-predictive unique ID
    "inquiry_date",           # Raw timestamp string
    "lead_stage",             # CRITICAL TARGET LEAKAGE: Subjective human label assigned
                              # downstream by sales agents ('Cold', 'Warm', 'Hot').
                              # Inflates validation score but unavailable for new raw leads.
    "market_median_price_pkr" # Intermediate join artifact
]


class LeakageDropper(BaseEstimator, TransformerMixin):
    """Transformer that safely removes non-predictive identifiers and data leakage features."""
    def __init__(self, cols_to_drop: List[str]):
        self.cols_to_drop = cols_to_drop

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X_df = X.copy() if isinstance(X, pd.DataFrame) else pd.DataFrame(X)
        existing_cols = [c for c in self.cols_to_drop if c in X_df.columns]
        return X_df.drop(columns=existing_cols)


# ========================================================
# 2. Train / Validation / Test Splitting (70 / 15 / 15)
# ========================================================
def split_data_70_15_15(
    X: pd.DataFrame,
    y: pd.Series,
    stratify: Optional[pd.Series] = None,
    random_state: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.Series]:
    """
    Partitions dataset into exact Train (70%), Validation (15%), and Test (15%) subsets.
    Supports stratified splitting for imbalanced classification tasks.
    """
    # First split: 70% Train, 30% Temporary (Validation + Test)
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y,
        test_size=0.30,
        random_state=random_state,
        stratify=stratify
    )

    # Second split: Split the 30% temp set 50/50 -> 15% Validation, 15% Test
    stratify_temp = y_temp if stratify is not None else None
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp,
        test_size=0.50,
        random_state=random_state,
        stratify=stratify_temp
    )

    return X_train, X_val, X_test, y_train, y_val, y_test


# ========================================================
# 3. High-Cardinality Encoder Comparison (One-Hot vs Target Encoding)
# ========================================================
def compare_ohe_vs_target_encoding(
    df_prop_feat: pd.DataFrame,
    target_col: str = "price_pkr",
    location_col: str = "location"
) -> Dict[str, any]:
    """
    Compares One-Hot Encoding vs Regularized Target Encoding on high-cardinality location column.
    Evaluates:
    - Dimensionality expansion
    - Memory footprint
    - Out-of-fold predictive power (Ridge Regression R2 and RMSE)
    """
    # Prepare clean data without leakage
    y = np.log1p(df_prop_feat[target_col])
    cols_to_remove = LEAKAGE_COLUMNS_PROPERTY + [target_col]
    feature_cols = [c for c in df_prop_feat.columns if c not in cols_to_remove]
    X = df_prop_feat[feature_cols].copy()

    # Split 70/15/15
    X_train, X_val, X_test, y_train, y_val, y_test = split_data_70_15_15(X, y)

    # Common numerical features
    num_cols = X.select_dtypes(include=[np.number]).columns.tolist()
    other_cat_cols = [c for c in ["city", "property_type", "property_age_bucket", "society_tier"] if c in X.columns]

    # Preprocessor 1: One-Hot Encoding for Location
    preprocessor_ohe = ColumnTransformer(
        transformers=[
            ("num", RobustScaler(), num_cols),
            ("other_cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), other_cat_cols),
            ("loc_ohe", OneHotEncoder(handle_unknown="ignore", sparse_output=False), [location_col])
        ]
    )

    # Preprocessor 2: Target Encoding for Location
    preprocessor_target = ColumnTransformer(
        transformers=[
            ("num", RobustScaler(), num_cols),
            ("other_cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), other_cat_cols),
            ("loc_target", TargetEncoder(cv=KFold(n_splits=5, shuffle=True, random_state=42), smooth="auto"), [location_col])
        ]
    )

    # Fit & Transform Train
    X_train_ohe = preprocessor_ohe.fit_transform(X_train, y_train)
    X_val_ohe = preprocessor_ohe.transform(X_val)

    X_train_te = preprocessor_target.fit_transform(X_train, y_train)
    X_val_te = preprocessor_target.transform(X_val)

    # Evaluate with Ridge Regressor
    model_ohe = Ridge(alpha=1.0)
    model_ohe.fit(X_train_ohe, y_train)
    preds_val_ohe = model_ohe.predict(X_val_ohe)
    r2_ohe = r2_score(y_val, preds_val_ohe)
    rmse_ohe = root_mean_squared_error(y_val, preds_val_ohe)

    model_te = Ridge(alpha=1.0)
    model_te.fit(X_train_te, y_train)
    preds_val_te = model_te.predict(X_val_te)
    r2_te = r2_score(y_val, preds_val_te)
    rmse_te = root_mean_squared_error(y_val, preds_val_te)

    comparison_results = {
        "one_hot_encoding": {
            "num_features": X_train_ohe.shape[1],
            "val_r2": float(r2_ohe),
            "val_rmse_log": float(rmse_ohe),
            "memory_kb": X_train_ohe.nbytes / 1024.0,
            "pros": "Preserves distinct coefficient for every known society; no assumption of target monotonicity.",
            "cons": "Sparse matrix (curse of dimensionality); completely fails on unseen locations in production."
        },
        "target_encoding": {
            "num_features": X_train_te.shape[1],
            "val_r2": float(r2_te),
            "val_rmse_log": float(rmse_te),
            "memory_kb": X_train_te.nbytes / 1024.0,
            "pros": "Compresses 32 societies into 1 dense numeric column; natural geographic price ordering; lower memory.",
            "cons": "Risk of target leakage if out-of-fold cross-fitting is not enforced."
        }
    }

    return comparison_results


# ========================================================
# 4. Property Valuation Pipeline Factory
# ========================================================
def build_property_pipeline(
    encoder_type: str = "target"
) -> Tuple[ColumnTransformer, List[str]]:
    """
    Creates a production-grade ColumnTransformer for property valuation.
    """
    numeric_features = [
        "plot_size_marla", "covered_area_sqft", "bedrooms", "bathrooms",
        "age_years", "floors", "is_corner", "is_park_facing", "is_main_boulevard",
        "amenities_count", "dist_to_main_road_km", "dist_to_school_km",
        "dist_to_hospital_km", "dist_to_commercial_km", "covered_area_ratio",
        "weighted_amenity_score", "composite_accessibility_index", "bed_bath_ratio",
        "total_rooms", "prime_orientation_score", "covered_area_per_bed"
    ]

    low_card_categoricals = ["city", "property_type", "property_age_bucket", "society_tier"]
    high_card_categorical = ["location"]

    transformers = [
        ("num", RobustScaler(), numeric_features),
        ("low_card_cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), low_card_categoricals)
    ]

    if encoder_type == "target":
        transformers.append(
            ("high_card_loc", TargetEncoder(cv=KFold(n_splits=5, shuffle=True, random_state=42), smooth="auto"), high_card_categorical)
        )
    else:
        transformers.append(
            ("high_card_loc", OneHotEncoder(handle_unknown="ignore", sparse_output=False), high_card_categorical)
        )

    preprocessor = ColumnTransformer(transformers=transformers)
    return preprocessor, numeric_features + low_card_categoricals + high_card_categorical


# ========================================================
# 5. Lead Scoring Pipeline Factory
# ========================================================
def build_leads_pipeline() -> Tuple[ColumnTransformer, List[str]]:
    """
    Creates a production-grade ColumnTransformer for lead scoring classification.
    Excludes lead_stage and all leaking features.
    """
    numeric_features = [
        "budget_pkr", "num_calls", "avg_call_duration_mins", "response_time_hours",
        "days_since_first_contact", "followup_count", "lead_engagement_score",
        "interaction_intensity", "objection_friction_score", "budget_to_market_ratio"
    ]

    categorical_features = [
        "lead_source", "preferred_city", "purpose", "property_type_preferred",
        "visit_booked", "visit_completed", "response_speed_category",
        "visit_funnel_status", "budget_realism_tier"
    ]

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", RobustScaler(), numeric_features),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical_features)
        ]
    )

    return preprocessor, numeric_features + categorical_features


if __name__ == "__main__":
    from data_cleaning import clean_property_data, clean_leads_data
    from feature_engineering import engineer_property_features, engineer_leads_features

    # 1. Load and process datasets
    print("Executing Task 5 Pipeline demonstration...")
    df_p = clean_property_data(pd.read_csv("Data/property_listings.csv"), verbose=False)
    df_l = clean_leads_data(pd.read_csv("Data/leads_scoring.csv"), verbose=False)

    df_p_feat = engineer_property_features(df_p)
    df_l_feat = engineer_leads_features(df_l, df_p)

    # 2. Compare OHE vs Target Encoding
    print("\n--- Comparing One-Hot vs Target Encoding for Locations ---")
    enc_comp = compare_ohe_vs_target_encoding(df_p_feat)
    print(f"One-Hot Encoding: {enc_comp['one_hot_encoding']['num_features']} features | Val R2: {enc_comp['one_hot_encoding']['val_r2']:.4f} | RMSE: {enc_comp['one_hot_encoding']['val_rmse_log']:.4f}")
    print(f"Target Encoding:  {enc_comp['target_encoding']['num_features']} features | Val R2: {enc_comp['target_encoding']['val_r2']:.4f} | RMSE: {enc_comp['target_encoding']['val_rmse_log']:.4f}")

    # 3. Stratified Split for Leads
    print("\n--- Stratified Splitting for Leads Dataset (70 / 15 / 15) ---")
    y_leads = df_l_feat["converted"]
    X_leads = df_l_feat.drop(columns=LEAKAGE_COLUMNS_LEADS + ["converted"])
    X_tr_l, X_va_l, X_te_l, y_tr_l, y_va_l, y_te_l = split_data_70_15_15(X_leads, y_leads, stratify=y_leads)

    print(f"Train Set: {X_tr_l.shape[0]} rows (Conversion rate: {y_tr_l.mean():.4f})")
    print(f"Val Set:   {X_va_l.shape[0]} rows (Conversion rate: {y_va_l.mean():.4f})")
    print(f"Test Set:  {X_te_l.shape[0]} rows (Conversion rate: {y_te_l.mean():.4f})")

    # 4. Fit Leads Pipeline
    pipeline_leads, lead_feature_cols = build_leads_pipeline()
    X_tr_l_proc = pipeline_leads.fit_transform(X_tr_l)
    X_va_l_proc = pipeline_leads.transform(X_va_l)
    print(f"Processed Leads Feature Matrix Shape: {X_tr_l_proc.shape}")
