"""
Main orchestrator for the retain pipeline.

Coordinates all retain pipeline modules to store memories efficiently.
"""
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from . import bank_utils
from ..db_utils import acquire_with_retry


def utcnow():
    """Get current UTC time."""
    return datetime.now(timezone.utc)

from .types import RetainContent, ExtractedFact, ProcessedFact
from . import (
    fact_extraction,
    embedding_processing,
    deduplication,
    chunk_storage,
    fact_storage,
    entity_processing,
    link_creation
)

logger = logging.getLogger(__name__)


async def retain_batch(
    pool,
    embeddings_model,
    llm_config,
    entity_resolver,
    task_backend,
    format_date_fn,
    duplicate_checker_fn,
    bank_id: str,
    contents_dicts: List[Dict[str, Any]],
    document_id: Optional[str] = None,
    is_first_batch: bool = True,
    fact_type_override: Optional[str] = None,
    confidence_score: Optional[float] = None,
) -> List[List[str]]:
    """
    Process a batch of content through the retain pipeline.

    Args:
        pool: Database connection pool
        embeddings_model: Embeddings model for generating embeddings
        llm_config: LLM configuration for fact extraction
        entity_resolver: Entity resolver for entity processing
        task_backend: Task backend for background jobs
        format_date_fn: Function to format datetime to readable string
        duplicate_checker_fn: Function to check for duplicate facts
        bank_id: Bank identifier
        contents_dicts: List of content dictionaries
        document_id: Optional document ID
        is_first_batch: Whether this is the first batch
        fact_type_override: Override fact type for all facts
        confidence_score: Confidence score for opinions

    Returns:
        List of unit ID lists (one list per content item)
    """
    start_time = time.time()
    total_chars = sum(len(item.get("content", "")) for item in contents_dicts)

    # Buffer all logs
    log_buffer = []
    log_buffer.append(f"{'='*60}")
    log_buffer.append(f"RETAIN_BATCH START: {bank_id}")
    log_buffer.append(f"Batch size: {len(contents_dicts)} content items, {total_chars:,} chars")
    log_buffer.append(f"{'='*60}")

    # Get bank profile
    profile = await bank_utils.get_bank_profile(pool, bank_id)
    agent_name = profile["name"]

    # Convert dicts to RetainContent objects
    contents = []
    for item in contents_dicts:
        content = RetainContent(
            content=item["content"],
            context=item.get("context", ""),
            event_date=item.get("event_date") or utcnow(),
            metadata=item.get("metadata", {})
        )
        contents.append(content)

    # Step 1: Extract facts from all contents
    step_start = time.time()
    extract_opinions = (fact_type_override == 'opinion')

    extracted_facts, chunks = await fact_extraction.extract_facts_from_contents(
        contents,
        llm_config,
        agent_name,
        extract_opinions
    )
    log_buffer.append(f"[1] Extract facts: {len(extracted_facts)} facts from {len(contents)} contents in {time.time() - step_start:.3f}s")

    if not extracted_facts:
        return [[] for _ in contents]

    # Apply fact_type_override if provided
    if fact_type_override:
        for fact in extracted_facts:
            fact.fact_type = fact_type_override

    # Step 2: Augment texts and generate embeddings
    step_start = time.time()
    augmented_texts = embedding_processing.augment_texts_with_dates(extracted_facts, format_date_fn)
    embeddings = await embedding_processing.generate_embeddings_batch(embeddings_model, augmented_texts)
    log_buffer.append(f"[2] Generate embeddings: {len(embeddings)} embeddings in {time.time() - step_start:.3f}s")

    # Step 3: Convert to ProcessedFact objects (without chunk_ids yet)
    processed_facts = [
        ProcessedFact.from_extracted_fact(extracted_fact, embedding)
        for extracted_fact, embedding in zip(extracted_facts, embeddings)
    ]

    # Step 4: Database transaction
    async with acquire_with_retry(pool) as conn:
        async with conn.transaction():
            # Ensure bank exists
            await fact_storage.ensure_bank_exists(conn, bank_id)

            # Handle document tracking
            if document_id:
                combined_content = "\n".join([c.get("content", "") for c in contents_dicts])
                await fact_storage.handle_document_tracking(
                    conn, bank_id, document_id, combined_content, is_first_batch
                )
            elif chunks:
                # Generate document_id for chunk storage
                document_id = str(uuid.uuid4())
                combined_content = "\n".join([c.get("content", "") for c in contents_dicts])
                await fact_storage.handle_document_tracking(
                    conn, bank_id, document_id, combined_content, is_first_batch
                )
                log_buffer.append(f"[2.5] Generated document_id: {document_id}")

            # Store chunks and map to facts
            step_start = time.time()
            chunk_id_map = {}
            if document_id and chunks:
                chunk_id_map = await chunk_storage.store_chunks_batch(conn, bank_id, document_id, chunks)
                log_buffer.append(f"[3] Store chunks: {len(chunks)} chunks in {time.time() - step_start:.3f}s")

                # Map chunk_ids to facts
                facts_chunk_indices = [fact.chunk_index for fact in extracted_facts]
                chunk_ids = chunk_storage.map_facts_to_chunks(facts_chunk_indices, chunk_id_map)
                for processed_fact, chunk_id in zip(processed_facts, chunk_ids):
                    processed_fact.chunk_id = chunk_id

            # Deduplication
            step_start = time.time()
            is_duplicate_flags = await deduplication.check_duplicates_batch(
                conn, bank_id, processed_facts, duplicate_checker_fn
            )
            log_buffer.append(f"[4] Deduplication: {sum(is_duplicate_flags)} duplicates in {time.time() - step_start:.3f}s")

            # Filter out duplicates
            non_duplicate_facts = deduplication.filter_duplicates(processed_facts, is_duplicate_flags)

            if not non_duplicate_facts:
                return [[] for _ in contents]

            # Insert facts
            step_start = time.time()
            unit_ids = await fact_storage.insert_facts_batch(conn, bank_id, non_duplicate_facts, document_id)
            log_buffer.append(f"[5] Insert facts: {len(unit_ids)} units in {time.time() - step_start:.3f}s")

            # Process entities
            step_start = time.time()
            entity_links = await entity_processing.process_entities_batch(
                entity_resolver, conn, bank_id, unit_ids, non_duplicate_facts
            )
            log_buffer.append(f"[6] Process entities: {len(entity_links)} links in {time.time() - step_start:.3f}s")

            # Create temporal links
            step_start = time.time()
            await link_creation.create_temporal_links_batch(conn, bank_id, unit_ids)
            log_buffer.append(f"[7] Temporal links: {time.time() - step_start:.3f}s")

            # Create semantic links
            step_start = time.time()
            embeddings_for_links = [fact.embedding for fact in non_duplicate_facts]
            await link_creation.create_semantic_links_batch(conn, bank_id, unit_ids, embeddings_for_links)
            log_buffer.append(f"[8] Semantic links: {time.time() - step_start:.3f}s")

            # Insert entity links
            step_start = time.time()
            if entity_links:
                await entity_processing.insert_entity_links_batch(conn, entity_links)
            log_buffer.append(f"[9] Entity links: {time.time() - step_start:.3f}s")

            # Create causal links
            step_start = time.time()
            causal_link_count = await link_creation.create_causal_links_batch(conn, unit_ids, non_duplicate_facts)
            log_buffer.append(f"[10] Causal links: {causal_link_count} links in {time.time() - step_start:.3f}s")

            # Map results back to original content items
            result_unit_ids = _map_results_to_contents(
                contents, extracted_facts, is_duplicate_flags, unit_ids
            )

            total_time = time.time() - start_time
            log_buffer.append(f"{'='*60}")
            log_buffer.append(f"RETAIN_BATCH COMPLETE: {len(unit_ids)} units in {total_time:.3f}s")
            log_buffer.append(f"{'='*60}")

            logger.info("\n" + "\n".join(log_buffer) + "\n")

            # Trigger background tasks
            await _trigger_background_tasks(
                task_backend,
                bank_id,
                unit_ids,
                non_duplicate_facts,
                entity_links
            )

            return result_unit_ids


