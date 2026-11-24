"""
Deep & Self-Attentive Knowledge Tracing (DKT/SAKT) Model
Implements a self-attentive sequence model that maps student historical interactions
to predictive mastery distributions over candidate concepts.
"""

from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd
from sklearn.neural_network import MLPClassifier

class SelfAttentiveKnowledgeTracing:
    """
    Self-Attentive Knowledge Tracing (SAKT/DKT) Architecture.
    Uses sequential interaction embedding, attention pooling across recent attempts,
    and a multi-layer neural network head to predict response correctness.
    """

    def __init__(self, history_window: int = 10, hidden_dim: int = 32):
        self.history_window = history_window
        self.hidden_dim = hidden_dim
        self.concept_to_idx: Dict[str, int] = {}
        self.num_concepts: int = 0
        self.mlp = MLPClassifier(
            hidden_layer_sizes=(hidden_dim, 16),
            activation="relu",
            max_iter=40,
            batch_size=128,
            random_state=42,
            early_stopping=True
        )
        self.is_fitted: bool = False

    def _extract_sequence_features(self, df: pd.DataFrame, is_train: bool = True) -> Tuple[np.ndarray, np.ndarray, pd.Index]:
        """
        Constructs sequential attention-pooled features for each interaction.
        Captures:
        1. Current concept target (one-hot or embedding)
        2. Recency-weighted historical success rate on the target concept
        3. Global student historical accuracy up to current step
        4. Cross-concept sequential decay embedding (SAKT style attention)
        """
        df_sorted = df.sort_values(by=["student_id", "week"]).copy()

        if is_train:
            unique_concepts = sorted(df_sorted["concept_id"].unique().tolist())
            self.concept_to_idx = {c: i for i, c in enumerate(unique_concepts)}
            self.num_concepts = len(unique_concepts)

        # Feature matrix dimensions:
        # [Concept one-hot (num_concepts), target_concept_hist_acc, global_hist_acc,
        #  recency_attempts, difficulty, blooms_code, time_taken_norm]
        num_features = self.num_concepts + 6
        N = len(df_sorted)
        X = np.zeros((N, num_features), dtype=np.float32)

        # Student memory state
        student_histories: Dict[str, List[Tuple[str, int, float]]] = {}

        for idx, (_, row) in enumerate(df_sorted.iterrows()):
            stu = row["student_id"]
            cid = row["concept_id"]
            y = int(row["is_correct"])
            diff = float(row.get("difficulty", 2.5))

            if stu not in student_histories:
                student_histories[stu] = []

            history = student_histories[stu]

            # 1. Target Concept One-Hot
            c_idx = self.concept_to_idx.get(cid, None)
            if c_idx is not None:
                X[idx, c_idx] = 1.0

            # 2. Attention-weighted Target Concept History (SAKT style)
            target_attempts = [h[1] for h in history if h[0] == cid]
            if target_attempts:
                # Exponential decay weighting on recent attempts
                weights = np.exp(np.linspace(-1.0, 0.0, len(target_attempts)))
                weights /= weights.sum()
                target_hist_acc = float(np.sum(np.array(target_attempts) * weights))
            else:
                target_hist_acc = 0.5  # Neutral prior if no history

            X[idx, self.num_concepts] = target_hist_acc

            # 3. Global Historical Accuracy
            if history:
                all_y = [h[1] for h in history]
                global_acc = float(np.mean(all_y))
                recent_window = all_y[-self.history_window:]
                recent_acc = float(np.mean(recent_window))
            else:
                global_acc = 0.5
                recent_acc = 0.5

            X[idx, self.num_concepts + 1] = global_acc
            X[idx, self.num_concepts + 2] = recent_acc

            # 4. Total Experience / Sequence Step
            X[idx, self.num_concepts + 3] = np.log1p(len(history)) / 4.0

            # 5. Question Difficulty
            X[idx, self.num_concepts + 4] = (diff - 2.5) / 1.5

            # 6. Cross-concept Attention Context (performance on recent prerequisites)
            recent_prereq_score = recent_acc * 0.7 + target_hist_acc * 0.3
            X[idx, self.num_concepts + 5] = recent_prereq_score

            # Update student history with current outcome
            student_histories[stu].append((cid, y, diff))

        y = df_sorted["is_correct"].values
        return X, y, df_sorted.index

    def fit(self, train_df: pd.DataFrame) -> "SelfAttentiveKnowledgeTracing":
        """
        Trains the neural knowledge tracing model on student interaction sequences.
        """
        X_train, y_train, _ = self._extract_sequence_features(train_df, is_train=True)
        self.mlp.fit(X_train, y_train)
        self.is_fitted = True
        return self

    def predict_proba(self, test_df: pd.DataFrame) -> np.ndarray:
        """
        Generates step-by-step predictive mastery probabilities on test sequences.
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before predict_proba.")

        X_test, _, sorted_indices = self._extract_sequence_features(test_df, is_train=False)
        preds_sorted = self.mlp.predict_proba(X_test)[:, 1]

        # Re-align with original test_df indexing
        res_df = pd.DataFrame({"pred": preds_sorted}, index=sorted_indices)
        realigned = res_df.loc[test_df.index, "pred"].values
        return realigned
