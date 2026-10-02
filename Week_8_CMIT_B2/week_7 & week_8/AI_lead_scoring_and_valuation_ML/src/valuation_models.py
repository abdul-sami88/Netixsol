"""
src/valuation_models.py
=======================
Core modeling, evaluation, Optuna hyperparameter optimization, MLflow experiment tracking,
and quantile-based property valuation engine for Pakistan Real Estate.

Author: AI Engineering Team
Task: Day 2 - Property Valuation Model (Regression)
"""

import os
import time
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    plt.rcParams["font.sans-serif"] = "DejaVu Sans"
    plt.rcParams["font.size"] = 10
    plt.rcParams["axes.edgecolor"] = "#cccccc"
    plt.rcParams["axes.linewidth"] = 0.8
except Exception:
    plt = None
    sns = None

from sklearn.dummy import DummyRegressor
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score

try:
    from xgboost import XGBRegressor
except Exception:
    XGBRegressor = None

try:
    from lightgbm import LGBMRegressor
except Exception:
    LGBMRegressor = None

try:
    from catboost import CatBoostRegressor
except Exception:
    CatBoostRegressor = None

try:
    import optuna
except Exception:
    optuna = None

try:
    import mlflow
    from mlflow.models import infer_signature
    from mlflow.tracking import MlflowClient
except Exception:
    mlflow = None
    infer_signature = None
    MlflowClient = None


# ========================================================
# 1. Currency Formatting & Metrics Computation
# ========================================================
def format_crore_lakh(amount_pkr: float) -> str:
    """
    Formats a raw PKR numeric value into customary Pakistani real estate terminology:
    - >= 1 Crore (10,000,000 PKR): formatted as X.XX crore
    - >= 1 Lakh (100,000 PKR): formatted as X.XX lakh
    - < 1 Lakh: formatted as PKR X,XXX
    """
    if np.isnan(amount_pkr):
        return "N/A"
    abs_amt = abs(amount_pkr)
    sign = "-" if amount_pkr < 0 else ""
    if abs_amt >= 10_000_000:
        return f"{sign}{abs_amt / 1e7:.2f} crore"
    elif abs_amt >= 100_000:
        return f"{sign}{abs_amt / 1e5:.2f} lakh"
    else:
        return f"{sign}PKR {abs_amt:,.0f}"


def compute_regression_metrics(y_true_pkr: np.ndarray, y_pred_pkr: np.ndarray) -> Dict[str, float]:
    """
    Computes standard regression evaluation metrics in raw PKR currency:
    - MAE: Mean Absolute Error (PKR)
    - RMSE: Root Mean Squared Error (PKR)
    - R2: Coefficient of Determination
    - MAPE: Mean Absolute Percentage Error (%)
    """
    # Ensure non-negative predictions for property price
    y_pred_safe = np.maximum(y_pred_pkr, 1.0)
    mae = mean_absolute_error(y_true_pkr, y_pred_safe)
    rmse = root_mean_squared_error(y_true_pkr, y_pred_safe)
    r2 = r2_score(y_true_pkr, y_pred_safe)
    mape = np.mean(np.abs((y_true_pkr - y_pred_safe) / y_true_pkr)) * 100.0

    return {
        "MAE_PKR": float(mae),
        "RMSE_PKR": float(rmse),
        "R2": float(r2),
        "MAPE_pct": float(mape)
    }


