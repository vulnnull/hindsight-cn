"""Test local MCP server."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_memory():
    """Create a mock MemoryEngine."""
    memory = MagicMock()
    memory._initialized = True
    memory.retain_batch_async = AsyncMock()
    memory.recall_async = AsyncMock(return_value=MagicMock(results=[]))
    return memory


@pytest.mark.asyncio
async def test_local_mcp_server_retain(mock_memory):
    """Test that retain tool fires async and returns immediately."""
    from hindsight_api.mcp_local import create_local_mcp_server

    bank_id = "test-bank"
    mcp_server = create_local_mcp_server(bank_id, memory=mock_memory)

    # Get the tools
    tools = mcp_server._tool_manager._tools
    assert "retain" in tools

    # Call retain
    retain_tool = tools["retain"]
    result = await retain_tool.fn(content="test content", context="test_context")

    # Returns immediately with accepted status
    assert result["status"] == "accepted"

    # Wait for background task to complete
    await asyncio.sleep(0.1)

    # Verify the memory was called correctly
    mock_memory.retain_batch_async.assert_called_once()
    call_kwargs = mock_memory.retain_batch_async.call_args.kwargs
    assert call_kwargs["bank_id"] == "test-bank"
    assert call_kwargs["contents"] == [{"content": "test content", "context": "test_context"}]


@pytest.mark.asyncio
async def test_local_mcp_server_recall(mock_memory):
    """Test that recall tool calls memory.recall_async with correct params."""
    from hindsight_api.mcp_local import create_local_mcp_server
    from hindsight_api.engine.memory_engine import Budget

    # Mock recall_async to return a proper pydantic model
    mock_result = MagicMock()
    mock_result.model_dump.return_value = {"results": []}
    mock_memory.recall_async = AsyncMock(return_value=mock_result)

    bank_id = "test-bank"
    mcp_server = create_local_mcp_server(bank_id, memory=mock_memory)

    # Get the tools
    tools = mcp_server._tool_manager._tools
    assert "recall" in tools

    # Call recall
    recall_tool = tools["recall"]
    result = await recall_tool.fn(query="test query", max_tokens=2048)

    # Result is a dict
    assert isinstance(result, dict)

    # Verify the memory was called correctly
    mock_memory.recall_async.assert_called_once()
    call_kwargs = mock_memory.recall_async.call_args.kwargs
    assert call_kwargs["bank_id"] == "test-bank"
    assert call_kwargs["query"] == "test query"
    assert call_kwargs["max_tokens"] == 2048
    assert call_kwargs["budget"] == Budget.HIGH


@pytest.mark.asyncio
async def test_local_mcp_server_retain_with_default_context(mock_memory):
    """Test that retain uses default context when not provided."""
    from hindsight_api.mcp_local import create_local_mcp_server

    bank_id = "test-bank"
    mcp_server = create_local_mcp_server(bank_id, memory=mock_memory)

    tools = mcp_server._tool_manager._tools
    retain_tool = tools["retain"]

    # Call retain without context
    await retain_tool.fn(content="test content")

    # Wait for background task
    await asyncio.sleep(0.1)

    call_kwargs = mock_memory.retain_batch_async.call_args.kwargs
    assert call_kwargs["contents"] == [{"content": "test content", "context": "general"}]


@pytest.mark.asyncio
async def test_local_mcp_server_retain_error_handling(mock_memory):
    """Test that retain errors are logged but don't affect response."""
    from hindsight_api.mcp_local import create_local_mcp_server

    mock_memory.retain_batch_async = AsyncMock(side_effect=Exception("Test error"))

    mcp_server = create_local_mcp_server("test-bank", memory=mock_memory)

    tools = mcp_server._tool_manager._tools
    retain_tool = tools["retain"]

    # Retain returns immediately with accepted status (fire and forget)
    result = await retain_tool.fn(content="test content")
    assert result["status"] == "accepted"

    # Wait for background task to complete (and log error)
    await asyncio.sleep(0.1)


@pytest.mark.asyncio
async def test_local_mcp_server_recall_error_handling(mock_memory):
    """Test that recall handles errors gracefully."""
    from hindsight_api.mcp_local import create_local_mcp_server

    mock_memory.recall_async = AsyncMock(side_effect=Exception("Test error"))

    mcp_server = create_local_mcp_server("test-bank", memory=mock_memory)

    tools = mcp_server._tool_manager._tools
    recall_tool = tools["recall"]

    result = await recall_tool.fn(query="test query")

    # Result is a dict with error
    assert isinstance(result, dict)
    assert "error" in result
    assert result["results"] == []


@pytest.mark.asyncio
async def test_local_mcp_server_recall_with_defaults(mock_memory):
    """Test that recall uses default max_tokens and HIGH budget."""
    from hindsight_api.mcp_local import create_local_mcp_server
    from hindsight_api.engine.memory_engine import Budget

    mock_result = MagicMock()
    mock_result.model_dump.return_value = {"results": []}
    mock_memory.recall_async = AsyncMock(return_value=mock_result)

    mcp_server = create_local_mcp_server("test-bank", memory=mock_memory)

    tools = mcp_server._tool_manager._tools
    recall_tool = tools["recall"]

    # Call with defaults
    await recall_tool.fn(query="test query")

    call_kwargs = mock_memory.recall_async.call_args.kwargs
    assert call_kwargs["max_tokens"] == 4096
    assert call_kwargs["budget"] == Budget.HIGH


@pytest.mark.asyncio
async def test_local_mcp_server_retain_with_timestamp(mock_memory):
    """Test that retain passes timestamp as event_date."""
    from datetime import datetime, timezone
    from hindsight_api.mcp_local import create_local_mcp_server

    mcp_server = create_local_mcp_server("test-bank", memory=mock_memory)

    tools = mcp_server._tool_manager._tools
    retain_tool = tools["retain"]

    # Call retain with timestamp
    result = await retain_tool.fn(
        content="test content", context="test_context", timestamp="2024-01-15T10:30:00Z"
    )

    assert result["status"] == "accepted"

    # Wait for background task
    await asyncio.sleep(0.1)

    call_kwargs = mock_memory.retain_batch_async.call_args.kwargs
    contents = call_kwargs["contents"]
    assert len(contents) == 1
    assert contents[0]["content"] == "test content"
    assert contents[0]["context"] == "test_context"
    assert "event_date" in contents[0]
    assert contents[0]["event_date"] == datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)


@pytest.mark.asyncio
async def test_local_mcp_server_retain_with_invalid_timestamp(mock_memory):
    """Test that retain rejects invalid timestamp format."""
    from hindsight_api.mcp_local import create_local_mcp_server

    mcp_server = create_local_mcp_server("test-bank", memory=mock_memory)

    tools = mcp_server._tool_manager._tools
    retain_tool = tools["retain"]

    # Call retain with invalid timestamp
    result = await retain_tool.fn(content="test content", timestamp="not-a-date")

    assert result["status"] == "error"
    assert "Invalid timestamp format" in result["message"]

    # Verify retain_batch_async was NOT called
    mock_memory.retain_batch_async.assert_not_called()
