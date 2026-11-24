"""
Item Response Theory (IRT) Engine: 1PL (Rasch) and 2PL Estimation
Estimates item difficulty (b) and item discrimination (a) across student interactions.
"""

from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from sklearn.linear_model import LogisticRegression

class IRTEngine:
    """
    Fits 1PL (Rasch) and 2PL Item Response Theory models.
    2PL: P(Y=1 | theta, a, b) = 1 / (1 + exp(-a * (theta - b)))
    1PL: P(Y=1 | theta, b)    = 1 / (1 + exp(-(theta - b)))
    """

    def __init__(self):
        self.item_params: Dict[str, Dict[str, float]] = {}
        self.student_abilities: Dict[str, float] = {}

    def fit(self, interactions_df: pd.DataFrame) -> "IRTEngine":
        """
        Estimates student ability theta_i and item parameters (a_j, b_j).
        Uses joint estimation via standardized student raw score proxies and logistic regression.
        """
        # Step 1: Calculate initial student ability theta proxy from global accuracy
        stu_stats = interactions_df.groupby("student_id")["is_correct"].agg(["mean", "count"])
        # Logit transformation of accuracy with empirical shrinkage
        eps = 1e-4
        stu_acc = np.clip(stu_stats["mean"].values, 0.05, 0.95)
        # Standardize ability distribution to mean 0, std 1
        raw_theta = np.log(stu_acc / (1.0 - stu_acc))
        std_theta = (raw_theta - np.mean(raw_theta)) / (np.std(raw_theta) + eps)
        self.student_abilities = dict(zip(stu_stats.index, std_theta))

        # Add estimated ability to interactions
        df = interactions_df.copy()
        df["theta"] = df["student_id"].map(self.student_abilities)

        # Step 2: Fit 1PL and 2PL for each item
        items = df["question_id"].unique()

        for q_id in items:
            q_df = df[df["question_id"] == q_id]
            if len(q_df) < 5:
                self.item_params[q_id] = {
                    "question_id": q_id,
                    "concept_id": q_df["concept_id"].iloc[0] if len(q_df) > 0 else "unknown",
                    "sample_size": len(q_df),
                    "mean_accuracy": float(q_df["is_correct"].mean()) if len(q_df) > 0 else 0.5,
                    "b_1pl": 0.0,
                    "b_2pl": 0.0,
                    "a_2pl": 1.0,
                    "point_biserial": 0.3
                }
                continue

            X_theta = q_df["theta"].values.reshape(-1, 1)
            y_resp = q_df["is_correct"].values
            mean_acc = float(np.mean(y_resp))

            # Point-biserial correlation between item response and student overall ability
            std_y = np.std(y_resp)
            std_t = np.std(q_df["theta"].values)
            if std_y > 0 and std_t > 0:
                p_biserial = float(np.corrcoef(y_resp, q_df["theta"].values)[0, 1])
            else:
                p_biserial = 0.0

            # 2PL Estimation via Logistic Regression:
            # logit(P) = beta_0 + beta_1 * theta = a * (theta - b)
            # -> a = beta_1, b = -beta_0 / beta_1
            try:
                lr = LogisticRegression(C=1e4, max_iter=200)
                lr.fit(X_theta, y_resp)
                a_2pl = float(lr.coef_[0][0])
                beta_0 = float(lr.intercept_[0])
                if abs(a_2pl) > 1e-3:
                    b_2pl = float(-beta_0 / a_2pl)
                else:
                    b_2pl = float(-beta_0)
                b_2pl = float(np.clip(b_2pl, -4.0, 4.0))
                a_2pl = float(np.clip(a_2pl, -2.5, 3.5))
            except Exception:
                # Fallback to empirical difficulty
                p_clip = np.clip(mean_acc, 0.02, 0.98)
                b_2pl = float(-np.log(p_clip / (1.0 - p_clip)))
                a_2pl = 1.0

            # 1PL (Rasch) Estimation (fixing a = 1.0):
            # logit(P) = theta - b -> b = mean(theta) - logit(mean_acc)
            p_clip = np.clip(mean_acc, 0.02, 0.98)
            b_1pl = float(-np.log(p_clip / (1.0 - p_clip)))

            self.item_params[q_id] = {
                "question_id": q_id,
                "concept_id": q_df["concept_id"].iloc[0],
                "sample_size": len(q_df),
                "mean_accuracy": round(mean_acc, 4),
                "b_1pl": round(b_1pl, 3),
                "b_2pl": round(b_2pl, 3),
                "a_2pl": round(a_2pl, 3),
                "point_biserial": round(p_biserial, 3)
            }

        return self

    def get_item_parameters_df(self) -> pd.DataFrame:
        """Returns all estimated item psychometric parameters as a DataFrame."""
        return pd.DataFrame(list(self.item_params.values()))

    def predict_probability(self, theta: float, question_id: str, model: str = "2pl") -> float:
        """Computes predicted probability of success for ability theta on question_id."""
        params = self.item_params.get(question_id, None)
        if params is None:
            return 0.5

        if model == "1pl":
            b = params["b_1pl"]
            logit = theta - b
        else:
            a = params["a_2pl"]
            b = params["b_2pl"]
            logit = a * (theta - b)

        prob = 1.0 / (1.0 + np.exp(-np.clip(logit, -15.0, 15.0)))
        return float(prob)