# ========================================================
# 2. Task 1: Baseline Models
# ========================================================
def train_and_eval_baselines(
    X_train_proc: np.ndarray,
    y_train_log: np.ndarray,
    X_test_proc: np.ndarray,
    y_test_log: np.ndarray,
    y_train_pkr: np.ndarray,
    y_test_pkr: np.ndarray
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Trains and compares Baseline Models:
    1. Mean Dummy Baseline (predicts train mean in PKR)
    2. Median Dummy Baseline (predicts train median in PKR)
    3. Linear Regression (OLS fitted in log space)
    4. Ridge Regression (L2 regularization)
    5. Lasso Regression (L1 regularization)

    Returns:
    - results_df: Summary comparison DataFrame
    - fitted_models: Dictionary of trained model instances
    """
    models = {}
    records = []

    # 1. Mean Baseline
    t0 = time.time()
    dummy_mean = DummyRegressor(strategy="mean")
    dummy_mean.fit(X_train_proc, y_train_pkr)
    pred_mean_pkr = dummy_mean.predict(X_test_proc)
    t_mean = time.time() - t0
    m_mean = compute_regression_metrics(y_test_pkr, pred_mean_pkr)
    m_mean.update({"Model": "Mean Baseline", "Category": "Baseline", "Train_Time_s": t_mean})
    records.append(m_mean)
    models["Mean Baseline"] = dummy_mean

    # 2. Median Baseline
    t0 = time.time()
    dummy_med = DummyRegressor(strategy="median")
    dummy_med.fit(X_train_proc, y_train_pkr)
    pred_med_pkr = dummy_med.predict(X_test_proc)
    t_med = time.time() - t0
    m_med = compute_regression_metrics(y_test_pkr, pred_med_pkr)
    m_med.update({"Model": "Median Baseline", "Category": "Baseline", "Train_Time_s": t_med})
    records.append(m_med)
    models["Median Baseline"] = dummy_med

    # 3. Linear Regression (OLS)
    t0 = time.time()
    lr = LinearRegression()
    lr.fit(X_train_proc, y_train_log)
    pred_lr_pkr = np.expm1(lr.predict(X_test_proc))
    t_lr = time.time() - t0
    m_lr = compute_regression_metrics(y_test_pkr, pred_lr_pkr)
    m_lr.update({"Model": "Linear Regression", "Category": "Linear", "Train_Time_s": t_lr})
    records.append(m_lr)
    models["Linear Regression"] = lr

    # 4. Ridge Regression
    t0 = time.time()
    ridge = Ridge(alpha=1.0, random_state=42)
    ridge.fit(X_train_proc, y_train_log)
    pred_ridge_pkr = np.expm1(ridge.predict(X_test_proc))
    t_ridge = time.time() - t0
    m_ridge = compute_regression_metrics(y_test_pkr, pred_ridge_pkr)
    m_ridge.update({"Model": "Ridge Regression", "Category": "Linear Regularized", "Train_Time_s": t_ridge})
    records.append(m_ridge)
    models["Ridge Regression"] = ridge

    # 5. Lasso Regression
    t0 = time.time()
    lasso = Lasso(alpha=0.001, max_iter=5000, random_state=42)
    lasso.fit(X_train_proc, y_train_log)
    pred_lasso_pkr = np.expm1(lasso.predict(X_test_proc))
    t_lasso = time.time() - t0
    m_lasso = compute_regression_metrics(y_test_pkr, pred_lasso_pkr)
    m_lasso.update({"Model": "Lasso Regression", "Category": "Linear Regularized", "Train_Time_s": t_lasso})
    records.append(m_lasso)
    models["Lasso Regression"] = lasso

    results_df = pd.DataFrame(records)
    return results_df, models


# ========================================================
# 3. Task 2: Advanced Tree & Boosting Models
# ========================================================
def train_and_eval_advanced_models(
    X_train_proc: np.ndarray,
    y_train_log: np.ndarray,
    X_test_proc: np.ndarray,
    y_test_log: np.ndarray,
    y_test_pkr: np.ndarray
) -> Tuple[pd.DataFrame, Dict[str, Any], Dict[str, np.ndarray]]:
    """
    Trains and compares Advanced Models:
    1. Random Forest Regressor
    2. XGBoost Regressor
    3. LightGBM Regressor
    4. CatBoost Regressor

    Returns:
    - results_df: Summary comparison DataFrame
    - fitted_models: Dictionary of trained model instances
    - predictions_pkr: Dictionary of test predictions in raw PKR
    """
    models = {}
    predictions_pkr = {}
    records = []

    # 1. Random Forest
    t0 = time.time()
    rf = RandomForestRegressor(n_estimators=150, max_depth=16, random_state=42, n_jobs=-1)
    rf.fit(X_train_proc, y_train_log)
    pred_rf = np.expm1(rf.predict(X_test_proc))
    t_rf = time.time() - t0
    m_rf = compute_regression_metrics(y_test_pkr, pred_rf)
    m_rf.update({"Model": "Random Forest", "Category": "Ensemble (Bagging)", "Train_Time_s": t_rf})
    records.append(m_rf)
    models["Random Forest"] = rf
    predictions_pkr["Random Forest"] = pred_rf

    # 2. XGBoost
    t0 = time.time()
    xgb = XGBRegressor(
        n_estimators=200,
        learning_rate=0.07,
        max_depth=6,
        subsample=0.85,
        colsample_bytree=0.85,
        random_state=42,
        n_jobs=-1
    )
    xgb.fit(X_train_proc, y_train_log)
    pred_xgb = np.expm1(xgb.predict(X_test_proc))
    t_xgb = time.time() - t0
    m_xgb = compute_regression_metrics(y_test_pkr, pred_xgb)
    m_xgb.update({"Model": "XGBoost", "Category": "Ensemble (Boosting)", "Train_Time_s": t_xgb})
    records.append(m_xgb)
    models["XGBoost"] = xgb
    predictions_pkr["XGBoost"] = pred_xgb

    # 3. LightGBM
    t0 = time.time()
    lgb = LGBMRegressor(
        n_estimators=200,
        learning_rate=0.07,
        max_depth=6,
        num_leaves=31,
        subsample=0.85,
        colsample_bytree=0.85,
        random_state=42,
        n_jobs=-1,
        verbose=-1
    )
    lgb.fit(X_train_proc, y_train_log)
    pred_lgb = np.expm1(lgb.predict(X_test_proc))
    t_lgb = time.time() - t0
    m_lgb = compute_regression_metrics(y_test_pkr, pred_lgb)
    m_lgb.update({"Model": "LightGBM", "Category": "Ensemble (Boosting)", "Train_Time_s": t_lgb})
    records.append(m_lgb)
    models["LightGBM"] = lgb
    predictions_pkr["LightGBM"] = pred_lgb

    # 4. CatBoost
    t0 = time.time()
    cb = CatBoostRegressor(
        iterations=250,
        learning_rate=0.07,
        depth=6,
        random_seed=42,
        verbose=0
    )
    cb.fit(X_train_proc, y_train_log)
    pred_cb = np.expm1(cb.predict(X_test_proc))
    t_cb = time.time() - t0
    m_cb = compute_regression_metrics(y_test_pkr, pred_cb)
    m_cb.update({"Model": "CatBoost", "Category": "Ensemble (Boosting)", "Train_Time_s": t_cb})
    records.append(m_cb)
    models["CatBoost"] = cb
    predictions_pkr["CatBoost"] = pred_cb

    results_df = pd.DataFrame(records)
    return results_df, models, predictions_pkr


# ========================================================
# 4. Task 3: In-Depth Error Diagnostics & Slicing
# ========================================================
def evaluate_error_segments(
    df_test_raw: pd.DataFrame,
    y_test_pkr: np.ndarray,
    y_pred_pkr: np.ndarray
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Breaks down model errors by City and by Price Range to answer:
    'Where does the model fail and why?'

    Price Tiers:
    - Tier 1: Budget (< 1 Crore)
    - Tier 2: Mid-Market (1 - 3 Crore)
    - Tier 3: Upper-Mid (3 - 6 Crore)
    - Tier 4: Luxury (> 6 Crore)
    """
    df_eval = df_test_raw.copy()
    df_eval["actual_pkr"] = y_test_pkr
    df_eval["pred_pkr"] = y_pred_pkr
    df_eval["abs_error_pkr"] = np.abs(df_eval["actual_pkr"] - df_eval["pred_pkr"])
    df_eval["pct_error"] = (df_eval["abs_error_pkr"] / df_eval["actual_pkr"]) * 100.0

    # Categorize into Pakistani real estate price tiers
    def assign_price_tier(pkr: float) -> str:
        if pkr < 10_000_000:
            return "1. Budget (< 1 Cr)"
        elif pkr < 30_000_000:
            return "2. Mid-Market (1-3 Cr)"
        elif pkr < 60_000_000:
            return "3. Upper-Mid (3-6 Cr)"
        else:
            return "4. Luxury (> 6 Cr)"

    df_eval["price_tier"] = df_eval["actual_pkr"].apply(assign_price_tier)

    # 1. Error by City
    city_group = df_eval.groupby("city").agg(
        listings_count=("actual_pkr", "count"),
        mean_actual_pkr=("actual_pkr", "mean"),
        mae_pkr=("abs_error_pkr", "mean"),
        median_abs_error_pkr=("abs_error_pkr", "median"),
        mape_pct=("pct_error", "mean")
    ).reset_index()

    city_group["mae_formatted"] = city_group["mae_pkr"].apply(format_crore_lakh)
    city_group["mean_actual_formatted"] = city_group["mean_actual_pkr"].apply(format_crore_lakh)

    # Compute R2 per city
    city_r2 = {}
    for c in city_group["city"]:
        sub = df_eval[df_eval["city"] == c]
        if len(sub) > 1:
            city_r2[c] = r2_score(sub["actual_pkr"], sub["pred_pkr"])
        else:
            city_r2[c] = np.nan
    city_group["r2_score"] = city_group["city"].map(city_r2)

    # 2. Error by Price Tier
    tier_group = df_eval.groupby("price_tier").agg(
        listings_count=("actual_pkr", "count"),
        mean_actual_pkr=("actual_pkr", "mean"),
        mae_pkr=("abs_error_pkr", "mean"),
        median_abs_error_pkr=("abs_error_pkr", "median"),
        mape_pct=("pct_error", "mean")
    ).reset_index()

    tier_group["mae_formatted"] = tier_group["mae_pkr"].apply(format_crore_lakh)
    tier_group["mean_actual_formatted"] = tier_group["mean_actual_pkr"].apply(format_crore_lakh)

    tier_r2 = {}
    for t in tier_group["price_tier"]:
        sub = df_eval[df_eval["price_tier"] == t]
        if len(sub) > 1:
            tier_r2[t] = r2_score(sub["actual_pkr"], sub["pred_pkr"])
        else:
            tier_r2[t] = np.nan
    tier_group["r2_score"] = tier_group["price_tier"].map(tier_r2)

    return city_group, tier_group


# ========================================================
# 5. Visualizations
# ========================================================
def plot_model_comparison(df_comparison: pd.DataFrame, output_path: str):
    """Generates an aesthetic 3-panel comparison chart across all models."""
    fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharey=False)

    df_sorted = df_comparison.sort_values(by="MAE_PKR", ascending=False).reset_index(drop=True)
    palette = ["#e74c3c" if c == "Baseline" else "#3498db" if "Linear" in c else "#2ecc71" for c in df_sorted["Category"]]

    # Panel 1: MAE in PKR (Crores)
    sns.barplot(
        data=df_sorted,
        y="Model",
        x=df_sorted["MAE_PKR"] / 1e7,
        ax=axes[0],
        hue="Model",
        palette=palette,
        legend=False
    )
    axes[0].set_title("Test Mean Absolute Error (MAE in Crore PKR)", fontsize=13, fontweight="bold", pad=12)
    axes[0].set_xlabel("MAE (Crore PKR)", fontsize=11)
    axes[0].set_ylabel("")
    for i, v in enumerate(df_sorted["MAE_PKR"]):
        axes[0].text(v / 1e7 + 0.05, i, format_crore_lakh(v), va="center", fontsize=9, fontweight="bold")

    # Panel 2: R² Score
    sns.barplot(
        data=df_sorted,
        y="Model",
        x="R2",
        ax=axes[1],
        hue="Model",
        palette=palette,
        legend=False
    )
    axes[1].set_title("Coefficient of Determination ($R^2$ Score)", fontsize=13, fontweight="bold", pad=12)
    axes[1].set_xlabel("$R^2$ Score", fontsize=11)
    axes[1].set_ylabel("")
    axes[1].set_xlim(-0.1, 1.05)
    for i, v in enumerate(df_sorted["R2"]):
        axes[1].text(max(v, 0.0) + 0.02, i, f"{v:.4f}", va="center", fontsize=9, fontweight="bold")

    # Panel 3: MAPE (%)
    sns.barplot(
        data=df_sorted,
        y="Model",
        x="MAPE_pct",
        ax=axes[2],
        hue="Model",
        palette=palette,
        legend=False
    )
    axes[2].set_title("Mean Absolute Percentage Error (MAPE %)", fontsize=13, fontweight="bold", pad=12)
    axes[2].set_xlabel("MAPE (%)", fontsize=11)
    axes[2].set_ylabel("")
    for i, v in enumerate(df_sorted["MAPE_pct"]):
        axes[2].text(v + 1.0, i, f"{v:.1f}%", va="center", fontsize=9, fontweight="bold")

    plt.suptitle("Pakistani Real Estate: Property Valuation Model Benchmark", fontsize=16, fontweight="bold", y=1.02)
    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


