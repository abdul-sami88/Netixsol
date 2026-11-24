"""
Knowledge Tracing Model Comparator
Conducts student-level train/test split benchmarking across Baseline, BKT, PFA, and DKT/SAKT
on ROC-AUC, Accuracy, and RMSE.
"""

from typing import Dict, Any, List, Tuple
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import roc_auc_score, accuracy_score, mean_squared_error

from knowledge_tracing.baseline_model import BaselineKTModel
from knowledge_tracing.bkt_model import BayesianKnowledgeTracing
from knowledge_tracing.pfa_model import PerformanceFactorsAnalysis
from knowledge_tracing.dkt_sakt_model import SelfAttentiveKnowledgeTracing

class KTModelComparator:
    """
    Evaluates and compares Knowledge Tracing models under a strict student-level split.
    """

    def __init__(
        self,
        interactions_path: str = "learner_data/data/student_interactions.csv",
        test_size: float = 0.20,
        random_state: int = 42
    ):
        self.interactions_path = interactions_path
        self.test_size = test_size
        self.random_state = random_state
        self.train_df: pd.DataFrame = None
        self.test_df: pd.DataFrame = None
        self.results_df: pd.DataFrame = None

    def prepare_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Performs a strict student-level train/test split to prevent data leakage.
        """
        df = pd.read_csv(self.interactions_path)
        unique_students = df["student_id"].unique()
        np.random.seed(self.random_state)
        shuffled_students = np.random.permutation(unique_students)

        split_idx = int(len(shuffled_students) * (1.0 - self.test_size))
        train_students = set(shuffled_students[:split_idx])
        test_students = set(shuffled_students[split_idx:])

        self.train_df = df[df["student_id"].isin(train_students)].copy()
        self.test_df = df[df["student_id"].isin(test_students)].copy()

        print(f"Data Split: {len(train_students)} train students ({len(self.train_df):,} interactions), "
              f"{len(test_students)} test students ({len(self.test_df):,} interactions).")

        return self.train_df, self.test_df

    def evaluate_model(
        self,
        name: str,
        y_true: np.ndarray,
        y_pred: np.ndarray
    ) -> Dict[str, Any]:
        """
        Computes ROC-AUC, Accuracy (at threshold 0.5), and RMSE.
        """
        auc = float(roc_auc_score(y_true, y_pred))
        acc = float(accuracy_score(y_true, (y_pred >= 0.5).astype(int)))
        rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))

        return {
            "Model": name,
            "ROC_AUC": round(auc, 4),
            "Accuracy": round(acc, 4),
            "RMSE": round(rmse, 4)
        }

    def run_benchmark(self) -> pd.DataFrame:
        """
        Trains and benchmarks all 4 Knowledge Tracing models.
        """
        if self.train_df is None:
            self.prepare_data()

        y_test = self.test_df["is_correct"].values
        metrics_list = []

        # 1. Baseline Model
        print("\n[1/4] Training Baseline Model...")
        baseline = BaselineKTModel().fit(self.train_df)
        p_base = baseline.predict_proba(self.test_df)
        m_base = self.evaluate_model("Baseline (Empirical Bayes)", y_test, p_base)
        metrics_list.append(m_base)

        # 2. Bayesian Knowledge Tracing (BKT)
        print("[2/4] Training BKT (Bayesian Knowledge Tracing)...")
        bkt = BayesianKnowledgeTracing().fit(self.train_df)
        p_bkt = bkt.predict_proba(self.test_df)
        m_bkt = self.evaluate_model("BKT (Bayesian Knowledge Tracing)", y_test, p_bkt)
        metrics_list.append(m_bkt)

        # 3. Performance Factors Analysis (PFA)
        print("[3/4] Training PFA (Performance Factors Analysis)...")
        pfa = PerformanceFactorsAnalysis().fit(self.train_df)
        p_pfa = pfa.predict_proba(self.test_df)
        m_pfa = self.evaluate_model("PFA (Performance Factors Analysis)", y_test, p_pfa)
        metrics_list.append(m_pfa)

        # 4. Deep / Self-Attentive Knowledge Tracing (DKT/SAKT)
        print("[4/4] Training DKT/SAKT (Self-Attentive Neural KT)...")
        dkt = SelfAttentiveKnowledgeTracing().fit(self.train_df)
        p_dkt = dkt.predict_proba(self.test_df)
        m_dkt = self.evaluate_model("DKT/SAKT (Self-Attentive Neural KT)", y_test, p_dkt)
        metrics_list.append(m_dkt)

        self.results_df = pd.DataFrame(metrics_list)
        return self.results_df

    def plot_comparison(self, output_path: str = "figures/knowledge_tracing_model_comparison.png") -> str:
        """
        Generates comparison chart across models on AUC, Accuracy, and RMSE.
        """
        if self.results_df is None:
            self.run_benchmark()

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        fig, axes = plt.subplots(1, 3, figsize=(15, 5), dpi=150)
        colors = ["#94a3b8", "#3b82f6", "#8b5cf6", "#10b981"]

        # 1. ROC-AUC
        axes[0].bar(self.results_df["Model"], self.results_df["ROC_AUC"], color=colors, width=0.55)
        axes[0].set_title("ROC-AUC (Higher is Better)", fontsize=11, weight="bold")
        axes[0].set_ylim(0.5, 0.90)
        axes[0].grid(axis="y", linestyle="--", alpha=0.6)
        for idx, v in enumerate(self.results_df["ROC_AUC"]):
            axes[0].text(idx, v + 0.01, f"{v:.3f}", ha="center", weight="bold", fontsize=9)

        # 2. Accuracy
        axes[1].bar(self.results_df["Model"], self.results_df["Accuracy"] * 100, color=colors, width=0.55)
        axes[1].set_title("Accuracy % (Higher is Better)", fontsize=11, weight="bold")
        axes[1].set_ylim(50, 85)
        axes[1].grid(axis="y", linestyle="--", alpha=0.6)
        for idx, v in enumerate(self.results_df["Accuracy"] * 100):
            axes[1].text(idx, v + 0.8, f"{v:.1f}%", ha="center", weight="bold", fontsize=9)

        # 3. RMSE
        axes[2].bar(self.results_df["Model"], self.results_df["RMSE"], color=colors, width=0.55)
        axes[2].set_title("RMSE (Lower is Better)", fontsize=11, weight="bold")
        axes[2].set_ylim(0.35, 0.55)
        axes[2].grid(axis="y", linestyle="--", alpha=0.6)
        for idx, v in enumerate(self.results_df["RMSE"]):
            axes[2].text(idx, v + 0.005, f"{v:.3f}", ha="center", weight="bold", fontsize=9)

        for ax in axes:
            ax.set_xticks(range(len(self.results_df)))
            ax.set_xticklabels(["Baseline", "BKT", "PFA", "DKT/SAKT"], rotation=0, fontsize=9.5)

        plt.suptitle("Knowledge Tracing Benchmark Comparison (Student-Level Split, N=200 Test Students)", fontsize=13, weight="bold", y=1.02)
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
        return output_path
