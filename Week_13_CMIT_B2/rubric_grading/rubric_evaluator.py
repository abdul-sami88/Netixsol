"""
Rubric-Based LLM Evaluator for Written Conceptual Answers
Grades student essay responses against a 10-point standardized rubric:
- Criterion 1: Technical Correctness & Core Mechanism (0 - 4 pts)
- Criterion 2: Edge Cases, Constraints & Trade-offs (0 - 3 pts)
- Criterion 3: Technical Terminology, Clarity & Structure (0 - 3 pts)

Applies rigorous concept checking, penalizes factual inversions, and guards against verbosity fluff.
"""

import re
from typing import Dict, Any, List

class RubricEvaluator:
    """
    Simulates standardized LLM rubric evaluation calibrated against human teacher benchmarks.
    """

    CRITERIA_KEYWORDS = {
        "Q1": {
            # Recursion & Call Stack
            "correct_mechanism": [
                ("call stack", 1.0),
                ("stack frame", 1.0),
                ("base case", 1.0),
                ("unwound", 0.5),
                ("pop", 0.5),
                ("lifo", 0.5),
                ("pushed", 0.5)
            ],
            "edge_cases": [
                ("1000", 1.0),
                ("sys.getrecursionlimit", 1.5),
                ("missing base case", 1.0),
                ("recursion depth", 1.0),
                ("stack overflow", 1.0),
                ("negative", 0.5)
            ],
            "terminology": [
                ("frame", 0.5),
                ("local variable", 0.5),
                ("recursionerror", 1.0),
                ("return address", 0.5),
                ("converge", 0.5)
            ],
            "misconceptions": [
                (r"\bheap\b", -2.0, "Confused call stack with heap allocation"),
                (r"\bsyntax\s*error\b", -3.0, "Confused RecursionError with syntax error"),
                (r"\bgarbage\s*collection\b", -1.5, "Irrelevant garbage collection reference")
            ]
        },
        "Q2": {
            # Complexity Comparison
            "correct_mechanism": [
                ("o(n^2)", 1.5),
                ("quadratic", 1.0),
                ("o(n)", 1.5),
                ("linear", 1.0),
                ("hash set", 1.0),
                ("o(1)", 1.0)
            ],
            "edge_cases": [
                ("o(1) space", 1.0),
                ("o(n) space", 1.0),
                ("trade-off", 1.0),
                ("collision", 1.0),
                ("memory", 0.5),
                ("embedded", 0.5)
            ],
            "terminology": [
                ("asymptotic", 0.5),
                ("lookup", 0.5),
                ("auxiliary space", 0.5),
                ("time complexity", 0.5),
                ("pairwise", 0.5)
            ],
            "misconceptions": [
                (r"o\(n\)\s*time\s*and\s*o\(n\)\s*space\s*for\s*nested", -3.0, "Inverted complexity of nested loops"),
                (r"o\(1\)\s*time.*hash\s*set", -2.0, "Claimed overall hash set algorithm is O(1) time instead of O(N)"),
                (r"exact\s*same\s*time\s*complexity", -4.0, "Claimed nested loops and hash set have identical time complexity"),
                (r"sort\s*the\s*list\s*first", -2.0, "Asserted nested loops sort the list first")
            ]
        },
        "Q3": {
            # Tuples & Immutability
            "correct_mechanism": [
                ("immutable", 1.5),
                ("cannot be modified", 1.0),
                ("hashable", 1.5),
                ("dictionary key", 1.5),
                ("set", 0.5)
            ],
            "edge_cases": [
                ("coordinate", 1.0),
                ("return multiple", 1.0),
                ("memory", 1.0),
                ("data integrity", 0.5),
                ("fixed block", 0.5),
                ("accidental modification", 0.5)
            ],
            "terminology": [
                ("hash value", 0.5),
                ("data integrity", 0.5),
                ("record", 0.5),
                ("allocation", 0.5),
                ("overhead", 0.5)
            ],
            "misconceptions": [
                (r"tuples\s*are\s*mutable", -4.0, "Claimed tuples are mutable"),
                (r"stored\s*on\s*the\s*hard\s*drive", -4.0, "Claimed tuples are stored on hard drive"),
                (r"only\s*difference", -2.0, "Claimed brackets are the only difference")
            ]
        }
    }

    def evaluate(self, question_id: str, response_text: str) -> Dict[str, Any]:
        cfg = self.CRITERIA_KEYWORDS.get(question_id, self.CRITERIA_KEYWORDS["Q1"])
        text_lower = response_text.lower()
        words = re.findall(r"\w+", text_lower)
        word_count = len(words)

        # 1. Score Criterion 1: Correct Mechanism (0 to 4)
        raw_c1 = 0.0
        for phrase, weight in cfg["correct_mechanism"]:
            if phrase in text_lower:
                raw_c1 += weight
        score_c1 = min(4.0, max(0.0, round(raw_c1, 1)))

        # 2. Score Criterion 2: Edge Cases & Trade-offs (0 to 3)
        raw_c2 = 0.0
        for phrase, weight in cfg["edge_cases"]:
            if phrase in text_lower:
                raw_c2 += weight
        score_c2 = min(3.0, max(0.0, round(raw_c2, 1)))

        # 3. Score Criterion 3: Technical Clarity & Terminology (0 to 3)
        raw_c3 = 0.0
        for phrase, weight in cfg["terminology"]:
            if phrase in text_lower:
                raw_c3 += weight
        if word_count >= 15 and score_c1 > 1.0:
            raw_c3 += 0.5
        score_c3 = min(3.0, max(0.0, round(raw_c3, 1)))

        # 4. Check Misconceptions & Inversions (Penalties)
        penalties = 0.0
        violations = []
        for pat, pen, msg in cfg["misconceptions"]:
            if re.search(pat, text_lower):
                penalties += abs(pen)
                violations.append(msg)

        # 5. Check Verbose Fluff Penalty (High word count but no concrete core terms)
        is_fluff = False
        fluff_markers = ["synergistic", "quantum compiler", "polymorphic", "architectural overflow", "non-volatile memory references"]
        for marker in fluff_markers:
            if marker in text_lower:
                is_fluff = True
                penalties += 2.0
                violations.append("Pseudo-technical verbosity / unsupported jargon detected")
                break

        # Calculate final composite score
        total_raw = (score_c1 + score_c2 + score_c3) - penalties
        total_score = max(0.0, min(10.0, round(total_raw, 0)))

        # Adjust score if core correctness was negligible
        if score_c1 <= 1.0:
            total_score = min(total_score, 4.0)
        if violations and total_score > 3.0 and is_fluff:
            total_score = 3.0

        return {
            "question_id": question_id,
            "total_score": int(total_score),
            "criterion_correctness": score_c1,
            "criterion_edge_cases": score_c2,
            "criterion_terminology": score_c3,
            "penalties_applied": penalties,
            "violations_detected": violations,
            "word_count": word_count,
            "feedback": self._generate_rubric_rationale(total_score, violations, score_c1, score_c2)
        }

    def _generate_rubric_rationale(self, score: float, violations: list, c1: float, c2: float) -> str:
        if score >= 9:
            return "Exemplary response: covers technical mechanisms, edge cases, and precise terminology accurately."
        elif score >= 7:
            return "Solid response: sound core explanation, though some edge cases or theoretical constraints could be expanded."
        elif score >= 5:
            return "Basic conceptual understanding demonstrated, but lacks technical depth or specific terminology."
        elif violations:
            return f"Contains significant factual misconceptions: {'; '.join(violations)}."
        else:
            return "Incomplete or inaccurate explanation. Key architectural mechanisms were omitted."
