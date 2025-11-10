"""
Search module for memory retrieval.

Provides modular search architecture:
- Retrieval: 4-way parallel (semantic + BM25 + graph + temporal)
- Reranking: Pluggable strategies (heuristic, cross-encoder)
"""

from .retrieval import retrieve_parallel
from .reranking import Reranker, HeuristicReranker, CrossEncoderReranker

__all__ = [
    "retrieve_parallel",
    "Reranker",
    "HeuristicReranker",
    "CrossEncoderReranker",
]