def _map_results_to_contents(
    contents: List[RetainContent],
    extracted_facts: List[ExtractedFact],
    is_duplicate_flags: List[bool],
    unit_ids: List[str]
) -> List[List[str]]:
    """
    Map created unit IDs back to original content items.

    Accounts for duplicates when mapping back.
    """
    result_unit_ids = []
    filtered_idx = 0

    # Group facts by content_index
    facts_by_content = {i: [] for i in range(len(contents))}
    for i, fact in enumerate(extracted_facts):
        facts_by_content[fact.content_index].append(i)

    for content_index in range(len(contents)):
        content_unit_ids = []
        for fact_idx in facts_by_content[content_index]:
            if not is_duplicate_flags[fact_idx]:
                content_unit_ids.append(unit_ids[filtered_idx])
                filtered_idx += 1
        result_unit_ids.append(content_unit_ids)

    return result_unit_ids


async def _trigger_background_tasks(
    task_backend,
    bank_id: str,
    unit_ids: List[str],
    facts: List[ProcessedFact],
    entity_links: List
) -> None:
    """Trigger opinion reinforcement and observation regeneration tasks."""
    # Trigger opinion reinforcement if there are entities
    fact_entities = [[e.name for e in fact.entities] for fact in facts]
    if any(fact_entities):
        await task_backend.submit_task({
            'type': 'reinforce_opinion',
            'bank_id': bank_id,
            'created_unit_ids': unit_ids,
            'unit_texts': [fact.fact_text for fact in facts],
            'unit_entities': fact_entities
        })

    # Trigger observation regeneration for top entities
    TOP_N_ENTITIES = 5
    MIN_FACTS_THRESHOLD = 5

    if entity_links:
        unique_entity_ids = set()
        for link in entity_links:
            # links are tuples: (unit_id, entity_id, confidence)
            if len(link) >= 2 and link[1]:
                unique_entity_ids.add(str(link[1]))

        if unique_entity_ids:
            await task_backend.submit_task({
                'type': 'regenerate_observations',
                'bank_id': bank_id,
                'entity_ids': list(unique_entity_ids)[:TOP_N_ENTITIES],
                'min_facts': MIN_FACTS_THRESHOLD
            })
