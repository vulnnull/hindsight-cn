---
sidebar_position: 8
---

# Documents

Track and manage document sources in your memory bank. Documents provide traceability — knowing where memories came from.

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

:::tip Prerequisites
Make sure you've [installed Hindsight](./installation) and understand [how retain works](./retain).
:::

## What Are Documents?

Documents are containers for retained content. They help you:

- **Track sources** — Know which PDF, conversation, or file a memory came from
- **Update content** — Re-retain a document to update its facts
- **Delete in bulk** — Remove all memories from a document at once
- **Organize memories** — Group related facts by source

## Retain with Document ID

Associate retained content with a document:

<Tabs>
<TabItem value="python" label="Python">

```python
from hindsight_client import Hindsight

client = Hindsight(base_url="http://localhost:8888")

# Retain with document ID
client.retain(
    bank_id="my-bank",
    content="Alice presented the Q4 roadmap...",
    document_id="meeting-2024-03-15"
)

# Batch retain for a document
client.retain_batch(
    bank_id="my-bank",
    items=[
        {"content": "Item 1: Product launch delayed to Q2"},
        {"content": "Item 2: New hiring targets announced"},
        {"content": "Item 3: Budget approved for ML team"}
    ],
    document_id="meeting-2024-03-15"
)

# From file
with open("notes.txt") as f:
    client.retain(
        bank_id="my-bank",
        content=f.read(),
        document_id="notes-2024-03-15"
    )
```

</TabItem>
<TabItem value="node" label="Node.js">

```typescript
import { HindsightClient } from '@hindsight/client';

const client = new HindsightClient({ baseUrl: 'http://localhost:8888' });

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
```

</TabItem>
<TabItem value="cli" label="CLI">

```bash
# Retain file with document ID
hindsight retain my-bank --file notes.txt --document-id notes-2024-03-15

# Batch retain directory
hindsight retain my-bank --files docs/*.md --document-id project-docs
```

</TabItem>
</Tabs>

## Update Documents

Re-retaining with the same document_id **replaces** the old content:

<Tabs>
<TabItem value="python" label="Python">

```python
# Original
client.retain(
    bank_id="my-bank",
    content="Project deadline: March 31",
    document_id="project-plan"
)

# Update (deletes old facts, creates new ones)
client.retain(
    bank_id="my-bank",
    content="Project deadline: April 15 (extended)",
    document_id="project-plan"
)
```

</TabItem>
<TabItem value="node" label="Node.js">

```typescript
// Original
await client.retain('my-bank', 'Project deadline: March 31', {
    document_id: 'project-plan'
});

// Update
await client.retain('my-bank', 'Project deadline: April 15 (extended)', {
    document_id: 'project-plan'
});
```

</TabItem>
<TabItem value="cli" label="CLI">

```bash
# Original
hindsight retain my-bank "Project deadline: March 31" --document-id project-plan

# Update
hindsight retain my-bank "Project deadline: April 15 (extended)" --document-id project-plan
```

</TabItem>
</Tabs>

## List Documents

View all documents in a memory bank:

<Tabs>
<TabItem value="python" label="Python">

```python
# Using the low-level API
from hindsight_client_api import ApiClient, Configuration
from hindsight_client_api.api import DefaultApi

config = Configuration(host="http://localhost:8888")
api_client = ApiClient(config)
api = DefaultApi(api_client)

# List all documents
response = api.list_documents(bank_id="my-bank")

for doc in response.items:
    print(f"{doc.id}: {doc.memory_unit_count} memories")
    print(f"  Created: {doc.created_at}")

# With pagination
response = api.list_documents(
    bank_id="my-bank",
    limit=50,
    offset=0
)
```

</TabItem>
<TabItem value="node" label="Node.js">

```typescript
import { sdk, createClient, createConfig } from '@hindsight/client';

const apiClient = createClient(createConfig({ baseUrl: 'http://localhost:8888' }));

// List all documents
const response = await sdk.listDocuments({
    client: apiClient,
    path: { bank_id: 'my-bank' }
});

for (const doc of response.data.items) {
    console.log(`${doc.id}: ${doc.memory_unit_count} memories`);
    console.log(`  Created: ${doc.created_at}`);
}
```

