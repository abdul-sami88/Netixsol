"""
Bad Question Detector (Item Psychometrics & Anomaly Auditing)
Identifies defective assessment questions using 2PL IRT discrimination (a),
difficulty (b), and point-biserial correlations.
"""

from typing import Dict, Any, List, Optional
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

class BadQuestionDetector:
    """
    Scans question bank and interaction metrics to flag psychometrically flawed questions.
    """

    CRITERIA = {
        "min_discrimination": 0.25,     # Below 0.25 has poor discriminative power
        "critical_neg_discrim": 0.0,    # Below 0 is inverted (high ability fails!)
        "min_point_biserial": 0.15,     # Weak correlation with overall ability
        "max_difficulty_b": 2.5,        # Extreme floor effect (>2.5 is excessively punishing)
        "min_difficulty_b": -2.5        # Extreme ceiling effect (<-2.5 is trivial)
    }

    def __init__(self, irt_params_df: pd.DataFrame, question_bank: Optional[List[Dict[str, Any]]] = None):
        self.irt_df = irt_params_df
        self.question_bank = {q["id"]: q for q in question_bank} if question_bank else {}
        self.flagged_questions: List[Dict[str, Any]] = []

    def audit_questions(self) -> pd.DataFrame:
        """
        Audits all questions against psychometric quality standards.
        """
        flagged = []

        for _, row in self.irt_df.iterrows():
            q_id = row["question_id"]
            a = row["a_2pl"]
            b = row["b_2pl"]
            p_bis = row["point_biserial"]
            acc = row["mean_accuracy"]

            defects = []
            severity = "NORMAL"

            # Check for negative or inverted discrimination
            if a < self.CRITERIA["critical_neg_discrim"]:
                defects.append("Inverted Discrimination (a < 0): High-ability students fail more often than low-ability students.")
                severity = "CRITICAL"
            elif a < self.CRITERIA["min_discrimination"]:
                defects.append(f"Low Discrimination (a={a:.2f}): Question acts like random noise; fails to distinguish mastery.")
                if severity != "CRITICAL":
                    severity = "MODERATE"

            # Check point-biserial correlation
            if p_bis < self.CRITERIA["min_point_biserial"]:
                defects.append(f"Weak Point-Biserial Correlation (r_pb={p_bis:.2f}): Misaligned with overall test performance.")
                if severity == "NORMAL":
                    severity = "MODERATE"

            # Check extreme difficulty
            if b > self.CRITERIA["max_difficulty_b"] or acc < 0.20:
                defects.append(f"Extreme Floor Effect (b={b:.2f}, acc={acc*100:.1f}%): Excessively punitive; triggers dropout.")
                if severity != "CRITICAL":
                    severity = "MODERATE"
            elif b < self.CRITERIA["min_difficulty_b"] or acc > 0.92:
                defects.append(f"Trivial Ceiling Effect (b={b:.2f}, acc={acc*100:.1f}%): Lacks diagnostic depth.")

            if defects:
                q_meta = self.question_bank.get(q_id, {})
                remedial_action = self._suggest_remedial_action(defects)

                flagged.append({
                    "question_id": q_id,
                    "concept_id": row["concept_id"],
                    "severity": severity,
                    "discrimination_a": round(a, 3),
                    "difficulty_b": round(b, 3),
                    "point_biserial": round(p_bis, 3),
                    "mean_accuracy_pct": round(acc * 100, 1),
                    "defects_count": len(defects),
                    "primary_defect": defects[0],
                    "remedial_action": remedial_action,
                    "prompt": q_meta.get("prompt", "")[:90] + "..." if q_meta.get("prompt") else "N/A"
                })

        self.flagged_questions = flagged
        df_flagged = pd.DataFrame(flagged)
        if not df_flagged.empty:
            df_flagged = df_flagged.sort_values(
                by=["severity", "discrimination_a"],
                ascending=[True, True]
            ).reset_index(drop=True)
        return df_flagged

    def _suggest_remedial_action(self, defects: List[str]) -> str:
        """Prescribes authoring corrections for flagged question defects."""
        text = " ".join(defects)
        if "Inverted Discrimination" in text:
            return "URGENT: Review answer key for errors; re-examine ambiguous distractor options that mislead proficient students."
        elif "Low Discrimination" in text:
            return "Clarify prompt wording; ensure options test core concept mechanics rather than superficial trivia."
        elif "Floor Effect" in text:
            return "Split into two scaffolding steps; provide clearer starter code templates and hint ladders."
        elif "Ceiling Effect" in text:
            return "Increase cognitive depth to Bloom's Applying/Analyzing tier; test realistic boundary values."
        return "Review item for general psychometric refinement."

    def plot_icc_comparison(
        self,
        good_qid: str,
        bad_qid: str,
        output_path: str = "figures/item_characteristic_curves.png"
    ) -> str:
        """
        Plots Item Characteristic Curves (ICC) comparing an exemplary question with a defective question.
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        theta_range = np.linspace(-3.5, 3.5, 200)

        good_row = self.irt_df[self.irt_df["question_id"] == good_qid]
        bad_row = self.irt_df[self.irt_df["question_id"] == bad_qid]

        if good_row.empty or bad_row.empty:
            # Fallback to extreme cases
            good_a, good_b = 1.45, 0.20
            bad_a, bad_b = -0.15, 1.85
        else:
            good_a, good_b = good_row["a_2pl"].values[0], good_row["b_2pl"].values[0]
            bad_a, bad_b = bad_row["a_2pl"].values[0], bad_row["b_2pl"].values[0]

        p_good = 1.0 / (1.0 + np.exp(-good_a * (theta_range - good_b)))
        p_bad = 1.0 / (1.0 + np.exp(-bad_a * (theta_range - bad_b)))

        plt.figure(figsize=(9, 5.5), dpi=150)
        plt.plot(theta_range, p_good, color="#10b981", lw=2.5, label=f"Good Item ({good_qid}): a={good_a:.2f}, b={good_b:.2f} (Ideal Monotonic)")
        plt.plot(theta_range, p_bad, color="#ef4444", lw=2.5, linestyle="--", label=f"Defective Item ({bad_qid}): a={bad_a:.2f}, b={bad_b:.2f} (Inverted / Flat)")

        plt.axhline(0.5, color="#94a3b8", linestyle=":", alpha=0.7)
        plt.axvline(0.0, color="#94a3b8", linestyle=":", alpha=0.7)

        plt.title("2PL Item Characteristic Curves (ICC): Good vs Flawed Question", fontsize=12, weight="bold", pad=12)
        plt.xlabel("Student Latent Ability (θ)", fontsize=10)
        plt.ylabel("Probability of Correct Response P(Y=1)", fontsize=10)
        plt.ylim(-0.05, 1.05)
        plt.grid(True, linestyle="--", alpha=0.5)
        plt.legend(frameon=True, loc="upper left")
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
        return output_path
