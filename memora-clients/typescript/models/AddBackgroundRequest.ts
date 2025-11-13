/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Request model for adding/merging background information.
 */
export type AddBackgroundRequest = {
    /**
     * New background information to add or merge
     */
    content: string;
    /**
     * If true, infer Big Five personality traits from the merged background (default: true)
     */
    update_personality?: boolean;
};

