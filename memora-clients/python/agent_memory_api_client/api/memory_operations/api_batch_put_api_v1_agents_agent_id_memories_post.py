from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.batch_put_request import BatchPutRequest
from ...models.batch_put_response import BatchPutResponse
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


def _get_kwargs(
    agent_id: str,
    *,
    body: BatchPutRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": f"/api/v1/agents/{agent_id}/memories",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> BatchPutResponse | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = BatchPutResponse.from_dict(response.json())

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
) -> Response[BatchPutResponse | HTTPValidationError]:
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
    body: BatchPutRequest,
) -> Response[BatchPutResponse | HTTPValidationError]:
    """Store multiple memories

     Store multiple memory items in batch with automatic fact extraction.

        Features:
        - Efficient batch processing
        - Automatic fact extraction from natural language
        - Entity recognition and linking
        - Document tracking with automatic upsert (when document_id is provided)
        - Temporal and semantic linking

        The system automatically:
        1. Extracts semantic facts from the content
        2. Generates embeddings
        3. Deduplicates similar facts
        4. Creates temporal, semantic, and entity links
        5. Tracks document metadata

        Note: If document_id is provided and already exists, the old document and its memory units will
    be deleted before creating new ones (upsert behavior).

    Args:
        agent_id (str):
        body (BatchPutRequest): Request model for batch put endpoint. Example: {'document_id':
            'conversation_123', 'items': [{'content': 'Alice works at Google', 'context': 'work'},
            {'content': 'Bob went hiking yesterday', 'event_date': '2024-01-15T10:00:00Z'}]}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[BatchPutResponse | HTTPValidationError]
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
    body: BatchPutRequest,
) -> BatchPutResponse | HTTPValidationError | None:
    """Store multiple memories

     Store multiple memory items in batch with automatic fact extraction.

        Features:
        - Efficient batch processing
        - Automatic fact extraction from natural language
        - Entity recognition and linking
        - Document tracking with automatic upsert (when document_id is provided)
        - Temporal and semantic linking

        The system automatically:
        1. Extracts semantic facts from the content
        2. Generates embeddings
        3. Deduplicates similar facts
        4. Creates temporal, semantic, and entity links
        5. Tracks document metadata

        Note: If document_id is provided and already exists, the old document and its memory units will
    be deleted before creating new ones (upsert behavior).

    Args:
        agent_id (str):
        body (BatchPutRequest): Request model for batch put endpoint. Example: {'document_id':
            'conversation_123', 'items': [{'content': 'Alice works at Google', 'context': 'work'},
            {'content': 'Bob went hiking yesterday', 'event_date': '2024-01-15T10:00:00Z'}]}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        BatchPutResponse | HTTPValidationError
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
    body: BatchPutRequest,
) -> Response[BatchPutResponse | HTTPValidationError]:
    """Store multiple memories

     Store multiple memory items in batch with automatic fact extraction.

        Features:
        - Efficient batch processing
        - Automatic fact extraction from natural language
        - Entity recognition and linking
        - Document tracking with automatic upsert (when document_id is provided)
        - Temporal and semantic linking

        The system automatically:
        1. Extracts semantic facts from the content
        2. Generates embeddings
        3. Deduplicates similar facts
        4. Creates temporal, semantic, and entity links
        5. Tracks document metadata

        Note: If document_id is provided and already exists, the old document and its memory units will
    be deleted before creating new ones (upsert behavior).

    Args:
        agent_id (str):
        body (BatchPutRequest): Request model for batch put endpoint. Example: {'document_id':
            'conversation_123', 'items': [{'content': 'Alice works at Google', 'context': 'work'},
            {'content': 'Bob went hiking yesterday', 'event_date': '2024-01-15T10:00:00Z'}]}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[BatchPutResponse | HTTPValidationError]
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
    body: BatchPutRequest,
) -> BatchPutResponse | HTTPValidationError | None:
    """Store multiple memories

     Store multiple memory items in batch with automatic fact extraction.

        Features:
        - Efficient batch processing
        - Automatic fact extraction from natural language
        - Entity recognition and linking
        - Document tracking with automatic upsert (when document_id is provided)
        - Temporal and semantic linking

        The system automatically:
        1. Extracts semantic facts from the content
        2. Generates embeddings
        3. Deduplicates similar facts
        4. Creates temporal, semantic, and entity links
        5. Tracks document metadata

        Note: If document_id is provided and already exists, the old document and its memory units will
    be deleted before creating new ones (upsert behavior).

    Args:
        agent_id (str):
        body (BatchPutRequest): Request model for batch put endpoint. Example: {'document_id':
            'conversation_123', 'items': [{'content': 'Alice works at Google', 'context': 'work'},
            {'content': 'Bob went hiking yesterday', 'event_date': '2024-01-15T10:00:00Z'}]}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        BatchPutResponse | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            agent_id=agent_id,
            client=client,
            body=body,
        )
    ).parsed
