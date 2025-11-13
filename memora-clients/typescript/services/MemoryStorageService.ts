/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { BatchPutAsyncResponse } from '../models/BatchPutAsyncResponse';
import type { BatchPutRequest } from '../models/BatchPutRequest';
import type { BatchPutResponse } from '../models/BatchPutResponse';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class MemoryStorageService {
    /**
     * Store multiple memories
     * Store multiple memory items in batch with automatic fact extraction.
     *
     * Features:
     * - Efficient batch processing
     * - Automatic fact extraction from natural language
     * - Entity recognition and linking
     * - Document tracking with automatic upsert (when document_id is provided)
     * - Temporal and semantic linking
     *
     * The system automatically:
     * 1. Extracts semantic facts from the content
     * 2. Generates embeddings
     * 3. Deduplicates similar facts
     * 4. Creates temporal, semantic, and entity links
     * 5. Tracks document metadata
     *
     * Note: If document_id is provided and already exists, the old document and its memory units will be deleted before creating new ones (upsert behavior).
     * @returns BatchPutResponse Successful Response
     * @throws ApiError
     */
    public static apiBatchPutApiMemoriesBatchPost({
        requestBody,
    }: {
        requestBody: BatchPutRequest,
    }): CancelablePromise<BatchPutResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/memories/batch',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Store multiple memories asynchronously
     * Store multiple memory items in batch asynchronously using the task backend.
     *
     * This endpoint returns immediately after queuing the task, without waiting for completion.
     * The actual processing happens in the background.
     *
     * Features:
     * - Immediate response (non-blocking)
     * - Background processing via task queue
     * - Efficient batch processing
     * - Automatic fact extraction from natural language
     * - Entity recognition and linking
     * - Document tracking with automatic upsert (when document_id is provided)
     * - Temporal and semantic linking
     *
     * The system automatically:
     * 1. Queues the batch put task
     * 2. Returns immediately with success=True, queued=True
     * 3. Processes in background: extracts facts, generates embeddings, creates links
     *
     * Note: If document_id is provided and already exists, the old document and its memory units will be deleted before creating new ones (upsert behavior).
     * @returns BatchPutAsyncResponse Successful Response
     * @throws ApiError
     */
    public static apiBatchPutAsyncApiMemoriesBatchAsyncPost({
        requestBody,
    }: {
        requestBody: BatchPutRequest,
    }): CancelablePromise<BatchPutAsyncResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/memories/batch_async',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List async operations
     * Get a list of all async operations (pending and failed) for a specific agent, including error messages for failed operations
     * @returns any Successful Response
     * @throws ApiError
     */
    public static apiListOperationsApiOperationsAgentIdGet({
        agentId,
    }: {
        agentId: string,
    }): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/operations/{agent_id}',
            path: {
                'agent_id': agentId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Cancel a pending async operation
     * Cancel a pending async operation by removing it from the queue
     * @returns any Successful Response
     * @throws ApiError
     */
    public static apiCancelOperationApiOperationsOperationIdDelete({
        operationId,
    }: {
        operationId: string,
    }): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/operations/{operation_id}',
            path: {
                'operation_id': operationId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Delete a memory unit
     * Delete a single memory unit and all its associated links (temporal, semantic, and entity links)
     * @returns any Successful Response
     * @throws ApiError
     */
    public static apiDeleteMemoryUnitApiMemoryUnitIdDelete({
        unitId,
    }: {
        unitId: string,
    }): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/memory/{unit_id}',
            path: {
                'unit_id': unitId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
