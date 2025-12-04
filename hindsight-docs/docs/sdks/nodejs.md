---
sidebar_position: 2
---

# Node.js Client

Official TypeScript/JavaScript client for the Hindsight API.

## Installation

```bash
npm install @vectorize-io/hindsight-client
```

## Quick Start

```typescript
import { HindsightClient } from '@vectorize-io/hindsight-client';

const client = new HindsightClient({ baseUrl: 'http://localhost:8888' });

// Retain a memory
await client.retain('my-agent', 'Alice works at Google');

// Recall memories
const response = await client.recall('my-agent', 'What does Alice do?');
for (const r of response.results) {
    console.log(r.text);
}

// Reflect - generate response with personality
const answer = await client.reflect('my-agent', 'Tell me about Alice');
console.log(answer.text);
```

## Client Initialization

```typescript
import { HindsightClient } from '@vectorize-io/hindsight-client';

const client = new HindsightClient({
    baseUrl: 'http://localhost:8888',
});
```

## Core Operations

### Retain (Store Memory)

```typescript
// Simple
await client.retain('my-agent', 'Alice works at Google');

// With options
await client.retain('my-agent', 'Alice got promoted', {
    timestamp: new Date('2024-01-15'),
    context: 'career update',
    metadata: { source: 'slack' },
    async: false,  // Set true for background processing
});
```

### Retain Batch

```typescript
await client.retainBatch('my-agent', [
    { content: 'Alice works at Google', context: 'career' },
    { content: 'Bob is a data scientist', context: 'career' },
], {
    documentId: 'conversation_001',
    async: false,
});
```

### Recall (Search)

```typescript
// Simple - returns RecallResponse
const response = await client.recall('my-agent', 'What does Alice do?');

for (const r of response.results) {
    console.log(`${r.text} (type: ${r.type})`);
}

// With options
const response = await client.recall('my-agent', 'What does Alice do?', {
    types: ['world', 'opinion'],  // Filter by fact type
    maxTokens: 4096,
    budget: 'high',  // 'low', 'mid', or 'high'
    trace: true,
});
```

### Reflect (Generate Response)

```typescript
const answer = await client.reflect('my-agent', 'What should I know about Alice?', {
    budget: 'low',  // 'low', 'mid', or 'high'
    context: 'preparing for a meeting',
});

console.log(answer.text);       // Generated response
console.log(answer.based_on);   // Memories used
```

## Bank Management

### Create Bank

```typescript
await client.createBank('my-agent', {
    name: 'Assistant',
    background: 'I am a helpful AI assistant',
    personality: {
        openness: 0.7,
        conscientiousness: 0.8,
        extraversion: 0.5,
        agreeableness: 0.6,
        neuroticism: 0.3,
        bias_strength: 0.5,
    },
});
```

### Get Bank Profile

```typescript
const profile = await client.getBankProfile('my-agent');
console.log(profile.personality);
console.log(profile.background);
```

### List Memories

```typescript
const response = await client.listMemories('my-agent', {
    type: 'world',  // Optional filter
    q: 'Alice',     // Optional text search
    limit: 100,
    offset: 0,
});

for (const memory of response.memories) {
    console.log(`${memory.id}: ${memory.text}`);
}
```

## TypeScript Types

The client exports all types for full TypeScript support:

```typescript
import type {
    RetainResponse,
    RecallResponse,
    RecallResult,
    ReflectResponse,
    BankProfileResponse,
    Budget,
} from '@vectorize-io/hindsight-client';

// Budget is a union type: 'low' | 'mid' | 'high'
const budget: Budget = 'mid';
```

## Advanced: Low-Level SDK

For advanced use cases, access the auto-generated SDK directly:

```typescript
import { sdk, createClient, createConfig } from '@vectorize-io/hindsight-client';

const client = createClient(createConfig({ baseUrl: 'http://localhost:8888' }));

// Use sdk functions directly
const response = await sdk.recallMemories({
    client,
    path: { bank_id: 'my-agent' },
    body: {
        query: 'What does Alice do?',
        budget: 'mid',
        max_tokens: 4096,
    },
});
```

## Error Handling

```typescript
import { HindsightClient } from '@vectorize-io/hindsight-client';

const client = new HindsightClient({ baseUrl: 'http://localhost:8888' });

try {
    const response = await client.recall('unknown-agent', 'test');
} catch (error) {
    console.error('Error:', error.message);
}
```

## Example: Full Workflow

```typescript
import { HindsightClient } from '@vectorize-io/hindsight-client';

async function main() {
    const client = new HindsightClient({ baseUrl: 'http://localhost:8888' });

    // Create a bank with personality
    await client.createBank('demo', {
        name: 'Demo Agent',
        background: 'A helpful assistant for demos',
        personality: {
            openness: 0.8,
            conscientiousness: 0.7,
            extraversion: 0.6,
            agreeableness: 0.8,
            neuroticism: 0.2,
            bias_strength: 0.5,
        },
    });

    // Store some memories
    await client.retain('demo', 'Alice works at Google');
    await client.retain('demo', 'Bob is a data scientist at Google');
    await client.retain('demo', 'Alice and Bob collaborate on ML projects');

    // Search for memories
    const searchResults = await client.recall('demo', 'Who works at Google?');
    console.log('Search results:');
    for (const r of searchResults.results) {
        console.log(`  - ${r.text}`);
    }

    // Generate a response
    const answer = await client.reflect('demo', 'What do you know about the team?');
    console.log('\nReflection:', answer.text);
}

main().catch(console.error);
```
