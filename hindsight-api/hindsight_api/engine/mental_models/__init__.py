"""
Mental models module for Hindsight.

Mental models contain directives - hard rules that are injected into reflect prompts.
Directives are user-defined and their observations are user-provided (not LLM-generated).

Other types of consolidated knowledge are handled by:
- Learnings: Automatic bottom-up consolidation from facts
- Pinned Reflections: User-curated living documents
"""

from .models import MentalModel, MentalModelSubtype

__all__ = ["MentalModel", "MentalModelSubtype"]
