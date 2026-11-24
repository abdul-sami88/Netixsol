"""
Dropout Early-Warning Machine Learning Model (LightGBM / GBDT)
Trains and evaluates gradient boosted decision trees to predict pre-Week 4 student attrition
using early Weeks 1 & 2 signals. Evaluated on PR-AUC and ROC-AUC.
"""

from typing import Dict, Any, List, Tuple
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    precision_recall_curve,
    classification_report,
    confusion_matrix
)
from dropout_early_warning.feature_engineering import DropoutFeatureExtractor

class DropoutPredictor:
    """
    LightGBM / Histogram-based Gradient Boosted Trees for dropout risk forecasting.
    """

    FEATURE_COLS = [
        "early_accuracy",
        "max_consecutive_failures",
        "avg_response_time_sec",
        "avg_hints_used",
        "avg_attempts_per_question",
        "accuracy_trend",
        "initial_ability",
        "speed_factor",
        "slip_rate"
    ]

    def __init__(self, test_size: float = 0.20, random_state: int = 42):
        self.test_size = test_size
        self.random_state = random_state
        self.model = HistGradientBoostingClassifier(
            max_iter=100,
            learning_rate=0.08,
            max_leaf_nodes=15,
            min_samples_leaf=10,
            random_state=random_state
        )
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        self.test_students = None
        self.metrics: Dict[str, Any] = {}

    def prepare_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Extracts features and splits into train and test sets."""
        extractor = DropoutFeatureExtractor()
        df = extractor.extract_features()

        X = df[self.FEATURE_COLS]
        y = df["is_pre_w4_dropout"]

        X_tr, X_te, y_tr, y_te, idx_tr, idx_te = train_test_split(
            X, y, df["student_id"], test_size=self.test_size, random_state=self.random_state, stratify=y
        )

        self.X_train = X_tr
        self.X_test = X_te
        self.y_train = y_tr
        self.y_test = y_te
        self.test_students = idx_te
        return X_tr, X_te

    def train_and_evaluate(self) -> Dict[str, Any]:
        """Trains model and computes PR-AUC, ROC-AUC, Precision, Recall, and F1."""
        if self.X_train is None:
            self.prepare_data()

        self.model.fit(self.X_train, self.y_train)

        y_prob = self.model.predict_proba(self.X_test)[:, 1]
        y_pred = (y_prob >= 0.50).astype(int)

        roc_auc = float(roc_auc_score(self.y_test, y_prob))
        pr_auc = float(average_precision_score(self.y_test, y_prob))
        base_rate = float(self.y_test.mean())

        cls_rep = classification_report(self.y_test, y_pred, output_dict=True)
        cm = confusion_matrix(self.y_test, y_pred).tolist()

        self.metrics = {
            "ROC_AUC": round(roc_auc, 4),
            "PR_AUC": round(pr_auc, 4),
            "Baseline_Positive_Rate": round(base_rate, 4),
            "Precision_At_Risk": round(cls_rep["1"]["precision"], 4),
            "Recall_At_Risk": round(cls_rep["1"]["recall"], 4),
            "F1_Score": round(cls_rep["1"]["f1-score"], 4),
            "Accuracy": round(cls_rep["accuracy"], 4),
            "Confusion_Matrix": cm,
            "Test_Set_Size": len(self.y_test)
        }

        return self.metrics

    def predict_risk_scores(self, X: pd.DataFrame) -> np.ndarray:
        """Returns dropout probability scores."""
        return self.model.predict_proba(X[self.FEATURE_COLS])[:, 1]

    def plot_pr_and_roc_curves(self, output_path: str = "figures/dropout_pr_curve.png") -> str:
        """Generates Precision-Recall and ROC curve plots."""
        if not self.metrics:
            self.train_and_evaluate()

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        y_prob = self.model.predict_proba(self.X_test)[:, 1]

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5), dpi=150)

        # 1. Precision-Recall Curve
        precision, recall, _ = precision_recall_curve(self.y_test, y_prob)
        ax1.plot(recall, precision, color="#0284c7", lw=2.5,
                 label=f"LightGBM PR Curve (PR-AUC = {self.metrics['PR_AUC']:.3f})")
        ax1.axhline(self.metrics["Baseline_Positive_Rate"], color="#94a3b8", linestyle="--",
                    label=f"Baseline Prior ({self.metrics['Baseline_Positive_Rate']*100:.1f}%)")
        ax1.set_title("Precision-Recall Curve (Early Dropout Warning)", fontsize=11, weight="bold")
        ax1.set_xlabel("Recall (Coverage of Dropping Students)", fontsize=10)
        ax1.set_ylabel("Precision (Accuracy of Risk Alarm)", fontsize=10)
        ax1.set_ylim(0, 1.05)
        ax1.grid(True, linestyle="--", alpha=0.5)
        ax1.legend(loc="lower left", frameon=True)

        # 2. Risk Distribution by True Label
        test_df = pd.DataFrame({"true_label": self.y_test, "risk_score": y_prob})
        retained = test_df[test_df["true_label"] == 0]["risk_score"]
        dropped = test_df[test_df["true_label"] == 1]["risk_score"]

        ax2.hist(retained, bins=15, alpha=0.6, color="#10b981", label="Retained Students (True 0)", density=True)
        ax2.hist(dropped, bins=15, alpha=0.6, color="#ef4444", label="Pre-W4 Dropouts (True 1)", density=True)
        ax2.axvline(0.50, color="#1e293b", linestyle=":", lw=2, label="Classification Cutoff (0.50)")
        ax2.set_title("Predicted Risk Score Distribution (Bimodal Separation)", fontsize=11, weight="bold")
        ax2.set_xlabel("Predicted Dropout Probability", fontsize=10)
        ax2.set_ylabel("Density", fontsize=10)
        ax2.grid(True, linestyle="--", alpha=0.5)
        ax2.legend(loc="upper center", frameon=True)

        plt.suptitle("Ilm Academy: Week 1 & 2 Early Dropout Risk Model Diagnostics", fontsize=13, weight="bold", y=1.02)
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
        return output_path
