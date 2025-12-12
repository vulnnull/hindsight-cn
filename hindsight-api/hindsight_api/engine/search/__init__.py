"""
Search module for memory retrieval.

Provides modular search architecture:
- Retrieval: 4-way parallel (semantic + BM25 + graph + temporal)
- Graph retrieval: Pluggable strategies (BFS, PPR)
- Reranking: Pluggable strategies (heuristic, cross-encoder)
"""

from .retrieval import (
    retrieve_parallel,
    get_default_graph_retriever,
    set_default_graph_retriever,
)
from .graph_retrieval import GraphRetriever, BFSGraphRetriever
from .reranking import CrossEncoderReranker

__all__ = [
    "retrieve_parallel",
    "get_default_graph_retriever",
    "set_default_graph_retriever",
    "GraphRetriever",
    "BFSGraphRetriever",
    "CrossEncoderReranker",
]
