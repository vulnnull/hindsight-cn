from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="AddBackgroundRequest")


@_attrs_define
class AddBackgroundRequest:
    """Request model for adding/merging background information.

    Example:
        {'content': 'I was born in Texas', 'update_personality': True}

    Attributes:
        content (str): New background information to add or merge
        update_personality (bool | Unset): If true, infer Big Five personality traits from the merged background
            (default: true) Default: True.
    """

    content: str
    update_personality: bool | Unset = True
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        content = self.content

        update_personality = self.update_personality

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "content": content,
            }
        )
        if update_personality is not UNSET:
            field_dict["update_personality"] = update_personality

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        content = d.pop("content")

        update_personality = d.pop("update_personality", UNSET)

        add_background_request = cls(
            content=content,
            update_personality=update_personality,
        )

        add_background_request.additional_properties = d
        return add_background_request

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
