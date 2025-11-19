/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { PersonalityTraits } from './PersonalityTraits';
/**
 * Agent list item with profile summary.
 */
export type AgentListItem = {
    agent_id: string;
    name: string;
    personality: PersonalityTraits;
    background: string;
    created_at?: (string | null);
    updated_at?: (string | null);
};

