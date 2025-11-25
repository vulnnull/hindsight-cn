"""
Helper functions for hybrid search (semantic + BM25 + graph).
"""

from typing import List, Dict, Any, Tuple
import asyncio


def reciprocal_rank_fusion(
    result_lists: List[List[Tuple[str, Dict[str, Any]]]],
    k: int = 60
) -> List[Tuple[str, Dict[str, Any], Dict[str, float]]]:
    """
    Merge multiple ranked result lists using Reciprocal Rank Fusion.

    RRF formula: score(d) = sum_over_lists(1 / (k + rank(d)))

    Args:
        result_lists: List of result lists, each containing (id, data) tuples
        k: Constant for RRF formula (default: 60)

    Returns:
        Merged list of (id, data, scores_dict) tuples, sorted by RRF score

    Example:
        semantic_results = [("id1", {...}), ("id2", {...}), ...]
        bm25_results = [("id2", {...}), ("id3", {...}), ...]
        graph_results = [("id1", {...}), ("id4", {...}), ...]

        merged = reciprocal_rank_fusion([semantic_results, bm25_results, graph_results])
        # Returns: [("id2", {...}, {"rrf": 0.05, "semantic_rank": 2, ...}), ...]
    """
    # Track scores from each list
    rrf_scores = {}
    source_ranks = {}  # Track rank from each source
    source_scores = {}  # Track original score from each source
    all_data = {}  # Store the actual data

    source_names = ["semantic", "bm25", "graph"]

    for source_idx, results in enumerate(result_lists):
        source_name = source_names[source_idx] if source_idx < len(source_names) else f"source_{source_idx}"

        for rank, (doc_id, data) in enumerate(results, start=1):
            # Store data (use first occurrence)
            if doc_id not in all_data:
                all_data[doc_id] = data

            # Calculate RRF score contribution
            if doc_id not in rrf_scores:
                rrf_scores[doc_id] = 0.0
                source_ranks[doc_id] = {}
                source_scores[doc_id] = {}

            rrf_scores[doc_id] += 1.0 / (k + rank)
            source_ranks[doc_id][f"{source_name}_rank"] = rank

            # Store original score if available
            if "score" in data:
                source_scores[doc_id][f"{source_name}_score"] = data["score"]

    # Combine into final results with metadata
    merged_results = []
    for doc_id, rrf_score in sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True):
        scores_dict = {
            "rrf_score": rrf_score,
            **source_ranks[doc_id],
            **source_scores[doc_id]
        }
        merged_results.append((doc_id, all_data[doc_id], scores_dict))

    return merged_results


def normalize_scores_on_deltas(
    results: List[Dict[str, Any]],
    score_keys: List[str]
) -> List[Dict[str, Any]]:
    """
    Normalize scores based on deltas (min-max normalization within result set).

    This ensures all scores are in [0, 1] range based on the spread in THIS result set.

    Args:
        results: List of result dicts
        score_keys: Keys to normalize (e.g., ["recency", "frequency"])

    Returns:
        Results with normalized scores added as "{key}_normalized"
    """
    for key in score_keys:
        values = [r.get(key, 0.0) for r in results if key in r]

        if not values:
            continue

        min_val = min(values)
        max_val = max(values)
        delta = max_val - min_val

        if delta > 0:
            for r in results:
                if key in r:
                    r[f"{key}_normalized"] = (r[key] - min_val) / delta
        else:
            # All values are the same, set to 0.5
            for r in results:
                if key in r:
                    r[f"{key}_normalized"] = 0.5

    return results
