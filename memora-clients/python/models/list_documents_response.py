from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.list_documents_response_items_item import ListDocumentsResponseItemsItem


T = TypeVar("T", bound="ListDocumentsResponse")


@_attrs_define
class ListDocumentsResponse:
    """Response model for list documents endpoint.

    Example:
        {'items': [{'agent_id': 'user123', 'content_hash': 'abc123', 'created_at': '2024-01-15T10:30:00Z', 'id':
            'session_1', 'memory_unit_count': 15, 'text_length': 5420, 'updated_at': '2024-01-15T10:30:00Z'}], 'limit': 100,
            'offset': 0, 'total': 50}

    Attributes:
        items (list[ListDocumentsResponseItemsItem]):
        total (int):
        limit (int):
        offset (int):
    """

    items: list[ListDocumentsResponseItemsItem]
    total: int
    limit: int
    offset: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        items = []
        for items_item_data in self.items:
            items_item = items_item_data.to_dict()
            items.append(items_item)

        total = self.total

        limit = self.limit

        offset = self.offset

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "items": items,
                "total": total,
                "limit": limit,
                "offset": offset,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.list_documents_response_items_item import ListDocumentsResponseItemsItem

        d = dict(src_dict)
        items = []
        _items = d.pop("items")
        for items_item_data in _items:
            items_item = ListDocumentsResponseItemsItem.from_dict(items_item_data)

            items.append(items_item)

        total = d.pop("total")

        limit = d.pop("limit")

        offset = d.pop("offset")

        list_documents_response = cls(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
        )

        list_documents_response.additional_properties = d
        return list_documents_response

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
