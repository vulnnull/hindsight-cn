"""Tests for hindsight_hermes.tools module."""

import json
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from hindsight_hermes.config import configure, reset_config
from hindsight_hermes.errors import HindsightError
from hindsight_hermes.tools import (
    RECALL_SCHEMA,
    REFLECT_SCHEMA,
    RETAIN_SCHEMA,
    _resolve_bank_id,
    _resolve_client,
    get_tool_definitions,
    memory_instructions,
    register,
    register_tools,
)


# --- Fixtures ---


@pytest.fixture(autouse=True)
def _clean_config():
    reset_config()
    yield
    reset_config()


@pytest.fixture()
def mock_client():
    client = MagicMock()
    client.create_bank = MagicMock()
    client.retain = MagicMock()
    client.recall = MagicMock(
        return_value=SimpleNamespace(
            results=[
                SimpleNamespace(text="Memory 1"),
                SimpleNamespace(text="Memory 2"),
            ]
        )
    )
    client.reflect = MagicMock(return_value=SimpleNamespace(text="Synthesized answer"))
    return client


@pytest.fixture()
def mock_registry():
    """Patch tools.registry.registry so register_tools() can import it."""
    mock_reg = MagicMock()
    mock_module = MagicMock()
    mock_module.registry = mock_reg
    with patch.dict(sys.modules, {"tools": MagicMock(), "tools.registry": mock_module}):
        yield mock_reg


# --- Schema tests ---


class TestSchemas:
    def test_retain_schema_has_content(self):
        assert RETAIN_SCHEMA["name"] == "hindsight_retain"
        assert "content" in RETAIN_SCHEMA["parameters"]["properties"]
        assert "content" in RETAIN_SCHEMA["parameters"]["required"]

    def test_recall_schema_has_query(self):
        assert RECALL_SCHEMA["name"] == "hindsight_recall"
        assert "query" in RECALL_SCHEMA["parameters"]["properties"]
        assert "query" in RECALL_SCHEMA["parameters"]["required"]

    def test_reflect_schema_has_query(self):
        assert REFLECT_SCHEMA["name"] == "hindsight_reflect"
        assert "query" in REFLECT_SCHEMA["parameters"]["properties"]

    def test_get_tool_definitions(self):
        defs = get_tool_definitions()
        assert len(defs) == 3
        names = {d["name"] for d in defs}
        assert names == {"hindsight_retain", "hindsight_recall", "hindsight_reflect"}


# --- Bank resolution tests ---


class TestResolveBankId:
    def test_bank_resolver_takes_priority(self):
        resolver = lambda args: "resolved-bank"
        assert _resolve_bank_id({}, "static-bank", resolver) == "resolved-bank"

    def test_static_bank_id(self):
        assert _resolve_bank_id({}, "static-bank", None) == "static-bank"

    def test_env_var_fallback(self, monkeypatch):
        monkeypatch.setenv("HINDSIGHT_BANK_ID", "env-bank")
        assert _resolve_bank_id({}, None, None) == "env-bank"

    def test_raises_when_no_bank(self, monkeypatch):
        monkeypatch.delenv("HINDSIGHT_BANK_ID", raising=False)
        with pytest.raises(HindsightError, match="No bank_id available"):
            _resolve_bank_id({}, None, None)


# --- Client resolution tests ---


class TestResolveClient:
    def test_returns_provided_client(self, mock_client):
        assert _resolve_client(mock_client, None, None) is mock_client

    def test_uses_global_config(self):
        configure(hindsight_api_url="http://localhost:9999", api_key="key")
        with patch("hindsight_hermes.tools.Hindsight") as MockH:
            _resolve_client(None, None, None)
            MockH.assert_called_once_with(base_url="http://localhost:9999", timeout=30.0, api_key="key")

    def test_raises_without_url(self):
        with pytest.raises(HindsightError, match="No Hindsight API URL"):
            _resolve_client(None, None, None)


# --- register_tools tests ---


