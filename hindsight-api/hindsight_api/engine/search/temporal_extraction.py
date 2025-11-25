"""
Temporal extraction for time-aware search queries.

Handles natural language temporal expressions using transformer-based query analysis.
"""

from typing import Optional, Tuple
from datetime import datetime
import logging
from hindsight_api.engine.query_analyzer import QueryAnalyzer, TransformerQueryAnalyzer

logger = logging.getLogger(__name__)

# Global default analyzer instance
# Can be overridden by passing a custom analyzer to extract_temporal_constraint
_default_analyzer: Optional[QueryAnalyzer] = None


def get_default_analyzer() -> QueryAnalyzer:
    """
    Get or create the default query analyzer.

    Uses lazy initialization to avoid loading model at import time.

    Returns:
        Default TransformerQueryAnalyzer instance
    """
    global _default_analyzer
    if _default_analyzer is None:
        _default_analyzer = TransformerQueryAnalyzer()
    return _default_analyzer


def extract_temporal_constraint(
    query: str,
    reference_date: Optional[datetime] = None,
    analyzer: Optional[QueryAnalyzer] = None,
) -> Optional[Tuple[datetime, datetime]]:
    """
    Extract temporal constraint from query using transformer-based analysis.

    Returns (start_date, end_date) tuple if temporal constraint found, else None.

    Args:
        query: Search query
        reference_date: Reference date for relative terms (defaults to now)
        analyzer: Custom query analyzer (defaults to TransformerQueryAnalyzer)

    Returns:
        (start_date, end_date) tuple or None
    """
    if analyzer is None:
        analyzer = get_default_analyzer()

    analysis = analyzer.analyze(query, reference_date)

    if analysis.temporal_constraint:
        result = (
            analysis.temporal_constraint.start_date,
            analysis.temporal_constraint.end_date
        )
        return result

    return None
