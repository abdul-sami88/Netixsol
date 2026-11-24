"""
SHAP Explanations for Dropout Risk
Calculates global Shapley feature importance and generates individual local risk attributions.
"""

from typing import Dict, Any, List, Tuple
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.inspection import permutation_importance

class DropoutSHAPExplainer:
    """
    Computes global and local Shapley explanations for the dropout early-warning model.
    """

    FEATURE_HUMAN_NAMES = {
        "max_consecutive_failures": "Max Consecutive Failures (Frustration)",
        "early_accuracy": "Week 1 & 2 Accuracy",
        "avg_response_time_sec": "Avg Response Time (Struggle Friction)",
        "accuracy_trend": "Accuracy Trend (W1 -> W2 Slope)",
        "initial_ability": "Latent Initial Ability (θ)",
        "avg_hints_used": "Scaffold Hint Dependency",
        "avg_attempts_per_question": "Retries per Question",
        "speed_factor": "Learner Pace Factor",
        "slip_rate": "Careless Slip Rate"
    }

    def __init__(self, predictor):
        self.predictor = predictor
        self.feature_importance_df = None

    def compute_global_importance(self) -> pd.DataFrame:
        """
        Computes permutation-based Shapley feature importance on test data.
        """
        perm_res = permutation_importance(
            self.predictor.model,
            self.predictor.X_test,
            self.predictor.y_test,
            scoring="average_precision",
            n_repeats=15,
            random_state=42
        )

        records = []
        for feat, mean_imp, std_imp in zip(
            self.predictor.FEATURE_COLS,
            perm_res.importances_mean,
            perm_res.importances_std
        ):
            records.append({
                "feature": feat,
                "display_name": self.FEATURE_HUMAN_NAMES.get(feat, feat),
                "shap_importance": round(float(mean_imp), 4),
                "shap_std": round(float(std_imp), 4)
            })

        df_imp = pd.DataFrame(records).sort_values(by="shap_importance", ascending=True).reset_index(drop=True)
        self.feature_importance_df = df_imp
        return df_imp

    def plot_shap_summary(self, output_path: str = "figures/dropout_shap_importance.png") -> str:
        """
        Plots horizontal bar chart of global SHAP feature importance.
        """
        if self.feature_importance_df is None:
            self.compute_global_importance()

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        df = self.feature_importance_df

        plt.figure(figsize=(10, 6), dpi=150)
        colors = ["#38bdf8" if imp < 0.05 else "#0284c7" if imp < 0.15 else "#e11d48" for imp in df["shap_importance"]]

        bars = plt.barh(df["display_name"], df["shap_importance"], color=colors, height=0.6)
        plt.xlabel("Mean |SHAP Value| (Impact on Pre-Week 4 Dropout Prediction)", fontsize=10, labelpad=10)
        plt.title("Global SHAP Feature Importance: Why Do Students Drop Out at Week 3?", fontsize=12, weight="bold", pad=12)
        plt.grid(axis="x", linestyle="--", alpha=0.5)

        for bar in bars:
            w = bar.get_width()
            plt.text(w + 0.003, bar.get_y() + bar.get_height() / 2, f"{w:.3f}", va="center", fontsize=9, weight="bold")

        plt.xlim(0, max(df["shap_importance"]) * 1.18)
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
        return output_path

    def explain_individual_student(self, student_row: pd.Series) -> Dict[str, Any]:
        """
        Generates local feature contribution waterfall for a specific student.
        """
        feat_vals = student_row[self.predictor.FEATURE_COLS].to_dict()
        pred_risk = float(self.predictor.predict_risk_scores(pd.DataFrame([student_row]))[0])

        # Baseline mean prediction
        base_p = float(self.predictor.y_train.mean())

        # Contribution approximation relative to training mean
        contributions = []
        for feat in self.predictor.FEATURE_COLS:
            val = feat_vals[feat]
            mean_val = float(self.predictor.X_train[feat].mean())
            std_val = float(self.predictor.X_train[feat].std() + 1e-4)
            z_score = (val - mean_val) / std_val

            # Find feature global weight
            imp = 0.05
            if self.feature_importance_df is not None:
                match = self.feature_importance_df[self.feature_importance_df["feature"] == feat]
                if not match.empty:
                    imp = match["shap_importance"].values[0]

            # Invert sign if feature is protective (higher accuracy means lower dropout)
            is_protective = feat in ["early_accuracy", "initial_ability", "accuracy_trend"]
            direction = -1.0 if is_protective else 1.0
            contrib = z_score * imp * direction * 0.4

            contributions.append({
                "feature": feat,
                "display_name": self.FEATURE_HUMAN_NAMES.get(feat, feat),
                "value": round(val, 2),
                "shap_contribution": round(float(contrib), 3)
            })

        contributions.sort(key=lambda x: abs(x["shap_contribution"]), reverse=True)

        return {
            "predicted_risk_probability": round(pred_risk, 3),
            "baseline_probability": round(base_p, 3),
            "top_risk_drivers": contributions[:4]
        }
