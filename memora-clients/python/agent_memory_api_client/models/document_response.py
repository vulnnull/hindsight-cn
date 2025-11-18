from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="DocumentResponse")


@_attrs_define
class DocumentResponse:
    """Response model for get document endpoint.

    Example:
        {'agent_id': 'user123', 'content_hash': 'abc123', 'created_at': '2024-01-15T10:30:00Z', 'id': 'session_1',
            'memory_unit_count': 15, 'original_text': 'Full document text here...', 'updated_at': '2024-01-15T10:30:00Z'}

    Attributes:
        id (str):
        agent_id (str):
        original_text (str):
        content_hash (None | str):
        created_at (str):
        updated_at (str):
        memory_unit_count (int):
    """

    id: str
    agent_id: str
    original_text: str
    content_hash: None | str
    created_at: str
    updated_at: str
    memory_unit_count: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        agent_id = self.agent_id

        original_text = self.original_text

        content_hash: None | str
        content_hash = self.content_hash

        created_at = self.created_at

        updated_at = self.updated_at

        memory_unit_count = self.memory_unit_count

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "agent_id": agent_id,
                "original_text": original_text,
                "content_hash": content_hash,
                "created_at": created_at,
                "updated_at": updated_at,
                "memory_unit_count": memory_unit_count,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        agent_id = d.pop("agent_id")

        original_text = d.pop("original_text")

        def _parse_content_hash(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        content_hash = _parse_content_hash(d.pop("content_hash"))

        created_at = d.pop("created_at")

        updated_at = d.pop("updated_at")

        memory_unit_count = d.pop("memory_unit_count")

        document_response = cls(
            id=id,
            agent_id=agent_id,
            original_text=original_text,
            content_hash=content_hash,
            created_at=created_at,
            updated_at=updated_at,
            memory_unit_count=memory_unit_count,
        )

        document_response.additional_properties = d
        return document_response

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
