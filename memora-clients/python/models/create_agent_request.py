from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.personality_traits import PersonalityTraits


T = TypeVar("T", bound="CreateAgentRequest")


@_attrs_define
class CreateAgentRequest:
    """Request model for creating/updating an agent.

    Example:
        {'background': 'I am a creative software engineer with 10 years of experience', 'personality': {'agreeableness':
            0.7, 'bias_strength': 0.7, 'conscientiousness': 0.6, 'extraversion': 0.5, 'neuroticism': 0.3, 'openness': 0.8}}

    Attributes:
        personality (None | PersonalityTraits | Unset):
        background (None | str | Unset):
    """

    personality: None | PersonalityTraits | Unset = UNSET
    background: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.personality_traits import PersonalityTraits

        personality: dict[str, Any] | None | Unset
        if isinstance(self.personality, Unset):
            personality = UNSET
        elif isinstance(self.personality, PersonalityTraits):
            personality = self.personality.to_dict()
        else:
            personality = self.personality

        background: None | str | Unset
        if isinstance(self.background, Unset):
            background = UNSET
        else:
            background = self.background

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if personality is not UNSET:
            field_dict["personality"] = personality
        if background is not UNSET:
            field_dict["background"] = background

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.personality_traits import PersonalityTraits

        d = dict(src_dict)

        def _parse_personality(data: object) -> None | PersonalityTraits | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                personality_type_0 = PersonalityTraits.from_dict(data)

                return personality_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | PersonalityTraits | Unset, data)

        personality = _parse_personality(d.pop("personality", UNSET))

        def _parse_background(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        background = _parse_background(d.pop("background", UNSET))

        create_agent_request = cls(
            personality=personality,
            background=background,
        )

        create_agent_request.additional_properties = d
        return create_agent_request

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
