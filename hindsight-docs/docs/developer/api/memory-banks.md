---
sidebar_position: 6
---

# Memory Bank Identity

Configure memory bank personality, background, and behavior.

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

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
    personality={
        "openness": 0.8,
        "conscientiousness": 0.7,
        "extraversion": 0.5,
        "agreeableness": 0.6,
        "neuroticism": 0.3,
        "bias_strength": 0.5
    }
)
```

</TabItem>
<TabItem value="node" label="Node.js">

```typescript
import { HindsightClient } from '@hindsight/client';

const client = new HindsightClient({ baseUrl: 'http://localhost:8888' });

await client.createBank('my-bank', {
    name: 'Research Assistant',
    background: 'I am a research assistant specializing in machine learning',
    personality: {
        openness: 0.8,
        conscientiousness: 0.7,
        extraversion: 0.5,
        agreeableness: 0.6,
        neuroticism: 0.3,
        bias_strength: 0.5
    }
});
```

</TabItem>
<TabItem value="cli" label="CLI">

```bash
# Set background
hindsight agent background my-bank "I am a research assistant specializing in ML"

# Set personality
hindsight agent personality my-bank \
    --openness 0.8 \
    --conscientiousness 0.7 \
    --extraversion 0.5 \
    --agreeableness 0.6 \
    --neuroticism 0.3 \
    --bias-strength 0.5
```

</TabItem>
</Tabs>

## Personality Traits (Big Five)

Each trait is scored 0.0 to 1.0:

| Trait | Low (0.0) | High (1.0) |
|-------|-----------|------------|
| **Openness** | Conventional, prefers proven methods | Curious, embraces new ideas |
| **Conscientiousness** | Flexible, spontaneous | Organized, systematic |
| **Extraversion** | Reserved, independent | Outgoing, collaborative |
| **Agreeableness** | Direct, analytical | Cooperative, diplomatic |
| **Neuroticism** | Calm, optimistic | Risk-aware, cautious |

### How Traits Affect Behavior

**Openness** influences how the bank weighs new vs. established ideas:

```python
# High openness bank
"Let's try this new framework—it looks promising!"

# Low openness bank
"Let's stick with the proven solution we know works."
```

**Conscientiousness** affects structure and thoroughness:

```python
# High conscientiousness bank
"Here's a detailed, step-by-step analysis..."

# Low conscientiousness bank
"Quick take: this should work, let's try it."
```

**Extraversion** shapes collaboration preferences:

```python
# High extraversion bank
"We should get the team together to discuss this."

# Low extraversion bank
"I'll analyze this independently and share my findings."
```

**Agreeableness** affects how disagreements are handled:

```python
# High agreeableness bank
"That's a valid point. Perhaps we can find a middle ground..."

# Low agreeableness bank
"Actually, the data doesn't support that conclusion."
```

**Neuroticism** influences risk assessment:

```python
# High neuroticism bank
"We should consider what could go wrong here..."

# Low neuroticism bank
"The risks seem manageable, let's proceed."
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
print(f"Personality: {profile.personality}")
```

</TabItem>
<TabItem value="node" label="Node.js">

```typescript
const profile = await client.getBankProfile('my-bank');

console.log(`Name: ${profile.name}`);
console.log(`Background: ${profile.background}`);
console.log(`Personality:`, profile.personality);
```

</TabItem>
<TabItem value="cli" label="CLI">

```bash
hindsight agent profile my-bank
```

</TabItem>
</Tabs>

## Default Values

If not specified, banks use neutral defaults:

```python
{
    "openness": 0.5,
    "conscientiousness": 0.5,
    "extraversion": 0.5,
    "agreeableness": 0.5,
    "neuroticism": 0.5,
    "bias_strength": 0.5,
    "background": ""
}
```

## Personality Templates

Common personality configurations:

| Use Case | O | C | E | A | N | Bias |
|----------|---|---|---|---|---|------|
| **Customer Support** | 0.5 | 0.7 | 0.6 | 0.9 | 0.3 | 0.4 |
| **Code Reviewer** | 0.4 | 0.9 | 0.3 | 0.4 | 0.5 | 0.6 |
| **Creative Writer** | 0.9 | 0.4 | 0.7 | 0.6 | 0.5 | 0.7 |
| **Risk Analyst** | 0.3 | 0.9 | 0.3 | 0.4 | 0.8 | 0.6 |
| **Research Assistant** | 0.8 | 0.8 | 0.4 | 0.5 | 0.4 | 0.5 |
| **Neutral (default)** | 0.5 | 0.5 | 0.5 | 0.5 | 0.5 | 0.5 |

<Tabs>
<TabItem value="python" label="Python">

```python
# Customer support bank
client.create_bank(
    bank_id="support",
    background="I am a friendly customer support agent",
    personality={
        "openness": 0.5,
        "conscientiousness": 0.7,
        "extraversion": 0.6,
        "agreeableness": 0.9,  # Very diplomatic
        "neuroticism": 0.3,    # Calm under pressure
        "bias_strength": 0.4
    }
)

# Code reviewer bank
client.create_bank(
    bank_id="reviewer",
    background="I am a thorough code reviewer focused on quality",
    personality={
        "openness": 0.4,       # Prefers proven patterns
        "conscientiousness": 0.9,  # Very thorough
        "extraversion": 0.3,
        "agreeableness": 0.4,  # Direct feedback
        "neuroticism": 0.5,
        "bias_strength": 0.6
    }
)
```

</TabItem>
<TabItem value="node" label="Node.js">

```typescript
// Customer support bank
await client.createBank('support', {
    background: 'I am a friendly customer support agent',
    personality: {
        openness: 0.5,
        conscientiousness: 0.7,
        extraversion: 0.6,
        agreeableness: 0.9,
        neuroticism: 0.3,
        bias_strength: 0.4
    }
});

// Code reviewer bank
await client.createBank('reviewer', {
    background: 'I am a thorough code reviewer focused on quality',
    personality: {
        openness: 0.4,
        conscientiousness: 0.9,
        extraversion: 0.3,
        agreeableness: 0.4,
        neuroticism: 0.5,
        bias_strength: 0.6
    }
});
```

</TabItem>
</Tabs>

## Bank Isolation

Each bank has:
- **Separate memories** — banks don't share memories
- **Own personality** — traits are per-bank
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
