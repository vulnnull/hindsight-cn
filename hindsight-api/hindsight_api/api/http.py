"""
FastAPI application factory and API routes for memory system.

This module provides the create_app function to create and configure
the FastAPI application with all API endpoints.
"""
import json
import logging
import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query


def _parse_metadata(metadata: Any) -> Dict[str, Any]:
    """Parse metadata that may be a dict, JSON string, or None."""
    if metadata is None:
        return {}
    if isinstance(metadata, dict):
        return metadata
    if isinstance(metadata, str):
        try:
            return json.loads(metadata)
        except json.JSONDecodeError:
            return {}
    return {}


from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, ConfigDict

from hindsight_api import MemoryEngine
from hindsight_api.engine.memory_engine import Budget
from hindsight_api.engine.db_utils import acquire_with_retry


logger = logging.getLogger(__name__)


class MetadataFilter(BaseModel):
    """Filter for metadata fields. Matches records where (key=value) OR (key not set) when match_unset=True."""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "key": "source",
            "value": "slack",
            "match_unset": True
        }
    })

    key: str = Field(description="Metadata key to filter on")
    value: Optional[str] = Field(default=None, description="Value to match. If None with match_unset=True, matches any record where key is not set.")
    match_unset: bool = Field(default=True, description="If True, also match records where this metadata key is not set")


class EntityIncludeOptions(BaseModel):
    """Options for including entity observations in recall results."""
    max_tokens: int = Field(default=500, description="Maximum tokens for entity observations")


class IncludeOptions(BaseModel):
    """Options for including additional data in recall results."""
    entities: Optional[EntityIncludeOptions] = Field(
        default=EntityIncludeOptions(),
        description="Include entity observations. Set to null to disable entity inclusion."
    )


class RecallRequest(BaseModel):
    """Request model for recall endpoint."""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "query": "What did Alice say about machine learning?",
            "types": ["world", "agent"],
            "budget": "mid",
            "max_tokens": 4096,
            "trace": True,
            "query_timestamp": "2023-05-30T23:40:00",
            "filters": [{"key": "source", "value": "slack", "match_unset": True}],
            "include": {
                "entities": {
                    "max_tokens": 500
                }
            }
        }
    })

    query: str
    types: Optional[List[str]] = Field(default=None, description="List of fact types to recall (defaults to all if not specified)")
    budget: Budget = Budget.MID
    max_tokens: int = 4096
    trace: bool = False
    query_timestamp: Optional[str] = Field(default=None, description="ISO format date string (e.g., '2023-05-30T23:40:00')")
    filters: Optional[List[MetadataFilter]] = Field(default=None, description="Filter by metadata. Multiple filters are ANDed together.")
    include: IncludeOptions = Field(default_factory=IncludeOptions, description="Options for including additional data (entities are included by default)")


class RecallResult(BaseModel):
    """Single recall result item."""
    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "text": "Alice works at Google on the AI team",
                "type": "world",
                "entities": ["Alice", "Google"],
                "context": "work info",
                "occurred_start": "2024-01-15T10:30:00Z",
                "occurred_end": "2024-01-15T10:30:00Z",
                "mentioned_at": "2024-01-15T10:30:00Z",
                "document_id": "session_abc123",
                "metadata": {"source": "slack"}
            }
        }
    }

    id: str
    text: str
    type: Optional[str] = None  # fact type: world, agent, opinion, observation
    entities: Optional[List[str]] = None  # Entity names mentioned in this fact
    context: Optional[str] = None
    occurred_start: Optional[str] = None  # ISO format date when the event started
    occurred_end: Optional[str] = None  # ISO format date when the event ended
    mentioned_at: Optional[str] = None  # ISO format date when the fact was mentioned
    document_id: Optional[str] = None  # Document this memory belongs to
    metadata: Optional[Dict[str, str]] = None  # User-defined metadata


class EntityObservationResponse(BaseModel):
    """An observation about an entity."""
    text: str
    mentioned_at: Optional[str] = None


class EntityStateResponse(BaseModel):
    """Current mental model of an entity."""
    entity_id: str
    canonical_name: str
    observations: List[EntityObservationResponse]


class EntityListItem(BaseModel):
    """Entity list item with summary."""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "canonical_name": "John",
            "mention_count": 15,
            "first_seen": "2024-01-15T10:30:00Z",
            "last_seen": "2024-02-01T14:00:00Z"
        }
    })

    id: str
    canonical_name: str
    mention_count: int
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class EntityListResponse(BaseModel):
    """Response model for entity list endpoint."""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "items": [
                {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "canonical_name": "John",
                    "mention_count": 15,
                    "first_seen": "2024-01-15T10:30:00Z",
                    "last_seen": "2024-02-01T14:00:00Z"
                }
            ]
        }
    })

    items: List[EntityListItem]


class EntityDetailResponse(BaseModel):
    """Response model for entity detail endpoint."""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "canonical_name": "John",
            "mention_count": 15,
            "first_seen": "2024-01-15T10:30:00Z",
            "last_seen": "2024-02-01T14:00:00Z",
            "observations": [
                {"text": "John works at Google", "mentioned_at": "2024-01-15T10:30:00Z"}
            ]
        }
    })

    id: str
    canonical_name: str
    mention_count: int
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    observations: List[EntityObservationResponse]


class RecallResponse(BaseModel):
    """Response model for recall endpoints."""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "results": [
                {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "text": "Alice works at Google on the AI team",
                    "type": "world",
                    "entities": ["Alice", "Google"],
                    "context": "work info",
                    "occurred_start": "2024-01-15T10:30:00Z",
                    "occurred_end": "2024-01-15T10:30:00Z"
                }
            ],
            "trace": {
                "query": "What did Alice say about machine learning?",
                "num_results": 1,
                "time_seconds": 0.123
            },
            "entities": {
                "Alice": {
                    "entity_id": "123e4567-e89b-12d3-a456-426614174001",
                    "canonical_name": "Alice",
                    "observations": [
                        {"text": "Alice works at Google on the AI team", "mentioned_at": "2024-01-15T10:30:00Z"}
                    ]
                }
            }
        }
    })

    results: List[RecallResult]
    trace: Optional[Dict[str, Any]] = None
    entities: Optional[Dict[str, EntityStateResponse]] = Field(default=None, description="Entity states for entities mentioned in results")


