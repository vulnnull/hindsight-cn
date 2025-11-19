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
    thinking_budget?: number;
    max_tokens?: number;
    trace?: boolean;
    question_date?: (string | null);
};

