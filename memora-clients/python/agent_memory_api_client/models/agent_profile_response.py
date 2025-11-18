from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.personality_traits import PersonalityTraits


T = TypeVar("T", bound="AgentProfileResponse")


@_attrs_define
class AgentProfileResponse:
    """Response model for agent profile.

    Example:
        {'agent_id': 'user123', 'background': 'I am a software engineer with 10 years of experience in startups',
            'personality': {'agreeableness': 0.7, 'bias_strength': 0.7, 'conscientiousness': 0.6, 'extraversion': 0.5,
            'neuroticism': 0.3, 'openness': 0.8}}

    Attributes:
        agent_id (str):
        personality (PersonalityTraits): Personality traits based on Big Five model. Example: {'agreeableness': 0.7,
            'bias_strength': 0.7, 'conscientiousness': 0.6, 'extraversion': 0.5, 'neuroticism': 0.3, 'openness': 0.8}.
        background (str):
    """

    agent_id: str
    personality: PersonalityTraits
    background: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        agent_id = self.agent_id

        personality = self.personality.to_dict()

        background = self.background

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "agent_id": agent_id,
                "personality": personality,
                "background": background,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.personality_traits import PersonalityTraits

        d = dict(src_dict)
        agent_id = d.pop("agent_id")

        personality = PersonalityTraits.from_dict(d.pop("personality"))

        background = d.pop("background")

        agent_profile_response = cls(
            agent_id=agent_id,
            personality=personality,
            background=background,
        )

        agent_profile_response.additional_properties = d
        return agent_profile_response

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
