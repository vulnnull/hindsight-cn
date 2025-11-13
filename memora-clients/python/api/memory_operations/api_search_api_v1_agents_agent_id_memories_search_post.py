from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.search_request import SearchRequest
from ...models.search_response import SearchResponse
from ...types import Response


def _get_kwargs(
    agent_id: str,
    *,
    body: SearchRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": f"/api/v1/agents/{agent_id}/memories/search",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | SearchResponse | None:
    if response.status_code == 200:
        response_200 = SearchResponse.from_dict(response.json())

        return response_200

    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[HTTPValidationError | SearchResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    agent_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: SearchRequest,
) -> Response[HTTPValidationError | SearchResponse]:
    """Search memory

     Search memory using semantic similarity and spreading activation.

        The fact_type parameter is optional and must be one of:
        - 'world': General knowledge about people, places, events, and things that happen
        - 'agent': Memories about what the AI agent did, actions taken, and tasks performed
        - 'opinion': The agent's formed beliefs, perspectives, and viewpoints

    Args:
        agent_id (str):
        body (SearchRequest): Request model for search endpoint. Example: {'fact_type': ['world',
            'agent'], 'max_tokens': 4096, 'query': 'What did Alice say about machine learning?',
            'question_date': '2023-05-30T23:40:00', 'reranker': 'heuristic', 'thinking_budget': 100,
            'trace': True}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | SearchResponse]
    """

    kwargs = _get_kwargs(
        agent_id=agent_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    agent_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: SearchRequest,
) -> HTTPValidationError | SearchResponse | None:
    """Search memory

     Search memory using semantic similarity and spreading activation.

        The fact_type parameter is optional and must be one of:
        - 'world': General knowledge about people, places, events, and things that happen
        - 'agent': Memories about what the AI agent did, actions taken, and tasks performed
        - 'opinion': The agent's formed beliefs, perspectives, and viewpoints

    Args:
        agent_id (str):
        body (SearchRequest): Request model for search endpoint. Example: {'fact_type': ['world',
            'agent'], 'max_tokens': 4096, 'query': 'What did Alice say about machine learning?',
            'question_date': '2023-05-30T23:40:00', 'reranker': 'heuristic', 'thinking_budget': 100,
            'trace': True}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | SearchResponse
    """

    return sync_detailed(
        agent_id=agent_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    agent_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: SearchRequest,
) -> Response[HTTPValidationError | SearchResponse]:
    """Search memory

     Search memory using semantic similarity and spreading activation.

        The fact_type parameter is optional and must be one of:
        - 'world': General knowledge about people, places, events, and things that happen
        - 'agent': Memories about what the AI agent did, actions taken, and tasks performed
        - 'opinion': The agent's formed beliefs, perspectives, and viewpoints

    Args:
        agent_id (str):
        body (SearchRequest): Request model for search endpoint. Example: {'fact_type': ['world',
            'agent'], 'max_tokens': 4096, 'query': 'What did Alice say about machine learning?',
            'question_date': '2023-05-30T23:40:00', 'reranker': 'heuristic', 'thinking_budget': 100,
            'trace': True}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | SearchResponse]
    """

    kwargs = _get_kwargs(
        agent_id=agent_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    agent_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: SearchRequest,
) -> HTTPValidationError | SearchResponse | None:
    """Search memory

     Search memory using semantic similarity and spreading activation.

        The fact_type parameter is optional and must be one of:
        - 'world': General knowledge about people, places, events, and things that happen
        - 'agent': Memories about what the AI agent did, actions taken, and tasks performed
        - 'opinion': The agent's formed beliefs, perspectives, and viewpoints

    Args:
        agent_id (str):
        body (SearchRequest): Request model for search endpoint. Example: {'fact_type': ['world',
            'agent'], 'max_tokens': 4096, 'query': 'What did Alice say about machine learning?',
            'question_date': '2023-05-30T23:40:00', 'reranker': 'heuristic', 'thinking_budget': 100,
            'trace': True}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | SearchResponse
    """

    return (
        await asyncio_detailed(
            agent_id=agent_id,
            client=client,
            body=body,
        )
    ).parsed
