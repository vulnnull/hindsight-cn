from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.document_response import DocumentResponse
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


def _get_kwargs(
    agent_id: str,
    document_id: str,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/api/v1/agents/{agent_id}/documents/{document_id}",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DocumentResponse | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = DocumentResponse.from_dict(response.json())

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
) -> Response[DocumentResponse | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    agent_id: str,
    document_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[DocumentResponse | HTTPValidationError]:
    """Get document details

     Get a specific document including its original text

    Args:
        agent_id (str):
        document_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DocumentResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        agent_id=agent_id,
        document_id=document_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    agent_id: str,
    document_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> DocumentResponse | HTTPValidationError | None:
    """Get document details

     Get a specific document including its original text

    Args:
        agent_id (str):
        document_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DocumentResponse | HTTPValidationError
    """

    return sync_detailed(
        agent_id=agent_id,
        document_id=document_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    agent_id: str,
    document_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[DocumentResponse | HTTPValidationError]:
    """Get document details

     Get a specific document including its original text

    Args:
        agent_id (str):
        document_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DocumentResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        agent_id=agent_id,
        document_id=document_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    agent_id: str,
    document_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> DocumentResponse | HTTPValidationError | None:
    """Get document details

     Get a specific document including its original text

    Args:
        agent_id (str):
        document_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DocumentResponse | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            agent_id=agent_id,
            document_id=document_id,
            client=client,
        )
    ).parsed
