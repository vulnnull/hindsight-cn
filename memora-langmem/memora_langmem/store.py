"""Memora implementation of LangGraph BaseStore interface."""

import json
from typing import Any, Iterable

from agent_memory_api_client import Client
from agent_memory_api_client.api.agent_management import (
    api_agents_api_v1_agents_get,
    api_create_or_update_agent_api_v1_agents_agent_id_put,
)
from agent_memory_api_client.api.memory_operations import (
    api_batch_put_api_v1_agents_agent_id_memories_post,
    api_delete_memory_unit_api_v1_agents_agent_id_memories_unit_id_delete,
    api_list_api_v1_agents_agent_id_memories_list_get,
    api_search_api_v1_agents_agent_id_memories_search_post,
)
from agent_memory_api_client.models import BatchPutRequest, CreateAgentRequest, MemoryItem, SearchRequest
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


class MemoraStore(BaseStore):
    """
    Memora implementation of LangGraph BaseStore.

    This store uses Memora's memory system as a backend for LangGraph's memory storage.
    Each namespace maps to a Memora agent, and items are stored as memory units.

    Args:
        base_url: The base URL of the Memora API server
        default_agent_id: Default agent ID to use when namespace is empty (optional)
    """

    def __init__(self, base_url: str, default_agent_id: str | None = None):
        """Initialize the Memora store.

        Args:
            base_url: Base URL for the Memora API
            default_agent_id: Default agent ID when namespace is empty
        """
        super().__init__()
        self.client = Client(base_url=base_url)
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
            response = api_agents_api_v1_agents_get.sync_detailed(client=self.client)
            if response.parsed and hasattr(response.parsed, "items"):
                existing_ids = [agent.agent_id for agent in response.parsed.items]
                if agent_id not in existing_ids:
                    self._create_agent(agent_id)
        except Exception:
            self._create_agent(agent_id)

    def _create_agent(self, agent_id: str) -> None:
        """Create a new agent."""
        request = CreateAgentRequest()
        api_create_or_update_agent_api_v1_agents_agent_id_put.sync_detailed(
            agent_id=agent_id, client=self.client, body=request
        )

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

        memory_item = MemoryItem(content=content, context=f"key:{op.key}")
        request = BatchPutRequest(items=[memory_item], document_id=op.key)

        api_batch_put_api_v1_agents_agent_id_memories_post.sync_detailed(
            agent_id=agent_id, client=self.client, body=request
        )
        return None

    def _get(self, op: GetOp) -> Item | None:
        """Retrieve an item by namespace and key."""
        agent_id = self._namespace_to_agent_id(op.namespace)

        try:
            response = api_list_api_v1_agents_agent_id_memories_list_get.sync_detailed(
                agent_id=agent_id, client=self.client, limit=1000
            )

            if not response.parsed or not hasattr(response.parsed, "items"):
                return None

            for memory_unit in response.parsed.items:
                if hasattr(memory_unit, "document_id") and memory_unit.document_id == op.key:
                    try:
                        value = self._deserialize_value(memory_unit.content or "{}")
                        stored_key = value.pop("__key__", op.key)
                        if stored_key == op.key:
                            return Item(
                                namespace=op.namespace,
                                key=op.key,
                                value=value,
                                created_at=getattr(memory_unit, "created_at", None),
                                updated_at=getattr(memory_unit, "updated_at", None),
                            )
                    except Exception:
                        continue

            return None
        except Exception:
            return None

    def _search(self, op: SearchOp) -> list[SearchItem]:
        """Search for items within a namespace prefix."""
        agent_id = self._namespace_to_agent_id(op.namespace_prefix)

        try:
            search_request = SearchRequest(query=op.query or "", max_tokens=op.limit * 100)

            response = api_search_api_v1_agents_agent_id_memories_search_post.sync_detailed(
                agent_id=agent_id, client=self.client, body=search_request
            )

            if not response.parsed or not hasattr(response.parsed, "results"):
                return []

            results: list[SearchItem] = []
            seen_keys = set()

            for result in response.parsed.results[op.offset : op.offset + op.limit]:
                try:
                    value = self._deserialize_value(result.fact or "{}")
                    key = value.pop("__key__", result.fact_id)

                    if key in seen_keys:
                        continue
                    seen_keys.add(key)

                    results.append(
                        SearchItem(
                            namespace=op.namespace_prefix,
                            key=key,
                            value=value,
                            score=getattr(result, "score", 1.0),
                            created_at=getattr(result, "created_at", None),
                            updated_at=getattr(result, "updated_at", None),
                        )
                    )

                    if len(results) >= op.limit:
                        break
                except Exception:
                    continue

            return results
        except Exception:
            return []

    def _list_namespaces(self, op: ListNamespacesOp) -> list[tuple[str, ...]]:
        """List all namespaces."""
        try:
            response = api_agents_api_v1_agents_get.sync_detailed(client=self.client)

            if not response.parsed or not hasattr(response.parsed, "items"):
                return []

            namespaces = []
            for agent in response.parsed.items:
                if hasattr(agent, "agent_id"):
                    namespace = tuple(agent.agent_id.split("__"))

                    if op.prefix and not self._matches_prefix(namespace, op.prefix):
                        continue
                    if op.suffix and not self._matches_suffix(namespace, op.suffix):
                        continue
                    if op.max_depth is not None and len(namespace) > op.max_depth:
                        continue

                    namespaces.append(namespace)

            return namespaces[op.offset : op.offset + op.limit]
        except Exception:
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
        """Delete an item."""
        agent_id = self._namespace_to_agent_id(namespace)

        try:
            response = api_list_api_v1_agents_agent_id_memories_list_get.sync_detailed(
                agent_id=agent_id, client=self.client, limit=1000
            )

            if response.parsed and hasattr(response.parsed, "items"):
                for memory_unit in response.parsed.items:
                    if hasattr(memory_unit, "document_id") and memory_unit.document_id == key:
                        if hasattr(memory_unit, "unit_id"):
                            api_delete_memory_unit_api_v1_agents_agent_id_memories_unit_id_delete.sync_detailed(
                                agent_id=agent_id, unit_id=memory_unit.unit_id, client=self.client
                            )
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
