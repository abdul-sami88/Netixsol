"""
Written Conceptual Answers Dataset (30 Student Responses)
Covers 3 foundational Python concepts:
- Q1: Recursion, call stack frames, and RecursionError
- Q2: Time/space complexity of duplicate detection (nested loops vs hash set)
- Q3: Tuple immutability, hashability, and list comparison

Includes human grading marks from Grader 1 and Grader 2 across the 10-point rubric:
- Technical Correctness & Mechanism (0-4 pts)
- Edge Cases & Constraints (0-3 pts)
- Technical Clarity & Terminology (0-3 pts)
"""

from typing import List, Dict, Any

QUESTIONS = {
    "Q1": {
        "id": "Q1",
        "concept": "C17: Recursion & Call Stack",
        "prompt": "Explain how recursion uses the call stack and what causes a RecursionError in Python.",
        "max_score": 10
    },
    "Q2": {
        "id": "Q2",
        "concept": "C21: Complexity & Hash Sets",
        "prompt": "Compare the time and space complexity of finding duplicate elements in a list using nested loops versus using a hash set.",
        "max_score": 10
    },
    "Q3": {
        "id": "Q3",
        "concept": "C08: Tuples & Immutability",
        "prompt": "Why are tuples immutable in Python, and in what real-world scenarios should a programmer choose a tuple instead of a list?",
        "max_score": 10
    }
}

