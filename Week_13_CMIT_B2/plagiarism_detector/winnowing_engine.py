"""
Stanford MOSS-Style Winnowing & Semantic Fingerprinting Engine
Implements:
1. K-gram tokenization and rolling polynomial hashing
2. Sliding-window minimum selection (Winnowing algorithm)
3. Jaccard & Containment set overlap calculation
4. Structural AST Vector Cosine Similarity
5. Composite Similarity Index (0.0 to 1.0)
"""

import math
from typing import List, Tuple, Set, Dict, Any
from collections import Counter
import os
import sys

# Ensure local imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from plagiarism_detector.ast_tokenizer import ASTTokenNormalizer

class WinnowingPlagiarismEngine:
    """
    Computes structural similarity between code snippets using Winnowing fingerprints
    and AST structural vector embeddings.
    """

    K_GRAM_SIZE = 5     # Length of token k-gram sequence
    WINDOW_SIZE = 4     # Sliding window for fingerprint selection
    BASE = 257          # Polynomial hash base
    MODULUS = 1000000007 # Large prime modulus

    def __init__(self, k: int = K_GRAM_SIZE, w: int = WINDOW_SIZE):
        self.k = k
        self.w = w
        self.normalizer = ASTTokenNormalizer()

    def _hash_kgram(self, tokens: List[str]) -> int:
        """
        Computes rolling polynomial hash for a k-gram of tokens.
        """
        h = 0
        for tok in tokens:
            # Map token string to integer hash seed
            tok_val = sum(ord(c) for c in tok)
            h = (h * self.BASE + tok_val) % self.MODULUS
        return h

    def generate_fingerprints(self, code_str: str) -> Tuple[Set[int], List[Tuple[int, int]], Counter]:
        """
        Extracts winnowing fingerprints and token counts from source code.
        Returns:
            - unique_hashes: set of chosen fingerprint hash values
            - located_fingerprints: list of (hash_val, line_number)
            - token_vector: Counter of AST node token occurrences
        """
        token_tuples = self.normalizer.normalize(code_str)
        token_strs = [t[0] for t in token_tuples]
        line_numbers = [t[1] for t in token_tuples]

        token_vector = Counter(token_strs)

        n = len(token_strs)
        if n < self.k:
            # If code is shorter than k-gram, use single composite hash
            h = self._hash_kgram(token_strs) if token_strs else 0
            return {h}, [(h, 1)], token_vector

        # 1. Generate all k-gram hashes
        hashes: List[Tuple[int, int]] = []
        for i in range(n - self.k + 1):
            kgram = token_strs[i : i + self.k]
            h = self._hash_kgram(kgram)
            line = line_numbers[i]
            hashes.append((h, line))

        # 2. Sliding window winnowing
        m = len(hashes)
        if m < self.w:
            # Fewer hashes than window size: pick global minimum
            min_h = min(hashes, key=lambda x: x[0])
            return {min_h[0]}, [min_h], token_vector

        chosen_hashes: Set[int] = set()
        chosen_records: List[Tuple[int, int]] = []
        prev_min_idx = -1

        for i in range(m - self.w + 1):
            window = hashes[i : i + self.w]
            # Select rightmost minimum to guarantee bounded guarantees
            min_val = min(h[0] for h in window)
            # Find rightmost occurrence in this window
            for j in range(self.w - 1, -1, -1):
                if window[j][0] == min_val:
                    min_idx = i + j
                    if min_idx != prev_min_idx:
                        chosen_hashes.add(min_val)
                        chosen_records.append(hashes[min_idx])
                        prev_min_idx = min_idx
                    break

        return chosen_hashes, chosen_records, token_vector

    def compute_cosine_similarity(self, vec1: Counter, vec2: Counter) -> float:
        """
        Computes cosine similarity between token frequency vectors.
        """
        all_keys = set(vec1.keys()).union(set(vec2.keys()))
        if not all_keys:
            return 0.0

        dot_product = sum(vec1[k] * vec2[k] for k in all_keys)
        norm1 = math.sqrt(sum(v ** 2 for v in vec1.values()))
        norm2 = math.sqrt(sum(v ** 2 for v in vec2.values()))

        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot_product / (norm1 * norm2)

    def compare_submissions(self, code_a: str, code_b: str) -> Dict[str, Any]:
        """
        Compares two submissions and calculates winnowing containment, Jaccard index,
        AST vector cosine similarity, and composite plagiarism score.
        """
        hashes_a, loc_a, vec_a = self.generate_fingerprints(code_a)
        hashes_b, loc_b, vec_b = self.generate_fingerprints(code_b)

        # Set intersection & union
        intersection = hashes_a.intersection(hashes_b)
        union = hashes_a.union(hashes_b)

        # Jaccard index
        jaccard = len(intersection) / len(union) if union else 0.0

        # Containment index: fraction of smaller code's fingerprints found in larger
        min_size = min(len(hashes_a), len(hashes_b))
        containment = len(intersection) / min_size if min_size > 0 else 0.0

        # Vector cosine similarity
        cosine_sim = self.compute_cosine_similarity(vec_a, vec_b)

        # Composite Plagiarism Score: 60% Containment + 40% Vector Cosine
        composite_score = (0.60 * containment) + (0.40 * cosine_sim)
        composite_score = round(min(1.0, max(0.0, composite_score)), 4)

        return {
            "composite_similarity": composite_score,
            "containment_similarity": round(containment, 4),
            "jaccard_similarity": round(jaccard, 4),
            "ast_vector_cosine": round(cosine_sim, 4),
            "shared_fingerprints_count": len(intersection),
            "fingerprints_a_count": len(hashes_a),
            "fingerprints_b_count": len(hashes_b)
        }
