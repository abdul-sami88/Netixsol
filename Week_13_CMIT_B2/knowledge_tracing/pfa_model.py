"""
Performance Factors Analysis (PFA) Model
Predicts learner correctness as a logistic function of concept baseline easiness,
cumulative prior successes (s_ik), and cumulative prior failures (f_ik).
"""

from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

class PerformanceFactorsAnalysis:
    """
    Standard Performance Factors Analysis (PFA) Knowledge Tracing Model.
    logit(p) = beta_k + gamma * successes + rho * failures + student_bias
    """

    def __init__(self):
        self.model = LogisticRegression(max_iter=500, C=1.0)
        self.concept_to_idx: Dict[str, int] = {}
        self.num_concepts: int = 0
        self.is_fitted: bool = False

    def _extract_pfa_features(self, df: pd.DataFrame, is_train: bool = True) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculates cumulative historical successes and failures chronologically per student-concept.
        """
        df_sorted = df.sort_values(by=["student_id", "week"]).copy()

        # Cumulative successes and failures
        df_sorted["prior_success"] = 0
        df_sorted["prior_failure"] = 0

        # Running tally
        student_history: Dict[Tuple[str, str], List[int]] = {}

        prior_s = []
        prior_f = []

        for _, row in df_sorted.iterrows():
            stu = row["student_id"]
            cid = row["concept_id"]
            y = int(row["is_correct"])

            hist = student_history.get((stu, cid), [0, 0])
            prior_s.append(hist[0])
            prior_f.append(hist[1])

            # Update tally for subsequent encounters
            if y == 1:
                hist[0] += 1
            else:
                hist[1] += 1
            student_history[(stu, cid)] = hist

        df_sorted["prior_success"] = prior_s
        df_sorted["prior_failure"] = prior_f

        if is_train:
            unique_concepts = sorted(df_sorted["concept_id"].unique().tolist())
            self.concept_to_idx = {c: i for i, c in enumerate(unique_concepts)}
            self.num_concepts = len(unique_concepts)

        # Feature matrix:
        # [Concept one-hot (num_concepts), prior_successes, prior_failures, difficulty]
        N = len(df_sorted)
        X = np.zeros((N, self.num_concepts + 3))

        for idx, (_, row) in enumerate(df_sorted.iterrows()):
            c_idx = self.concept_to_idx.get(row["concept_id"], None)
            if c_idx is not None:
                X[idx, c_idx] = 1.0
            X[idx, self.num_concepts] = row["prior_success"]
            X[idx, self.num_concepts + 1] = row["prior_failure"]
            X[idx, self.num_concepts + 2] = row.get("difficulty", 2.5)

        y = df_sorted["is_correct"].values
        return X, y, df_sorted.index

    def fit(self, train_df: pd.DataFrame) -> "PerformanceFactorsAnalysis":
        """
        Trains the PFA logistic regression model.
        """
        X_train, y_train, _ = self._extract_pfa_features(train_df, is_train=True)
        self.model.fit(X_train, y_train)
        self.is_fitted = True
        return self

    def predict_proba(self, test_df: pd.DataFrame) -> np.ndarray:
        """
        Predicts probability of correct response for test sequences.
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before calling predict_proba.")

        X_test, _, sorted_indices = self._extract_pfa_features(test_df, is_train=False)
        preds_sorted = self.model.predict_proba(X_test)[:, 1]

        # Map back to original test_df ordering
        results_df = pd.DataFrame({"pred": preds_sorted}, index=sorted_indices)
        realigned = results_df.loc[test_df.index, "pred"].values
        return realigned
