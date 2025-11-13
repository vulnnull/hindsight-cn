from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.agent_profile_response import AgentProfileResponse
from ...models.http_validation_error import HTTPValidationError
from ...models.update_personality_request import UpdatePersonalityRequest
from ...types import Response


def _get_kwargs(
    agent_id: str,
    *,
    body: UpdatePersonalityRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "put",
        "url": f"/api/v1/agents/{agent_id}/profile",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> AgentProfileResponse | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = AgentProfileResponse.from_dict(response.json())

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
) -> Response[AgentProfileResponse | HTTPValidationError]:
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
    body: UpdatePersonalityRequest,
) -> Response[AgentProfileResponse | HTTPValidationError]:
    """Update agent personality

     Update agent's Big Five personality traits and bias strength

    Args:
        agent_id (str):
        body (UpdatePersonalityRequest): Request model for updating personality traits.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AgentProfileResponse | HTTPValidationError]
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
    body: UpdatePersonalityRequest,
) -> AgentProfileResponse | HTTPValidationError | None:
    """Update agent personality

     Update agent's Big Five personality traits and bias strength

    Args:
        agent_id (str):
        body (UpdatePersonalityRequest): Request model for updating personality traits.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AgentProfileResponse | HTTPValidationError
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
    body: UpdatePersonalityRequest,
) -> Response[AgentProfileResponse | HTTPValidationError]:
    """Update agent personality

     Update agent's Big Five personality traits and bias strength

    Args:
        agent_id (str):
        body (UpdatePersonalityRequest): Request model for updating personality traits.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AgentProfileResponse | HTTPValidationError]
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
    body: UpdatePersonalityRequest,
) -> AgentProfileResponse | HTTPValidationError | None:
    """Update agent personality

     Update agent's Big Five personality traits and bias strength

    Args:
        agent_id (str):
        body (UpdatePersonalityRequest): Request model for updating personality traits.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AgentProfileResponse | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            agent_id=agent_id,
            client=client,
            body=body,
        )
    ).parsed
