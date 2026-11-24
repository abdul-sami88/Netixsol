"""
ASSISTments and EdNet Benchmark Data Loader
Loads and formats educational benchmark datasets for Knowledge Tracing and IRT parameter calibration.
"""

from typing import Dict, Any, List, Optional
import os
import pandas as pd
import numpy as np

class BenchmarkDataLoader:
    """
    Standardizes ASSISTments and EdNet datasets into uniform learner interaction logs.
    """

    @staticmethod
    def generate_synthetic_assistments_benchmark(
        num_records: int = 5000,
        output_csv: str = "learner_data/data/assistments_benchmark.csv"
    ) -> pd.DataFrame:
        """
        Generates realistic ASSISTments 2009-2010 skill builder benchmark format.
        Columns: order_id, user_id, problem_id, skill_name, correct, attempt_count,
                 ms_first_response, hint_count, opportunity.
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_csv)), exist_ok=True)
        np.random.seed(42)

        skills = [
            "variables", "conditionals", "loops", "functions",
            "lists", "dictionaries", "oop_basics", "recursion"
        ]

        user_ids = [f"ASSIST_U_{i:04d}" for i in range(1, 251)]
        records = []

        order_id = 100000
        for uid in user_ids:
            user_skill_ability = {s: np.random.normal(0.65, 0.15) for s in skills}
            for skill in skills:
                num_opps = np.random.randint(2, 6)
                for opp in range(1, num_opps + 1):
                    ability = user_skill_ability[skill]
                    prob_correct = np.clip(ability + (opp * 0.05) - 0.1, 0.15, 0.95)
                    correct = int(np.random.rand() < prob_correct)
                    ms_time = int(np.clip(np.random.lognormal(9.8, 0.5), 3000, 120000))
                    hints = 0 if correct else np.random.choice([0, 1, 2, 3], p=[0.4, 0.3, 0.2, 0.1])
                    attempts = 1 if correct else np.random.choice([2, 3, 4], p=[0.6, 0.3, 0.1])

                    records.append({
                        "order_id": order_id,
                        "user_id": uid,
                        "problem_id": f"PR_{np.random.randint(1000, 9999)}",
                        "skill_name": skill,
                        "correct": correct,
                        "attempt_count": attempts,
                        "ms_first_response": ms_time,
                        "hint_count": hints,
                        "opportunity": opp
                    })
                    order_id += 1

        df = pd.DataFrame(records)
        df.to_csv(output_csv, index=False)
        return df

    @staticmethod
    def load_assistments_data(file_path: str) -> pd.DataFrame:
        """Loads and validates ASSISTments format CSV."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Benchmark file not found: {file_path}")
        df = pd.read_csv(file_path)
        required_cols = {"user_id", "skill_name", "correct", "attempt_count"}
        if not required_cols.issubset(set(df.columns)):
            raise ValueError(f"Missing required ASSISTments columns: {required_cols - set(df.columns)}")
        return df

    @staticmethod
    def compute_benchmark_metrics(df: pd.DataFrame) -> Dict[str, Any]:
        """Calculates global benchmark metrics for IRT/BKT calibration."""
        mean_acc = float(df["correct"].mean())
        mean_time_sec = float(df["ms_first_response"].mean() / 1000.0) if "ms_first_response" in df.columns else 25.0
        mean_attempts = float(df["attempt_count"].mean())
        mean_hints = float(df["hint_count"].mean()) if "hint_count" in df.columns else 0.4

        # Accuracy per skill
        skill_acc = df.groupby("skill_name")["correct"].mean().to_dict()

        return {
            "total_benchmark_records": len(df),
            "benchmark_mean_accuracy": round(mean_acc, 3),
            "benchmark_mean_time_sec": round(mean_time_sec, 2),
            "benchmark_mean_attempts": round(mean_attempts, 2),
            "benchmark_mean_hints": round(mean_hints, 2),
            "skill_accuracy": {k: round(v, 3) for k, v in skill_acc.items()}
        }

