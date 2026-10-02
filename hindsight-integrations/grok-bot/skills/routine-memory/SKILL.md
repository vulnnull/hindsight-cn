---
name: routine-memory
description: Carry state between runs of a scheduled routine using Hindsight memory. Use when creating or editing a routine, to write the recall and retain steps into the routine's own instructions, and at the start and end of every scheduled or event-triggered routine run.
---

# Remember between routine runs

A routine runs again and again. Without memory each run starts from zero, repeats work and misses what changed. Read the last run before starting, and record this run before finishing.

## When creating or editing a routine

Write the memory steps into the routine's own instructions, so every run carries them even when nobody is in the chat:

- First: "Recall the last run of <routine name> from Hindsight and use it."
- Last: "Retain a run note to Hindsight: what this run found, what changed, and what the next run should check first."

Tell the user you added them.

## At the start of the run

1. Call `recall` on this Bot's bank with the query "last run of <routine name>".
2. Use it: skip what was already handled, pick up what was left open, and compare against what the last run found.

## At the end of the run

1. Call `retain` on this Bot's bank with a note covering: the routine name, the date, what this run found, what changed since the last run, and what the next run should check first. Retain a note even when nothing changed, so the next run knows when this one looked.
2. Use the tags `source:grok-bot`, `bot:<bot-name>` and `routine:<routine name>`.
3. If the run found something other Bots should act on, also retain it to `grok-bot::shared` (see the `bot-handoff` skill).
