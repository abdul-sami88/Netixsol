"""
Test-Based Grading Engine
Executes student code against Visible, Hidden, and Efficiency scale tests inside SecureCodeSandbox.
Enforces partial credit, timeout limits, and asymptotic complexity checks (O(N) vs O(N^2)).
"""

import json
import time
from typing import Dict, Any, Optional
import os
import sys

# Ensure local imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from grading_sandbox.secure_sandbox import SecureCodeSandbox

TEST_HARNESS_TEMPLATE = """
import json
import time

def run_tests():
    report = {
        "visible_passed": 0,
        "visible_total": 2,
        "visible_score": 0.0,
        "hidden_passed": 0,
        "hidden_total": 3,
        "hidden_score": 0.0,
        "efficiency_passed": False,
        "efficiency_score": 0.0,
        "efficiency_time_sec": 0.0,
        "total_score": 0.0,
        "failed_test": None,
        "failed_reason": None
    }

    # Helper validator
    def check_res(got, exp, nums, target):
        if not isinstance(got, (list, tuple)) or len(got) != 2:
            return False, f"Expected a list of 2 indices, got {repr(got)}"
        i, j = sorted(got)
        if i < 0 or j >= len(nums):
            return False, f"Indices [{i}, {j}] out of bounds for array length {len(nums)}"
        if i == j:
            return False, f"Pointers must be distinct, but got identical index {i}"
        if nums[i] + nums[j] != target:
            return False, f"nums[{i}] + nums[{j}] = {nums[i]} + {nums[j]} = {nums[i] + nums[j]}, expected {target}"
        return True, ""

    try:
        # --- Visible Tests (40 pts) ---
        # V1: nums = [2, 7, 11, 15], target = 9 -> [0, 1]
        nums1, t1 = [2, 7, 11, 15], 9
        res1 = two_sum(nums1, t1)
        ok1, err1 = check_res(res1, [0, 1], nums1, t1)
        if ok1:
            report["visible_passed"] += 1
            report["visible_score"] += 20.0
        else:
            if not report["failed_test"]:
                report["failed_test"] = "Visible Test 1: [2, 7, 11, 15], target=9"
                report["failed_reason"] = err1

        # V2: nums = [3, 2, 4], target = 6 -> [1, 2]
        nums2, t2 = [3, 2, 4], 6
        res2 = two_sum(nums2, t2)
        ok2, err2 = check_res(res2, [1, 2], nums2, t2)
        if ok2:
            report["visible_passed"] += 1
            report["visible_score"] += 20.0
        else:
            if not report["failed_test"]:
                report["failed_test"] = "Visible Test 2: [3, 2, 4], target=6"
                report["failed_reason"] = err2

        # --- Hidden Correctness Tests (30 pts) ---
        # H1: Duplicates: nums = [3, 3], target = 6 -> [0, 1]
        nums3, t3 = [3, 3], 6
        res3 = two_sum(nums3, t3)
        ok3, err3 = check_res(res3, [0, 1], nums3, t3)
        if ok3:
            report["hidden_passed"] += 1
            report["hidden_score"] += 10.0
        else:
            if not report["failed_test"]:
                report["failed_test"] = "Hidden Test 1 (Duplicate Elements): [3, 3], target=6"
                report["failed_reason"] = err3

        # H2: Negative values: nums = [-1, -2, -3, -4, -5], target = -8 -> [2, 4]
        nums4, t4 = [-1, -2, -3, -4, -5], -8
        res4 = two_sum(nums4, t4)
        ok4, err4 = check_res(res4, [2, 4], nums4, t4)
        if ok4:
            report["hidden_passed"] += 1
            report["hidden_score"] += 10.0
        else:
            if not report["failed_test"]:
                report["failed_test"] = "Hidden Test 2 (Negative Numbers): [-1, -2, -3, -4, -5], target=-8"
                report["failed_reason"] = err4

        # H3: Zeros and Offset: nums = [0, 4, 3, 0], target = 0 -> [0, 3]
        nums5, t5 = [0, 4, 3, 0], 0
        res5 = two_sum(nums5, t5)
        ok5, err5 = check_res(res5, [0, 3], nums5, t5)
        if ok5:
            report["hidden_passed"] += 1
            report["hidden_score"] += 10.0
        else:
            if not report["failed_test"]:
                report["failed_test"] = "Hidden Test 3 (Zero Values): [0, 4, 3, 0], target=0"
                report["failed_reason"] = err5

        # --- Hidden Efficiency Scale Test (30 pts) ---
        # Generate N = 3,500 array. Target formed at end: idx 3480 and 3499
        N = 3500
        scale_nums = list(range(1, N + 1))
        scale_target = scale_nums[N - 20] + scale_nums[N - 1] # e.g. 3481 + 3500

        t_start = time.perf_counter()
        res_scale = two_sum(scale_nums, scale_target)
        t_elapsed = time.perf_counter() - t_start
        report["efficiency_time_sec"] = round(t_elapsed, 4)

        ok_scale, err_scale = check_res(res_scale, [N - 20, N - 1], scale_nums, scale_target)
        if ok_scale:
            # Efficiency threshold: O(N) finishes in < 0.03s. O(N^2) takes > 0.15s
            if t_elapsed <= 0.035:
                report["efficiency_passed"] = True
                report["efficiency_score"] = 30.0
            elif t_elapsed <= 0.10:
                report["efficiency_passed"] = True
                report["efficiency_score"] = 15.0
            else:
                # O(N^2) quadratic scale failure
                report["efficiency_passed"] = False
                report["efficiency_score"] = 0.0
                if not report["failed_test"]:
                    report["failed_test"] = f"Scale Efficiency Test (N={N})"
                    report["failed_reason"] = f"Runtime {t_elapsed:.3f}s exceeded linear time threshold (0.035s). Detected O(N^2) quadratic algorithm."
        else:
            report["efficiency_passed"] = False
            report["efficiency_score"] = 0.0
            if not report["failed_test"]:
                report["failed_test"] = f"Scale Efficiency Test (N={N})"
                report["failed_reason"] = err_scale

    except Exception as e:
        report["failed_test"] = "Runtime Error during execution"
        report["failed_reason"] = f"{type(e).__name__}: {str(e)}"

    report["total_score"] = report["visible_score"] + report["hidden_score"] + report["efficiency_score"]
    print("AUTOGRADER_JSON_OUTPUT_START")
    print(json.dumps(report))
    print("AUTOGRADER_JSON_OUTPUT_END")

if __name__ == "__main__":
    run_tests()
"""

