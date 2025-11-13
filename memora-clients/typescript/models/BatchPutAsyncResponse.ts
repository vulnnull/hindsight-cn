/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Response model for async batch put endpoint.
 */
export type BatchPutAsyncResponse = {
    success: boolean;
    message: string;
    agent_id: string;
    document_id?: (string | null);
    items_count: number;
    queued: boolean;
};

