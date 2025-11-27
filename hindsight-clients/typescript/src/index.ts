/**
 * Hindsight Client - Clean, TypeScript SDK for the Hindsight API.
 *
 * Example:
 * ```typescript
 * import { HindsightClient } from '@hindsight/client';
 *
 * const client = new HindsightClient({ baseUrl: 'http://localhost:8888' });
 *
 * // Retain a memory
 * await client.retain('alice', 'Alice loves AI');
 *
 * // Recall memories
 * const results = await client.recall('alice', 'What does Alice like?');
 *
 * // Generate contextual answer
 * const answer = await client.reflect('alice', 'What are my interests?');
 * ```
 */

import { createClient, createConfig } from '../generated/client';
import type { Client } from '../generated/client';
import * as sdk from '../generated/sdk.gen';
import type {
    RetainRequest,
    RetainResponse,
    RecallRequest,
    RecallResponse,
    RecallResult,
    ReflectRequest,
    ReflectResponse,
    ListMemoryUnitsResponse,
    BankProfileResponse,
    CreateBankRequest,
    Budget,
} from '../generated/types.gen';

export interface HindsightClientOptions {
    baseUrl: string;
}

export interface MemoryItemInput {
    content: string;
    timestamp?: string | Date;
    context?: string;
    metadata?: Record<string, string>;
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
     * Retain a single memory for a bank.
     */
    async retain(
        bankId: string,
        content: string,
        options?: { timestamp?: Date | string; context?: string; metadata?: Record<string, string> }
    ): Promise<RetainResponse> {
        const item: { content: string; timestamp?: string; context?: string; metadata?: Record<string, string> } = { content };
        if (options?.timestamp) {
            item.timestamp =
                options.timestamp instanceof Date
                    ? options.timestamp.toISOString()
                    : options.timestamp;
        }
        if (options?.context) {
            item.context = options.context;
        }
        if (options?.metadata) {
            item.metadata = options.metadata;
        }

        const response = await sdk.retainMemories({
            client: this.client,
            path: { bank_id: bankId },
            body: { items: [item] },
        });

        return response.data!;
    }

    /**
     * Retain multiple memories in batch.
     */
    async retainBatch(bankId: string, items: MemoryItemInput[], options?: { documentId?: string; async?: boolean }): Promise<RetainResponse> {
        const processedItems = items.map((item) => ({
            content: item.content,
            context: item.context,
            metadata: item.metadata,
            timestamp:
                item.timestamp instanceof Date
                    ? item.timestamp.toISOString()
                    : item.timestamp,
        }));

        const response = await sdk.retainMemories({
            client: this.client,
            path: { bank_id: bankId },
            body: {
                items: processedItems,
                document_id: options?.documentId,
                async: options?.async,
            },
        });

        return response.data!;
    }

    /**
     * Recall memories with a natural language query.
     * Returns a simplified list of recall results.
     */
    async recall(
        bankId: string,
        query: string,
        options?: { maxTokens?: number; budget?: Budget }
    ): Promise<RecallResult[]> {
        const response = await sdk.recallMemories({
            client: this.client,
            path: { bank_id: bankId },
            body: {
                query,
                max_tokens: options?.maxTokens,
                budget: options?.budget || 'mid',
            },
        });

        return response.data?.results ?? [];
    }

    /**
     * Recall memories with full options and response.
     */
    async recallMemories(
        bankId: string,
        options: {
            query: string;
            types?: string[];
            maxTokens?: number;
            trace?: boolean;
            budget?: Budget;
        }
    ): Promise<RecallResponse> {
        const response = await sdk.recallMemories({
            client: this.client,
            path: { bank_id: bankId },
            body: {
                query: options.query,
                types: options.types,
                max_tokens: options.maxTokens,
                trace: options.trace,
                budget: options.budget || 'mid',
            },
        });

        return response.data!;
    }

    /**
     * Reflect and generate a contextual answer using the bank's identity and memories.
     */
    async reflect(
        bankId: string,
        query: string,
        options?: { context?: string; budget?: Budget }
    ): Promise<ReflectResponse> {
        const response = await sdk.reflect({
            client: this.client,
            path: { bank_id: bankId },
            body: {
                query,
                context: options?.context,
                budget: options?.budget || 'low',
            },
        });

        return response.data!;
    }

    /**
     * List memories with pagination.
     */
    async listMemories(
        bankId: string,
        options?: { limit?: number; offset?: number; type?: string; q?: string }
    ): Promise<ListMemoryUnitsResponse> {
        const response = await sdk.listMemories({
            client: this.client,
            path: { bank_id: bankId },
            query: {
                limit: options?.limit,
                offset: options?.offset,
                type: options?.type,
                q: options?.q,
            },
        });

        return response.data!;
    }

    /**
     * Create or update a bank with personality and background.
     */
    async createBank(
        bankId: string,
        options: { name?: string; background?: string; personality?: any }
    ): Promise<BankProfileResponse> {
        const response = await sdk.createOrUpdateBank({
            client: this.client,
            path: { bank_id: bankId },
            body: {
                name: options.name,
                background: options.background,
                personality: options.personality,
            },
        });

        return response.data!;
    }

    /**
     * Get a bank's profile.
     */
    async getBankProfile(bankId: string): Promise<BankProfileResponse> {
        const response = await sdk.getBankProfile({
            client: this.client,
            path: { bank_id: bankId },
        });

        return response.data!;
    }
}

// Re-export types for convenience
export type {
    RetainRequest,
    RetainResponse,
    RecallRequest,
    RecallResponse,
    RecallResult,
    ReflectRequest,
    ReflectResponse,
    ListMemoryUnitsResponse,
    BankProfileResponse,
    CreateBankRequest,
    Budget,
};

// Also export low-level SDK functions for advanced usage
export * as sdk from '../generated/sdk.gen';
export { createClient, createConfig } from '../generated/client';
export type { Client } from '../generated/client';