class CodeTestRunner:
    """
    Executes unit tests against student code submissions safely.
    """

    def __init__(self, sandbox: Optional[SecureCodeSandbox] = None):
        self.sandbox = sandbox or SecureCodeSandbox(timeout_sec=2.0)

    def grade_submission(self, code_str: str) -> Dict[str, Any]:
        """
        Runs code in sandbox with test harness. Parses test results and computes scores.
        """
        raw_result = self.sandbox.execute_code(code_str, test_harness_str=TEST_HARNESS_TEMPLATE)

        verdict = raw_result.get("verdict")
        exec_time = raw_result.get("execution_time_sec", 0.0)

        # Handle Security Violations
        if verdict == "SECURITY_VIOLATION":
            return {
                "autograder_score": 0.0,
                "visible_score": 0.0,
                "hidden_score": 0.0,
                "efficiency_score": 0.0,
                "verdict": "SECURITY_VIOLATION",
                "execution_time_sec": exec_time,
                "failed_test": "Security Screening",
                "failed_reason": "; ".join(raw_result.get("violations", ["Restricted operation"]))
            }

        # Handle Infinite Loops / Time Limit Exceeded
        if verdict == "TIME_LIMIT_EXCEEDED":
            return {
                "autograder_score": 0.0,
                "visible_score": 0.0,
                "hidden_score": 0.0,
                "efficiency_score": 0.0,
                "verdict": "TIME_LIMIT_EXCEEDED",
                "execution_time_sec": exec_time,
                "failed_test": "Execution Timeout",
                "failed_reason": f"Execution exceeded {self.sandbox.timeout_sec}s timeout limit. Infinite loop detected."
            }

        # Parse JSON output from sandbox stdout
        stdout = raw_result.get("stdout", "")
        if "AUTOGRADER_JSON_OUTPUT_START" in stdout:
            try:
                json_str = stdout.split("AUTOGRADER_JSON_OUTPUT_START")[1].split("AUTOGRADER_JSON_OUTPUT_END")[0].strip()
                parsed = json.loads(json_str)

                return {
                    "autograder_score": float(parsed.get("total_score", 0.0)),
                    "visible_score": float(parsed.get("visible_score", 0.0)),
                    "hidden_score": float(parsed.get("hidden_score", 0.0)),
                    "efficiency_score": float(parsed.get("efficiency_score", 0.0)),
                    "visible_passed": int(parsed.get("visible_passed", 0)),
                    "hidden_passed": int(parsed.get("hidden_passed", 0)),
                    "efficiency_passed": bool(parsed.get("efficiency_passed", False)),
                    "efficiency_time_sec": float(parsed.get("efficiency_time_sec", 0.0)),
                    "verdict": "ACCEPTED" if parsed.get("total_score") == 100.0 else "PARTIAL_CREDIT" if parsed.get("total_score", 0) > 0 else "WRONG_ANSWER",
                    "execution_time_sec": exec_time,
                    "failed_test": parsed.get("failed_test"),
                    "failed_reason": parsed.get("failed_reason")
                }
            except Exception as e:
                pass

        # Syntax error or unhandled runtime crash
        stderr = raw_result.get("stderr", "")
        return {
            "autograder_score": 0.0,
            "visible_score": 0.0,
            "hidden_score": 0.0,
            "efficiency_score": 0.0,
            "verdict": "RUNTIME_ERROR" if "SyntaxError" not in stderr else "SYNTAX_ERROR",
            "execution_time_sec": exec_time,
            "failed_test": "Code Compilation / Execution",
            "failed_reason": stderr[:300] if stderr else "Program exited prematurely without test report."
        }
