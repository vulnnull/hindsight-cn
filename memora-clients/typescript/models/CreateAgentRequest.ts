/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { PersonalityTraits } from './PersonalityTraits';
/**
 * Request model for creating/updating an agent.
 */
export type CreateAgentRequest = {
    personality?: (PersonalityTraits | null);
    background?: (string | null);
};

