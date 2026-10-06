"""Single-item retain forwards observation_scopes and strategy, as retain_batch items already do."""

from unittest.mock import MagicMock

import pytest

from hindsight_client import Hindsight


def _capture_retain(monkeypatch, client, captured):
    async def fake_retain(bank_id, request_obj, _request_timeout=None):
        captured["request"] = request_obj
        return MagicMock(success=True)

    monkeypatch.setattr(client._memory_api, "retain_memories", fake_retain)


@pytest.mark.parametrize("scopes", ["per_tag", "combined", "all_combinations", "shared", [["project:p1"], []]])
def test_retain_forwards_scopes_and_strategy(monkeypatch, scopes):
    client = Hindsight(base_url="http://example.invalid")
    captured: dict[str, object] = {}
    _capture_retain(monkeypatch, client, captured)

    client.retain("test-bank", "Meeting notes", observation_scopes=scopes, strategy="meeting")

    item = captured["request"].items[0]
    assert item.observation_scopes.actual_instance == scopes
    assert item.strategy == "meeting"


async def test_aretain_forwards_scopes_and_strategy(monkeypatch):
    client = Hindsight(base_url="http://example.invalid")
    captured: dict[str, object] = {}
    _capture_retain(monkeypatch, client, captured)

    await client.aretain("test-bank", "Meeting notes", observation_scopes="shared", strategy="meeting")

    item = captured["request"].items[0]
    assert item.observation_scopes.actual_instance == "shared"
    assert item.strategy == "meeting"


def test_retain_omits_scopes_and_strategy_by_default(monkeypatch):
    client = Hindsight(base_url="http://example.invalid")
    captured: dict[str, object] = {}
    _capture_retain(monkeypatch, client, captured)

    client.retain("test-bank", "Meeting notes")

    item = captured["request"].items[0]
    assert item.observation_scopes is None
    assert item.strategy is None
