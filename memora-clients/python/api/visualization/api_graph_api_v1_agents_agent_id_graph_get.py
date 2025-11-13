from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.graph_data_response import GraphDataResponse
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    agent_id: str,
    *,
    fact_type: None | str | Unset = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_fact_type: None | str | Unset
    if isinstance(fact_type, Unset):
        json_fact_type = UNSET
    else:
        json_fact_type = fact_type
    params["fact_type"] = json_fact_type

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/api/v1/agents/{agent_id}/graph",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> GraphDataResponse | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = GraphDataResponse.from_dict(response.json())

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
) -> Response[GraphDataResponse | HTTPValidationError]:
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
    fact_type: None | str | Unset = UNSET,
) -> Response[GraphDataResponse | HTTPValidationError]:
    """Get memory graph data

     Retrieve graph data for visualization, optionally filtered by fact_type (world/agent/opinion).
    Limited to 1000 most recent items.

    Args:
        agent_id (str):
        fact_type (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GraphDataResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        agent_id=agent_id,
        fact_type=fact_type,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    agent_id: str,
    *,
    client: AuthenticatedClient | Client,
    fact_type: None | str | Unset = UNSET,
) -> GraphDataResponse | HTTPValidationError | None:
    """Get memory graph data

     Retrieve graph data for visualization, optionally filtered by fact_type (world/agent/opinion).
    Limited to 1000 most recent items.

    Args:
        agent_id (str):
        fact_type (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GraphDataResponse | HTTPValidationError
    """

    return sync_detailed(
        agent_id=agent_id,
        client=client,
        fact_type=fact_type,
    ).parsed


async def asyncio_detailed(
    agent_id: str,
    *,
    client: AuthenticatedClient | Client,
    fact_type: None | str | Unset = UNSET,
) -> Response[GraphDataResponse | HTTPValidationError]:
    """Get memory graph data

     Retrieve graph data for visualization, optionally filtered by fact_type (world/agent/opinion).
    Limited to 1000 most recent items.

    Args:
        agent_id (str):
        fact_type (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GraphDataResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        agent_id=agent_id,
        fact_type=fact_type,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    agent_id: str,
    *,
    client: AuthenticatedClient | Client,
    fact_type: None | str | Unset = UNSET,
) -> GraphDataResponse | HTTPValidationError | None:
    """Get memory graph data

     Retrieve graph data for visualization, optionally filtered by fact_type (world/agent/opinion).
    Limited to 1000 most recent items.

    Args:
        agent_id (str):
        fact_type (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GraphDataResponse | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            agent_id=agent_id,
            client=client,
            fact_type=fact_type,
        )
    ).parsed
