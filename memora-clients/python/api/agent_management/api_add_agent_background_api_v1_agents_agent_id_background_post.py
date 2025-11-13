from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.add_background_request import AddBackgroundRequest
from ...models.background_response import BackgroundResponse
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


def _get_kwargs(
    agent_id: str,
    *,
    body: AddBackgroundRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": f"/api/v1/agents/{agent_id}/background",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> BackgroundResponse | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = BackgroundResponse.from_dict(response.json())

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
) -> Response[BackgroundResponse | HTTPValidationError]:
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
    body: AddBackgroundRequest,
) -> Response[BackgroundResponse | HTTPValidationError]:
    """Add/merge agent background

     Add new background information or merge with existing. LLM intelligently resolves conflicts,
    normalizes to first person, and optionally infers personality traits.

    Args:
        agent_id (str):
        body (AddBackgroundRequest): Request model for adding/merging background information.
            Example: {'content': 'I was born in Texas', 'update_personality': True}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[BackgroundResponse | HTTPValidationError]
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
    body: AddBackgroundRequest,
) -> BackgroundResponse | HTTPValidationError | None:
    """Add/merge agent background

     Add new background information or merge with existing. LLM intelligently resolves conflicts,
    normalizes to first person, and optionally infers personality traits.

    Args:
        agent_id (str):
        body (AddBackgroundRequest): Request model for adding/merging background information.
            Example: {'content': 'I was born in Texas', 'update_personality': True}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        BackgroundResponse | HTTPValidationError
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
    body: AddBackgroundRequest,
) -> Response[BackgroundResponse | HTTPValidationError]:
    """Add/merge agent background

     Add new background information or merge with existing. LLM intelligently resolves conflicts,
    normalizes to first person, and optionally infers personality traits.

    Args:
        agent_id (str):
        body (AddBackgroundRequest): Request model for adding/merging background information.
            Example: {'content': 'I was born in Texas', 'update_personality': True}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[BackgroundResponse | HTTPValidationError]
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
    body: AddBackgroundRequest,
) -> BackgroundResponse | HTTPValidationError | None:
    """Add/merge agent background

     Add new background information or merge with existing. LLM intelligently resolves conflicts,
    normalizes to first person, and optionally infers personality traits.

    Args:
        agent_id (str):
        body (AddBackgroundRequest): Request model for adding/merging background information.
            Example: {'content': 'I was born in Texas', 'update_personality': True}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        BackgroundResponse | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            agent_id=agent_id,
            client=client,
            body=body,
        )
    ).parsed
