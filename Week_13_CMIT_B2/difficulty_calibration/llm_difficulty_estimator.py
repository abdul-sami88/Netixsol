"""
Cognitive Difficulty Estimator
Predicts assessment difficulty based on Bloom's taxonomy tier, AST syntactic complexity,
cognitive load, and distractor trickiness.
"""

from typing import Dict, Any, List
import ast
import numpy as np

class LLMDifficultyEstimator:
    """
    Estimates a priori cognitive difficulty (b_pred) for questions before empirical testing.
    """

    BLOOM_WEIGHTS = {
        "Remembering": -1.2,
        "Understanding": -0.5,
        "Applying": 0.2,
        "Analyzing": 0.9,
        "Evaluating": 1.5,
        "Creating": 2.0
    }

    CONCEPT_COMPLEXITY_BIAS = {
        "variables": -1.0,
        "integers_floats": -0.8,
        "strings": -0.7,
        "booleans": -0.6,
        "if_else": -0.3,
        "while_loops": 0.3,
        "for_loops": 0.2,
        "nested_loops": 1.1,
        "functions_def": 0.1,
        "variable_scope": 0.8,
        "lists": 0.0,
        "list_comprehensions": 0.7,
        "dictionaries": 0.2,
        "recursion": 1.4,
        "decorators": 1.8,
        "iterators_generators": 1.5,
        "classes_instances": 0.9,
        "oop_inheritance": 1.3
    }

    @classmethod
    def estimate_difficulty(cls, question: Dict[str, Any]) -> float:
        """
        Computes predicted difficulty score b_pred on standard IRT logit scale [-3.0, 3.0].
        """
        bloom = question.get("blooms_level", "Applying")
        cid = question.get("concept_id", "functions_def")
        q_type = question.get("type", "mcq")

        # Base from Bloom's level
        b_bloom = cls.BLOOM_WEIGHTS.get(bloom, 0.0)

        # Concept intrinsic complexity
        b_concept = cls.CONCEPT_COMPLEXITY_BIAS.get(cid, 0.0)

        # Format factor (coding challenges are inherently more cognitively demanding than MCQs)
        format_adj = 0.4 if q_type == "coding" else 0.1 if q_type == "short_answer" else -0.2

        # Code length / AST complexity adjustment if code is present
        code_str = question.get("solution_code", "") or question.get("prompt", "")
        code_adj = 0.0
        if "def " in code_str or "while " in code_str or "for " in code_str:
            lines = [l for l in code_str.split("\n") if l.strip()]
            if len(lines) > 6:
                code_adj += 0.3
            if "if " in code_str and "else" in code_str:
                code_adj += 0.2

        raw_b = b_bloom * 0.45 + b_concept * 0.40 + format_adj + code_adj
        clamped_b = float(np.clip(raw_b, -2.8, 2.8))
        return round(clamped_b, 3)
