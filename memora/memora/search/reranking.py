"""
Reranking abstraction for search results.

Supports multiple reranking strategies:
1. Heuristic: Weighted combination of semantic + BM25 + normalized boosts
2. Cross-encoder: Neural reranking using a transformer model
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime, timezone
import numpy as np


def utcnow():
    """Get current UTC time."""
    return datetime.now(timezone.utc)


def calculate_recency_weight(days_since: float) -> float:
    """Calculate recency weight using exponential decay."""
    half_life_days = 30.0
    return np.exp(-np.log(2) * days_since / half_life_days)


def calculate_frequency_weight(access_count: int) -> float:
    """Calculate frequency weight using logarithmic scale."""
    return 1.0 + np.log1p(access_count) * 0.1


class Reranker(ABC):
    """Abstract base class for reranking strategies."""

    @abstractmethod
    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        Rerank candidates and return top_k results.

        Args:
            query: Search query
            candidates: List of candidate documents with scores
            top_k: Number of top results to return

        Returns:
            Reranked list of candidates (not limited to top_k, that's done by MMR)
        """
        pass


class HeuristicReranker(Reranker):
    """
    Heuristic reranking using weighted combination of signals.

    Scoring formula:
    - Base: 60% semantic_similarity + 40% bm25_normalized
    - Recency boost: +20% (normalized on deltas)
    - Frequency boost: +10% (normalized on deltas)
    """

    def __init__(self):
        """Initialize heuristic reranker."""
        pass

    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Rerank using heuristic scoring."""
        from ..search_helpers import normalize_scores_on_deltas

        # Calculate recency and frequency for all candidates
        for c in candidates:
            event_date = c["event_date"]
            if isinstance(event_date, str):
                event_date = datetime.fromisoformat(event_date)

            days_since = (utcnow() - event_date).total_seconds() / 86400
            c["recency"] = calculate_recency_weight(days_since)
            c["frequency"] = calculate_frequency_weight(c.get("access_count", 0))

        # Normalize recency and frequency on deltas
        candidates = normalize_scores_on_deltas(candidates, ["recency", "frequency"])

        # Normalize BM25 scores
        bm25_scores = [c["bm25_score"] for c in candidates if c["bm25_score"] > 0]
        if bm25_scores:
            max_bm25 = max(bm25_scores)
            for c in candidates:
                c["bm25_score_normalized"] = c["bm25_score"] / max_bm25 if max_bm25 > 0 else 0.0
        else:
            for c in candidates:
                c["bm25_score_normalized"] = 0.0

        # Calculate final score
        for c in candidates:
            # Base score: weighted combination of semantic and BM25
            base_score = (
                0.6 * c["semantic_similarity"] +
                0.4 * c["bm25_score_normalized"]
            )

            # Apply normalized boosts
            recency_boost = 1.0 + (0.2 * c.get("recency_normalized", 0.0))
            frequency_boost = 1.0 + (0.1 * c.get("frequency_normalized", 0.0))

            final_score = base_score * recency_boost * frequency_boost

            c["weight"] = final_score

        # Sort by final weight
        candidates.sort(key=lambda x: x["weight"], reverse=True)

        return candidates


class CrossEncoderReranker(Reranker):
    """
    Neural reranking using a cross-encoder model.

    Uses cross-encoder/ms-marco-MiniLM-L-6-v2 by default:
    - Fast inference (~80ms for 100 pairs on CPU)
    - Small model (80MB)
    - Trained for passage re-ranking
    """

    def __init__(self, cross_encoder=None):
        """
        Initialize cross-encoder reranker.

        Args:
            cross_encoder: CrossEncoderReranker instance. If None, uses default
                          SentenceTransformersCrossEncoder with ms-marco-MiniLM-L-6-v2
        """
        if cross_encoder is None:
            from ..cross_encoder import SentenceTransformersCrossEncoder
            cross_encoder = SentenceTransformersCrossEncoder()
        self.cross_encoder = cross_encoder

    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Rerank using cross-encoder scores."""
        if not candidates:
            return candidates

        # Prepare query-document pairs with date information
        pairs = []
        for c in candidates:
            # Use text + context for better ranking
            doc_text = c["text"]
            if c.get("context"):
                doc_text = f"{c['context']}: {doc_text}"

            # Add formatted date information for temporal awareness
            if c.get("event_date"):
                event_date = c["event_date"]

                # Format in two styles for better model understanding
                # 1. ISO format: YYYY-MM-DD
                date_iso = event_date.strftime("%Y-%m-%d")

                # 2. Human-readable: "June 5, 2022"
                date_readable = event_date.strftime("%B %d, %Y")

                # Prepend date to document text
                doc_text = f"[Date: {date_readable} ({date_iso})] {doc_text}"

            pairs.append([query, doc_text])

        # Get cross-encoder scores
        scores = self.cross_encoder.predict(pairs)

        # Normalize scores using sigmoid to [0, 1] range
        # Cross-encoder returns logits which can be negative
        import numpy as np
        def sigmoid(x):
            return 1 / (1 + np.exp(-x))

        normalized_scores = [sigmoid(score) for score in scores]

        # Assign normalized scores to candidates
        for c, raw_score, norm_score in zip(candidates, scores, normalized_scores):
            c["weight"] = float(norm_score)
            c["cross_encoder_score"] = float(raw_score)
            c["cross_encoder_score_normalized"] = float(norm_score)

        # Sort by cross-encoder score
        candidates.sort(key=lambda x: x["weight"], reverse=True)

        return candidates
