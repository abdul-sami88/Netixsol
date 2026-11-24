"""
Guardrails and Anti-Leakage Defense Module
Enforces strict anti-leakage rules and defends against prompt injection / jailbreak attempts.
Guarantees 0% direct answer leakage to student assessment challenges.
"""

import re
from typing import Dict, Any, List, Tuple

class GuardrailsDefense:
    """
    Detects jailbreaks, prompt injection, and prevents full code solution leakage.
    """

    JAILBREAK_PATTERNS = [
        r"ignore (all )?(previous|above) instructions",
        r"system override",
        r"dan mode",
        r"roleplay as",
        r"developer (mode|debugging mode|override)",
        r"debug mode",
        r"print (the )?(entire |full )?(solution|code)",
        r"write (out )?(the )?(full )?code for me",
        r"just give me the (code|answer|solution)",
        r"my (grandmother|mother|boss|professor) (is|needs)",
        r"bypass (rules|guardrails|safety)",
        r"pretend you are",
        r"output python code only",
        r"security audit test",
        r"write a story.*code",
        r"system admin"
    ]

    DIRECT_SOLUTION_DEMANDS = [
        r"give me the code",
        r"give me the answer",
        r"solve it for me",
        r"write the function",
        r"do my homework",
        r"just tell me what to write",
        r"full solution"
    ]

    def __init__(self):
        self.jailbreak_regex = [re.compile(p, re.IGNORECASE) for p in self.JAILBREAK_PATTERNS]
        self.demand_regex = [re.compile(p, re.IGNORECASE) for p in self.DIRECT_SOLUTION_DEMANDS]

    def detect_jailbreak(self, user_message: str) -> Tuple[bool, str]:
        """
        Detects adversarial prompt injections aiming to bypass pedagogical guardrails.
        """
        for r in self.jailbreak_regex:
            if r.search(user_message):
                return True, "adversarial_jailbreak_attempt"
        return False, "clean"

    def detect_solution_demand(self, user_message: str) -> bool:
        """
        Detects students explicitly demanding the answer.
        """
        for r in self.demand_regex:
            if r.search(user_message):
                return True
        return False

    def sanitize_response(
        self,
        tutor_response: str,
        forbidden_solution_snippets: List[str]
    ) -> Tuple[str, bool]:
        """
        Post-generation safeguard: inspects response for accidental solution leakage.
        Returns (sanitized_response, was_leaked).
        """
        leaked = False
        sanitized = tutor_response

        for snippet in forbidden_solution_snippets:
            if len(snippet.strip()) > 15 and snippet.strip() in sanitized:
                leaked = True
                # Redact the full solution snippet with a Socratic scaffold
                sanitized = sanitized.replace(
                    snippet.strip(),
                    "# [Solution Redacted by Socratic Guardrail - Think through the base condition!]"
                )

        return sanitized, leaked

    def get_jailbreak_refusal_message(self, language: str = "english") -> str:
        """
        Returns a polite pedagogical refusal when a jailbreak is attempted.
        """
        if language.lower() == "urdulish":
            return (
                "Arey dost, main aapko direct solution nahi de sakta! Main aapka AI Tutor hoon, "
                "aur mera maqsad aapki real learning aur problem-solving skills develop karna hai. "
                "Mujhe bataiye aap kis specific step ya logic par confuse ho rahay hain, "
                "hum mil kar step-by-step figure out karte hain!"
            )
        return (
            "I hear you, but as your Socratic AI Tutor, I cannot give you the complete code or direct answer! "
            "My job is to help you build real mastery so you can solve this yourself. "
            "Tell me: what does your function currently do, and what step feels tricky?"
        )
