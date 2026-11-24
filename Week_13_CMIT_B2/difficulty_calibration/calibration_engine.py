"""
Difficulty Calibration Engine
Compares LLM-predicted cognitive difficulty with empirically measured 2PL IRT difficulty (b).
Computes calibration metrics (MAE, RMSE, Pearson r) and diagnoses miscalibrated items.
"""

from typing import Dict, Any, List, Tuple
import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from difficulty_calibration.llm_difficulty_estimator import LLMDifficultyEstimator

class DifficultyCalibrationEngine:
    """
    Evaluates alignment between expected cognitive difficulty and observed student performance.
    """

    def __init__(self, irt_params_df: pd.DataFrame, question_bank: List[Dict[str, Any]]):
        self.irt_df = irt_params_df
        self.question_bank = {q["id"]: q for q in question_bank}
        self.comparison_df: pd.DataFrame = None

    def run_calibration(self) -> pd.DataFrame:
        """
        Calculates predicted vs measured difficulty for all items.
        """
        records = []
        for _, row in self.irt_df.iterrows():
            q_id = row["question_id"]
            b_meas = float(row["b_2pl"])
            a_meas = float(row["a_2pl"])
            acc = float(row["mean_accuracy"])
            cid = row["concept_id"]

            q_obj = self.question_bank.get(q_id, {"blooms_level": "Applying", "concept_id": cid, "type": "mcq"})
            b_pred = LLMDifficultyEstimator.estimate_difficulty(q_obj)

            residual = round(b_meas - b_pred, 3)
            records.append({
                "question_id": q_id,
                "concept_id": cid,
                "blooms_level": q_obj.get("blooms_level", "Applying"),
                "type": q_obj.get("type", "mcq"),
                "predicted_b": b_pred,
                "measured_b": round(b_meas, 3),
                "residual_error": residual,
                "abs_residual": abs(residual),
                "discrimination_a": round(a_meas, 3),
                "accuracy_pct": round(acc * 100, 1),
                "miscalibration_type": "Underestimated" if residual > 1.2 else "Overestimated" if residual < -1.2 else "Well_Calibrated"
            })

        df = pd.DataFrame(records)
        self.comparison_df = df
        return df

    def compute_metrics(self) -> Dict[str, Any]:
        """
        Computes MAE, RMSE, Pearson correlation r, and miscalibration rates.
        """
        if self.comparison_df is None:
            self.run_calibration()

        df = self.comparison_df
        b_pred = df["predicted_b"].values
        b_meas = df["measured_b"].values

        mae = float(np.mean(np.abs(b_meas - b_pred)))
        rmse = float(np.sqrt(np.mean((b_meas - b_pred)**2)))
        pearson_r = float(np.corrcoef(b_pred, b_meas)[0, 1])

        well_calibrated = len(df[df["miscalibration_type"] == "Well_Calibrated"])
        underestimated = len(df[df["miscalibration_type"] == "Underestimated"])
        overestimated = len(df[df["miscalibration_type"] == "Overestimated"])

        return {
            "total_items_calibrated": len(df),
            "mae": round(mae, 3),
            "rmse": round(rmse, 3),
            "pearson_correlation_r": round(pearson_r, 3),
            "well_calibrated_count": well_calibrated,
            "well_calibrated_pct": round(well_calibrated / len(df) * 100, 1),
            "underestimated_count": underestimated,
            "overestimated_count": overestimated
        }

    def plot_calibration_scatter(self, output_path: str = "figures/difficulty_calibration_scatter.png") -> str:
        """
        Renders scatter plot comparing predicted vs measured difficulty with regression line.
        """
        if self.comparison_df is None:
            self.run_calibration()

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        df = self.comparison_df
        metrics = self.compute_metrics()

        plt.figure(figsize=(9, 6.5), dpi=150)

        # Plot points color-coded by miscalibration type
        palette = {"Well_Calibrated": "#10b981", "Underestimated": "#ef4444", "Overestimated": "#f59e0b"}
        for m_type, color in palette.items():
            sub = df[df["miscalibration_type"] == m_type]
            plt.scatter(sub["predicted_b"], sub["measured_b"], color=color, alpha=0.75, s=40, label=f"{m_type.replace('_', ' ')} ({len(sub)})")

        # Identity line (y = x)
        lims = [-3.0, 3.0]
        plt.plot(lims, lims, color="#64748b", linestyle="--", lw=1.5, label="Perfect Calibration Line (y = x)")

        # Linear trendline
        m, c = np.polyfit(df["predicted_b"], df["measured_b"], 1)
        x_trend = np.linspace(-2.5, 2.5, 100)
        plt.plot(x_trend, m * x_trend + c, color="#0284c7", lw=2, label=f"Fitted Trend (r = {metrics['pearson_correlation_r']:.3f})")

        plt.title("Difficulty Calibration: LLM-Predicted vs. Measured 2PL IRT Difficulty (b)", fontsize=12, weight="bold", pad=12)
        plt.xlabel("LLM-Predicted Cognitive Difficulty (b_pred)", fontsize=10)
        plt.ylabel("Measured Empirical Difficulty 2PL IRT (b_meas)", fontsize=10)
        plt.xlim(-3.0, 3.0)
        plt.ylim(-3.0, 3.0)
        plt.grid(True, linestyle="--", alpha=0.5)
        plt.legend(frameon=True, loc="upper left")

        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
        return output_path
