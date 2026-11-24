"""
Question Builder Module
Constructs 30 newly authored assessment questions:
- MCQs with misconception-annotated distractors
- Short Answer output/syntax predictions
- Coding tasks with starter code and test cases
"""

from typing import Dict, Any, List

class QuestionBuilder:
    """
    Synthesizes rich questions across Bloom's levels with explicit misconception mapping.
    """

    @staticmethod
    def build_all_candidate_questions() -> List[Dict[str, Any]]:
        """
        Builds 30 distinct questions covering recursion, functions, loops, and data structures.
        """
        questions = []

        # --- MCQs WITH MISCONCEPTION-BASED DISTRACTORS (12 items) ---
        mcq_items = [
            {
                "id": "GEN_MCQ_01",
                "type": "mcq",
                "concept_id": "recursion",
                "difficulty": 3,
                "blooms_level": "Analyzing",
                "prompt": "Consider the following recursive function:\n```python\ndef mystery(n):\n    if n == 0:\n        return 0\n    return n + mystery(n - 2)\n```\nWhat occurs when evaluating `mystery(5)` in standard Python?",
                "options": {
                    "A": "RecursionError: maximum recursion depth exceeded (infinite recursion).",
                    "B": "Returns 9 (5 + 3 + 1).",
                    "C": "Returns 0.",
                    "D": "Returns 15 (5 + 4 + 3 + 2 + 1)."
                },
                "correct_answer": "A",
                "explanation": "Since n decreases by 2 on each step (5 -> 3 -> 1 -> -1 -> -3...), it skips n == 0 entirely and recurses infinitely until RecursionError.",
                "distractor_misconceptions": {
                    "B": "Student assumes Python automatically stops at negative numbers or converts n == 0 to n <= 0.",
                    "C": "Student assumes base case return 0 overrides the entire sum calculation.",
                    "D": "Student assumes n decreases by 1 rather than by 2."
                }
            },
            {
                "id": "GEN_MCQ_02",
                "type": "mcq",
                "concept_id": "recursion",
                "difficulty": 4,
                "blooms_level": "Evaluating",
                "prompt": "Why is the base case `if n <= 1: return 1` safer than `if n == 1: return 1` in a recursive factorial function?",
                "options": {
                    "A": "It properly handles 0! = 1 and prevents infinite recursion if called with 0 or negative integers.",
                    "B": "It allows Python's compiler to optimize tail recursion into iterative assembly.",
                    "C": "It doubles the maximum recursion limit in sys.getrecursionlimit().",
                    "D": "It forces n to convert automatically from float to int."
                },
                "correct_answer": "A",
                "explanation": "Factorial of 0 is mathematically 1. Testing n <= 1 prevents infinite recursion for n = 0 or negative edge cases.",
                "distractor_misconceptions": {
                    "B": "Student assumes Python supports automatic tail call elimination (CPython does not).",
                    "C": "Student confuses base case logic with runtime recursion stack limits.",
                    "D": "Student assumes comparison operators cast numeric types."
                }
            },
            {
                "id": "GEN_MCQ_03",
                "type": "mcq",
                "concept_id": "functions_def",
                "difficulty": 2,
                "blooms_level": "Understanding",
                "prompt": "What is printed by the following code?\n```python\ndef greet(name):\n    print(f'Hello {name}')\n\nval = greet('Ali')\nprint(val)\n```",
                "options": {
                    "A": "Hello Ali\nNone",
                    "B": "Hello Ali\nHello Ali",
                    "C": "Hello Ali\n'Ali'",
                    "D": "None\nHello Ali"
                },
                "correct_answer": "A",
                "explanation": "greet() prints to the console but lacks a return statement, so it implicitly returns None. Thus val holds None.",
                "distractor_misconceptions": {
                    "B": "Print vs Return confusion: student assumes printing assigns the printed string to val.",
                    "C": "Student assumes the argument 'Ali' is returned by default.",
                    "D": "Student assumes assignment runs before function execution."
                }
            },
            {
                "id": "GEN_MCQ_04",
                "type": "mcq",
                "concept_id": "functions_def",
                "difficulty": 3,
                "blooms_level": "Analyzing",
                "prompt": "What is the output of running this code?\n```python\ndef add_item(item, box=[]):\n    box.append(item)\n    return box\n\nprint(add_item('apple'))\nprint(add_item('banana'))\n```",
                "options": {
                    "A": "['apple']\n['apple', 'banana']",
                    "B": "['apple']\n['banana']",
                    "C": "['apple']\n['apple']",
                    "D": "['banana']\n['apple', 'banana']"
                },
                "correct_answer": "A",
                "explanation": "Default arguments are evaluated once when the function is defined. The mutable list box is shared across all subsequent calls.",
                "distractor_misconceptions": {
                    "B": "Mutable default misconception: student assumes box=[] re-instantiates as an empty list on each call.",
                    "C": "Student assumes the function cannot be called more than once.",
                    "D": "Student assumes subsequent calls overwrite previous list references."
                }
            },
            {
                "id": "GEN_MCQ_05",
                "type": "mcq",
                "concept_id": "while_loops",
                "difficulty": 2,
                "blooms_level": "Applying",
                "prompt": "What is the final value of x after this loop completes?\n```python\nx = 1\nwhile x < 8:\n    x *= 2\n```",
                "options": {
                    "A": "8",
                    "B": "4",
                    "C": "16",
                    "D": "7"
                },
                "correct_answer": "A",
                "explanation": "x takes values 1 -> 2 -> 4 -> 8. When x = 8, the condition 8 < 8 evaluates to False, terminating the loop.",
                "distractor_misconceptions": {
                    "B": "Student assumes loop terminates before reaching the boundary multiplier.",
                    "C": "Student assumes the loop executes one additional time after reaching 8.",
                    "D": "Student confuses while condition with exclusive range upper bound."
                }
            },
            {
                "id": "GEN_MCQ_06",
                "type": "mcq",
                "concept_id": "variable_scope",
                "difficulty": 3,
                "blooms_level": "Analyzing",
                "prompt": "What is printed?\n```python\nx = 10\ndef modify():\n    x = 20\nmodify()\nprint(x)\n```",
                "options": {
                    "A": "10",
                    "B": "20",
                    "C": "None",
                    "D": "UnboundLocalError"
                },
                "correct_answer": "A",
                "explanation": "Assigning x = 20 creates a local variable inside modify(). The global x remains 10.",
                "distractor_misconceptions": {
                    "B": "Scope shadowing misconception: student assumes local reassignment alters the global variable.",
                    "C": "Student confuses variable assignment with function return.",
                    "D": "Student assumes reading and writing x in separate scopes raises UnboundLocalError."
                }
            },
            {
                "id": "GEN_MCQ_07",
                "type": "mcq",
                "concept_id": "lists",
                "difficulty": 2,
                "blooms_level": "Understanding",
                "prompt": "What does `nums = [1, 2, 3]; copy_nums = nums; copy_nums.append(4); print(nums)` print?",
                "options": {
                    "A": "[1, 2, 3, 4]",
                    "B": "[1, 2, 3]",
                    "C": "None",
                    "D": "TypeError"
                },
                "correct_answer": "A",
                "explanation": "Assignment binds a new reference pointing to the same list object in memory. Mutating copy_nums mutates nums.",
                "distractor_misconceptions": {
                    "B": "Pass-by-value misconception: student assumes assignment creates an independent copy.",
                    "C": "Student confuses in-place append return with list value.",
                    "D": "Student assumes appending to an alias raises an error."
                }
            },
            {
                "id": "GEN_MCQ_08",
                "type": "mcq",
                "concept_id": "dictionaries",
                "difficulty": 2,
                "blooms_level": "Applying",
                "prompt": "What is the result of `data = {'a': 1}; print(data.get('b', 5))`?",
                "options": {
                    "A": "5",
                    "B": "KeyError: 'b'",
                    "C": "None",
                    "D": "1"
                },
                "correct_answer": "A",
                "explanation": "dict.get(key, default) safely returns default (5) when key does not exist.",
                "distractor_misconceptions": {
                    "B": "Student confuses .get() with direct subscript indexing data['b'].",
                    "C": "Student assumes .get() always returns None on missing key regardless of default.",
                    "D": "Student assumes first dictionary value is returned."
                }
            },
            {
                "id": "GEN_MCQ_09",
                "type": "mcq",
                "concept_id": "recursion",
                "difficulty": 3,
                "blooms_level": "Analyzing",
                "prompt": "In recursive Fibonacci `def fib(n): return n if n <= 1 else fib(n-1) + fib(n-2)`, what is the time complexity without memoization?",
                "options": {
                    "A": "O(2^n) - Exponential due to duplicate subproblems in the recursion tree.",
                    "B": "O(n) - Linear because n decreases by 1.",
                    "C": "O(n^2) - Quadratic due to two calls.",
                    "D": "O(log n) - Logarithmic tree traversal."
                },
                "correct_answer": "A",
                "explanation": "Each call branches into two recursive calls, creating a binary recursion tree of depth n with ~2^n total nodes.",
                "distractor_misconceptions": {
                    "B": "Student assumes recursion is linear whenever parameter decrements by 1.",
                    "C": "Student confuses branching factor with nested loop iterations.",
                    "D": "Student confuses branching with binary search halving."
                }
            },
            {
                "id": "GEN_MCQ_10",
                "type": "mcq",
                "concept_id": "logical_operators",
                "difficulty": 2,
                "blooms_level": "Analyzing",
                "prompt": "What does `print([] or 'Python')` output in Python?",
                "options": {
                    "A": "'Python'",
                    "B": "True",
                    "C": "[]",
                    "D": "False"
                },
                "correct_answer": "A",
                "explanation": "In Python, 'or' returns the first truthy operand. [] is falsy, so 'Python' is returned.",
                "distractor_misconceptions": {
                    "B": "Student assumes logical operators in Python always cast and return bool True/False.",
                    "C": "Student assumes the first operand is always returned.",
                    "D": "Student assumes empty list forces the whole expression to evaluate to False."
                }
            },
            {
                "id": "GEN_MCQ_11",
                "type": "mcq",
                "concept_id": "range_function",
                "difficulty": 2,
                "blooms_level": "Understanding",
                "prompt": "What is the length of `list(range(5, 15, 3))`?",
                "options": {
                    "A": "4 (values 5, 8, 11, 14)",
                    "B": "5 (values 5, 8, 11, 14, 17)",
                    "C": "3 (values 5, 8, 11)",
                    "D": "10"
                },
                "correct_answer": "A",
                "explanation": "The progression is 5, 8, 11, 14 (17 >= 15 so it is excluded). Length is 4.",
                "distractor_misconceptions": {
                    "B": "Student assumes step includes boundary overshoot.",
                    "C": "Student assumes stop value 15 is excluded so 14 is dropped.",
                    "D": "Student assumes length is stop - start."
                }
            },
            {
                "id": "GEN_MCQ_12",
                "type": "mcq",
                "concept_id": "break_continue",
                "difficulty": 2,
                "blooms_level": "Applying",
                "prompt": "What is printed?\n```python\nfor i in range(4):\n    if i == 2:\n        continue\n    print(i, end=' ')\n```",
                "options": {
                    "A": "0 1 3 ",
                    "B": "0 1 ",
                    "C": "0 1 2 3 ",
                    "D": "3 "
                },
                "correct_answer": "A",
                "explanation": "continue skips the remainder of iteration i=2 and advances to i=3.",
                "distractor_misconceptions": {
                    "B": "Student confuses continue with break (assuming it terminates the loop).",
                    "C": "Student assumes continue has no effect.",
                    "D": "Student assumes continue skips all prior iterations."
                }
            }
        ]
        questions.extend(mcq_items)

        # --- SHORT ANSWER QUESTIONS (9 items) ---
        sa_items = [
            {
                "id": "GEN_SA_01",
                "type": "short_answer",
                "concept_id": "recursion",
                "difficulty": 3,
                "blooms_level": "Analyzing",
                "prompt": "Predict the return value of `power(2, 3)` given:\n```python\ndef power(b, e):\n    if e == 0: return 1\n    return b * power(b, e - 1)\n```",
                "correct_answer": "8",
                "explanation": "Computes 2^3: 2 * (2 * (2 * 1)) = 8."
            },
            {
                "id": "GEN_SA_02",
                "type": "short_answer",
                "concept_id": "recursion",
                "difficulty": 3,
                "blooms_level": "Understanding",
                "prompt": "What built-in Python exception is raised when a recursive function lacks a base case?",
                "correct_answer": "RecursionError",
                "explanation": "Python raises RecursionError when the maximum call stack depth (default 1000) is exceeded."
            },
            {
                "id": "GEN_SA_03",
                "type": "short_answer",
                "concept_id": "functions_def",
                "difficulty": 2,
                "blooms_level": "Understanding",
                "prompt": "What is the return value of a Python function that finishes execution without reaching a return statement?",
                "correct_answer": "None",
                "explanation": "Functions without explicit return implicitly return None."
            },
            {
                "id": "GEN_SA_04",
                "type": "short_answer",
                "concept_id": "while_loops",
                "difficulty": 2,
                "blooms_level": "Applying",
                "prompt": "How many times does 'Hi' print in the following snippet?\n```python\nc = 5\nwhile c > 2:\n    print('Hi')\n    c -= 1\n```",
                "correct_answer": "3",
                "explanation": "Executes for c = 5, 4, 3 (when c = 2, 2 > 2 is False). Total 3 times."
            },
            {
                "id": "GEN_SA_05",
                "type": "short_answer",
                "concept_id": "lists",
                "difficulty": 2,
                "blooms_level": "Applying",
                "prompt": "Given `lst = [10, 20, 30, 40]`, what does `lst.pop(1)` return?",
                "correct_answer": "20",
                "explanation": "pop(1) removes and returns the element at index 1, which is 20."
            },
            {
                "id": "GEN_SA_06",
                "type": "short_answer",
                "concept_id": "dictionaries",
                "difficulty": 2,
                "blooms_level": "Understanding",
                "prompt": "What is the average time complexity of looking up a key in a Python dictionary? (Answer in Big-O notation, e.g. O(1), O(n))",
                "correct_answer": "O(1)",
                "explanation": "Python dictionaries use hash tables, achieving O(1) average lookup complexity."
            },
            {
                "id": "GEN_SA_07",
                "type": "short_answer",
                "concept_id": "type_casting",
                "difficulty": 2,
                "blooms_level": "Understanding",
                "prompt": "What is the boolean evaluation of `bool('False')` in Python? (True or False)",
                "correct_answer": "True",
                "explanation": "Any non-empty string is truthy in Python, regardless of its textual content."
            },
            {
                "id": "GEN_SA_08",
                "type": "short_answer",
                "concept_id": "recursion",
                "difficulty": 4,
                "blooms_level": "Analyzing",
                "prompt": "What is the maximum recursion depth limit typically set to in standard CPython? (Enter integer number)",
                "correct_answer": "1000",
                "explanation": "sys.getrecursionlimit() is 1000 by default in standard Python."
            },
            {
                "id": "GEN_SA_09",
                "type": "short_answer",
                "concept_id": "variable_scope",
                "difficulty": 3,
                "blooms_level": "Remembering",
                "prompt": "What Python keyword is used inside a function to allow modifying a variable in the module-level namespace?",
                "correct_answer": "global",
                "explanation": "The 'global' keyword explicitly declares a variable as referencing the global namespace."
            }
        ]
        questions.extend(sa_items)

        # --- CODING QUESTIONS WITH EXECUTABLE TEST CASES (9 items) ---
        coding_items = [
            {
                "id": "GEN_CODE_01",
                "type": "coding",
                "concept_id": "recursion",
                "difficulty": 3,
                "blooms_level": "Applying",
                "prompt": "Write a recursive function `recursive_sum(n)` that takes a positive integer n and returns the sum of all integers from 1 up to n. (e.g. recursive_sum(4) -> 1 + 2 + 3 + 4 = 10). Base case: when n <= 1, return n.",
                "starter_code": "def recursive_sum(n):\n    # Write your recursive code here\n    pass",
                "solution_code": "def recursive_sum(n):\n    if n <= 1:\n        return n\n    return n + recursive_sum(n - 1)",
                "test_cases": [
                    {"input": "recursive_sum(1)", "expected": 1},
                    {"input": "recursive_sum(4)", "expected": 10},
                    {"input": "recursive_sum(10)", "expected": 55}
                ],
                "explanation": "Base case n <= 1 returns n. Recursive step adds n to recursive_sum(n - 1)."
            },
            {
                "id": "GEN_CODE_02",
                "type": "coding",
                "concept_id": "recursion",
                "difficulty": 3,
                "blooms_level": "Applying",
                "prompt": "Write a recursive function `recursive_reverse(s)` that takes a string s and returns the string reversed. Base case: if length of s is <= 1, return s.",
                "starter_code": "def recursive_reverse(s):\n    pass",
                "solution_code": "def recursive_reverse(s):\n    if len(s) <= 1:\n        return s\n    return s[-1] + recursive_reverse(s[:-1])",
                "test_cases": [
                    {"input": "recursive_reverse('cat')", "expected": "tac"},
                    {"input": "recursive_reverse('hello')", "expected": "olleh"},
                    {"input": "recursive_reverse('a')", "expected": "a"}
                ],
                "explanation": "Base case len(s) <= 1 returns s. Recursive step appends last character to reversed prefix."
            },
            {
                "id": "GEN_CODE_03",
                "type": "coding",
                "concept_id": "recursion",
                "difficulty": 4,
                "blooms_level": "Creating",
                "prompt": "Write a recursive function `count_occurrences(lst, target)` that counts how many times `target` appears in the list `lst` without using loop or lst.count().",
                "starter_code": "def count_occurrences(lst, target):\n    pass",
                "solution_code": "def count_occurrences(lst, target):\n    if not lst:\n        return 0\n    match = 1 if lst[0] == target else 0\n    return match + count_occurrences(lst[1:], target)",
                "test_cases": [
                    {"input": "count_occurrences([1, 2, 3, 2, 2], 2)", "expected": 3},
                    {"input": "count_occurrences([1, 2, 3], 5)", "expected": 0},
                    {"input": "count_occurrences([], 1)", "expected": 0}
                ],
                "explanation": "Base case not lst returns 0. Evaluates head element and recurses on tail lst[1:]."
            },
            {
                "id": "GEN_CODE_04",
                "type": "coding",
                "concept_id": "functions_def",
                "difficulty": 2,
                "blooms_level": "Applying",
                "prompt": "Write a function `safe_divide(a, b)` that returns a / b rounded to 2 decimals, or returns None if b == 0.",
                "starter_code": "def safe_divide(a, b):\n    pass",
                "solution_code": "def safe_divide(a, b):\n    if b == 0:\n        return None\n    return round(a / b, 2)",
                "test_cases": [
                    {"input": "safe_divide(10, 2)", "expected": 5.0},
                    {"input": "safe_divide(10, 0)", "expected": None},
                    {"input": "safe_divide(7, 3)", "expected": 2.33}
                ],
                "explanation": "Guards against ZeroDivisionError by checking b == 0 before performing division."
            },
            {
                "id": "GEN_CODE_05",
                "type": "coding",
                "concept_id": "while_loops",
                "difficulty": 3,
                "blooms_level": "Applying",
                "prompt": "Write a function `collatz_steps(n)` that returns the number of steps required to reach 1 in the Collatz sequence (if n is even: n = n // 2; if n is odd: n = 3*n + 1). If n is initially 1, return 0.",
                "starter_code": "def collatz_steps(n):\n    pass",
                "solution_code": "def collatz_steps(n):\n    steps = 0\n    while n > 1:\n        if n % 2 == 0:\n            n = n // 2\n        else:\n            n = 3 * n + 1\n        steps += 1\n    return steps",
                "test_cases": [
                    {"input": "collatz_steps(1)", "expected": 0},
                    {"input": "collatz_steps(6)", "expected": 8},
                    {"input": "collatz_steps(2)", "expected": 1}
                ],
                "explanation": "Uses a while loop until n reaches 1, updating n according to parity rules and tallying steps."
            },
            {
                "id": "GEN_CODE_06",
                "type": "coding",
                "concept_id": "lists",
                "difficulty": 2,
                "blooms_level": "Applying",
                "prompt": "Write a function `deduplicate_preserve_order(items)` that returns a new list with duplicates removed while preserving their original first-occurrence order.",
                "starter_code": "def deduplicate_preserve_order(items):\n    pass",
                "solution_code": "def deduplicate_preserve_order(items):\n    seen = set()\n    res = []\n    for x in items:\n        if x not in seen:\n            seen.add(x)\n            res.append(x)\n    return res",
                "test_cases": [
                    {"input": "deduplicate_preserve_order([3, 1, 2, 1, 3, 4])", "expected": [3, 1, 2, 4]},
                    {"input": "deduplicate_preserve_order([])", "expected": []}
                ],
                "explanation": "Uses a tracking set for O(1) membership checks and an output list to maintain encounter order."
            },
            {
                "id": "GEN_CODE_07",
                "type": "coding",
                "concept_id": "dictionaries",
                "difficulty": 2,
                "blooms_level": "Applying",
                "prompt": "Write a function `invert_dictionary(d)` that swaps keys and values in a dictionary mapping unique keys to unique values.",
                "starter_code": "def invert_dictionary(d):\n    pass",
                "solution_code": "def invert_dictionary(d):\n    return {v: k for k, v in d.items()}",
                "test_cases": [
                    {"input": "invert_dictionary({'a': 1, 'b': 2})", "expected": {1: 'a', 2: 'b'}},
                    {"input": "invert_dictionary({})", "expected": {}}
                ],
                "explanation": "Dictionary comprehension swapping k and v across d.items()."
            },
            {
                "id": "GEN_CODE_08",
                "type": "coding",
                "concept_id": "recursion",
                "difficulty": 4,
                "blooms_level": "Creating",
                "prompt": "Write a recursive function `flatten_list(nested)` that flattens an arbitrarily nested list of integers into a single flat 1D list. e.g. [1, [2, [3, 4]], 5] -> [1, 2, 3, 4, 5].",
                "starter_code": "def flatten_list(nested):\n    pass",
                "solution_code": "def flatten_list(nested):\n    flat = []\n    for item in nested:\n        if isinstance(item, list):\n            flat.extend(flatten_list(item))\n        else:\n            flat.append(item)\n    return flat",
                "test_cases": [
                    {"input": "flatten_list([1, [2, [3, 4]], 5])", "expected": [1, 2, 3, 4, 5]},
                    {"input": "flatten_list([])", "expected": []},
                    {"input": "flatten_list([10, 20])", "expected": [10, 20]}
                ],
                "explanation": "Iterates elements; if element is a list, recursively flattens and extends; otherwise appends leaf item."
            },
            {
                "id": "GEN_CODE_09",
                "type": "coding",
                "concept_id": "functions_def",
                "difficulty": 3,
                "blooms_level": "Applying",
                "prompt": "Write a function `apply_transform(nums, func)` that returns a new list containing the result of applying the callable `func` to each element in `nums`.",
                "starter_code": "def apply_transform(nums, func):\n    pass",
                "solution_code": "def apply_transform(nums, func):\n    return [func(x) for x in nums]",
                "test_cases": [
                    {"input": "apply_transform([1, 2, 3], lambda x: x * 10)", "expected": [10, 20, 30]},
                    {"input": "apply_transform([], lambda x: x)", "expected": []}
                ],
                "explanation": "Higher order function demonstrating functional mapping over an iterable."
            }
        ]
        questions.extend(coding_items)

        return questions
