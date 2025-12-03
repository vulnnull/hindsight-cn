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

<Tabs>
<TabItem value="python" label="Python">

```python
from hindsight_client import Hindsight

client = Hindsight(base_url="http://localhost:8888")

client.retain(
    bank_id="my-bank",
    content="Alice works at Google in Mountain View. She specializes in TensorFlow."
)
```

</TabItem>
<TabItem value="node" label="Node.js">

```typescript
import { HindsightClient } from '@hindsight/client';

const client = new HindsightClient({ baseUrl: 'http://localhost:8888' });

await client.retain('my-bank', 'Alice works at Google in Mountain View. She specializes in TensorFlow.');
```

</TabItem>
</Tabs>

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
# Using the low-level API
from hindsight_client_api import ApiClient, Configuration
from hindsight_client_api.api import DefaultApi

config = Configuration(host="http://localhost:8888")
api_client = ApiClient(config)
api = DefaultApi(api_client)

# List all entities
response = api.list_entities(bank_id="my-bank")

for entity in response.items:
    print(f"{entity.canonical_name}: {entity.mention_count} mentions")

# List with pagination
response = api.list_entities(
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

// List all entities
const response = await sdk.listEntities({
    client: apiClient,
    path: { bank_id: 'my-bank' }
});

for (const entity of response.data.items) {
    console.log(`${entity.canonical_name}: ${entity.mention_count} mentions`);
}

// List with pagination
const paginated = await sdk.listEntities({
    client: apiClient,
    path: { bank_id: 'my-bank' },
    query: { limit: 50, offset: 0 }
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
# Get entity details with observations
entity = api.get_entity(
    bank_id="my-bank",
    entity_id="entity-uuid"
)

print(f"Entity: {entity.canonical_name}")
print(f"First seen: {entity.first_seen}")
print(f"Mentions: {entity.mention_count}")

# Observations (synthesized summaries)
for obs in entity.observations:
    print(f"  - {obs.text}")
```

</TabItem>
<TabItem value="node" label="Node.js">

```typescript
// Get entity details
const entity = await sdk.getEntity({
    client: apiClient,
    path: { bank_id: 'my-bank', entity_id: 'entity-uuid' }
});

console.log(`Entity: ${entity.data.canonical_name}`);
console.log(`First seen: ${entity.data.first_seen}`);
console.log(`Mentions: ${entity.data.mention_count}`);

// Observations
for (const obs of entity.data.observations) {
    console.log(`  - ${obs.text}`);
}
```

</TabItem>
<TabItem value="cli" label="CLI">

```bash
# Get entity details
hindsight entities get my-bank entity-uuid
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

## Regenerate Observations

Force regeneration of entity observations:

<Tabs>
<TabItem value="python" label="Python">

```python
# Regenerate observations for an entity
api.regenerate_entity_observations(
    bank_id="my-bank",
    entity_id="entity-uuid"
)
```

</TabItem>
<TabItem value="node" label="Node.js">

```typescript
// Regenerate observations
await sdk.regenerateEntityObservations({
    client: apiClient,
    path: { bank_id: 'my-bank', entity_id: 'entity-uuid' }
});
```

</TabItem>
</Tabs>

## Entity Response Format

```json
{
  "id": "entity-uuid",
  "canonical_name": "Alice Chen",
  "first_seen": "2024-01-15T10:30:00Z",
  "last_seen": "2024-03-20T14:22:00Z",
  "mention_count": 47,
  "observations": [
    {
      "text": "Alice is a software engineer at Google specializing in ML",
      "mentioned_at": "2024-03-20T15:00:00Z"
    }
  ]
}
```

## Next Steps

- [**Memory Banks**](./memory-banks) — Configure bank personality
- [**Documents**](./documents) — Track document sources
- [**Operations**](./operations) — Monitor background tasks
