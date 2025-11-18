from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.agent_list_item import AgentListItem


T = TypeVar("T", bound="AgentListResponse")


@_attrs_define
class AgentListResponse:
    """Response model for listing all agents.

    Example:
        {'agents': [{'agent_id': 'user123', 'background': 'I am a software engineer', 'created_at':
            '2024-01-15T10:30:00Z', 'personality': {'agreeableness': 0.5, 'bias_strength': 0.5, 'conscientiousness': 0.5,
            'extraversion': 0.5, 'neuroticism': 0.5, 'openness': 0.5}, 'updated_at': '2024-01-16T14:20:00Z'}]}

    Attributes:
        agents (list[AgentListItem]):
    """

    agents: list[AgentListItem]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        agents = []
        for agents_item_data in self.agents:
            agents_item = agents_item_data.to_dict()
            agents.append(agents_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "agents": agents,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.agent_list_item import AgentListItem

        d = dict(src_dict)
        agents = []
        _agents = d.pop("agents")
        for agents_item_data in _agents:
            agents_item = AgentListItem.from_dict(agents_item_data)

            agents.append(agents_item)

        agent_list_response = cls(
            agents=agents,
        )

        agent_list_response.additional_properties = d
        return agent_list_response

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
