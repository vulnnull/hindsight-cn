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
export class AgentProfileService {
    /**
     * List all agents
     * Get a list of all agents with their profiles
     * @returns AgentListResponse Successful Response
     * @throws ApiError
     */
    public static apiListAgentsApiAgentsGet(): CancelablePromise<AgentListResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/agents',
        });
    }
    /**
     * Get agent profile
     * Get personality traits and background for an agent. Auto-creates agent with defaults if not exists.
     * @returns AgentProfileResponse Successful Response
     * @throws ApiError
     */
    public static apiGetAgentProfileApiAgentsAgentIdProfileGet({
        agentId,
    }: {
        agentId: string,
    }): CancelablePromise<AgentProfileResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/agents/{agent_id}/profile',
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
    public static apiUpdateAgentPersonalityApiAgentsAgentIdProfilePut({
        agentId,
        requestBody,
    }: {
        agentId: string,
        requestBody: UpdatePersonalityRequest,
    }): CancelablePromise<AgentProfileResponse> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/api/agents/{agent_id}/profile',
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
    public static apiAddAgentBackgroundApiAgentsAgentIdBackgroundPost({
        agentId,
        requestBody,
    }: {
        agentId: string,
        requestBody: AddBackgroundRequest,
    }): CancelablePromise<BackgroundResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/agents/{agent_id}/background',
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
    public static apiCreateOrUpdateAgentApiAgentsAgentIdPut({
        agentId,
        requestBody,
    }: {
        agentId: string,
        requestBody: CreateAgentRequest,
    }): CancelablePromise<AgentProfileResponse> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/api/agents/{agent_id}',
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
