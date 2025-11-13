from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.think_request import ThinkRequest
from ...models.think_response import ThinkResponse
from ...types import Response


def _get_kwargs(
    agent_id: str,
    *,
    body: ThinkRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": f"/api/v1/agents/{agent_id}/think",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | ThinkResponse | None:
    if response.status_code == 200:
        response_200 = ThinkResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | ThinkResponse]:
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
    body: ThinkRequest,
) -> Response[HTTPValidationError | ThinkResponse]:
    """Think and generate answer

     Think and formulate an answer using agent identity, world facts, and opinions.

        This endpoint:
        1. Retrieves agent facts (agent's identity)
        2. Retrieves world facts relevant to the query
        3. Retrieves existing opinions (agent's perspectives)
        4. Uses LLM to formulate a contextual answer
        5. Extracts and stores any new opinions formed
        6. Returns plain text answer, the facts used, and new opinions

    Args:
        agent_id (str):
        body (ThinkRequest): Request model for think endpoint. Example: {'context': 'This is for a
            research paper on AI ethics', 'query': 'What do you think about artificial intelligence?',
            'thinking_budget': 50}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ThinkResponse]
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
    body: ThinkRequest,
) -> HTTPValidationError | ThinkResponse | None:
    """Think and generate answer

     Think and formulate an answer using agent identity, world facts, and opinions.

        This endpoint:
        1. Retrieves agent facts (agent's identity)
        2. Retrieves world facts relevant to the query
        3. Retrieves existing opinions (agent's perspectives)
        4. Uses LLM to formulate a contextual answer
        5. Extracts and stores any new opinions formed
        6. Returns plain text answer, the facts used, and new opinions

    Args:
        agent_id (str):
        body (ThinkRequest): Request model for think endpoint. Example: {'context': 'This is for a
            research paper on AI ethics', 'query': 'What do you think about artificial intelligence?',
            'thinking_budget': 50}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ThinkResponse
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
    body: ThinkRequest,
) -> Response[HTTPValidationError | ThinkResponse]:
    """Think and generate answer

     Think and formulate an answer using agent identity, world facts, and opinions.

        This endpoint:
        1. Retrieves agent facts (agent's identity)
        2. Retrieves world facts relevant to the query
        3. Retrieves existing opinions (agent's perspectives)
        4. Uses LLM to formulate a contextual answer
        5. Extracts and stores any new opinions formed
        6. Returns plain text answer, the facts used, and new opinions

    Args:
        agent_id (str):
        body (ThinkRequest): Request model for think endpoint. Example: {'context': 'This is for a
            research paper on AI ethics', 'query': 'What do you think about artificial intelligence?',
            'thinking_budget': 50}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ThinkResponse]
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
    body: ThinkRequest,
) -> HTTPValidationError | ThinkResponse | None:
    """Think and generate answer

     Think and formulate an answer using agent identity, world facts, and opinions.

        This endpoint:
        1. Retrieves agent facts (agent's identity)
        2. Retrieves world facts relevant to the query
        3. Retrieves existing opinions (agent's perspectives)
        4. Uses LLM to formulate a contextual answer
        5. Extracts and stores any new opinions formed
        6. Returns plain text answer, the facts used, and new opinions

    Args:
        agent_id (str):
        body (ThinkRequest): Request model for think endpoint. Example: {'context': 'This is for a
            research paper on AI ethics', 'query': 'What do you think about artificial intelligence?',
            'thinking_budget': 50}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ThinkResponse
    """

    return (
        await asyncio_detailed(
            agent_id=agent_id,
            client=client,
            body=body,
        )
    ).parsed
