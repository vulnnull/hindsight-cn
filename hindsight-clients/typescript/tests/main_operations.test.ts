/**
 * These tests require a running Hindsight API server.
 */

import { HindsightClient } from '../src';

// Test configuration
const HINDSIGHT_API_URL = process.env.HINDSIGHT_API_URL || 'http://localhost:8888';
const TEST_AGENT_ID = `test_agent_${new Date().toISOString().replace(/[-:T.Z]/g, '').slice(0, 15)}`;

let client: HindsightClient;

beforeAll(() => {
    client = new HindsightClient({ baseUrl: HINDSIGHT_API_URL });
});

describe('TestStore', () => {
    test('put single memory', async () => {
        const response = await client.put(
            TEST_AGENT_ID,
            'Alice loves artificial intelligence and machine learning'
        );

        expect(response).not.toBeNull();
        expect(response.success).toBe(true);
        expect(response.items_count).toBe(1);
    });

    test('put memory with context', async () => {
        const response = await client.put(TEST_AGENT_ID, 'Bob went hiking in the mountains', {
            eventDate: new Date('2024-01-15T10:30:00'),
            context: 'outdoor activities',
        });

        expect(response).not.toBeNull();
        expect(response.success).toBe(true);
    });

    test('put batch memories', async () => {
        const response = await client.putBatch(TEST_AGENT_ID, [
            { content: 'Charlie enjoys reading science fiction books' },
            { content: 'Diana is learning to play the guitar', context: 'hobbies' },
            { content: 'Eve completed a marathon last month', event_date: '2024-10-15' },
        ]);

        expect(response).not.toBeNull();
        expect(response.success).toBe(true);
        expect(response.items_count).toBe(3);
    });
});

describe('TestSearch', () => {
    beforeAll(async () => {
        // Setup: Store some test memories before search tests
        await client.putBatch(TEST_AGENT_ID, [
            { content: 'Alice loves programming in Python' },
            { content: 'Bob enjoys hiking and outdoor adventures' },
            { content: 'Charlie is interested in quantum physics' },
            { content: 'Diana plays the violin beautifully' },
        ]);
    });

    test('search basic', async () => {
        const results = await client.search(TEST_AGENT_ID, 'What does Alice like?');

        expect(results).not.toBeNull();
        expect(results.length).toBeGreaterThan(0);

        // Check that at least one result contains relevant information
        const resultTexts = results.map((r) => r.text || '');
        const hasRelevant = resultTexts.some(
            (text) => text.includes('Alice') || text.includes('Python') || text.includes('programming')
        );
        expect(hasRelevant).toBe(true);
    });

    test('search with max tokens', async () => {
        const results = await client.search(TEST_AGENT_ID, 'outdoor activities', {
            maxTokens: 1024,
        });

        expect(results).not.toBeNull();
        expect(Array.isArray(results)).toBe(true);
    });

    test('search full featured', async () => {
        const response = await client.searchMemories(TEST_AGENT_ID, {
            query: "What are people's hobbies?",
            factType: ['world'],
            maxTokens: 2048,
            trace: true,
        });

        expect(response).not.toBeNull();
        expect(response.results).toBeDefined();
        // Trace should be included when enabled
        if (response.trace) {
            expect(typeof response.trace).toBe('object');
        }
    });
});

describe('TestThink', () => {
    beforeAll(async () => {
        // Setup: Create agent and store test memories
        await client.createAgent(TEST_AGENT_ID, {
            name: 'Test Agent',
            background: 'I am a helpful AI assistant interested in technology and science.',
        });

        await client.putBatch(TEST_AGENT_ID, [
            { content: 'The Python programming language is great for data science' },
            { content: 'Machine learning models can recognize patterns in data' },
            { content: 'Neural networks are inspired by biological neurons' },
        ]);
    });

    test('think basic', async () => {
        const response = await client.think(
            TEST_AGENT_ID,
            'What do you think about artificial intelligence?'
        );

        expect(response).not.toBeNull();
        expect(response.text).toBeDefined();
        expect(response.text!.length).toBeGreaterThan(0);

        // Should include facts that were used
        if (response.based_on) {
            expect(Array.isArray(response.based_on)).toBe(true);
        }
    });

    test('think with context', async () => {
        const response = await client.think(TEST_AGENT_ID, 'Should I learn Python?', {
            context: "I'm interested in starting a career in data science",
            thinkingBudget: 100,
        });

        expect(response).not.toBeNull();
        expect(response.text).toBeDefined();
        expect(response.text!.length).toBeGreaterThan(0);
    });
});

describe('TestListMemories', () => {
    beforeAll(async () => {
        // Setup: Store some test memories
        await client.putBatch(TEST_AGENT_ID, [
            { content: 'Test memory 0' },
            { content: 'Test memory 1' },
            { content: 'Test memory 2' },
            { content: 'Test memory 3' },
            { content: 'Test memory 4' },
        ]);
    });

    test('list all memories', async () => {
        const response = await client.listMemories(TEST_AGENT_ID);

        expect(response).not.toBeNull();
        expect(response.items).toBeDefined();
        expect(response.total).toBeDefined();
        expect(response.items!.length).toBeGreaterThan(0);
    });

    test('list with pagination', async () => {
        const response = await client.listMemories(TEST_AGENT_ID, {
            limit: 2,
            offset: 0,
        });

        expect(response).not.toBeNull();
        expect(response.items).toBeDefined();
        expect(response.items!.length).toBeLessThanOrEqual(2);
    });
});

describe('TestEndToEndWorkflow', () => {
    test('complete workflow', async () => {
        const workflowAgentId = `workflow_test_${new Date().toISOString().replace(/[-:T.Z]/g, '').slice(0, 15)}`;

        // 1. Create agent
        await client.createAgent(workflowAgentId, {
            name: 'Alice',
            background: 'I am a software engineer who loves Python programming.',
        });

        // 2. Store memories
        const storeResponse = await client.putBatch(workflowAgentId, [
            { content: 'I completed a project using FastAPI' },
            { content: 'I learned about async programming in Python' },
            { content: 'I enjoy working on open source projects' },
        ]);
        expect(storeResponse.success).toBe(true);

        // 3. Search for relevant memories
        const searchResults = await client.search(
            workflowAgentId,
            'What programming technologies do I use?'
        );
        expect(searchResults.length).toBeGreaterThan(0);

        // 4. Generate contextual answer
        const thinkResponse = await client.think(
            workflowAgentId,
            'What are my professional interests?'
        );
        expect(thinkResponse.text).toBeDefined();
        expect(thinkResponse.text!.length).toBeGreaterThan(0);
    });
});
