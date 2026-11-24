"""
Misconception Synthesizer for Diagnostic Question Generation
Models specific cognitive mental bugs and generates targeted distractors for multiple choice items.
"""

from typing import Dict, Any, List

class MisconceptionSynthesizer:
    """
    Catalogues documented cognitive misconceptions in introductory Python
    and generates pedagogically plausible distractors.
    """

    MISCONCEPTIONS_CATALOG = {
        "recursion": [
            {
                "id": "REC_NO_BASE",
                "name": "Missing Base Case",
                "description": "Student assumes recursion terminates implicitly without an explicit conditional return, causing maximum recursion depth exceeded.",
                "buggy_reasoning": "The function keeps shrinking the number so it should stop on its own."
            },
            {
                "id": "REC_RETURN_MISSING",
                "name": "Missing Recursive Return",
                "description": "Student invokes recursive step without return keyword (e.g., `solve(n-1)` instead of `return solve(n-1)`), yielding None.",
                "buggy_reasoning": "Calling the function inside the body should automatically return the inner answer."
            },
            {
                "id": "REC_OFF_BY_ONE",
                "name": "Off-by-One Base Condition",
                "description": "Using n == 0 when n <= 0 is needed, or stopping at n == 1 for operations requiring n == 0, causing off-by-one errors.",
                "buggy_reasoning": "Factorial of 0 is undefined or 0, rather than 1."
            }
        ],
        "functions_def": [
            {
                "id": "FUNC_PRINT_VS_RETURN",
                "name": "Print vs Return Confusion",
                "description": "Student prints result inside function and assumes caller receives the value, instead of receiving None.",
                "buggy_reasoning": "Since I saw the number on the screen, the function must have outputted it to my variable."
            },
            {
                "id": "FUNC_MUTABLE_DEFAULT",
                "name": "Shared Mutable Default Argument",
                "description": "Using def append_item(x, lst=[]) expecting a fresh list on each call, leading to state persistence across invocations.",
                "buggy_reasoning": "Default arguments evaluate fresh every time the function is called."
            },
            {
                "id": "FUNC_LEGB_SHADOWING",
                "name": "Local Reassignment vs Global Mutation",
                "description": "Assigning to a variable inside function shadows module variable rather than modifying the outer scope.",
                "buggy_reasoning": "Assigning x = 10 inside changes the x I created outside."
            }
        ],
        "while_loops": [
            {
                "id": "LOOP_NO_INCREMENT",
                "name": "Infinite Loop via Unmodified Counter",
                "description": "Forgetting to update counter inside loop body.",
                "buggy_reasoning": "The while condition checks itself automatically."
            },
            {
                "id": "LOOP_EXCLUSIVE_BOUND",
                "name": "Inclusive vs Exclusive Condition",
                "description": "Using < instead of <= causing one fewer iteration than required.",
                "buggy_reasoning": "while i < 10 will run 10 times if i starts at 1."
            }
        ]
    }

    @classmethod
    def get_misconceptions(cls, concept_id: str) -> List[Dict[str, Any]]:
        """Returns documented misconceptions for concept."""
        return cls.MISCONCEPTIONS_CATALOG.get(concept_id, cls.MISCONCEPTIONS_CATALOG["recursion"])
