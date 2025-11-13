/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { DocumentResponse } from '../models/DocumentResponse';
import type { ListDocumentsResponse } from '../models/ListDocumentsResponse';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class DocumentsService {
    /**
     * List documents
     * List documents with pagination and optional search. Documents are the source content from which memory units are extracted.
     * @returns ListDocumentsResponse Successful Response
     * @throws ApiError
     */
    public static apiListDocumentsApiV1AgentsAgentIdDocumentsGet({
        agentId,
        q,
        limit = 100,
        offset,
    }: {
        agentId: string,
        q?: (string | null),
        limit?: number,
        offset?: number,
    }): CancelablePromise<ListDocumentsResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/agents/{agent_id}/documents',
            path: {
                'agent_id': agentId,
            },
            query: {
                'q': q,
                'limit': limit,
                'offset': offset,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get document details
     * Get a specific document including its original text
     * @returns DocumentResponse Successful Response
     * @throws ApiError
     */
    public static apiGetDocumentApiV1AgentsAgentIdDocumentsDocumentIdGet({
        agentId,
        documentId,
    }: {
        agentId: string,
        documentId: string,
    }): CancelablePromise<DocumentResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/agents/{agent_id}/documents/{document_id}',
            path: {
                'agent_id': agentId,
                'document_id': documentId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
