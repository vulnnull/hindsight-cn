---
name: memory-retain
description: Save what was learned to Hindsight long-term memory. Use when a task finishes, when the user states a fact, decision or preference, and when you discover something a later run or another Bot would need.
---

# Save what was learned

Memory is only useful if the next run can find it. Save the outcome and the reason, not a transcript.

## Steps

1. Decide where it belongs:
   - Only useful to this Bot's own work: this Bot's bank, `grok-bot::<bot-name>`.
   - Useful to any Bot, or a fact about the user: `grok-bot::shared`.
2. Write a short, self-contained note that makes sense with no other context: what happened or was decided, who decided it, when, and why. "On 3 Oct the user chose Vendor B over Vendor A because A has no EU data residency" beats "user picked B".
3. Call `retain` with that note as `content`, and `tags` of `source:grok-bot` and `bot:<bot-name>`.

## Rules

- One note per distinct fact or decision. Do not paste whole conversations or tool output.
- Never store passwords, one-time codes, API keys, card or account numbers, or health measurements.
- Never write to banks that belong to the user's other tools.
