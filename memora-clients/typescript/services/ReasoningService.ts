/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ThinkRequest } from '../models/ThinkRequest';
import type { ThinkResponse } from '../models/ThinkResponse';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class ReasoningService {
    /**
     * Think and generate answer
     * Think and formulate an answer using agent identity, world facts, and opinions.
     *
     * This endpoint:
     * 1. Retrieves agent facts (agent's identity)
     * 2. Retrieves world facts relevant to the query
     * 3. Retrieves existing opinions (agent's perspectives)
     * 4. Uses LLM to formulate a contextual answer
     * 5. Extracts and stores any new opinions formed
     * 6. Returns plain text answer, the facts used, and new opinions
     * @returns ThinkResponse Successful Response
     * @throws ApiError
     */
    public static think({
        agentId,
        requestBody,
    }: {
        agentId: string,
        requestBody: ThinkRequest,
    }): CancelablePromise<ThinkResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/agents/{agent_id}/think',
            path: {
                'agent_id': agentId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
