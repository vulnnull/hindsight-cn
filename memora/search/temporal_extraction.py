"""
Temporal extraction for time-aware search queries.

Handles natural language temporal expressions like:
- "last year", "in June", "last month"
- "last spring", "this summer" (custom season support)
- "between March and May"
"""

from typing import Optional, Tuple
from datetime import datetime, timedelta
import re


def extract_temporal_constraint(
    query: str,
    reference_date: Optional[datetime] = None
) -> Optional[Tuple[datetime, datetime]]:
    """
    Extract temporal constraint from query.

    Returns (start_date, end_date) tuple if temporal constraint found, else None.

    Args:
        query: Search query
        reference_date: Reference date for relative terms (defaults to now)

    Returns:
        (start_date, end_date) tuple or None
    """
    if reference_date is None:
        reference_date = datetime.now()

    query_lower = query.lower()

    # Try dateparser for standard temporal expressions
    import dateparser

    # Parse using dateparser with relative base
    settings = {
        'RELATIVE_BASE': reference_date,
        'PREFER_DATES_FROM': 'past',  # Prefer past dates for "in June"
        'RETURN_AS_TIMEZONE_AWARE': False
    }

    # Try to find temporal expressions
    temporal_keywords = [
        'in', 'during', 'last', 'this', 'next', 'between',
        'january', 'february', 'march', 'april', 'may', 'june',
        'july', 'august', 'september', 'october', 'november', 'december',
        'spring', 'summer', 'fall', 'autumn', 'winter',
        'year', 'month', 'week', 'day'
    ]

    has_temporal = any(keyword in query_lower for keyword in temporal_keywords)
    if not has_temporal:
        return None

    # Try season detection first (custom handling)
    season_match = _extract_season(query_lower, reference_date)
    if season_match:
        return season_match

    # Try specific month patterns
    month_match = _extract_month(query_lower, reference_date)
    if month_match:
        return month_match

    # Try relative periods
    relative_match = _extract_relative_period(query_lower, reference_date)
    if relative_match:
        return relative_match

    # Try "between X and Y" patterns
    between_match = _extract_between_dates(query_lower, reference_date)
    if between_match:
        return between_match

    # Fallback to dateparser for other expressions
    parsed = dateparser.parse(query, settings=settings)
    if parsed:
        # If we got a single date, create a range around it (±1 day)
        start_date = parsed.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = parsed.replace(hour=23, minute=59, second=59, microsecond=999999)
        return (start_date, end_date)

    return None


def _extract_season(query: str, reference_date: datetime) -> Optional[Tuple[datetime, datetime]]:
    """Extract season-based temporal constraint."""
    seasons = {
        'spring': (3, 5),   # March - May
        'summer': (6, 8),   # June - August
        'fall': (9, 11),    # September - November
        'autumn': (9, 11),  # September - November
        'winter': (12, 2),  # December - February
    }

    for season_name, (start_month, end_month) in seasons.items():
        if season_name not in query:
            continue

        # Determine year based on "last", "this", "next"
        year = reference_date.year
        if 'last' in query:
            year -= 1
        elif 'next' in query:
            year += 1

        # Handle winter crossing year boundary
        if season_name in ('winter',):
            if start_month > end_month:
                # Winter spans two years (Dec-Feb)
                start_date = datetime(year, start_month, 1)
                end_date = datetime(year + 1, end_month, 28)  # Feb 28
                if _is_leap_year(year + 1):
                    end_date = datetime(year + 1, end_month, 29)
            else:
                start_date = datetime(year, start_month, 1)
                end_date = _last_day_of_month(year, end_month)
        else:
            start_date = datetime(year, start_month, 1)
            end_date = _last_day_of_month(year, end_month)

        return (start_date, end_date)

    return None


def _extract_month(query: str, reference_date: datetime) -> Optional[Tuple[datetime, datetime]]:
    """Extract month-based temporal constraint."""
    months = {
        'january': 1, 'february': 2, 'march': 3, 'april': 4,
        'may': 5, 'june': 6, 'july': 7, 'august': 8,
        'september': 9, 'october': 10, 'november': 11, 'december': 12,
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4,
        'jun': 6, 'jul': 7, 'aug': 8, 'sep': 9,
        'oct': 10, 'nov': 11, 'dec': 12,
    }

    for month_name, month_num in months.items():
        if month_name not in query:
            continue

        # Determine year
        year = reference_date.year

        # Check if query mentions "last" before the month
        if 'last' in query and query.index('last') < query.index(month_name):
            year -= 1
        # Check if current date is past this month, assume last year
        elif reference_date.month > month_num:
            pass  # Use current year (past month)
        elif reference_date.month < month_num:
            year -= 1  # Use last year

        start_date = datetime(year, month_num, 1)
        end_date = _last_day_of_month(year, month_num)

        return (start_date, end_date)

    return None


def _extract_relative_period(query: str, reference_date: datetime) -> Optional[Tuple[datetime, datetime]]:
    """Extract relative period like 'last year', 'last month', 'last week'."""

    # Last year
    if 'last year' in query:
        year = reference_date.year - 1
        return (datetime(year, 1, 1), datetime(year, 12, 31, 23, 59, 59))

    # This year
    if 'this year' in query:
        year = reference_date.year
        return (datetime(year, 1, 1), datetime(year, 12, 31, 23, 59, 59))

    # Last month
    if 'last month' in query:
        first_day = reference_date.replace(day=1)
        last_month_end = first_day - timedelta(days=1)
        last_month_start = last_month_end.replace(day=1)
        return (last_month_start, last_month_end.replace(hour=23, minute=59, second=59))

    # This month
    if 'this month' in query:
        start = reference_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end = _last_day_of_month(reference_date.year, reference_date.month)
        return (start, end)

    # Last week
    if 'last week' in query:
        days_since_monday = reference_date.weekday()
        last_monday = reference_date - timedelta(days=days_since_monday + 7)
        last_sunday = last_monday + timedelta(days=6)
        return (
            last_monday.replace(hour=0, minute=0, second=0, microsecond=0),
            last_sunday.replace(hour=23, minute=59, second=59, microsecond=999999)
        )

    return None


def _extract_between_dates(query: str, reference_date: datetime) -> Optional[Tuple[datetime, datetime]]:
    """Extract 'between X and Y' date ranges."""
    pattern = r'between\s+(\w+)\s+and\s+(\w+)'
    match = re.search(pattern, query.lower())

    if not match:
        return None

    start_str = match.group(1)
    end_str = match.group(2)

    import dateparser
    settings = {'RELATIVE_BASE': reference_date, 'RETURN_AS_TIMEZONE_AWARE': False}

    start_date = dateparser.parse(start_str, settings=settings)
    end_date = dateparser.parse(end_str, settings=settings)

    if start_date and end_date:
        return (
            start_date.replace(hour=0, minute=0, second=0, microsecond=0),
            end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        )

    return None


def _last_day_of_month(year: int, month: int) -> datetime:
    """Get last day of month."""
    if month == 12:
        next_month = datetime(year + 1, 1, 1)
    else:
        next_month = datetime(year, month + 1, 1)
    last_day = next_month - timedelta(days=1)
    return last_day.replace(hour=23, minute=59, second=59, microsecond=999999)


def _is_leap_year(year: int) -> bool:
    """Check if year is leap year."""
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
