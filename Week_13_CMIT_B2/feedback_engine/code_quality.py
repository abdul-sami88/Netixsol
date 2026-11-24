"""
Code Quality & Static Analysis Engine
Calculates McCabe Cyclomatic Complexity, Maintainability Index, nesting depth,
and PEP 8 structural lint rules using Python's native AST parser (zero external binary dependencies).
"""

import ast
import math
from typing import Dict, Any, List

class ComplexityVisitor(ast.NodeVisitor):
    """
    Computes Cyclomatic Complexity (M = decision_points + 1) and tracks nesting depth.
    """
    def __init__(self):
        self.decision_points = 0
        self.max_depth = 0
        self.current_depth = 0

    def _enter_block(self):
        self.current_depth += 1
        if self.current_depth > self.max_depth:
            self.max_depth = self.current_depth

    def _exit_block(self):
        self.current_depth -= 1

    def visit_If(self, node: ast.If):
        self.decision_points += 1
        self._enter_block()
        self.generic_visit(node)
        self._exit_block()

    def visit_For(self, node: ast.For):
        self.decision_points += 1
        self._enter_block()
        self.generic_visit(node)
        self._exit_block()

    def visit_While(self, node: ast.While):
        self.decision_points += 1
        self._enter_block()
        self.generic_visit(node)
        self._exit_block()

    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        self.decision_points += 1
        self._enter_block()
        self.generic_visit(node)
        self._exit_block()

    def visit_With(self, node: ast.With):
        self._enter_block()
        self.generic_visit(node)
        self._exit_block()

    def visit_BoolOp(self, node: ast.BoolOp):
        # 'and' or 'or' each add a branching decision point
        self.decision_points += len(node.values) - 1
        self.generic_visit(node)

    def visit_IfExp(self, node: ast.IfExp):
        self.decision_points += 1
        self.generic_visit(node)

    def visit_comprehension(self, node: ast.comprehension):
        self.decision_points += 1
        self.generic_visit(node)


class CodeQualityAnalyzer:
    """
    Comprehensive static quality analyzer for student code submissions.
    """

    SHADOW_BUILTINS = {"list", "dict", "str", "int", "sum", "set", "tuple", "len", "type", "id", "input", "range"}

    def analyze(self, code_str: str) -> Dict[str, Any]:
        lines = code_str.strip().split("\n")
        loc = len([line for line in lines if line.strip() and not line.strip().startswith("#")])
        loc = max(loc, 1)

        style_warnings = []

        # Check line lengths
        for idx, line in enumerate(lines, start=1):
            if len(line) > 79:
                style_warnings.append(f"Line {idx} exceeds 79 characters ({len(line)} chars) [PEP 8: E501]")

        try:
            tree = ast.parse(code_str)
        except SyntaxError as e:
            return {
                "is_parsable": False,
                "cyclomatic_complexity": 1,
                "complexity_rating": "N/A",
                "maintainability_index": 0.0,
                "loc": loc,
                "max_nesting_depth": 0,
                "has_docstring": False,
                "style_warnings": [f"SyntaxError: {e.msg} at line {e.lineno}"]
            }

        # Measure Cyclomatic Complexity
        visitor = ComplexityVisitor()
        visitor.visit(tree)
        cyclomatic = visitor.decision_points + 1
        max_depth = visitor.max_depth

        # Complexity Rating
        if cyclomatic <= 5:
            rating = "A (Low Complexity / Clean)"
        elif cyclomatic <= 10:
            rating = "B (Moderate Complexity)"
        elif cyclomatic <= 20:
            rating = "C (High Complexity / Complex)"
        else:
            rating = "D (Untestable / Extreme Complexity)"

        # Check Docstrings and Naming
        has_docstring = False
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if ast.get_docstring(node):
                    has_docstring = True
                if not node.name.islower() and "_" not in node.name:
                    style_warnings.append(f"Function '{node.name}' should use snake_case [PEP 8: N802]")
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                if node.id in self.SHADOW_BUILTINS:
                    style_warnings.append(f"Variable '{node.id}' shadows Python built-in name [PEP 8: A001]")

        # Maintainability Index Calculation (Radon / SEI Standard)
        # MI = 171 - 5.2 * ln(V) - 0.23 * M - 16.2 * ln(LOC)
        # Normalized to 0 - 100
        halstead_est = loc * (visitor.decision_points + 2) * 5.0
        halstead_vol = max(halstead_est, 1.0)
        raw_mi = 171.0 - (5.2 * math.log(halstead_vol)) - (0.23 * cyclomatic) - (16.2 * math.log(loc))
        normalized_mi = max(0.0, min(100.0, (raw_mi * 100.0) / 171.0))

        return {
            "is_parsable": True,
            "cyclomatic_complexity": cyclomatic,
            "complexity_rating": rating,
            "maintainability_index": round(normalized_mi, 1),
            "loc": loc,
            "max_nesting_depth": max_depth,
            "has_docstring": has_docstring,
            "style_warnings": style_warnings[:3] # Limit to top 3 warnings
        }
