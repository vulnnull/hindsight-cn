#!/usr/bin/env node
/**
 * Documents API examples for Hindsight (Node.js)
 * Run: node examples/api/documents.mjs
 */
import { HindsightClient, sdk, createClient, createConfig } from '@vectorize-io/hindsight-client';

const HINDSIGHT_URL = process.env.HINDSIGHT_API_URL || 'http://localhost:8888';

// =============================================================================
// Setup (not shown in docs)
// =============================================================================
const client = new HindsightClient({ baseUrl: HINDSIGHT_URL });

// =============================================================================
// Doc Examples
// =============================================================================

// [docs:document-retain]
// Retain with document ID
await client.retain('my-bank', 'Alice presented the Q4 roadmap...', {
    document_id: 'meeting-2024-03-15'
});

// Batch retain
await client.retainBatch('my-bank', [
    { content: 'Item 1: Product launch delayed to Q2' },
    { content: 'Item 2: New hiring targets announced' },
    { content: 'Item 3: Budget approved for ML team' }
], { documentId: 'meeting-2024-03-15' });
// [/docs:document-retain]


// [docs:document-update]
// Original
await client.retain('my-bank', 'Project deadline: March 31', {
    document_id: 'project-plan'
});

// Update
await client.retain('my-bank', 'Project deadline: April 15 (extended)', {
    document_id: 'project-plan'
});
// [/docs:document-update]


// [docs:document-get]
const apiClient = createClient(createConfig({ baseUrl: 'http://localhost:8888' }));

// Get document to expand context from recall results
const { data: doc } = await sdk.getDocument({
    client: apiClient,
    path: { bank_id: 'my-bank', document_id: 'meeting-2024-03-15' }
});

console.log(`Document: ${doc.id}`);
console.log(`Original text: ${doc.original_text}`);
console.log(`Memory count: ${doc.memory_unit_count}`);
console.log(`Created: ${doc.created_at}`);
// [/docs:document-get]


// =============================================================================
// Cleanup (not shown in docs)
// =============================================================================
await fetch(`${HINDSIGHT_URL}/v1/default/banks/my-bank`, { method: 'DELETE' });

console.log('documents.mjs: All examples passed');
