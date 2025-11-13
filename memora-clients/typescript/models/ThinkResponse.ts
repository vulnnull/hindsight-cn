/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ThinkFact } from './ThinkFact';
/**
 * Response model for think endpoint.
 */
export type ThinkResponse = {
    text: string;
    based_on?: Array<ThinkFact>;
    new_opinions?: Array<string>;
};