class TestRegisterTools:
    def test_registers_three_tools(self, mock_client, mock_registry):
        register_tools(bank_id="b", client=mock_client)
        assert mock_registry.register.call_count == 3
        names = {call.kwargs["name"] for call in mock_registry.register.call_args_list}
        assert names == {"hindsight_retain", "hindsight_recall", "hindsight_reflect"}

    def test_retain_handler_success(self, mock_client, mock_registry):
        register_tools(bank_id="b", client=mock_client)
        handler = mock_registry.register.call_args_list[0].kwargs["handler"]
        result = json.loads(handler({"content": "hello"}))
        assert result["result"] == "Memory stored successfully."
        mock_client.retain.assert_called_once_with(bank_id="b", content="hello")

    def test_retain_handler_with_tags(self, mock_client, mock_registry):
        register_tools(bank_id="b", client=mock_client, tags=["tag1"])
        handler = mock_registry.register.call_args_list[0].kwargs["handler"]
        handler({"content": "hello"})
        mock_client.retain.assert_called_once_with(bank_id="b", content="hello", tags=["tag1"])

    def test_recall_handler_success(self, mock_client, mock_registry):
        register_tools(bank_id="b", client=mock_client)
        handler = mock_registry.register.call_args_list[1].kwargs["handler"]
        result = json.loads(handler({"query": "test"}))
        assert "Memory 1" in result["result"]
        assert "Memory 2" in result["result"]

    def test_recall_handler_no_results(self, mock_client, mock_registry):
        mock_client.recall.return_value = SimpleNamespace(results=[])
        register_tools(bank_id="b", client=mock_client)
        handler = mock_registry.register.call_args_list[1].kwargs["handler"]
        result = json.loads(handler({"query": "test"}))
        assert result["result"] == "No relevant memories found."

    def test_reflect_handler_success(self, mock_client, mock_registry):
        register_tools(bank_id="b", client=mock_client)
        handler = mock_registry.register.call_args_list[2].kwargs["handler"]
        result = json.loads(handler({"query": "test"}))
        assert result["result"] == "Synthesized answer"

    def test_handler_returns_error_on_exception(self, mock_client, mock_registry):
        mock_client.retain.side_effect = RuntimeError("boom")
        register_tools(bank_id="b", client=mock_client)
        handler = mock_registry.register.call_args_list[0].kwargs["handler"]
        result = json.loads(handler({"content": "hello"}))
        assert "error" in result
        assert "boom" in result["error"]

    def test_ensure_bank_called(self, mock_client, mock_registry):
        register_tools(bank_id="b", client=mock_client)
        handler = mock_registry.register.call_args_list[0].kwargs["handler"]
        handler({"content": "hello"})
        mock_client.create_bank.assert_called_once_with(bank_id="b", name="b")

    def test_ensure_bank_idempotent(self, mock_client, mock_registry):
        register_tools(bank_id="b", client=mock_client)
        handler = mock_registry.register.call_args_list[0].kwargs["handler"]
        handler({"content": "first"})
        handler({"content": "second"})
        # create_bank should only be called once
        mock_client.create_bank.assert_called_once()


# --- register (plugin entry point) tests ---


class TestRegisterPlugin:
    def test_register_calls_ctx_register_tool(self, monkeypatch, mock_client):
        monkeypatch.setenv("HINDSIGHT_API_URL", "http://localhost:8888")
        monkeypatch.setenv("HINDSIGHT_BANK_ID", "test-bank")
        ctx = MagicMock()
        with patch("hindsight_hermes.tools._resolve_client", return_value=mock_client):
            register(ctx)
        assert ctx.register_tool.call_count == 3

    def test_register_skips_without_config(self, monkeypatch):
        monkeypatch.delenv("HINDSIGHT_API_URL", raising=False)
        monkeypatch.delenv("HINDSIGHT_API_KEY", raising=False)
        ctx = MagicMock()
        register(ctx)
        ctx.register_tool.assert_not_called()


# --- memory_instructions tests ---


class TestMemoryInstructions:
    def test_returns_formatted_memories(self, mock_client):
        result = memory_instructions(bank_id="b", client=mock_client)
        assert "Relevant memories:" in result
        assert "1. Memory 1" in result
        assert "2. Memory 2" in result

    def test_returns_empty_on_no_results(self, mock_client):
        mock_client.recall.return_value = SimpleNamespace(results=[])
        result = memory_instructions(bank_id="b", client=mock_client)
        assert result == ""

    def test_returns_empty_on_exception(self, mock_client):
        mock_client.recall.side_effect = RuntimeError("fail")
        result = memory_instructions(bank_id="b", client=mock_client)
        assert result == ""

    def test_returns_empty_on_no_client(self):
        result = memory_instructions(bank_id="b")
        assert result == ""

    def test_respects_max_results(self, mock_client):
        result = memory_instructions(bank_id="b", client=mock_client, max_results=1)
        assert "1. Memory 1" in result
        assert "Memory 2" not in result

    def test_custom_prefix(self, mock_client):
        result = memory_instructions(bank_id="b", client=mock_client, prefix="Context:\n")
        assert result.startswith("Context:")
