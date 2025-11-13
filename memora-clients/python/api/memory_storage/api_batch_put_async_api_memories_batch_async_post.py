from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.batch_put_async_response import BatchPutAsyncResponse
from ...models.batch_put_request import BatchPutRequest
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


def _get_kwargs(
    *,
    body: BatchPutRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/memories/batch_async",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> BatchPutAsyncResponse | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = BatchPutAsyncResponse.from_dict(response.json())

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
) -> Response[BatchPutAsyncResponse | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: BatchPutRequest,
) -> Response[BatchPutAsyncResponse | HTTPValidationError]:
    """Store multiple memories asynchronously

     Store multiple memory items in batch asynchronously using the task backend.

        This endpoint returns immediately after queuing the task, without waiting for completion.
        The actual processing happens in the background.

        Features:
        - Immediate response (non-blocking)
        - Background processing via task queue
        - Efficient batch processing
        - Automatic fact extraction from natural language
        - Entity recognition and linking
        - Document tracking with automatic upsert (when document_id is provided)
        - Temporal and semantic linking

        The system automatically:
        1. Queues the batch put task
        2. Returns immediately with success=True, queued=True
        3. Processes in background: extracts facts, generates embeddings, creates links

        Note: If document_id is provided and already exists, the old document and its memory units will
    be deleted before creating new ones (upsert behavior).

    Args:
        body (BatchPutRequest): Request model for batch put endpoint. Example: {'agent_id':
            'user123', 'document_id': 'conversation_123', 'items': [{'content': 'Alice works at
            Google', 'context': 'work'}, {'content': 'Bob went hiking yesterday', 'event_date':
            '2024-01-15T10:00:00Z'}]}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[BatchPutAsyncResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: BatchPutRequest,
) -> BatchPutAsyncResponse | HTTPValidationError | None:
    """Store multiple memories asynchronously

     Store multiple memory items in batch asynchronously using the task backend.

        This endpoint returns immediately after queuing the task, without waiting for completion.
        The actual processing happens in the background.

        Features:
        - Immediate response (non-blocking)
        - Background processing via task queue
        - Efficient batch processing
        - Automatic fact extraction from natural language
        - Entity recognition and linking
        - Document tracking with automatic upsert (when document_id is provided)
        - Temporal and semantic linking

        The system automatically:
        1. Queues the batch put task
        2. Returns immediately with success=True, queued=True
        3. Processes in background: extracts facts, generates embeddings, creates links

        Note: If document_id is provided and already exists, the old document and its memory units will
    be deleted before creating new ones (upsert behavior).

    Args:
        body (BatchPutRequest): Request model for batch put endpoint. Example: {'agent_id':
            'user123', 'document_id': 'conversation_123', 'items': [{'content': 'Alice works at
            Google', 'context': 'work'}, {'content': 'Bob went hiking yesterday', 'event_date':
            '2024-01-15T10:00:00Z'}]}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        BatchPutAsyncResponse | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: BatchPutRequest,
) -> Response[BatchPutAsyncResponse | HTTPValidationError]:
    """Store multiple memories asynchronously

     Store multiple memory items in batch asynchronously using the task backend.

        This endpoint returns immediately after queuing the task, without waiting for completion.
        The actual processing happens in the background.

        Features:
        - Immediate response (non-blocking)
        - Background processing via task queue
        - Efficient batch processing
        - Automatic fact extraction from natural language
        - Entity recognition and linking
        - Document tracking with automatic upsert (when document_id is provided)
        - Temporal and semantic linking

        The system automatically:
        1. Queues the batch put task
        2. Returns immediately with success=True, queued=True
        3. Processes in background: extracts facts, generates embeddings, creates links

        Note: If document_id is provided and already exists, the old document and its memory units will
    be deleted before creating new ones (upsert behavior).

    Args:
        body (BatchPutRequest): Request model for batch put endpoint. Example: {'agent_id':
            'user123', 'document_id': 'conversation_123', 'items': [{'content': 'Alice works at
            Google', 'context': 'work'}, {'content': 'Bob went hiking yesterday', 'event_date':
            '2024-01-15T10:00:00Z'}]}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[BatchPutAsyncResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: BatchPutRequest,
) -> BatchPutAsyncResponse | HTTPValidationError | None:
    """Store multiple memories asynchronously

     Store multiple memory items in batch asynchronously using the task backend.

        This endpoint returns immediately after queuing the task, without waiting for completion.
        The actual processing happens in the background.

        Features:
        - Immediate response (non-blocking)
        - Background processing via task queue
        - Efficient batch processing
        - Automatic fact extraction from natural language
        - Entity recognition and linking
        - Document tracking with automatic upsert (when document_id is provided)
        - Temporal and semantic linking

        The system automatically:
        1. Queues the batch put task
        2. Returns immediately with success=True, queued=True
        3. Processes in background: extracts facts, generates embeddings, creates links

        Note: If document_id is provided and already exists, the old document and its memory units will
    be deleted before creating new ones (upsert behavior).

    Args:
        body (BatchPutRequest): Request model for batch put endpoint. Example: {'agent_id':
            'user123', 'document_id': 'conversation_123', 'items': [{'content': 'Alice works at
            Google', 'context': 'work'}, {'content': 'Bob went hiking yesterday', 'event_date':
            '2024-01-15T10:00:00Z'}]}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        BatchPutAsyncResponse | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
