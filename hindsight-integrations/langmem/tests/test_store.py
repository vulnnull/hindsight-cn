"""Tests for HindsightStore implementation."""

import os
import time

import pytest

from hindsight_langmem import HindsightStore


@pytest.fixture
def store():
    """Create a HindsightStore instance for testing."""
    base_url = os.getenv("HINDSIGHT_API_URL", "http://localhost:8888")
    return HindsightStore(base_url=base_url, default_agent_id=f"test_agent_{int(time.time())}")


def test_put_and_get(store):
    """Test storing and retrieving an item."""
    namespace = ("test", "namespace")
    key = "test_key"
    value = {"data": "test_value", "number": 42}

    store.put(namespace, key, value)

    time.sleep(1)

    retrieved = store.get(namespace, key)
    assert retrieved is not None
    assert retrieved.key == key
    assert retrieved.namespace == namespace
    assert retrieved.value == value


def test_search(store):
    """Test searching for items."""
    namespace = ("search", "test")
    key1 = "item1"
    value1 = {"content": "This is about machine learning", "type": "note"}

    key2 = "item2"
    value2 = {"content": "This is about deep learning and neural networks", "type": "article"}

    store.put(namespace, key1, value1)
    store.put(namespace, key2, value2)

    time.sleep(2)

    results = store.search(namespace, query="machine learning", limit=5)

    assert len(results) > 0
    assert any(r.key in [key1, key2] for r in results)


def test_delete(store):
    """Test deleting an item."""
    namespace = ("delete", "test")
    key = "to_delete"
    value = {"data": "temporary"}

    store.put(namespace, key, value)

    time.sleep(1)

    retrieved = store.get(namespace, key)
    assert retrieved is not None

    store.delete(namespace, key)

    time.sleep(1)

    retrieved_after_delete = store.get(namespace, key)
    assert retrieved_after_delete is None


def test_list_namespaces(store):
    """Test listing namespaces."""
    namespace1 = ("list", "test", "one")
    namespace2 = ("list", "test", "two")

    store.put(namespace1, "key1", {"data": "value1"})
    store.put(namespace2, "key2", {"data": "value2"})

    time.sleep(1)

    namespaces = store.list_namespaces(prefix=("list",))

    assert len(namespaces) >= 2
    assert namespace1 in namespaces
    assert namespace2 in namespaces


def test_batch_operations(store):
    """Test batch operations."""
    from langgraph.store.base import GetOp, PutOp

    namespace = ("batch", "test")

    ops = [
        PutOp(namespace=namespace, key="key1", value={"data": "value1"}),
        PutOp(namespace=namespace, key="key2", value={"data": "value2"}),
    ]

    results = store.batch(ops)
    assert len(results) == 2

    time.sleep(1)

    get_ops = [
        GetOp(namespace=namespace, key="key1"),
        GetOp(namespace=namespace, key="key2"),
    ]

    get_results = store.batch(get_ops)
    assert len(get_results) == 2
    assert get_results[0] is not None
    assert get_results[0].value == {"data": "value1"}
    assert get_results[1] is not None
    assert get_results[1].value == {"data": "value2"}
