/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { SearchRequest } from '../models/SearchRequest';
import type { SearchResponse } from '../models/SearchResponse';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class SearchService {
    /**
     * Search memory
     * Search memory using semantic similarity and spreading activation.
     *
     * The fact_type parameter is required and must be one of:
     * - 'world': General knowledge about people, places, events, and things that happen
     * - 'agent': Memories about what the AI agent did, actions taken, and tasks performed
     * - 'opinion': The agent's formed beliefs, perspectives, and viewpoints
     * @returns SearchResponse Successful Response
     * @throws ApiError
     */
    public static apiSearchApiSearchPost({
        requestBody,
    }: {
        requestBody: SearchRequest,
    }): CancelablePromise<SearchResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/search',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
