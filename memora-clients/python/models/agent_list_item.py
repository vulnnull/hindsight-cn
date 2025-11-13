from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.personality_traits import PersonalityTraits


T = TypeVar("T", bound="AgentListItem")


@_attrs_define
class AgentListItem:
    """Agent list item with profile summary.

    Attributes:
        agent_id (str):
        personality (PersonalityTraits): Personality traits based on Big Five model. Example: {'agreeableness': 0.7,
            'bias_strength': 0.7, 'conscientiousness': 0.6, 'extraversion': 0.5, 'neuroticism': 0.3, 'openness': 0.8}.
        background (str):
        created_at (None | str | Unset):
        updated_at (None | str | Unset):
    """

    agent_id: str
    personality: PersonalityTraits
    background: str
    created_at: None | str | Unset = UNSET
    updated_at: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        agent_id = self.agent_id

        personality = self.personality.to_dict()

        background = self.background

        created_at: None | str | Unset
        if isinstance(self.created_at, Unset):
            created_at = UNSET
        else:
            created_at = self.created_at

        updated_at: None | str | Unset
        if isinstance(self.updated_at, Unset):
            updated_at = UNSET
        else:
            updated_at = self.updated_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "agent_id": agent_id,
                "personality": personality,
                "background": background,
            }
        )
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.personality_traits import PersonalityTraits

        d = dict(src_dict)
        agent_id = d.pop("agent_id")

        personality = PersonalityTraits.from_dict(d.pop("personality"))

        background = d.pop("background")

        def _parse_created_at(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        created_at = _parse_created_at(d.pop("created_at", UNSET))

        def _parse_updated_at(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        updated_at = _parse_updated_at(d.pop("updated_at", UNSET))

        agent_list_item = cls(
            agent_id=agent_id,
            personality=personality,
            background=background,
            created_at=created_at,
            updated_at=updated_at,
        )

        agent_list_item.additional_properties = d
        return agent_list_item

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
