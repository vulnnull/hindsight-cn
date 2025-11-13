/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { AddBackgroundRequest } from '../models/AddBackgroundRequest';
import type { AgentListResponse } from '../models/AgentListResponse';
import type { AgentProfileResponse } from '../models/AgentProfileResponse';
import type { BackgroundResponse } from '../models/BackgroundResponse';
import type { CreateAgentRequest } from '../models/CreateAgentRequest';
import type { UpdatePersonalityRequest } from '../models/UpdatePersonalityRequest';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class AgentManagementService {
    /**
     * List all agents
     * Get a list of all agents with their profiles
     * @returns AgentListResponse Successful Response
     * @throws ApiError
     */
    public static apiAgentsApiV1AgentsGet(): CancelablePromise<AgentListResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/agents',
        });
    }
    /**
     * Get memory statistics for an agent
     * Get statistics about nodes and links for a specific agent
     * @returns any Successful Response
     * @throws ApiError
     */
    public static apiStatsApiV1AgentsAgentIdStatsGet({
        agentId,
    }: {
        agentId: string,
    }): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/agents/{agent_id}/stats',
            path: {
                'agent_id': agentId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get agent profile
     * Get personality traits and background for an agent. Auto-creates agent with defaults if not exists.
     * @returns AgentProfileResponse Successful Response
     * @throws ApiError
     */
    public static apiGetAgentProfileApiV1AgentsAgentIdProfileGet({
        agentId,
    }: {
        agentId: string,
    }): CancelablePromise<AgentProfileResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/agents/{agent_id}/profile',
            path: {
                'agent_id': agentId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update agent personality
     * Update agent's Big Five personality traits and bias strength
     * @returns AgentProfileResponse Successful Response
     * @throws ApiError
     */
    public static apiUpdateAgentPersonalityApiV1AgentsAgentIdProfilePut({
        agentId,
        requestBody,
    }: {
        agentId: string,
        requestBody: UpdatePersonalityRequest,
    }): CancelablePromise<AgentProfileResponse> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/api/v1/agents/{agent_id}/profile',
            path: {
                'agent_id': agentId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Add/merge agent background
     * Add new background information or merge with existing. LLM intelligently resolves conflicts, normalizes to first person, and optionally infers personality traits.
     * @returns BackgroundResponse Successful Response
     * @throws ApiError
     */
    public static apiAddAgentBackgroundApiV1AgentsAgentIdBackgroundPost({
        agentId,
        requestBody,
    }: {
        agentId: string,
        requestBody: AddBackgroundRequest,
    }): CancelablePromise<BackgroundResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/agents/{agent_id}/background',
            path: {
                'agent_id': agentId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create or update agent
     * Create a new agent or update existing agent with personality and background. Auto-fills missing fields with defaults.
     * @returns AgentProfileResponse Successful Response
     * @throws ApiError
     */
    public static apiCreateOrUpdateAgentApiV1AgentsAgentIdPut({
        agentId,
        requestBody,
    }: {
        agentId: string,
        requestBody: CreateAgentRequest,
    }): CancelablePromise<AgentProfileResponse> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/api/v1/agents/{agent_id}',
            path: {
                'agent_id': agentId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
