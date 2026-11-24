"""
Zone of Proximal Development (ZPD) Selector
Filters and scores candidate assessment items to target the sweet spot:
60% to 80% predicted probability of success (optimal challenge without frustration).
"""

from typing import Dict, Any, List, Optional
import numpy as np

class ZPDSelector:
    """
    Selects items tailored to a student's Zone of Proximal Development (ZPD).
    Target: P(correct | theta) in [0.60, 0.80], ideally centered around 0.70.
    """

    def __init__(self, target_p_low: float = 0.60, target_p_high: float = 0.80, optimal_p: float = 0.70):
        self.target_p_low = target_p_low
        self.target_p_high = target_p_high
        self.optimal_p = optimal_p

    def calculate_zpd_score(self, predicted_p: float) -> float:
        """
        Scores how well predicted_p fits into the ZPD window.
        Returns a value in [0.0, 1.0], peaking at optimal_p (0.70).
        """
        if self.target_p_low <= predicted_p <= self.target_p_high:
            # Triangular score peaking at 1.0 at optimal_p
            dist = abs(predicted_p - self.optimal_p)
            max_dist = max(self.optimal_p - self.target_p_low, self.target_p_high - self.optimal_p)
            score = 1.0 - 0.5 * (dist / max_dist)
            return float(np.clip(score, 0.5, 1.0))
        elif predicted_p < self.target_p_low:
            # Too hard: penalize heavily to prevent frustration and dropout
            penalty = (self.target_p_low - predicted_p) / self.target_p_low
            return float(max(0.0, 0.5 * (1.0 - penalty)))
        else:
            # Too easy: penalize boredom
            penalty = (predicted_p - self.target_p_high) / (1.0 - self.target_p_high + 1e-4)
            return float(max(0.1, 0.5 * (1.0 - penalty)))

    def filter_and_rank_items(
        self,
        candidate_items: List[Dict[str, Any]],
        student_theta: float,
        irt_lookup: Dict[str, Dict[str, float]]
    ) -> List[Dict[str, Any]]:
        """
        Ranks candidate items based on their ZPD fitness for a student with ability student_theta.
        """
        ranked = []
        for item in candidate_items:
            qid = item["id"]
            params = irt_lookup.get(qid, {"a_2pl": 1.2, "b_2pl": (item["difficulty"] - 3.0) * 0.9})
            a = params.get("a_2pl", 1.2)
            b = params.get("b_2pl", 0.0)

            # Predicted probability of correct response under 2PL IRT
            logit = np.clip(a * (student_theta - b), -15.0, 15.0)
            p_pred = 1.0 / (1.0 + np.exp(-logit))

            zpd_score = self.calculate_zpd_score(p_pred)
            in_zpd = self.target_p_low <= p_pred <= self.target_p_high

            ranked.append({
                "item": item,
                "question_id": qid,
                "concept_id": item["concept_id"],
                "predicted_p": round(float(p_pred), 3),
                "zpd_score": round(zpd_score, 3),
                "in_zpd": in_zpd,
                "a": round(float(a), 2),
                "b": round(float(b), 2)
            })

        # Sort descending by zpd_score
        ranked.sort(key=lambda x: x["zpd_score"], reverse=True)
        return ranked
