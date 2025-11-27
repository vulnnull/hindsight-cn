"""
Link creation utilities for temporal, semantic, and entity links.
"""

import time
import logging
from typing import List
from datetime import timedelta

logger = logging.getLogger(__name__)


def _log(log_buffer, message, level='info'):
    """Helper to log to buffer if available, otherwise use logger."""
    if log_buffer is not None:
        log_buffer.append(message)
    else:
        if level == 'info':
            logger.info(message)
        else:
            logger.debug(message)


async def extract_entities_batch_optimized(
    entity_resolver,
    conn,
    bank_id: str,
    unit_ids: List[str],
    sentences: List[str],
    context: str,
    fact_dates: List,
    llm_entities: List[List[dict]],
    log_buffer: List[str] = None,
) -> List[tuple]:
    """
    Process LLM-extracted entities for ALL facts in batch.

    Uses entities provided by the LLM (no spaCy needed), then resolves
    and links them in bulk.

    Args:
        entity_resolver: EntityResolver instance for entity resolution
        conn: Database connection
        agent_id: bank IDentifier
        unit_ids: List of unit IDs
        sentences: List of fact sentences
        context: Context string
        fact_dates: List of fact dates
        llm_entities: List of entity lists from LLM extraction
        log_buffer: Optional buffer for logging

    Returns:
        List of tuples for batch insertion: (from_unit_id, to_unit_id, link_type, weight, entity_id)
    """
    try:
        # Step 1: Convert LLM entities to the format expected by entity resolver
        substep_start = time.time()
        all_entities = []
        for entity_list in llm_entities:
            # Convert List[Entity] or List[dict] to List[Dict] format
            formatted_entities = []
            for ent in entity_list:
                # Handle both Entity objects and dicts
                if hasattr(ent, 'text'):
                    formatted_entities.append({'text': ent.text, 'type': ent.type})
                elif isinstance(ent, dict):
                    formatted_entities.append({'text': ent.get('text', ''), 'type': ent.get('type', 'CONCEPT')})
            all_entities.append(formatted_entities)

        total_entities = sum(len(ents) for ents in all_entities)
        _log(log_buffer, f"  [6.1] Process LLM entities: {total_entities} entities from {len(sentences)} facts in {time.time() - substep_start:.3f}s")

        # Step 2: Resolve entities in BATCH (much faster!)
        substep_start = time.time()
        step_6_2_start = time.time()

        # [6.2.1] Prepare all entities for batch resolution
        substep_6_2_1_start = time.time()
        all_entities_flat = []
        entity_to_unit = []  # Maps flat index to (unit_id, local_index)

        for unit_id, entities, fact_date in zip(unit_ids, all_entities, fact_dates):
            if not entities:
                continue

            for local_idx, entity in enumerate(entities):
                all_entities_flat.append({
                    'text': entity['text'],
                    'type': entity['type'],
                    'nearby_entities': entities,
                })
                entity_to_unit.append((unit_id, local_idx, fact_date))
        _log(log_buffer, f"    [6.2.1] Prepare entities: {len(all_entities_flat)} entities in {time.time() - substep_6_2_1_start:.3f}s")

        # Resolve ALL entities in one batch call
        if all_entities_flat:
            # [6.2.2] Batch resolve entities
            substep_6_2_2_start = time.time()
            # Group by date for batch resolution (most will have same date)
            entities_by_date = {}
            for idx, (unit_id, local_idx, fact_date) in enumerate(entity_to_unit):
                date_key = fact_date
                if date_key not in entities_by_date:
                    entities_by_date[date_key] = []
                entities_by_date[date_key].append((idx, all_entities_flat[idx]))

            _log(log_buffer, f"    [6.2.2] Grouped into {len(entities_by_date)} date buckets, resolving...")

            # Resolve each date group in batch
            resolved_entity_ids = [None] * len(all_entities_flat)
            for date_idx, (fact_date, entities_group) in enumerate(entities_by_date.items(), 1):
                date_bucket_start = time.time()
                indices = [idx for idx, _ in entities_group]
                entities_data = [entity_data for _, entity_data in entities_group]

                batch_resolved = await entity_resolver.resolve_entities_batch(
                    bank_id=bank_id,
                    entities_data=entities_data,
                    context=context,
                    unit_event_date=fact_date,
                    conn=conn
                )

                for idx, entity_id in zip(indices, batch_resolved):
                    resolved_entity_ids[idx] = entity_id

                _log(log_buffer, f"      [6.2.2.{date_idx}] Resolved {len(entities_data)} entities in {time.time() - date_bucket_start:.3f}s")

            _log(log_buffer, f"    [6.2.2] Resolve entities: {len(all_entities_flat)} entities in {time.time() - substep_6_2_2_start:.3f}s")

            # [6.2.3] Create unit-entity links in BATCH
            substep_6_2_3_start = time.time()
            # Map resolved entities back to units and collect all (unit, entity) pairs
            unit_to_entity_ids = {}
            unit_entity_pairs = []
            for idx, (unit_id, local_idx, fact_date) in enumerate(entity_to_unit):
                if unit_id not in unit_to_entity_ids:
                    unit_to_entity_ids[unit_id] = []

                entity_id = resolved_entity_ids[idx]
                unit_to_entity_ids[unit_id].append(entity_id)
                unit_entity_pairs.append((unit_id, entity_id))

            # Batch insert all unit-entity links (MUCH faster!)
            await entity_resolver.link_units_to_entities_batch(unit_entity_pairs, conn=conn)
            _log(log_buffer, f"    [6.2.3] Create unit-entity links (batched): {len(unit_entity_pairs)} links in {time.time() - substep_6_2_3_start:.3f}s")

            _log(log_buffer, f"  [6.2] Entity resolution (batched): {len(all_entities_flat)} entities resolved in {time.time() - step_6_2_start:.3f}s")
        else:
            unit_to_entity_ids = {}
            _log(log_buffer, f"  [6.2] Entity resolution (batched): 0 entities in {time.time() - step_6_2_start:.3f}s")

        # Step 3: Create entity links between units that share entities
        substep_start = time.time()
        # Collect all unique entity IDs
        all_entity_ids = set()
        for entity_ids in unit_to_entity_ids.values():
            all_entity_ids.update(entity_ids)

        _log(log_buffer, f"  [6.3] Creating entity links for {len(all_entity_ids)} unique entities...")

        # Find all units that reference these entities (ONE batched query)
        entity_to_units = {}
        if all_entity_ids:
            query_start = time.time()
            import uuid
            entity_id_list = [uuid.UUID(eid) if isinstance(eid, str) else eid for eid in all_entity_ids]
            rows = await conn.fetch(
                """
                SELECT entity_id, unit_id
                FROM unit_entities
                WHERE entity_id = ANY($1::uuid[])
                """,
                entity_id_list
            )
            _log(log_buffer, f"      [6.3.1] Query unit_entities: {len(rows)} rows in {time.time() - query_start:.3f}s")

            # Group by entity_id
            group_start = time.time()
            for row in rows:
                entity_id = row['entity_id']
                if entity_id not in entity_to_units:
                    entity_to_units[entity_id] = []
                entity_to_units[entity_id].append(row['unit_id'])
            _log(log_buffer, f"      [6.3.2] Group by entity_id: {time.time() - group_start:.3f}s")

        # Create bidirectional links between units that share entities
        link_gen_start = time.time()
        links = []
        for entity_id, units_with_entity in entity_to_units.items():
            # For each pair of units with this entity, create bidirectional links
            for i, unit_id_1 in enumerate(units_with_entity):
                for unit_id_2 in units_with_entity[i+1:]:
                    # Bidirectional links
                    links.append((unit_id_1, unit_id_2, 'entity', 1.0, entity_id))
                    links.append((unit_id_2, unit_id_1, 'entity', 1.0, entity_id))

        _log(log_buffer, f"      [6.3.3] Generate {len(links)} links: {time.time() - link_gen_start:.3f}s")
        _log(log_buffer, f"  [6.3] Entity link creation: {len(links)} links for {len(all_entity_ids)} unique entities in {time.time() - substep_start:.3f}s")

        return links

    except Exception as e:
        logger.error(f"Failed to extract entities in batch: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


async def create_temporal_links_batch_per_fact(
    conn,
    bank_id: str,
    unit_ids: List[str],
    time_window_hours: int = 24,
    log_buffer: List[str] = None,
):
    """
    Create temporal links for multiple units, each with their own event_date.

    Queries the event_date for each unit from the database and creates temporal
    links based on individual dates (supports per-fact dating).

    Args:
        conn: Database connection
        agent_id: bank IDentifier
        unit_ids: List of unit IDs
        time_window_hours: Time window in hours for temporal links
        log_buffer: Optional buffer for logging
    """
    if not unit_ids:
        return

    try:
        import time as time_mod

        # Get the event_date for each new unit
        fetch_dates_start = time_mod.time()
        rows = await conn.fetch(
            """
            SELECT id, event_date
            FROM memory_units
            WHERE id::text = ANY($1)
            """,
            unit_ids
        )
        new_units = {str(row['id']): row['event_date'] for row in rows}
        _log(log_buffer, f"      [7.1] Fetch event_dates for {len(unit_ids)} units: {time_mod.time() - fetch_dates_start:.3f}s")

        # Fetch ALL potential temporal neighbors in ONE query (much faster!)
        # Get time range across all units
        all_dates = list(new_units.values())
        min_date = min(all_dates) - timedelta(hours=time_window_hours)
        max_date = max(all_dates) + timedelta(hours=time_window_hours)

        fetch_neighbors_start = time_mod.time()
        all_candidates = await conn.fetch(
            """
            SELECT id, event_date
            FROM memory_units
            WHERE bank_id = $1
              AND event_date BETWEEN $2 AND $3
              AND id::text != ALL($4)
            ORDER BY event_date DESC
            """,
            bank_id,
            min_date,
            max_date,
            unit_ids
        )
        _log(log_buffer, f"      [7.2] Fetch {len(all_candidates)} candidate neighbors (1 query): {time_mod.time() - fetch_neighbors_start:.3f}s")

        # Filter and create links in memory (much faster than N queries)
        link_gen_start = time_mod.time()
        links = []
        for unit_id, unit_event_date in new_units.items():
            # Filter candidates within this unit's time window
            time_lower = unit_event_date - timedelta(hours=time_window_hours)
            time_upper = unit_event_date + timedelta(hours=time_window_hours)

            matching_neighbors = [
                (row['id'], row['event_date'])
                for row in all_candidates
                if time_lower <= row['event_date'] <= time_upper
            ][:10]  # Limit to top 10

            for recent_id, recent_event_date in matching_neighbors:
                # Calculate temporal proximity weight
                time_diff_hours = abs((unit_event_date - recent_event_date).total_seconds() / 3600)
                weight = max(0.3, 1.0 - (time_diff_hours / time_window_hours))
                links.append((unit_id, str(recent_id), 'temporal', weight, None))

        _log(log_buffer, f"      [7.3] Generate {len(links)} temporal links: {time_mod.time() - link_gen_start:.3f}s")

        if links:
            insert_start = time_mod.time()
            await conn.executemany(
                """
                INSERT INTO memory_links (from_unit_id, to_unit_id, link_type, weight, entity_id)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (from_unit_id, to_unit_id, link_type, COALESCE(entity_id, '00000000-0000-0000-0000-000000000000'::uuid)) DO NOTHING
                """,
                links
            )
            _log(log_buffer, f"      [7.4] Insert {len(links)} temporal links: {time_mod.time() - insert_start:.3f}s")

    except Exception as e:
        logger.error(f"Failed to create temporal links: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


async def create_semantic_links_batch(
    conn,
    bank_id: str,
    unit_ids: List[str],
    embeddings: List[List[float]],
    top_k: int = 5,
    threshold: float = 0.7,
    log_buffer: List[str] = None,
):
    """
    Create semantic links for multiple units efficiently.

    For each unit, finds similar units and creates links.

    Args:
        conn: Database connection
        agent_id: bank IDentifier
        unit_ids: List of unit IDs
        embeddings: List of embedding vectors
        top_k: Number of top similar units to link
        threshold: Minimum similarity threshold
        log_buffer: Optional buffer for logging
    """
    if not unit_ids or not embeddings:
        return

    try:
        import time as time_mod
        import numpy as np

        # Fetch ALL existing units with embeddings in ONE query
        fetch_start = time_mod.time()
        all_existing = await conn.fetch(
            """
            SELECT id, embedding
            FROM memory_units
            WHERE bank_id = $1
              AND embedding IS NOT NULL
              AND id::text != ALL($2)
            """,
            bank_id,
            unit_ids
        )
        _log(log_buffer, f"      [8.1] Fetch {len(all_existing)} existing embeddings (1 query): {time_mod.time() - fetch_start:.3f}s")

        # Convert to numpy for vectorized similarity computation
        compute_start = time_mod.time()
        all_links = []

        if all_existing:
            # Convert existing embeddings to numpy array
            existing_ids = [str(row['id']) for row in all_existing]
            # Stack embeddings as 2D array: (num_embeddings, embedding_dim)
            embedding_arrays = []
            for row in all_existing:
                raw_emb = row['embedding']
                # Handle different pgvector formats
                if isinstance(raw_emb, str):
                    # Parse string format: "[1.0, 2.0, ...]"
                    import json
                    emb = np.array(json.loads(raw_emb), dtype=np.float32)
                elif isinstance(raw_emb, (list, tuple)):
                    emb = np.array(raw_emb, dtype=np.float32)
                else:
                    # Try direct conversion (works for numpy arrays, pgvector objects, etc.)
                    emb = np.array(raw_emb, dtype=np.float32)

                # Ensure it's 1D
                if emb.ndim != 1:
                    raise ValueError(f"Expected 1D embedding, got shape {emb.shape}")
                embedding_arrays.append(emb)

            if not embedding_arrays:
                existing_embeddings = np.array([])
            elif len(embedding_arrays) == 1:
                # Single embedding: reshape to (1, dim)
                existing_embeddings = embedding_arrays[0].reshape(1, -1)
            else:
                # Multiple embeddings: vstack
                existing_embeddings = np.vstack(embedding_arrays)

            # For each new unit, compute similarities with ALL existing units
            for unit_id, new_embedding in zip(unit_ids, embeddings):
                new_emb_array = np.array(new_embedding)

                # Compute cosine similarities (dot product for normalized vectors)
                similarities = np.dot(existing_embeddings, new_emb_array)

                # Find top-k above threshold
                # Get indices of similarities above threshold
                above_threshold = np.where(similarities >= threshold)[0]

                if len(above_threshold) > 0:
                    # Sort by similarity (descending) and take top-k
                    sorted_indices = above_threshold[np.argsort(-similarities[above_threshold])][:top_k]

                    for idx in sorted_indices:
                        similar_id = existing_ids[idx]
                        similarity = float(similarities[idx])
                        all_links.append((unit_id, similar_id, 'semantic', similarity, None))

        _log(log_buffer, f"      [8.2] Compute similarities & generate {len(all_links)} semantic links: {time_mod.time() - compute_start:.3f}s")

        if all_links:
            insert_start = time_mod.time()
            await conn.executemany(
                """
                INSERT INTO memory_links (from_unit_id, to_unit_id, link_type, weight, entity_id)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (from_unit_id, to_unit_id, link_type, COALESCE(entity_id, '00000000-0000-0000-0000-000000000000'::uuid)) DO NOTHING
                """,
                all_links
            )
            _log(log_buffer, f"      [8.3] Insert {len(all_links)} semantic links: {time_mod.time() - insert_start:.3f}s")

    except Exception as e:
        logger.error(f"Failed to create semantic links: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


async def insert_entity_links_batch(conn, links: List[tuple]):
    """
    Insert all entity links in a single batch.

    Args:
        conn: Database connection
        links: List of tuples (from_unit_id, to_unit_id, link_type, weight, entity_id)
    """
    if not links:
        return

    try:
        await conn.executemany(
            """
            INSERT INTO memory_links (from_unit_id, to_unit_id, link_type, weight, entity_id)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (from_unit_id, to_unit_id, link_type, COALESCE(entity_id, '00000000-0000-0000-0000-000000000000'::uuid)) DO NOTHING
            """,
            links
        )
    except Exception as e:
        logger.warning(f"Failed to insert entity links: {str(e)}")


async def create_causal_links_batch(
    conn,
    unit_ids: List[str],
    causal_relations_per_fact: List[List[dict]],
) -> int:
    """
    Create causal links between facts based on LLM-extracted causal relationships.

    Args:
        conn: Database connection
        unit_ids: List of unit IDs (in same order as causal_relations_per_fact)
        causal_relations_per_fact: List of causal relations for each fact.
            Each element is a list of dicts with:
            - target_fact_index: Index into unit_ids for the target fact
            - relation_type: "causes", "caused_by", "enables", or "prevents"
            - strength: Float in [0.0, 1.0] representing relationship strength

    Returns:
        Number of causal links created

    Causal link types:
    - "causes": This fact directly causes the target fact (forward causation)
    - "caused_by": This fact was caused by the target fact (backward causation)
    - "enables": This fact enables/allows the target fact (enablement)
    - "prevents": This fact prevents/blocks the target fact (prevention)
    """
    if not unit_ids or not causal_relations_per_fact:
        return 0

    try:
        import time as time_mod
        create_start = time_mod.time()

        # Build links list
        links = []
        for fact_idx, causal_relations in enumerate(causal_relations_per_fact):
            if not causal_relations:
                continue

            from_unit_id = unit_ids[fact_idx]

            for relation in causal_relations:
                target_idx = relation['target_fact_index']
                relation_type = relation['relation_type']
                strength = relation.get('strength', 1.0)

                # Validate target index
                if target_idx < 0 or target_idx >= len(unit_ids):
                    logger.warning(f"Invalid target_fact_index {target_idx} in causal relation from fact {fact_idx}")
                    continue

                to_unit_id = unit_ids[target_idx]

                # Don't create self-links
                if from_unit_id == to_unit_id:
                    continue

                # Add the causal link
                # link_type is the relation_type (e.g., "causes", "caused_by")
                # weight is the strength of the relationship
                links.append((from_unit_id, to_unit_id, relation_type, strength, None))

        logger.debug(f"Generated {len(links)} causal links in {time_mod.time() - create_start:.3f}s")

        if links:
            insert_start = time_mod.time()
            await conn.executemany(
                """
                INSERT INTO memory_links (from_unit_id, to_unit_id, link_type, weight, entity_id)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (from_unit_id, to_unit_id, link_type, COALESCE(entity_id, '00000000-0000-0000-0000-000000000000'::uuid)) DO NOTHING
                """,
                links
            )
            logger.debug(f"Inserted {len(links)} causal links in {time_mod.time() - insert_start:.3f}s")

        return len(links)

    except Exception as e:
        logger.error(f"Failed to create causal links: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
