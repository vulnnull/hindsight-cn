from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ThinkFact")


@_attrs_define
class ThinkFact:
    """A fact used in think response.

    Example:
        {'context': 'healthcare discussion', 'event_date': '2024-01-15T10:30:00Z', 'id':
            '123e4567-e89b-12d3-a456-426614174000', 'text': 'AI is used in healthcare', 'type': 'world'}

    Attributes:
        text (str):
        id (None | str | Unset):
        type_ (None | str | Unset):
        activation (float | None | Unset):
        context (None | str | Unset):
        event_date (None | str | Unset):
    """

    text: str
    id: None | str | Unset = UNSET
    type_: None | str | Unset = UNSET
    activation: float | None | Unset = UNSET
    context: None | str | Unset = UNSET
    event_date: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        text = self.text

        id: None | str | Unset
        if isinstance(self.id, Unset):
            id = UNSET
        else:
            id = self.id

        type_: None | str | Unset
        if isinstance(self.type_, Unset):
            type_ = UNSET
        else:
            type_ = self.type_

        activation: float | None | Unset
        if isinstance(self.activation, Unset):
            activation = UNSET
        else:
            activation = self.activation

        context: None | str | Unset
        if isinstance(self.context, Unset):
            context = UNSET
        else:
            context = self.context

        event_date: None | str | Unset
        if isinstance(self.event_date, Unset):
            event_date = UNSET
        else:
            event_date = self.event_date

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "text": text,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if type_ is not UNSET:
            field_dict["type"] = type_
        if activation is not UNSET:
            field_dict["activation"] = activation
        if context is not UNSET:
            field_dict["context"] = context
        if event_date is not UNSET:
            field_dict["event_date"] = event_date

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        text = d.pop("text")

        def _parse_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        id = _parse_id(d.pop("id", UNSET))

        def _parse_type_(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        type_ = _parse_type_(d.pop("type", UNSET))

        def _parse_activation(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        activation = _parse_activation(d.pop("activation", UNSET))

        def _parse_context(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        context = _parse_context(d.pop("context", UNSET))

        def _parse_event_date(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        event_date = _parse_event_date(d.pop("event_date", UNSET))

        think_fact = cls(
            text=text,
            id=id,
            type_=type_,
            activation=activation,
            context=context,
            event_date=event_date,
        )

        think_fact.additional_properties = d
        return think_fact

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
