from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.search_response_trace_type_0 import SearchResponseTraceType0
    from ..models.search_result import SearchResult


T = TypeVar("T", bound="SearchResponse")


@_attrs_define
class SearchResponse:
    """Response model for search endpoints.

    Example:
        {'results': [{'activation': 0.95, 'context': 'work info', 'event_date': '2024-01-15T10:30:00Z', 'id':
            '123e4567-e89b-12d3-a456-426614174000', 'text': 'Alice works at Google on the AI team', 'type': 'world'}],
            'trace': {'num_results': 1, 'query': 'What did Alice say about machine learning?', 'time_seconds': 0.123}}

    Attributes:
        results (list[SearchResult]):
        trace (None | SearchResponseTraceType0 | Unset):
    """

    results: list[SearchResult]
    trace: None | SearchResponseTraceType0 | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.search_response_trace_type_0 import SearchResponseTraceType0

        results = []
        for results_item_data in self.results:
            results_item = results_item_data.to_dict()
            results.append(results_item)

        trace: dict[str, Any] | None | Unset
        if isinstance(self.trace, Unset):
            trace = UNSET
        elif isinstance(self.trace, SearchResponseTraceType0):
            trace = self.trace.to_dict()
        else:
            trace = self.trace

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "results": results,
            }
        )
        if trace is not UNSET:
            field_dict["trace"] = trace

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.search_response_trace_type_0 import SearchResponseTraceType0
        from ..models.search_result import SearchResult

        d = dict(src_dict)
        results = []
        _results = d.pop("results")
        for results_item_data in _results:
            results_item = SearchResult.from_dict(results_item_data)

            results.append(results_item)

        def _parse_trace(data: object) -> None | SearchResponseTraceType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                trace_type_0 = SearchResponseTraceType0.from_dict(data)

                return trace_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | SearchResponseTraceType0 | Unset, data)

        trace = _parse_trace(d.pop("trace", UNSET))

        search_response = cls(
            results=results,
            trace=trace,
        )

        search_response.additional_properties = d
        return search_response

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
