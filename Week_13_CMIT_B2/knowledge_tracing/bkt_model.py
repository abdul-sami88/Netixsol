"""
Bayesian Knowledge Tracing (BKT) Engine
Standard 4-parameter HMM (L0, T, G, S) per concept with sequence log-likelihood estimation
and sequential belief state updating.
"""

from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd
from scipy.optimize import minimize

class BayesianKnowledgeTracing:
    """
    Standard Bayesian Knowledge Tracing model.
    Maintains latent belief state P(L_t) for each student-concept pair.
    """

    DEFAULT_PARAMS = {
        "L0": 0.35,  # Initial prior knowledge
        "T": 0.12,   # Transition / learning rate
        "G": 0.20,   # Guess rate
        "S": 0.10    # Slip rate
    }

    def __init__(self):
        # concept_id -> {L0, T, G, S}
        self.params: Dict[str, Dict[str, float]] = {}

    def _sequence_log_likelihood(
        self,
        observations: List[int],
        L0: float,
        T: float,
        G: float,
        S: float
    ) -> float:
        """
        Computes negative log-likelihood of an observed binary sequence under BKT parameters.
        """
        p_L = L0
        nll = 0.0
        eps = 1e-6

        for y in observations:
            # P(Y=1 | L_t)
            p_correct = p_L * (1.0 - S) + (1.0 - p_L) * G
            p_correct = np.clip(p_correct, eps, 1.0 - eps)

            if y == 1:
                nll -= np.log(p_correct)
                # Posterior update
                p_L_given_y = (p_L * (1.0 - S)) / p_correct
            else:
                nll -= np.log(1.0 - p_correct)
                p_L_given_y = (p_L * S) / (1.0 - p_correct)

            # Transition step
            p_L = p_L_given_y + (1.0 - p_L_given_y) * T
            p_L = np.clip(p_L, 0.0, 1.0)

        return nll

    def fit_concept(self, sequences: List[List[int]], default_L0: float = 0.35) -> Dict[str, float]:
        """
        Estimates (L0, T, G, S) for a single concept using bounded optimization.
        """
        if not sequences or sum(len(seq) for seq in sequences) < 5:
            return dict(self.DEFAULT_PARAMS)

        def objective(theta):
            L0, T, G, S = theta
            total_nll = 0.0
            for seq in sequences:
                total_nll += self._sequence_log_likelihood(seq, L0, T, G, S)
            return total_nll

        # Parameter bounds: L0 in [0.05, 0.85], T in [0.02, 0.35], G in [0.05, 0.30], S in [0.02, 0.25]
        bounds = [(0.05, 0.85), (0.02, 0.35), (0.05, 0.30), (0.02, 0.25)]
        init_guess = [default_L0, 0.10, 0.20, 0.10]

        try:
            res = minimize(objective, init_guess, bounds=bounds, method="L-BFGS-B", options={"maxiter": 15})
            if res.x is not None and not np.isnan(res.x).any():
                return {
                    "L0": float(res.x[0]),
                    "T": float(res.x[1]),
                    "G": float(res.x[2]),
                    "S": float(res.x[3])
                }
        except Exception:
            pass

        return dict(self.DEFAULT_PARAMS)

    def fit(self, train_df: pd.DataFrame) -> "BayesianKnowledgeTracing":
        """
        Fits BKT parameters across all concepts in the training dataset.
        """
        self.params = {}
        # Group observations by concept and student
        concepts = train_df["concept_id"].unique()

        for cid in concepts:
            c_df = train_df[train_df["concept_id"] == cid]
            # Empirical accuracy as prior guidance
            emp_acc = float(c_df["is_correct"].mean())
            init_L0 = np.clip(emp_acc * 0.6, 0.1, 0.8)

            # Collect sequences per student
            sequences = []
            for _, stu_group in c_df.groupby("student_id"):
                sequences.append(stu_group["is_correct"].tolist())

            params = self.fit_concept(sequences, default_L0=init_L0)
            self.params[cid] = params

        return self

    def predict_proba(self, test_df: pd.DataFrame) -> np.ndarray:
        """
        Performs forward sequential prediction over test student sequences.
        Simulates live tracking: predicts next outcome before updating state with observation.
        """
        # Track belief state for each (student_id, concept_id)
        student_states: Dict[Tuple[str, str], float] = {}
        preds = []

        # Ensure ordered chronologically
        df_sorted = test_df.sort_values(by=["student_id", "week"]).copy()

        for _, row in df_sorted.iterrows():
            stu_id = row["student_id"]
            cid = row["concept_id"]
            obs = int(row["is_correct"])

            # Retrieve concept parameters
            p_dict = self.params.get(cid, self.DEFAULT_PARAMS)
            L0, T, G, S = p_dict["L0"], p_dict["T"], p_dict["G"], p_dict["S"]

            # Current knowledge state
            key = (stu_id, cid)
            p_L = student_states.get(key, L0)

            # Predict P(Y_t = 1)
            p_correct = p_L * (1.0 - S) + (1.0 - p_L) * G
            p_correct = float(np.clip(p_correct, 0.01, 0.99))
            preds.append(p_correct)

            # Posterior update with actual observation
            if obs == 1:
                p_L_given_y = (p_L * (1.0 - S)) / p_correct
            else:
                p_L_given_y = (p_L * S) / (1.0 - p_correct)

            # Next state after learning opportunity
            p_L_next = p_L_given_y + (1.0 - p_L_given_y) * T
            student_states[key] = float(np.clip(p_L_next, 0.0, 1.0))

        # Re-align with original test_df index
        df_sorted["pred_bkt"] = preds
        reindexed_preds = df_sorted.loc[test_df.index, "pred_bkt"].values
        return reindexed_preds
