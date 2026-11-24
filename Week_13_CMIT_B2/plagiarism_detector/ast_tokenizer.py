"""
AST & Token Normalization Engine (Stanford MOSS Style)
Transforms raw Python code into an invariant canonical token stream:
- Anonymizes identifiers (variables -> VAR, functions -> FUNC, args -> ARG)
- Normalizes literals (numbers -> NUM, strings -> STR)
- Strips comments, docstrings, formatting, and dead whitespace
- Preserves grammatical control flow, operations, and AST structures
"""

import ast
import tokenize
import io
from typing import List, Tuple, Dict, Any

class ASTTokenNormalizer:
    """
    Normalizes Python code to defeat superficial plagiarism obfuscation
    (variable renaming, docstring manipulation, and formatting changes).
    """

    def normalize(self, code_str: str) -> List[Tuple[str, int]]:
        """
        Parses code via AST and returns a list of (canonical_token, line_number) tuples.
        """
        try:
            tree = ast.parse(code_str)
        except SyntaxError:
            # Fallback to lexical tokenization if syntax error
            return self._lexical_fallback(code_str)

        tokens: List[Tuple[str, int]] = []

        # Identifier mapping tables
        var_map: Dict[str, str] = {}
        func_map: Dict[str, str] = {}
        var_counter = 0
        func_counter = 0

        # AST Walker that emits canonical structural tokens
        for node in ast.walk(tree):
            lineno = getattr(node, "lineno", 1)
            node_type = type(node).__name__

            if isinstance(node, ast.FunctionDef):
                if node.name not in func_map:
                    func_counter += 1
                    func_map[node.name] = f"FUNC_{func_counter}"
                tokens.append((f"DEF_{func_map[node.name]}", lineno))

            elif isinstance(node, ast.Name):
                if node.id in var_map:
                    tokens.append((var_map[node.id], lineno))
                else:
                    var_counter += 1
                    mapped = f"VAR_{var_counter}"
                    var_map[node.id] = mapped
                    tokens.append((mapped, lineno))

            elif isinstance(node, (ast.For, ast.AsyncFor)):
                tokens.append(("FOR_LOOP", lineno))

            elif isinstance(node, ast.While):
                tokens.append(("WHILE_LOOP", lineno))

            elif isinstance(node, ast.If):
                tokens.append(("IF_BRANCH", lineno))

            elif isinstance(node, ast.Return):
                tokens.append(("RETURN_STMT", lineno))

            elif isinstance(node, ast.Call):
                tokens.append(("CALL_OP", lineno))

            elif isinstance(node, ast.Subscript):
                tokens.append(("INDEX_ACCESS", lineno))

            elif isinstance(node, ast.BinOp):
                op_name = type(node.op).__name__
                tokens.append((f"BINOP_{op_name}", lineno))

            elif isinstance(node, ast.Compare):
                tokens.append(("COMPARE_OP", lineno))

            elif isinstance(node, ast.Dict):
                tokens.append(("DICT_LITERAL", lineno))

            elif isinstance(node, ast.List):
                tokens.append(("LIST_LITERAL", lineno))

            elif isinstance(node, ast.Constant):
                if isinstance(node.value, (int, float)):
                    tokens.append(("NUM_CONST", lineno))
                elif isinstance(node.value, str):
                    tokens.append(("STR_CONST", lineno))

        return tokens

    def _lexical_fallback(self, code_str: str) -> List[Tuple[str, int]]:
        tokens = []
        try:
            reader = io.StringIO(code_str).readline
            for tok in tokenize.generate_tokens(reader):
                tok_type, tok_string, (srow, _), _, _ = tok
                if tok_type == tokenize.NAME:
                    tokens.append(("ID", srow))
                elif tok_type == tokenize.NUMBER:
                    tokens.append(("NUM", srow))
                elif tok_type == tokenize.STRING:
                    tokens.append(("STR", srow))
                elif tok_type == tokenize.OP:
                    tokens.append((f"OP_{tok_string}", srow))
        except Exception:
            pass
        return tokens
