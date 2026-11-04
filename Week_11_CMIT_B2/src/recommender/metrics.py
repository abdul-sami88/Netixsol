"""
Recommender Systems Evaluation Metrics Module
Implements standard offline evaluation metrics for Top-K ranking:
- Precision@K, Recall@K, Hit Rate@K
- NDCG@K (Normalized Discounted Cumulative Gain)
- MAP@K (Mean Average Precision)
- Catalogue Coverage
- Intra-List Diversity (Category / Jaccard distance)
- Novelty (Self-information / Inverse Popularity)
"""

import math
import numpy as np
from typing import List, Set, Dict

def precision_at_k(recommended: List[str], ground_truth: Set[str], k: int = 10) -> float:
    if k <= 0 or not ground_truth:
        return 0.0
    rec_k = recommended[:k]
    hits = sum(1 for item in rec_k if item in ground_truth)
    return hits / k

def recall_at_k(recommended: List[str], ground_truth: Set[str], k: int = 10) -> float:
    if not ground_truth or k <= 0:
        return 0.0
    rec_k = recommended[:k]
    hits = sum(1 for item in rec_k if item in ground_truth)
    return hits / len(ground_truth)

def hit_rate_at_k(recommended: List[str], ground_truth: Set[str], k: int = 10) -> float:
    if not ground_truth or k <= 0:
        return 0.0
    rec_k = recommended[:k]
    return 1.0 if any(item in ground_truth for item in rec_k) else 0.0

def ndcg_at_k(recommended: List[str], ground_truth: Set[str], k: int = 10) -> float:
    if not ground_truth or k <= 0:
        return 0.0
    rec_k = recommended[:k]
    
    # Calculate DCG
    dcg = 0.0
    for i, item in enumerate(rec_k):
        if item in ground_truth:
            dcg += 1.0 / math.log2(i + 2)
            
    # Calculate Ideal DCG (IDCG)
    ideal_hits = min(k, len(ground_truth))
    idcg = sum(1.0 / math.log2(i + 2) for i in range(ideal_hits))
    
    return dcg / idcg if idcg > 0 else 0.0

def map_at_k(recommended: List[str], ground_truth: Set[str], k: int = 10) -> float:
    if not ground_truth or k <= 0:
        return 0.0
    rec_k = recommended[:k]
    
    score = 0.0
    num_hits = 0.0
    for i, item in enumerate(rec_k):
        if item in ground_truth:
            num_hits += 1.0
            score += num_hits / (i + 1.0)
            
    ideal_hits = min(k, len(ground_truth))
    return score / ideal_hits if ideal_hits > 0 else 0.0

def compute_catalogue_coverage(all_recommendations: List[List[str]], total_catalogue_size: int, k: int = 10) -> float:
    """Fraction of unique items in catalogue recommended to at least one user."""
    unique_rec_items = set()
    for recs in all_recommendations:
        unique_rec_items.update(recs[:k])
    return (len(unique_rec_items) / total_catalogue_size) * 100.0 if total_catalogue_size > 0 else 0.0

def compute_novelty(all_recommendations: List[List[str]], item_popularity_prob: Dict[str, float], k: int = 10) -> float:
    """Mean self-information: -log2(P(item)) across recommended items."""
    novelty_scores = []
    min_prob = 1e-6
    for recs in all_recommendations:
        rec_k = recs[:k]
        if not rec_k:
            continue
        list_novelty = [
            -math.log2(item_popularity_prob.get(item, min_prob))
            for item in rec_k
        ]
        novelty_scores.append(np.mean(list_novelty))
    return float(np.mean(novelty_scores)) if novelty_scores else 0.0

def compute_diversity(all_recommendations: List[List[str]], item_to_category: Dict[str, str], k: int = 10) -> float:
    """Measures intra-list category entropy/diversity (fraction of distinct categories per top-K list)."""
    div_scores = []
    for recs in all_recommendations:
        rec_k = recs[:k]
        if len(rec_k) <= 1:
            continue
        cats = [item_to_category.get(item, "Unknown") for item in rec_k]
        unique_cats = len(set(cats))
        div_scores.append(unique_cats / len(rec_k))
    return float(np.mean(div_scores)) if div_scores else 0.0
