"""Test MCP server routing with dynamic bank_id."""

import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_memory():
    """Create a mock MemoryEngine."""
    memory = MagicMock()
    memory.retain_batch_async = AsyncMock()
    memory.recall_async = AsyncMock(return_value=MagicMock(results=[]))
    return memory


@pytest.mark.asyncio
async def test_mcp_context_variable():
    """Test that context variable works correctly."""
    from hindsight_api.api.mcp import get_current_bank_id, _current_bank_id

    # Initially None
    assert get_current_bank_id() is None

    # Set and verify
    token = _current_bank_id.set("test-bank-123")
    try:
        assert get_current_bank_id() == "test-bank-123"
    finally:
        _current_bank_id.reset(token)

    # Back to None after reset
    assert get_current_bank_id() is None


@pytest.mark.asyncio
async def test_mcp_tools_use_context_bank_id(mock_memory):
    """Test that MCP tools use bank_id from context."""
    from hindsight_api.api.mcp import create_mcp_server, _current_bank_id

    mcp_server = create_mcp_server(mock_memory)

    # Get the tools
    tools = mcp_server._tool_manager._tools
    assert "retain" in tools
    assert "recall" in tools

    # Test retain with bank_id from context
    token = _current_bank_id.set("context-bank-id")
    try:
        retain_tool = tools["retain"]
        result = await retain_tool.fn(content="test content", context="test_context")
        assert "successfully" in result.lower()

        # Verify the memory was called with the context bank_id
        mock_memory.retain_batch_async.assert_called_once()
        call_kwargs = mock_memory.retain_batch_async.call_args.kwargs
        assert call_kwargs["bank_id"] == "context-bank-id"
    finally:
        _current_bank_id.reset(token)


def test_path_parsing_logic():
    """Test the path parsing logic for bank_id extraction."""
    def parse_path(path):
        """Simulate the path parsing logic from MCPMiddleware."""
        if not path.startswith("/") or len(path) <= 1:
            return None, None  # Error case

        parts = path[1:].split("/", 1)
        if not parts[0]:
            return None, None  # Error case

        bank_id = parts[0]
        new_path = "/" + parts[1] if len(parts) > 1 else "/"
        return bank_id, new_path

    # Test bank-specific paths
    bank_id, remaining = parse_path("/my-bank/")
    assert bank_id == "my-bank"
    assert remaining == "/"

    bank_id, remaining = parse_path("/my-bank")
    assert bank_id == "my-bank"
    assert remaining == "/"

    # Test error case - no bank_id
    bank_id, remaining = parse_path("/")
    assert bank_id is None

    # Test with complex bank_id
    bank_id, remaining = parse_path("/user_12345/")
    assert bank_id == "user_12345"
    assert remaining == "/"

    # Test with additional path after bank_id
    bank_id, remaining = parse_path("/my-bank/some/path")
    assert bank_id == "my-bank"
    assert remaining == "/some/path"
