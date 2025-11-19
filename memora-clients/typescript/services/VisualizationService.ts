/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { GraphDataResponse } from '../models/GraphDataResponse';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class VisualizationService {
    /**
     * Get memory graph data
     * Retrieve graph data for visualization, optionally filtered by fact_type (world/agent/opinion). Limited to 1000 most recent items.
     * @returns GraphDataResponse Successful Response
     * @throws ApiError
     */
    public static getGraph({
        agentId,
        factType,
    }: {
        agentId: string,
        factType?: (string | null),
    }): CancelablePromise<GraphDataResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/agents/{agent_id}/graph',
            path: {
                'agent_id': agentId,
            },
            query: {
                'fact_type': factType,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
