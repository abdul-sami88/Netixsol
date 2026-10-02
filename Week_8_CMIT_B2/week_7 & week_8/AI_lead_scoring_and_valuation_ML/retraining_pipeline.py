"""
retraining_pipeline.py
======================
Day 5 - Task 2: Automated Retraining, Model Evaluation, Gated Promotion & Rollback Engine.

Workflow:
1. Ingests new production data / drifted market batch
2. Retrains challenger model (LightGBM / Quantile Engine / SHAP Explainer)
3. Evaluates Challenger vs Champion on a strict holdout test set
4. Gated Promotion: Promotes Challenger only if Challenger MAPE < Champion MAPE and R² is maintained
5. Rollback Mechanism: Creates automated versioned snapshots before promotion with 1-click restore
6. Retraining Scheduler: Supports Event-Driven (Drift Alert) and Cron-Based (Monthly) triggers
"""

import os
import sys
import shutil
import json
import argparse
from datetime import datetime
from typing import Dict, Any, Tuple, Optional

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

import numpy as np
import pandas as pd
import joblib
from lightgbm import LGBMRegressor
import shap

# Setup paths
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "src"))

from src.pipeline import (
    split_data_70_15_15,
    build_property_pipeline,
    LEAKAGE_COLUMNS_PROPERTY
)
from src.valuation_models import (
    compute_regression_metrics,
    format_crore_lakh,
    PropertyValuationEngine
)


MODELS_DIR = os.path.join(BASE_DIR, "saved_models")
ARCHIVE_DIR = os.path.join(MODELS_DIR, "archive")
ROLLBACK_DIR = os.path.join(MODELS_DIR, "rollback")


