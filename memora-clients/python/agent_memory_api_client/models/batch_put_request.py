from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.memory_item import MemoryItem


T = TypeVar("T", bound="BatchPutRequest")


@_attrs_define
class BatchPutRequest:
    """Request model for batch put endpoint.

    Example:
        {'document_id': 'conversation_123', 'items': [{'content': 'Alice works at Google', 'context': 'work'},
            {'content': 'Bob went hiking yesterday', 'event_date': '2024-01-15T10:00:00Z'}]}

    Attributes:
        items (list[MemoryItem]):
        document_id (None | str | Unset):
    """

    items: list[MemoryItem]
    document_id: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        items = []
        for items_item_data in self.items:
            items_item = items_item_data.to_dict()
            items.append(items_item)

        document_id: None | str | Unset
        if isinstance(self.document_id, Unset):
            document_id = UNSET
        else:
            document_id = self.document_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "items": items,
            }
        )
        if document_id is not UNSET:
            field_dict["document_id"] = document_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.memory_item import MemoryItem

        d = dict(src_dict)
        items = []
        _items = d.pop("items")
        for items_item_data in _items:
            items_item = MemoryItem.from_dict(items_item_data)

            items.append(items_item)

        def _parse_document_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        document_id = _parse_document_id(d.pop("document_id", UNSET))

        batch_put_request = cls(
            items=items,
            document_id=document_id,
        )

        batch_put_request.additional_properties = d
        return batch_put_request

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
