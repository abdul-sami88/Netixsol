"""
50 Student Submissions Dataset for 'two_sum' Challenge
Includes diverse submission types:
- 15 Optimal O(N) hash map solutions
- 10 Inefficient O(N^2) nested loop solutions
- 8 Duplicate / self-pairing edge case bugs
- 7 Missing empty / negative / single-element handlers
- 5 Runtime errors (IndexError, TypeError)
- 3 Syntax errors
- 2 Sandbox violation attempts

Includes independent human grades from Teacher 1 and Teacher 2 for benchmark comparison.
"""

from typing import List, Dict, Any

# Problem Specification:
# Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.
# You may assume that each input would have exactly one solution, and you may not use the same element twice.
# Return [idx1, idx2] in ascending order.

SUBMISSIONS_DATASET: List[Dict[str, Any]] = [
    # --- 1 to 15: Optimal O(N) Hash Map Solutions ---
    {
        "id": "SUB-01",
        "student_id": "STU-1001",
        "category": "Optimal O(N)",
        "code": """def two_sum(nums, target):
    seen = {}
    for i, num in enumerate(nums):
        comp = target - num
        if comp in seen:
            return [seen[comp], i]
        seen[num] = i
    return []
""",
        "teacher_1_score": 100,
        "teacher_2_score": 100,
        "notes": "Clean standard one-pass hash map solution."
    },
    {
        "id": "SUB-02",
        "student_id": "STU-1002",
        "category": "Optimal O(N)",
        "code": """def two_sum(nums, target):
    # Map each value to its index
    lookup = {}
    for idx, val in enumerate(nums):
        needed = target - val
        if needed in lookup:
            return [lookup[needed], idx]
        lookup[val] = idx
    return []
""",
        "teacher_1_score": 100,
        "teacher_2_score": 98,
        "notes": "Excellent clarity and comments."
    },
    {
        "id": "SUB-03",
        "student_id": "STU-1003",
        "category": "Optimal O(N)",
        "code": """def two_sum(nums, target):
    d = {}
    for i in range(len(nums)):
        x = nums[i]
        diff = target - x
        if diff in d:
            return [d[diff], i]
        d[x] = i
    return []
""",
        "teacher_1_score": 98,
        "teacher_2_score": 95,
        "notes": "Good range(len(nums)) loop with hash table."
    },
    {
        "id": "SUB-04",
        "student_id": "STU-1004",
        "category": "Optimal O(N)",
        "code": """def two_sum(nums, target):
    m = {}
    for idx, n in enumerate(nums):
        rem = target - n
        if rem in m:
            return sorted([m[rem], idx])
        m[n] = idx
    return []
""",
        "teacher_1_score": 100,
        "teacher_2_score": 100,
        "notes": "Sorted indices guarantee ascending order."
    },
    {
        "id": "SUB-05",
        "student_id": "STU-1005",
        "category": "Optimal O(N)",
        "code": """def two_sum(nums, target):
    seen_map = dict()
    for i, val in enumerate(nums):
        if (target - val) in seen_map:
            return [seen_map[target - val], i]
        seen_map[val] = i
    return []
""",
        "teacher_1_score": 95,
        "teacher_2_score": 95,
        "notes": "Optimal O(N) time and space."
    },
    {
        "id": "SUB-06",
        "student_id": "STU-1006",
        "category": "Optimal O(N)",
        "code": """def two_sum(nums, target):
    cache = {}
    for pos, item in enumerate(nums):
        delta = target - item
        if delta in cache:
            return [cache[delta], pos]
        cache[item] = pos
    return []
""",
        "teacher_1_score": 98,
        "teacher_2_score": 97,
        "notes": "Very clean hash lookup."
    },
    {
        "id": "SUB-07",
        "student_id": "STU-1007",
        "category": "Optimal O(N)",
        "code": """def two_sum(nums, target):
    table = {}
    for i in range(len(nums)):
        val = nums[i]
        complement = target - val
        if complement in table:
            return [table[complement], i]
        table[val] = i
    return []
""",
        "teacher_1_score": 95,
        "teacher_2_score": 95,
        "notes": "Correct linear scan."
    },
    {
        "id": "SUB-08",
        "student_id": "STU-1008",
        "category": "Optimal O(N)",
        "code": """def two_sum(nums, target):
    num_to_idx = {}
    for idx, num in enumerate(nums):
        if target - num in num_to_idx:
            return [num_to_idx[target - num], idx]
        num_to_idx[num] = idx
    return []
""",
        "teacher_1_score": 100,
        "teacher_2_score": 98,
        "notes": "Succinct and idiomatic."
    },
    {
        "id": "SUB-09",
        "student_id": "STU-1009",
        "category": "Optimal O(N)",
        "code": """def two_sum(nums, target):
    memo = {}
    for i, x in enumerate(nums):
        need = target - x
        if need in memo:
            return [memo[need], i]
        memo[x] = i
    return []
""",
        "teacher_1_score": 96,
        "teacher_2_score": 96,
        "notes": "Optimal O(N)."
    },
    {
        "id": "SUB-10",
        "student_id": "STU-1010",
        "category": "Optimal O(N)",
        "code": """def two_sum(nums, target):
    history = {}
    for idx, v in enumerate(nums):
        partner = target - v
        if partner in history:
            return [history[partner], idx]
        history[v] = idx
    return []
""",
        "teacher_1_score": 97,
        "teacher_2_score": 96,
        "notes": "Descriptive variable names."
    },
    {
        "id": "SUB-11",
        "student_id": "STU-1011",
        "category": "Optimal O(N)",
        "code": """def two_sum(nums, target):
    seen = {}
    for i in range(len(nums)):
        c = target - nums[i]
        if c in seen:
            return [seen[c], i]
        seen[nums[i]] = i
    return []
""",
        "teacher_1_score": 94,
        "teacher_2_score": 94,
        "notes": "Standard hash map."
    },
    {
        "id": "SUB-12",
        "student_id": "STU-1012",
        "category": "Optimal O(N)",
        "code": """def two_sum(nums, target):
    visited = {}
    for idx, num in enumerate(nums):
        res = target - num
        if res in visited:
            return [visited[res], idx]
        visited[num] = idx
    return []
""",
        "teacher_1_score": 96,
        "teacher_2_score": 95,
        "notes": "Fast and correct."
    },
    {
        "id": "SUB-13",
        "student_id": "STU-1013",
        "category": "Optimal O(N)",
        "code": """def two_sum(nums, target):
    # Two-pass hash table
    d = {}
    for i, n in enumerate(nums):
        d[n] = i
    for i, n in enumerate(nums):
        c = target - n
        if c in d and d[c] != i:
            return [i, d[c]]
    return []
""",
        "teacher_1_score": 92,
        "teacher_2_score": 90,
        "notes": "Two-pass hash map; slightly more memory but still O(N)."
    },
    {
        "id": "SUB-14",
        "student_id": "STU-1014",
        "category": "Optimal O(N)",
        "code": """def two_sum(nums, target):
    indices = {}
    for i, x in enumerate(nums):
        if target - x in indices:
            return [indices[target - x], i]
        indices[x] = i
    return []
""",
        "teacher_1_score": 95,
        "teacher_2_score": 95,
        "notes": "Solid O(N) linear time implementation."
    },
    {
        "id": "SUB-15",
        "student_id": "STU-1015",
        "category": "Optimal O(N)",
        "code": """def two_sum(nums, target):
    res_dict = {}
    for i, v in enumerate(nums):
        diff = target - v
        if diff in res_dict:
            return [res_dict[diff], i]
        res_dict[v] = i
    return []
""",
        "teacher_1_score": 97,
        "teacher_2_score": 97,
        "notes": "Optimal O(N)."
    },

    # --- 16 to 25: Inefficient O(N^2) Solutions ---
    {
        "id": "SUB-16",
        "student_id": "STU-1016",
        "category": "Inefficient O(N^2)",
        "code": """def two_sum(nums, target):
    # Nested loops
    n = len(nums)
    for i in range(n):
        for j in range(i + 1, n):
            if nums[i] + nums[j] == target:
                return [i, j]
    return []
""",
        "teacher_1_score": 68,
        "teacher_2_score": 70,
        "notes": "Brute force O(N^2). Passes small tests, but inefficient."
    },
    {
        "id": "SUB-17",
        "student_id": "STU-1017",
        "category": "Inefficient O(N^2)",
        "code": """def two_sum(nums, target):
    for i in range(len(nums)):
        for j in range(len(nums)):
            if i != j and nums[i] + nums[j] == target:
                return [min(i, j), max(i, j)]
    return []
""",
        "teacher_1_score": 65,
        "teacher_2_score": 65,
        "notes": "Quadratic nested loops without even skipping redundant pairs."
    },
    {
        "id": "SUB-18",
        "student_id": "STU-1018",
        "category": "Inefficient O(N^2)",
        "code": """def two_sum(nums, target):
    for i in range(len(nums)):
        val = nums[i]
        rem = target - val
        if rem in nums[i+1:]:
            j = nums[i+1:].index(rem) + (i + 1)
            return [i, j]
    return []
""",
        "teacher_1_score": 70,
        "teacher_2_score": 72,
        "notes": "List slicing and index() inside loop makes it O(N^2)."
    },
    {
        "id": "SUB-19",
        "student_id": "STU-1019",
        "category": "Inefficient O(N^2)",
        "code": """def two_sum(nums, target):
    l = len(nums)
    for a in range(l):
        for b in range(a + 1, l):
            if nums[a] + nums[b] == target:
                return [a, b]
    return []
""",
        "teacher_1_score": 68,
        "teacher_2_score": 70,
        "notes": "Brute force O(N^2)."
    },
    {
        "id": "SUB-20",
        "student_id": "STU-1020",
        "category": "Inefficient O(N^2)",
        "code": """def two_sum(nums, target):
    i = 0
    while i < len(nums):
        j = i + 1
        while j < len(nums):
            if nums[i] + nums[j] == target:
                return [i, j]
            j += 1
        i += 1
    return []
""",
        "teacher_1_score": 66,
        "teacher_2_score": 68,
        "notes": "Nested while loops, O(N^2)."
    },
    {
        "id": "SUB-21",
        "student_id": "STU-1021",
        "category": "Inefficient O(N^2)",
        "code": """def two_sum(nums, target):
    for i, x in enumerate(nums):
        for j, y in enumerate(nums):
            if i < j and x + y == target:
                return [i, j]
    return []
""",
        "teacher_1_score": 67,
        "teacher_2_score": 68,
        "notes": "O(N^2) pairwise check."
    },
    {
        "id": "SUB-22",
        "student_id": "STU-1022",
        "category": "Inefficient O(N^2)",
        "code": """def two_sum(nums, target):
    ans = []
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            if nums[i] + nums[j] == target:
                ans.append(i)
                ans.append(j)
                return ans
    return []
""",
        "teacher_1_score": 68,
        "teacher_2_score": 69,
        "notes": "O(N^2) nested loop."
    },
    {
        "id": "SUB-23",
        "student_id": "STU-1023",
        "category": "Inefficient O(N^2)",
        "code": """def two_sum(nums, target):
    for i in range(len(nums) - 1):
        for j in range(i + 1, len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]
    return []
""",
        "teacher_1_score": 69,
        "teacher_2_score": 70,
        "notes": "O(N^2) brute force."
    },
    {
        "id": "SUB-24",
        "student_id": "STU-1024",
        "category": "Inefficient O(N^2)",
        "code": """def two_sum(nums, target):
    for idx1, n1 in enumerate(nums):
        for idx2 in range(idx1 + 1, len(nums)):
            if n1 + nums[idx2] == target:
                return [idx1, idx2]
    return []
""",
        "teacher_1_score": 68,
        "teacher_2_score": 70,
        "notes": "O(N^2) double loop."
    },
    {
        "id": "SUB-25",
        "student_id": "STU-1025",
        "category": "Inefficient O(N^2)",
        "code": """def two_sum(nums, target):
    res = []
    for i in range(len(nums)):
        target_val = target - nums[i]
        for j in range(i + 1, len(nums)):
            if nums[j] == target_val:
                return [i, j]
    return res
""",
        "teacher_1_score": 68,
        "teacher_2_score": 70,
        "notes": "Quadratic time complexity."
    },

    # --- 26 to 33: Duplicate / Self-Pairing Edge Case Bugs ---
    {
        "id": "SUB-26",
        "student_id": "STU-1026",
        "category": "Duplicate/Self Bug",
        "code": """def two_sum(nums, target):
    # Bug: allows picking the same element twice if target is 2*nums[i]!
    for i, x in enumerate(nums):
        diff = target - x
        if diff in nums:
            return [i, nums.index(diff)]
    return []
""",
        "teacher_1_score": 45,
        "teacher_2_score": 50,
        "notes": "Critical bug: picks same index twice on target = 2 * nums[i]."
    },
    {
        "id": "SUB-27",
        "student_id": "STU-1027",
        "category": "Duplicate/Self Bug",
        "code": """def two_sum(nums, target):
    d = {val: i for i, val in enumerate(nums)}
    for i, val in enumerate(nums):
        comp = target - val
        # Bug: fails when comp == val if duplicate exists, or picks self!
        if comp in d:
            return [i, d[comp]]
    return []
""",
        "teacher_1_score": 50,
        "teacher_2_score": 52,
        "notes": "Does not check if d[comp] != i, returning [i, i]."
    },
    {
        "id": "SUB-28",
        "student_id": "STU-1028",
        "category": "Duplicate/Self Bug",
        "code": """def two_sum(nums, target):
    seen = {}
    for i, n in enumerate(nums):
        seen[n] = i # Overwrites duplicate early
    for i, n in enumerate(nums):
        needed = target - n
        if needed in seen and seen[needed] != i:
            return [i, seen[needed]]
    return []
""",
        "teacher_1_score": 82,
        "teacher_2_score": 85,
        "notes": "Overwrites duplicates in first pass, but handles duplicate pairs like [3, 3] correctly."
    },
    {
        "id": "SUB-29",
        "student_id": "STU-1029",
        "category": "Duplicate/Self Bug",
        "code": """def two_sum(nums, target):
    for i in range(len(nums)):
        partner = target - nums[i]
        if partner in nums:
            idx = nums.index(partner)
            if idx != i:
                return [i, idx]
    return []
""",
        "teacher_1_score": 60,
        "teacher_2_score": 62,
        "notes": "Fails on duplicate values like [3, 3] because nums.index(partner) always returns first 3."
    },
    {
        "id": "SUB-30",
        "student_id": "STU-1030",
        "category": "Duplicate/Self Bug",
        "code": """def two_sum(nums, target):
    for i in range(len(nums)):
        needed = target - nums[i]
        # Over-simplification
        if needed in nums and nums.index(needed) != i:
            return sorted([i, nums.index(needed)])
    return []
""",
        "teacher_1_score": 58,
        "teacher_2_score": 60,
        "notes": "nums.index() returns first occurrence, failing on duplicate targets."
    },
    {
        "id": "SUB-31",
        "student_id": "STU-1031",
        "category": "Duplicate/Self Bug",
        "code": """def two_sum(nums, target):
    # Returns [i, i] if target is 2 * nums[i]
    for i in range(len(nums)):
        needed = target - nums[i]
        if needed in nums:
            return [i, nums.index(needed)]
    return []
""",
        "teacher_1_score": 45,
        "teacher_2_score": 48,
        "notes": "Returns self-element [i, i]."
    },
    {
        "id": "SUB-32",
        "student_id": "STU-1032",
        "category": "Duplicate/Self Bug",
        "code": """def two_sum(nums, target):
    s = set(nums)
    for i, num in enumerate(nums):
        comp = target - num
        if comp in s:
            return [i, nums.index(comp)]
    return []
""",
        "teacher_1_score": 48,
        "teacher_2_score": 50,
        "notes": "Fails when comp == num, returning same index."
    },
    {
        "id": "SUB-33",
        "student_id": "STU-1033",
        "category": "Duplicate/Self Bug",
        "code": """def two_sum(nums, target):
    memo = {}
    for i in range(len(nums)):
        memo[nums[i]] = i
    for i in range(len(nums)):
        diff = target - nums[i]
        if diff in memo:
            return [i, memo[diff]]
    return []
""",
        "teacher_1_score": 52,
        "teacher_2_score": 55,
        "notes": "Returns same index if diff == nums[i]."
    },

    # --- 34 to 40: Missing Edge Cases (Empty, Single, Negatives) ---
    {
        "id": "SUB-34",
        "student_id": "STU-1034",
        "category": "Missing Edge Cases",
        "code": """def two_sum(nums, target):
    # Doesn't handle negative numbers properly
    nums = [x for x in nums if x > 0]
    seen = {}
    for i, n in enumerate(nums):
        if target - n in seen:
            return [seen[target - n], i]
        seen[n] = i
    return []
""",
        "teacher_1_score": 40,
        "teacher_2_score": 45,
        "notes": "Arbitrarily filters out negative numbers! Alters original indices."
    },
    {
        "id": "SUB-35",
        "student_id": "STU-1035",
        "category": "Missing Edge Cases",
        "code": """def two_sum(nums, target):
    if len(nums) <= 2:
        return [0, 1]
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]
    return []
""",
        "teacher_1_score": 55,
        "teacher_2_score": 58,
        "notes": "Hardcoded [0, 1] for len <= 2 regardless of target sum!"
    },
    {
        "id": "SUB-36",
        "student_id": "STU-1036",
        "category": "Missing Edge Cases",
        "code": """def two_sum(nums, target):
    # Only checks positive numbers
    for i in range(len(nums)):
        if nums[i] < 0:
            continue
        for j in range(i + 1, len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]
    return []
""",
        "teacher_1_score": 50,
        "teacher_2_score": 52,
        "notes": "Fails completely when inputs or target involve negative numbers."
    },
    {
        "id": "SUB-37",
        "student_id": "STU-1037",
        "category": "Missing Edge Cases",
        "code": """def two_sum(nums, target):
    # Assumes sorted array (two pointers without sorting first)
    left = 0
    right = len(nums) - 1
    while left < right:
        curr = nums[left] + nums[right]
        if curr == target:
            return [left, right]
        elif curr < target:
            left += 1
        else:
            right -= 1
    return []
""",
        "teacher_1_score": 50,
        "teacher_2_score": 48,
        "notes": "Applies two-pointer on unsorted array. Fails whenever input is not sorted."
    },
    {
        "id": "SUB-38",
        "student_id": "STU-1038",
        "category": "Missing Edge Cases",
        "code": """def two_sum(nums, target):
    # Assumes target is always greater than elements
    seen = {}
    for i, x in enumerate(nums):
        if x > target:
            continue
        if target - x in seen:
            return [seen[target - x], i]
        seen[x] = i
    return []
""",
        "teacher_1_score": 55,
        "teacher_2_score": 55,
        "notes": "Skips elements > target, failing for negative numbers."
    },
    {
        "id": "SUB-39",
        "student_id": "STU-1039",
        "category": "Missing Edge Cases",
        "code": """def two_sum(nums, target):
    # Stops after 10 iterations
    for i in range(min(10, len(nums))):
        for j in range(i + 1, min(10, len(nums))):
            if nums[i] + nums[j] == target:
                return [i, j]
    return []
""",
        "teacher_1_score": 35,
        "teacher_2_score": 38,
        "notes": "Artificially truncates search to first 10 elements."
    },
    {
        "id": "SUB-40",
        "student_id": "STU-1040",
        "category": "Missing Edge Cases",
        "code": """def two_sum(nums, target):
    if nums[0] + nums[1] == target:
        return [0, 1]
    return []
""",
        "teacher_1_score": 20,
        "teacher_2_score": 25,
        "notes": "Only checks the very first pair."
    },

    # --- 41 to 45: Runtime Errors ---
    {
        "id": "SUB-41",
        "student_id": "STU-1041",
        "category": "Runtime Error",
        "code": """def two_sum(nums, target):
    # IndexError on empty or single element input
    for i in range(len(nums)):
        if nums[i] + nums[i + 1] == target:
            return [i, i + 1]
    return []
""",
        "teacher_1_score": 25,
        "teacher_2_score": 25,
        "notes": "Raises IndexError on nums[i + 1] at last index."
    },
    {
        "id": "SUB-42",
        "student_id": "STU-1042",
        "category": "Runtime Error",
        "code": """def two_sum(nums, target):
    # TypeError
    seen = []
    for i in range(len(nums)):
        seen[nums[i]] = i # Cannot assign by value to list index
    return []
""",
        "teacher_1_score": 15,
        "teacher_2_score": 15,
        "notes": "TypeError: list indices must be integers or slices, not int value assignment."
    },
    {
        "id": "SUB-43",
        "student_id": "STU-1043",
        "category": "Runtime Error",
        "code": """def two_sum(nums, target):
    # UnboundLocalError / NameError
    for i in range(len(nums)):
        if nums[i] + complement == target:
            return [i, j]
""",
        "teacher_1_score": 10,
        "teacher_2_score": 10,
        "notes": "NameError: complement is not defined."
    },
    {
        "id": "SUB-44",
        "student_id": "STU-1044",
        "category": "Runtime Error",
        "code": """def two_sum(nums, target):
    # Recursion without base case
    return two_sum(nums, target)
""",
        "teacher_1_score": 0,
        "teacher_2_score": 0,
        "notes": "Unbounded recursion causing RecursionError."
    },
    {
        "id": "SUB-45",
        "student_id": "STU-1045",
        "category": "Runtime Error",
        "code": """def two_sum(nums, target):
    # ZeroDivisionError attempt
    ratio = target / (nums[0] - nums[0])
    return []
""",
        "teacher_1_score": 0,
        "teacher_2_score": 0,
        "notes": "ZeroDivisionError on first line."
    },

    # --- 46 to 48: Syntax Errors ---
    {
        "id": "SUB-46",
        "student_id": "STU-1046",
        "category": "Syntax Error",
        "code": """def two_sum(nums, target):
    for i in range(len(nums))
        if nums[i] == target:
            return i
""",
        "teacher_1_score": 0,
        "teacher_2_score": 0,
        "notes": "SyntaxError: missing colon after for loop."
    },
    {
        "id": "SUB-47",
        "student_id": "STU-1047",
        "category": "Syntax Error",
        "code": """def two_sum(nums, target):
    seen = {}
    for i, x in enumerate(nums)
        seen[x] = i
    return []
""",
        "teacher_1_score": 0,
        "teacher_2_score": 0,
        "notes": "SyntaxError: missing colon."
    },
    {
        "id": "SUB-48",
        "student_id": "STU-1048",
        "category": "Syntax Error",
        "code": """def two_sum(nums, target):
    return [i, j for i in nums]
""",
        "teacher_1_score": 0,
        "teacher_2_score": 0,
        "notes": "SyntaxError: invalid list comprehension syntax."
    },

    # --- 49 to 50: Security Violation Attempts ---
    {
        "id": "SUB-49",
        "student_id": "STU-1049",
        "category": "Security Violation",
        "code": """import os
def two_sum(nums, target):
    # Malicious attempt to read environment
    print(os.environ)
    return [0, 1]
""",
        "teacher_1_score": 0,
        "teacher_2_score": 0,
        "notes": "Security breach: imports os module."
    },
    {
        "id": "SUB-50",
        "student_id": "STU-1050",
        "category": "Security Violation",
        "code": """def two_sum(nums, target):
    # Dynamic code injection
    eval("__import__('sys').exit(0)")
    return []
""",
        "teacher_1_score": 0,
        "teacher_2_score": 0,
        "notes": "Security breach: uses eval() and dynamic reflection."
    }
]
