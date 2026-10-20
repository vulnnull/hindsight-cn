"""Seed facts straight into a store-owned bank, for fixtures that would otherwise INSERT into SQL.

A fixture that needs exact facts (a known count, a chosen vector) cannot get them from a retain,
whose extraction is the LLM's business. For a Postgres bank it writes ``memory_units`` directly;
a store-owned bank keeps nothing there, so the same fixture writes through the store instead.
"""

from hindsight_api.engine.memories import get_memories
from hindsight_api.engine.retain import embedding_utils
from hindsight_api.engine.retain.types import ProcessedFact, pack_embedding


async def store_write_facts(
    memory,
    bank_id: str,
    unit_ids: list[str],
    texts: list[str],
    *,
    fact_type: str = "world",
    embeddings: list[list[float]] | None = None,
    text_search: bool = True,
) -> None:
    """Write one fact per text under the given ids. Embeds the texts when no vectors are given.

    ``text_search=False`` leaves the facts out of the keyword index, matching a SQL seed that
    writes no ``search_vector``.
    """
    if embeddings is None:
        embeddings = await embedding_utils.generate_embeddings_batch(memory.embeddings, texts)
    facts = [
        ProcessedFact(
            fact_text=text,
            fact_type=fact_type,
            embedding=pack_embedding(emb),
            occurred_start=None,
            occurred_end=None,
            mentioned_at=None,
            context="",
            metadata={},
        )
        for text, emb in zip(texts, embeddings)
    ]
    await get_memories().retain(bank_id, unit_ids, facts, enable_text_search=text_search)
