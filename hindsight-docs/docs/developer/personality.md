---
sidebar_position: 4
---

# Personality

Hindsight's personality framework (CARA) uses the Big Five model to influence how agents form and express opinions.

## Big Five Traits

Each trait is scored 0.0 to 1.0:

| Trait | Low (0.0) | High (1.0) |
|-------|-----------|------------|
| **Openness** | Conventional, practical | Curious, creative |
| **Conscientiousness** | Flexible, spontaneous | Organized, disciplined |
| **Extraversion** | Reserved, reflective | Outgoing, energetic |
| **Agreeableness** | Analytical, direct | Cooperative, diplomatic |
| **Neuroticism** | Calm, stable | Risk-aware, cautious |

## Bias Strength

The `bias_strength` parameter (0.0-1.0) controls personality influence:

- **0.0**: Purely evidence-based reasoning
- **0.5**: Balanced personality/evidence mix
- **1.0**: Strongly personality-driven opinions

## Opinion Formation

When agents encounter information:

1. Evidence is retrieved from memory
2. Personality traits weight different aspects
3. Confidence score reflects evidence + personality alignment

**Example**: Two agents given the same facts about remote work:

**Agent A** (openness=0.9, conscientiousness=0.2):
> "Remote work unlocks creative flexibility and spontaneous innovation."

**Agent B** (openness=0.2, conscientiousness=0.9):
> "Remote work lacks the structure and accountability needed for consistent performance."

Same facts, different conclusions based on personality.

## Opinion Reinforcement

Opinions evolve as new evidence arrives:

| Evidence Type | Effect |
|---------------|--------|
| **Reinforcing** | Confidence increases (+0.1) |
| **Weakening** | Confidence decreases (-0.15) |
| **Contradicting** | Opinion revised, confidence reset |

**Example Evolution**:

```
t=0: "Python is best for data science" (0.70)
t=1: New evidence: Python dominates ML → (0.85)
t=2: New evidence: Julia is 10x faster → (0.75, text revised)
t=3: New evidence: Rust taking over production → (0.55, text revised)
```

## Agent Profile

### Setting Personality

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

<Tabs>
<TabItem value="python" label="Python">

```python
from hindsight_client import Hindsight

client = Hindsight(base_url="http://localhost:8888")

client.create_agent(
    agent_id="my-agent",
    name="Creative Assistant",
    background="I am a creative AI interested in new ideas",
    personality={
        "openness": 0.8,
        "conscientiousness": 0.6,
        "extraversion": 0.5,
        "agreeableness": 0.7,
        "neuroticism": 0.3,
        "bias_strength": 0.7
    }
)
```

</TabItem>
<TabItem value="node" label="Node.js">

```typescript
import { OpenAPI, ManagementService } from '@hindsight/client';

OpenAPI.BASE = 'http://localhost:8888';

await ManagementService.createAgentApiAgentsAgentIdPut('my-agent', {
    name: 'Creative Assistant',
    background: 'I am a creative AI interested in new ideas',
    personality: {
        openness: 0.8,
        conscientiousness: 0.6,
        extraversion: 0.5,
        agreeableness: 0.7,
        neuroticism: 0.3,
        bias_strength: 0.7
    }
});
```

</TabItem>
<TabItem value="cli" label="CLI">

```bash
hindsight agent background my-agent "I am a creative AI interested in new ideas"
hindsight agent personality my-agent \
    --openness 0.8 \
    --conscientiousness 0.6 \
    --extraversion 0.5 \
    --agreeableness 0.7 \
    --neuroticism 0.3 \
    --bias-strength 0.7
```

</TabItem>
</Tabs>

### Background

First-person narrative providing agent context:

```python
client.create_agent(
    agent_id="my-agent",
    background="I am a senior software architect with 15 years of distributed systems experience. I prefer simplicity over cutting-edge technology."
)
```

Background influences:
- How questions are interpreted
- Perspective in responses
- Opinion formation context

### Background Merging

New background info is merged intelligently:

- **Conflicts**: New overwrites old
- **Additions**: Non-conflicting info is added
- **Normalization**: Converts to first-person ("You are..." → "I am...")

## Default Personality

If unspecified, agents default to neutral (0.5):

```json
{
  "openness": 0.5,
  "conscientiousness": 0.5,
  "extraversion": 0.5,
  "agreeableness": 0.5,
  "neuroticism": 0.5,
  "bias_strength": 0.5
}
```

## Use Case Examples

| Use Case | Recommended Traits |
|----------|-------------------|
| Customer Support | High agreeableness, low neuroticism |
| Code Review | High conscientiousness, low agreeableness |
| Creative Writing | High openness, high extraversion |
| Risk Analysis | High neuroticism, high conscientiousness |