class MemoryItem(BaseModel):
    """Single memory item for retain."""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "content": "Alice mentioned she's working on a new ML model",
            "timestamp": "2024-01-15T10:30:00Z",
            "context": "team meeting",
            "metadata": {"source": "slack", "channel": "engineering"}
        }
    })

    content: str
    timestamp: Optional[datetime] = None
    context: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None


class RetainRequest(BaseModel):
    """Request model for retain endpoint."""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "items": [
                {
                    "content": "Alice works at Google",
                    "context": "work"
                },
                {
                    "content": "Bob went hiking yesterday",
                    "timestamp": "2024-01-15T10:00:00Z"
                }
            ],
            "document_id": "conversation_123",
            "async": False
        }
    })

    items: List[MemoryItem]
    document_id: Optional[str] = None
    async_: bool = Field(
        default=False,
        alias="async",
        description="If true, process asynchronously in background. If false, wait for completion (default: false)"
    )


class RetainResponse(BaseModel):
    """Response model for retain endpoint."""
    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "success": True,
                "bank_id": "user123",
                "document_id": "conversation_123",
                "items_count": 2,
                "async": False
            }
        }
    )

    success: bool
    bank_id: str
    document_id: Optional[str] = None
    items_count: int
    async_: bool = Field(alias="async", serialization_alias="async", description="Whether the operation was processed asynchronously")


class FactsIncludeOptions(BaseModel):
    """Options for including facts (based_on) in reflect results."""
    pass  # No additional options needed, just enable/disable


class ReflectIncludeOptions(BaseModel):
    """Options for including additional data in reflect results."""
    facts: Optional[FactsIncludeOptions] = Field(
        default=None,
        description="Include facts that the answer is based on. Set to {} to enable, null to disable (default: disabled)."
    )
    entities: Optional[EntityIncludeOptions] = Field(
        default=None,
        description="Include entity observations. Set to {max_tokens: N} to enable, null to disable (default: disabled)."
    )


class ReflectRequest(BaseModel):
    """Request model for reflect endpoint."""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "query": "What do you think about artificial intelligence?",
            "budget": "low",
            "context": "This is for a research paper on AI ethics",
            "filters": [{"key": "source", "value": "slack", "match_unset": True}],
            "include": {
                "facts": {},
                "entities": {"max_tokens": 500}
            }
        }
    })

    query: str
    budget: Budget = Budget.LOW
    context: Optional[str] = None
    filters: Optional[List[MetadataFilter]] = Field(default=None, description="Filter by metadata. Multiple filters are ANDed together.")
    include: ReflectIncludeOptions = Field(default_factory=ReflectIncludeOptions, description="Options for including additional data (both disabled by default)")


class OpinionItem(BaseModel):
    """Model for an opinion with confidence score."""
    text: str
    confidence: float


class ReflectFact(BaseModel):
    """A fact used in think response."""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "text": "AI is used in healthcare",
            "type": "world",
            "context": "healthcare discussion",
            "occurred_start": "2024-01-15T10:30:00Z",
            "occurred_end": "2024-01-15T10:30:00Z"
        }
    })

    id: Optional[str] = None
    text: str
    type: Optional[str] = None  # fact type: world, agent, opinion
    context: Optional[str] = None
    occurred_start: Optional[str] = None
    occurred_end: Optional[str] = None


class ReflectResponse(BaseModel):
    """Response model for think endpoint."""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "text": "Based on my understanding, AI is a transformative technology...",
            "based_on": [
                {
                    "id": "123",
                    "text": "AI is used in healthcare",
                    "type": "world"
                },
                {
                    "id": "456",
                    "text": "I discussed AI applications last week",
                    "type": "agent"
                }
            ]
        }
    })

    text: str
    based_on: List[ReflectFact] = []  # Facts used to generate the response


class BanksResponse(BaseModel):
    """Response model for banks list endpoint."""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "banks": ["user123", "bank_alice", "bank_bob"]
        }
    })

    banks: List[str]


class PersonalityTraits(BaseModel):
    """Personality traits based on Big Five model."""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "openness": 0.8,
            "conscientiousness": 0.6,
            "extraversion": 0.5,
            "agreeableness": 0.7,
            "neuroticism": 0.3,
            "bias_strength": 0.7
        }
    })

    openness: float = Field(ge=0.0, le=1.0, description="Openness to experience (0-1)")
    conscientiousness: float = Field(ge=0.0, le=1.0, description="Conscientiousness (0-1)")
    extraversion: float = Field(ge=0.0, le=1.0, description="Extraversion (0-1)")
    agreeableness: float = Field(ge=0.0, le=1.0, description="Agreeableness (0-1)")
    neuroticism: float = Field(ge=0.0, le=1.0, description="Neuroticism (0-1)")
    bias_strength: float = Field(ge=0.0, le=1.0, description="How strongly personality influences opinions (0-1)")


class BankProfileResponse(BaseModel):
    """Response model for bank profile."""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "bank_id": "user123",
            "name": "Alice",
            "personality": {
                "openness": 0.8,
                "conscientiousness": 0.6,
                "extraversion": 0.5,
                "agreeableness": 0.7,
                "neuroticism": 0.3,
                "bias_strength": 0.7
            },
            "background": "I am a software engineer with 10 years of experience in startups"
        }
    })

    bank_id: str
    name: str
    personality: PersonalityTraits
    background: str


class UpdatePersonalityRequest(BaseModel):
    """Request model for updating personality traits."""
    personality: PersonalityTraits


class AddBackgroundRequest(BaseModel):
    """Request model for adding/merging background information."""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "content": "I was born in Texas",
            "update_personality": True
        }
    })

    content: str = Field(description="New background information to add or merge")
    update_personality: bool = Field(
        default=True,
        description="If true, infer Big Five personality traits from the merged background (default: true)"
    )


