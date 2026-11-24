"""
1,000 Student Cognitive Simulator
Simulates diverse learner interactions using Item Response Theory (IRT 3PL),
Bayesian Knowledge Tracing (BKT) ability updates, response speed dynamics,
slip/guess probabilities, and Ilm Academy's empirical 45% pre-Week 4 dropout pattern.
"""

from typing import List, Dict, Any, Tuple
import os
import numpy as np
import pandas as pd
from concept_graph.concepts_def import CONCEPTS

class StudentSimulator:
    """
    Simulates a cohort of 1,000 students progressing through a rigid linear curriculum.
    """

    WEEK_MODULE_MAP = {
        1: "1_Basics_Primitives",
        2: "2_Control_Flow",
        3: "3_Iteration",       # Week 3 Bottleneck Cliff!
        4: "4_Functions",
        5: "5_Data_Structures",
        6: "6_Advanced_Tools",
        7: "7_OOP_Systems",
        8: "7_OOP_Systems"
    }

    ARCHETYPES = {
        "Struggling Novice": {
            "weight": 0.32,
            "ability_mean": -1.3,
            "ability_std": 0.35,
            "speed_mean": 1.35,      # Slower response time
            "slip_mean": 0.16,       # Higher accidental slips
            "guess_mean": 0.22,      # Guessing when unsure
            "learning_rate": 0.04,   # Slower ability growth
            "frustration_tol": 3     # Drops out after 3-4 consecutive struggles
        },
        "At-Risk Disengaged": {
            "weight": 0.16,
            "ability_mean": -1.8,
            "ability_std": 0.30,
            "speed_mean": 1.50,
            "slip_mean": 0.20,
            "guess_mean": 0.25,
            "learning_rate": 0.02,
            "frustration_tol": 2     # Very fragile persistence
        },
        "Steady Learner": {
            "weight": 0.34,
            "ability_mean": 0.1,
            "ability_std": 0.35,
            "speed_mean": 1.0,
            "slip_mean": 0.08,
            "guess_mean": 0.18,
            "learning_rate": 0.09,
            "frustration_tol": 6
        },
        "Fast-Paced Explorer": {
            "weight": 0.18,
            "ability_mean": 1.25,
            "ability_std": 0.35,
            "speed_mean": 0.75,      # Swift completion
            "slip_mean": 0.04,
            "guess_mean": 0.15,
            "learning_rate": 0.15,
            "frustration_tol": 10
        }
    }

    def __init__(self, num_students: int = 1000, seed: int = 42):
        self.num_students = num_students
        self.seed = seed
        np.random.seed(seed)
        self.students: List[Dict[str, Any]] = []
        self.interactions: List[Dict[str, Any]] = []

    def generate_students(self) -> List[Dict[str, Any]]:
        """
        Creates 1,000 synthetic student profiles with cognitive attributes.
        """
        archetype_names = list(self.ARCHETYPES.keys())
        weights = [self.ARCHETYPES[k]["weight"] for k in archetype_names]

        students = []
        for i in range(1, self.num_students + 1):
            arch_name = np.random.choice(archetype_names, p=weights)
            arch_cfg = self.ARCHETYPES[arch_name]

            init_ability = float(np.random.normal(arch_cfg["ability_mean"], arch_cfg["ability_std"]))
            speed = float(np.clip(np.random.normal(arch_cfg["speed_mean"], 0.15), 0.5, 2.5))
            slip = float(np.clip(np.random.normal(arch_cfg["slip_mean"], 0.02), 0.02, 0.25))
            guess = float(np.clip(np.random.normal(arch_cfg["guess_mean"], 0.03), 0.10, 0.30))
            lr = float(np.clip(np.random.normal(arch_cfg["learning_rate"], 0.02), 0.01, 0.25))
            tol = int(max(1, np.random.normal(arch_cfg["frustration_tol"], 0.8)))

            student = {
                "student_id": f"STU_{i:04d}",
                "archetype": arch_name,
                "initial_ability": round(init_ability, 3),
                "current_ability": round(init_ability, 3),
                "speed_factor": round(speed, 3),
                "slip_rate": round(slip, 3),
                "guess_rate": round(guess, 3),
                "learning_rate": round(lr, 3),
                "frustration_tolerance": tol,
                "consecutive_failures": 0,
                "total_attempts": 0,
                "total_correct": 0,
                "is_dropped_out": False,
                "dropout_week": None,
                "status": "Active"
            }
            students.append(student)

        self.students = students
        return students

    def simulate_curriculum(
        self,
        question_bank: List[Dict[str, Any]]
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Simulates student progression over 8 weeks of instruction.
        Enforces Ilm Academy's empirical 45% pre-Week 4 dropout pattern.
        """
        if not self.students:
            self.generate_students()

        # Organize questions by module
        questions_by_module = {}
        for q in question_bank:
            mod = q["module"]
            if mod not in questions_by_module:
                questions_by_module[mod] = []
            questions_by_module[mod].append(q)

        all_interactions = []
        interaction_counter = 1

        for week in range(1, 9):
            target_module = self.WEEK_MODULE_MAP[week]
            week_questions = questions_by_module.get(target_module, [])

            if not week_questions:
                continue

            for student in self.students:
                # If already dropped out, skip
                if student["is_dropped_out"]:
                    continue

                # Each student attempts a sample of 6 questions per week
                selected_questions = np.random.choice(week_questions, size=min(6, len(week_questions)), replace=False)

                week_failures = 0
                for q in selected_questions:
                    # Item Response Theory (3PL) + Slip & Guess calculation
                    q_diff_scaled = (q["difficulty"] - 3.0) * 0.9 # Difficulty parameter b
                    theta = student["current_ability"]
                    discrimination = 1.35 # a parameter
                    g = student["guess_rate"]
                    s = student["slip_rate"]

                    # Log-odds probability of knowing
                    p_known = 1.0 / (1.0 + np.exp(-discrimination * (theta - q_diff_scaled)))
                    # Probability of correct response
                    prob_correct = g + (1.0 - g - s) * p_known
                    prob_correct = float(np.clip(prob_correct, 0.05, 0.95))

                    is_correct = int(np.random.rand() < prob_correct)

                    # Response time (Speed)
                    base_sec = 25.0 * (q["difficulty"] * 0.4 + 0.6)
                    noise = np.random.normal(0, 0.2)
                    time_taken = float(np.clip(base_sec * student["speed_factor"] * np.exp(0.2 * (q_diff_scaled - theta) + noise), 5.0, 180.0))

                    # Attempts and Hints
                    attempts = 1 if is_correct else int(np.random.choice([2, 3, 4], p=[0.55, 0.30, 0.15]))
                    hints = 0 if is_correct else int(np.random.choice([0, 1, 2, 3], p=[0.35, 0.35, 0.20, 0.10]))

                    pre_theta = student["current_ability"]

                    # Update student ability (BKT learning update)
                    if is_correct:
                        gain = student["learning_rate"] * max(0.05, q_diff_scaled - pre_theta + 0.3)
                        student["current_ability"] = float(np.clip(pre_theta + gain, -3.0, 3.0))
                        student["consecutive_failures"] = max(0, student["consecutive_failures"] - 1)
                    else:
                        student["consecutive_failures"] += 1
                        week_failures += 1

                    student["total_attempts"] += 1
                    student["total_correct"] += is_correct

                    interaction = {
                        "interaction_id": f"INT_{interaction_counter:06d}",
                        "student_id": student["student_id"],
                        "archetype": student["archetype"],
                        "week": week,
                        "module": target_module,
                        "question_id": q["id"],
                        "concept_id": q["concept_id"],
                        "difficulty": q["difficulty"],
                        "blooms_level": q["blooms_level"],
                        "is_correct": is_correct,
                        "time_taken_seconds": round(time_taken, 1),
                        "attempt_count": attempts,
                        "hints_used": hints,
                        "pre_ability": round(pre_theta, 3),
                        "post_ability": round(student["current_ability"], 3),
                        "dropped_out_this_step": 0
                    }
                    all_interactions.append(interaction)
                    interaction_counter += 1

                # --- Dynamic Dropout Determination at end of Week ---
                # Ilm Academy empirical client pattern: 45% cumulative dropout before week 4!
                # Week 1: ~7% drop (onboarding friction)
                # Week 2: ~11% drop (conditionals / abstract logic)
                # Week 3: ~27% drop (loops / iteration / nested structures - the critical bottleneck cliff)
                # Total before Week 4: ~45% (450 students)
                if not student["is_dropped_out"]:
                    dropout_prob = 0.0
                    acc = student["total_correct"] / max(1, student["total_attempts"])

                    if week == 1:
                        if student["archetype"] in ["At-Risk Disengaged", "Struggling Novice"] and acc < 0.45:
                            dropout_prob = 0.30
                        elif student["consecutive_failures"] >= student["frustration_tolerance"]:
                            dropout_prob = 0.20
                    elif week == 2:
                        if student["archetype"] in ["At-Risk Disengaged", "Struggling Novice"] and acc < 0.50:
                            dropout_prob = 0.44
                        elif student["consecutive_failures"] >= student["frustration_tolerance"]:
                            dropout_prob = 0.32
                    elif week == 3: # The heavy Week 3 Cliff!
                        if student["archetype"] == "At-Risk Disengaged":
                            dropout_prob = 0.95
                        elif student["archetype"] == "Struggling Novice":
                            dropout_prob = 0.82
                        elif student["archetype"] == "Steady Learner" and acc < 0.50:
                            dropout_prob = 0.32
                        elif student["consecutive_failures"] >= student["frustration_tolerance"]:
                            dropout_prob = 0.65
                    elif week >= 4:
                        # Post-week 3: mild natural attrition (~3-5%)
                        if student["consecutive_failures"] >= student["frustration_tolerance"] * 1.5:
                            dropout_prob = 0.12
                        else:
                            dropout_prob = 0.02

                    if np.random.rand() < dropout_prob:
                        student["is_dropped_out"] = True
                        student["dropout_week"] = week
                        student["status"] = f"Dropped_Week_{week}"
                        all_interactions[-1]["dropped_out_this_step"] = 1

        # Post-process students final status
        for s in self.students:
            if not s["is_dropped_out"]:
                s["status"] = "Completed"
                s["dropout_week"] = None

        df_students = pd.DataFrame(self.students)
        df_interactions = pd.DataFrame(all_interactions)

        return df_students, df_interactions

    def save_datasets(
        self,
        df_students: pd.DataFrame,
        df_interactions: pd.DataFrame,
        students_csv: str = "learner_data/data/students_profile.csv",
        interactions_csv: str = "learner_data/data/student_interactions.csv"
    ) -> None:
        """Saves generated simulation datasets to CSV."""
        os.makedirs(os.path.dirname(os.path.abspath(students_csv)), exist_ok=True)
        df_students.to_csv(students_csv, index=False)
        df_interactions.to_csv(interactions_csv, index=False)
