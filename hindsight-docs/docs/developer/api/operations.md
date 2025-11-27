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
# Start async batch retain
operation = client.retain_batch_async(
    bank_id="my-bank",
    contents=[
        {"content": doc1_text},
        {"content": doc2_text},
        # ... hundreds or thousands of documents
    ]
)

print(f"Operation ID: {operation['operation_id']}")
print(f"Status: {operation['status']}")  # 'pending' or 'running'

# Check status
status = client.get_operation(
    bank_id="my-bank",
    operation_id=operation['operation_id']
)

print(f"Status: {status['status']}")  # 'pending', 'running', 'completed', 'failed'
print(f"Progress: {status['progress']}/{status['total']}")

# Wait for completion
import time

while True:
    status = client.get_operation(bank_id="my-bank", operation_id=operation['operation_id'])
    if status['status'] in ['completed', 'failed']:
        break
    print(f"Progress: {status['progress']}/{status['total']}")
    time.sleep(5)

if status['status'] == 'completed':
    print(f"Created {len(status['result']['memory_ids'])} memories")
```

</TabItem>
<TabItem value="node" label="Node.js">

```javascript
// Start async batch retain
const operation = await client.retainBatchAsync({
    bankId: 'my-bank',
    contents: [
        { content: doc1Text },
        { content: doc2Text },
        // ... hundreds or thousands of documents
    ]
});

console.log(`Operation ID: ${operation.operationId}`);
console.log(`Status: ${operation.status}`);

// Check status
const status = await client.getOperation({
    bankId: 'my-bank',
    operationId: operation.operationId
});

console.log(`Status: ${status.status}`);
console.log(`Progress: ${status.progress}/${status.total}`);

// Wait for completion
async function waitForOperation(bankId, operationId) {
    while (true) {
        const status = await client.getOperation({ bankId, operationId });
        if (['completed', 'failed'].includes(status.status)) {
            return status;
        }
        console.log(`Progress: ${status.progress}/${status.total}`);
        await new Promise(resolve => setTimeout(resolve, 5000));
    }
}

const finalStatus = await waitForOperation('my-bank', operation.operationId);
if (finalStatus.status === 'completed') {
    console.log(`Created ${finalStatus.result.memoryIds.length} memories`);
}
```

</TabItem>
<TabItem value="cli" label="CLI">

```bash
# Start async batch retain
hindsight retain my-bank --files docs/*.md --async

# Returns operation ID: op-abc123...

# Check status
hindsight operations get my-bank op-abc123

# Watch progress
hindsight operations watch my-bank op-abc123
```

</TabItem>
</Tabs>

## List Operations

View all operations for a memory bank:

<Tabs>
<TabItem value="python" label="Python">

```python
# List all operations
operations = client.list_operations(bank_id="my-bank")

for op in operations:
    print(f"{op['operation_id']}: {op['type']} - {op['status']}")
    if op['status'] == 'running':
        print(f"  Progress: {op['progress']}/{op['total']}")

# Filter by status
pending = client.list_operations(
    bank_id="my-bank",
    status="pending"
)

running = client.list_operations(
    bank_id="my-bank",
    status="running"
)

# With pagination
operations = client.list_operations(
    bank_id="my-bank",
    limit=50,
    offset=0
)
```

</TabItem>
<TabItem value="node" label="Node.js">

```javascript
// List all operations
const operations = await client.listOperations({
    bankId: 'my-bank'
});

operations.forEach(op => {
    console.log(`${op.operationId}: ${op.type} - ${op.status}`);
    if (op.status === 'running') {
        console.log(`  Progress: ${op.progress}/${op.total}`);
    }
});

// Filter by status
const pending = await client.listOperations({
    bankId: 'my-bank',
    status: 'pending'
});
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
client.cancel_operation(
    bank_id="my-bank",
    operation_id="op-abc123"
)

# Cancel all pending operations
operations = client.list_operations(bank_id="my-bank", status="pending")
for op in operations:
    client.cancel_operation(bank_id="my-bank", operation_id=op['operation_id'])
```

</TabItem>
<TabItem value="node" label="Node.js">

```javascript
// Cancel operation
await client.cancelOperation({
    bankId: 'my-bank',
    operationId: 'op-abc123'
});

// Cancel all pending
const pending = await client.listOperations({
    bankId: 'my-bank',
    status: 'pending'
});

for (const op of pending) {
    await client.cancelOperation({
        bankId: 'my-bank',
        operationId: op.operationId
    });
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
  "operation_id": "op-abc123",
  "bank_id": "my-bank",
  "type": "batch_retain",
  "status": "running",
  "progress": 450,
  "total": 1000,
  "created_at": "2024-03-15T10:00:00Z",
  "started_at": "2024-03-15T10:00:05Z",
  "completed_at": null,
  "error": null,
  "result": null
}
```

## Monitoring Strategies

### Polling

```python
import time

def wait_for_operation(client, bank_id, operation_id, poll_interval=5):
    while True:
        status = client.get_operation(bank_id=bank_id, operation_id=operation_id)

        if status['status'] == 'completed':
            return status['result']
        elif status['status'] == 'failed':
            raise Exception(f"Operation failed: {status['error']}")
        elif status['status'] == 'cancelled':
            raise Exception("Operation was cancelled")

        print(f"Progress: {status['progress']}/{status['total']}")
        time.sleep(poll_interval)

# Use it
result = wait_for_operation(client, "my-bank", op_id)
print(f"Created {len(result['memory_ids'])} memories")
```

### Webhooks (Coming Soon)

```python
# Configure webhook for operation completion
client.configure_webhook(
    bank_id="my-bank",
    url="https://myapp.com/webhooks/hindsight",
    events=["operation.completed", "operation.failed"]
)
```

## Performance Tips

**Use async for large batches:**
- Sync: < 100 items or < 100KB
- Async: > 100 items or > 100KB

**Monitor progress:**
- Check `progress` / `total` fields
- Poll every 5-10 seconds

**Handle failures:**
- Check `error` field for details
- Retry with exponential backoff
- Break large batches into smaller chunks

## Next Steps

- [**Documents**](./documents) — Track document sources
- [**Entities**](./entities) — Monitor entity tracking
- [**Memory Banks**](./memory-banks) — Configure bank settings
