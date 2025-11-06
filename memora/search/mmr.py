"""
Maximal Marginal Relevance (MMR) for diversity in search results.
"""

from typing import List, Dict, Any
import numpy as np
import json


def apply_mmr(
    results: List[Dict[str, Any]],
    top_k: int,
    mmr_lambda: float,
    log_buffer: List[str]
) -> List[Dict[str, Any]]:
    """
    Apply Maximal Marginal Relevance (MMR) to diversify search results.

    MMR balances relevance with diversity by selecting results that are:
    1. Relevant to the query (high score)
    2. Different from already selected results (low similarity)

    Formula: MMR = λ * relevance - (1-λ) * max_similarity_to_selected

    Args:
        results: Sorted list of all results with embeddings
        top_k: Number of results to select
        mmr_lambda: Balance parameter (0=max diversity, 1=max relevance)
        log_buffer: Buffer for logging

    Returns:
        List of selected results with MMR metadata
    """
    if not results or top_k <= 0:
        return []

    if len(results) <= top_k:
        # Not enough results for MMR to matter
        for idx, result in enumerate(results):
            result["original_rank"] = idx + 1
            result["mmr_score"] = None
            result["mmr_relevance"] = None
            result["mmr_max_similarity"] = None
            result["mmr_diversified"] = False
            result.pop("embedding", None)
        return results

    # Normalize relevance scores to [0, 1] for fair comparison
    weights = [r["weight"] for r in results]
    min_weight = min(weights)
    max_weight = max(weights)
    weight_range = max_weight - min_weight

    if weight_range > 0:
        for r in results:
            r["_normalized_weight"] = (r["weight"] - min_weight) / weight_range
    else:
        for r in results:
            r["_normalized_weight"] = 1.0

    # Convert embeddings to numpy arrays
    for r in results:
        emb = r.get("embedding")
        if emb is not None:
            if isinstance(emb, str):
                emb = json.loads(emb)
            if not isinstance(emb, np.ndarray):
                emb = np.array(emb, dtype=np.float64)
            r["_embedding"] = emb
        else:
            r["_embedding"] = None

    # MMR selection
    selected = []
    remaining = list(results)
    diversified_count = 0

    for _ in range(top_k):
        if not remaining:
            break

        if not selected:
            # First result: pick highest relevance
            best_idx = 0
            best = remaining[best_idx]
            best_relevance = best["_normalized_weight"]
            best_max_similarity = 0.0
        else:
            # Subsequent results: balance relevance and diversity
            best_idx = None
            best_mmr_score = float('-inf')
            best_relevance = 0.0
            best_max_similarity = 0.0

            for idx, candidate in enumerate(remaining):
                relevance = candidate["_normalized_weight"]

                # Calculate max similarity to already selected results
                max_similarity = 0.0
                candidate_emb = candidate.get("_embedding")

                if candidate_emb is not None:
                    for selected_result in selected:
                        selected_emb = selected_result.get("_embedding")
                        if selected_emb is not None:
                            # Cosine similarity
                            dot_product = np.dot(candidate_emb, selected_emb)
                            norm_candidate = np.linalg.norm(candidate_emb)
                            norm_selected = np.linalg.norm(selected_emb)
                            if norm_candidate > 0 and norm_selected > 0:
                                similarity = dot_product / (norm_candidate * norm_selected)
                                max_similarity = max(max_similarity, similarity)

                # MMR score
                mmr_score = mmr_lambda * relevance - (1 - mmr_lambda) * max_similarity

                if mmr_score > best_mmr_score:
                    best_mmr_score = mmr_score
                    best_idx = idx
                    best_relevance = relevance
                    best_max_similarity = max_similarity

        # Select best result
        best = remaining.pop(best_idx)
        best["original_rank"] = len(selected) + 1
        best["mmr_score"] = best_mmr_score if selected else best_relevance
        best["mmr_relevance"] = best_relevance
        best["mmr_max_similarity"] = best_max_similarity

        # Check if this was a diversified pick (not top of remaining by relevance)
        if selected and best_idx > 0:
            best["mmr_diversified"] = True
            diversified_count += 1
        else:
            best["mmr_diversified"] = False

        selected.append(best)

    # Clean up temporary fields and embeddings
    for r in selected:
        r.pop("_normalized_weight", None)
        r.pop("_embedding", None)
        r.pop("embedding", None)

    log_buffer.append(f"      MMR: Selected {len(selected)} results, {diversified_count} diversified picks")

    return selected