def plot_actual_vs_predicted(
    y_test_pkr: np.ndarray,
    y_pred_pkr: np.ndarray,
    model_name: str,
    output_path: str
):
    """Generates Actual vs Predicted scatter and Residual Diagnostics."""
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    y_test_cr = y_test_pkr / 1e7
    y_pred_cr = y_pred_pkr / 1e7
    residuals_cr = y_test_cr - y_pred_cr

    # Panel 1: Actual vs Predicted with 45-degree line
    max_val = max(y_test_cr.max(), y_pred_cr.max()) * 1.05
    scatter = axes[0].scatter(
        y_test_cr,
        y_pred_cr,
        alpha=0.6,
        c=np.abs(residuals_cr),
        cmap="viridis",
        edgecolors="none",
        s=35
    )
    axes[0].plot([0, max_val], [0, max_val], "r--", linewidth=2, label="Ideal Line (y = x)")
    axes[0].set_title(f"Actual vs Predicted Property Price ({model_name})", fontsize=13, fontweight="bold", pad=12)
    axes[0].set_xlabel("Actual Price (Crore PKR)", fontsize=11)
    axes[0].set_ylabel("Predicted Price (Crore PKR)", fontsize=11)
    axes[0].set_xlim(0, max_val)
    axes[0].set_ylim(0, max_val)
    cbar = plt.colorbar(scatter, ax=axes[0])
    cbar.set_label("Absolute Error (Crore PKR)", fontsize=10)
    axes[0].legend(loc="upper left", frameon=True)

    # Panel 2: Residual Distribution
    sns.histplot(residuals_cr, bins=45, kde=True, ax=axes[1], color="#2980b9", edgecolor="#1c5980")
    axes[1].axvline(0, color="r", linestyle="--", linewidth=2, label="Zero Error")
    axes[1].axvline(np.mean(residuals_cr), color="orange", linestyle=":", linewidth=2, label=f"Mean Residual ({np.mean(residuals_cr):.2f} Cr)")
    axes[1].set_title("Residual Error Distribution (Actual - Predicted)", fontsize=13, fontweight="bold", pad=12)
    axes[1].set_xlabel("Residual Error (Crore PKR)", fontsize=11)
    axes[1].set_ylabel("Listing Count", fontsize=11)
    axes[1].legend(loc="upper right", frameon=True)

    plt.suptitle("Model Evaluation & Residual Diagnostics", fontsize=16, fontweight="bold", y=0.98)
    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