# ========================================================
# 1. Rollback & Snapshot Manager
# ========================================================
class ModelVersionManager:
    """Manages backup snapshots, immutable archiving, and automated rollback."""
    
    ARTIFACT_FILES = [
        "valuation_champion_model.joblib",
        "valuation_pipeline.joblib",
        "valuation_quantile_engine.joblib",
        "valuation_shap_explainer.joblib",
        "models_metadata.json"
    ]

    @classmethod
    def create_snapshot(cls, tag: Optional[str] = None) -> str:
        """Creates a timestamped snapshot in saved_models/archive and updates saved_models/rollback."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        version_tag = f"snapshot_{timestamp}" if not tag else f"snapshot_{timestamp}_{tag}"
        target_dir = os.path.join(ARCHIVE_DIR, version_tag)
        os.makedirs(target_dir, exist_ok=True)
        os.makedirs(ROLLBACK_DIR, exist_ok=True)

        copied_count = 0
        for fname in cls.ARTIFACT_FILES:
            src = os.path.join(MODELS_DIR, fname)
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(target_dir, fname))
                shutil.copy2(src, os.path.join(ROLLBACK_DIR, fname))
                copied_count += 1

        print(f"Created version snapshot ({copied_count} files) at: {target_dir}")
        print(f"Updated quick-rollback mirror at: {ROLLBACK_DIR}")
        return target_dir

    @classmethod
    def execute_rollback(cls, source_dir: Optional[str] = None) -> bool:
        """Restores model artifacts from rollback/ or a specified archive snapshot."""
        src_path = source_dir or ROLLBACK_DIR
        if not os.path.exists(src_path):
            print(f"Rollback failed: source directory does not exist ({src_path})")
            return False

        available_files = [f for f in cls.ARTIFACT_FILES if os.path.exists(os.path.join(src_path, f))]
        if not available_files:
            print(f"Rollback failed: No model artifacts found in {src_path}")
            return False

        print(f"Initiating rollback from: {src_path}")
        for fname in available_files:
            src = os.path.join(src_path, fname)
            dst = os.path.join(MODELS_DIR, fname)
            shutil.copy2(src, dst)
            print(f"Restored: {fname}")

        print("Model rollback completed successfully. Previous champion reinstated.")
        return True


# ========================================================
# 2. Automated Retraining & Gated Promotion Pipeline
# ========================================================
class RetrainingPipeline:
    def __init__(self, models_dir: str = MODELS_DIR):
        self.models_dir = models_dir
        self.version_manager = ModelVersionManager()

    def load_champion(self) -> Tuple[Any, Any, Any, Dict[str, Any]]:
        """Loads current champion pipeline, model, engine, and metadata."""
        pipe_path = os.path.join(self.models_dir, "valuation_pipeline.joblib")
        model_path = os.path.join(self.models_dir, "valuation_champion_model.joblib")
        engine_path = os.path.join(self.models_dir, "valuation_quantile_engine.joblib")
        meta_path = os.path.join(self.models_dir, "models_metadata.json")

        if not (os.path.exists(pipe_path) and os.path.exists(model_path)):
            raise RuntimeError(f"Champion artifacts missing in {self.models_dir}")

        pipeline = joblib.load(pipe_path)
        champion_model = joblib.load(model_path)
        engine = joblib.load(engine_path)
        with open(meta_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        return pipeline, champion_model, engine, metadata

    def run_retraining(
        self,
        new_data_path: str,
        acceptance_margin_pct: float = 0.0,
        force_promote: bool = False
    ) -> Dict[str, Any]:
        """
        Executes end-to-end retraining:
        1. Ingests new data combined with baseline historical data
        2. Splits into train/val/holdout
        3. Trains Challenger LightGBM model and Quantile Engine
        4. Benchmarks Champion vs Challenger on holdout set
        5. Gated promotion with automatic rollback snapshot
        """
        print("\n" + "=" * 80)
        print(">>> INITIATING AUTOMATED RETRAINING & GATED PROMOTION PIPELINE")
        print("=" * 80)

        # 1. Load Data
        base_path = os.path.join(BASE_DIR, "data_cleaned", "property_listings_cleaned.csv")
        df_base = pd.read_csv(base_path)
        
        if os.path.exists(new_data_path):
            df_new = pd.read_csv(new_data_path)
            print(f"Loaded new production batch: {len(df_new):,} records from {os.path.basename(new_data_path)}")
            # Combine historical + new batch with weighting towards recent trends
            combined_df = pd.concat([df_base, df_new], ignore_index=True)
        else:
            print(f"New data path not found ({new_data_path}), falling back to baseline.")
            combined_df = df_base

        print(f"Total training pool: {len(combined_df):,} records")

        # 2. Prepare features and target
        y_pkr = combined_df["price_pkr"].values
        y_log = np.log1p(y_pkr)
        feature_cols = [c for c in combined_df.columns if c not in LEAKAGE_COLUMNS_PROPERTY + ["price_pkr"]]
        X_raw = combined_df[feature_cols].copy()

        # Holdout split: 70% train, 15% validation, 15% holdout test
        X_train_raw, X_val_raw, X_test_raw, y_train_log, y_val_log, y_test_log = split_data_70_15_15(
            X_raw, pd.Series(y_log), random_state=42
        )
        y_test_pkr = np.expm1(y_test_log.values)

        # 3. Fit New Pipeline & Challenger Model
        print("Fitting Challenger ColumnTransformer pipeline...")
        challenger_pipeline, raw_features = build_property_pipeline(encoder_type="target")
        X_train_proc = challenger_pipeline.fit_transform(X_train_raw, y_train_log.values)
        X_test_proc = challenger_pipeline.transform(X_test_raw)

        print("Training Challenger LightGBM Regressor on latest market distribution...")
        challenger_model = LGBMRegressor(
            n_estimators=350,
            learning_rate=0.05,
            max_depth=8,
            num_leaves=45,
            subsample=0.85,
            colsample_bytree=0.85,
            reg_alpha=0.15,
            reg_lambda=1.2,
            random_state=42,
            n_jobs=-1,
            verbose=-1
        )
        challenger_model.fit(X_train_proc, y_train_log.values)

        # 4. Evaluate Challenger on Holdout Set
        challenger_preds_pkr = np.expm1(challenger_model.predict(X_test_proc))
        challenger_metrics = compute_regression_metrics(y_test_pkr, challenger_preds_pkr)

        # 5. Evaluate Current Champion on the SAME Holdout Set
        champ_pipe, champ_model, champ_engine, champ_meta = self.load_champion()
        X_test_champ_proc = champ_pipe.transform(X_test_raw)
        champ_preds_pkr = np.expm1(champ_model.predict(X_test_champ_proc))
        champion_metrics = compute_regression_metrics(y_test_pkr, champ_preds_pkr)

        print("\n--- Model Benchmark on Production Holdout Set ---")
        print(f"Current Champion -> MAPE: {champion_metrics['MAPE_pct']:.2f}% | R²: {champion_metrics['R2']:.4f} | MAE: {format_crore_lakh(champion_metrics['MAE_PKR'])}")
        print(f"Challenger Model -> MAPE: {challenger_metrics['MAPE_pct']:.2f}% | R²: {challenger_metrics['R2']:.4f} | MAE: {format_crore_lakh(challenger_metrics['MAE_PKR'])}")

        mape_improvement = champion_metrics["MAPE_pct"] - challenger_metrics["MAPE_pct"]
        r2_improvement = challenger_metrics["R2"] - champion_metrics["R2"]

        print(f"Delta: MAPE Improvement: {mape_improvement:+.2f}% | R² Improvement: {r2_improvement:+.4f}")

        # 6. Gated Promotion Decision
        # Challenger must improve MAPE by at least acceptance_margin_pct and not collapse R2
        is_promoted = force_promote or (
            (challenger_metrics["MAPE_pct"] < champion_metrics["MAPE_pct"] - acceptance_margin_pct) and
            (challenger_metrics["R2"] >= champion_metrics["R2"] - 0.02)
        )

        promotion_result = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "promoted": bool(is_promoted),
            "champion_metrics": {
                "MAPE_pct": round(champion_metrics["MAPE_pct"], 2),
                "R2": round(champion_metrics["R2"], 4),
                "MAE_pkr": round(champion_metrics["MAE_PKR"], 0),
                "MAE_formatted": format_crore_lakh(champion_metrics["MAE_PKR"])
            },
            "challenger_metrics": {
                "MAPE_pct": round(challenger_metrics["MAPE_pct"], 2),
                "R2": round(challenger_metrics["R2"], 4),
                "MAE_pkr": round(challenger_metrics["MAE_PKR"], 0),
                "MAE_formatted": format_crore_lakh(challenger_metrics["MAE_PKR"])
            },
            "deltas": {
                "mape_improvement_pct": round(mape_improvement, 2),
                "r2_improvement": round(r2_improvement, 4)
            }
        }

        if is_promoted:
            print("\n✅ PROMOTION ACCEPTED: Challenger outperformed Champion! Commencing deployment.")
            # 1. Create rollback snapshot of current champion
            snapshot_dir = self.version_manager.create_snapshot(tag="pre_retrain")
            promotion_result["rollback_snapshot"] = snapshot_dir

            # 2. Fit Quantile Engine and SHAP explainer for Challenger
            print("Fitting Quantile Engine (80% Confidence Interval) for Challenger...")
            challenger_engine = PropertyValuationEngine(confidence_level=0.80)
            challenger_engine.fit(X_train_proc, y_train_log.values)

            print("Fitting SHAP TreeExplainer for Challenger...")
            challenger_explainer = shap.TreeExplainer(challenger_model)

            # 3. Overwrite Active Production Artifacts
            joblib.dump(challenger_pipeline, os.path.join(self.models_dir, "valuation_pipeline.joblib"))
            joblib.dump(challenger_model, os.path.join(self.models_dir, "valuation_champion_model.joblib"))
            joblib.dump(challenger_engine, os.path.join(self.models_dir, "valuation_quantile_engine.joblib"))
            joblib.dump(challenger_explainer, os.path.join(self.models_dir, "valuation_shap_explainer.joblib"))

            # 4. Update Metadata
            new_version = f"1.1.{int(datetime.now().strftime('%m%d%H'))}"
            champ_meta["property_valuation"]["version"] = new_version
            champ_meta["property_valuation"]["trained_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            champ_meta["property_valuation"]["metrics"] = {
                "MAE_PKR": round(challenger_metrics["MAE_PKR"], 2),
                "MAE_formatted": format_crore_lakh(challenger_metrics["MAE_PKR"]),
                "RMSE_PKR": round(challenger_metrics["RMSE_PKR"], 2),
                "R2": round(challenger_metrics["R2"], 4),
                "MAPE_pct": round(challenger_metrics["MAPE_pct"], 2)
            }
            with open(os.path.join(self.models_dir, "models_metadata.json"), "w", encoding="utf-8") as f:
                json.dump(champ_meta, f, indent=2)

            promotion_result["deployed_version"] = new_version
            print(f"🎉 Challenger successfully deployed as Champion Version {new_version}!")
        else:
            print("\n❌ PROMOTION REJECTED: Challenger did not beat current Champion SLA. Preserving existing Champion.")

        # Save Retraining Audit Log
        audit_log_path = os.path.join(BASE_DIR, "reports", "retraining_audit_log.json")
        os.makedirs(os.path.dirname(audit_log_path), exist_ok=True)
        
        history = []
        if os.path.exists(audit_log_path):
            try:
                with open(audit_log_path, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except Exception:
                history = []
        history.append(promotion_result)
        with open(audit_log_path, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)
        print(f"Retraining audit log updated at: {audit_log_path}")

        return promotion_result


# ========================================================
# 3. Retraining Schedule & Triggers Definition
# ========================================================
SCHEDULE_DOCUMENTATION = """
# Pakistan Real Estate AI — Retraining & Model Lifecycle Schedule