class BackgroundResponse(BaseModel):
    """Response model for background update."""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "background": "I was born in Texas. I am a software engineer with 10 years of experience.",
            "personality": {
                "openness": 0.7,
                "conscientiousness": 0.6,
                "extraversion": 0.5,
                "agreeableness": 0.8,
                "neuroticism": 0.4,
                "bias_strength": 0.6
            }
        }
    })

    background: str
    personality: Optional[PersonalityTraits] = None


class BankListItem(BaseModel):
    """Bank list item with profile summary."""
    bank_id: str
    name: str
    personality: PersonalityTraits
    background: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class BankListResponse(BaseModel):
    """Response model for listing all banks."""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "banks": [
                {
                    "bank_id": "user123",
                    "name": "Alice",
                    "personality": {
                        "openness": 0.5,
                        "conscientiousness": 0.5,
                        "extraversion": 0.5,
                        "agreeableness": 0.5,
                        "neuroticism": 0.5,
                        "bias_strength": 0.5
                    },
                    "background": "I am a software engineer",
                    "created_at": "2024-01-15T10:30:00Z",
                    "updated_at": "2024-01-16T14:20:00Z"
                }
            ]
        }
    })

    banks: List[BankListItem]


class CreateBankRequest(BaseModel):
    """Request model for creating/updating a bank."""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "name": "Alice",
            "personality": {
                "openness": 0.8,
                "conscientiousness": 0.6,
                "extraversion": 0.5,
                "agreeableness": 0.7,
                "neuroticism": 0.3,
                "bias_strength": 0.7
            },
            "background": "I am a creative software engineer with 10 years of experience"
        }
    })

    name: Optional[str] = None
    personality: Optional[PersonalityTraits] = None
    background: Optional[str] = None


class GraphDataResponse(BaseModel):
    """Response model for graph data endpoint."""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "nodes": [
                {"id": "1", "label": "Alice works at Google", "type": "world"},
                {"id": "2", "label": "Bob went hiking", "type": "world"}
            ],
            "edges": [
                {"from": "1", "to": "2", "type": "semantic", "weight": 0.8}
            ],
            "table_rows": [
                {"id": "abc12345...", "text": "Alice works at Google", "context": "Work info", "date": "2024-01-15 10:30", "entities": "Alice (PERSON), Google (ORGANIZATION)"}
            ],
            "total_units": 2
        }
    })

    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    table_rows: List[Dict[str, Any]]
    total_units: int


class ListMemoryUnitsResponse(BaseModel):
    """Response model for list memory units endpoint."""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "items": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "text": "Alice works at Google on the AI team",
                    "context": "Work conversation",
                    "date": "2024-01-15T10:30:00Z",
                    "type": "world",
                    "entities": "Alice (PERSON), Google (ORGANIZATION)"
                }
            ],
            "total": 150,
            "limit": 100,
            "offset": 0
        }
    })

    items: List[Dict[str, Any]]
    total: int
    limit: int
    offset: int


class ListDocumentsResponse(BaseModel):
    """Response model for list documents endpoint."""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "items": [
                {
                    "id": "session_1",
                    "bank_id": "user123",
                    "content_hash": "abc123",
                    "created_at": "2024-01-15T10:30:00Z",
                    "updated_at": "2024-01-15T10:30:00Z",
                    "text_length": 5420,
                    "memory_unit_count": 15
                }
            ],
            "total": 50,
            "limit": 100,
            "offset": 0
        }
    })

    items: List[Dict[str, Any]]
    total: int
    limit: int
    offset: int


class DocumentResponse(BaseModel):
    """Response model for get document endpoint."""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": "session_1",
            "bank_id": "user123",
            "original_text": "Full document text here...",
            "content_hash": "abc123",
            "created_at": "2024-01-15T10:30:00Z",
            "updated_at": "2024-01-15T10:30:00Z",
            "memory_unit_count": 15
        }
    })

    id: str
    bank_id: str
    original_text: str
    content_hash: Optional[str]
    created_at: str
    updated_at: str
    memory_unit_count: int


class DeleteResponse(BaseModel):
    """Response model for delete operations."""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "success": True
        }
    })

    success: bool


def create_app(memory: MemoryEngine, run_migrations: bool = True, initialize_memory: bool = True) -> FastAPI:
    """
    Create and configure the FastAPI application.

    Args:
        memory: MemoryEngine instance (already initialized with required parameters)
        run_migrations: Whether to run database migrations on startup (default: True)
        initialize_memory: Whether to initialize memory system on startup (default: True)

    Returns:
        Configured FastAPI application

    Note:
        When mounting this app as a sub-application, the lifespan events may not fire.
        In that case, you should call memory.initialize() manually before starting the server
        and memory.close() when shutting down.
    """
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """
        Lifespan context manager for startup and shutdown events.
        Note: This only fires when running the app standalone, not when mounted.
        """
        # Startup: Initialize database and memory system
        if initialize_memory:
            await memory.initialize()
            logging.info("Memory system initialized")

        if run_migrations:
            from hindsight_api.migrations import run_migrations as do_migrations
            do_migrations(memory.db_url)
            logging.info("Database migrations applied")



        yield

        # Shutdown: Cleanup memory system
        await memory.close()
        logging.info("Memory system closed")

    app = FastAPI(
        title="Hindsight HTTP API",
        version="1.0.0",
        description="HTTP API for Hindsight",
        contact={
            "name": "Memory System",
        },
        license_info={
            "name": "Apache 2.0",
            "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
        },
        lifespan=lifespan
    )

    # IMPORTANT: Set memory on app.state immediately, don't wait for lifespan
    # This is required for mounted sub-applications where lifespan may not fire
    app.state.memory = memory

    # Register all routes
    _register_routes(app)

    return app