def plot_error_breakdown(
    city_errors: pd.DataFrame,
    tier_errors: pd.DataFrame,
    output_path: str
):
    """Visualizes error metrics across Cities and Price Tiers."""
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # City Breakdown
    sns.barplot(
        data=city_errors.sort_values(by="mape_pct", ascending=True),
        y="city",
        x="mape_pct",
        ax=axes[0],
        hue="city",
        palette="crest",
        legend=False
    )
    axes[0].set_title("Prediction Error by City (MAPE %)", fontsize=13, fontweight="bold", pad=12)
    axes[0].set_xlabel("MAPE (%)", fontsize=11)
    axes[0].set_ylabel("City", fontsize=11)
    for i, row in city_errors.sort_values(by="mape_pct", ascending=True).reset_index(drop=True).iterrows():
        axes[0].text(row["mape_pct"] + 0.3, i, f"{row['mape_pct']:.1f}% (MAE: {row['mae_formatted']})", va="center", fontsize=9)

    # Price Tier Breakdown
    sns.barplot(
        data=tier_errors,
        y="price_tier",
        x="mape_pct",
        ax=axes[1],
        hue="price_tier",
        palette="flare",
        legend=False
    )
    axes[1].set_title("Prediction Error by Property Price Tier (MAPE %)", fontsize=13, fontweight="bold", pad=12)
    axes[1].set_xlabel("MAPE (%)", fontsize=11)
    axes[1].set_ylabel("Price Tier", fontsize=11)
    for i, row in tier_errors.iterrows():
        axes[1].text(row["mape_pct"] + 0.3, i, f"{row['mape_pct']:.1f}% (MAE: {row['mae_formatted']})", va="center", fontsize=9)

    plt.suptitle("Where Does the Model Struggle? Sliced Error Analysis", fontsize=16, fontweight="bold", y=1.02)
    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