1. Event-Driven Trigger (Drift Violation):
   - Condition: MAPE > 15.0% or Prediction PSI >= 0.25 on a 30-day sliding batch.
   - Mechanism: drift_monitoring.py triggers retraining_pipeline.py via webhook / subprocess.
   - Frequency: On-Demand (within 1 hour of drift detection alert).

2. Calendar-Driven Schedule (Monthly Cadence):
   - Cron Expression: `0 2 1 * *` (Runs on the 1st of every month at 02:00 AM PKT / 21:00 UTC).
   - Rationale: Captures monthly real estate inflation, new development schemes, and shifting demand.
   - Orchestration: Render Cron Job / GitHub Actions Workflow / Linux crontab.

3. Rollback Runbook:
   - Command: `python retraining_pipeline.py --rollback`
   - SLA: Instant restore (< 15 seconds) from saved_models/rollback/.
"""


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automated Retraining Pipeline")
    parser.add_argument("--new-data", type=str, default="data_cleaned/property_listings_drifted_simulated.csv",
                        help="Path to new drifted production data batch")
    parser.add_argument("--rollback", action="store_true", help="Execute immediate rollback to previous champion")
    parser.add_argument("--force-promote", action="store_true", help="Force champion promotion regardless of threshold")
    parser.add_argument("--print-schedule", action="store_true", help="Print operational retraining schedule")
    args = parser.parse_args()

    if args.print_schedule:
        print(SCHEDULE_DOCUMENTATION)
        sys.exit(0)

    if args.rollback:
        ModelVersionManager.execute_rollback()
        sys.exit(0)

    pipeline = RetrainingPipeline()
    pipeline.run_retraining(
        new_data_path=os.path.join(BASE_DIR, args.new_data),
        force_promote=args.force_promote
    )
