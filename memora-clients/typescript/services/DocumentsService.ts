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
    public static apiListDocumentsApiDocumentsGet({
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
            url: '/api/documents',
            query: {
                'agent_id': agentId,
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
    public static apiGetDocumentApiDocumentsDocumentIdGet({
        documentId,
        agentId,
    }: {
        documentId: string,
        agentId: string,
    }): CancelablePromise<DocumentResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/documents/{document_id}',
            path: {
                'document_id': documentId,
            },
            query: {
                'agent_id': agentId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
