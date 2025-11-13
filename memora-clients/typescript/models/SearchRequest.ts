/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Request model for search endpoint.
 */
export type SearchRequest = {
    query: string;
    fact_type?: (Array<string> | null);
    agent_id?: string;
    thinking_budget?: number;
    max_tokens?: number;
    reranker?: string;
    trace?: boolean;
    question_date?: (string | null);
};