def _register_routes(app: FastAPI):
    """Register all API routes on the given app instance."""


    @app.get(
        "/v1/default/banks/{bank_id}/graph",
        response_model=GraphDataResponse,
        summary="Get memory graph data",
        description="Retrieve graph data for visualization, optionally filtered by type (world/agent/opinion). Limited to 1000 most recent items.",
        operation_id="get_graph"
    )
    async def api_graph(bank_id: str,
        type: Optional[str] = None
    ):
        """Get graph data from database, filtered by bank_id and optionally by type."""
        try:
            data = await app.state.memory.get_graph_data(bank_id, type)
            return data
        except Exception as e:
            import traceback
            error_detail = f"{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
            logger.error(f"Error in /v1/default/banks/{bank_id}/graph: {error_detail}")
            raise HTTPException(status_code=500, detail=str(e))


    @app.get(
        "/v1/default/banks/{bank_id}/memories/list",
        response_model=ListMemoryUnitsResponse,
        summary="List memory units",
        description="List memory units with pagination and optional full-text search. Supports filtering by type. Results are sorted by most recent first (mentioned_at DESC, then created_at DESC).",
        operation_id="list_memories"
    )
    async def api_list(bank_id: str,
        type: Optional[str] = None,
        q: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ):
        """
        List memory units for table view with optional full-text search.

        Results are ordered by most recent first, using mentioned_at timestamp
        (when the memory was mentioned/learned), falling back to created_at.

        Args:
            bank_id: Memory Bank ID (from path)
            type: Filter by fact type (world, agent, opinion)
            q: Search query for full-text search (searches text and context)
            limit: Maximum number of results (default: 100)
            offset: Offset for pagination (default: 0)
        """
        try:
            data = await app.state.memory.list_memory_units(
                bank_id=bank_id,
                fact_type=type,
                search_query=q,
                limit=limit,
                offset=offset
            )
            return data
        except Exception as e:
            import traceback
            error_detail = f"{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
            logger.error(f"Error in /v1/default/banks/{bank_id}/memories/list: {error_detail}")
            raise HTTPException(status_code=500, detail=str(e))


    @app.post(
        "/v1/default/banks/{bank_id}/memories/recall",
        response_model=RecallResponse,
        summary="Recall memory",
        description="""
    Recall memory using semantic similarity and spreading activation.

    The type parameter is optional and must be one of:
    - 'world': General knowledge about people, places, events, and things that happen
    - 'agent': Memories about what the AI agent did, actions taken, and tasks performed
    - 'opinion': The bank's formed beliefs, perspectives, and viewpoints
    - 'observation': Synthesized observations about entities (generated automatically)

    Set include_entities=true to get entity observations alongside recall results.
        """,
        operation_id="recall_memories"
    )
    async def api_recall(bank_id: str, request: RecallRequest):
        """Run a recall and return results with trace."""
        try:
            # Validate types
            valid_fact_types = ["world", "agent", "opinion", "observation"]

            # Default to world, agent, opinion if not specified (exclude observation by default)
            fact_types = request.types if request.types else ["world", "agent", "opinion"]
            for ft in fact_types:
                if ft not in valid_fact_types:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid type '{ft}'. Must be one of: {', '.join(valid_fact_types)}"
                    )

            # Parse query_timestamp if provided
            question_date = None
            if request.query_timestamp:
                try:
                    question_date = datetime.fromisoformat(request.query_timestamp.replace('Z', '+00:00'))
                except ValueError as e:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid query_timestamp format. Expected ISO format (e.g., '2023-05-30T23:40:00'): {str(e)}"
                    )

            # Determine entity inclusion settings
            include_entities = request.include.entities is not None
            max_entity_tokens = request.include.entities.max_tokens if include_entities else 500

            # Run recall with tracing
            core_result = await app.state.memory.recall_async(
                bank_id=bank_id,
                query=request.query,
                budget=request.budget,
                max_tokens=request.max_tokens,
                enable_trace=request.trace,
                fact_type=fact_types,
                question_date=question_date,
                include_entities=include_entities,
                max_entity_tokens=max_entity_tokens
            )

            # Convert core MemoryFact objects to API RecallResult objects (excluding internal metrics)
            recall_results = [
                RecallResult(
                    id=fact.id,
                    text=fact.text,
                    type=fact.fact_type,
                    entities=fact.entities,
                    context=fact.context,
                    occurred_start=fact.occurred_start,
                    occurred_end=fact.occurred_end,
                    mentioned_at=fact.mentioned_at,
                    document_id=fact.document_id
                )
                for fact in core_result.results
            ]

            # Convert core EntityState objects to API EntityStateResponse objects
            entities_response = None
            if core_result.entities:
                entities_response = {}
                for name, state in core_result.entities.items():
                    entities_response[name] = EntityStateResponse(
                        entity_id=state.entity_id,
                        canonical_name=state.canonical_name,
                        observations=[
                            EntityObservationResponse(text=obs.text, mentioned_at=obs.mentioned_at)
                            for obs in state.observations
                        ]
                    )

            return RecallResponse(
                results=recall_results,
                trace=core_result.trace,
                entities=entities_response
            )
        except HTTPException:
            raise
        except Exception as e:
            import traceback
            error_detail = f"{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
            logger.error(f"Error in /v1/default/banks/{bank_id}/memories/recall: {error_detail}")
            raise HTTPException(status_code=500, detail=str(e))


    @app.post(
        "/v1/default/banks/{bank_id}/reflect",
        response_model=ReflectResponse,
        summary="Reflect and generate answer",
        description="""
    Reflect and formulate an answer using bank identity, world facts, and opinions.

    This endpoint:
    1. Retrieves agent facts (bank's identity)
    2. Retrieves world facts relevant to the query
    3. Retrieves existing opinions (bank's perspectives)
    4. Uses LLM to formulate a contextual answer
    5. Extracts and stores any new opinions formed
    6. Returns plain text answer, the facts used, and new opinions
        """,
        operation_id="reflect"
    )
    async def api_reflect(bank_id: str, request: ReflectRequest):
        try:
            # Use the memory system's reflect_async method
            core_result = await app.state.memory.reflect_async(
                bank_id=bank_id,
                query=request.query,
                budget=request.budget,
                context=request.context
            )

            # Convert core MemoryFact objects to API ReflectFact objects if facts are requested
            based_on_facts = []
            if request.include.facts is not None:
                for fact_type, facts in core_result.based_on.items():
                    for fact in facts:
                        based_on_facts.append(ReflectFact(
                            id=fact.id,
                            text=fact.text,
                            type=fact.fact_type,
                            context=fact.context,
                            occurred_start=fact.occurred_start,
                            occurred_end=fact.occurred_end
                        ))

            # TODO: Handle entities inclusion when supported in reflect
            # entities_response = None
            # if request.include.entities is not None:
            #     max_entity_tokens = request.include.entities.max_tokens
            #     # ... fetch and format entities

            return ReflectResponse(
                text=core_result.text,
                based_on=based_on_facts,
            )

        except Exception as e:
            import traceback
            error_detail = f"{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
            logger.error(f"Error in /v1/default/banks/{bank_id}/reflect: {error_detail}")
            raise HTTPException(status_code=500, detail=str(e))


    @app.get(
        "/v1/default/banks",
        response_model=BankListResponse,
        summary="List all memory banks",
        description="Get a list of all agents with their profiles",
        operation_id="list_banks"
    )
    async def api_list_banks():
        """Get list of all banks with their profiles."""
        try:
            banks = await app.state.memory.list_banks()
            return BankListResponse(banks=banks)
        except Exception as e:
            import traceback
            error_detail = f"{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
            logger.error(f"Error in /v1/default/banks: {error_detail}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get(
        "/v1/default/banks/{bank_id}/stats",
        summary="Get statistics for memory bank",
        description="Get statistics about nodes and links for a specific agent",
        operation_id="get_agent_stats"
    )
    async def api_stats(bank_id: str):
        """Get statistics about memory nodes and links for a memory bank."""
        try:
            pool = await app.state.memory._get_pool()
            async with acquire_with_retry(pool) as conn:
                # Get node counts by fact_type
                node_stats = await conn.fetch(
                    """
                    SELECT fact_type, COUNT(*) as count
                    FROM memory_units
                    WHERE bank_id = $1
                    GROUP BY fact_type
                    """,
                    bank_id
                )

                # Get link counts by link_type
                link_stats = await conn.fetch(
                    """
                    SELECT ml.link_type, COUNT(*) as count
                    FROM memory_links ml
                    JOIN memory_units mu ON ml.from_unit_id = mu.id
                    WHERE mu.bank_id = $1
                    GROUP BY ml.link_type
                    """,
                    bank_id
                )

                # Get link counts by fact_type (from nodes)
                link_fact_type_stats = await conn.fetch(
                    """
                    SELECT mu.fact_type, COUNT(*) as count
                    FROM memory_links ml
                    JOIN memory_units mu ON ml.from_unit_id = mu.id
                    WHERE mu.bank_id = $1
                    GROUP BY mu.fact_type
                    """,
                    bank_id
                )

                # Get link counts by fact_type AND link_type
                link_breakdown_stats = await conn.fetch(
                    """
                    SELECT mu.fact_type, ml.link_type, COUNT(*) as count
                    FROM memory_links ml
                    JOIN memory_units mu ON ml.from_unit_id = mu.id
                    WHERE mu.bank_id = $1
                    GROUP BY mu.fact_type, ml.link_type
                    """,
                    bank_id
                )

                # Get pending and failed operations counts
                ops_stats = await conn.fetch(
                    """
                    SELECT status, COUNT(*) as count
                    FROM async_operations
                    WHERE bank_id = $1
                    GROUP BY status
                    """,
                    bank_id
                )
                ops_by_status = {row['status']: row['count'] for row in ops_stats}
                pending_operations = ops_by_status.get('pending', 0)
                failed_operations = ops_by_status.get('failed', 0)

                # Get document count
                doc_count_result = await conn.fetchrow(
                    """
                    SELECT COUNT(*) as count
                    FROM documents
                    WHERE bank_id = $1
                    """,
                    bank_id
                )
                total_documents = doc_count_result['count'] if doc_count_result else 0

                # Format results
                nodes_by_type = {row['fact_type']: row['count'] for row in node_stats}
                links_by_type = {row['link_type']: row['count'] for row in link_stats}
                links_by_fact_type = {row['fact_type']: row['count'] for row in link_fact_type_stats}

                # Build detailed breakdown: {fact_type: {link_type: count}}
                links_breakdown = {}
                for row in link_breakdown_stats:
                    fact_type = row['fact_type']
                    link_type = row['link_type']
                    count = row['count']
                    if fact_type not in links_breakdown:
                        links_breakdown[fact_type] = {}
                    links_breakdown[fact_type][link_type] = count

                total_nodes = sum(nodes_by_type.values())
                total_links = sum(links_by_type.values())

                return {
                    "bank_id": bank_id,
                    "total_nodes": total_nodes,
                    "total_links": total_links,
                    "total_documents": total_documents,
                    "nodes_by_fact_type": nodes_by_type,
                    "links_by_link_type": links_by_type,
                    "links_by_fact_type": links_by_fact_type,
                    "links_breakdown": links_breakdown,
                    "pending_operations": pending_operations,
                    "failed_operations": failed_operations
                }

        except Exception as e:
            import traceback
            error_detail = f"{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
            logger.error(f"Error in /v1/default/banks/{bank_id}/stats: {error_detail}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get(
        "/v1/default/banks/{bank_id}/entities",
        response_model=EntityListResponse,
        summary="List entities",
        description="List all entities (people, organizations, etc.) known by the bank, ordered by mention count.",
        operation_id="list_entities"
    )
    async def api_list_entities(bank_id: str,
        limit: int = Query(default=100, description="Maximum number of entities to return")
    ):
        """List entities for a memory bank."""
        try:
            entities = await app.state.memory.list_entities(bank_id, limit=limit)
            return EntityListResponse(
                items=[EntityListItem(**e) for e in entities]
            )
        except Exception as e:
            import traceback
            error_detail = f"{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
            logger.error(f"Error in /v1/default/banks/{bank_id}/entities: {error_detail}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get(
        "/v1/default/banks/{bank_id}/entities/{entity_id}",
        response_model=EntityDetailResponse,
        summary="Get entity details",
        description="Get detailed information about an entity including observations (mental model).",
        operation_id="get_entity"
    )
    async def api_get_entity(bank_id: str, entity_id: str):
        """Get entity details with observations."""
        try:
            # First get the entity metadata
            pool = await app.state.memory._get_pool()
            async with acquire_with_retry(pool) as conn:
                entity_row = await conn.fetchrow(
                    """
                    SELECT id, canonical_name, mention_count, first_seen, last_seen, metadata
                    FROM entities
                    WHERE bank_id = $1 AND id = $2
                    """,
                    bank_id, uuid.UUID(entity_id)
                )

            if not entity_row:
                raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found")

            # Get observations for the entity
            observations = await app.state.memory.get_entity_observations(
                bank_id, entity_id, limit=20
            )

            return EntityDetailResponse(
                id=str(entity_row['id']),
                canonical_name=entity_row['canonical_name'],
                mention_count=entity_row['mention_count'],
                first_seen=entity_row['first_seen'].isoformat() if entity_row['first_seen'] else None,
                last_seen=entity_row['last_seen'].isoformat() if entity_row['last_seen'] else None,
                metadata=_parse_metadata(entity_row['metadata']),
                observations=[
                    EntityObservationResponse(text=obs.text, mentioned_at=obs.mentioned_at)
                    for obs in observations
                ]
            )
        except HTTPException:
            raise
        except Exception as e:
            import traceback
            error_detail = f"{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
            logger.error(f"Error in /v1/default/banks/{bank_id}/entities/{entity_id}: {error_detail}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post(
        "/v1/default/banks/{bank_id}/entities/{entity_id}/regenerate",
        response_model=EntityDetailResponse,
        summary="Regenerate entity observations",
        description="Regenerate observations for an entity based on all facts mentioning it.",
        operation_id="regenerate_entity_observations"
    )
    async def api_regenerate_entity_observations(bank_id: str, entity_id: str):
        """Regenerate observations for an entity."""
        try:
            # First get the entity metadata
            pool = await app.state.memory._get_pool()
            async with acquire_with_retry(pool) as conn:
                entity_row = await conn.fetchrow(
                    """
                    SELECT id, canonical_name, mention_count, first_seen, last_seen, metadata
                    FROM entities
                    WHERE bank_id = $1 AND id = $2
                    """,
                    bank_id, uuid.UUID(entity_id)
                )

            if not entity_row:
                raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found")

            # Regenerate observations
            await app.state.memory.regenerate_entity_observations(
                bank_id=bank_id,
                entity_id=entity_id,
                entity_name=entity_row['canonical_name']
            )

            # Get updated observations
            observations = await app.state.memory.get_entity_observations(
                bank_id, entity_id, limit=20
            )

            return EntityDetailResponse(
                id=str(entity_row['id']),
                canonical_name=entity_row['canonical_name'],
                mention_count=entity_row['mention_count'],
                first_seen=entity_row['first_seen'].isoformat() if entity_row['first_seen'] else None,
                last_seen=entity_row['last_seen'].isoformat() if entity_row['last_seen'] else None,
                metadata=_parse_metadata(entity_row['metadata']),
                observations=[
                    EntityObservationResponse(text=obs.text, mentioned_at=obs.mentioned_at)
                    for obs in observations
                ]
            )
        except HTTPException:
            raise
        except Exception as e:
            import traceback
            error_detail = f"{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
            logger.error(f"Error in /v1/default/banks/{bank_id}/entities/{entity_id}/regenerate: {error_detail}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get(
        "/v1/default/banks/{bank_id}/documents",
        response_model=ListDocumentsResponse,
        summary="List documents",
        description="List documents with pagination and optional search. Documents are the source content from which memory units are extracted.",
        operation_id="list_documents"
    )
    async def api_list_documents(bank_id: str,
        q: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ):
        """
        List documents for a memory bank with optional search.

        Args:
            bank_id: Memory Bank ID (from path)
            q: Search query (searches document ID and metadata)
            limit: Maximum number of results (default: 100)
            offset: Offset for pagination (default: 0)
        """
        try:
            data = await app.state.memory.list_documents(
                bank_id=bank_id,
                search_query=q,
                limit=limit,
                offset=offset
            )
            return data
        except Exception as e:
            import traceback
            error_detail = f"{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
            logger.error(f"Error in /v1/default/banks/{bank_id}/documents: {error_detail}")
            raise HTTPException(status_code=500, detail=str(e))


    @app.get(
        "/v1/default/banks/{bank_id}/documents/{document_id}",
        response_model=DocumentResponse,
        summary="Get document details",
        description="Get a specific document including its original text",
        operation_id="get_document"
    )
    async def api_get_document(bank_id: str,
        document_id: str
    ):
        """
        Get a specific document with its original text.

        Args:
            bank_id: Memory Bank ID (from path)
            document_id: Document ID (from path)
        """
        try:
            document = await app.state.memory.get_document(document_id, bank_id)
            if not document:
                raise HTTPException(status_code=404, detail="Document not found")
            return document
        except HTTPException:
            raise
        except Exception as e:
            import traceback
            error_detail = f"{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
            logger.error(f"Error in /v1/default/banks/{bank_id}/documents/{document_id}: {error_detail}")
            raise HTTPException(status_code=500, detail=str(e))


    @app.delete(
        "/v1/default/banks/{bank_id}/documents/{document_id}",
        summary="Delete a document",
        description="""
Delete a document and all its associated memory units and links.

This will cascade delete:
- The document itself
- All memory units extracted from this document
- All links (temporal, semantic, entity) associated with those memory units

This operation cannot be undone.
        """,
        operation_id="delete_document"
    )
    async def api_delete_document(bank_id: str,
        document_id: str
    ):
        """
        Delete a document and all its associated memory units and links.

        Args:
            bank_id: Memory Bank ID (from path)
            document_id: Document ID to delete (from path)
        """
        try:
            result = await app.state.memory.delete_document(document_id, bank_id)

            if result["document_deleted"] == 0:
                raise HTTPException(status_code=404, detail="Document not found")

            return {
                "success": True,
                "message": f"Document '{document_id}' and {result['memory_units_deleted']} associated memory units deleted successfully",
                "document_id": document_id,
                "memory_units_deleted": result["memory_units_deleted"]
            }
        except HTTPException:
            raise
        except Exception as e:
            import traceback
            error_detail = f"{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
            logger.error(f"Error in /v1/default/banks/{bank_id}/documents/{document_id}: {error_detail}")
            raise HTTPException(status_code=500, detail=str(e))


    @app.get(
        "/v1/default/banks/{bank_id}/operations",
        summary="List async operations",
        description="Get a list of all async operations (pending and failed) for a specific agent, including error messages for failed operations",
        operation_id="list_operations"
    )
    async def api_list_operations(bank_id: str):
        """List all async operations (pending and failed) for a memory bank."""
        try:
            pool = await app.state.memory._get_pool()
            async with acquire_with_retry(pool) as conn:
                operations = await conn.fetch(
                    """
                    SELECT id, bank_id, task_type, items_count, document_id, created_at, status, error_message
                    FROM async_operations
                    WHERE bank_id = $1
                    ORDER BY created_at ASC
                    """,
                    bank_id
                )

                return {
                    "bank_id": bank_id,
                    "operations": [
                        {
                            "id": str(row['id']),
                            "task_type": row['task_type'],
                            "items_count": row['items_count'],
                            "document_id": row['document_id'],
                            "created_at": row['created_at'].isoformat(),
                            "status": row['status'],
                            "error_message": row['error_message']
                        }
                        for row in operations
                    ]
                }

        except Exception as e:
            import traceback
            error_detail = f"{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
            logger.error(f"Error in /v1/default/banks/{bank_id}/operations: {error_detail}")
            raise HTTPException(status_code=500, detail=str(e))


    @app.delete(
        "/v1/default/banks/{bank_id}/operations/{operation_id}",
        summary="Cancel a pending async operation",
        description="Cancel a pending async operation by removing it from the queue",
        operation_id="cancel_operation"
    )
    async def api_cancel_operation(bank_id: str, operation_id: str):
        """Cancel a pending async operation."""
        try:
            # Validate UUID format
            try:
                op_uuid = uuid.UUID(operation_id)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid operation_id format: {operation_id}")

            pool = await app.state.memory._get_pool()
            async with acquire_with_retry(pool) as conn:
                # Check if operation exists and belongs to this memory bank
                result = await conn.fetchrow(
                    "SELECT bank_id FROM async_operations WHERE id = $1 AND bank_id = $2",
                    op_uuid,
                    bank_id
                )

                if not result:
                    raise HTTPException(status_code=404, detail=f"Operation {operation_id} not found for memory bank {bank_id}")

                # Delete the operation
                await conn.execute(
                    "DELETE FROM async_operations WHERE id = $1",
                    op_uuid
                )

                return {
                    "success": True,
                    "message": f"Operation {operation_id} cancelled",
                    "operation_id": operation_id,
                    "bank_id": bank_id
                }

        except HTTPException:
            raise
        except Exception as e:
            import traceback
            error_detail = f"{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
            logger.error(f"Error in /v1/default/banks/{bank_id}/operations/{operation_id}: {error_detail}")
            raise HTTPException(status_code=500, detail=str(e))


    @app.get(
        "/v1/default/banks/{bank_id}/profile",
        response_model=BankProfileResponse,
        summary="Get memory bank profile",
        description="Get personality traits and background for a memory bank. Auto-creates agent with defaults if not exists.",
        operation_id="get_bank_profile"
    )
    async def api_get_bank_profile(bank_id: str):
        """Get memory bank profile (personality + background)."""
        try:
            profile = await app.state.memory.get_bank_profile(bank_id)
            return BankProfileResponse(
                bank_id=bank_id,
                name=profile["name"],
                personality=PersonalityTraits(**profile["personality"]),
                background=profile["background"]
            )
        except Exception as e:
            import traceback
            error_detail = f"{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
            logger.error(f"Error in /v1/default/banks/{bank_id}/profile: {error_detail}")
            raise HTTPException(status_code=500, detail=str(e))


    @app.put(
        "/v1/default/banks/{bank_id}/profile",
        response_model=BankProfileResponse,
        summary="Update memory bank personality",
        description="Update bank's Big Five personality traits and bias strength",
        operation_id="update_bank_personality"
    )
    async def api_update_bank_personality(bank_id: str,
        request: UpdatePersonalityRequest
    ):
        """Update bank personality traits."""
        try:
            # Update personality
            await app.state.memory.update_bank_personality(
                bank_id,
                request.personality.model_dump()
            )

            # Get updated profile
            profile = await app.state.memory.get_bank_profile(bank_id)
            return BankProfileResponse(
                bank_id=bank_id,
                name=profile["name"],
                personality=PersonalityTraits(**profile["personality"]),
                background=profile["background"]
            )
        except Exception as e:
            import traceback
            error_detail = f"{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
            logger.error(f"Error in /v1/default/banks/{bank_id}/profile: {error_detail}")
            raise HTTPException(status_code=500, detail=str(e))


    @app.post(
        "/v1/default/banks/{bank_id}/background",
        response_model=BackgroundResponse,
        summary="Add/merge memory bank background",
        description="Add new background information or merge with existing. LLM intelligently resolves conflicts, normalizes to first person, and optionally infers personality traits.",
        operation_id="add_bank_background"
    )
    async def api_add_bank_background(bank_id: str,
        request: AddBackgroundRequest
    ):
        """Add or merge bank background information. Optionally infer personality traits."""
        try:
            result = await app.state.memory.merge_bank_background(
                bank_id,
                request.content,
                update_personality=request.update_personality
            )

            response = BackgroundResponse(background=result["background"])
            if "personality" in result:
                response.personality = PersonalityTraits(**result["personality"])

            return response
        except Exception as e:
            import traceback
            error_detail = f"{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
            logger.error(f"Error in /v1/default/banks/{bank_id}/background: {error_detail}")
            raise HTTPException(status_code=500, detail=str(e))


    @app.put(
        "/v1/default/banks/{bank_id}",
        response_model=BankProfileResponse,
        summary="Create or update memory bank",
        description="Create a new agent or update existing agent with personality and background. Auto-fills missing fields with defaults.",
        operation_id="create_or_update_bank"
    )
    async def api_create_or_update_bank(bank_id: str,
        request: CreateBankRequest
    ):
        """Create or update an agent with personality and background."""
        try:
            # Get existing profile or create with defaults
            profile = await app.state.memory.get_bank_profile(bank_id)

            # Update name if provided
            if request.name is not None:
                pool = await app.state.memory._get_pool()
                async with acquire_with_retry(pool) as conn:
                    await conn.execute(
                        """
                        UPDATE banks
                        SET name = $2,
                            updated_at = NOW()
                        WHERE bank_id = $1
                        """,
                        bank_id,
                        request.name
                    )
                profile["name"] = request.name

            # Update personality if provided
            if request.personality is not None:
                await app.state.memory.update_bank_personality(
                    bank_id,
                    request.personality.model_dump()
                )
                profile["personality"] = request.personality.model_dump()

            # Update background if provided (replace, not merge)
            if request.background is not None:
                pool = await app.state.memory._get_pool()
                async with acquire_with_retry(pool) as conn:
                    await conn.execute(
                        """
                        UPDATE agents
                        SET background = $2,
                            updated_at = NOW()
                        WHERE bank_id = $1
                        """,
                        bank_id,
                        request.background
                    )
                profile["background"] = request.background

            # Get final profile
            final_profile = await app.state.memory.get_bank_profile(bank_id)
            return BankProfileResponse(
                bank_id=bank_id,
                name=final_profile["name"],
                personality=PersonalityTraits(**final_profile["personality"]),
                background=final_profile["background"]
            )
        except Exception as e:
            import traceback
            error_detail = f"{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
            logger.error(f"Error in /v1/default/banks/{bank_id}: {error_detail}")
            raise HTTPException(status_code=500, detail=str(e))


    @app.post(
        "/v1/default/banks/{bank_id}/memories",
        response_model=RetainResponse,
        summary="Retain memories",
        description="""
    Retain memory items with automatic fact extraction.

    This is the main endpoint for storing memories. It supports both synchronous and asynchronous processing
    via the async parameter.

    Features:
    - Efficient batch processing
    - Automatic fact extraction from natural language
    - Entity recognition and linking
    - Document tracking with automatic upsert (when document_id is provided)
    - Temporal and semantic linking
    - Optional asynchronous processing

    The system automatically:
    1. Extracts semantic facts from the content
    2. Generates embeddings
    3. Deduplicates similar facts
    4. Creates temporal, semantic, and entity links
    5. Tracks document metadata

    When async=true:
    - Returns immediately after queuing the task
    - Processing happens in the background
    - Use the operations endpoint to monitor progress

    When async=false (default):
    - Waits for processing to complete
    - Returns after all memories are stored

    Note: If document_id is provided and already exists, the old document and its memory units will be deleted before creating new ones (upsert behavior).
        """,
        operation_id="retain_memories"
    )
    async def api_retain(bank_id: str, request: RetainRequest):
        """Retain memories with optional async processing."""
        try:
            # Prepare contents for processing
            contents = []
            for item in request.items:
                content_dict = {"content": item.content}
                if item.timestamp:
                    content_dict["event_date"] = item.timestamp
                if item.context:
                    content_dict["context"] = item.context
                if item.metadata:
                    content_dict["metadata"] = item.metadata
                contents.append(content_dict)

            if request.async_:
                # Async processing: queue task and return immediately
                operation_id = uuid.uuid4()

                # Insert operation record into database
                pool = await app.state.memory._get_pool()
                async with acquire_with_retry(pool) as conn:
                    await conn.execute(
                        """
                        INSERT INTO async_operations (id, bank_id, task_type, items_count, document_id)
                        VALUES ($1, $2, $3, $4, $5)
                        """,
                        operation_id,
                        bank_id,
                        'retain',
                        len(contents),
                        request.document_id
                    )

                # Submit task to background queue
                await app.state.memory._task_backend.submit_task({
                    'type': 'batch_put',
                    'operation_id': str(operation_id),
                    'bank_id': bank_id,
                    'contents': contents,
                    'document_id': request.document_id
                })

                logging.info(f"Retain task queued for bank_id={bank_id}, {len(contents)} items, operation_id={operation_id}")

                return RetainResponse(
                    success=True,
                    bank_id=bank_id,
                    document_id=request.document_id,
                    items_count=len(contents),
                    async_=True
                )
            else:
                # Synchronous processing: wait for completion
                result = await app.state.memory.retain_batch_async(
                    bank_id=bank_id,
                    contents=contents,
                    document_id=request.document_id
                )

                return RetainResponse(
                    success=True,
                    bank_id=bank_id,
                    document_id=request.document_id,
                    items_count=len(contents),
                    async_=False
                )
        except Exception as e:
            import traceback
            error_detail = f"{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
            logger.error(f"Error in /v1/default/banks/{bank_id}/memories (retain): {error_detail}")
            raise HTTPException(status_code=500, detail=str(e))


    @app.delete(
        "/v1/default/banks/{bank_id}/memories",
        response_model=DeleteResponse,
        summary="Clear memory bank memories",
        description="Delete memory units for a memory bank. Optionally filter by type (world, agent, opinion) to delete only specific types. This is a destructive operation that cannot be undone. The bank profile (personality and background) will be preserved.",
        operation_id="clear_bank_memories"
    )
    async def api_clear_bank_memories(bank_id: str,
        type: Optional[str] = Query(None, description="Optional fact type filter (world, agent, opinion)")
    ):
        """Clear memories for a memory bank, optionally filtered by type."""
        try:
            await app.state.memory.delete_bank(bank_id, fact_type=type)

            return DeleteResponse(
                success=True
            )
        except Exception as e:
            import traceback
            error_detail = f"{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
            logger.error(f"Error in /v1/default/banks/{bank_id}/memories: {error_detail}")
            raise HTTPException(status_code=500, detail=str(e))
