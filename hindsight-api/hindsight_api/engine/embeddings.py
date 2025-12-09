"""
Embeddings abstraction for the memory system.

Provides an interface for generating embeddings with different backends.

IMPORTANT: All embeddings must produce 384-dimensional vectors to match
the database schema (pgvector column defined as vector(384)).
"""
from abc import ABC, abstractmethod
from typing import List
import logging

logger = logging.getLogger(__name__)

# Fixed embedding dimension required by database schema
EMBEDDING_DIMENSION = 384


class Embeddings(ABC):
    """
    Abstract base class for embedding generation.

    All implementations MUST generate 384-dimensional embeddings to match
    the database schema.
    """

    @abstractmethod
    def load(self) -> None:
        """
        Load the embedding model.

        This should be called during initialization to load the model
        and avoid cold start latency on first encode() call.
        """
        pass

    @abstractmethod
    def encode(self, texts: List[str]) -> List[List[float]]:
        """
        Generate 384-dimensional embeddings for a list of texts.

        Args:
            texts: List of text strings to encode

        Returns:
            List of 384-dimensional embedding vectors (each is a list of floats)
        """
        pass


class SentenceTransformersEmbeddings(Embeddings):
    """
    Embeddings implementation using SentenceTransformers.

    Call load() during initialization to load the model and avoid cold starts.

    Default model is BAAI/bge-small-en-v1.5 which produces 384-dimensional
    embeddings matching the database schema.
    """

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        """
        Initialize SentenceTransformers embeddings.

        Args:
            model_name: Name of the SentenceTransformer model to use.
                       Must produce 384-dimensional embeddings.
                       Default: BAAI/bge-small-en-v1.5
        """
        self.model_name = model_name
        self._model = None

    def load(self) -> None:
        """Load the embedding model."""
        if self._model is not None:
            return

        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError(
                "sentence-transformers is required for SentenceTransformersEmbeddings. "
                "Install it with: pip install sentence-transformers"
            )

        logger.info(f"Loading embedding model: {self.model_name}...")
        # Disable lazy loading (meta tensors) which causes issues with newer transformers/accelerate
        # Setting low_cpu_mem_usage=False and device_map=None ensures tensors are fully materialized
        self._model = SentenceTransformer(
            self.model_name,
            model_kwargs={"low_cpu_mem_usage": False, "device_map": None},
        )

        # Validate dimension matches database schema
        model_dim = self._model.get_sentence_embedding_dimension()
        if model_dim != EMBEDDING_DIMENSION:
            raise ValueError(
                f"Model {self.model_name} produces {model_dim}-dimensional embeddings, "
                f"but database schema requires {EMBEDDING_DIMENSION} dimensions. "
                f"Use a model that produces {EMBEDDING_DIMENSION}-dimensional embeddings."
            )

        logger.info(f"Model loaded (embedding dim: {model_dim})")

    def encode(self, texts: List[str]) -> List[List[float]]:
        """
        Generate 384-dimensional embeddings for a list of texts.

        Args:
            texts: List of text strings to encode

        Returns:
            List of 384-dimensional embedding vectors
        """
        if self._model is None:
            self.load()
        embeddings = self._model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        return [emb.tolist() for emb in embeddings]
