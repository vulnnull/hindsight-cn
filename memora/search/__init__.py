"""
Search module for memory retrieval.

Provides modular search architecture:
- Retrieval: 3-way parallel (semantic + BM25 + graph)
- Reranking: Pluggable strategies (heuristic, cross-encoder)
- MMR: Diversity enforcement
"""

from .retrieval import retrieve_parallel
from .reranking import Reranker, HeuristicReranker, CrossEncoderReranker
from .mmr import apply_mmr

__all__ = [
    "retrieve_parallel",
    "Reranker",
    "HeuristicReranker",
    "CrossEncoderReranker",
    "apply_mmr",
]
