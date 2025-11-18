from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.personality_traits import PersonalityTraits


T = TypeVar("T", bound="BackgroundResponse")


@_attrs_define
class BackgroundResponse:
    """Response model for background update.

    Example:
        {'background': 'I was born in Texas. I am a software engineer with 10 years of experience.', 'personality':
            {'agreeableness': 0.8, 'bias_strength': 0.6, 'conscientiousness': 0.6, 'extraversion': 0.5, 'neuroticism': 0.4,
            'openness': 0.7}}

    Attributes:
        background (str):
        personality (None | PersonalityTraits | Unset):
    """

    background: str
    personality: None | PersonalityTraits | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.personality_traits import PersonalityTraits

        background = self.background

        personality: dict[str, Any] | None | Unset
        if isinstance(self.personality, Unset):
            personality = UNSET
        elif isinstance(self.personality, PersonalityTraits):
            personality = self.personality.to_dict()
        else:
            personality = self.personality

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "background": background,
            }
        )
        if personality is not UNSET:
            field_dict["personality"] = personality

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.personality_traits import PersonalityTraits

        d = dict(src_dict)
        background = d.pop("background")

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

        background_response = cls(
            background=background,
            personality=personality,
        )

        background_response.additional_properties = d
        return background_response

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
