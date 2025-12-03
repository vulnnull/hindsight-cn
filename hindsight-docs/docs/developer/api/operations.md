---
sidebar_position: 9
---

# Operations

Monitor and manage long-running background tasks in Hindsight.

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

:::tip Prerequisites
Make sure you've [installed Hindsight](./installation) and understand [how retain works](./retain).
:::

## What Are Operations?

Some Hindsight tasks run asynchronously in the background:

- **Batch retain** — Processing large document sets
- **Entity observations** — Synthesizing entity summaries
- **Graph updates** — Building connections between memories

Operations provide a way to track these background tasks.

## Async Batch Retain

For large content batches, use async mode to avoid timeouts:

<Tabs>
<TabItem value="python" label="Python">

```python
from hindsight_client import Hindsight

client = Hindsight(base_url="http://localhost:8888")

# Start async batch retain
result = client.retain_batch(
    bank_id="my-bank",
    items=[
        {"content": doc1_text},
        {"content": doc2_text},
        # ... hundreds or thousands of documents
    ],
    async_=True  # Enable async mode
)

print(f"Operation ID: {result.get('operation_id')}")
```

</TabItem>
<TabItem value="node" label="Node.js">

```typescript
import { HindsightClient } from '@hindsight/client';

const client = new HindsightClient({ baseUrl: 'http://localhost:8888' });

// Start async batch retain
const result = await client.retainBatch('my-bank', [
    { content: doc1Text },
    { content: doc2Text },
    // ... hundreds or thousands of documents
], { async: true });

console.log(`Operation ID: ${result.operation_id}`);
```

</TabItem>
<TabItem value="cli" label="CLI">

```bash
# Start async batch retain
hindsight retain my-bank --files docs/*.md --async

# Returns operation ID: op-abc123...
```

</TabItem>
</Tabs>

## List Operations

View all operations for a memory bank:

<Tabs>
<TabItem value="python" label="Python">

```python
# Using the low-level API
from hindsight_client_api import ApiClient, Configuration
from hindsight_client_api.api import DefaultApi

config = Configuration(host="http://localhost:8888")
api_client = ApiClient(config)
api = DefaultApi(api_client)

# List all operations
response = api.list_operations(bank_id="my-bank")

for op in response.items:
    print(f"{op.id}: {op.task_type} - {op.status}")
    print(f"  Items: {op.items_count}")
    if op.error_message:
        print(f"  Error: {op.error_message}")
```

</TabItem>
<TabItem value="node" label="Node.js">

```typescript
import { sdk, createClient, createConfig } from '@hindsight/client';

const apiClient = createClient(createConfig({ baseUrl: 'http://localhost:8888' }));

// List all operations
const response = await sdk.listOperations({
    client: apiClient,
    path: { bank_id: 'my-bank' }
});

for (const op of response.data.items) {
    console.log(`${op.id}: ${op.task_type} - ${op.status}`);
    console.log(`  Items: ${op.items_count}`);
    if (op.error_message) {
        console.log(`  Error: ${op.error_message}`);
    }
}
```

</TabItem>
<TabItem value="cli" label="CLI">

```bash
# List all operations
hindsight operations list my-bank

# Filter by status
hindsight operations list my-bank --status running

# Watch all running operations
hindsight operations watch my-bank --all
```

</TabItem>
</Tabs>

## Cancel Operations

Stop a running or pending operation:

<Tabs>
<TabItem value="python" label="Python">

```python
# Cancel operation
api.cancel_operation(
    bank_id="my-bank",
    operation_id="op-abc123"
)

# Cancel all pending operations
response = api.list_operations(bank_id="my-bank")
for op in response.items:
    if op.status == "pending":
        api.cancel_operation(bank_id="my-bank", operation_id=op.id)
```

</TabItem>
<TabItem value="node" label="Node.js">

```typescript
// Cancel operation
await sdk.cancelOperation({
    client: apiClient,
    path: { bank_id: 'my-bank', operation_id: 'op-abc123' }
});

// Cancel all pending
const ops = await sdk.listOperations({
    client: apiClient,
    path: { bank_id: 'my-bank' }
});

for (const op of ops.data.items) {
    if (op.status === 'pending') {
        await sdk.cancelOperation({
            client: apiClient,
            path: { bank_id: 'my-bank', operation_id: op.id }
        });
    }
}
```

</TabItem>
<TabItem value="cli" label="CLI">

```bash
# Cancel operation
hindsight operations cancel my-bank op-abc123

# Cancel all pending
hindsight operations cancel my-bank --all-pending
```

</TabItem>
</Tabs>

## Operation States

| State | Description |
|-------|-------------|
| **pending** | Queued, waiting to start |
| **running** | Currently processing |
| **completed** | Successfully finished |
| **failed** | Encountered an error |
| **cancelled** | Stopped by user |

## Operation Types

| Type | Description |
|------|-------------|
| **batch_retain** | Async batch content ingestion |
| **regenerate_observations** | Entity observation synthesis |
| **graph_update** | Link and connection building |

## Operation Response Format

```json
{
  "id": "op-abc123",
  "bank_id": "my-bank",
  "task_type": "batch_retain",
  "status": "completed",
  "items_count": 1000,
  "document_id": "batch-001",
  "created_at": "2024-03-15T10:00:00Z",
  "error_message": null
}
```

## Monitoring Strategies

### Polling

<Tabs>
<TabItem value="python" label="Python">

```python
import time

def wait_for_operations(api, bank_id, poll_interval=5):
    """Wait for all pending/running operations to complete."""
    while True:
        response = api.list_operations(bank_id=bank_id)

        pending_or_running = [
            op for op in response.items
            if op.status in ['pending', 'running']
        ]

        if not pending_or_running:
            print("All operations completed!")
            break

        for op in pending_or_running:
            print(f"  {op.id}: {op.status} ({op.items_count} items)")

        time.sleep(poll_interval)

# Use it
wait_for_operations(api, "my-bank")
```

</TabItem>
<TabItem value="node" label="Node.js">

```typescript
async function waitForOperations(apiClient: any, bankId: string, pollInterval = 5000) {
    while (true) {
        const response = await sdk.listOperations({
            client: apiClient,
            path: { bank_id: bankId }
        });

        const pendingOrRunning = response.data.items.filter(
            (op: any) => ['pending', 'running'].includes(op.status)
        );

        if (pendingOrRunning.length === 0) {
            console.log('All operations completed!');
            break;
        }

        for (const op of pendingOrRunning) {
            console.log(`  ${op.id}: ${op.status} (${op.items_count} items)`);
        }

        await new Promise(resolve => setTimeout(resolve, pollInterval));
    }
}

// Use it
await waitForOperations(apiClient, 'my-bank');
```

</TabItem>
</Tabs>

## Performance Tips

**Use async for large batches:**
- Sync: < 100 items or < 100KB
- Async: > 100 items or > 100KB

**Monitor progress:**
- Check `items_count` field
- Poll every 5-10 seconds

**Handle failures:**
- Check `error_message` field for details
- Retry with exponential backoff
- Break large batches into smaller chunks

## Next Steps

- [**Documents**](./documents) — Track document sources
- [**Entities**](./entities) — Monitor entity tracking
- [**Memory Banks**](./memory-banks) — Configure bank settings
