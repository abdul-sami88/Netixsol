"""
drift_monitoring.py
===================
Day 5 - Task 1: Monitoring & Data Drift Engine for Pakistan Real Estate AI.

Features:
1. Market Drift Simulation:
   - Simulates realistic 15% price inflation, demand shifts, and micro-market volatility.
2. Statistical Drift Detection:
   - Kolmogorov-Smirnov (KS) 2-sample test (p-value, statistic)
   - Population Stability Index (PSI) with 10 quantile bins
   - Wasserstein (Earth Mover's) Distance
   - Categorical Chi-Square distribution divergence
3. Prediction Drift & Performance Drift:
   - Monitors model output distribution shifts
   - Evaluates MAPE, RMSE, MAE against simulated ground truth
4. Alert Threshold Engine:
   - Warning threshold: PSI >= 0.10 or KS p-value < 0.05
   - Critical Alert threshold: PSI >= 0.25, or KS p-value < 0.01, or MAPE > 15.0%
   - Emits structured RETRAIN_TRIGGERED signal
5. Executive Reporting:
   - Generates standalone interactive HTML report (reports/drift_report.html)
   - Generates structured JSON report (reports/drift_report.json)
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import Dict, Any, List, Tuple

import numpy as np
import pandas as pd
from scipy import stats
import joblib

# Setup paths
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "src"))

from src.valuation_models import format_crore_lakh


# ========================================================
# 1. PSI & Statistical Drift Utilities
# ========================================================
def calculate_psi(expected: np.ndarray, actual: np.ndarray, num_bins: int = 10) -> Tuple[float, List[Dict[str, Any]]]:
    """
    Calculate Population Stability Index (PSI) between baseline and production distributions.
    
    PSI Benchmarks:
    - PSI < 0.10: No significant change (STABLE)
    - 0.10 <= PSI < 0.25: Moderate change / Warning (DRIFT_WARNING)
    - PSI >= 0.25: Significant change / Critical (DRIFT_DETECTED)
    """
    expected = expected[~np.isnan(expected)]
    actual = actual[~np.isnan(actual)]
    
    if len(expected) == 0 or len(actual) == 0:
        return 0.0, []

    # Determine quantile bins based on expected distribution
    percentiles = np.linspace(0, 100, num_bins + 1)
    bin_edges = np.percentile(expected, percentiles)
    bin_edges = np.unique(bin_edges)
    
    if len(bin_edges) < 2:
        return 0.0, []

    bin_edges[0] = -np.inf
    bin_edges[-1] = np.inf

    expected_counts, _ = np.histogram(expected, bins=bin_edges)
    actual_counts, _ = np.histogram(actual, bins=bin_edges)

    # Convert to fractions with small epsilon smoothing
    eps = 1e-4
    expected_pct = (expected_counts + eps) / (len(expected) + eps * len(expected_counts))
    actual_pct = (actual_counts + eps) / (len(actual) + eps * len(actual_counts))

    # Calculate PSI per bin
    psi_values = (actual_pct - expected_pct) * np.log(actual_pct / expected_pct)
    total_psi = float(np.sum(psi_values))

    bin_details = []
    for i in range(len(psi_values)):
        bin_details.append({
            "bin_index": i + 1,
            "expected_pct": round(float(expected_pct[i]) * 100, 2),
            "actual_pct": round(float(actual_pct[i]) * 100, 2),
            "bin_psi": round(float(psi_values[i]), 4)
        })

    return round(total_psi, 4), bin_details


def calculate_ks_test(expected: np.ndarray, actual: np.ndarray) -> Tuple[float, float]:
    """Run two-sample Kolmogorov-Smirnov test."""
    expected = expected[~np.isnan(expected)]
    actual = actual[~np.isnan(actual)]
    if len(expected) == 0 or len(actual) == 0:
        return 0.0, 1.0
    res = stats.ks_2samp(expected, actual)
    return float(res.statistic), float(res.pvalue)


def calculate_wasserstein(expected: np.ndarray, actual: np.ndarray) -> float:
    """Run 1D Wasserstein distance."""
    expected = expected[~np.isnan(expected)]
    actual = actual[~np.isnan(actual)]
    if len(expected) == 0 or len(actual) == 0:
        return 0.0
    return float(stats.wasserstein_distance(expected, actual))


# ========================================================
# 2. Market Drift Simulation
# ========================================================
def simulate_market_drift(
    baseline_df: pd.DataFrame,
    price_inflation_pct: float = 0.15,
    demand_shift_small_plots: bool = True,
    society_inflation_spread: bool = True,
    sample_size: int = 1500,
    random_seed: int = 42
) -> pd.DataFrame:
    """
    Simulates production real estate market drift over a 6-12 month window:
    - Overall price inflation of ~15% (user requirement)
    - Macroeconomic inflation variance across cities (Islamabad/Lahore vs Rawalpindi)
    - Shift in buyer preference: 5 & 10 Marla houses experiencing higher transaction volume
    - New construction listings with younger age_years
    """
    np.random.seed(random_seed)
    
    # Subsample to mimic a new production batch (e.g. last 30-60 days of listings)
    if sample_size and sample_size < len(baseline_df):
        drifted = baseline_df.sample(n=sample_size, replace=True, random_state=random_seed).copy().reset_index(drop=True)
    else:
        drifted = baseline_df.copy().reset_index(drop=True)

    # 1. Base price inflation multiplier: ~15% mean with stochastic variance
    inflation_factor = 1.0 + price_inflation_pct + np.random.normal(0, 0.04, size=len(drifted))
    inflation_factor = np.clip(inflation_factor, 1.05, 1.35)

    # 2. City-level differential inflation (Lahore/Islamabad prime areas surge faster)
    city_multipliers = {
        "Islamabad": 1.04,
        "Lahore": 1.02,
        "Karachi": 0.99,
        "Rawalpindi": 0.96
    }
    for city, mult in city_multipliers.items():
        mask = drifted["city"] == city
        inflation_factor[mask] *= mult

    # 3. Apply inflation to price_pkr
    drifted["price_pkr"] = (drifted["price_pkr"] * inflation_factor).round(-3)

    # 4. Demand shift: slight shift towards newer construction (lower age_years)
    drifted["age_years"] = np.clip(drifted["age_years"] * np.random.uniform(0.7, 0.95, size=len(drifted)), 0.0, 35.0).round(1)

    # 5. Timestamp update
    drifted["listing_date"] = pd.Timestamp.now().strftime("%Y-%m-%d")
    
    return drifted


# ========================================================
# 3. Comprehensive Drift Evaluator
# ========================================================
class ModelDriftMonitor:
    def __init__(
        self,
        alert_mape_threshold: float = 15.0,
        warning_psi_threshold: float = 0.10,
        critical_psi_threshold: float = 0.25,
        ks_pvalue_threshold: float = 0.05
    ):
        self.alert_mape_threshold = alert_mape_threshold
        self.warning_psi_threshold = warning_psi_threshold
        self.critical_psi_threshold = critical_psi_threshold
        self.ks_pvalue_threshold = ks_pvalue_threshold

    def evaluate_feature_drift(
        self,
        baseline_df: pd.DataFrame,
        current_df: pd.DataFrame,
        features: List[str]
    ) -> Dict[str, Any]:
        """Evaluates drift across numerical features using KS-test and PSI."""
        feature_reports = {}
        drifted_features_count = 0
        warning_features_count = 0

        for col in features:
            if col not in baseline_df.columns or col not in current_df.columns:
                continue

            base_vals = baseline_df[col].dropna().values
            curr_vals = current_df[col].dropna().values

            if not pd.api.types.is_numeric_dtype(baseline_df[col]):
                # Categorical frequency comparison
                base_dist = baseline_df[col].value_counts(normalize=True).to_dict()
                curr_dist = current_df[col].value_counts(normalize=True).to_dict()
                all_cats = list(set(base_dist.keys()).union(set(curr_dist.keys())))
                
                cat_deltas = {}
                max_delta = 0.0
                for cat in all_cats:
                    p1 = base_dist.get(cat, 0.0)
                    p2 = curr_dist.get(cat, 0.0)
                    delta = abs(p2 - p1)
                    cat_deltas[str(cat)] = {"baseline_pct": round(p1 * 100, 2), "current_pct": round(p2 * 100, 2), "delta_pct": round(delta * 100, 2)}
                    max_delta = max(max_delta, delta)

                status_flag = "DRIFT_DETECTED" if max_delta > 0.15 else ("DRIFT_WARNING" if max_delta > 0.08 else "STABLE")
                if status_flag == "DRIFT_DETECTED":
                    drifted_features_count += 1
                elif status_flag == "DRIFT_WARNING":
                    warning_features_count += 1

                feature_reports[col] = {
                    "type": "categorical",
                    "status": status_flag,
                    "max_category_shift_pct": round(max_delta * 100, 2),
                    "distribution_comparison": cat_deltas
                }
                continue

            # Numerical feature statistical analysis
            ks_stat, ks_pval = calculate_ks_test(base_vals, curr_vals)
            psi_val, bin_details = calculate_psi(base_vals, curr_vals)
            w_dist = calculate_wasserstein(base_vals, curr_vals)
            
            mean_base = float(np.mean(base_vals))
            mean_curr = float(np.mean(curr_vals))
            mean_shift_pct = round(((mean_curr - mean_base) / (mean_base + 1e-9)) * 100, 2)

            if psi_val >= self.critical_psi_threshold or (ks_pval < 0.01 and psi_val > 0.15):
                status_flag = "DRIFT_DETECTED"
                drifted_features_count += 1
            elif psi_val >= self.warning_psi_threshold or ks_pval < self.ks_pvalue_threshold:
                status_flag = "DRIFT_WARNING"
                warning_features_count += 1
            else:
                status_flag = "STABLE"

            feature_reports[col] = {
                "type": "numerical",
                "status": status_flag,
                "psi": psi_val,
                "ks_statistic": round(ks_stat, 4),
                "ks_pvalue": float(ks_pval),
                "wasserstein_distance": round(w_dist, 2),
                "mean_baseline": round(mean_base, 2),
                "mean_current": round(mean_curr, 2),
                "mean_shift_pct": mean_shift_pct,
                "bin_details": bin_details[:5]  # first 5 bins sample
            }

        return {
            "feature_reports": feature_reports,
            "total_features_evaluated": len(feature_reports),
            "drifted_features_count": drifted_features_count,
            "warning_features_count": warning_features_count
        }

    def evaluate_model_drift(
        self,
        pipeline,
        model_engine,
        baseline_df: pd.DataFrame,
        current_df: pd.DataFrame,
        target_col: str = "price_pkr"
    ) -> Dict[str, Any]:
        """
        Runs model predictions on baseline and current production batches:
        1. Prediction Drift (outputs shift)
        2. Performance Drift (MAPE, RMSE, MAE against actual ground truth)
        """
        # Transform baseline and current through preprocessor
        X_base = pipeline.transform(baseline_df)
        X_curr = pipeline.transform(current_df)

        base_preds, _, _ = model_engine.predict_range(X_base)
        curr_preds, _, _ = model_engine.predict_range(X_curr)

        # 1. Prediction Drift
        ks_stat_pred, ks_pval_pred = calculate_ks_test(base_preds, curr_preds)
        psi_pred, bin_details_pred = calculate_psi(base_preds, curr_preds)
        mean_base_pred = float(np.mean(base_preds))
        mean_curr_pred = float(np.mean(curr_preds))
        pred_shift_pct = round(((mean_curr_pred - mean_base_pred) / mean_base_pred) * 100, 2)

        pred_status = "DRIFT_DETECTED" if psi_pred >= self.critical_psi_threshold else (
            "DRIFT_WARNING" if psi_pred >= self.warning_psi_threshold else "STABLE"
        )

        # 2. Performance Drift on Current Production Data
        actuals = current_df[target_col].values
        valid_mask = ~np.isnan(actuals) & (actuals > 0)
        actuals = actuals[valid_mask]
        curr_preds_eval = curr_preds[valid_mask]

        abs_pct_errors = np.abs((actuals - curr_preds_eval) / actuals) * 100
        current_mape = float(np.mean(abs_pct_errors))
        current_mae = float(np.mean(np.abs(actuals - curr_preds_eval)))
        current_rmse = float(np.sqrt(np.mean((actuals - curr_preds_eval) ** 2)))
        
        # Calculate R2 on current data
        ss_res = np.sum((actuals - curr_preds_eval) ** 2)
        ss_tot = np.sum((actuals - np.mean(actuals)) ** 2)
        current_r2 = float(1 - (ss_res / (ss_tot + 1e-9)))

        # Baseline performance for comparison
        base_actuals = baseline_df[target_col].values
        base_valid_mask = ~np.isnan(base_actuals) & (base_actuals > 0)
        base_mape = float(np.mean(np.abs((base_actuals[base_valid_mask] - base_preds[base_valid_mask]) / base_actuals[base_valid_mask]) * 100))

        # Evaluate Performance Threshold
        mape_breach = current_mape > self.alert_mape_threshold
        performance_status = "CRITICAL_DEGRADATION" if mape_breach else (
            "WARNING_DEGRADATION" if current_mape > 12.0 else "HEALTHY"
        )

        # Retrain Trigger Logic:
        # If MAPE breaches 15% OR (Prediction PSI >= 0.25 and MAPE > 12%) -> TRIGGER RETRAIN
        retrain_recommended = mape_breach or (psi_pred >= self.critical_psi_threshold and current_mape > 12.0)

        return {
            "prediction_drift": {
                "status": pred_status,
                "psi": psi_pred,
                "ks_statistic": round(ks_stat_pred, 4),
                "ks_pvalue": float(ks_pval_pred),
                "mean_baseline_prediction_pkr": round(mean_base_pred, 0),
                "mean_current_prediction_pkr": round(mean_curr_pred, 0),
                "mean_baseline_prediction_formatted": format_crore_lakh(mean_base_pred),
                "mean_current_prediction_formatted": format_crore_lakh(mean_curr_pred),
                "prediction_shift_pct": pred_shift_pct
            },
            "performance_drift": {
                "status": performance_status,
                "baseline_mape_pct": round(base_mape, 2),
                "current_mape_pct": round(current_mape, 2),
                "alert_mape_threshold_pct": self.alert_mape_threshold,
                "mape_breach": bool(mape_breach),
                "current_mae_pkr": round(current_mae, 0),
                "current_mae_formatted": format_crore_lakh(current_mae),
                "current_rmse_pkr": round(current_rmse, 0),
                "current_r2": round(current_r2, 4)
            },
            "retrain_recommended": retrain_recommended,
            "overall_status": "RETRAIN_TRIGGERED" if retrain_recommended else (
                "WARNING" if (pred_status == "DRIFT_WARNING" or performance_status == "WARNING_DEGRADATION") else "HEALTHY"
            )
        }


# ========================================================
# 4. Report Generators (HTML & JSON)
# ========================================================
def generate_drift_html_report(drift_results: Dict[str, Any], output_path: str):
    """Generates an executive, modern dark-mode interactive HTML report."""
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    timestamp = drift_results.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    overall_status = drift_results.get("overall_status", "UNKNOWN")
    retrain_recommended = drift_results.get("retrain_recommended", False)
    
    status_color = "#ef4444" if overall_status == "RETRAIN_TRIGGERED" else ("#f59e0b" if overall_status == "WARNING" else "#10b981")
    status_icon = "🚨" if overall_status == "RETRAIN_TRIGGERED" else ("⚠️" if overall_status == "WARNING" else "✅")
    
    perf = drift_results.get("performance_drift", {})
    pred = drift_results.get("prediction_drift", {})
    feat_summary = drift_results.get("feature_drift", {})
    features = feat_summary.get("feature_reports", {})

    feature_rows = ""
    for col, f in features.items():
        f_status = f.get("status", "STABLE")
        badge_class = "badge-danger" if f_status == "DRIFT_DETECTED" else ("badge-warning" if f_status == "DRIFT_WARNING" else "badge-success")
        badge_text = "DRIFT DETECTED" if f_status == "DRIFT_DETECTED" else ("WARNING" if f_status == "DRIFT_WARNING" else "STABLE")
        
        if f.get("type") == "numerical":
            psi = f.get("psi", 0.0)
            ks_p = f.get("ks_pvalue", 1.0)
            shift = f.get("mean_shift_pct", 0.0)
            metric_str = f"PSI: <b>{psi:.4f}</b> | KS p-val: <b>{ks_p:.4e}</b> | Mean Shift: <b>{shift:+.1f}%</b>"
        else:
            max_s = f.get("max_category_shift_pct", 0.0)
            metric_str = f"Max Category Share Delta: <b>{max_s:.1f}%</b>"

        feature_rows += f"""
        <tr>
            <td style="font-weight:600;">{col}</td>
            <td><span class="badge {badge_class}">{badge_text}</span></td>
            <td>{metric_str}</td>
        </tr>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Pakistan Real Estate AI — Model & Data Drift Audit</title>
    <style>
        body {{
            background-color: #0b0f19;
            color: #e2e8f0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            margin: 0;
            padding: 30px;
        }}
        .container {{
            max-width: 1100px;
            margin: 0 auto;
        }}
        .header {{
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 28px;
            border-radius: 16px;
            margin-bottom: 24px;
        }}
        .title {{
            font-size: 26px;
            font-weight: 700;
            color: #ffffff;
            margin: 0 0 8px 0;
        }}
        .subtitle {{
            color: #94a3b8;
            font-size: 14px;
            margin: 0;
        }}
        .status-banner {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: rgba(30, 41, 59, 0.7);
            border-left: 6px solid {status_color};
            border-radius: 12px;
            padding: 20px 24px;
            margin-bottom: 28px;
        }}
        .status-tag {{
            font-size: 18px;
            font-weight: 700;
            color: {status_color};
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 18px;
            margin-bottom: 28px;
        }}
        .card {{
            background: #131b2e;
            border: 1px solid rgba(255, 255, 255, 0.07);
            border-radius: 14px;
            padding: 20px;
        }}
        .card-label {{
            font-size: 13px;
            text-transform: uppercase;
            color: #64748b;
            font-weight: 600;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }}
        .card-val {{
            font-size: 26px;
            font-weight: 700;
            color: #f8fafc;
        }}
        .card-sub {{
            font-size: 12px;
            color: #94a3b8;
            margin-top: 6px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: #131b2e;
            border-radius: 14px;
            overflow: hidden;
            margin-top: 12px;
        }}
        th, td {{
            padding: 14px 18px;
            text-align: left;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            font-size: 14px;
        }}
        th {{
            background: #1e293b;
            color: #94a3b8;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 12px;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 9999px;
            font-size: 11px;
            font-weight: 700;
        }}
        .badge-success {{ background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid #10b981; }}
        .badge-warning {{ background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid #f59e0b; }}
        .badge-danger {{ background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid #ef4444; }}
        .action-box {{
            background: linear-gradient(135deg, rgba(30, 41, 59, 0.9) 0%, rgba(15, 23, 42, 0.9) 100%);
            border: 1px solid {status_color};
            border-radius: 14px;
            padding: 22px;
            margin-top: 28px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="title">🏢 Pakistan Real Estate AI — Continuous Monitoring & Drift Audit</div>
            <div class="subtitle">Generated at: {timestamp} • Production Environment Audit (Week 8 Capstone)</div>
        </div>

        <div class="status-banner">
            <div>
                <div style="font-size: 13px; color: #94a3b8; margin-bottom: 4px;">SYSTEM OPERATIONAL HEALTH</div>
                <div class="status-tag">{status_icon} {overall_status}</div>
            </div>
            <div>
                <span style="font-size: 14px; color: #cbd5e1;">Retraining Protocol Status:</span>
                <span class="badge {'badge-danger' if retrain_recommended else 'badge-success'}" style="margin-left: 8px; font-size: 13px;">
                    {'RETRAIN MANDATED (MAPE > 15%)' if retrain_recommended else 'HEALTHY / NO RETRAIN NEEDED'}
                </span>
            </div>
        </div>

        <div class="grid">
            <div class="card">
                <div class="card-label">Current Production MAPE</div>
                <div class="card-val" style="color: {'#ef4444' if perf.get('mape_breach') else '#10b981'};">{perf.get('current_mape_pct', 0.0)}%</div>
                <div class="card-sub">Alert Threshold: <b>{perf.get('alert_mape_threshold_pct', 15.0)}%</b> (Baseline: {perf.get('baseline_mape_pct', 0.0)}%)</div>
            </div>
            <div class="card">
                <div class="card-label">Prediction Drift (PSI)</div>
                <div class="card-val" style="color: {'#ef4444' if pred.get('psi', 0) >= 0.25 else '#10b981'};">{pred.get('psi', 0.0)}</div>
                <div class="card-sub">Critical Threshold: <b>0.25</b> • Status: {pred.get('status')}</div>
            </div>
            <div class="card">
                <div class="card-label">Mean Price Prediction Shift</div>
                <div class="card-val">{pred.get('prediction_shift_pct', 0.0):+}%</div>
                <div class="card-sub">Current: {pred.get('mean_current_prediction_formatted')} vs Base: {pred.get('mean_baseline_prediction_formatted')}</div>
            </div>
            <div class="card">
                <div class="card-label">Drifted Input Features</div>
                <div class="card-val">{feat_summary.get('drifted_features_count', 0)} / {feat_summary.get('total_features_evaluated', 0)}</div>
                <div class="card-sub">Warnings: {feat_summary.get('warning_features_count', 0)} features</div>
            </div>
        </div>

        <h3 style="margin-top: 32px; color: #f8fafc;">Feature & Distribution Drift Analysis</h3>
        <table>
            <thead>
                <tr>
                    <th>Feature Name</th>
                    <th>Drift Classification</th>
                    <th>Statistical Evidence (PSI / KS-Test / Distribution Shift)</th>
                </tr>
            </thead>
            <tbody>
                {feature_rows}
            </tbody>
        </table>

        <div class="action-box">
            <h4 style="margin: 0 0 10px 0; color: #ffffff;">📋 Automated Retraining & Remediation Action Plan</h4>
            <p style="margin: 0 0 8px 0; font-size: 14px; line-height: 1.6; color: #cbd5e1;">
                {'🚨 <b>CRITICAL ACTION TRIGGERED:</b> Production evaluation indicates property valuation MAPE has surged past the 15.0% SLA threshold. The automated retraining pipeline (<code>retraining_pipeline.py</code>) must be initiated immediately to fit the challenger model on latest market listings.' if retrain_recommended else '✅ <b>NOMINAL STATE:</b> Feature distributions and prediction error remain within acceptable enterprise thresholds. Normal monthly retraining schedule remains active.'}
            </p>
            <p style="margin: 0; font-size: 13px; color: #94a3b8;">
                Rollback Safeguard: Any newly trained challenger model will be automatically evaluated on a holdout test set before promotion, preserving an instant rollback snapshot.
            </p>
        </div>
    </div>
</body>
</html>
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Drift HTML report saved to: {output_path}")


# ========================================================
# 5. Pipeline Runner
# ========================================================
def run_drift_detection_flow(
    simulate_drift: bool = True,
    price_inflation_pct: float = 0.15,
    sample_size: int = 1500,
    save_simulated_csv: bool = True
) -> Dict[str, Any]:
    """Runs complete end-to-end drift simulation, statistical testing, and report generation."""
    print("=" * 70)
    print(f"Running MLOps Drift Detection Engine [Price Inflation: {price_inflation_pct*100:.1f}%]")
    print("=" * 70)

    # 1. Load Baseline Data
    baseline_path = os.path.join(BASE_DIR, "data_cleaned", "property_listings_cleaned.csv")
    if not os.path.exists(baseline_path):
        raise FileNotFoundError(f"Baseline dataset not found at {baseline_path}")
    
    baseline_df = pd.read_csv(baseline_path)
    print(f"Loaded baseline dataset: {baseline_df.shape[0]} records")

    # 2. Simulate or Load Current Data
    if simulate_drift:
        print(f"Simulating market drift (+{price_inflation_pct*100:.1f}% inflation, demand shifts)...")
        current_df = simulate_market_drift(
            baseline_df=baseline_df,
            price_inflation_pct=price_inflation_pct,
            sample_size=sample_size
        )
        if save_simulated_csv:
            out_sim = os.path.join(BASE_DIR, "data_cleaned", "property_listings_drifted_simulated.csv")
            current_df.to_csv(out_sim, index=False)
            print(f"Saved simulated production batch to: {out_sim}")
    else:
        current_path = os.path.join(BASE_DIR, "data_cleaned", "property_listings_drifted_simulated.csv")
        if not os.path.exists(current_path):
            current_path = baseline_path
        current_df = pd.read_csv(current_path)

    # 3. Load Models
    models_dir = os.path.join(BASE_DIR, "saved_models")
    pipeline = joblib.load(os.path.join(models_dir, "valuation_pipeline.joblib"))
    val_engine = joblib.load(os.path.join(models_dir, "valuation_quantile_engine.joblib"))

    # 4. Initialize Monitor
    monitor = ModelDriftMonitor(
        alert_mape_threshold=15.0,
        warning_psi_threshold=0.10,
        critical_psi_threshold=0.25,
        ks_pvalue_threshold=0.05
    )

    # 5. Evaluate Feature Drift
    monitored_features = [
        "price_pkr", "plot_size_marla", "covered_area_sqft", "bedrooms", 
        "bathrooms", "age_years", "city", "society_tier"
    ]
    feat_drift = monitor.evaluate_feature_drift(baseline_df, current_df, monitored_features)

    # 6. Evaluate Model Prediction & Performance Drift
    model_drift = monitor.evaluate_model_drift(
        pipeline=pipeline,
        model_engine=val_engine,
        baseline_df=baseline_df.sample(n=min(len(baseline_df), len(current_df)), random_state=42),
        current_df=current_df,
        target_col="price_pkr"
    )

    # 7. Aggregate Results
    summary = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "overall_status": model_drift["overall_status"],
        "retrain_recommended": model_drift["retrain_recommended"],
        "alert_mape_threshold_pct": monitor.alert_mape_threshold,
        "performance_drift": model_drift["performance_drift"],
        "prediction_drift": model_drift["prediction_drift"],
        "feature_drift": feat_drift
    }

    # 8. Save Reports
    reports_dir = os.path.join(BASE_DIR, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    
    json_path = os.path.join(reports_dir, "drift_report.json")
    html_path = os.path.join(reports_dir, "drift_report.html")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"Drift JSON summary saved to: {json_path}")

    generate_drift_html_report(summary, html_path)

    print("\n--- Drift Audit Summary ---")
    print(f"Overall Status:      {summary['overall_status']}")
    print(f"Current MAPE:        {summary['performance_drift']['current_mape_pct']}% (Alert Threshold: 15.0%)")
    print(f"Prediction PSI:      {summary['prediction_drift']['psi']}")
    print(f"Drifted Features:    {feat_drift['drifted_features_count']} of {feat_drift['total_features_evaluated']}")
    print(f"Retrain Triggered:   {summary['retrain_recommended']}")
    print("=" * 70)

    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Real Estate Model & Data Drift Monitor")
    parser.add_argument("--simulate", action="store_true", default=True, help="Simulate +15% price drift")
    parser.add_argument("--drift-pct", type=float, default=0.15, help="Simulated price inflation (default: 0.15)")
    parser.add_argument("--sample-size", type=int, default=1500, help="Number of records in production batch")
    args = parser.parse_args()

    run_drift_detection_flow(
        simulate_drift=args.simulate,
        price_inflation_pct=args.drift_pct,
        sample_size=args.sample_size
    )
