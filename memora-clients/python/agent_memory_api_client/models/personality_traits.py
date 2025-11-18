from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="PersonalityTraits")


@_attrs_define
class PersonalityTraits:
    """Personality traits based on Big Five model.

    Example:
        {'agreeableness': 0.7, 'bias_strength': 0.7, 'conscientiousness': 0.6, 'extraversion': 0.5, 'neuroticism': 0.3,
            'openness': 0.8}

    Attributes:
        openness (float): Openness to experience (0-1)
        conscientiousness (float): Conscientiousness (0-1)
        extraversion (float): Extraversion (0-1)
        agreeableness (float): Agreeableness (0-1)
        neuroticism (float): Neuroticism (0-1)
        bias_strength (float): How strongly personality influences opinions (0-1)
    """

    openness: float
    conscientiousness: float
    extraversion: float
    agreeableness: float
    neuroticism: float
    bias_strength: float
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        openness = self.openness

        conscientiousness = self.conscientiousness

        extraversion = self.extraversion

        agreeableness = self.agreeableness

        neuroticism = self.neuroticism

        bias_strength = self.bias_strength

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "openness": openness,
                "conscientiousness": conscientiousness,
                "extraversion": extraversion,
                "agreeableness": agreeableness,
                "neuroticism": neuroticism,
                "bias_strength": bias_strength,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        openness = d.pop("openness")

        conscientiousness = d.pop("conscientiousness")

        extraversion = d.pop("extraversion")

        agreeableness = d.pop("agreeableness")

        neuroticism = d.pop("neuroticism")

        bias_strength = d.pop("bias_strength")

        personality_traits = cls(
            openness=openness,
            conscientiousness=conscientiousness,
            extraversion=extraversion,
            agreeableness=agreeableness,
            neuroticism=neuroticism,
            bias_strength=bias_strength,
        )

        personality_traits.additional_properties = d
        return personality_traits

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
