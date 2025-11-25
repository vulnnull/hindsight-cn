/**
 * Hindsight Client - Clean, TypeScript SDK for the Hindsight API.
 *
 * Example:
 * ```typescript
 * import { HindsightClient } from '@hindsight/client';
 *
 * const client = new HindsightClient({ baseUrl: 'http://localhost:8888' });
 *
 * // Store a memory
 * await client.put('alice', 'Alice loves AI');
 *
 * // Search memories
 * const results = await client.search('alice', 'What does Alice like?');
 *
 * // Generate contextual answer
 * const answer = await client.think('alice', 'What are my interests?');
 * ```
 */

import { createClient, createConfig } from '../generated/client';
import type { Client } from '../generated/client';
import * as sdk from '../generated/sdk.gen';
import type {
    BatchPutRequest,
    BatchPutResponse,
    SearchRequest,
    SearchResponse,
    SearchResult,
    ThinkRequest,
    ThinkResponse,
    ListMemoryUnitsResponse,
    AgentProfileResponse,
    CreateAgentRequest,
} from '../generated/types.gen';

export interface HindsightClientOptions {
    baseUrl: string;
}

export interface MemoryItemInput {
    content: string;
    event_date?: string | Date;
    context?: string;
}

export class HindsightClient {
    private client: Client;

    constructor(options: HindsightClientOptions) {
        this.client = createClient(
            createConfig({
                baseUrl: options.baseUrl,
            })
        );
    }

    /**
     * Store a single memory for an agent.
     */
    async put(
        agentId: string,
        content: string,
        options?: { eventDate?: Date | string; context?: string }
    ): Promise<BatchPutResponse> {
        const item: { content: string; event_date?: string; context?: string } = { content };
        if (options?.eventDate) {
            item.event_date =
                options.eventDate instanceof Date
                    ? options.eventDate.toISOString()
                    : options.eventDate;
        }
        if (options?.context) {
            item.context = options.context;
        }

        const response = await sdk.batchPutMemories({
            client: this.client,
            path: { agent_id: agentId },
            body: { items: [item] },
        });

        return response.data!;
    }

    /**
     * Store multiple memories in batch.
     */
    async putBatch(agentId: string, items: MemoryItemInput[]): Promise<BatchPutResponse> {
        const processedItems = items.map((item) => ({
            content: item.content,
            context: item.context,
            event_date:
                item.event_date instanceof Date
                    ? item.event_date.toISOString()
                    : item.event_date,
        }));

        const response = await sdk.batchPutMemories({
            client: this.client,
            path: { agent_id: agentId },
            body: { items: processedItems },
        });

        return response.data!;
    }

    /**
     * Search memories with a natural language query.
     * Returns a simplified list of search results.
     */
    async search(
        agentId: string,
        query: string,
        options?: { maxTokens?: number }
    ): Promise<SearchResult[]> {
        const response = await sdk.searchMemories({
            client: this.client,
            path: { agent_id: agentId },
            body: {
                query,
                max_tokens: options?.maxTokens,
            },
        });

        return response.data?.results ?? [];
    }

    /**
     * Search memories with full options and response.
     */
    async searchMemories(
        agentId: string,
        options: {
            query: string;
            factType?: string[];
            maxTokens?: number;
            trace?: boolean;
        }
    ): Promise<SearchResponse> {
        const response = await sdk.searchMemories({
            client: this.client,
            path: { agent_id: agentId },
            body: {
                query: options.query,
                fact_type: options.factType,
                max_tokens: options.maxTokens,
                trace: options.trace,
            },
        });

        return response.data!;
    }

    /**
     * Think and generate a contextual answer using the agent's identity and memories.
     */
    async think(
        agentId: string,
        query: string,
        options?: { context?: string; thinkingBudget?: number }
    ): Promise<ThinkResponse> {
        const response = await sdk.think({
            client: this.client,
            path: { agent_id: agentId },
            body: {
                query,
                context: options?.context,
                thinking_budget: options?.thinkingBudget,
            },
        });

        return response.data!;
    }

    /**
     * List memories with pagination.
     */
    async listMemories(
        agentId: string,
        options?: { limit?: number; offset?: number; factType?: string; q?: string }
    ): Promise<ListMemoryUnitsResponse> {
        const response = await sdk.listMemories({
            client: this.client,
            path: { agent_id: agentId },
            query: {
                limit: options?.limit,
                offset: options?.offset,
                fact_type: options?.factType,
                q: options?.q,
            },
        });

        return response.data!;
    }

    /**
     * Create or update an agent with personality and background.
     */
    async createAgent(
        agentId: string,
        options: { name?: string; background?: string }
    ): Promise<AgentProfileResponse> {
        const response = await sdk.createOrUpdateAgent({
            client: this.client,
            path: { agent_id: agentId },
            body: {
                name: options.name,
                background: options.background,
            },
        });

        return response.data!;
    }

    /**
     * Get an agent's profile.
     */
    async getAgentProfile(agentId: string): Promise<AgentProfileResponse> {
        const response = await sdk.getAgentProfile({
            client: this.client,
            path: { agent_id: agentId },
        });

        return response.data!;
    }
}

// Re-export types for convenience
export type {
    BatchPutRequest,
    BatchPutResponse,
    SearchRequest,
    SearchResponse,
    SearchResult,
    ThinkRequest,
    ThinkResponse,
    ListMemoryUnitsResponse,
    AgentProfileResponse,
    CreateAgentRequest,
};

// Also export low-level SDK functions for advanced usage
export * as sdk from '../generated/sdk.gen';
export { createClient, createConfig } from '../generated/client';
export type { Client } from '../generated/client';
