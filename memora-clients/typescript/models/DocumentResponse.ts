/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Response model for get document endpoint.
 */
export type DocumentResponse = {
    id: string;
    agent_id: string;
    original_text: string;
    content_hash: (string | null);
    created_at: string;
    updated_at: string;
    memory_unit_count: number;
};

