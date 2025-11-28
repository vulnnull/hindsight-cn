"""
Embedding processing for retain pipeline.

Handles augmenting fact texts with temporal information and generating embeddings.
"""
import logging
from typing import List
from datetime import datetime

from . import embedding_utils
from .types import ExtractedFact

logger = logging.getLogger(__name__)


def augment_texts_with_dates(facts: List[ExtractedFact], format_date_fn) -> List[str]:
    """
    Augment fact texts with readable dates for better temporal matching.

    This allows queries like "camping in June" to match facts that happened in June.

    Args:
        facts: List of ExtractedFact objects
        format_date_fn: Function to format datetime to readable string

    Returns:
        List of augmented text strings (same length as facts)
    """
    augmented_texts = []
    for fact in facts:
        # Use occurred_start as the representative date
        fact_date = fact.occurred_start or fact.mentioned_at
        readable_date = format_date_fn(fact_date)
        # Augment text with date for embedding (but store original text in DB)
        augmented_text = f"{fact.fact_text} (happened in {readable_date})"
        augmented_texts.append(augmented_text)
    return augmented_texts


async def generate_embeddings_batch(
    embeddings_model,
    texts: List[str]
) -> List[List[float]]:
    """
    Generate embeddings for a batch of texts.

    Args:
        embeddings_model: Embeddings model instance
        texts: List of text strings to embed

    Returns:
        List of embedding vectors (same length as texts)
    """
    if not texts:
        return []

    embeddings = await embedding_utils.generate_embeddings_batch(
        embeddings_model,
        texts
    )

    return embeddings
