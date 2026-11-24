"""
Baseline Knowledge Tracing Model
Implements a concept-specific empirical Bayesian prior baseline.
"""

from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd

class BaselineKTModel:
    """
    Empirical Bayes Baseline Model for Knowledge Tracing.
    Predicts probability based on historical concept accuracy smoothed with global prior.
    """

    def __init__(self, laplace_alpha: float = 1.0, laplace_beta: float = 2.0):
        self.laplace_alpha = laplace_alpha
        self.laplace_beta = laplace_beta
        self.concept_probs: Dict[str, float] = {}
        self.global_mean: float = 0.5

    def fit(self, train_df: pd.DataFrame) -> "BaselineKTModel":
        """
        Calculates smoothed historical accuracy per concept on training interactions.
        """
        self.global_mean = float(train_df["is_correct"].mean())
        grouped = train_df.groupby("concept_id")["is_correct"].agg(["sum", "count"]).to_dict(orient="index")

        for cid, stats in grouped.items():
            smoothed = (stats["sum"] + self.laplace_alpha) / (stats["count"] + self.laplace_beta)
            self.concept_probs[cid] = float(smoothed)

        return self

    def predict_proba(self, test_df: pd.DataFrame) -> np.ndarray:
        """
        Predicts probability of correct response for each test interaction.
        """
        preds = []
        for _, row in test_df.iterrows():
            cid = row["concept_id"]
            p = self.concept_probs.get(cid, self.global_mean)
            preds.append(p)
        return np.array(preds)
