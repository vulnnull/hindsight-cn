from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.graph_data_response_edges_item import GraphDataResponseEdgesItem
    from ..models.graph_data_response_nodes_item import GraphDataResponseNodesItem
    from ..models.graph_data_response_table_rows_item import GraphDataResponseTableRowsItem


T = TypeVar("T", bound="GraphDataResponse")


@_attrs_define
class GraphDataResponse:
    """Response model for graph data endpoint.

    Example:
        {'edges': [{'from': '1', 'to': '2', 'type': 'semantic', 'weight': 0.8}], 'nodes': [{'id': '1', 'label': 'Alice
            works at Google', 'type': 'world'}, {'id': '2', 'label': 'Bob went hiking', 'type': 'world'}], 'table_rows':
            [{'context': 'Work info', 'date': '2024-01-15 10:30', 'entities': 'Alice (PERSON), Google (ORGANIZATION)', 'id':
            'abc12345...', 'text': 'Alice works at Google'}], 'total_units': 2}

    Attributes:
        nodes (list[GraphDataResponseNodesItem]):
        edges (list[GraphDataResponseEdgesItem]):
        table_rows (list[GraphDataResponseTableRowsItem]):
        total_units (int):
    """

    nodes: list[GraphDataResponseNodesItem]
    edges: list[GraphDataResponseEdgesItem]
    table_rows: list[GraphDataResponseTableRowsItem]
    total_units: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        nodes = []
        for nodes_item_data in self.nodes:
            nodes_item = nodes_item_data.to_dict()
            nodes.append(nodes_item)

        edges = []
        for edges_item_data in self.edges:
            edges_item = edges_item_data.to_dict()
            edges.append(edges_item)

        table_rows = []
        for table_rows_item_data in self.table_rows:
            table_rows_item = table_rows_item_data.to_dict()
            table_rows.append(table_rows_item)

        total_units = self.total_units

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "nodes": nodes,
                "edges": edges,
                "table_rows": table_rows,
                "total_units": total_units,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.graph_data_response_edges_item import GraphDataResponseEdgesItem
        from ..models.graph_data_response_nodes_item import GraphDataResponseNodesItem
        from ..models.graph_data_response_table_rows_item import GraphDataResponseTableRowsItem

        d = dict(src_dict)
        nodes = []
        _nodes = d.pop("nodes")
        for nodes_item_data in _nodes:
            nodes_item = GraphDataResponseNodesItem.from_dict(nodes_item_data)

            nodes.append(nodes_item)

        edges = []
        _edges = d.pop("edges")
        for edges_item_data in _edges:
            edges_item = GraphDataResponseEdgesItem.from_dict(edges_item_data)

            edges.append(edges_item)

        table_rows = []
        _table_rows = d.pop("table_rows")
        for table_rows_item_data in _table_rows:
            table_rows_item = GraphDataResponseTableRowsItem.from_dict(table_rows_item_data)

            table_rows.append(table_rows_item)

        total_units = d.pop("total_units")

        graph_data_response = cls(
            nodes=nodes,
            edges=edges,
            table_rows=table_rows,
            total_units=total_units,
        )

        graph_data_response.additional_properties = d
        return graph_data_response

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
