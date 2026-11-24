"""
A/B Test Simulator for Curriculum Impact Evaluation
Simulates 2,000 students in a randomized controlled trial:
- 1,000 Control Students: Fixed Curriculum (One-size-fits-all, no adaptive engine, manual grading delays)
- 1,000 Treatment Students: Adaptive Platform (ZPD 60-80%, Thompson bandit, Socratic tutor, instant code feedback)
Tracks: Pre/Post test scores, normalized learning gain, time to mastery, dropout survival, and teacher hours.
"""

import numpy as np
import json
import os
from typing import List, Dict, Any

def simulate_ab_test(n_per_group: int = 1000, random_seed: int = 42) -> List[Dict[str, Any]]:
    np.random.seed(random_seed)
    students = []

    for i in range(n_per_group * 2):
        is_treatment = (i >= n_per_group)
        group_name = "Adaptive Platform (Treatment)" if is_treatment else "Fixed Curriculum (Control)"
        group_code = "TREATMENT" if is_treatment else "CONTROL"
        stu_id = f"STU-{2001 + i}"

        # Baseline student ability (Normal distribution truncated between 0.15 and 0.65)
        ability = np.clip(np.random.normal(0.38, 0.12), 0.15, 0.75)
        pre_test = round(float(np.clip(ability + np.random.normal(0, 0.05), 0.10, 0.70)), 3)

        if not is_treatment:
            # Control Group (Fixed Curriculum):
            # One-size-fits-all causes students with ability < 0.40 to get overwhelmed (C17 Recursion bottleneck)
            # High dropout rate (44.6% pre-week 4), slower time to mastery, lower post-test
            struggle_factor = max(0.0, 0.45 - ability)
            dropout_prob = 0.446 + (struggle_factor * 0.6)
            dropped_pre_w4 = bool(np.random.rand() < min(0.75, dropout_prob))
            dropped_w8 = dropped_pre_w4 or bool(np.random.rand() < 0.15)

            if dropped_pre_w4:
                post_test = round(float(np.clip(pre_test + np.random.normal(0.05, 0.03), 0.10, 0.50)), 3)
                time_to_mastery = round(float(np.random.normal(12.0, 2.5)), 1)
                gain = round(float(max(0.0, (post_test - pre_test) / (1.0 - pre_test))), 3)
            else:
                learning_bump = np.random.normal(0.20, 0.08)
                post_test = round(float(np.clip(pre_test + learning_bump, 0.25, 0.85)), 3)
                time_to_mastery = round(float(np.random.normal(32.4, 6.2)), 1)
                gain = round(float(max(0.0, (post_test - pre_test) / (1.0 - pre_test))), 3)

            # Teacher hours spent per student in manual grading and repetitive office hours
            teacher_hours = round(float(np.random.normal(2.8, 0.5)), 2)

        else:
            # Treatment Group (Adaptive Platform):
            # ZPD (60-80% success), Thompson bandit, 24/7 Socratic tutor, instant autograding feedback
            # Dramatically reduced dropout (18.4%), accelerated time to mastery (18.2h), higher gain (0.63)
            struggle_factor = max(0.0, 0.45 - ability)
            dropout_prob = 0.184 + (struggle_factor * 0.15)
            dropped_pre_w4 = bool(np.random.rand() < min(0.35, dropout_prob))
            dropped_w8 = dropped_pre_w4 or bool(np.random.rand() < 0.08)

            if dropped_pre_w4:
                post_test = round(float(np.clip(pre_test + np.random.normal(0.12, 0.04), 0.15, 0.60)), 3)
                time_to_mastery = round(float(np.random.normal(10.0, 2.0)), 1)
                gain = round(float(max(0.0, (post_test - pre_test) / (1.0 - pre_test))), 3)
            else:
                learning_bump = np.random.normal(0.40, 0.09)
                post_test = round(float(np.clip(pre_test + learning_bump, 0.55, 0.98)), 3)
                time_to_mastery = round(float(np.random.normal(18.2, 3.8)), 1)
                gain = round(float(max(0.0, (post_test - pre_test) / (1.0 - pre_test))), 3)

            # Teacher hours spent: 91% reduction because autograder handles regular grading
            teacher_hours = round(float(np.random.normal(0.24, 0.08)), 2)

        students.append({
            "student_id": stu_id,
            "group": group_code,
            "group_name": group_name,
            "baseline_ability": round(float(ability), 3),
            "pre_test_score": pre_test,
            "post_test_score": post_test,
            "normalized_learning_gain": gain,
            "time_to_mastery_hours": time_to_mastery,
            "dropped_out_pre_week4": dropped_pre_w4,
            "dropped_out_week8": dropped_w8,
            "teacher_hours_used": teacher_hours
        })

    return students
