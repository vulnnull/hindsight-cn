"""
Pydantic models for mental models.
"""

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class MentalModelSubtype(str, Enum):
    """Subtype of mental model.

    Currently only DIRECTIVE is supported. Other types of consolidated knowledge
    are handled by:
    - Learnings: Automatic bottom-up consolidation from facts
    - Pinned Reflections: User-curated living documents
    """

    DIRECTIVE = "directive"  # User-defined hard rules, observations user-provided


class MentalModel(BaseModel):
    """
    A mental model representing synthesized understanding.

    Mental models are the agent's consolidated knowledge. Unlike raw facts,
    mental models provide:
    - A one-liner description for quick scanning/retrieval
    - A full summary for deep understanding
    - Links to related mental models
    """

    id: str = Field(description="Unique identifier within the bank")
    bank_id: str = Field(description="Bank this mental model belongs to")
    subtype: MentalModelSubtype = Field(description="How this model was created")
    name: str = Field(description="Human-readable name")
    description: str = Field(description="One-liner for quick scanning and retrieval matching")
    summary: str | None = Field(default=None, description="Full synthesized understanding")

    # References
    entity_id: str | None = Field(default=None, description="Reference to entities table when type=entity")
    source_facts: list[str] = Field(default_factory=list, description="Fact IDs used to generate summary")
    links: list[str] = Field(default_factory=list, description="Related mental model IDs")

    # Tags for scoped visibility (similar to document tags)
    tags: list[str] = Field(default_factory=list, description="Tags for scoped visibility filtering")

    # Timestamps
    last_updated: datetime | None = Field(default=None, description="When summary was last regenerated")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="When this model was created"
    )
