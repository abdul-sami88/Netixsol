"""
Inter-Rater Agreement Metrics for Rubric Grading
Calculates Pearson Correlation, Cohen's Kappa, Quadratic Weighted Kappa (QWK),
and Fleiss' Multi-Rater Kappa across LLM and Human Graders.
"""

import numpy as np
from typing import Dict, Any, List

def compute_quadratic_weighted_kappa(rater_a: List[int], rater_b: List[int], min_rating: int = 0, max_rating: int = 10) -> float:
    """
    Computes Quadratic Weighted Kappa (QWK) for ordinal rubric scores.
    """
    num_ratings = max_rating - min_rating + 1
    conf_mat = np.zeros((num_ratings, num_ratings), dtype=float)

    for a, b in zip(rater_a, rater_b):
        idx_a = max(0, min(num_ratings - 1, a - min_rating))
        idx_b = max(0, min(num_ratings - 1, b - min_rating))
        conf_mat[idx_a, idx_b] += 1.0

    n = len(rater_a)
    if n == 0:
        return 0.0

    # Weight matrix
    w = np.zeros((num_ratings, num_ratings), dtype=float)
    for i in range(num_ratings):
        for j in range(num_ratings):
            w[i, j] = ((i - j) ** 2) / ((num_ratings - 1) ** 2)

    # Marginals & Expected matrix
    hist_a = np.sum(conf_mat, axis=1)
    hist_b = np.sum(conf_mat, axis=0)
    expected = np.outer(hist_a, hist_b) / n

    # Kappa numerator and denominator
    numerator = np.sum(w * conf_mat)
    denominator = np.sum(w * expected)

    if denominator == 0:
        return 1.0
    return float(1.0 - (numerator / denominator))


def compute_cohens_kappa_binned(rater_a: List[int], rater_b: List[int]) -> float:
    """
    Computes standard unweighted Cohen's Kappa on 4 achievement tiers:
    0: Fail/Poor (0-3), 1: Developing (4-6), 2: Proficient (7-8), 3: Exemplary (9-10)
    """
    def to_tier(score):
        if score <= 3: return 0
        if score <= 6: return 1
        if score <= 8: return 2
        return 3

    tiers_a = [to_tier(s) for s in rater_a]
    tiers_b = [to_tier(s) for s in rater_b]

    n = len(tiers_a)
    k = 4
    conf = np.zeros((k, k), dtype=float)
    for a, b in zip(tiers_a, tiers_b):
        conf[a, b] += 1

    po = np.trace(conf) / n
    pe = np.sum(np.sum(conf, axis=1) * np.sum(conf, axis=0)) / (n ** 2)

    if 1.0 - pe == 0:
        return 1.0
    return float((po - pe) / (1.0 - pe))


def compute_fleiss_kappa(ratings_matrix: np.ndarray) -> float:
    """
    Computes Fleiss' Kappa across N subjects and k categories.
    ratings_matrix has shape (N, k) where each entry is count of raters assigning subject i to category j.
    """
    N, k = ratings_matrix.shape
    n = np.sum(ratings_matrix[0, :]) # raters per subject

    p_j = np.sum(ratings_matrix, axis=0) / (N * n)
    P_i = (np.sum(ratings_matrix ** 2, axis=1) - n) / (n * (n - 1))

    P_bar = np.mean(P_i)
    P_e_bar = np.sum(p_j ** 2)

    if 1.0 - P_e_bar == 0:
        return 1.0
    return float((P_bar - P_e_bar) / (1.0 - P_e_bar))
