"""
Entity processing for retain pipeline.

Handles entity extraction, resolution, and link creation for stored facts.
"""
import logging
from typing import List, Tuple, Dict, Any
from uuid import UUID

from .types import ProcessedFact, EntityRef
from . import link_utils

logger = logging.getLogger(__name__)


async def process_entities_batch(
    entity_resolver,
    conn,
    bank_id: str,
    unit_ids: List[str],
    facts: List[ProcessedFact]
) -> List[Tuple[str, str, float]]:
    """
    Process entities for all facts and create entity links.

    This function:
    1. Extracts entity mentions from fact texts
    2. Resolves entity names to canonical entities
    3. Creates entity records in the database
    4. Returns entity links ready for insertion

    Args:
        entity_resolver: EntityResolver instance for entity resolution
        conn: Database connection
        bank_id: Bank identifier
        unit_ids: List of unit IDs (same length as facts)
        facts: List of ProcessedFact objects

    Returns:
        List of entity link tuples: (unit_id, entity_id, confidence)
    """
    if not unit_ids or not facts:
        return []

    if len(unit_ids) != len(facts):
        raise ValueError(f"Mismatch between unit_ids ({len(unit_ids)}) and facts ({len(facts)})")

    # Extract data for link_utils function
    fact_texts = [fact.fact_text for fact in facts]
    fact_dates = [fact.occurred_start for fact in facts]
    entities_per_fact = [[entity.name for entity in (fact.entities or [])] for fact in facts]

    # Use existing link_utils function for entity processing
    entity_links = await link_utils.extract_entities_batch_optimized(
        entity_resolver,
        conn,
        bank_id,
        unit_ids,
        fact_texts,
        "",  # context (not used in current implementation)
        fact_dates,
        entities_per_fact,
        []  # log_buffer (optional)
    )

    return entity_links


async def insert_entity_links_batch(
    conn,
    entity_links: List[Tuple[str, str, float]]
) -> None:
    """
    Insert entity links in batch.

    Args:
        conn: Database connection
        entity_links: List of (unit_id, entity_id, confidence) tuples
    """
    if not entity_links:
        return

    await link_utils.insert_entity_links_batch(conn, entity_links)
