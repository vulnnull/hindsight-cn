---
sidebar_position: 7
---

# Entities

Entities are the people, organizations, places, and concepts that Hindsight automatically tracks across your memory bank.

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

:::tip Prerequisites
Make sure you've [installed Hindsight](./installation) and understand [how retain works](./retain).
:::

## What Are Entities?

When you retain information, Hindsight automatically identifies and tracks entities:

```python
client.retain(
    bank_id="my-bank",
    content="Alice works at Google in Mountain View. She specializes in TensorFlow."
)
```

**Entities extracted:**
- **Alice** (person)
- **Google** (organization)
- **Mountain View** (location)
- **TensorFlow** (product)

## Entity Resolution

Multiple mentions are unified into a single entity:

- "Alice" + "Alice Chen" + "Alice C." → one person
- "Bob" + "Robert Chen" → one person (nickname)
- Context-aware: "Apple (company)" vs "apple (fruit)"

## List Entities

Get all entities tracked in a memory bank:

<Tabs>
<TabItem value="python" label="Python">

```python
# List all entities
entities = client.list_entities(bank_id="my-bank")

for entity in entities:
    print(f"{entity['name']}: {entity['mention_count']} mentions")

# List with filters
entities = client.list_entities(
    bank_id="my-bank",
    limit=50,
    offset=0
)
```

</TabItem>
<TabItem value="node" label="Node.js">

```javascript
// List all entities
const entities = await client.listEntities({
    bankId: 'my-bank'
});

entities.forEach(e => {
    console.log(`${e.name}: ${e.mentionCount} mentions`);
});

// List with filters
const filtered = await client.listEntities({
    bankId: 'my-bank',
    limit: 50,
    offset: 0
});
```

</TabItem>
<TabItem value="cli" label="CLI">

```bash
# List all entities
hindsight entities list my-bank

# With limit
hindsight entities list my-bank --limit 50
```

</TabItem>
</Tabs>

## Get Entity Details

Retrieve detailed information about a specific entity:

<Tabs>
<TabItem value="python" label="Python">

```python
# Get entity state (observations + related facts)
entity = client.get_entity(
    bank_id="my-bank",
    entity_id="entity-uuid"
)

print(f"Entity: {entity['name']}")
print(f"First seen: {entity['first_seen']}")
print(f"Mentions: {entity['mention_count']}")

# Observations (synthesized summaries)
for obs in entity['observations']:
    print(f"  - {obs['text']}")

# Include related facts
entity = client.get_entity(
    bank_id="my-bank",
    entity_id="entity-uuid",
    include_facts=True,
    max_facts=20
)

for fact in entity['facts']:
    print(f"  [{fact['occurred_at']}] {fact['text']}")
```

</TabItem>
<TabItem value="node" label="Node.js">

```javascript
// Get entity state
const entity = await client.getEntity({
    bankId: 'my-bank',
    entityId: 'entity-uuid'
});

console.log(`Entity: ${entity.name}`);
console.log(`First seen: ${entity.firstSeen}`);
console.log(`Mentions: ${entity.mentionCount}`);

// Observations
entity.observations.forEach(obs => {
    console.log(`  - ${obs.text}`);
});

// Include related facts
const withFacts = await client.getEntity({
    bankId: 'my-bank',
    entityId: 'entity-uuid',
    includeFacts: true,
    maxFacts: 20
});
```

</TabItem>
<TabItem value="cli" label="CLI">

```bash
# Get entity details
hindsight entities get my-bank entity-uuid

# With related facts
hindsight entities get my-bank entity-uuid --include-facts
```

</TabItem>
</Tabs>

## Entity Observations

Observations are high-level summaries automatically synthesized from multiple facts:

**Facts about Alice:**
- "Alice works at Google"
- "Alice is a software engineer"
- "Alice specializes in ML"

**Observation created:**
- "Alice is a software engineer at Google specializing in ML"

Observations are generated in the background after retaining information.

## Search Entities

Find entities by name or related terms:

<Tabs>
<TabItem value="python" label="Python">

```python
# Search by name
entities = client.search_entities(
    bank_id="my-bank",
    query="Alice"
)

# Fuzzy matching handles variations
entities = client.search_entities(
    bank_id="my-bank",
    query="Alic"  # Matches "Alice", "Alicia", etc.
)
```

</TabItem>
<TabItem value="node" label="Node.js">

```javascript
// Search by name
const entities = await client.searchEntities({
    bankId: 'my-bank',
    query: 'Alice'
});

// Fuzzy matching
const fuzzy = await client.searchEntities({
    bankId: 'my-bank',
    query: 'Alic'
});
```

</TabItem>
<TabItem value="cli" label="CLI">

```bash
# Search entities
hindsight entities search my-bank "Alice"
```

</TabItem>
</Tabs>

## Entity Response Format

```json
{
  "id": "entity-uuid",
  "name": "Alice Chen",
  "canonical_name": "Alice Chen",
  "first_seen": "2024-01-15T10:30:00Z",
  "last_seen": "2024-03-20T14:22:00Z",
  "mention_count": 47,
  "observations": [
    {
      "text": "Alice is a software engineer at Google specializing in ML",
      "created_at": "2024-03-20T15:00:00Z"
    }
  ]
}
```

## Next Steps

- [**Memory Banks**](./memory-banks) — Configure bank personality
- [**Documents**](./documents) — Track document sources
- [**Operations**](./operations) — Monitor background tasks
