"""
Plagiarism Evaluation Benchmark Dataset (40 Submission Pairs)
Contains balanced representative pairs across 4 distinct integrity categories:
- 10 Exact Verbatim Copies (Ground truth: Plagiarized = 1)
- 10 Obfuscated Copies via Variable Renaming & Comment Changes (Ground truth: Plagiarized = 1)
- 5 Structural Refactoring / Statement Reordering Copies (Ground truth: Plagiarized = 1)
- 15 Independently Authored Clean Submissions (Ground truth: Clean / Non-Plagiarized = 0)
"""

from typing import List, Dict, Any

PLAGIARISM_PAIRS: List[Dict[str, Any]] = [
    # --- 1 to 10: Exact Verbatim Copies ---
    {
        "pair_id": "PAIR-01",
        "category": "Verbatim Copy",
        "is_plagiarized": 1,
        "student_a": "STU-3001",
        "student_b": "STU-3002",
        "code_a": """def two_sum(nums, target):
    seen = {}
    for i, num in enumerate(nums):
        comp = target - num
        if comp in seen:
            return [seen[comp], i]
        seen[num] = i
    return []
""",
        "code_b": """def two_sum(nums, target):
    seen = {}
    for i, num in enumerate(nums):
        comp = target - num
        if comp in seen:
            return [seen[comp], i]
        seen[num] = i
    return []
"""
    },
    {
        "pair_id": "PAIR-02",
        "category": "Verbatim Copy",
        "is_plagiarized": 1,
        "student_a": "STU-3003",
        "student_b": "STU-3004",
        "code_a": """def two_sum(nums, target):
    lookup = {}
    for idx, val in enumerate(nums):
        needed = target - val
        if needed in lookup:
            return [lookup[needed], idx]
        lookup[val] = idx
    return []
""",
        "code_b": """def two_sum(nums, target):
    lookup = {}
    for idx, val in enumerate(nums):
        needed = target - val
        if needed in lookup:
            return [lookup[needed], idx]
        lookup[val] = idx
    return []
"""
    },
    {
        "pair_id": "PAIR-03",
        "category": "Verbatim Copy",
        "is_plagiarized": 1,
        "student_a": "STU-3005",
        "student_b": "STU-3006",
        "code_a": """def two_sum(nums, target):
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]
    return []
""",
        "code_b": """def two_sum(nums, target):
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]
    return []
"""
    },
    {
        "pair_id": "PAIR-04",
        "category": "Verbatim Copy",
        "is_plagiarized": 1,
        "student_a": "STU-3007",
        "student_b": "STU-3008",
        "code_a": """def two_sum(nums, target):
    d = dict()
    for pos, x in enumerate(nums):
        req = target - x
        if req in d:
            return [d[req], pos]
        d[x] = pos
    return []
""",
        "code_b": """def two_sum(nums, target):
    d = dict()
    for pos, x in enumerate(nums):
        req = target - x
        if req in d:
            return [d[req], pos]
        d[x] = pos
    return []
"""
    },
    {
        "pair_id": "PAIR-05",
        "category": "Verbatim Copy",
        "is_plagiarized": 1,
        "student_a": "STU-3009",
        "student_b": "STU-3010",
        "code_a": """def two_sum(nums, target):
    m = {}
    for i in range(len(nums)):
        if target - nums[i] in m:
            return [m[target - nums[i]], i]
        m[nums[i]] = i
    return []
""",
        "code_b": """def two_sum(nums, target):
    m = {}
    for i in range(len(nums)):
        if target - nums[i] in m:
            return [m[target - nums[i]], i]
        m[nums[i]] = i
    return []
"""
    },
    {
        "pair_id": "PAIR-06",
        "category": "Verbatim Copy",
        "is_plagiarized": 1,
        "student_a": "STU-3011",
        "student_b": "STU-3012",
        "code_a": """def two_sum(nums, target):
    cache = {}
    for i, item in enumerate(nums):
        c = target - item
        if c in cache:
            return [cache[c], i]
        cache[item] = i
    return []
""",
        "code_b": """def two_sum(nums, target):
    cache = {}
    for i, item in enumerate(nums):
        c = target - item
        if c in cache:
            return [cache[c], i]
        cache[item] = i
    return []
"""
    },
    {
        "pair_id": "PAIR-07",
        "category": "Verbatim Copy",
        "is_plagiarized": 1,
        "student_a": "STU-3013",
        "student_b": "STU-3014",
        "code_a": """def two_sum(nums, target):
    for a in range(len(nums)):
        for b in range(a + 1, len(nums)):
            if nums[a] + nums[b] == target:
                return [a, b]
    return []
""",
        "code_b": """def two_sum(nums, target):
    for a in range(len(nums)):
        for b in range(a + 1, len(nums)):
            if nums[a] + nums[b] == target:
                return [a, b]
    return []
"""
    },
    {
        "pair_id": "PAIR-08",
        "category": "Verbatim Copy",
        "is_plagiarized": 1,
        "student_a": "STU-3015",
        "student_b": "STU-3016",
        "code_a": """def two_sum(nums, target):
    indices = {}
    for idx, val in enumerate(nums):
        partner = target - val
        if partner in indices:
            return [indices[partner], idx]
        indices[val] = idx
    return []
""",
        "code_b": """def two_sum(nums, target):
    indices = {}
    for idx, val in enumerate(nums):
        partner = target - val
        if partner in indices:
            return [indices[partner], idx]
        indices[val] = idx
    return []
"""
    },
    {
        "pair_id": "PAIR-09",
        "category": "Verbatim Copy",
        "is_plagiarized": 1,
        "student_a": "STU-3017",
        "student_b": "STU-3018",
        "code_a": """def two_sum(nums, target):
    memo = {}
    for i, v in enumerate(nums):
        if target - v in memo:
            return [memo[target - v], i]
        memo[v] = i
    return []
""",
        "code_b": """def two_sum(nums, target):
    memo = {}
    for i, v in enumerate(nums):
        if target - v in memo:
            return [memo[target - v], i]
        memo[v] = i
    return []
"""
    },
    {
        "pair_id": "PAIR-10",
        "category": "Verbatim Copy",
        "is_plagiarized": 1,
        "student_a": "STU-3019",
        "student_b": "STU-3020",
        "code_a": """def two_sum(nums, target):
    store = {}
    for i, n in enumerate(nums):
        diff = target - n
        if diff in store:
            return [store[diff], i]
        store[n] = i
    return []
""",
        "code_b": """def two_sum(nums, target):
    store = {}
    for i, n in enumerate(nums):
        diff = target - n
        if diff in store:
            return [store[diff], i]
        store[n] = i
    return []
"""
    },

    # --- 11 to 20: Obfuscated Copies (Variable Renaming & Comment Tampering) ---
    {
        "pair_id": "PAIR-11",
        "category": "Variable Renaming Obfuscation",
        "is_plagiarized": 1,
        "student_a": "STU-3021",
        "student_b": "STU-3022",
        "code_a": """def two_sum(nums, target):
    seen = {}
    for i, num in enumerate(nums):
        comp = target - num
        if comp in seen:
            return [seen[comp], i]
        seen[num] = i
    return []
""",
        "code_b": """# My original assignment submission
def two_sum(arr, goal):
    my_dictionary = {}
    for index_pos, current_element in enumerate(arr):
        required_difference = goal - current_element
        if required_difference in my_dictionary:
            return [my_dictionary[required_difference], index_pos]
        my_dictionary[current_element] = index_pos
    return []
"""
    },
    {
        "pair_id": "PAIR-12",
        "category": "Variable Renaming Obfuscation",
        "is_plagiarized": 1,
        "student_a": "STU-3023",
        "student_b": "STU-3024",
        "code_a": """def two_sum(nums, target):
    table = {}
    for i in range(len(nums)):
        val = nums[i]
        complement = target - val
        if complement in table:
            return [table[complement], i]
        table[val] = i
    return []
""",
        "code_b": """def two_sum(numbers, tgt):
    # Lookup table
    h_table = {}
    for p in range(len(numbers)):
        elem = numbers[p]
        delta = tgt - elem
        if delta in h_table:
            return [h_table[delta], p]
        h_table[elem] = p
    return []
"""
    },
    {
        "pair_id": "PAIR-13",
        "category": "Variable Renaming Obfuscation",
        "is_plagiarized": 1,
        "student_a": "STU-3025",
        "student_b": "STU-3026",
        "code_a": """def two_sum(nums, target):
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]
    return []
""",
        "code_b": """def two_sum(lst, k):
    n_len = len(lst)
    for ptr1 in range(n_len):
        for ptr2 in range(ptr1 + 1, n_len):
            if lst[ptr1] + lst[ptr2] == k:
                return [ptr1, ptr2]
    return []
"""
    },
    {
        "pair_id": "PAIR-14",
        "category": "Variable Renaming Obfuscation",
        "is_plagiarized": 1,
        "student_a": "STU-3027",
        "student_b": "STU-3028",
        "code_a": """def two_sum(nums, target):
    seen = dict()
    for k, v in enumerate(nums):
        if target - v in seen:
            return [seen[target - v], k]
        seen[v] = k
    return []
""",
        "code_b": """def two_sum(elements, t):
    tracked = dict()
    for pos, x_val in enumerate(elements):
        if t - x_val in tracked:
            return [tracked[t - x_val], pos]
        tracked[x_val] = pos
    return []
"""
    },
    {
        "pair_id": "PAIR-15",
        "category": "Variable Renaming Obfuscation",
        "is_plagiarized": 1,
        "student_a": "STU-3029",
        "student_b": "STU-3030",
        "code_a": """def two_sum(nums, target):
    memo = {}
    for idx, num in enumerate(nums):
        rem = target - num
        if rem in memo:
            return [memo[rem], idx]
        memo[num] = idx
    return []
""",
        "code_b": """def two_sum(data, target_value):
    # Store visited numbers
    visited_map = {}
    for cursor, element in enumerate(data):
        missing = target_value - element
        if missing in visited_map:
            return [visited_map[missing], cursor]
        visited_map[element] = cursor
    return []
"""
    },
    {
        "pair_id": "PAIR-16",
        "category": "Variable Renaming Obfuscation",
        "is_plagiarized": 1,
        "student_a": "STU-3031",
        "student_b": "STU-3032",
        "code_a": """def two_sum(nums, target):
    hashmap = {}
    for i, x in enumerate(nums):
        comp = target - x
        if comp in hashmap:
            return [hashmap[comp], i]
        hashmap[x] = i
    return []
""",
        "code_b": """def two_sum(a, t):
    h = {}
    for j, y in enumerate(a):
        z = t - y
        if z in h:
            return [h[z], j]
        h[y] = j
    return []
"""
    },
    {
        "pair_id": "PAIR-17",
        "category": "Variable Renaming Obfuscation",
        "is_plagiarized": 1,
        "student_a": "STU-3033",
        "student_b": "STU-3034",
        "code_a": """def two_sum(nums, target):
    d = {}
    for i, val in enumerate(nums):
        need = target - val
        if need in d:
            return [d[need], i]
        d[val] = i
    return []
""",
        "code_b": """# Student Ali submission
def two_sum(arr, total):
    res_dict = {}
    for index, item in enumerate(arr):
        diff = total - item
        if diff in res_dict:
            return [res_dict[diff], index]
        res_dict[item] = index
    return []
"""
    },
    {
        "pair_id": "PAIR-18",
        "category": "Variable Renaming Obfuscation",
        "is_plagiarized": 1,
        "student_a": "STU-3035",
        "student_b": "STU-3036",
        "code_a": """def two_sum(nums, target):
    for i in range(len(nums)):
        for j in range(len(nums)):
            if i != j and nums[i] + nums[j] == target:
                return [i, j]
    return []
""",
        "code_b": """def two_sum(items, t):
    for a in range(len(items)):
        for b in range(len(items)):
            if a != b and items[a] + items[b] == t:
                return [a, b]
    return []
"""
    },
    {
        "pair_id": "PAIR-19",
        "category": "Variable Renaming Obfuscation",
        "is_plagiarized": 1,
        "student_a": "STU-3037",
        "student_b": "STU-3038",
        "code_a": """def two_sum(nums, target):
    mapping = {}
    for idx, num in enumerate(nums):
        if target - num in mapping:
            return [mapping[target - num], idx]
        mapping[num] = idx
    return []
""",
        "code_b": """def two_sum(nums_array, goal_sum):
    records = {}
    for loc, value in enumerate(nums_array):
        if goal_sum - value in records:
            return [records[goal_sum - value], loc]
        records[value] = loc
    return []
"""
    },
    {
        "pair_id": "PAIR-20",
        "category": "Variable Renaming Obfuscation",
        "is_plagiarized": 1,
        "student_a": "STU-3039",
        "student_b": "STU-3040",
        "code_a": """def two_sum(nums, target):
    seen = {}
    for i, n in enumerate(nums):
        comp = target - n
        if comp in seen:
            return [seen[comp], i]
        seen[n] = i
    return []
""",
        "code_b": """def two_sum(values, target):
    index_cache = {}
    for p, val in enumerate(values):
        c = target - val
        if c in index_cache:
            return [index_cache[c], p]
        index_cache[val] = p
    return []
"""
    },

    # --- 21 to 25: Structural Refactoring / Statement Reordering ---
    {
        "pair_id": "PAIR-21",
        "category": "Structural Refactoring",
        "is_plagiarized": 1,
        "student_a": "STU-3041",
        "student_b": "STU-3042",
        "code_a": """def two_sum(nums, target):
    seen = {}
    for i, num in enumerate(nums):
        comp = target - num
        if comp in seen:
            return [seen[comp], i]
        seen[num] = i
    return []
""",
        "code_b": """def two_sum(nums, target):
    # Reversed storage structure
    seen = {}
    for i in range(len(nums)):
        n = nums[i]
        c = target - n
        if c in seen:
            ans = [seen[c], i]
            return ans
        seen[n] = i
    return []
"""
    },
    {
        "pair_id": "PAIR-22",
        "category": "Structural Refactoring",
        "is_plagiarized": 1,
        "student_a": "STU-3043",
        "student_b": "STU-3044",
        "code_a": """def two_sum(nums, target):
    d = {}
    for i, x in enumerate(nums):
        if target - x in d:
            return [d[target - x], i]
        d[x] = i
    return []
""",
        "code_b": """def two_sum(nums, target):
    # Two-pass extraction
    d = {}
    for i, x in enumerate(nums):
        d[x] = i
    for i, x in enumerate(nums):
        if target - x in d and d[target - x] != i:
            return [i, d[target - x]]
    return []
"""
    },
    {
        "pair_id": "PAIR-23",
        "category": "Structural Refactoring",
        "is_plagiarized": 1,
        "student_a": "STU-3045",
        "student_b": "STU-3046",
        "code_a": """def two_sum(nums, target):
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]
    return []
""",
        "code_b": """def two_sum(nums, target):
    n = len(nums)
    i = 0
    while i < n:
        j = i + 1
        while j < n:
            if nums[i] + nums[j] == target:
                return [i, j]
            j += 1
        i += 1
    return []
"""
    },
    {
        "pair_id": "PAIR-24",
        "category": "Structural Refactoring",
        "is_plagiarized": 1,
        "student_a": "STU-3047",
        "student_b": "STU-3048",
        "code_a": """def two_sum(nums, target):
    table = {}
    for idx, val in enumerate(nums):
        partner = target - val
        if partner in table:
            return [table[partner], idx]
        table[val] = idx
    return []
""",
        "code_b": """def two_sum(nums, target):
    table = dict()
    for idx in range(len(nums)):
        val = nums[idx]
        diff = target - val
        if diff in table.keys():
            return [table.get(diff), idx]
        table[val] = idx
    return []
"""
    },
    {
        "pair_id": "PAIR-25",
        "category": "Structural Refactoring",
        "is_plagiarized": 1,
        "student_a": "STU-3049",
        "student_b": "STU-3050",
        "code_a": """def two_sum(nums, target):
    lookup = {}
    for i, num in enumerate(nums):
        diff = target - num
        if diff in lookup:
            return [lookup[diff], i]
        lookup[num] = i
    return []
""",
        "code_b": """def two_sum(nums, target):
    lookup = {}
    ans = None
    for i, num in enumerate(nums):
        complement = target - num
        if complement in lookup:
            ans = [lookup[complement], i]
            break
        lookup[num] = i
    return ans if ans is not None else []
"""
    },

    # --- 26 to 40: Clean Independent Submissions (True Negatives, label = 0) ---
    {
        "pair_id": "PAIR-26",
        "category": "Clean Independent",
        "is_plagiarized": 0,
        "student_a": "STU-3051",
        "student_b": "STU-3052",
        "code_a": """def two_sum(nums, target):
    # Two pointers on sorted pairs
    indexed = sorted([(val, i) for i, val in enumerate(nums)])
    left, right = 0, len(nums) - 1
    while left < right:
        s = indexed[left][0] + indexed[right][0]
        if s == target:
            return sorted([indexed[left][1], indexed[right][1]])
        elif s < target:
            left += 1
        else:
            right -= 1
    return []
""",
        "code_b": """def two_sum(nums, target):
    seen = {}
    for i, num in enumerate(nums):
        comp = target - num
        if comp in seen:
            return [seen[comp], i]
        seen[num] = i
    return []
"""
    },
    {
        "pair_id": "PAIR-27",
        "category": "Clean Independent",
        "is_plagiarized": 0,
        "student_a": "STU-3053",
        "student_b": "STU-3054",
        "code_a": """def two_sum(nums, target):
    # Binary search approach
    sorted_pairs = sorted([(nums[i], i) for i in range(len(nums))])
    for i in range(len(nums)):
        needed = target - sorted_pairs[i][0]
        # binary search for needed
        lo, hi = i + 1, len(nums) - 1
        while lo <= hi:
            mid = (lo + hi) // 2
            if sorted_pairs[mid][0] == needed:
                return sorted([sorted_pairs[i][1], sorted_pairs[mid][1]])
            elif sorted_pairs[mid][0] < needed:
                lo = mid + 1
            else:
                hi = mid - 1
    return []
""",
        "code_b": """def two_sum(nums, target):
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]
    return []
"""
    },
    {
        "pair_id": "PAIR-28",
        "category": "Clean Independent",
        "is_plagiarized": 0,
        "student_a": "STU-3055",
        "student_b": "STU-3056",
        "code_a": """def recursive_factorial(n):
    if n <= 1:
        return 1
    return n * recursive_factorial(n - 1)
""",
        "code_b": """def two_sum(nums, target):
    seen = {}
    for i, x in enumerate(nums):
        if target - x in seen:
            return [seen[target - x], i]
        seen[x] = i
    return []
"""
    },
    {
        "pair_id": "PAIR-29",
        "category": "Clean Independent",
        "is_plagiarized": 0,
        "student_a": "STU-3057",
        "student_b": "STU-3058",
        "code_a": """def valid_palindrome(s):
    cleaned = [c.lower() for c in s if c.isalnum()]
    return cleaned == cleaned[::-1]
""",
        "code_b": """def two_sum(nums, target):
    d = {}
    for i in range(len(nums)):
        if target - nums[i] in d:
            return [d[target - nums[i]], i]
        d[nums[i]] = i
    return []
"""
    },
    {
        "pair_id": "PAIR-30",
        "category": "Clean Independent",
        "is_plagiarized": 0,
        "student_a": "STU-3059",
        "student_b": "STU-3060",
        "code_a": """def two_sum(nums, target):
    # Two pointer with dictionary index restore
    nums_with_idx = [[val, i] for i, val in enumerate(nums)]
    nums_with_idx.sort(key=lambda x: x[0])
    p1 = 0
    p2 = len(nums) - 1
    while p1 < p2:
        val_sum = nums_with_idx[p1][0] + nums_with_idx[p2][0]
        if val_sum == target:
            res = [nums_with_idx[p1][1], nums_with_idx[p2][1]]
            res.sort()
            return res
        if val_sum < target:
            p1 += 1
        else:
            p2 -= 1
    return []
""",
        "code_b": """def two_sum(nums, target):
    for i in range(len(nums)):
        val = nums[i]
        rem = target - val
        if rem in nums[i+1:]:
            j = nums[i+1:].index(rem) + i + 1
            return [i, j]
    return []
"""
    },
    {
        "pair_id": "PAIR-31",
        "category": "Clean Independent",
        "is_plagiarized": 0,
        "student_a": "STU-3061",
        "student_b": "STU-3062",
        "code_a": """def two_sum(nums, target):
    counts = {}
    for n in nums:
        counts[n] = counts.get(n, 0) + 1
    for i, n in enumerate(nums):
        c = target - n
        if c == n and counts[n] > 1:
            j = nums.index(c, i + 1)
            return [i, j]
        elif c != n and c in counts:
            return [i, nums.index(c)]
    return []
""",
        "code_b": """def two_sum(nums, target):
    memo = {}
    for idx, v in enumerate(nums):
        if target - v in memo:
            return [memo[target - v], idx]
        memo[v] = idx
    return []
"""
    },
    {
        "pair_id": "PAIR-32",
        "category": "Clean Independent",
        "is_plagiarized": 0,
        "student_a": "STU-3063",
        "student_b": "STU-3064",
        "code_a": """def two_sum(nums, target):
    # Sorting and bisect
    import bisect
    pairs = sorted((val, idx) for idx, val in enumerate(nums))
    vals = [p[0] for p in pairs]
    for i, (v, orig_i) in enumerate(pairs):
        partner = target - v
        idx = bisect.bisect_left(vals, partner, i + 1)
        if idx < len(vals) and vals[idx] == partner:
            return sorted([orig_i, pairs[idx][1]])
    return []
""",
        "code_b": """def two_sum(nums, target):
    cache = {}
    for i in range(len(nums)):
        x = nums[i]
        diff = target - x
        if diff in cache:
            return [cache[diff], i]
        cache[x] = i
    return []
"""
    },
    {
        "pair_id": "PAIR-33",
        "category": "Clean Independent",
        "is_plagiarized": 0,
        "student_a": "STU-3065",
        "student_b": "STU-3066",
        "code_a": """def find_max(arr):
    if not arr:
        return None
    m = arr[0]
    for x in arr:
        if x > m:
            m = x
    return m
""",
        "code_b": """def two_sum(nums, target):
    seen = {}
    for i, num in enumerate(nums):
        comp = target - num
        if comp in seen:
            return [seen[comp], i]
        seen[num] = i
    return []
"""
    },
    {
        "pair_id": "PAIR-34",
        "category": "Clean Independent",
        "is_plagiarized": 0,
        "student_a": "STU-3067",
        "student_b": "STU-3068",
        "code_a": """def binary_search(arr, x):
    l, r = 0, len(arr) - 1
    while l <= r:
        m = (l + r) // 2
        if arr[m] == x: return m
        elif arr[m] < x: l = m + 1
        else: r = m - 1
    return -1
""",
        "code_b": """def two_sum(nums, target):
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]
    return []
"""
    },
    {
        "pair_id": "PAIR-35",
        "category": "Clean Independent",
        "is_plagiarized": 0,
        "student_a": "STU-3069",
        "student_b": "STU-3070",
        "code_a": """def merge_sorted(a, b):
    res = []
    i, j = 0, 0
    while i < len(a) and j < len(b):
        if a[i] < b[j]:
            res.append(a[i])
            i += 1
        else:
            res.append(b[j])
            j += 1
    res.extend(a[i:])
    res.extend(b[j:])
    return res
""",
        "code_b": """def two_sum(nums, target):
    d = {}
    for i, n in enumerate(nums):
        if target - n in d:
            return [d[target - n], i]
        d[n] = i
    return []
"""
    },
    {
        "pair_id": "PAIR-36",
        "category": "Clean Independent",
        "is_plagiarized": 0,
        "student_a": "STU-3071",
        "student_b": "STU-3072",
        "code_a": """def count_vowels(s):
    v = set("aeiouAEIOU")
    return sum(1 for c in s if c in v)
""",
        "code_b": """def two_sum(nums, target):
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]
    return []
"""
    },
    {
        "pair_id": "PAIR-37",
        "category": "Clean Independent",
        "is_plagiarized": 0,
        "student_a": "STU-3073",
        "student_b": "STU-3074",
        "code_a": """def reverse_list(head):
    prev = None
    curr = head
    while curr:
        nxt = curr.next
        curr.next = prev
        prev = curr
        curr = nxt
    return prev
""",
        "code_b": """def two_sum(nums, target):
    memo = {}
    for i, x in enumerate(nums):
        comp = target - x
        if comp in memo:
            return [memo[comp], i]
        memo[x] = i
    return []
"""
    },
    {
        "pair_id": "PAIR-38",
        "category": "Clean Independent",
        "is_plagiarized": 0,
        "student_a": "STU-3075",
        "student_b": "STU-3076",
        "code_a": """def two_sum(nums, target):
    # Exhaustive recursion
    def helper(idx, chosen):
        if len(chosen) == 2:
            i, j = chosen
            if nums[i] + nums[j] == target:
                return [i, j]
            return None
        if idx >= len(nums):
            return None
        # include or exclude
        with_curr = helper(idx + 1, chosen + [idx])
        if with_curr: return with_curr
        return helper(idx + 1, chosen)
    res = helper(0, [])
    return res if res else []
""",
        "code_b": """def two_sum(nums, target):
    store = {}
    for i, n in enumerate(nums):
        rem = target - n
        if rem in store:
            return [store[rem], i]
        store[n] = i
    return []
"""
    },
    {
        "pair_id": "PAIR-39",
        "category": "Clean Independent",
        "is_plagiarized": 0,
        "student_a": "STU-3077",
        "student_b": "STU-3078",
        "code_a": """def is_prime(n):
    if n <= 1: return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0: return False
    return True
""",
        "code_b": """def two_sum(nums, target):
    seen = {}
    for i, v in enumerate(nums):
        if target - v in seen:
            return [seen[target - v], i]
        seen[v] = i
    return []
"""
    },
    {
        "pair_id": "PAIR-40",
        "category": "Clean Independent",
        "is_plagiarized": 0,
        "student_a": "STU-3079",
        "student_b": "STU-3080",
        "code_a": """def fibonacci(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a
""",
        "code_b": """def two_sum(nums, target):
    m = {}
    for i, num in enumerate(nums):
        diff = target - num
        if diff in m:
            return [m[diff], i]
        m[num] = i
    return []
"""
    }
]
