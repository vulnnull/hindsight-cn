"""
Test query analyzer for temporal extraction.
"""
import pytest
from datetime import datetime
from hindsight_api.engine.query_analyzer import TransformerQueryAnalyzer, QueryAnalysis


def test_query_analyzer_june_2024(query_analyzer):
    reference_date = datetime(2025, 1, 15, 12, 0, 0)

    query = "june 2024"
    analysis = query_analyzer.analyze(query, reference_date)

    print(f"\nQuery: '{query}'")
    print(f"Analysis: {analysis}")

    assert analysis.temporal_constraint is not None, "Should extract temporal constraint"
    assert analysis.temporal_constraint.start_date.year == 2024
    assert analysis.temporal_constraint.start_date.month == 6
    assert analysis.temporal_constraint.start_date.day == 1
    assert analysis.temporal_constraint.end_date.year == 2024
    assert analysis.temporal_constraint.end_date.month == 6
    assert analysis.temporal_constraint.end_date.day == 30


def test_query_analyzer_dogs_june_2023(query_analyzer):
    reference_date = datetime(2025, 1, 15, 12, 0, 0)

    query = "dogs in June 2023"
    analysis = query_analyzer.analyze(query, reference_date)

    print(f"\nQuery: '{query}'")
    print(f"Analysis: {analysis}")

    assert analysis.temporal_constraint is not None, "Should extract temporal constraint"
    assert analysis.temporal_constraint.start_date.year == 2023
    assert analysis.temporal_constraint.start_date.month == 6
    assert analysis.temporal_constraint.start_date.day == 1
    assert analysis.temporal_constraint.end_date.year == 2023
    assert analysis.temporal_constraint.end_date.month == 6
    assert analysis.temporal_constraint.end_date.day == 30


def test_query_analyzer_march_2023(query_analyzer):
    reference_date = datetime(2025, 1, 15, 12, 0, 0)

    query = "March 2023"
    analysis = query_analyzer.analyze(query, reference_date)

    print(f"\nQuery: '{query}'")
    print(f"Analysis: {analysis}")

    assert analysis.temporal_constraint is not None, "Should extract temporal constraint"
    assert analysis.temporal_constraint.start_date.year == 2023
    assert analysis.temporal_constraint.start_date.month == 3
    assert analysis.temporal_constraint.start_date.day == 1
    assert analysis.temporal_constraint.end_date.year == 2023
    assert analysis.temporal_constraint.end_date.month == 3
    assert analysis.temporal_constraint.end_date.day == 31


def test_query_analyzer_last_year(query_analyzer):
    reference_date = datetime(2025, 1, 15, 12, 0, 0)

    query = "last year"
    analysis = query_analyzer.analyze(query, reference_date)

    print(f"\nQuery: '{query}'")
    print(f"Analysis: {analysis}")

    assert analysis.temporal_constraint is not None, "Should extract temporal constraint"
    assert analysis.temporal_constraint.start_date.year == 2024
    assert analysis.temporal_constraint.start_date.month == 1
    assert analysis.temporal_constraint.start_date.day == 1
    assert analysis.temporal_constraint.end_date.year == 2024
    assert analysis.temporal_constraint.end_date.month == 12
    assert analysis.temporal_constraint.end_date.day == 31


def test_query_analyzer_no_temporal(query_analyzer):
    reference_date = datetime(2025, 1, 15, 12, 0, 0)

    query = "what is the weather"
    analysis = query_analyzer.analyze(query, reference_date)

    print(f"\nQuery: '{query}'")
    print(f"Analysis: {analysis}")

    assert analysis.temporal_constraint is None, "Should not extract temporal constraint"


def test_query_analyzer_activities_june_2024(query_analyzer):
    reference_date = datetime(2025, 1, 15, 12, 0, 0)

    query = "melanie activities in june 2024"
    analysis = query_analyzer.analyze(query, reference_date)

    print(f"\nQuery: '{query}'")
    print(f"Analysis: {analysis}")

    assert analysis.temporal_constraint is not None, "Should extract temporal constraint"
    assert analysis.temporal_constraint.start_date.year == 2024
    assert analysis.temporal_constraint.start_date.month == 6
    assert analysis.temporal_constraint.start_date.day == 1
    assert analysis.temporal_constraint.end_date.year == 2024
    assert analysis.temporal_constraint.end_date.month == 6
    assert analysis.temporal_constraint.end_date.day == 30