WRITTEN_RESPONSES: List[Dict[str, Any]] = [
    # --- Question 1: Recursion & Call Stack (Responses 1 to 10) ---
    {
        "id": "RESP-01",
        "question_id": "Q1",
        "student_id": "STU-2001",
        "response_text": (
            "When a recursive function calls itself, Python pushes a new stack frame onto the call stack. "
            "This frame stores the function's local variables, parameters, and the return address. "
            "Each nested call waits until the base case is reached, after which frames are unwound (popped) in LIFO order. "
            "A RecursionError is triggered when the recursion depth exceeds Python's sys.getrecursionlimit() "
            "(typically 1,000 frames), usually caused by a missing base case or an argument that fails to converge toward it."
        ),
        "human_1_score": 10,
        "human_2_score": 10,
        "type": "Exemplary"
    },
    {
        "id": "RESP-02",
        "question_id": "Q1",
        "student_id": "STU-2002",
        "response_text": (
            "Recursion uses stack frames on the call stack. Every time the function calls itself, a frame is added. "
            "When the base case returns, frames pop off. If you forget a base case or make infinite calls, "
            "it exceeds the recursion limit and gives a RecursionError."
        ),
        "human_1_score": 9,
        "human_2_score": 9,
        "type": "Solid"
    },
    {
        "id": "RESP-03",
        "question_id": "Q1",
        "student_id": "STU-2003",
        "response_text": (
            "In Python, recursion puts calls in a stack. The top call finishes first and goes back. "
            "RecursionError happens when there are too many calls and memory fills up."
        ),
        "human_1_score": 7,
        "human_2_score": 7,
        "type": "Basic Correct"
    },
    {
        "id": "RESP-04",
        "question_id": "Q1",
        "student_id": "STU-2004",
        "response_text": (
            "Recursion is a programming technique where functions invoke themselves repeatedly. "
            "It is fundamental to computer science algorithms like quicksort and tree traversals. "
            "RecursionError occurs when the function repeats forever without stopping."
        ),
        "human_1_score": 6,
        "human_2_score": 5,
        "type": "Superficial"
    },
    {
        "id": "RESP-05",
        "question_id": "Q1",
        "student_id": "STU-2005",
        "response_text": (
            "Recursion utilizes the execution stack in the system kernel. Each invocation instantiates polymorphic "
            "computational state across the execution pipeline, synthesizing algorithmic state transformations. "
            "When an architectural overflow manifests in the runtime thread hierarchy, the quantum compiler emits "
            "a fatal RecursionError exception to preemptively isolate thread memory."
        ),
        "human_1_score": 2,
        "human_2_score": 3,
        "type": "Verbose Fluff / Pseudo-technical"
    },
    {
        "id": "RESP-06",
        "question_id": "Q1",
        "student_id": "STU-2006",
        "response_text": (
            "A function calls itself until done. If it doesn't stop, you get RecursionError."
        ),
        "human_1_score": 4,
        "human_2_score": 4,
        "type": "Ultra-brief"
    },
    {
        "id": "RESP-07",
        "question_id": "Q1",
        "student_id": "STU-2007",
        "response_text": (
            "Recursion stores variables in the heap memory. When you call a function recursively, "
            "Python dynamically reallocates garbage collection queues. If the heap runs out of RAM, "
            "it produces a RecursionError."
        ),
        "human_1_score": 2,
        "human_2_score": 2,
        "type": "Misconception (Heap vs Stack)"
    },
    {
        "id": "RESP-08",
        "question_id": "Q1",
        "student_id": "STU-2008",
        "response_text": (
            "Each recursive call adds a stack frame containing local variables to the call stack. "
            "If the recursion reaches the base case, the frames return and pop off. "
            "However, if the base case condition is faulty (e.g. n == 0 when n starts negative and decrements), "
            "the stack grows until Python's limit of 1000 frames is breached, throwing RecursionError."
        ),
        "human_1_score": 10,
        "human_2_score": 9,
        "type": "Exemplary with Edge Case"
    },
    {
        "id": "RESP-09",
        "question_id": "Q1",
        "student_id": "STU-2009",
        "response_text": (
            "RecursionError is just a syntax error caused by writing an invalid while loop inside a function."
        ),
        "human_1_score": 1,
        "human_2_score": 0,
        "type": "Completely Incorrect"
    },
    {
        "id": "RESP-10",
        "question_id": "Q1",
        "student_id": "STU-2010",
        "response_text": (
            "Recursion adds frames to the stack. A RecursionError happens when there is no base case, "
            "causing stack overflow beyond the recursion depth limit (1000)."
        ),
        "human_1_score": 8,
        "human_2_score": 8,
        "type": "Good Concise"
    },

    # --- Question 2: Complexity Comparison (Responses 11 to 20) ---
    {
        "id": "RESP-11",
        "question_id": "Q2",
        "student_id": "STU-2011",
        "response_text": (
            "Using nested loops compares every pair of elements, resulting in O(N^2) quadratic time complexity "
            "and O(1) auxiliary space since no extra data structures are allocated. "
            "In contrast, using a hash set enables O(1) average lookup per element as we iterate once through the list, "
            "yielding O(N) linear time complexity. The trade-off is O(N) auxiliary space to store unique elements. "
            "However, in the worst case with hash collisions, set lookups could degrade to O(N), but Python's SipHash keeps it O(1) in practice."
        ),
        "human_1_score": 10,
        "human_2_score": 10,
        "type": "Exemplary with Trade-off"
    },
    {
        "id": "RESP-12",
        "question_id": "Q2",
        "student_id": "STU-2012",
        "response_text": (
            "Nested loops take O(N^2) time because for each item you check all other items. Space is O(1). "
            "A hash set takes O(N) time because set lookups are O(1) on average. Space is O(N) for the set."
        ),
        "human_1_score": 9,
        "human_2_score": 9,
        "type": "Solid"
    },
    {
        "id": "RESP-13",
        "question_id": "Q2",
        "student_id": "STU-2013",
        "response_text": (
            "Nested loops are slower (O(n squared)) while hash set is faster (O(n)). "
            "Hash sets take more memory though."
        ),
        "human_1_score": 7,
        "human_2_score": 7,
        "type": "Basic Correct"
    },
    {
        "id": "RESP-14",
        "question_id": "Q2",
        "student_id": "STU-2014",
        "response_text": (
            "Algorithmic efficiency is critical in modern software engineering paradigms. When deploying dual iterative "
            "loops, the asymptotic trajectory expands exponentially across multidimensional iterations. "
            "Conversely, hashing utilizes deterministic key hashing vectors to optimize computational throughput. "
            "Therefore, hash sets exhibit superior synergistic runtime properties."
        ),
        "human_1_score": 3,
        "human_2_score": 3,
        "type": "Verbose Fluff / Pseudo-technical"
    },
    {
        "id": "RESP-15",
        "question_id": "Q2",
        "student_id": "STU-2015",
        "response_text": (
            "Nested loops take O(N) time and O(N) space. Hash set takes O(1) time and O(N^2) space."
        ),
        "human_1_score": 2,
        "human_2_score": 2,
        "type": "Inverted Complexity Error"
    },
    {
        "id": "RESP-16",
        "question_id": "Q2",
        "student_id": "STU-2016",
        "response_text": (
            "Nested loop: O(N^2) time, O(1) space. Hash set: O(N) time, O(N) space."
        ),
        "human_1_score": 8,
        "human_2_score": 8,
        "type": "Ultra-brief Accurate"
    },
    {
        "id": "RESP-17",
        "question_id": "Q2",
        "student_id": "STU-2017",
        "response_text": (
            "Nested loops take O(N log N) time because the computer has to sort the list first before comparing. "
            "Hash sets take O(N) time."
        ),
        "human_1_score": 4,
        "human_2_score": 4,
        "type": "Partial Misconception"
    },
    {
        "id": "RESP-18",
        "question_id": "Q2",
        "student_id": "STU-2018",
        "response_text": (
            "With nested loops, two pointers compare nums[i] and nums[j], taking N*(N-1)/2 operations which is O(N^2) time, "
            "with O(1) space. A set uses hashing for O(1) lookups, giving O(N) time overall, but requires O(N) extra memory. "
            "If memory is extremely constrained (e.g. embedded systems), nested loops or in-place sorting might be preferred."
        ),
        "human_1_score": 10,
        "human_2_score": 10,
        "type": "Exemplary with System Context"
    },
    {
        "id": "RESP-19",
        "question_id": "Q2",
        "student_id": "STU-2019",
        "response_text": (
            "Both methods have the exact same time complexity O(N), but nested loops are easier to read and debug."
        ),
        "human_1_score": 2,
        "human_2_score": 1,
        "type": "Incorrect"
    },
    {
        "id": "RESP-20",
        "question_id": "Q2",
        "student_id": "STU-2020",
        "response_text": (
            "Double loop checks every item against all others, so it takes quadratic O(n^2) time, using no extra space O(1). "
            "A set stores seen items, taking linear O(n) space and O(n) time."
        ),
        "human_1_score": 9,
        "human_2_score": 8,
        "type": "Good Concise"
    },

    # --- Question 3: Tuples & Immutability (Responses 21 to 30) ---
    {
        "id": "RESP-21",
        "question_id": "Q3",
        "student_id": "STU-2021",
        "response_text": (
            "Tuples are immutable in Python, meaning their elements cannot be modified, added, or removed after creation. "
            "This immutability ensures data integrity and allows tuples (containing only hashable elements) to be hashable, "
            "meaning they can serve as dictionary keys or set members, whereas lists cannot. "
            "Real-world scenarios: 1) Representing fixed records like geographic coordinates (lat, lon) or RGB values; "
            "2) Returning multiple values from functions; 3) Dictionary keys for multi-dimensional coordinates."
        ),
        "human_1_score": 10,
        "human_2_score": 10,
        "type": "Exemplary"
    },
    {
        "id": "RESP-22",
        "question_id": "Q3",
        "student_id": "STU-2022",
        "response_text": (
            "Tuples cannot be changed once created (immutable). They should be used for data that shouldn't change, "
            "like coordinates (x, y) or database records. Also they can be used as dictionary keys because they are hashable."
        ),
        "human_1_score": 9,
        "human_2_score": 8,
        "type": "Solid"
    },
    {
        "id": "RESP-23",
        "question_id": "Q3",
        "student_id": "STU-2023",
        "response_text": (
            "Tuples are immutable so you can't edit them. Lists are mutable. "
            "Use tuples when you want constant data."
        ),
        "human_1_score": 6,
        "human_2_score": 6,
        "type": "Basic Correct"
    },
    {
        "id": "RESP-24",
        "question_id": "Q3",
        "student_id": "STU-2024",
        "response_text": (
            "In modern object-oriented Python architecture, tuples represent an immutable encapsulation of data structures. "
            "By ensuring non-volatile memory references, tuples enhance algorithmic integrity across asynchronous threads. "
            "Programmers deploy tuples whenever robust architectural isolation is required."
        ),
        "human_1_score": 3,
        "human_2_score": 3,
        "type": "Verbose Fluff / Pseudo-technical"
    },
    {
        "id": "RESP-25",
        "question_id": "Q3",
        "student_id": "STU-2025",
        "response_text": (
            "Tuples are mutable while lists are immutable. You use tuples when you need to append items rapidly."
        ),
        "human_1_score": 0,
        "human_2_score": 0,
        "type": "Completely Inverted"
    },
    {
        "id": "RESP-26",
        "question_id": "Q3",
        "student_id": "STU-2026",
        "response_text": (
            "Tuples are immutable for safety and slight memory efficiency. Use them as dictionary keys or coordinate pairs."
        ),
        "human_1_score": 8,
        "human_2_score": 8,
        "type": "Good Concise"
    },
    {
        "id": "RESP-27",
        "question_id": "Q3",
        "student_id": "STU-2027",
        "response_text": (
            "Tuples are immutable because Python doesn't have enough memory to resize them. "
            "Lists are stored in RAM but tuples are stored on the hard drive."
        ),
        "human_1_score": 1,
        "human_2_score": 1,
        "type": "Absurd Misconception"
    },
    {
        "id": "RESP-28",
        "question_id": "Q3",
        "student_id": "STU-2028",
        "response_text": (
            "Tuples cannot be altered after creation. Because their hash value remains constant, tuples containing hashable "
            "types can be used as keys in dictionaries (e.g. graph node pairs `(u, v)`). "
            "They also prevent accidental modification of sensitive configurations (e.g. database credentials `(host, port)`). "
            "Tuples also have lower memory overhead than lists due to fixed memory block allocation."
        ),
        "human_1_score": 10,
        "human_2_score": 10,
        "type": "Exemplary with Memory Detail"
    },
    {
        "id": "RESP-29",
        "question_id": "Q3",
        "student_id": "STU-2029",
        "response_text": (
            "Tuples use round brackets () and lists use square brackets []. That is the only difference."
        ),
        "human_1_score": 2,
        "human_2_score": 2,
        "type": "Superficial"
    },
    {
        "id": "RESP-30",
        "question_id": "Q3",
        "student_id": "STU-2030",
        "response_text": (
            "Tuples are immutable so their values cannot change. This makes them hashable, so they can be keys in a dictionary. "
            "Use them for fixed groups like (latitude, longitude)."
        ),
        "human_1_score": 9,
        "human_2_score": 9,
        "type": "Solid"
    }
]
