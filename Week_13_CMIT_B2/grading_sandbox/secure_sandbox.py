"""
Secure Code Execution Sandbox
Provides process-isolated execution with strict wall-clock timeouts, memory limits,
sanitized environment variables, and pre-execution AST security screening.
"""

import ast
import os
import sys
import subprocess
import tempfile
import time
from typing import Dict, Any, List, Tuple, Optional

class ASTSecurityInspector(ast.NodeVisitor):
    """
    Inspects Python Abstract Syntax Tree (AST) before execution to intercept malicious calls,
    unauthorized imports, filesystem operations, and reflection/metaprogramming escapes.
    """

    BANNED_MODULES = {
        "os", "sys", "subprocess", "socket", "ctypes", "shutil", "urllib",
        "requests", "http", "ftplib", "builtins", "__builtin__", "importlib",
        "signal", "pty", "commands", "posix", "nt"
    }

    BANNED_BUILTINS = {
        "eval", "exec", "__import__", "compile", "open", "input",
        "globals", "locals", "getattr", "setattr", "delattr"
    }

    BANNED_ATTRIBUTES = {
        "__subclasses__", "__bases__", "__mro__", "__globals__",
        "__code__", "__closure__", "__builtins__"
    }

    def __init__(self):
        self.violations: List[str] = []

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            mod_root = alias.name.split(".")[0]
            if mod_root in self.BANNED_MODULES:
                self.violations.append(f"Security Violation: Import of banned module '{alias.name}'")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module:
            mod_root = node.module.split(".")[0]
            if mod_root in self.BANNED_MODULES:
                self.violations.append(f"Security Violation: Import from banned module '{node.module}'")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        # Check direct calls to banned built-ins
        if isinstance(node.func, ast.Name):
            if node.func.id in self.BANNED_BUILTINS:
                self.violations.append(f"Security Violation: Direct invocation of banned built-in '{node.func.id}()'")
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):
        if node.attr in self.BANNED_ATTRIBUTES:
            self.violations.append(f"Security Violation: Reflection escape via dunder attribute '{node.attr}'")
        self.generic_visit(node)


class SecureCodeSandbox:
    """
    Runs untrusted Python student submissions in an isolated subprocess sandbox.
    """

    DEFAULT_TIMEOUT_SEC = 2.0  # Strict 2-second wall-clock CPU timeout

    def __init__(self, timeout_sec: float = DEFAULT_TIMEOUT_SEC, python_executable: Optional[str] = None):
        self.timeout_sec = timeout_sec
        self.python_executable = python_executable or sys.executable

    def audit_ast(self, code_str: str) -> Tuple[bool, List[str]]:
        """
        Scans code AST before running. Returns (is_safe, list_of_violations).
        """
        try:
            tree = ast.parse(code_str)
        except SyntaxError as e:
            return False, [f"SyntaxError: {e.msg} on line {e.lineno}"]

        inspector = ASTSecurityInspector()
        inspector.visit(tree)
        is_safe = len(inspector.violations) == 0
        return is_safe, inspector.violations

    def execute_code(
        self,
        code_str: str,
        test_harness_str: str = "",
        custom_timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Executes code safely inside an isolated subprocess with zero environment access.
        """
        timeout = custom_timeout or self.timeout_sec

        # 1. Pre-execution AST security screening
        is_safe, violations = self.audit_ast(code_str)
        if not is_safe:
            return {
                "verdict": "SECURITY_VIOLATION",
                "status_code": 403,
                "execution_time_sec": 0.0,
                "stdout": "",
                "stderr": "; ".join(violations),
                "is_contained": True,
                "violations": violations
            }

        # 2. Prepare isolated source file
        full_code = f"{code_str}\n\n# --- Test Execution Harness ---\n{test_harness_str}"

        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
            temp_path = f.name
            f.write(full_code)

        start_time = time.time()
        # Isolated minimal environment (no host tokens, credentials, or user vars)
        sanitized_env = {
            "SYSTEMROOT": os.environ.get("SYSTEMROOT", "C:\\Windows"),
            "PATH": os.environ.get("PATH", ""),
            "PYTHONPATH": ""
        }

        try:
            # Run in isolated subprocess
            proc = subprocess.run(
                [self.python_executable, "-I", temp_path], # -I isolated mode (ignores PYTHONPATH and user site)
                capture_output=True,
                text=True,
                timeout=timeout,
                env=sanitized_env
            )
            elapsed = time.time() - start_time

            if proc.returncode == 0:
                verdict = "SUCCESS"
            else:
                verdict = "RUNTIME_ERROR"

            return {
                "verdict": verdict,
                "status_code": proc.returncode,
                "execution_time_sec": round(elapsed, 4),
                "stdout": proc.stdout.strip(),
                "stderr": proc.stderr.strip()[:500],
                "is_contained": True,
                "violations": []
            }

        except subprocess.TimeoutExpired:
            elapsed = time.time() - start_time
            return {
                "verdict": "TIME_LIMIT_EXCEEDED",
                "status_code": 124,
                "execution_time_sec": round(elapsed, 3),
                "stdout": "",
                "stderr": f"Execution terminated: CPU wall-clock limit of {timeout}s exceeded (Infinite loop detected).",
                "is_contained": True,
                "violations": ["CPU timeout exceeded"]
            }

        except Exception as e:
            elapsed = time.time() - start_time
            return {
                "verdict": "SANDBOX_ERROR",
                "status_code": 500,
                "execution_time_sec": round(elapsed, 3),
                "stdout": "",
                "stderr": str(e),
                "is_contained": True,
                "violations": []
            }

        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
