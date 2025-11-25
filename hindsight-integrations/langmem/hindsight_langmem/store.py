"""Hindsight implementation of LangGraph BaseStore interface."""

import json
from typing import Any, Iterable

from hindsight_client import Hindsight
from langgraph.store.base import (
    BaseStore,
    GetOp,
    Item,
    ListNamespacesOp,
    Op,
    PutOp,
    Result,
    SearchItem,
    SearchOp,
)


class HindsightStore(BaseStore):
    """
    Hindsight implementation of LangGraph BaseStore.

    This store uses Hindsight's memory system as a backend for LangGraph's memory storage.
    Each namespace maps to a Hindsight agent, and items are stored as memory units.

    Args:
        base_url: The base URL of the Hindsight API server
        default_agent_id: Default agent ID to use when namespace is empty (optional)
    """

    def __init__(self, base_url: str, default_agent_id: str | None = None):
        """Initialize the Hindsight store.

        Args:
            base_url: Base URL for the Hindsight API
            default_agent_id: Default agent ID when namespace is empty
        """
        super().__init__()
        self.client = Hindsight(base_url=base_url)
        self.default_agent_id = default_agent_id or "default"
        self._ensure_agent_exists(self.default_agent_id)

    def _namespace_to_agent_id(self, namespace: tuple[str, ...]) -> str:
        """Convert namespace to agent ID."""
        if not namespace:
            return self.default_agent_id
        return "__".join(namespace)

    def _ensure_agent_exists(self, agent_id: str) -> None:
        """Ensure an agent exists, create if it doesn't."""
        try:
            # Try to create agent (idempotent operation)
            self.client.create_agent(agent_id=agent_id)
        except Exception:
            # Agent likely already exists
            pass

    def _serialize_value(self, value: dict[str, Any]) -> str:
        """Serialize a value to JSON string."""
        return json.dumps(value, sort_keys=True)

    def _deserialize_value(self, content: str) -> dict[str, Any]:
        """Deserialize JSON string back to value."""
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {"content": content}

    def batch(self, ops: Iterable[Op]) -> list[Result]:
        """Execute a batch of operations synchronously."""
        results: list[Result] = []
        for op in ops:
            if isinstance(op, PutOp):
                results.append(self._put(op))
            elif isinstance(op, GetOp):
                results.append(self._get(op))
            elif isinstance(op, SearchOp):
                results.append(self._search(op))
            elif isinstance(op, ListNamespacesOp):
                results.append(self._list_namespaces(op))
            else:
                results.append(None)
        return results

    async def abatch(self, ops: Iterable[Op]) -> list[Result]:
        """Execute a batch of operations asynchronously."""
        return self.batch(ops)

    def _put(self, op: PutOp) -> None:
        """Store an item."""
        agent_id = self._namespace_to_agent_id(op.namespace)
        self._ensure_agent_exists(agent_id)

        value_with_key = {"__key__": op.key, **op.value}
        content = self._serialize_value(value_with_key)

        self.client.put(
            agent_id=agent_id,
            content=content,
            context=f"key:{op.key}",
            document_id=op.key,
        )
        return None

    def _get(self, op: GetOp) -> Item | None:
        """Retrieve an item by namespace and key."""
        agent_id = self._namespace_to_agent_id(op.namespace)

        try:
            response = self.client.get_document(agent_id=agent_id, document_id=op.key)

            if not response or not response.get("original_text"):
                return None

            # Parse the original text to get the value
            value = self._deserialize_value(response["original_text"])
            stored_key = value.pop("__key__", op.key)

            if stored_key != op.key:
                return None

            return Item(
                namespace=op.namespace,
                key=op.key,
                value=value,
                created_at=response.get("created_at"),
                updated_at=response.get("updated_at"),
            )
        except Exception:
            return None

    def _search(self, op: SearchOp) -> list[SearchItem]:
        """Search for items within a namespace prefix."""
        agent_id = self._namespace_to_agent_id(op.namespace_prefix)

        try:
            results = self.client.search(
                agent_id=agent_id,
                query=op.query or "",
                max_tokens=op.limit * 100,
            )

            if not results:
                return []

            items: list[SearchItem] = []
            seen_keys = set()

            for result in results[op.offset : op.offset + op.limit]:
                try:
                    text = result.get("text", "")
                    value = self._deserialize_value(text)
                    key = value.pop("__key__", result.get("id"))

                    if key in seen_keys:
                        continue
                    seen_keys.add(key)

                    items.append(
                        SearchItem(
                            namespace=op.namespace_prefix,
                            key=key,
                            value=value,
                            score=1.0,
                            created_at=None,
                            updated_at=None,
                        )
                    )

                    if len(items) >= op.limit:
                        break
                except Exception:
                    continue

            return items
        except Exception:
            return []

    def _list_namespaces(self, op: ListNamespacesOp) -> list[tuple[str, ...]]:
        """List all namespaces."""
        # Not fully implemented - would need to list all agents
        return []

    def _matches_prefix(self, namespace: tuple[str, ...], prefix: tuple[str, ...]) -> bool:
        """Check if namespace matches prefix."""
        if len(namespace) < len(prefix):
            return False
        return namespace[: len(prefix)] == prefix

    def _matches_suffix(self, namespace: tuple[str, ...], suffix: tuple[str, ...]) -> bool:
        """Check if namespace matches suffix."""
        if len(namespace) < len(suffix):
            return False
        return namespace[-len(suffix) :] == suffix

    def put(
        self,
        namespace: tuple[str, ...],
        key: str,
        value: dict[str, Any],
        index: bool | list[str] | None = None,
    ) -> None:
        """Store a single item."""
        self._put(PutOp(namespace=namespace, key=key, value=value))

    async def aput(
        self,
        namespace: tuple[str, ...],
        key: str,
        value: dict[str, Any],
        index: bool | list[str] | None = None,
    ) -> None:
        """Store a single item asynchronously."""
        self.put(namespace, key, value, index)

    def get(self, namespace: tuple[str, ...], key: str) -> Item | None:
        """Retrieve a single item."""
        return self._get(GetOp(namespace=namespace, key=key))

    async def aget(self, namespace: tuple[str, ...], key: str) -> Item | None:
        """Retrieve a single item asynchronously."""
        return self.get(namespace, key)

    def delete(self, namespace: tuple[str, ...], key: str) -> None:
        """Delete an item by deleting the document."""
        agent_id = self._namespace_to_agent_id(namespace)

        try:
            self.client.delete_document(agent_id=agent_id, document_id=key)
        except Exception:
            pass

    async def adelete(self, namespace: tuple[str, ...], key: str) -> None:
        """Delete an item asynchronously."""
        self.delete(namespace, key)

    def search(
        self,
        namespace_prefix: tuple[str, ...],
        query: str | None = None,
        filter: dict[str, Any] | None = None,
        limit: int = 10,
        offset: int = 0,
    ) -> list[SearchItem]:
        """Search for items."""
        return self._search(SearchOp(namespace_prefix=namespace_prefix, query=query, limit=limit, offset=offset))

    async def asearch(
        self,
        namespace_prefix: tuple[str, ...],
        query: str | None = None,
        filter: dict[str, Any] | None = None,
        limit: int = 10,
        offset: int = 0,
    ) -> list[SearchItem]:
        """Search for items asynchronously."""
        return self.search(namespace_prefix, query, filter, limit, offset)

    def list_namespaces(
        self,
        prefix: tuple[str, ...] | None = None,
        suffix: tuple[str, ...] | None = None,
        max_depth: int | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[tuple[str, ...]]:
        """List all namespaces."""
        return self._list_namespaces(
            ListNamespacesOp(prefix=prefix, suffix=suffix, max_depth=max_depth, limit=limit, offset=offset)
        )

    async def alist_namespaces(
        self,
        prefix: tuple[str, ...] | None = None,
        suffix: tuple[str, ...] | None = None,
        max_depth: int | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[tuple[str, ...]]:
        """List all namespaces asynchronously."""
        return self.list_namespaces(prefix, suffix, max_depth, limit, offset)
