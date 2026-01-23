"""Tests for the shared MCP tools module."""

from datetime import datetime, timezone

import pytest

from hindsight_api.mcp_tools import build_content_dict, parse_timestamp


class TestParseTimestamp:
    """Tests for parse_timestamp function."""

    def test_parse_iso_format_with_z(self):
        """Test parsing ISO format with Z suffix."""
        result = parse_timestamp("2024-01-15T10:30:00Z")
        assert result == datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)

    def test_parse_iso_format_with_offset(self):
        """Test parsing ISO format with timezone offset."""
        result = parse_timestamp("2024-01-15T10:30:00+00:00")
        assert result == datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)

    def test_parse_iso_format_without_tz(self):
        """Test parsing ISO format without timezone."""
        result = parse_timestamp("2024-01-15T10:30:00")
        assert result == datetime(2024, 1, 15, 10, 30, 0)

    def test_parse_invalid_format_raises(self):
        """Test that invalid format raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            parse_timestamp("not-a-date")
        assert "Invalid timestamp format" in str(exc_info.value)


class TestBuildContentDict:
    """Tests for build_content_dict function."""

    def test_basic_content(self):
        """Test building content dict with just content and context."""
        result, error = build_content_dict("test content", "test_context")
        assert error is None
        assert result == {"content": "test content", "context": "test_context"}

    def test_with_valid_timestamp(self):
        """Test building content dict with valid timestamp."""
        result, error = build_content_dict("test content", "test_context", "2024-01-15T10:30:00Z")
        assert error is None
        assert result["content"] == "test content"
        assert result["context"] == "test_context"
        assert result["event_date"] == datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)

    def test_with_invalid_timestamp(self):
        """Test building content dict with invalid timestamp."""
        result, error = build_content_dict("test content", "test_context", "invalid")
        assert error is not None
        assert "Invalid timestamp format" in error
        assert result == {}

    def test_with_none_timestamp(self):
        """Test building content dict with None timestamp."""
        result, error = build_content_dict("test content", "test_context", None)
        assert error is None
        assert "event_date" not in result
