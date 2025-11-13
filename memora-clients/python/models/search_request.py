from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="SearchRequest")


@_attrs_define
class SearchRequest:
    """Request model for search endpoint.

    Example:
        {'fact_type': ['world', 'agent'], 'max_tokens': 4096, 'query': 'What did Alice say about machine learning?',
            'question_date': '2023-05-30T23:40:00', 'reranker': 'heuristic', 'thinking_budget': 100, 'trace': True}

    Attributes:
        query (str):
        fact_type (list[str] | None | Unset):
        thinking_budget (int | Unset):  Default: 100.
        max_tokens (int | Unset):  Default: 4096.
        reranker (str | Unset):  Default: 'heuristic'.
        trace (bool | Unset):  Default: False.
        question_date (None | str | Unset):
    """

    query: str
    fact_type: list[str] | None | Unset = UNSET
    thinking_budget: int | Unset = 100
    max_tokens: int | Unset = 4096
    reranker: str | Unset = "heuristic"
    trace: bool | Unset = False
    question_date: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        query = self.query

        fact_type: list[str] | None | Unset
        if isinstance(self.fact_type, Unset):
            fact_type = UNSET
        elif isinstance(self.fact_type, list):
            fact_type = self.fact_type

        else:
            fact_type = self.fact_type

        thinking_budget = self.thinking_budget

        max_tokens = self.max_tokens

        reranker = self.reranker

        trace = self.trace

        question_date: None | str | Unset
        if isinstance(self.question_date, Unset):
            question_date = UNSET
        else:
            question_date = self.question_date

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "query": query,
            }
        )
        if fact_type is not UNSET:
            field_dict["fact_type"] = fact_type
        if thinking_budget is not UNSET:
            field_dict["thinking_budget"] = thinking_budget
        if max_tokens is not UNSET:
            field_dict["max_tokens"] = max_tokens
        if reranker is not UNSET:
            field_dict["reranker"] = reranker
        if trace is not UNSET:
            field_dict["trace"] = trace
        if question_date is not UNSET:
            field_dict["question_date"] = question_date

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        query = d.pop("query")

        def _parse_fact_type(data: object) -> list[str] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                fact_type_type_0 = cast(list[str], data)

                return fact_type_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None | Unset, data)

        fact_type = _parse_fact_type(d.pop("fact_type", UNSET))

        thinking_budget = d.pop("thinking_budget", UNSET)

        max_tokens = d.pop("max_tokens", UNSET)

        reranker = d.pop("reranker", UNSET)

        trace = d.pop("trace", UNSET)

        def _parse_question_date(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        question_date = _parse_question_date(d.pop("question_date", UNSET))

        search_request = cls(
            query=query,
            fact_type=fact_type,
            thinking_budget=thinking_budget,
            max_tokens=max_tokens,
            reranker=reranker,
            trace=trace,
            question_date=question_date,
        )

        search_request.additional_properties = d
        return search_request

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
