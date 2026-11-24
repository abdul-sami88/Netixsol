"""
Thompson Sampling Multi-Armed Bandit
Balances exploration (uncertainty in concept mastery) with exploitation
(reinforcing struggling concepts within ZPD).
"""

from typing import Dict, Any, List, Optional
import numpy as np

class ThompsonSamplingBandit:
    """
    Beta-Bernoulli Thompson Sampling engine for adaptive pedagogical decision-making.
    """

    def __init__(self, prior_alpha: float = 2.0, prior_beta: float = 2.0):
        self.prior_alpha = prior_alpha
        self.prior_beta = prior_beta
        # student_id -> concept_id -> [alpha, beta]
        self.student_arms: Dict[str, Dict[str, List[float]]] = {}

    def get_or_init_arms(self, student_id: str, concepts: List[str]) -> Dict[str, List[float]]:
        """Initializes Beta distributions for student concepts if not present."""
        if student_id not in self.student_arms:
            self.student_arms[student_id] = {}

        arms = self.student_arms[student_id]
        for c in concepts:
            if c not in arms:
                arms[c] = [self.prior_alpha, self.prior_beta]
        return arms

    def sample_concept(
        self,
        student_id: str,
        eligible_concepts: List[str],
        concept_masteries: Dict[str, float],
        zpd_scores_by_concept: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Draws Thompson samples from Beta distributions for eligible concepts,
        and weighs them by ZPD alignment and mastery gap.
        """
        arms = self.get_or_init_arms(student_id, eligible_concepts)
        best_concept = None
        best_priority = -1.0
        details = []

        for cid in eligible_concepts:
            alpha, beta = arms[cid]
            # Draw sample from Beta(alpha, beta)
            sampled_theta = np.random.beta(alpha, beta)

            # Factors:
            # 1. ZPD fitness (prefer concepts with questions well-aligned to ability)
            zpd_weight = zpd_scores_by_concept.get(cid, 0.7)
            # 2. Mastery deficit (prefer concepts that are not yet mastered: 1 - mastery)
            cur_mastery = concept_masteries.get(cid, 0.0)
            mastery_deficit = max(0.1, 1.0 - cur_mastery)

            # Combined Priority Score:
            # High uncertainty (wide Beta) + High ZPD fit + High Need
            priority = (1.0 - sampled_theta) * 0.4 + zpd_weight * 0.4 + mastery_deficit * 0.2

            details.append({
                "concept_id": cid,
                "alpha": alpha,
                "beta": beta,
                "sampled_theta": round(float(sampled_theta), 3),
                "zpd_weight": round(float(zpd_weight), 3),
                "mastery_deficit": round(float(mastery_deficit), 3),
                "priority_score": round(float(priority), 3)
            })

            if priority > best_priority:
                best_priority = priority
                best_concept = cid

        return {
            "selected_concept": best_concept,
            "priority": round(best_priority, 3),
            "candidates": details
        }

    def update_arm(self, student_id: str, concept_id: str, is_correct: bool) -> None:
        """
        Updates posterior Beta parameters following an observed student response.
        """
        arms = self.get_or_init_arms(student_id, [concept_id])
        if is_correct:
            arms[concept_id][0] += 1.0  # Increment alpha
        else:
            arms[concept_id][1] += 1.0  # Increment beta
