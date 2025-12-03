"""
Cross-encoder abstraction for reranking.

Provides an interface for reranking with different backends.
"""
from abc import ABC, abstractmethod
from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)


class CrossEncoderModel(ABC):
    """
    Abstract base class for cross-encoder reranking.

    Cross-encoders take query-document pairs and return relevance scores.
    """

    @abstractmethod
    def load(self) -> None:
        """
        Load the cross-encoder model.

        This should be called during initialization to load the model
        and avoid cold start latency on first predict() call.
        """
        pass

    @abstractmethod
    def predict(self, pairs: List[Tuple[str, str]]) -> List[float]:
        """
        Score query-document pairs for relevance.

        Args:
            pairs: List of (query, document) tuples to score

        Returns:
            List of relevance scores (higher = more relevant)
        """
        pass


class SentenceTransformersCrossEncoder(CrossEncoderModel):
    """
    Cross-encoder implementation using SentenceTransformers.

    Call load() during initialization to load the model and avoid cold starts.

    Default model is cross-encoder/ms-marco-MiniLM-L-6-v2:
    - Fast inference (~80ms for 100 pairs on CPU)
    - Small model (80MB)
    - Trained for passage re-ranking
    """

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        """
        Initialize SentenceTransformers cross-encoder.

        Args:
            model_name: Name of the CrossEncoder model to use.
                       Default: cross-encoder/ms-marco-MiniLM-L-6-v2
        """
        self.model_name = model_name
        self._model = None

    def load(self) -> None:
        """Load the cross-encoder model."""
        if self._model is not None:
            return

        try:
            from sentence_transformers import CrossEncoder
        except ImportError:
            raise ImportError(
                "sentence-transformers is required for SentenceTransformersCrossEncoder. "
                "Install it with: pip install sentence-transformers"
            )

        logger.info(f"Loading cross-encoder model: {self.model_name}...")
        self._model = CrossEncoder(self.model_name)
        logger.info("Cross-encoder model loaded")

    def predict(self, pairs: List[Tuple[str, str]]) -> List[float]:
        """
        Score query-document pairs for relevance.

        Args:
            pairs: List of (query, document) tuples to score

        Returns:
            List of relevance scores (raw logits from the model)
        """
        if self._model is None:
            self.load()
        scores = self._model.predict(pairs, show_progress_bar=False)
        return scores.tolist() if hasattr(scores, 'tolist') else list(scores)
