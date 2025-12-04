---
sidebar_position: 4
---

# Reflect: How Hindsight Reasons with Disposition

When you call `reflect()`, Hindsight doesn't just retrieve facts — it **reasons** about them through the lens of the bank's unique disposition, forming new opinions and generating contextual responses.

## Why Reflect?

Most AI systems can retrieve facts, but they can't **reason** about them in a consistent way. Every response is generated fresh without a stable perspective or evolving beliefs.

### The Problem

Without reflect:
- **No consistent character**: "Should we adopt remote work?" gets a different answer each time based on the LLM's randomness
- **No opinion formation**: The system never develops beliefs based on accumulated evidence
- **No reasoning context**: Responses don't reflect what the bank has learned or its perspective
- **Generic responses**: Every AI sounds the same — no disposition, no point of view

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
| You're building your own reasoning | You want disposition-consistent responses |
| You need maximum control | You want the bank to "think" for itself |
| Simple fact lookup | Forming recommendations or opinions |

**Example:**
- `recall("Alice")` → Returns all Alice facts
- `reflect("Should we hire Alice?")` → Reasons about Alice's fit based on accumulated knowledge, weighs evidence, forms opinion

---

## The Reflect Process

1. **Recall** relevant memories based on the query
2. **Load** the bank's disposition traits and background
3. **Reason** about the memories through the disposition lens
4. **Form** new opinions with confidence scores
5. **Return** response, sources, and any new beliefs

---

## Disposition Framework (CARA)

When you create a memory bank, you can configure its disposition using **Big Five traits**. These traits influence how the bank interprets information and forms opinions:

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
    disposition={
        "openness": 0.3,  # Prefers proven methods
        "conscientiousness": 0.9,  # Highly organized
        # ... other traits
    }
)
```

The background provides context that shapes how disposition traits are applied:
- "I prefer simplicity" + low openness → consistently favors established solutions
- "15 years experience" → responses reference this expertise
- First-person perspective → creates consistent voice

### Bias Strength

The `bias_strength` parameter (0-1) controls how much disposition influences reasoning:

- **0.0**: Purely evidence-based
- **0.5**: Balanced disposition and evidence
- **1.0**: Strongly disposition-driven

---

## Opinion Formation

When `reflect()` encounters a question that warrants forming an opinion, disposition shapes the response.

### Same Facts, Different Opinions

Two banks with different dispositions, given identical facts about remote work:

**Bank A** (high openness, low conscientiousness):
> "Remote work unlocks creative flexibility and spontaneous innovation. The freedom to work from anywhere enables breakthrough thinking."

**Bank B** (low openness, high conscientiousness):
> "Remote work lacks the structure and accountability needed for consistent performance. In-person collaboration is more reliable."

**Same facts → Different conclusions** because disposition shapes interpretation.

---

## Opinion Evolution

Opinions aren't static — they evolve as new evidence arrives. Here's a real-world example with a database library:

| Event | What the bank learns | Opinion formed |
|-------|---------------------|----------------|
| **Day 1** | "Redis is open source under BSD license" | "Redis is excellent for caching — fast, reliable, and OSS-friendly" (confidence: 0.85) |
| **Day 2** | "Redis has great community support and documentation" | Opinion reinforced (confidence: 0.90) |
| **Day 30** | "Redis changed license to SSPL, restricting cloud usage" | "Redis is still technically strong, but license concerns for cloud deployments" (confidence: 0.65) |
| **Day 45** | "Valkey forked Redis under BSD license with Linux Foundation backing" | "Consider Valkey for new projects requiring true OSS; Redis for existing deployments" (confidence: 0.80) |

**Before the license change:**
> "Should we use Redis for our caching layer?"
> → "Yes, Redis is the industry standard — fast, battle-tested, and fully open source."

**After the license change:**
> "Should we use Redis for our caching layer?"
> → "It depends. For cloud deployments, consider Valkey (the BSD-licensed fork). For on-premise, Redis remains excellent technically."

This **continuous learning** ensures recommendations stay current with real-world changes.

---

## Disposition Presets by Use Case

Different use cases benefit from different disposition configurations:

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
- **Response text** — Disposition-influenced answer
- **Based on** — Which memories were used (with relevance scores)

**Example:**
```json
{
  "text": "Based on Alice's ML expertise and her work at Google, she'd be an excellent fit for the research team lead position...",
  "based_on": {
    "world": [
      {"text": "Alice works at Google...", "weight": 0.95},
      {"text": "Alice specializes in ML...", "weight": 0.88}
    ]
  }
}
```

**Note:** New opinions are formed asynchronously in the background. They'll influence future `reflect()` calls but aren't returned directly.

---

## Why Disposition Matters

Without disposition, all AI assistants sound the same. With disposition:

- **Customer support bots** can be diplomatic and empathetic
- **Code review assistants** can be direct and thorough
- **Creative assistants** can be open to unconventional ideas
- **Risk analysts** can be appropriately cautious

Disposition creates **consistent character** across conversations while allowing opinions to **evolve with evidence**.

---

## Next Steps

- [**Retain**](./retain) — How rich facts are stored
- [**Recall**](./retrieval) — How multi-strategy search works
- [API Reference: Reflect](./api/reflect) — Code examples and usage
