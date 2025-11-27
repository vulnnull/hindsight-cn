---
sidebar_position: 4
---

# Reflect: How Hindsight Reasons with Personality

When you call `reflect()`, Hindsight doesn't just retrieve facts — it **reasons** about them through the lens of the bank's unique personality, forming new opinions and generating contextual responses.

## Why Reflect?

Most AI systems can retrieve facts, but they can't **reason** about them in a consistent way. Every response is generated fresh without a stable perspective or evolving beliefs.

### The Problem

Without reflect:
- **No consistent character**: "Should we adopt remote work?" gets a different answer each time based on the LLM's randomness
- **No opinion formation**: The system never develops beliefs based on accumulated evidence
- **No reasoning context**: Responses don't reflect what the bank has learned or its perspective
- **Generic responses**: Every AI sounds the same — no personality, no point of view

### The Value

With reflect:
- **Consistent character**: A bank configured as "detail-oriented, cautious" will consistently emphasize risks and thorough planning
- **Evolving opinions**: As the bank learns more about a topic, its opinions strengthen, weaken, or change — just like a real expert
- **Contextual reasoning**: Responses reflect the bank's accumulated knowledge and perspective: "Based on what I know about your team's remote work success..."
- **Differentiated behavior**: Customer support bots sound diplomatic, code reviewers sound direct, creative assistants sound open-minded

### When to Use Reflect

| Use `recall()` when... | Use `reflect()` when... |
|------------------------|-------------------------|
| You need raw facts | You need reasoned interpretation |
| You're building your own reasoning | You want personality-consistent responses |
| You need maximum control | You want the bank to "think" for itself |
| Simple fact lookup | Forming recommendations or opinions |

**Example:**
- `recall("Alice")` → Returns all Alice facts
- `reflect("Should we hire Alice?")` → Reasons about Alice's fit based on accumulated knowledge, weighs evidence, forms opinion

---

## The Reflect Process

```
Query
  ↓
Recall relevant memories
  ↓
Load bank personality
  ↓
Reason with personality context
  ↓
Form new opinions
  ↓
Response + Sources + New Beliefs
```

---

## Personality Framework (CARA)

When you create a memory bank, you can configure its personality using **Big Five traits**. These traits influence how the bank interprets information and forms opinions:

You can also provide a natural language **background** that describes the bank's identity and perspective, which shapes how these traits are applied.

| Trait | Low | High |
|-------|-----|------|
| **Openness** | Prefers proven methods | Embraces new ideas |
| **Conscientiousness** | Flexible, spontaneous | Systematic, organized |
| **Extraversion** | Independent | Collaborative |
| **Agreeableness** | Direct, analytical | Diplomatic, harmonious |
| **Neuroticism** | Calm, optimistic | Risk-aware, cautious |

### Background: Natural Language Identity

Beyond numeric traits, you can provide a natural language **background** that describes the bank's identity:

```python
client.create_bank(
    bank_id="my-bank",
    background="I am a senior software architect with 15 years of distributed "
               "systems experience. I prefer simplicity over cutting-edge technology.",
    personality={
        "openness": 0.3,  # Prefers proven methods
        "conscientiousness": 0.9,  # Highly organized
        # ... other traits
    }
)
```

The background provides context that shapes how personality traits are applied:
- "I prefer simplicity" + low openness → consistently favors established solutions
- "15 years experience" → responses reference this expertise
- First-person perspective → creates consistent voice

### Bias Strength

The `bias_strength` parameter (0-1) controls how much personality influences reasoning:

- **0.0**: Purely evidence-based
- **0.5**: Balanced personality and evidence
- **1.0**: Strongly personality-driven

---

## Opinion Formation

When `reflect()` encounters a question that warrants forming an opinion, personality shapes the response.

### Same Facts, Different Opinions

Two banks with different personalities, given identical facts about remote work:

**Bank A** (high openness, low conscientiousness):
> "Remote work unlocks creative flexibility and spontaneous innovation. The freedom to work from anywhere enables breakthrough thinking."

**Bank B** (low openness, high conscientiousness):
> "Remote work lacks the structure and accountability needed for consistent performance. In-person collaboration is more reliable."

**Same facts → Different conclusions** because personality shapes interpretation.

---

## Opinion Evolution

Opinions aren't static — they evolve as new evidence arrives:

```
Day 1: retain("Python is widely used in ML")
       → Opinion formed: "Python is best for data science" (confidence: 0.70)

Day 2: retain("98% of ML engineers use Python")
       → Opinion reinforced: "Python is best for data science" (confidence: 0.85)

Day 3: retain("Julia is 10x faster for numerical computing")
       → Opinion revised: "Python is best for data science due to ecosystem,
                           though Julia excels in performance" (confidence: 0.75)

Day 4: retain("Rust ML libraries growing rapidly")
       → Opinion updated: "Python remains dominant but Rust is gaining ground
                           for production systems" (confidence: 0.60)
```

This **continuous learning** ensures opinions stay current.

---

## Personality Presets by Use Case

Different use cases benefit from different personality configurations:

| Use Case | Recommended Traits | Why |
|----------|-------------------|-----|
| **Customer Support** | High agreeableness<br/>Low neuroticism | Diplomatic, calm under pressure |
| **Code Review** | High conscientiousness<br/>Low agreeableness | Detail-oriented, direct feedback |
| **Creative Writing** | High openness<br/>High extraversion | Embraces novelty, expressive |
| **Risk Analysis** | High neuroticism<br/>High conscientiousness | Risk-aware, methodical |
| **Research Assistant** | High openness<br/>High conscientiousness | Curious, thorough |

---

## What You Get from Reflect

When you call `reflect()`:

**Returns:**
- **Response text** — Personality-influenced answer
- **Based on** — Which memories were used (with relevance scores)
- **New opinions** — Any beliefs formed during reasoning (with confidence)

**Example:**
```json
{
  "text": "Based on Alice's ML expertise and her work at Google,
           she'd be an excellent fit for the research team lead position...",
  "based_on": {
    "world": [
      {"text": "Alice works at Google...", "weight": 0.95},
      {"text": "Alice specializes in ML...", "weight": 0.88}
    ]
  },
  "new_opinions": [
    {"text": "Alice would excel as research team lead", "confidence": 0.82}
  ]
}
```

---

## Why Personality Matters

Without personality, all AI assistants sound the same. With personality:

- **Customer support bots** can be diplomatic and empathetic
- **Code review assistants** can be direct and thorough
- **Creative assistants** can be open to unconventional ideas
- **Risk analysts** can be appropriately cautious

Personality creates **consistent character** across conversations while allowing opinions to **evolve with evidence**.

---

## Next Steps

- [**Retain**](./retain) — How rich facts are stored
- [**Recall**](./retrieval) — How multi-strategy search works
- [API Reference: Reflect](/developer/api/think) — Code examples and usage
