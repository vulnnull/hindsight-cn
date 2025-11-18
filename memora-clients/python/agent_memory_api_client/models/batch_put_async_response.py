from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="BatchPutAsyncResponse")


@_attrs_define
class BatchPutAsyncResponse:
    """Response model for async batch put endpoint.

    Example:
        {'agent_id': 'user123', 'document_id': 'conversation_123', 'items_count': 2, 'message': 'Batch put task queued
            for background processing', 'queued': True, 'success': True}

    Attributes:
        success (bool):
        message (str):
        agent_id (str):
        items_count (int):
        queued (bool):
        document_id (None | str | Unset):
    """

    success: bool
    message: str
    agent_id: str
    items_count: int
    queued: bool
    document_id: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        success = self.success

        message = self.message

        agent_id = self.agent_id

        items_count = self.items_count

        queued = self.queued

        document_id: None | str | Unset
        if isinstance(self.document_id, Unset):
            document_id = UNSET
        else:
            document_id = self.document_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "success": success,
                "message": message,
                "agent_id": agent_id,
                "items_count": items_count,
                "queued": queued,
            }
        )
        if document_id is not UNSET:
            field_dict["document_id"] = document_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        success = d.pop("success")

        message = d.pop("message")

        agent_id = d.pop("agent_id")

        items_count = d.pop("items_count")

        queued = d.pop("queued")

        def _parse_document_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        document_id = _parse_document_id(d.pop("document_id", UNSET))

        batch_put_async_response = cls(
            success=success,
            message=message,
            agent_id=agent_id,
            items_count=items_count,
            queued=queued,
            document_id=document_id,
        )

        batch_put_async_response.additional_properties = d
        return batch_put_async_response

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
