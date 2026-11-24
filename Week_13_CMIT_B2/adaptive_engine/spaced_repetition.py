"""
Spaced Repetition Engine
Models memory retention decay via the Ebbinghaus forgetting curve:
R(t) = exp(-delta_t / S)
Triggers scheduled review intervals before mastered knowledge decays.
"""

from typing import Dict, Any, List, Optional
import numpy as np

class SpacedRepetitionScheduler:
    """
    Manages long-term retention and review scheduling for mastered concepts.
    """

    RETENTION_THRESHOLD = 0.75  # Trigger review when predicted retention falls below 75%

    def __init__(self, base_stability: float = 3.0, stability_factor: float = 2.2):
        self.base_stability = base_stability
        self.stability_factor = stability_factor
        # student_id -> concept_id -> {last_session, stability, review_count}
        self.student_memory: Dict[str, Dict[str, Dict[str, Any]]] = {}

    def record_practice(
        self,
        student_id: str,
        concept_id: str,
        is_correct: bool,
        current_session: int
    ) -> None:
        """
        Updates memory stability and records current session timestamp.
        """
        if student_id not in self.student_memory:
            self.student_memory[student_id] = {}

        mem = self.student_memory[student_id]
        if concept_id not in mem:
            mem[concept_id] = {
                "last_session": current_session,
                "stability": self.base_stability,
                "review_count": 1
            }
        else:
            prev = mem[concept_id]
            if is_correct:
                # Expand stability exponentially on successful recall
                new_stability = prev["stability"] * self.stability_factor
                prev["review_count"] += 1
            else:
                # Reset or contract stability on failure
                new_stability = max(self.base_stability, prev["stability"] * 0.6)

            prev["stability"] = float(new_stability)
            prev["last_session"] = current_session

    def get_retention(self, student_id: str, concept_id: str, current_session: int) -> float:
        """
        Computes current retention probability R(t) = exp(-delta_t / S).
        """
        mem = self.student_memory.get(student_id, {}).get(concept_id, None)
        if mem is None:
            return 1.0  # Fresh concept

        delta_t = max(0, current_session - mem["last_session"])
        s = mem["stability"]
        retention = float(np.exp(-delta_t / s))
        return retention

    def get_concepts_needing_review(
        self,
        student_id: str,
        mastered_concepts: List[str],
        current_session: int
    ) -> List[Dict[str, Any]]:
        """
        Identifies mastered concepts whose retention has dropped below threshold.
        """
        due_for_review = []
        for cid in mastered_concepts:
            r = self.get_retention(student_id, cid, current_session)
            if r < self.RETENTION_THRESHOLD:
                mem = self.student_memory.get(student_id, {}).get(cid, {})
                due_for_review.append({
                    "concept_id": cid,
                    "retention": round(r, 3),
                    "days_since_practice": current_session - mem.get("last_session", current_session),
                    "stability": round(mem.get("stability", self.base_stability), 2),
                    "priority": round(1.0 - r, 3)
                })

        due_for_review.sort(key=lambda x: x["retention"])
        return due_for_review