# ========================================================
# 6. Task 4: Optuna Hyperparameter Tuning & MLflow Tracking
# ========================================================
def tune_and_track_with_mlflow(
    X_train_proc: np.ndarray,
    y_train_log: np.ndarray,
    X_val_proc: np.ndarray,
    y_val_log: np.ndarray,
    X_test_proc: np.ndarray,
    y_test_log: np.ndarray,
    y_test_pkr: np.ndarray,
    feature_names: List[str],
    n_trials: int = 15,
    db_uri: str = "sqlite:///mlflow.db"
) -> Tuple[Dict[str, Any], Any, str]:
    """
    Uses Optuna to tune the two best models (CatBoost and LightGBM),
    logs all trials and metrics into MLflow, logs the champion model artifact,
    and registers it in the MLflow Model Registry.
    """
    os.environ["MLFLOW_DISABLE_AGENT_HINT"] = "1"
    mlflow.set_tracking_uri(db_uri)
    experiment_name = "Day2_Property_Valuation_Optimization"
    mlflow.set_experiment(experiment_name)

    optuna.logging.set_verbosity(optuna.logging.WARNING)

    y_val_pkr = np.expm1(y_val_log)

    print(f"\n[OPTUNA] Beginning Hyperparameter Search for LightGBM ({n_trials} trials)...")
    
    # 1. LightGBM Objective
    def lgb_objective(trial: optuna.Trial):
        params = {
            "n_estimators": trial.suggest_int("n_estimators", 150, 400),
            "learning_rate": trial.suggest_float("learning_rate", 0.02, 0.15, log=True),
            "max_depth": trial.suggest_int("max_depth", 4, 10),
            "num_leaves": trial.suggest_int("num_leaves", 20, 100),
            "subsample": trial.suggest_float("subsample", 0.6, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
            "reg_alpha": trial.suggest_float("reg_alpha", 1e-3, 10.0, log=True),
            "reg_lambda": trial.suggest_float("reg_lambda", 1e-3, 10.0, log=True),
            "random_state": 42,
            "n_jobs": -1,
            "verbose": -1
        }
        
        t0 = time.time()
        model = LGBMRegressor(**params)
        model.fit(X_train_proc, y_train_log)
        train_time = time.time() - t0
        
        preds_val_log = model.predict(X_val_proc)
        preds_val_pkr = np.expm1(preds_val_log)
        val_mae = mean_absolute_error(y_val_pkr, preds_val_pkr)
        
        # Log trial into MLflow child run
        with mlflow.start_run(run_name=f"Optuna_LGBM_Trial_{trial.number}", nested=True):
            mlflow.log_params(params)
            mlflow.log_metric("val_mae_pkr", val_mae)
            mlflow.log_metric("train_time_sec", train_time)
            
        return val_mae

    lgb_study = optuna.create_study(direction="minimize")
    lgb_study.optimize(lgb_objective, n_trials=n_trials)
    print(f" -> Best LightGBM Val MAE: PKR {lgb_study.best_value:,.0f} ({format_crore_lakh(lgb_study.best_value)})")

    # 2. CatBoost Objective
    print(f"\n[OPTUNA] Beginning Hyperparameter Search for CatBoost ({n_trials} trials)...")
    def cb_objective(trial: optuna.Trial):
        params = {
            "iterations": trial.suggest_int("iterations", 200, 450),
            "learning_rate": trial.suggest_float("learning_rate", 0.02, 0.12, log=True),
            "depth": trial.suggest_int("depth", 4, 8),
            "l2_leaf_reg": trial.suggest_float("l2_leaf_reg", 1.0, 10.0),
            "random_seed": 42,
            "verbose": 0
        }
        
        t0 = time.time()
        model = CatBoostRegressor(**params)
        model.fit(X_train_proc, y_train_log)
        train_time = time.time() - t0
        
        preds_val_log = model.predict(X_val_proc)
        preds_val_pkr = np.expm1(preds_val_log)
        val_mae = mean_absolute_error(y_val_pkr, preds_val_pkr)
        
        with mlflow.start_run(run_name=f"Optuna_CatBoost_Trial_{trial.number}", nested=True):
            mlflow.log_params(params)
            mlflow.log_metric("val_mae_pkr", val_mae)
            mlflow.log_metric("train_time_sec", train_time)
            
        return val_mae

    cb_study = optuna.create_study(direction="minimize")
    cb_study.optimize(cb_objective, n_trials=n_trials)
    print(f" -> Best CatBoost Val MAE: PKR {cb_study.best_value:,.0f} ({format_crore_lakh(cb_study.best_value)})")

    # 3. Determine Overall Champion Model & Log in Registry
    best_lgb_params = lgb_study.best_params
    best_lgb_params.update({"random_state": 42, "n_jobs": -1, "verbose": -1})
    best_cb_params = cb_study.best_params
    best_cb_params.update({"random_seed": 42, "verbose": 0})

    champion_name = "CatBoost" if cb_study.best_value < lgb_study.best_value else "LightGBM"
    champion_params = best_cb_params if champion_name == "CatBoost" else best_lgb_params
    print(f"\n>>> CHAMPION MODEL IDENTIFIED: {champion_name} (Val MAE: PKR {min(cb_study.best_value, lgb_study.best_value):,.0f})")

    # Train Champion Model on Train + Val combined
    X_train_val = np.vstack([X_train_proc, X_val_proc])
    y_train_val = np.concatenate([y_train_log, y_val_log])

    t0 = time.time()
    if champion_name == "CatBoost":
        champion_model = CatBoostRegressor(**champion_params)
    else:
        champion_model = LGBMRegressor(**champion_params)
        
    champion_model.fit(X_train_val, y_train_val)
    train_duration = time.time() - t0

    # Final Evaluation on Held-out Test Set
    test_preds_pkr = np.expm1(champion_model.predict(X_test_proc))
    test_metrics = compute_regression_metrics(y_test_pkr, test_preds_pkr)

    # MLflow Master Champion Run & Registry
    registry_model_name = "Pakistan_Property_Valuation_Model"
    with mlflow.start_run(run_name=f"Champion_{champion_name}_Production"):
        mlflow.log_params(champion_params)
        mlflow.log_metrics({
            "test_mae_pkr": test_metrics["MAE_PKR"],
            "test_rmse_pkr": test_metrics["RMSE_PKR"],
            "test_r2": test_metrics["R2"],
            "test_mape_pct": test_metrics["MAPE_pct"],
            "train_duration_sec": train_duration
        })
        mlflow.log_param("num_features", len(feature_names))
        mlflow.log_text("\n".join(feature_names), "feature_names.txt")
        
        signature = infer_signature(X_train_val[:5], champion_model.predict(X_train_val[:5]))
        
        if champion_name == "CatBoost":
            mlflow.catboost.log_model(
                champion_model,
                name="model",
                signature=signature,
                registered_model_name=registry_model_name
            )
        else:
            mlflow.lightgbm.log_model(
                champion_model,
                name="model",
                signature=signature,
                registered_model_name=registry_model_name
            )

    print(f"Registered Champion Model '{registry_model_name}' successfully into MLflow Model Registry.")
    return test_metrics, champion_model, champion_name


# ========================================================
# 7. Task 5: Price Range & Confidence Engine
# ========================================================
class PropertyValuationEngine:
    """
    Real Estate Valuation Engine providing:
    - Fair Market Price (P50 point prediction)
    - Lower & Upper Confidence Bounds (e.g., P10 and P90 quantile prediction intervals)
    - Automated Investment Verdict (Underpriced / Fair / Overpriced)
    - Client-ready bilingual Urdu/English explanation
    """
    def __init__(self, confidence_level: float = 0.80):
        self.confidence_level = confidence_level
        self.alpha_low = (1.0 - confidence_level) / 2.0  # e.g., 0.10 for 80%
        self.alpha_high = 1.0 - self.alpha_low          # e.g., 0.90 for 80%
        self.q_low_model = None
        self.q_mid_model = None
        self.q_high_model = None

    def fit(self, X_train: np.ndarray, y_train_log: np.ndarray):
        """Fits quantile regression models for lower, median, and upper bounds."""
        print(f"Fitting Quantile Valuation Engine (Coverage: {int(self.confidence_level*100)}% | P{int(self.alpha_low*100)} - P{int(self.alpha_high*100)})...")
        self.q_low_model = LGBMRegressor(
            objective="quantile",
            alpha=self.alpha_low,
            n_estimators=180,
            learning_rate=0.07,
            max_depth=6,
            random_state=42,
            verbose=-1,
            n_jobs=-1
        ).fit(X_train, y_train_log)

        self.q_mid_model = LGBMRegressor(
            n_estimators=200,
            learning_rate=0.07,
            max_depth=6,
            random_state=42,
            verbose=-1,
            n_jobs=-1
        ).fit(X_train, y_train_log)

        self.q_high_model = LGBMRegressor(
            objective="quantile",
            alpha=self.alpha_high,
            n_estimators=180,
            learning_rate=0.07,
            max_depth=6,
            random_state=42,
            verbose=-1,
            n_jobs=-1
        ).fit(X_train, y_train_log)

    def predict_range(self, X_features: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Returns (pred_mid_pkr, pred_low_pkr, pred_high_pkr)."""
        pred_low_pkr = np.expm1(self.q_low_model.predict(X_features))
        pred_mid_pkr = np.expm1(self.q_mid_model.predict(X_features))
        pred_high_pkr = np.expm1(self.q_high_model.predict(X_features))

        # Enforce monotonic interval consistency: low <= mid <= high
        pred_low_pkr = np.minimum(pred_low_pkr, pred_mid_pkr)
        pred_high_pkr = np.maximum(pred_high_pkr, pred_mid_pkr)

        return pred_mid_pkr, pred_low_pkr, pred_high_pkr

    def evaluate_listing(
        self,
        features_vec: np.ndarray,
        listed_price_pkr: float,
        property_desc: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluates a single property listing against market valuation intervals:
        Determines if property is Underpriced, Fair, or Overpriced.
        Generates formatted client report string.
        """
        f_vec = features_vec.reshape(1, -1) if len(features_vec.shape) == 1 else features_vec
        pred_mid, pred_low, pred_high = self.predict_range(f_vec)
        p_mid = float(pred_mid[0])
        p_low = float(pred_low[0])
        p_high = float(pred_high[0])

        # Verdict logic
        diff_pct = ((listed_price_pkr - p_mid) / p_mid) * 100.0

        if listed_price_pkr > p_high:
            verdict = "Overpriced"
            diff_bound_pct = ((listed_price_pkr - p_high) / p_high) * 100.0
            narrative = f"Overpriced by ~{abs(diff_pct):.1f}% above fair market value ({abs(diff_bound_pct):.1f}% above upper market boundary)."
        elif listed_price_pkr < p_low:
            verdict = "Underpriced"
            diff_bound_pct = ((p_low - listed_price_pkr) / p_low) * 100.0
            narrative = f"Underpriced by ~{abs(diff_pct):.1f}% below fair market value (Prime Investment Bargain, {abs(diff_bound_pct):.1f}% below market floor)."
        else:
            verdict = "Fair"
            narrative = f"Fairly Priced within market consensus interval (deviation: {diff_pct:+.1f}% from median)."

        client_output = (
            f"Predicted: {format_crore_lakh(p_mid)} (range {format_crore_lakh(p_low)} - {format_crore_lakh(p_high)}). "
            f"Listed at {format_crore_lakh(listed_price_pkr)} -> {verdict} by ~{abs(diff_pct):.1f}%."
        )

        return {
            "predicted_price_pkr": p_mid,
            "lower_range_pkr": p_low,
            "upper_range_pkr": p_high,
            "listed_price_pkr": listed_price_pkr,
            "verdict": verdict,
            "percentage_diff": diff_pct,
            "narrative": narrative,
            "client_output": client_output,
            "property_desc": property_desc
        }
