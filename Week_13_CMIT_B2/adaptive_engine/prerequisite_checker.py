"""
Prerequisite Checker Module
Validates concept eligibility against the prerequisite DAG.
Ensures students only encounter concepts whose parent concepts are solidly mastered.
"""

from typing import Dict, Any, List, Set, Optional
import json
import os

class PrerequisiteChecker:
    """
    Enforces DAG-based dependency rules for adaptive learning.
    """

    def __init__(self, concept_graph_path: str = "concept_graph/concept_graph.json"):
        self.prerequisites: Dict[str, List[str]] = {}
        self.concept_names: Dict[str, str] = {}
        self.load_graph(concept_graph_path)

    def load_graph(self, path: str) -> None:
        """Loads DAG edges and nodes from exported concept graph."""
        if not os.path.exists(path):
            raise FileNotFoundError(f"Concept graph not found at {path}")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for node in data.get("nodes", []):
            cid = node["id"]
            self.prerequisites[cid] = node.get("prerequisites", [])
            self.concept_names[cid] = node.get("name", cid)

    def is_concept_eligible(
        self,
        concept_id: str,
        student_mastery_scores: Dict[str, float],
        mastery_threshold: float = 0.70
    ) -> Tuple[bool, List[str]]:
        """
        Checks if concept_id is unlocked.
        Returns (is_eligible, missing_prerequisites).
        """
        prereqs = self.prerequisites.get(concept_id, [])
        if not prereqs:
            return True, []

        missing = []
        for p in prereqs:
            score = student_mastery_scores.get(p, 0.0)
            if score < mastery_threshold:
                missing.append(p)

        is_eligible = len(missing) == 0
        return is_eligible, missing

    def get_unlocked_concepts(
        self,
        student_mastery_scores: Dict[str, float],
        mastery_threshold: float = 0.70
    ) -> List[str]:
        """
        Returns all concepts whose prerequisites are satisfied but are not yet mastered.
        """
        unlocked = []
        for cid in self.prerequisites:
            current_mastery = student_mastery_scores.get(cid, 0.0)
            if current_mastery < mastery_threshold:
                eligible, missing = self.is_concept_eligible(cid, student_mastery_scores, mastery_threshold)
                if eligible:
                    unlocked.append(cid)
        return unlocked
