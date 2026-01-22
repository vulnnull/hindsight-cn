"""
Tests for the reflect agent with mocked LLM outputs.

These tests verify:
1. Tool name normalization for various LLM output formats
2. Recovery from unknown tool calls
3. Recovery from tool execution errors
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from hindsight_api.engine.reflect.agent import (
    _normalize_tool_name,
    _is_done_tool,
    run_reflect_agent,
)
from hindsight_api.engine.response_models import LLMToolCall, LLMToolCallResult


class TestToolNameNormalization:
    """Test tool name normalization for various LLM output formats."""

    def test_normalize_standard_name(self):
        """Standard tool names should pass through unchanged."""
        assert _normalize_tool_name("done") == "done"
        assert _normalize_tool_name("recall") == "recall"
        assert _normalize_tool_name("search_reflections") == "search_reflections"
        assert _normalize_tool_name("search_mental_models") == "search_mental_models"
        assert _normalize_tool_name("expand") == "expand"

    def test_normalize_functions_prefix(self):
        """Tool names with 'functions.' prefix should be normalized."""
        assert _normalize_tool_name("functions.done") == "done"
        assert _normalize_tool_name("functions.recall") == "recall"
        assert _normalize_tool_name("functions.search_reflections") == "search_reflections"

    def test_normalize_call_equals_prefix(self):
        """Tool names with 'call=' prefix should be normalized."""
        assert _normalize_tool_name("call=done") == "done"
        assert _normalize_tool_name("call=recall") == "recall"

    def test_normalize_call_equals_functions_prefix(self):
        """Tool names with 'call=functions.' prefix should be normalized."""
        assert _normalize_tool_name("call=functions.done") == "done"
        assert _normalize_tool_name("call=functions.recall") == "recall"
        assert _normalize_tool_name("call=functions.search_mental_models") == "search_mental_models"

    def test_is_done_tool(self):
        """Test _is_done_tool helper."""
        # Standard
        assert _is_done_tool("done") is True
        assert _is_done_tool("recall") is False

        # With prefixes
        assert _is_done_tool("functions.done") is True
        assert _is_done_tool("call=done") is True
        assert _is_done_tool("call=functions.done") is True

        # Not done
        assert _is_done_tool("functions.recall") is False
        assert _is_done_tool("call=functions.recall") is False


class TestReflectAgentMocked:
    """Test reflect agent with mocked LLM outputs."""

    @pytest.fixture
    def mock_llm(self):
        """Create a mock LLM provider."""
        llm = MagicMock()
        llm.call_with_tools = AsyncMock()
        # Also mock call() for final iteration fallback
        llm.call = AsyncMock(return_value="Fallback answer from final iteration")
        return llm

    @pytest.fixture
    def mock_functions(self):
        """Create mock search/recall functions."""
        return {
            "search_reflections_fn": AsyncMock(return_value={"reflections": []}),
            "search_mental_models_fn": AsyncMock(return_value={"mental_models": []}),
            "recall_fn": AsyncMock(return_value={"memories": [{"id": "mem-1", "content": "test memory"}]}),
            "expand_fn": AsyncMock(return_value={"memories": []}),
        }

    @pytest.mark.asyncio
    async def test_handles_functions_prefix_in_done(self, mock_llm, mock_functions):
        """Test that 'functions.done' is handled correctly."""
        # First call: LLM calls recall
        # Second call: LLM calls functions.done
        mock_llm.call_with_tools.side_effect = [
            LLMToolCallResult(
                tool_calls=[LLMToolCall(id="1", name="recall", arguments={"query": "test"})],
                finish_reason="tool_calls",
            ),
            LLMToolCallResult(
                tool_calls=[
                    LLMToolCall(
                        id="2",
                        name="functions.done",
                        arguments={"answer": "Test answer", "memory_ids": ["mem-1"]},
                    )
                ],
                finish_reason="tool_calls",
            ),
        ]

        result = await run_reflect_agent(
            llm_config=mock_llm,
            bank_id="test-bank",
            query="test query",
            bank_profile={"name": "Test", "mission": "Testing"},
            **mock_functions,
        )

        assert result.text == "Test answer"
        assert "mem-1" in result.used_memory_ids

    @pytest.mark.asyncio
    async def test_handles_call_equals_functions_prefix(self, mock_llm, mock_functions):
        """Test that 'call=functions.done' is handled correctly."""
        mock_llm.call_with_tools.side_effect = [
            LLMToolCallResult(
                tool_calls=[LLMToolCall(id="1", name="recall", arguments={"query": "test"})],
                finish_reason="tool_calls",
            ),
            LLMToolCallResult(
                tool_calls=[
                    LLMToolCall(
                        id="2",
                        name="call=functions.done",
                        arguments={"answer": "Test answer", "memory_ids": ["mem-1"]},
                    )
                ],
                finish_reason="tool_calls",
            ),
        ]

        result = await run_reflect_agent(
            llm_config=mock_llm,
            bank_id="test-bank",
            query="test query",
            bank_profile={"name": "Test", "mission": "Testing"},
            **mock_functions,
        )

        assert result.text == "Test answer"

    @pytest.mark.asyncio
    async def test_recovery_from_unknown_tool(self, mock_llm, mock_functions):
        """Test that LLM can recover after calling an unknown tool."""
        # First call: LLM calls unknown tool
        # Second call: LLM calls valid recall after seeing error
        # Third call: LLM calls done
        mock_llm.call_with_tools.side_effect = [
            LLMToolCallResult(
                tool_calls=[LLMToolCall(id="1", name="invalid_tool", arguments={"foo": "bar"})],
                finish_reason="tool_calls",
            ),
            LLMToolCallResult(
                tool_calls=[LLMToolCall(id="2", name="recall", arguments={"query": "test"})],
                finish_reason="tool_calls",
            ),
            LLMToolCallResult(
                tool_calls=[
                    LLMToolCall(
                        id="3",
                        name="done",
                        arguments={"answer": "Recovered successfully", "memory_ids": ["mem-1"]},
                    )
                ],
                finish_reason="tool_calls",
            ),
        ]

        result = await run_reflect_agent(
            llm_config=mock_llm,
            bank_id="test-bank",
            query="test query",
            bank_profile={"name": "Test", "mission": "Testing"},
            **mock_functions,
        )

        assert result.text == "Recovered successfully"
        # Verify the LLM was called 3 times (initial + recovery + done)
        assert mock_llm.call_with_tools.call_count == 3

    @pytest.mark.asyncio
    async def test_recovery_from_tool_execution_error(self, mock_llm, mock_functions):
        """Test that LLM can recover after a tool execution fails."""
        # Make recall fail the first time, succeed the second time
        mock_functions["recall_fn"].side_effect = [
            Exception("Database connection failed"),
            {"memories": [{"id": "mem-1", "content": "test memory"}]},
        ]

        mock_llm.call_with_tools.side_effect = [
            LLMToolCallResult(
                tool_calls=[LLMToolCall(id="1", name="recall", arguments={"query": "test"})],
                finish_reason="tool_calls",
            ),
            # LLM tries again after seeing error
            LLMToolCallResult(
                tool_calls=[LLMToolCall(id="2", name="recall", arguments={"query": "test retry"})],
                finish_reason="tool_calls",
            ),
            LLMToolCallResult(
                tool_calls=[
                    LLMToolCall(
                        id="3",
                        name="done",
                        arguments={"answer": "Recovered from error", "memory_ids": ["mem-1"]},
                    )
                ],
                finish_reason="tool_calls",
            ),
        ]

        result = await run_reflect_agent(
            llm_config=mock_llm,
            bank_id="test-bank",
            query="test query",
            bank_profile={"name": "Test", "mission": "Testing"},
            **mock_functions,
        )

        assert result.text == "Recovered from error"
        assert mock_llm.call_with_tools.call_count == 3

    @pytest.mark.asyncio
    async def test_normalizes_tool_names_in_other_tools(self, mock_llm, mock_functions):
        """Test that tool names are normalized for all tools, not just done."""
        mock_llm.call_with_tools.side_effect = [
            # LLM calls 'functions.recall' instead of 'recall'
            LLMToolCallResult(
                tool_calls=[LLMToolCall(id="1", name="functions.recall", arguments={"query": "test"})],
                finish_reason="tool_calls",
            ),
            LLMToolCallResult(
                tool_calls=[
                    LLMToolCall(
                        id="2",
                        name="done",
                        arguments={"answer": "Test answer", "memory_ids": ["mem-1"]},
                    )
                ],
                finish_reason="tool_calls",
            ),
        ]

        result = await run_reflect_agent(
            llm_config=mock_llm,
            bank_id="test-bank",
            query="test query",
            bank_profile={"name": "Test", "mission": "Testing"},
            **mock_functions,
        )

        assert result.text == "Test answer"
        # Verify recall was actually called (normalization worked)
        mock_functions["recall_fn"].assert_called_once()

    @pytest.mark.asyncio
    async def test_max_iterations_reached(self, mock_llm, mock_functions):
        """Test that agent stops after max iterations even with errors."""
        # LLM keeps calling unknown tools
        mock_llm.call_with_tools.return_value = LLMToolCallResult(
            tool_calls=[LLMToolCall(id="1", name="unknown_tool", arguments={})],
            finish_reason="tool_calls",
        )

        result = await run_reflect_agent(
            llm_config=mock_llm,
            bank_id="test-bank",
            query="test query",
            bank_profile={"name": "Test", "mission": "Testing"},
            max_iterations=3,
            **mock_functions,
        )

        # Should have a result even if no memories found
        assert result is not None
        assert result.iterations == 3
