"""
Search module for memory retrieval.

Provides modular search architecture:
- Retrieval: 4-way parallel (semantic + BM25 + graph + temporal)
- Reranking: Pluggable strategies (heuristic, cross-encoder)
"""

from .retrieval import retrieve_parallel
from .reranking import CrossEncoderReranker

__all__ = [
    "retrieve_parallel",
    "CrossEncoderReranker",
]