</TabItem>
<TabItem value="cli" label="CLI">

```bash
# List documents
hindsight documents list my-bank

# With limit
hindsight documents list my-bank --limit 50
```

</TabItem>
</Tabs>

## Get Document Details

Retrieve a specific document with its content:

<Tabs>
<TabItem value="python" label="Python">

```python
# Get document
doc = api.get_document(
    bank_id="my-bank",
    document_id="meeting-2024-03-15"
)

print(f"Document: {doc.id}")
print(f"Original text: {doc.original_text[:200]}...")
print(f"Memories: {doc.memory_unit_count}")
```

</TabItem>
<TabItem value="node" label="Node.js">

```typescript
// Get document
const doc = await sdk.getDocument({
    client: apiClient,
    path: { bank_id: 'my-bank', document_id: 'meeting-2024-03-15' }
});

console.log(`Document: ${doc.data.id}`);
console.log(`Original text: ${doc.data.original_text.substring(0, 200)}...`);
console.log(`Memories: ${doc.data.memory_unit_count}`);
```

</TabItem>
<TabItem value="cli" label="CLI">

```bash
# Get document
hindsight documents get my-bank meeting-2024-03-15
```

</TabItem>
</Tabs>

## Delete Documents

Remove a document and all its memories:

<Tabs>
<TabItem value="python" label="Python">

```python
# Delete document (removes all associated memories)
api.delete_document(
    bank_id="my-bank",
    document_id="old-meeting"
)

# Bulk delete
for doc_id in ["old-1", "old-2", "old-3"]:
    api.delete_document(bank_id="my-bank", document_id=doc_id)
```

</TabItem>
<TabItem value="node" label="Node.js">

```typescript
// Delete document
await sdk.deleteDocument({
    client: apiClient,
    path: { bank_id: 'my-bank', document_id: 'old-meeting' }
});

// Bulk delete
for (const docId of ['old-1', 'old-2', 'old-3']) {
    await sdk.deleteDocument({
        client: apiClient,
        path: { bank_id: 'my-bank', document_id: docId }
    });
}
```

</TabItem>
<TabItem value="cli" label="CLI">

```bash
# Delete document
hindsight documents delete my-bank old-meeting

# Confirm deletion
hindsight documents delete my-bank old-meeting --confirm
```

</TabItem>
</Tabs>

## Document Response Format

```json
{
  "id": "meeting-2024-03-15",
  "bank_id": "my-bank",
  "original_text": "Alice presented the Q4 roadmap...",
  "memory_unit_count": 12,
  "created_at": "2024-03-15T14:00:00Z",
  "retain_params": {
    "context": "team meeting",
    "event_date": "2024-03-15"
  }
}
```

## Use Cases

### Meeting Notes

<Tabs>
<TabItem value="python" label="Python">

```python
from datetime import date

# Store meeting notes with date-based IDs
client.retain(
    bank_id="team-memory",
    content=meeting_transcript,
    document_id=f"meeting-{date.today()}"
)
```

</TabItem>
</Tabs>

### Documentation

<Tabs>
<TabItem value="python" label="Python">

```python
from pathlib import Path

# Store docs with version tracking
docs_dir = Path("docs")
version = "1.0"

for file in docs_dir.glob("*.md"):
    client.retain(
        bank_id="docs-memory",
        content=file.read_text(),
        document_id=f"docs-{file.stem}-v{version}"
    )
```

</TabItem>
</Tabs>

### Conversation History

<Tabs>
<TabItem value="python" label="Python">

```python
# Store chat history with session IDs
client.retain(
    bank_id="chat-memory",
    content=conversation,
    document_id=f"session-{session_id}"
)
```

</TabItem>
</Tabs>

## Next Steps

- [**Entities**](./entities) — Track people, places, and concepts
- [**Operations**](./operations) — Monitor background tasks
- [**Memory Banks**](./memory-banks) — Configure bank settings
