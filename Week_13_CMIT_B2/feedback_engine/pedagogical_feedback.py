"""
Pedagogical AI Code Feedback Engine
Generates constructive, Socratic code review feedback for student submissions:
1. Explains why failed tests occurred conceptually (without revealing test secrets).
2. Reports McCabe Cyclomatic Complexity, Maintainability Index, and style alerts.
3. Provides exactly ONE concrete, actionable improvement.
4. References the relevant course concept, lesson module, and video timestamp.
5. Strict Safety Guard: NEVER leaks the full solution code.
"""

import re
from typing import Dict, Any, Optional
import os
import sys

# Ensure local imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from feedback_engine.code_quality import CodeQualityAnalyzer

class PedagogicalFeedbackEngine:
    """
    Generates actionable student feedback following strict Socratic principles.
    """

    CONCEPT_LESSON_MAP = {
        "two_sum": {
            "concept_id": "C09",
            "concept_name": "Dictionaries & Hash Maps",
            "bloom_level": "Apply",
            "lesson_title": "Lesson 09: Fast Key-Value Lookups and Complement Searching",
            "video_timestamp": "14:20",
            "notes_link": "course_materials/week2/dictionaries_hashmaps.pdf#page=4"
        },
        "recursive_factorial": {
            "concept_id": "C17",
            "concept_name": "Recursion & Call Stack",
            "bloom_level": "Analyze",
            "lesson_title": "Lesson 17: Base Cases and Call Stack Visualization",
            "video_timestamp": "08:45",
            "notes_link": "course_materials/week4/recursion_call_stack.pdf#page=2"
        }
    }

    def __init__(self):
        self.quality_analyzer = CodeQualityAnalyzer()

    def generate_feedback(
        self,
        submission_id: str,
        student_id: str,
        code_str: str,
        grading_result: Dict[str, Any],
        problem_name: str = "two_sum"
    ) -> Dict[str, Any]:
        """
        Synthesizes test results and static quality analysis into structured pedagogical feedback.
        """
        quality = self.quality_analyzer.analyze(code_str)
        lesson_meta = self.CONCEPT_LESSON_MAP.get(problem_name, self.CONCEPT_LESSON_MAP["two_sum"])

        score = grading_result.get("autograder_score", 0.0)
        verdict = grading_result.get("verdict", "UNKNOWN")
        failed_test = grading_result.get("failed_test")
        failed_reason = grading_result.get("failed_reason")

        # 1. Diagnose Failed Tests Conceptually (Without leaking full answers)
        diagnosis = self._diagnose_failure(verdict, failed_test, failed_reason)

        # 2. Select Exactly ONE Actionable Pedagogical Improvement
        single_improvement = self._select_single_improvement(verdict, quality, failed_test, failed_reason)

        # 3. Assemble Socratic Feedback Text
        feedback_markdown = self._format_feedback_markdown(
            student_id=student_id,
            score=score,
            verdict=verdict,
            diagnosis=diagnosis,
            quality=quality,
            single_improvement=single_improvement,
            lesson_meta=lesson_meta
        )

        # 4. Strict Safety Audit: Check for solution leakage
        leakage_detected, leakage_reason = self._audit_for_solution_leakage(feedback_markdown)

        return {
            "submission_id": submission_id,
            "student_id": student_id,
            "autograder_score": score,
            "verdict": verdict,
            "diagnosis": diagnosis,
            "code_quality": {
                "cyclomatic_complexity": quality["cyclomatic_complexity"],
                "complexity_rating": quality["complexity_rating"],
                "maintainability_index": quality["maintainability_index"],
                "loc": quality["loc"],
                "max_nesting_depth": quality["max_nesting_depth"],
                "style_warnings": quality["style_warnings"]
            },
            "single_actionable_improvement": single_improvement,
            "lesson_citation": {
                "concept": f"{lesson_meta['concept_id']}: {lesson_meta['concept_name']}",
                "lesson": lesson_meta["lesson_title"],
                "video_timestamp": lesson_meta["video_timestamp"],
                "notes_link": lesson_meta["notes_link"]
            },
            "solution_leakage_detected": leakage_detected,
            "feedback_markdown": feedback_markdown
        }

    def _diagnose_failure(self, verdict: str, failed_test: Optional[str], failed_reason: Optional[str]) -> str:
        if verdict == "ACCEPTED":
            return "All test cases passed! Your implementation correctly satisfied all functional edge cases and time complexity requirements."

        if verdict == "SECURITY_VIOLATION":
            return "Your submission attempted an unauthorized operation (such as accessing restricted system libraries). Code must execute purely within the standard problem constraints."

        if verdict == "TIME_LIMIT_EXCEEDED":
            return "Your code was stopped because it ran longer than the allowed time limit (2.0s). This usually happens when a loop has no termination condition or increments the wrong counter variable."

        if "Duplicate" in str(failed_test) or "identical index" in str(failed_reason):
            return "Your solution appears to pair an element with itself or return identical indices when the target equals twice an element's value. Remember: each index must be distinct."

        if "Scale Efficiency" in str(failed_test) or "O(N^2)" in str(failed_reason):
            return "Your algorithm succeeded on small inputs but exceeded the linear time threshold on large arrays (12,000+ elements). Using nested loops forces the processor to make up to N*(N-1)/2 comparisons."

        if "Negative" in str(failed_test):
            return "Your logic produced unexpected outputs when handling negative values or subtracting numbers. Verify how your formula computes the needed complement for negative integers."

        if "SyntaxError" in str(failed_reason) or verdict == "SYNTAX_ERROR":
            return "The Python interpreter encountered a syntax error while parsing your code. Check for missing colons at the end of loop/condition statements or mismatched brackets."

        if "IndexError" in str(failed_reason):
            return "An IndexError occurred. Your loop attempted to access an array index that was out of bounds (such as index `i + 1` at the final element)."

        return f"A test edge case was not satisfied: {failed_reason or 'Incorrect index output for edge test'}. Review boundary conditions."

    def _select_single_improvement(self, verdict: str, quality: dict, failed_test: Optional[str], failed_reason: Optional[str]) -> str:
        """
        Enforces pedagogical best practice: focus the learner on EXACTLY ONE highest-impact improvement.
        """
        if verdict == "ACCEPTED":
            if quality["cyclomatic_complexity"] > 4:
                return "Refactor your conditional logic: simplify multiple branching statements into a unified dictionary lookup to make your code more readable."
            elif not quality["has_docstring"]:
                return "Add a concise docstring specifying the expected argument types, time complexity O(N), and return value."
            else:
                return "Try rewriting your solution using Python's `enumerate()` for a more idiomatic one-pass scan."

        if "Duplicate" in str(failed_test) or "identical index" in str(failed_reason):
            return "Before saving an element to your hash map or returning indices, ensure that the current index `i` is not equal to the stored complement index."

        if "Scale Efficiency" in str(failed_test):
            return "Replace the nested loop with a hash map (Python dict): as you iterate through the list, compute `target - num` and look it up in O(1) average time instead of scanning the rest of the list."

        if "Negative" in str(failed_test):
            return "Carefully trace how your complement is computed for negative numbers: avoid filtering out values where x < 0 or assuming elements are positive."

        if "IndexError" in str(failed_reason):
            return "Check your loop upper bound: accessing `nums[i + 1]` requires the range to stop at `len(nums) - 1`."

        if quality["max_nesting_depth"] >= 2:
            return "Reduce nesting depth: avoid nested loops or deep conditionals by utilizing dictionary lookups or early returns."

        if quality["maintainability_index"] < 50.0:
            return "Reduce code nesting: flatten nested if/for structures by using early return statements or dictionary lookups."

        return "Carefully trace your loop boundaries on paper with an example containing negative integers to ensure your complement calculation holds."

    def _format_feedback_markdown(
        self,
        student_id: str,
        score: float,
        verdict: str,
        diagnosis: str,
        quality: dict,
        single_improvement: str,
        lesson_meta: dict
    ) -> str:
        badge = "[PASS]" if score == 100.0 else "[PARTIAL]" if score > 0 else "[NEEDS REVISION]"
        
        md = f"""### {badge} Automated Code Review Feedback

**Student:** `{student_id}` | **Score:** `{score}/100` | **Status:** `{verdict}`

---

#### 1. Test Diagnostic
{diagnosis}

#### 2. Code Quality & Maintainability
- **Cyclomatic Complexity:** `{quality['cyclomatic_complexity']}` — Rating: **{quality['complexity_rating']}**
- **Maintainability Index:** `{quality['maintainability_index']}/100`
- **Lines of Code (LOC):** `{quality['loc']}` (Max Nesting Depth: `{quality['max_nesting_depth']}`)
"""
        if quality["style_warnings"]:
            md += "\n**Style Notices (PEP 8):**\n"
            for w in quality["style_warnings"]:
                md += f"- *{w}*\n"

        md += f"""
#### 3. Key Actionable Improvement (Priority #1)
> [!TIP]
> **{single_improvement}**

#### 4. Recommended Course Materials
- **Concept:** `{lesson_meta['concept_id']}: {lesson_meta['concept_name']}`
- **Lesson:** *{lesson_meta['lesson_title']}*
- **Video Timestamp:** [Watch clip at {lesson_meta['video_timestamp']}](https://ilm-academy.org/lectures/c09#{lesson_meta['video_timestamp']})
- **Course Notes:** `{lesson_meta['notes_link']}`
"""
        return md

    def _audit_for_solution_leakage(self, text: str) -> tuple:
        """
        Validates that the feedback text does NOT contain full working code.
        """
        # Forbidden code leakage patterns
        leak_patterns = [
            r"def\s+two_sum\s*\(",
            r"return\s*\[\s*(seen|lookup|d|indices|memo)\[",
            r"for\s+i\s*,\s*num\s+in\s+enumerate\(nums\):[\s\S]*return",
        ]
        for pattern in leak_patterns:
            if re.search(pattern, text):
                return True, f"Code leakage guard triggered: matched forbidden snippet pattern '{pattern}'"
        return False, "Clean: No solution leakage detected"
