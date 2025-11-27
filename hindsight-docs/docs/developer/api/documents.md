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
# Retain with document ID
client.retain(
    bank_id="my-bank",
    content="Alice presented the Q4 roadmap...",
    document_id="meeting-2024-03-15"
)

# Batch retain for a document
client.retain_batch(
    bank_id="my-bank",
    contents=[
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

```javascript
// Retain with document ID
await client.retain({
    bankId: 'my-bank',
    content: 'Alice presented the Q4 roadmap...',
    documentId: 'meeting-2024-03-15'
});

// Batch retain
await client.retainBatch({
    bankId: 'my-bank',
    contents: [
        { content: 'Item 1: Product launch delayed to Q2' },
        { content: 'Item 2: New hiring targets announced' },
        { content: 'Item 3: Budget approved for ML team' }
    ],
    documentId: 'meeting-2024-03-15'
});
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

```javascript
// Original
await client.retain({
    bankId: 'my-bank',
    content: 'Project deadline: March 31',
    documentId: 'project-plan'
});

// Update
await client.retain({
    bankId: 'my-bank',
    content: 'Project deadline: April 15 (extended)',
    documentId: 'project-plan'
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
# List all documents
documents = client.list_documents(bank_id="my-bank")

for doc in documents:
    print(f"{doc['id']}: {doc['memory_count']} memories")
    print(f"  Created: {doc['created_at']}")
    print(f"  Updated: {doc['updated_at']}")

# With pagination
documents = client.list_documents(
    bank_id="my-bank",
    limit=50,
    offset=0
)
```

</TabItem>
<TabItem value="node" label="Node.js">

```javascript
// List all documents
const documents = await client.listDocuments({
    bankId: 'my-bank'
});

documents.forEach(doc => {
    console.log(`${doc.id}: ${doc.memoryCount} memories`);
    console.log(`  Created: ${doc.createdAt}`);
    console.log(`  Updated: ${doc.updatedAt}`);
});
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

Retrieve a specific document with its memories:

<Tabs>
<TabItem value="python" label="Python">

```python
# Get document
doc = client.get_document(
    bank_id="my-bank",
    document_id="meeting-2024-03-15"
)

print(f"Document: {doc['id']}")
print(f"Original text: {doc['original_text'][:200]}...")
print(f"Memories: {doc['memory_count']}")

# Get with memories
doc = client.get_document(
    bank_id="my-bank",
    document_id="meeting-2024-03-15",
    include_memories=True
)

for memory in doc['memories']:
    print(f"  - {memory['text']}")
```

</TabItem>
<TabItem value="node" label="Node.js">

```javascript
// Get document
const doc = await client.getDocument({
    bankId: 'my-bank',
    documentId: 'meeting-2024-03-15'
});

console.log(`Document: ${doc.id}`);
console.log(`Memories: ${doc.memoryCount}`);

// Get with memories
const withMemories = await client.getDocument({
    bankId: 'my-bank',
    documentId: 'meeting-2024-03-15',
    includeMemories: true
});
```

</TabItem>
<TabItem value="cli" label="CLI">

```bash
# Get document
hindsight documents get my-bank meeting-2024-03-15

# With memories
hindsight documents get my-bank meeting-2024-03-15 --include-memories
```

</TabItem>
</Tabs>

## Delete Documents

Remove a document and all its memories:

<Tabs>
<TabItem value="python" label="Python">

```python
# Delete document (removes all associated memories)
client.delete_document(
    bank_id="my-bank",
    document_id="old-meeting"
)

# Bulk delete
for doc_id in ["old-1", "old-2", "old-3"]:
    client.delete_document(bank_id="my-bank", document_id=doc_id)
```

</TabItem>
<TabItem value="node" label="Node.js">

```javascript
// Delete document
await client.deleteDocument({
    bankId: 'my-bank',
    documentId: 'old-meeting'
});

// Bulk delete
for (const docId of ['old-1', 'old-2', 'old-3']) {
    await client.deleteDocument({
        bankId: 'my-bank',
        documentId: docId
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
  "content_hash": "sha256:abc123...",
  "memory_count": 12,
  "created_at": "2024-03-15T14:00:00Z",
  "updated_at": "2024-03-15T14:00:00Z",
  "metadata": {}
}
```

## Use Cases

### Meeting Notes

```python
# Store meeting notes with date-based IDs
client.retain(
    bank_id="team-memory",
    content=meeting_transcript,
    document_id=f"meeting-{date.today()}"
)
```

### Documentation

```python
# Store docs with version tracking
for file in docs_dir.glob("*.md"):
    client.retain(
        bank_id="docs-memory",
        content=file.read_text(),
        document_id=f"docs-{file.stem}-v{version}"
    )
```

### Conversation History

```python
# Store chat history with session IDs
client.retain(
    bank_id="chat-memory",
    content=conversation,
    document_id=f"session-{session_id}"
)
```

## Next Steps

- [**Entities**](./entities) — Track people, places, and concepts
- [**Operations**](./operations) — Monitor background tasks
- [**Memory Banks**](./memory-banks) — Configure bank settings
