"""
Socratic Hint Ladder Module
Implements a 4-tier pedagogical guidance ladder:
1. Guiding Question -> 2. Concept Pointer -> 3. Partial Hint -> 4. Similar Example
Guarantees the tutor NEVER hands over the solution.
"""

from typing import Dict, Any, List, Optional

class SocraticHintLadder:
    """
    Progressive scaffolding ladder providing graduated assistance.
    """

    HINT_LEVELS = {
        1: "Guiding Question",
        2: "Concept Pointer",
        3: "Partial Scaffold",
        4: "Similar Worked Example"
    }

    # Curated pedagogical ladders for core Python stumbling blocks
    LADDER_TEMPLATES = {
        "recursion": {
            1: {
                "english": "Every recursive function needs to know when to stop. What is the simplest possible input for this problem that you can answer immediately without any further calculation?",
                "urdulish": "Har recursive function ko aik stopping point chahiye hota hai. Socho sab se chota ya simplest input kya ho sakta hai jiska answer tum bina kisi mazeed calculation ke foran de sakte ho?"
            },
            2: {
                "english": "Take a look at Lesson 8 on Recursion. Remember the two golden rules: (1) The Base Case (the exit condition) and (2) The Recursive Step (calling the function with a smaller subproblem). Which of these two is currently missing or misfiring in your code?",
                "urdulish": "Lesson 8 ka concept yaad karein: Recursion ke 2 ahem rules hain: (1) Base Case (rukne ki condition) aur (2) Recursive Step (function ko chotay input ke sath call karna). Aapke code mein in dono mein se konsi cheez ghalat ho rahi hai?"
            },
            3: {
                "english": "Here is the structural skeleton:\n```python\ndef solve(n):\n    if <base_condition>:      # e.g., when n is down to 0 or 1\n        return <base_value>   # direct answer\n    else:\n        return <operation>(n, solve(n - 1)) # step towards base case\n```\nWhat should `<base_condition>` be for your specific task?",
                "urdulish": "Yeh structural framework dekhein:\n```python\ndef solve(n):\n    if <base_condition>:      # misal ke tor par jab n chota ho jaye\n        return <base_value>   # direct jawab\n    else:\n        return <operation>(n, solve(n - 1)) # base case ki taraf qadam\n```\nAapke task ke mutabiq `<base_condition>` kya honi chahiye?"
            },
            4: {
                "english": "Here is an isomorphic example of calculating a countdown list using recursion:\n```python\ndef countdown(n):\n    if n <= 0:\n        return []\n    return [n] + countdown(n - 1)\n```\nNotice how `countdown(n-1)` shrinks the input until it hits `0`. How can you apply this same shrinking logic to your problem?",
                "urdulish": "Yeh similar example dekhein jahan hum countdown list banate hain:\n```python\ndef countdown(n):\n    if n <= 0:\n        return []\n    return [n] + countdown(n - 1)\n```\nDekhein har bar `n - 1` input ko chota kar raha hai jab tak 0 na aa jaye. Yehi shrinking pattern aap apne problem par kaisay laga saktay hain?"
            }
        },
        "while_loops": {
            1: {
                "english": "A while loop keeps running as long as its condition is True. What variable in your condition needs to change inside the loop so the condition eventually turns False?",
                "urdulish": "While loop tab tak chalta hai jab tak condition True rehti hai. Loop ke andar aisi konsi variable hai jisko change hona chahiye taake loop kabhi stop bhi ho sake?"
            },
            2: {
                "english": "Check Lesson 3 on Loops. When a loop variable is never updated inside the loop body, Python gets trapped in an infinite loop. Are you incrementing or decrementing your loop counter?",
                "urdulish": "Lesson 3 mein infinite loops ka section yaad karein. Agar loop ke andar counter update na ho, to code crash ho jata hai. Kya aap apne counter variable ko increment/decrement kar rahay hain?"
            },
            3: {
                "english": "Think of the loop structure:\n```python\ncounter = 0\nwhile counter < limit:\n    # do action\n    counter += 1  # essential step\n```\nCheck where your update statement is placed.",
                "urdulish": "Loop ka structure dekhein: har iteration ke end par `counter += 1` jaisa step hona zaroori hai. Kya aapka update step if block ke andar chupa hua to nahi?"
            },
            4: {
                "english": "Here is an example that accumulates sum of numbers safely:\n```python\ntotal, i = 0, 1\nwhile i <= 5:\n    total += i\n    i += 1\n```\nCompare this with your loop: how does `i` guarantee termination?",
                "urdulish": "Yeh safe accumulator example dekhein: `i += 1` har step par loop ko boundary ki taraf le jata hai. Aapke code mein stopping condition kaisay achieve hogi?"
            }
        },
        "functions_def": {
            1: {
                "english": "Is your code printing the result to the screen with `print()`, or returning it to the caller with `return`? What happens if another variable tries to store the result?",
                "urdulish": "Aapka code `print()` se console par show kar raha hai ya `return` se value wapis bhej raha hai? Agar caller function ke result ko save karna chahay to kya milega?"
            },
            2: {
                "english": "Remember the fundamental distinction from Lesson 4: `print()` is a display side-effect that produces `None`, while `return` hands the computed object back so other functions can use it.",
                "urdulish": "Lesson 4 ka rule: `print()` sirf screen par dikhata hai aur `None` deta hai, jabkay `return` asal value caller ko return karta hai taake agla code usay use kar sakay."
            },
            3: {
                "english": "Skeleton comparison:\n```python\ndef calculate(x):\n    result = x * 2\n    return result  # not print(result)!\n```\nWhere is your return statement located?",
                "urdulish": "Skeleton dekhein: `return result` hona chahiye, `print` nahi. Check karein ke aapka return statement function ke indentation ke andar hai ya bahar?"
            },
            4: {
                "english": "Here is an example:\n```python\ndef double(n):\n    return n * 2\n\nans = double(5) # ans now holds 10\n```\nHow can you use this pattern to return your computed output?",
                "urdulish": "Yeh example dekhein: `ans = double(5)` karne se 10 save ho jata hai. Aap apne function mein calculation ko kaisay return karengay?"
            }
        }
    }

    def get_ladder_step(
        self,
        concept_id: str,
        rung: int,
        language: str = "english"
    ) -> Dict[str, Any]:
        """
        Retrieves the Socratic hint for the requested rung (1 to 4).
        """
        rung = max(1, min(4, rung))
        lang_key = "urdulish" if language.lower() == "urdulish" else "english"

        templates = self.LADDER_TEMPLATES.get(concept_id, self.LADDER_TEMPLATES["recursion"])
        hint_text = templates[rung][lang_key]

        return {
            "rung": rung,
            "rung_name": self.HINT_LEVELS[rung],
            "hint_text": hint_text,
            "never_gives_solution": True
        }
