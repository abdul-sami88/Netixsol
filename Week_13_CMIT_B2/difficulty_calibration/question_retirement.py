"""
Question Retirement & Remediation Policy
Identifies defective, anomalous, or miscalibrated items and retires them from active rotation.
"""

from typing import Dict, Any, List
import os
import json
import pandas as pd

class QuestionRetirementPolicy:
    """
    Enforces quality standards by identifying and retiring psychometrically flawed items.
    """

    RETIREMENT_THRESHOLDS = {
        "min_discrimination": 0.25,     # Items below 0.25 fail to differentiate mastery
        "critical_neg_discrim": 0.0,    # Inverted items (harmful)
        "max_abs_residual": 2.0,        # Severe calibration mismatch
        "min_accuracy": 0.15,           # Unusable floor effect
        "max_accuracy": 0.95            # Trivial ceiling effect
    }

    @classmethod
    def evaluate_retirement(cls, calibration_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Splits questions into active/retained set and retired set.
        Returns (retained_df, retired_df).
        """
        retired = []
        retained = []

        for _, row in calibration_df.iterrows():
            q_id = row["question_id"]
            a = row["discrimination_a"]
            b = row["measured_b"]
            acc = row["accuracy_pct"] / 100.0
            res = abs(row["residual_error"])

            reasons = []
            if a < cls.RETIREMENT_THRESHOLDS["critical_neg_discrim"]:
                reasons.append("Critical: Inverted discrimination (a < 0). Proficient students fail more frequently.")
            elif a < cls.RETIREMENT_THRESHOLDS["min_discrimination"]:
                reasons.append(f"Substandard discrimination (a={a:.2f} < 0.25). Provides little diagnostic value.")

            if acc < cls.RETIREMENT_THRESHOLDS["min_accuracy"] or b > 2.6:
                reasons.append(f"Severe floor effect: accuracy={acc*100:.1f}%, difficulty={b:.2f}. Causes high dropout.")

            if res > cls.RETIREMENT_THRESHOLDS["max_abs_residual"]:
                reasons.append(f"Severe calibration failure: residual={res:.2f}. Item behaves unpredictably.")

            if reasons:
                row_dict = dict(row)
                row_dict["retirement_reasons"] = reasons
                row_dict["remediation_plan"] = cls._prescribe_fix(reasons)
                retired.append(row_dict)
            else:
                retained.append(dict(row))

        df_ret = pd.DataFrame(retired)
        df_keep = pd.DataFrame(retained)
        return df_keep, df_ret

    @classmethod
    def _prescribe_fix(cls, reasons: List[str]) -> str:
        text = " ".join(reasons)
        if "Inverted discrimination" in text:
            return "Re-author question: audit answer key for false keys; eliminate deceptive trick options."
        elif "Substandard discrimination" in text:
            return "Rewrite options to target explicit student mental models and diagnostic misconceptions."
        elif "floor effect" in text:
            return "Add intermediate scaffolding hint ladder; provide docstring and starter template."
        return "Calibrate cognitive complexity to target intermediate Bloom's tier."

    @classmethod
    def export_retirement_report(
        cls,
        calibration_df: pd.DataFrame,
        output_path: str = "day3_reports/retired_questions.json"
    ) -> Dict[str, Any]:
        """Exports retired question audit to disk."""
        df_keep, df_ret = cls.evaluate_retirement(calibration_df)
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        report = {
            "total_items_audited": len(calibration_df),
            "retained_active_items": len(df_keep),
            "retired_items_count": len(df_ret),
            "retirement_rate_pct": round(len(df_ret) / len(calibration_df) * 100, 1),
            "retired_questions": df_ret.to_dict(orient="records") if not df_ret.empty else []
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        return report
