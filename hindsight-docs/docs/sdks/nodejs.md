---
sidebar_position: 2
---

# Node.js Client

Official TypeScript/JavaScript client for the Hindsight API.

## Installation

```bash
npm install @hindsight/client
```

## Quick Start

```typescript
import { OpenAPI, MemoryStorageService, SearchService } from '@hindsight/client';

// Configure base URL
OpenAPI.BASE = 'http://localhost:8888';

// Store a memory
await MemoryStorageService.putApiPutPost({
    agent_id: 'my-agent',
    content: 'Alice works at Google as a software engineer',
});

// Search memories
const results = await SearchService.searchApiSearchPost({
    agent_id: 'my-agent',
    query: 'What does Alice do?',
});

console.log(results);
```

## Configuration

```typescript
import { OpenAPI } from '@hindsight/client';

OpenAPI.BASE = 'http://localhost:8888';
OpenAPI.TOKEN = 'your-api-token';  // If authentication is enabled
```

## Memory Operations

### Store Memory

```typescript
import { MemoryStorageService } from '@hindsight/client';

await MemoryStorageService.putApiPutPost({
    agent_id: 'my-agent',
    content: 'Alice works at Google as a software engineer',
    context: 'career discussion',
    event_date: '2024-01-15T10:00:00Z',
});
```

### Store Batch

```typescript
await MemoryStorageService.batchApiMemoriesBatchPost({
    agent_id: 'my-agent',
    items: [
        { content: 'Alice works at Google', context: 'career' },
        { content: 'Bob is a data scientist', context: 'career' },
    ],
    document_id: 'conversation_001',
});
```

## Search Operations

### Basic Search

```typescript
import { SearchService } from '@hindsight/client';

const results = await SearchService.searchApiSearchPost({
    agent_id: 'my-agent',
    query: 'What does Alice do?',
});

for (const r of results.results) {
    console.log(`${r.text} (weight: ${r.weight})`);
}
```

### Advanced Search

```typescript
const results = await SearchService.recallApiRecallPost({
    bank_id: 'my-agent',
    query: 'What does Alice do?',
    budget: 'low',  // 'low', 'mid', or 'high'
    top_k: 10,
});
```

### Search World Facts

```typescript
const worldFacts = await SearchService.worldSearchApiWorldSearchPost({
    agent_id: 'my-agent',
    query: 'Who works at Google?',
});
```

### Search Opinions

```typescript
const opinions = await SearchService.opinionSearchApiOpinionSearchPost({
    agent_id: 'my-agent',
    query: 'What do I think about Python?',
});
```

## Reflect (Generate Response)

```typescript
import { ReasoningService } from '@hindsight/client';

const response = await ReasoningService.reflectApiReflectPost({
    bank_id: 'my-agent',
    query: 'What should I know about Alice?',
    budget: 'low',  // 'low', 'mid', or 'high'
});

console.log(response.text);        // Generated response
console.log(response.based_on);    // Memories used
console.log(response.new_opinions); // New opinions formed
```

## Memory bank Management

### Create Memory bank

```typescript
import { ManagementService } from '@hindsight/client';

await ManagementService.createAgentApiAgentsAgentIdPut('my-agent', {
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

### Get Profile

```typescript
const profile = await ManagementService.getProfileApiAgentsAgentIdProfileGet('my-agent');
console.log(profile.personality);
console.log(profile.background);
```

### List Memory banks

```typescript
const memory banks = await ManagementService.listAgentsApiAgentsGet();
for (const agent of memory banks.memory banks) {
    console.log(agent.agent_id);
}
```

### Update Personality

```typescript
await ManagementService.updatePersonalityApiAgentsAgentIdProfilePut('my-agent', {
    openness: 0.9,
    conscientiousness: 0.7,
});
```

### Merge Background

```typescript
await ManagementService.mergeBackgroundApiAgentsAgentIdBackgroundPost('my-agent', {
    background: 'Additional context to merge',
});
```

## Error Handling

```typescript
import { ApiError } from '@hindsight/client';

try {
    await SearchService.searchApiSearchPost({
        agent_id: 'unknown-agent',
        query: 'test',
    });
} catch (error) {
    if (error instanceof ApiError) {
        console.log(`Error: ${error.message}`);
        console.log(`Status: ${error.status}`);
    }
}
```

## TypeScript Types

The client exports all types for full TypeScript support:

```typescript
import type {
    AgentProfile,
    SearchResult,
    ThinkResponse,
    MemoryItem,
    PersonalityTraits,
} from '@hindsight/client';

const personality: PersonalityTraits = {
    openness: 0.7,
    conscientiousness: 0.8,
    extraversion: 0.5,
    agreeableness: 0.6,
    neuroticism: 0.3,
    bias_strength: 0.5,
};
```
