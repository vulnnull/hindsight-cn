/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { GraphDataResponse } from '../models/GraphDataResponse';
import type { ListMemoryUnitsResponse } from '../models/ListMemoryUnitsResponse';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class VisualizationService {
    /**
     * Get memory graph data
     * Retrieve graph data for visualization, optionally filtered by agent_id and fact_type (world/agent/opinion). Limited to 1000 most recent items.
     * @returns GraphDataResponse Successful Response
     * @throws ApiError
     */
    public static apiGraphApiGraphGet({
        agentId,
        factType,
    }: {
        agentId?: (string | null),
        factType?: (string | null),
    }): CancelablePromise<GraphDataResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/graph',
            query: {
                'agent_id': agentId,
                'fact_type': factType,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List memory units
     * List memory units with pagination and optional full-text search. Supports filtering by agent_id and fact_type.
     * @returns ListMemoryUnitsResponse Successful Response
     * @throws ApiError
     */
    public static apiListApiListGet({
        agentId,
        factType,
        q,
        limit = 100,
        offset,
    }: {
        agentId?: (string | null),
        factType?: (string | null),
        q?: (string | null),
        limit?: number,
        offset?: number,
    }): CancelablePromise<ListMemoryUnitsResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/list',
            query: {
                'agent_id': agentId,
                'fact_type': factType,
                'q': q,
                'limit': limit,
                'offset': offset,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
