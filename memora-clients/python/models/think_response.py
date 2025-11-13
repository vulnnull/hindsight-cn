from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.think_fact import ThinkFact


T = TypeVar("T", bound="ThinkResponse")


@_attrs_define
class ThinkResponse:
    """Response model for think endpoint.

    Example:
        {'based_on': [{'activation': 0.9, 'id': '123', 'text': 'AI is used in healthcare', 'type': 'world'},
            {'activation': 0.85, 'id': '456', 'text': 'I discussed AI applications last week', 'type': 'agent'}],
            'new_opinions': ['AI has great potential when used responsibly'], 'text': 'Based on my understanding, AI is a
            transformative technology...'}

    Attributes:
        text (str):
        based_on (list[ThinkFact] | Unset):
        new_opinions (list[str] | Unset):
    """

    text: str
    based_on: list[ThinkFact] | Unset = UNSET
    new_opinions: list[str] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        text = self.text

        based_on: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.based_on, Unset):
            based_on = []
            for based_on_item_data in self.based_on:
                based_on_item = based_on_item_data.to_dict()
                based_on.append(based_on_item)

        new_opinions: list[str] | Unset = UNSET
        if not isinstance(self.new_opinions, Unset):
            new_opinions = self.new_opinions

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "text": text,
            }
        )
        if based_on is not UNSET:
            field_dict["based_on"] = based_on
        if new_opinions is not UNSET:
            field_dict["new_opinions"] = new_opinions

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.think_fact import ThinkFact

        d = dict(src_dict)
        text = d.pop("text")

        _based_on = d.pop("based_on", UNSET)
        based_on: list[ThinkFact] | Unset = UNSET
        if _based_on is not UNSET:
            based_on = []
            for based_on_item_data in _based_on:
                based_on_item = ThinkFact.from_dict(based_on_item_data)

                based_on.append(based_on_item)

        new_opinions = cast(list[str], d.pop("new_opinions", UNSET))

        think_response = cls(
            text=text,
            based_on=based_on,
            new_opinions=new_opinions,
        )

        think_response.additional_properties = d
        return think_response

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
