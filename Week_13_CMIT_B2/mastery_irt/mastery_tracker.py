"""
Concept Mastery Tracker
Calculates latent mastery scores per concept across all students,
and profiles key diagnostic personas (e.g., Ali: loop-strong/function-weak; Sara: fast/careless).
"""

from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd

class MasteryTracker:
    """
    Computes and manages student mastery scores across concepts using interaction traces.
    """

    MASTERY_THRESHOLD = 0.75

    def __init__(self, interactions_df: Optional[pd.DataFrame] = None):
        self.interactions_df = interactions_df
        # student_id -> concept_id -> mastery_score (0.0 to 1.0)
        self.mastery_matrix: Dict[str, Dict[str, float]] = {}

    def compute_all_masteries(self, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Calculates mastery for every (student, concept) pair using recency-weighted BKT/accuracy.
        """
        if df is None:
            df = self.interactions_df
        if df is None:
            raise ValueError("No interactions dataframe provided.")

        records = []
        for (stu_id, cid), group in df.groupby(["student_id", "concept_id"]):
            group_sorted = group.sort_values(by="week")
            attempts = len(group_sorted)
            corrects = group_sorted["is_correct"].sum()

            # Recency-weighted moving average
            weights = np.exp(np.linspace(-0.8, 0.0, attempts))
            weights /= weights.sum()
            weighted_acc = float(np.sum(group_sorted["is_correct"].values * weights))

            # Bayesian smoothing towards 0.5 prior
            prior_weight = max(1, 4 - attempts)
            smoothed_mastery = (weighted_acc * attempts + 0.5 * prior_weight) / (attempts + prior_weight)
            smoothed_mastery = float(np.clip(smoothed_mastery, 0.05, 0.98))

            if stu_id not in self.mastery_matrix:
                self.mastery_matrix[stu_id] = {}
            self.mastery_matrix[stu_id][cid] = round(smoothed_mastery, 3)

            records.append({
                "student_id": stu_id,
                "concept_id": cid,
                "module": group_sorted["module"].iloc[0],
                "attempts": attempts,
                "corrects": corrects,
                "mastery_score": round(smoothed_mastery, 3),
                "is_mastered": smoothed_mastery >= self.MASTERY_THRESHOLD
            })

        return pd.DataFrame(records)

    def get_student_mastery_profile(self, student_id: str) -> Dict[str, Any]:
        """
        Retrieves a student's full concept mastery map, mastered list, and struggle list.
        """
        if student_id not in self.mastery_matrix:
            if self.interactions_df is not None:
                self.compute_all_masteries()

        student_scores = self.mastery_matrix.get(student_id, {})
        mastered = [c for c, m in student_scores.items() if m >= self.MASTERY_THRESHOLD]
        struggling = [c for c, m in student_scores.items() if m < 0.45]
        in_progress = [c for c, m in student_scores.items() if 0.45 <= m < self.MASTERY_THRESHOLD]

        return {
            "student_id": student_id,
            "total_concepts_attempted": len(student_scores),
            "mastered_concepts": mastered,
            "struggling_concepts": struggling,
            "in_progress_concepts": in_progress,
            "mastery_scores": student_scores,
            "overall_mastery_rate": round(len(mastered) / max(1, len(student_scores)), 3)
        }

    @staticmethod
    def construct_ali_profile() -> Dict[str, Any]:
        """
        Constructs Ali's diagnostic persona:
        Scenario: Strong in loops, weak in functions.
        """
        ali_scores = {
            # Primitives & Control Flow (Mastered)
            "variables": 0.88, "integers_floats": 0.90, "strings": 0.85, "booleans": 0.82,
            "comparison_operators": 0.86, "if_else": 0.80, "elif_chains": 0.78,
            # Loops (Very Strong!)
            "while_loops": 0.88, "range_function": 0.92, "for_loops": 0.85,
            "break_continue": 0.84, "nested_loops": 0.80, "for_else": 0.76,
            # Functions (Weak / Struggling Bottleneck)
            "functions_def": 0.42, "arguments_parameters": 0.35, "return_statement": 0.30,
            "variable_scope": 0.26, "args_kwargs": 0.28, "lambda_functions": 0.22,
            # Data Structures (Partially explored)
            "lists": 0.70, "list_slicing": 0.65, "tuples": 0.60
        }
        return {
            "student_id": "STU_ALI",
            "name": "Ali",
            "archetype": "Loop Specialist / Function Challenged",
            "description": "Strong in iteration and nested loops, but struggles with function scope and return vs print semantics.",
            "speed_factor": 1.05,
            "slip_rate": 0.08,
            "guess_rate": 0.18,
            "mastery_scores": ali_scores
        }

    @staticmethod
    def construct_sara_profile() -> Dict[str, Any]:
        """
        Constructs Sara's diagnostic persona:
        Scenario: Fast but careless (high ability, rapid response times, high slip rate).
        """
        sara_scores = {
            "variables": 0.78, "integers_floats": 0.76, "strings": 0.72, "booleans": 0.75,
            "comparison_operators": 0.78, "if_else": 0.74, "elif_chains": 0.70,
            "while_loops": 0.75, "range_function": 0.68, "for_loops": 0.72,
            "break_continue": 0.66, "nested_loops": 0.64,
            "functions_def": 0.74, "arguments_parameters": 0.70, "return_statement": 0.65,
            "variable_scope": 0.60,
            "lists": 0.72, "list_slicing": 0.68, "dictionaries": 0.70
        }
        return {
            "student_id": "STU_SARA",
            "name": "Sara",
            "archetype": "Fast but Careless",
            "description": "High cognitive ability and rapid solving speed, but frequently slips on edge cases, off-by-one indices, and mutable types.",
            "speed_factor": 0.65,  # Solves in ~65% of standard time
            "slip_rate": 0.22,    # Unusually high slip rate!
            "guess_rate": 0.12,
            "mastery_scores": sara_scores
        }
