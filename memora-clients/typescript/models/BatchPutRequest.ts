/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { MemoryItem } from './MemoryItem';
/**
 * Request model for batch put endpoint.
 */
export type BatchPutRequest = {
    items: Array<MemoryItem>;
    document_id?: (string | null);
};

