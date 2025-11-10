"""
Embedding generation operations for memory units.
"""

import asyncio
import logging
from typing import List

logger = logging.getLogger(__name__)


class EmbeddingOperationsMixin:
    """Mixin class for embedding operations."""

    def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text using the configured embeddings backend.

        Args:
            text: Text to embed

        Returns:
            Embedding vector (dimension depends on embeddings backend)
        """
        try:
            embeddings = self.embeddings.encode([text])
            return embeddings[0]
        except Exception as e:
            raise Exception(f"Failed to generate embedding: {str(e)}")

    async def _generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts using the configured embeddings backend.

        Runs the embedding generation in a thread pool to avoid blocking the event loop
        for CPU-bound operations.

        Args:
            texts: List of texts to embed

        Returns:
            List of embeddings in same order as input texts
        """
        try:
            # Run embeddings in thread pool to avoid blocking event loop
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None,  # Use default thread pool
                self.embeddings.encode,
                texts
            )
            return embeddings
        except Exception as e:
            raise Exception(f"Failed to generate batch embeddings: {str(e)}")
