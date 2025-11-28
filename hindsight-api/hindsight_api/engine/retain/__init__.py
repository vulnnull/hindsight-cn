"""
Retain pipeline modules for storing memories.

This package contains modular components for the retain operation:
- types: Type definitions for retain pipeline
- fact_extraction: Extract facts from content
- embedding_processing: Augment texts and generate embeddings
- deduplication: Check for duplicate facts
- entity_processing: Process and resolve entities
- link_creation: Create temporal, semantic, entity, and causal links
- chunk_storage: Handle chunk storage
- fact_storage: Handle fact insertion into database
"""

from .types import (
    RetainContent,
    ExtractedFact,
    ProcessedFact,
    ChunkMetadata,
    EntityRef,
    CausalRelation,
    RetainBatch
)

from . import fact_extraction
from . import embedding_processing
from . import deduplication
from . import entity_processing
from . import link_creation
from . import chunk_storage
from . import fact_storage

__all__ = [
    # Types
    "RetainContent",
    "ExtractedFact",
    "ProcessedFact",
    "ChunkMetadata",
    "EntityRef",
    "CausalRelation",
    "RetainBatch",
    # Modules
    "fact_extraction",
    "embedding_processing",
    "deduplication",
    "entity_processing",
    "link_creation",
    "chunk_storage",
    "fact_storage",
]
