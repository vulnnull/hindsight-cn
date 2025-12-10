---
sidebar_position: 6
---

# Memory Bank

Configure memory bank disposition, background, and behavior.
Memory banks have characteristics:
- Banks are completely isolated from each other.
- You don't need to pre-create it, Hindsight will create it for you with default settings.
- Banks have a profile that influences how they form opinions from memories. (optional)

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

:::tip Prerequisites
Make sure you've completed the [Quick Start](./quickstart) to install the client and start the server.
:::

## Creating a Memory Bank

<Tabs>
<TabItem value="python" label="Python">

```python
from hindsight_client import Hindsight

client = Hindsight(base_url="http://localhost:8888")

client.create_bank(
    bank_id="my-bank",
    name="Research Assistant",
    background="I am a research assistant specializing in machine learning",
    disposition={
        "skepticism": 4,   # Questions claims, wants evidence
        "literalism": 3,   # Balanced interpretation
        "empathy": 3       # Balanced emotional consideration
    }
)
```

</TabItem>
<TabItem value="node" label="Node.js">

```typescript
import { HindsightClient } from '@vectorize-io/hindsight-client';

const client = new HindsightClient({ baseUrl: 'http://localhost:8888' });

await client.createBank('my-bank', {
    name: 'Research Assistant',
    background: 'I am a research assistant specializing in machine learning',
    disposition: {
        skepticism: 4,
        literalism: 3,
        empathy: 3
    }
});
```

</TabItem>
<TabItem value="cli" label="CLI">

```bash
# Set background
hindsight bank background my-bank "I am a research assistant specializing in ML"

# Set disposition
hindsight bank disposition my-bank \
    --skepticism 4 \
    --literalism 3 \
    --empathy 3
```

</TabItem>
</Tabs>

## Disposition Traits

Each trait is scored 1 to 5:

| Trait | Low (1) | High (5) |
|-------|---------|----------|
| **Skepticism** | Trusting, accepts information at face value | Skeptical, questions and doubts claims |
| **Literalism** | Flexible interpretation, reads between the lines | Literal interpretation, takes things exactly as stated |
| **Empathy** | Detached, focuses on facts and logic | Empathetic, considers emotional context |

### How Traits Affect Behavior

**Skepticism** influences how the bank evaluates claims:

```python
# High skepticism (5)
"What's the source for this? Have these results been replicated?"

# Low skepticism (1)
"That sounds reasonable, let's proceed with that assumption."
```

**Literalism** affects interpretation:

```python
# High literalism (5)
"The requirement says 'users' - that means all users, no exceptions."

# Low literalism (1)
"When they say 'users', they probably mean active users in this context."
```

**Empathy** shapes how emotional context is considered:

```python
# High empathy (5)
"I understand this is frustrating. Let's find a solution that works for you."

# Low empathy (1)
"Here are the facts: Option A has 20% better performance than Option B."
```

## Background

The background is a first-person narrative providing bank context:

<Tabs>
<TabItem value="python" label="Python">

```python
client.create_bank(
    bank_id="financial-advisor",
    background="""I am a conservative financial advisor with 20 years of experience.
    I prioritize capital preservation over aggressive growth.
    I have seen multiple market crashes and believe in diversification."""
)
```

</TabItem>
<TabItem value="node" label="Node.js">

```typescript
await client.createBank('financial-advisor', {
    background: `I am a conservative financial advisor with 20 years of experience.
    I prioritize capital preservation over aggressive growth.
    I have seen multiple market crashes and believe in diversification.`
});
```

</TabItem>
</Tabs>

Background influences:
- How questions are interpreted
- Perspective in responses
- Opinion formation context

## Getting Bank Profile

<Tabs>
<TabItem value="python" label="Python">

```python
# Using the low-level API
from hindsight_client_api import ApiClient, Configuration
from hindsight_client_api.api import DefaultApi

config = Configuration(host="http://localhost:8888")
api_client = ApiClient(config)
api = DefaultApi(api_client)

profile = api.get_bank_profile("my-bank")

print(f"Name: {profile.name}")
print(f"Background: {profile.background}")
print(f"Disposition: {profile.disposition}")
```

</TabItem>
<TabItem value="node" label="Node.js">

```typescript
const profile = await client.getBankProfile('my-bank');

console.log(`Name: ${profile.name}`);
console.log(`Background: ${profile.background}`);
console.log(`Disposition:`, profile.disposition);
```

</TabItem>
<TabItem value="cli" label="CLI">

```bash
hindsight bank profile my-bank
```

</TabItem>
</Tabs>

## Default Values

If not specified, banks use neutral defaults:

```python
{
    "skepticism": 3,
    "literalism": 3,
    "empathy": 3,
    "background": ""
}
```

## Disposition Templates

Common disposition configurations:

| Use Case | Skepticism | Literalism | Empathy |
|----------|------------|------------|---------|
| **Customer Support** | 2 | 2 | 5 |
| **Code Reviewer** | 4 | 5 | 2 |
| **Legal Analyst** | 5 | 5 | 2 |
| **Therapist/Coach** | 2 | 2 | 5 |
| **Research Assistant** | 4 | 3 | 3 |
| **Neutral (default)** | 3 | 3 | 3 |

<Tabs>
<TabItem value="python" label="Python">

```python
# Customer support bank
client.create_bank(
    bank_id="support",
    background="I am a friendly customer support agent",
    disposition={
        "skepticism": 2,   # Trusting
        "literalism": 2,   # Flexible interpretation
        "empathy": 5       # Very empathetic
    }
)

# Code reviewer bank
client.create_bank(
    bank_id="reviewer",
    background="I am a thorough code reviewer focused on quality",
    disposition={
        "skepticism": 4,   # Questions assumptions
        "literalism": 5,   # Exact interpretation
        "empathy": 2       # Direct, fact-focused
    }
)
```

</TabItem>
<TabItem value="node" label="Node.js">

```typescript
// Customer support bank
await client.createBank('support', {
    background: 'I am a friendly customer support agent',
    disposition: {
        skepticism: 2,
        literalism: 2,
        empathy: 5
    }
});

// Code reviewer bank
await client.createBank('reviewer', {
    background: 'I am a thorough code reviewer focused on quality',
    disposition: {
        skepticism: 4,
        literalism: 5,
        empathy: 2
    }
});
```

</TabItem>
</Tabs>

## Bank Isolation

Each bank has:
- **Separate memories** — banks don't share memories
- **Own disposition** — traits are per-bank
- **Independent opinions** — formed from their own experiences

<Tabs>
<TabItem value="python" label="Python">

```python
# Store to bank A
client.retain(bank_id="bank-a", content="Python is great")

# Bank B doesn't see it
results = client.recall(bank_id="bank-b", query="Python")
# Returns empty
```

</TabItem>
<TabItem value="node" label="Node.js">

```typescript
// Store to bank A
await client.retain('bank-a', 'Python is great');

// Bank B doesn't see it
const results = await client.recall('bank-b', 'Python');
// Returns empty
```

</TabItem>
</Tabs>
