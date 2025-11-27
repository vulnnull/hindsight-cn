---
sidebar_position: 5
---

# Opinions

How memory banks form, store, and evolve beliefs.

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

## What Are Opinions?

Opinions are beliefs formed by the memory bank based on evidence and personality. Unlike world facts (objective information received) or agent facts (actions taken), opinions are **judgments** with confidence scores.

| Type | Example | Confidence |
|------|---------|------------|
| World Fact | "Python was created in 1991" | — |
| Memory bank Fact | "I recommended Python to Bob" | — |
| Opinion | "Python is the best language for data science" | 0.85 |

## How Opinions Form

Opinions are created during `think` operations when the memory bank:
1. Retrieves relevant facts
2. Applies personality traits
3. Forms a judgment
4. Assigns a confidence score

```mermaid
graph LR
    F[Facts] --> P[Personality Filter]
    P --> J[Judgment]
    J --> O[Opinion + Confidence]
    O --> S[(Store)]
```

<Tabs>
<TabItem value="python" label="Python">

```python
# Ask a question that might form an opinion
answer = client.think(
    agent_id="my-agent",
    query="What do you think about functional programming?"
)

# Check if new opinions were formed
for opinion in answer["new_opinions"]:
    print(f"New opinion: {opinion['text']}")
    print(f"Confidence: {opinion['confidence']}")
```

</TabItem>
</Tabs>

## Searching Opinions

<Tabs>
<TabItem value="python" label="Python">

```python
# Search only opinions
opinions = client.search_memories(
    agent_id="my-agent",
    query="programming languages",
    fact_type=["opinion"]
)

for op in opinions:
    print(f"{op['text']} (confidence: {op['confidence_score']:.2f})")
```

</TabItem>
<TabItem value="cli" label="CLI">

```bash
hindsight memory search my-agent "programming" --fact-type opinion
```

</TabItem>
</Tabs>

## Opinion Evolution

Opinions change as new evidence arrives:

| Evidence Type | Effect |
|---------------|--------|
| **Reinforcing** | Confidence increases (+0.1) |
| **Weakening** | Confidence decreases (-0.15) |
| **Contradicting** | Opinion revised, confidence reset |

**Example evolution:**

```
t=0: "Python is best for data science" (0.70)
     ↓ New evidence: Python dominates ML libraries
t=1: "Python is best for data science" (0.85)
     ↓ New evidence: Julia is 10x faster for numerical computing
t=2: "Python is best for data science, though Julia is faster" (0.75)
     ↓ New evidence: Most teams still use Python
t=3: "Python is best for data science" (0.82)
```

## Personality Influence

Different personalities form different opinions from the same facts:

<Tabs>
<TabItem value="python" label="Python">

```python
# Create two memory banks with different personalities
client.create_agent(
    agent_id="open-minded",
    personality={"openness": 0.9, "conscientiousness": 0.3, "bias_strength": 0.7}
)

client.create_agent(
    agent_id="conservative",
    personality={"openness": 0.2, "conscientiousness": 0.9, "bias_strength": 0.7}
)

# Store the same facts to both
facts = [
    "Rust has better memory safety than C++",
    "C++ has a larger ecosystem and more libraries",
    "Rust compile times are longer than C++"
]
for fact in facts:
    client.store(agent_id="open-minded", content=fact)
    client.store(agent_id="conservative", content=fact)

# Ask both the same question
q = "Should we rewrite our C++ codebase in Rust?"

answer1 = client.think(agent_id="open-minded", query=q)
# Likely: "Yes, Rust's safety benefits outweigh migration costs"

answer2 = client.think(agent_id="conservative", query=q)
# Likely: "No, C++'s ecosystem and our team's expertise make it the safer choice"
```

</TabItem>
</Tabs>

## Bias Strength

The `bias_strength` parameter (0-1) controls how much personality influences opinions:

| Value | Behavior |
|-------|----------|
| 0.0 | Pure evidence-based reasoning |
| 0.5 | Balanced personality + evidence |
| 1.0 | Strongly personality-driven |

```python
# Evidence-focused agent
client.create_agent(
    agent_id="analyst",
    personality={"bias_strength": 0.2}  # Low bias
)

# Personality-driven agent
client.create_agent(
    agent_id="advisor",
    personality={"bias_strength": 0.8}  # High bias
)
```

## Opinions in Think Responses

When `think` uses opinions, they appear in `based_on`:

```python
answer = client.think(agent_id="my-agent", query="What language should I learn?")

print("World facts used:")
for f in answer["based_on"]["world"]:
    print(f"  {f['text']}")

print("\nOpinions used:")
for o in answer["based_on"]["opinion"]:
    print(f"  {o['text']} (confidence: {o['confidence_score']})")
```

## Confidence Thresholds

Opinions below a confidence threshold may be:
- Excluded from responses
- Marked as uncertain
- Revised more easily

```python
# Low confidence opinions are held loosely
# "I think Python might be good for this" (0.45)

# High confidence opinions are stated firmly
# "Python is definitely the right choice" (0.92)
```
