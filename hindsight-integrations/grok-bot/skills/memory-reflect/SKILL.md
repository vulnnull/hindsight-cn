---
name: memory-reflect
description: Answer questions about history, habits and past decisions by reasoning over Hindsight memory. Use when asked what was decided about something, how something is usually done, what changed over time, or what is known about a topic.
---

# Reason over memory

`recall` returns individual memories. `reflect` reads across them and answers the question, which is better for anything that needs a judgement over history.

## Steps

1. Call `reflect` with the user's question on the bank most likely to hold the answer: `grok-bot::shared` for things about the user or the team, this Bot's bank for its own work, or one of the user's other banks for their work in other tools.
2. If the answer depends on more than one bank, reflect on each and combine the answers, saying which part came from where.
3. Give the answer directly. If memory is thin or contradictory, say so rather than filling the gap.
