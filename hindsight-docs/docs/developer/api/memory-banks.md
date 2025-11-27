---
sidebar_position: 6
---

# Memory bank Identity

Configure memory bank personality, background, and behavior.

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

## Creating an Memory bank

<Tabs>
<TabItem value="python" label="Python">

```python
from hindsight_client import Hindsight

client = Hindsight(base_url="http://localhost:8888")

client.create_agent(
    agent_id="my-agent",
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
import { OpenAPI, ManagementService } from '@hindsight/client';

OpenAPI.BASE = 'http://localhost:8888';

await ManagementService.createAgentApiAgentsAgentIdPut('my-agent', {
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
hindsight agent background my-agent "I am a research assistant specializing in ML"

# Set personality
hindsight memory bank personality my-agent \
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

**Openness** influences how the memory bank weighs new vs. established ideas:

```python
# High openness agent
"Let's try this new framework—it looks promising!"

# Low openness agent
"Let's stick with the proven solution we know works."
```

**Conscientiousness** affects structure and thoroughness:

```python
# High conscientiousness agent
"Here's a detailed, step-by-step analysis..."

# Low conscientiousness agent
"Quick take: this should work, let's try it."
```

**Extraversion** shapes collaboration preferences:

```python
# High extraversion agent
"We should get the team together to discuss this."

# Low extraversion agent
"I'll analyze this independently and share my findings."
```

**Agreeableness** affects how disagreements are handled:

```python
# High agreeableness agent
"That's a valid point. Perhaps we can find a middle ground..."

# Low agreeableness agent
"Actually, the data doesn't support that conclusion."
```

**Neuroticism** influences risk assessment:

```python
# High neuroticism agent
"We should consider what could go wrong here..."

# Low neuroticism agent
"The risks seem manageable, let's proceed."
```

## Background

The background is a first-person narrative providing agent context:

<Tabs>
<TabItem value="python" label="Python">

```python
client.create_agent(
    agent_id="financial-advisor",
    background="""I am a conservative financial advisor with 20 years of experience.
    I prioritize capital preservation over aggressive growth.
    I have seen multiple market crashes and believe in diversification."""
)
```

</TabItem>
</Tabs>

Background influences:
- How questions are interpreted
- Perspective in responses
- Opinion formation context

### Merging Background

New background information is merged intelligently:

<Tabs>
<TabItem value="python" label="Python">

```python
# Original background
client.create_agent(
    agent_id="assistant",
    background="I am a helpful AI assistant"
)

# Add more context (merged, not replaced)
client.update_background(
    agent_id="assistant",
    background="I specialize in Python programming"
)

# Result: "I am a helpful AI assistant. I specialize in Python programming."
```

</TabItem>
</Tabs>

Merging rules:
- **Conflicts**: New overwrites old
- **Additions**: Non-conflicting info is added
- **Normalization**: "You are..." → "I am..."

## Getting Memory bank Profile

<Tabs>
<TabItem value="python" label="Python">

```python
profile = client.get_profile(agent_id="my-agent")

print(f"Background: {profile['background']}")
print(f"Personality: {profile['personality']}")
```

</TabItem>
<TabItem value="cli" label="CLI">

```bash
hindsight memory bank profile my-agent
```

</TabItem>
</Tabs>

## Updating Personality

<Tabs>
<TabItem value="python" label="Python">

```python
client.update_personality(
    agent_id="my-agent",
    openness=0.9,
    conscientiousness=0.8
)
```

</TabItem>
</Tabs>

## Listing Memory banks

<Tabs>
<TabItem value="python" label="Python">

```python
memory banks = client.list_agents()
for agent in memory banks:
    print(agent["agent_id"])
```

</TabItem>
<TabItem value="cli" label="CLI">

```bash
hindsight agent list
```

</TabItem>
</Tabs>

## Default Values

If not specified, memory banks use neutral defaults:

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
# Customer support agent
client.create_agent(
    agent_id="support",
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

# Code reviewer agent
client.create_agent(
    agent_id="reviewer",
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
</Tabs>

## Memory bank Isolation

Each agent has:
- **Separate memories** — memory banks don't share memories
- **Own personality** — traits are per-agent
- **Independent opinions** — formed from their own experiences

```python
# Store to agent A
client.store(agent_id="agent-a", content="Python is great")

# Memory bank B doesn't see it
results = client.search(agent_id="agent-b", query="Python")
# Returns empty
```
