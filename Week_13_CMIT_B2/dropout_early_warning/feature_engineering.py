"""
Feature Engineering for Early-Warning Dropout Prediction
Extracts early diagnostic behavioral and cognitive signals from Weeks 1 & 2.
"""

from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd

class DropoutFeatureExtractor:
    """
    Transforms raw early interaction logs into feature vectors for predictive churn modeling.
    """

    def __init__(
        self,
        interactions_path: str = "learner_data/data/student_interactions.csv",
        students_path: str = "learner_data/data/students_profile.csv"
    ):
        self.interactions_path = interactions_path
        self.students_path = students_path

    def extract_features(self) -> pd.DataFrame:
        """
        Extracts predictive features strictly using Weeks 1 & 2 interactions.
        Target: is_pre_w4_dropout (1 if dropped out in week 1, 2, or 3; else 0).
        """
        df_int = pd.read_csv(self.interactions_path)
        df_stu = pd.read_csv(self.students_path)

        # Target label: dropped out before week 4
        # dropout_week in [1, 2, 3] -> 1, else 0
        df_stu["is_pre_w4_dropout"] = df_stu["dropout_week"].apply(lambda w: 1 if pd.notnull(w) and int(w) <= 3 else 0)

        # Filter interactions to early period only (Weeks 1 & 2)
        early_int = df_int[df_int["week"].isin([1, 2])].copy()

        feature_records = []
        for stu_id, group in early_int.groupby("student_id"):
            group_sorted = group.sort_values(by=["week", "interaction_id"])

            total_early_attempts = len(group_sorted)
            w1_w2_acc = float(group_sorted["is_correct"].mean())
            avg_time = float(group_sorted["time_taken_seconds"].mean())
            avg_hints = float(group_sorted["hints_used"].mean())
            avg_retries = float(group_sorted["attempt_count"].mean())

            # Consecutive failures in early weeks (frustration accumulator)
            outcomes = group_sorted["is_correct"].values
            max_consec_fails = 0
            cur_fails = 0
            for y in outcomes:
                if y == 0:
                    cur_fails += 1
                    if cur_fails > max_consec_fails:
                        max_consec_fails = cur_fails
                else:
                    cur_fails = 0

            # Week 1 vs Week 2 trajectory trend
            w1_group = group_sorted[group_sorted["week"] == 1]
            w2_group = group_sorted[group_sorted["week"] == 2]
            w1_acc = float(w1_group["is_correct"].mean()) if len(w1_group) > 0 else w1_w2_acc
            w2_acc = float(w2_group["is_correct"].mean()) if len(w2_group) > 0 else w1_acc
            acc_trend = round(w2_acc - w1_acc, 3)

            feature_records.append({
                "student_id": stu_id,
                "early_accuracy": round(w1_w2_acc, 3),
                "max_consecutive_failures": max_consec_fails,
                "avg_response_time_sec": round(avg_time, 1),
                "avg_hints_used": round(avg_hints, 2),
                "avg_attempts_per_question": round(avg_retries, 2),
                "accuracy_trend": acc_trend,
                "total_early_interactions": total_early_attempts
            })

        df_features = pd.DataFrame(feature_records)

        # Merge with student profiles (archetype, initial attributes, target label)
        merged = pd.merge(
            df_features,
            df_stu[["student_id", "archetype", "initial_ability", "speed_factor", "slip_rate", "is_pre_w4_dropout"]],
            on="student_id",
            how="inner"
        )

        return merged
