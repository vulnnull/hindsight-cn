"""
Deduplication logic for retain pipeline.

Checks for duplicate facts using semantic similarity and temporal proximity.
"""

import logging
from collections import defaultdict
from datetime import UTC

from .types import ProcessedFact

logger = logging.getLogger(__name__)


async def check_duplicates_batch(conn, bank_id: str, facts: list[ProcessedFact], duplicate_checker_fn) -> list[bool]:
    """
    Check which facts are duplicates using batched time-window queries.

    Groups facts by 12-hour time buckets to efficiently check for duplicates
    within a 24-hour window.

    Args:
        conn: Database connection
        bank_id: Bank identifier
        facts: List of ProcessedFact objects to check
        duplicate_checker_fn: Async function(conn, bank_id, texts, embeddings, date, time_window_hours)
                              that returns List[bool] indicating duplicates

    Returns:
        List of boolean flags (same length as facts) indicating if each fact is a duplicate
    """
    if not facts:
        return []

    # Group facts by event_date (rounded to 12-hour buckets) for efficient batching
    time_buckets = defaultdict(list)
    for idx, fact in enumerate(facts):
        # Use occurred_start if available, otherwise use mentioned_at
        # For deduplication purposes, we need a time reference
        fact_date = fact.occurred_start if fact.occurred_start is not None else fact.mentioned_at

        # Defensive: if both are None (shouldn't happen), use now()
        if fact_date is None:
            from datetime import datetime

            fact_date = datetime.now(UTC)

        # Round to 12-hour bucket to group similar times
        bucket_key = fact_date.replace(hour=(fact_date.hour // 12) * 12, minute=0, second=0, microsecond=0)
        time_buckets[bucket_key].append((idx, fact))

    # Process each bucket in batch
    all_is_duplicate = [False] * len(facts)

    for bucket_date, bucket_items in time_buckets.items():
        indices = [item[0] for item in bucket_items]
        texts = [item[1].fact_text for item in bucket_items]
        embeddings = [item[1].embedding for item in bucket_items]

        # Check duplicates for this time bucket
        dup_flags = await duplicate_checker_fn(conn, bank_id, texts, embeddings, bucket_date, time_window_hours=24)

        # Map results back to original indices
        for idx, is_dup in zip(indices, dup_flags):
            all_is_duplicate[idx] = is_dup

    return all_is_duplicate


def filter_duplicates(facts: list[ProcessedFact], is_duplicate_flags: list[bool]) -> list[ProcessedFact]:
    """
    Filter out duplicate facts based on duplicate flags.

    Args:
        facts: List of ProcessedFact objects
        is_duplicate_flags: Boolean flags indicating which facts are duplicates

    Returns:
        List of non-duplicate facts
    """
    if len(facts) != len(is_duplicate_flags):
        raise ValueError(f"Mismatch between facts ({len(facts)}) and flags ({len(is_duplicate_flags)})")

    return [fact for fact, is_dup in zip(facts, is_duplicate_flags) if not is_dup]
