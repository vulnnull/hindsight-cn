"""
Core response models for Hindsight memory system.

These models define the structure of data returned by the core MemoryEngine class.
API response models should be kept separate and convert from these core models to maintain
API stability even if internal models change.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class MemoryFact(BaseModel):
    """
    A single memory fact returned by search or think operations.

    This represents a unit of information stored in the memory system,
    including both the content and metadata.
    """
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "text": "Alice works at Google on the AI team",
            "fact_type": "world",
            "context": "work info",
            "event_date": "2024-01-15T10:30:00Z",
            "document_id": "session_abc123",
            "metadata": {"source": "slack"},
            "activation": 0.95
        }
    })

    id: str = Field(description="Unique identifier for the memory fact")
    text: str = Field(description="The actual text content of the memory")
    fact_type: str = Field(description="Type of fact: 'world', 'agent', or 'opinion'")
    context: Optional[str] = Field(None, description="Additional context for the memory")
    event_date: Optional[str] = Field(None, description="ISO format date when the event occurred")
    occurred_start: Optional[str] = Field(None, description="ISO format date when the event started occurring")
    occurred_end: Optional[str] = Field(None, description="ISO format date when the event ended occurring")
    mentioned_at: Optional[str] = Field(None, description="ISO format date when the fact was mentioned/learned")
    document_id: Optional[str] = Field(None, description="ID of the document this memory belongs to")
    metadata: Optional[Dict[str, str]] = Field(None, description="User-defined metadata")

    # Internal metrics (used by system but may not be exposed in API)
    activation: Optional[float] = Field(None, description="Internal activation score")


class SearchResult(BaseModel):
    """
    Result from a search operation.

    Contains a list of matching memory facts and optional trace information
    for debugging and transparency.
    """
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "results": [
                {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "text": "Alice works at Google on the AI team",
                    "fact_type": "world",
                    "context": "work info",
                    "event_date": "2024-01-15T10:30:00Z",
                    "activation": 0.95
                }
            ],
            "trace": {
                "query": "What did Alice say about machine learning?",
                "num_results": 1
            }
        }
    })

    results: List[MemoryFact] = Field(description="List of memory facts matching the query")
    trace: Optional[Dict[str, Any]] = Field(None, description="Trace information for debugging")


class ThinkResult(BaseModel):
    """
    Result from a think operation.

    Contains the formulated answer, the facts it was based on (organized by type),
    and any new opinions that were formed during the thinking process.
    """
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "text": "Based on my knowledge, machine learning is being actively used in healthcare...",
            "based_on": {
                "world": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "text": "Machine learning is used in medical diagnosis",
                        "fact_type": "world",
                        "context": "healthcare",
                        "event_date": "2024-01-15T10:30:00Z"
                    }
                ],
                "agent": [],
                "opinion": []
            },
            "new_opinions": [
                "Machine learning has great potential in healthcare"
            ]
        }
    })

    text: str = Field(description="The formulated answer text")
    based_on: Dict[str, List[MemoryFact]] = Field(
        description="Facts used to formulate the answer, organized by type (world, agent, opinion)"
    )
    new_opinions: List[str] = Field(
        default_factory=list,
        description="List of newly formed opinions during thinking"
    )


class Opinion(BaseModel):
    """
    An opinion with confidence score.

    Opinions represent the agent's formed perspectives on topics,
    with a confidence level indicating strength of belief.
    """
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "text": "Machine learning has great potential in healthcare",
            "confidence": 0.85
        }
    })

    text: str = Field(description="The opinion text")
    confidence: float = Field(description="Confidence score between 0.0 and 1.0")
