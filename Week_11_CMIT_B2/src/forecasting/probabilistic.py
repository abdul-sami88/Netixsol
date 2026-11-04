"""
Probabilistic Forecasting & Quantile Calibration Engine
Implements Task 4:
1. Multi-Quantile Regression using LightGBM (P10, P50, P90)
2. Empirical Calibration Verification (checking if P90 covers reality ~90% of the time)
3. Pinball / Quantile Loss & Winkler Interval Score
4. Fan Chart / Prediction Interval Ribbon Visualizations
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
    
FIG_DIR = os.path.join(BASE_DIR, "reports", "figures")
os.makedirs(FIG_DIR, exist_ok=True)

import lightgbm as lgb
from src.forecasting.analysis import load_daily_category_sales
from src.forecasting.models import create_lag_and_rolling_features


class QuantileForecastingEngine:
    """
    Fits separate LightGBM models for quantiles alpha in [0.10, 0.50, 0.90].
    Guarantees non-crossing quantiles via monotonic sort post-processing: P10 <= P50 <= P90.
    """
    def __init__(self, quantiles: List[float] = [0.10, 0.50, 0.90]):
        self.quantiles = quantiles
        self.models = {}
        self.feature_cols = []

    def fit(self, train_df: pd.DataFrame, feature_cols: List[str], target_col: str = "units_sold"):
        self.feature_cols = feature_cols
        clean = train_df.dropna(subset=self.feature_cols + [target_col])
        X = clean[self.feature_cols]
        y = clean[target_col]
        
        for q in self.quantiles:
            params = {
                "objective": "quantile",
                "alpha": q,
                "metric": "quantile",
                "boosting_type": "gbdt",
                "n_estimators": 150,
                "learning_rate": 0.05,
                "num_leaves": 31,
                "min_child_samples": 10,
                "subsample": 0.85,
                "colsample_bytree": 0.85,
                "random_state": 42,
                "verbosity": -1
            }
            model = lgb.LGBMRegressor(**params)
            model.fit(X, y)
            self.models[q] = model
        return self

    def predict_quantiles(self, test_df: pd.DataFrame) -> Dict[str, np.ndarray]:
        X = test_df[self.feature_cols].fillna(0)
        raw_preds = {}
        for q in self.quantiles:
            raw_preds[q] = np.maximum(0.0, self.models[q].predict(X))
            
        # Post-process to ensure non-crossing: P10 <= P50 <= P90
        p10 = raw_preds[0.10]
        p50 = raw_preds[0.50]
        p90 = raw_preds[0.90]
        
        # Enforce monotonicity
        p10_adj = np.minimum(p10, p50)
        p90_adj = np.maximum(p90, p50)
        
        return {
            "P10": p10_adj,
            "P50": p50,
            "P90": p90_adj
        }


def compute_pinball_loss(y_true: np.ndarray, y_pred: np.ndarray, alpha: float) -> float:
    """Pinball loss = max(alpha * (y - y_hat), (1 - alpha) * (y_hat - y))."""
    diff = y_true - y_pred
    loss = np.maximum(alpha * diff, (alpha - 1.0) * diff)
    return float(np.mean(loss))


def compute_winkler_score(y_true: np.ndarray, lower: np.ndarray, upper: np.ndarray, alpha: float = 0.20) -> float:
    """
    Winkler score for (1 - alpha) interval (e.g. 80% interval between P10 and P90):
    Rewards narrow intervals while penalizing points outside [lower, upper].
    """
    width = upper - lower
    penalty_below = np.where(y_true < lower, (2.0 / alpha) * (lower - y_true), 0.0)
    penalty_above = np.where(y_true > upper, (2.0 / alpha) * (y_true - upper), 0.0)
    score = width + penalty_below + penalty_above
    return float(np.mean(score))


def run_probabilistic_evaluation(cat_df: pd.DataFrame, horizon_days: int = 28):
    """
    Trains quantile regression models, verifies empirical calibration,
    and produces fan charts with P10/P50/P90 ribbons.
    """
    print("="*75)
    print("   TASK 4: PROBABILISTIC FORECASTS & QUANTILE CALIBRATION")
    print("="*75)
    
    dates = np.sort(cat_df["date"].unique())
    cutoff_date = dates[-horizon_days]
    
    feat_df = create_lag_and_rolling_features(cat_df, group_col="category", target_col="units_sold")
    feature_cols = [
        "day_of_week", "day_of_month", "month", "is_weekend_int", "day_of_year",
        "is_festival_int", "dow_sin", "dow_cos", "month_sin", "month_cos",
        "lag_1", "lag_2", "lag_7", "lag_14", "lag_21", "lag_28",
        "rolling_mean_7", "rolling_std_7", "rolling_max_7", "rolling_min_7",
        "rolling_mean_14", "rolling_std_14", "rolling_max_14", "rolling_min_14",
        "rolling_mean_28", "rolling_std_28", "category_cat"
    ]
    
    train_df = feat_df[feat_df["date"] < cutoff_date]
    test_df = feat_df[feat_df["date"] >= cutoff_date]
    
    print(f"Training Quantile LightGBM models on {len(train_df):,} records (up to {str(cutoff_date)[:10]})...")
    q_engine = QuantileForecastingEngine(quantiles=[0.10, 0.50, 0.90])
    q_engine.fit(train_df, feature_cols, target_col="units_sold")
    
    print(f"Generating probabilistic forecast intervals for {horizon_days}-day test horizon...")
    test_preds = q_engine.predict_quantiles(test_df)
    test_df = test_df.copy()
    test_df["P10"] = test_preds["P10"]
    test_df["P50"] = test_preds["P50"]
    test_df["P90"] = test_preds["P90"]
    
    # Calibration Check: Empirical Coverage Calculation
    y_test = test_df["units_sold"].values
    cov_p10 = np.mean(y_test <= test_df["P10"].values) * 100.0
    cov_p50 = np.mean(y_test <= test_df["P50"].values) * 100.0
    cov_p90 = np.mean(y_test <= test_df["P90"].values) * 100.0
    
    # Interval Coverage (P10 <= y <= P90)
    in_interval = np.mean((y_test >= test_df["P10"].values) & (y_test <= test_df["P90"].values)) * 100.0
    
    # Losses
    pb_10 = compute_pinball_loss(y_test, test_df["P10"].values, alpha=0.10)
    pb_50 = compute_pinball_loss(y_test, test_df["P50"].values, alpha=0.50)
    pb_90 = compute_pinball_loss(y_test, test_df["P90"].values, alpha=0.90)
    winkler = compute_winkler_score(y_test, test_df["P10"].values, test_df["P90"].values, alpha=0.20)
    
    print("\n" + "="*75)
    print("EMPIRICAL QUANTILE CALIBRATION & ACCURACY BENCHMARK:")
    print("="*75)
    cal_table = pd.DataFrame([
        {"Quantile": "P10 (Pessimistic)", "Theoretical (%)": 10.0, "Empirical Coverage (%)": round(cov_p10, 2), "Pinball Loss": round(pb_10, 3)},
        {"Quantile": "P50 (Median)", "Theoretical (%)": 50.0, "Empirical Coverage (%)": round(cov_p50, 2), "Pinball Loss": round(pb_50, 3)},
        {"Quantile": "P90 (Optimistic / Buffer)", "Theoretical (%)": 90.0, "Empirical Coverage (%)": round(cov_p90, 2), "Pinball Loss": round(pb_90, 3)},
    ])
    print(cal_table.to_string(index=False))
    print(f"\n80% Prediction Interval [P10, P90] Real-World Coverage: {in_interval:.1f}% (Nominal Target: 80.0%)")
    print(f"Average Interval Width: {np.mean(test_df['P90'] - test_df['P10']):.2f} units")
    print(f"Overall Winkler Score: {winkler:.2f}")
    
    # Plot Fan Chart / Ribbon for Fashion & Electronics
    fig, axes = plt.subplots(2, 1, figsize=(15, 9), sharex=True)
    
    for idx, cat in enumerate(["Fashion", "Electronics"]):
        ax = axes[idx]
        cat_sub = test_df[test_df["category"] == cat].sort_values("date")
        
        # Historical context (last 30 days of train)
        hist = train_df[(train_df["category"] == cat) & (train_df["date"] >= cutoff_date - pd.Timedelta(days=30))].sort_values("date")
        
        ax.plot(hist["date"], hist["units_sold"], label="Historical Actuals", color="#333333", lw=1.5, marker="o", markersize=3)
        ax.plot(cat_sub["date"], cat_sub["units_sold"], label="Ground Truth Demand", color="#000000", lw=2, marker="s", markersize=4)
        ax.plot(cat_sub["date"], cat_sub["P50"], label="P50 Median Forecast", color="#1f77b4", lw=2, linestyle="--")
        
        # Shaded [P10, P90] interval ribbon
        ax.fill_between(cat_sub["date"], cat_sub["P10"], cat_sub["P90"], color="#1f77b4", alpha=0.25, 
                        label="80% Prediction Interval [P10, P90]")
        
        # Mark festival days
        fest_days = cat_sub[cat_sub["is_festival"]]
        if not fest_days.empty:
            ax.scatter(fest_days["date"], fest_days["units_sold"], color="#d62728", s=60, zorder=5, label="Festival Day")
            
        ax.axvline(cutoff_date, color="gray", linestyle=":", lw=1.5)
        ax.text(cutoff_date + pd.Timedelta(days=1), ax.get_ylim()[1]*0.9, "Forecast Horizon -->", fontsize=10, color="gray", fontweight="bold")
        
        ax.set_title(f"Probabilistic Demand Forecast: {cat} Category (P10, P50, P90 Prediction Ribbon)", fontsize=12, fontweight="bold")
        ax.set_ylabel("Daily Units Sold", fontsize=10, fontweight="bold")
        ax.legend(frameon=True, facecolor="white", loc="upper left")
        ax.grid(True, alpha=0.3)
        
    axes[1].set_xlabel("Date", fontsize=11, fontweight="bold")
    plt.tight_layout()
    prob_fig_path = os.path.join(FIG_DIR, "probabilistic_forecast_intervals.png")
    fig.savefig(prob_fig_path, dpi=200)
    plt.close(fig)
    
    print("\n[SUCCESS] Task 4 complete. Saved fan chart to 'reports/figures/probabilistic_forecast_intervals.png'.")
    return test_df, cal_table, in_interval


if __name__ == "__main__":
    from src.forecasting.analysis import load_daily_category_sales
    import duckdb
    con = duckdb.connect(os.path.join(BASE_DIR, "data", "processed", "shopkaro.duckdb"), read_only=True)
    cat_df = load_daily_category_sales(con)
    con.close()
    run_probabilistic_evaluation(cat_df, horizon_days=28)

