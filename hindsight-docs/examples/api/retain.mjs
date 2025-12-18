#!/usr/bin/env node
/**
 * Retain API examples for Hindsight (Node.js)
 * Run: node examples/api/retain.mjs
 */
import { HindsightClient } from '@vectorize-io/hindsight-client';

const HINDSIGHT_URL = process.env.HINDSIGHT_API_URL || 'http://localhost:8888';

// =============================================================================
// Setup (not shown in docs)
// =============================================================================
const client = new HindsightClient({ baseUrl: HINDSIGHT_URL });

// =============================================================================
// Doc Examples
// =============================================================================

// [docs:retain-basic]
await client.retain('my-bank', 'Alice works at Google as a software engineer');
// [/docs:retain-basic]


// [docs:retain-with-context]
await client.retain('my-bank', 'Alice got promoted to senior engineer', {
    context: 'career update',
    timestamp: '2024-03-15T10:00:00Z'
});
// [/docs:retain-with-context]


// [docs:retain-batch]
await client.retainBatch('my-bank', [
    { content: 'Alice works at Google', context: 'career' },
    { content: 'Bob is a data scientist at Meta', context: 'career' },
    { content: 'Alice and Bob are friends', context: 'relationship' }
], { documentId: 'conversation_001' });
// [/docs:retain-batch]


// [docs:retain-async]
// Start async ingestion (returns immediately)
await client.retainBatch('my-bank', [
    { content: 'Large batch item 1' },
    { content: 'Large batch item 2' },
], {
    documentId: 'large-doc',
    async: true
});
// [/docs:retain-async]


// =============================================================================
// Cleanup (not shown in docs)
// =============================================================================
await fetch(`${HINDSIGHT_URL}/v1/default/banks/my-bank`, { method: 'DELETE' });

console.log('retain.mjs: All examples passed');
