from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.list_memory_units_response import ListMemoryUnitsResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    agent_id: str,
    *,
    fact_type: None | str | Unset = UNSET,
    q: None | str | Unset = UNSET,
    limit: int | Unset = 100,
    offset: int | Unset = 0,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_fact_type: None | str | Unset
    if isinstance(fact_type, Unset):
        json_fact_type = UNSET
    else:
        json_fact_type = fact_type
    params["fact_type"] = json_fact_type

    json_q: None | str | Unset
    if isinstance(q, Unset):
        json_q = UNSET
    else:
        json_q = q
    params["q"] = json_q

    params["limit"] = limit

    params["offset"] = offset

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/api/v1/agents/{agent_id}/memories/list",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | ListMemoryUnitsResponse | None:
    if response.status_code == 200:
        response_200 = ListMemoryUnitsResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | ListMemoryUnitsResponse]:
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
    q: None | str | Unset = UNSET,
    limit: int | Unset = 100,
    offset: int | Unset = 0,
) -> Response[HTTPValidationError | ListMemoryUnitsResponse]:
    """List memory units

     List memory units with pagination and optional full-text search. Supports filtering by fact_type.

    Args:
        agent_id (str):
        fact_type (None | str | Unset):
        q (None | str | Unset):
        limit (int | Unset):  Default: 100.
        offset (int | Unset):  Default: 0.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ListMemoryUnitsResponse]
    """

    kwargs = _get_kwargs(
        agent_id=agent_id,
        fact_type=fact_type,
        q=q,
        limit=limit,
        offset=offset,
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
    q: None | str | Unset = UNSET,
    limit: int | Unset = 100,
    offset: int | Unset = 0,
) -> HTTPValidationError | ListMemoryUnitsResponse | None:
    """List memory units

     List memory units with pagination and optional full-text search. Supports filtering by fact_type.

    Args:
        agent_id (str):
        fact_type (None | str | Unset):
        q (None | str | Unset):
        limit (int | Unset):  Default: 100.
        offset (int | Unset):  Default: 0.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ListMemoryUnitsResponse
    """

    return sync_detailed(
        agent_id=agent_id,
        client=client,
        fact_type=fact_type,
        q=q,
        limit=limit,
        offset=offset,
    ).parsed


async def asyncio_detailed(
    agent_id: str,
    *,
    client: AuthenticatedClient | Client,
    fact_type: None | str | Unset = UNSET,
    q: None | str | Unset = UNSET,
    limit: int | Unset = 100,
    offset: int | Unset = 0,
) -> Response[HTTPValidationError | ListMemoryUnitsResponse]:
    """List memory units

     List memory units with pagination and optional full-text search. Supports filtering by fact_type.

    Args:
        agent_id (str):
        fact_type (None | str | Unset):
        q (None | str | Unset):
        limit (int | Unset):  Default: 100.
        offset (int | Unset):  Default: 0.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ListMemoryUnitsResponse]
    """

    kwargs = _get_kwargs(
        agent_id=agent_id,
        fact_type=fact_type,
        q=q,
        limit=limit,
        offset=offset,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    agent_id: str,
    *,
    client: AuthenticatedClient | Client,
    fact_type: None | str | Unset = UNSET,
    q: None | str | Unset = UNSET,
    limit: int | Unset = 100,
    offset: int | Unset = 0,
) -> HTTPValidationError | ListMemoryUnitsResponse | None:
    """List memory units

     List memory units with pagination and optional full-text search. Supports filtering by fact_type.

    Args:
        agent_id (str):
        fact_type (None | str | Unset):
        q (None | str | Unset):
        limit (int | Unset):  Default: 100.
        offset (int | Unset):  Default: 0.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ListMemoryUnitsResponse
    """

    return (
        await asyncio_detailed(
            agent_id=agent_id,
            client=client,
            fact_type=fact_type,
            q=q,
            limit=limit,
            offset=offset,
        )
    ).parsed
