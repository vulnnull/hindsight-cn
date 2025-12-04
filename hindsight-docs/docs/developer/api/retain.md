---
sidebar_position: 2
---

# Ingest Data

Store memories, conversations, and documents into Hindsight.

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

:::tip Prerequisites
Make sure you've completed the [Quick Start](./quickstart) to install the client and start the server.
:::

## Store a Single Memory

<Tabs>
<TabItem value="python" label="Python">

```python
from hindsight_client import Hindsight

client = Hindsight(base_url="http://localhost:8888")

client.retain(
    bank_id="my-bank",
    content="Alice works at Google as a software engineer"
)
```

</TabItem>
<TabItem value="node" label="Node.js">

```typescript
import { HindsightClient } from '@vectorize-io/hindsight-client';

const client = new HindsightClient({ baseUrl: 'http://localhost:8888' });

await client.retain('my-bank', 'Alice works at Google as a software engineer');
```

</TabItem>
<TabItem value="cli" label="CLI">

```bash
hindsight memory put my-bank "Alice works at Google as a software engineer"
```

</TabItem>
</Tabs>

## Store with Context and Date

Add context and event dates for better retrieval:

<Tabs>
<TabItem value="python" label="Python">

```python
client.retain(
    bank_id="my-bank",
    content="Alice got promoted to senior engineer",
    context="career update",
    timestamp="2024-03-15T10:00:00Z"
)
```

</TabItem>
<TabItem value="node" label="Node.js">

```typescript
await client.retain('my-bank', 'Alice got promoted to senior engineer', {
    context: 'career update',
    timestamp: '2024-03-15T10:00:00Z'
});
```

</TabItem>
<TabItem value="cli" label="CLI">

```bash
hindsight memory put my-bank "Alice got promoted" \
    --context "career update" \
    --event-date "2024-03-15"
```

</TabItem>
</Tabs>

The `timestamp` enables temporal queries like "What happened last spring?"

## Batch Ingestion

Store multiple memories in a single request:

<Tabs>
<TabItem value="python" label="Python">

```python
client.retain_batch(
    bank_id="my-bank",
    items=[
        {"content": "Alice works at Google", "context": "career"},
        {"content": "Bob is a data scientist at Meta", "context": "career"},
        {"content": "Alice and Bob are friends", "context": "relationship"}
    ],
    document_id="conversation_001"
)
```

</TabItem>
<TabItem value="node" label="Node.js">

```typescript
await client.retainBatch('my-bank', [
    { content: 'Alice works at Google', context: 'career' },
    { content: 'Bob is a data scientist at Meta', context: 'career' },
    { content: 'Alice and Bob are friends', context: 'relationship' }
], { documentId: 'conversation_001' });
```

</TabItem>
</Tabs>

The `document_id` groups related memories for later management.

## Store from Files

<Tabs>
<TabItem value="cli" label="CLI">

```bash
# Single file
hindsight memory put-files my-bank document.txt

# Multiple files
hindsight memory put-files my-bank doc1.txt doc2.md notes.txt

# With document ID
hindsight memory put-files my-bank report.pdf --document-id "q4-report"
```

</TabItem>
</Tabs>

:::info How Retain Works
Learn about fact extraction, entity resolution, and graph construction in the [Retain Architecture](/developer/retain) guide.
:::

## Async Ingestion

For large batches, use async ingestion:

<Tabs>
<TabItem value="python" label="Python">

```python
# Start async ingestion
result = client.retain_batch(
    bank_id="my-bank",
    items=[...large batch...],
    document_id="large-doc",
    async_=True
)

# Result contains operation_id for tracking
print(result["operation_id"])
```

</TabItem>
<TabItem value="node" label="Node.js">

```typescript
// Start async ingestion
const result = await client.retainBatch('my-bank', largeItems, {
    documentId: 'large-doc',
    async: true
});

console.log(result.operation_id);
```

</TabItem>
</Tabs>

## Best Practices

| Do | Don't |
|----|-------|
| Include context for better retrieval | Store raw unstructured dumps |
| Use document_id to group related content | Mix unrelated content in one batch |
| Add timestamp for temporal queries | Omit dates if time matters |
| Store conversations as they happen | Wait to batch everything |
