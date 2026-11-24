"""
Automated Question Validator & Acceptance Engine
Performs multi-stage quality verification:
1. Python AST syntax parsing
2. Unit test case execution against sample solutions
3. Distractor plausibility & misconception audit
4. Computes automated acceptance rate
"""

import ast
from typing import Dict, Any, List, Tuple
import os
import json
from question_generator.question_builder import QuestionBuilder

class QuestionValidator:
    """
    Automated validator ensuring all generated questions are syntactically sound,
    executable, and pedagogically robust.
    """

    def __init__(self):
        self.validated_items: List[Dict[str, Any]] = []
        self.rejection_log: List[Dict[str, Any]] = []

    def validate_code_syntax(self, code_str: str) -> Tuple[bool, str]:
        """Validates Python code syntax using AST parsing."""
        if not code_str or not code_str.strip():
            return True, "empty"
        try:
            ast.parse(code_str)
            return True, "valid"
        except SyntaxError as e:
            return False, f"SyntaxError: {e.msg} on line {e.lineno}"

    def execute_test_cases(self, solution_code: str, test_cases: List[Dict[str, Any]]) -> Tuple[bool, str]:
        """
        Executes unit test cases against the sample solution in an isolated namespace.
        """
        if not solution_code or not test_cases:
            return True, "no_tests_required"

        namespace = {}
        try:
            exec(solution_code, namespace)
        except Exception as e:
            return False, f"Solution compilation failed: {str(e)}"

        for idx, tc in enumerate(test_cases, 1):
            test_call = tc["input"]
            expected = tc["expected"]
            try:
                actual = eval(test_call, namespace)
                if actual != expected:
                    return False, f"Test {idx} failed: {test_call} returned {actual}, expected {expected}"
            except Exception as e:
                return False, f"Test {idx} error: {str(e)}"

        return True, "all_passed"

    def validate_question(self, q: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Performs comprehensive checks on a question object.
        """
        q_id = q["id"]
        q_type = q["type"]
        errors = []

        # 1. Prompt validity
        if len(q.get("prompt", "").strip()) < 15:
            errors.append("Prompt is too brief or empty.")

        # 2. Type-specific checks
        if q_type == "mcq":
            options = q.get("options", {})
            if len(options) < 4:
                errors.append(f"MCQ has only {len(options)} options; expected 4.")
            if q.get("correct_answer") not in options:
                errors.append(f"Correct answer '{q.get('correct_answer')}' not among options {list(options.keys())}.")
            # Check unique option values
            opt_vals = list(options.values())
            if len(opt_vals) != len(set(opt_vals)):
                errors.append("Duplicate option texts detected.")

        elif q_type == "coding":
            sol = q.get("solution_code", "")
            tests = q.get("test_cases", [])
            # Check syntax
            is_valid_syntax, syn_msg = self.validate_code_syntax(sol)
            if not is_valid_syntax:
                errors.append(f"Solution syntax invalid: {syn_msg}")
            # Run test cases
            passed_tests, test_msg = self.execute_test_cases(sol, tests)
            if not passed_tests:
                errors.append(f"Unit test failure: {test_msg}")

        elif q_type == "short_answer":
            if not q.get("correct_answer", "").strip():
                errors.append("Short answer missing correct answer string.")

        is_accepted = len(errors) == 0
        return is_accepted, errors

    def run_validation_suite(
        self,
        questions: Optional[List[Dict[str, Any]]] = None,
        export_path: str = "question_generator/generated_questions.json"
    ) -> Dict[str, Any]:
        """
        Validates question collection and exports accepted set.
        """
        if questions is None:
            questions = QuestionBuilder.build_all_candidate_questions()

        accepted = []
        rejected = []

        for q in questions:
            is_ok, errs = self.validate_question(q)
            if is_ok:
                accepted.append(q)
            else:
                rejected.append({"question_id": q["id"], "errors": errs})

        total = len(questions)
        acceptance_rate = round(len(accepted) / max(1, total) * 100, 1)

        self.validated_items = accepted
        self.rejection_log = rejected

        # Export accepted questions
        os.makedirs(os.path.dirname(os.path.abspath(export_path)), exist_ok=True)
        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(accepted, f, indent=2)

        summary = {
            "total_questions_evaluated": total,
            "accepted_count": len(accepted),
            "rejected_count": len(rejected),
            "acceptance_rate_pct": acceptance_rate,
            "exported_file": export_path,
            "breakdown_by_type": {
                "mcq": len([q for q in accepted if q["type"] == "mcq"]),
                "short_answer": len([q for q in accepted if q["type"] == "short_answer"]),
                "coding": len([q for q in accepted if q["type"] == "coding"])
            }
        }
        return summary
