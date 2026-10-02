---
name: memory-setup
description: Set up and check Hindsight long-term memory for this Bot. Use the first time a Bot uses Hindsight, when the user asks to connect or check memory, or whenever a Hindsight tool call fails.
---

# Set up Hindsight memory

Hindsight stores memory in **banks**. This plugin uses three kinds:

- **This Bot's bank**, `grok-bot::<bot-name>`: what this Bot learns in its own work. Build `<bot-name>` from the Bot's name, lowercase, with spaces turned into hyphens (a Bot named "Sales Researcher" uses `grok-bot::sales-researcher`).
  When you are not a Grok Bot (for example, an agent in Cursor), this bank is per project instead: `cursor::<project-name>`, from the open workspace folder's name in the same lowercase, hyphenated form. With no workspace open, ask the user what to call it. Never use another Bot's `grok-bot::` bank as your own; those are read-only to you.
- **The shared bank**, `grok-bot::shared`: what every Bot on this account should know.
- **The user's other banks**: memory written by the user's other AI tools, such as Claude Code or ChatGPT. Read these when a task touches that work. Never write to them.

## Steps

1. Call `list_banks`. A successful call proves the connection is real. If it fails, tell the user to reconnect Hindsight in the plugin's settings and stop. Do not guess endpoints or hostnames.
2. If you are a Grok Bot that still has the default name "Grok Bot", ask the user what to call it before going further. The name becomes the bank id, so a default name would give every unnamed Bot the same bank, and renaming later strands its memory under the old id.
3. If this Bot's bank does not exist, call `create_bank` with its `bank_id` and a `name` of "Grok Bot: <Bot name>".
4. If `grok-bot::shared` does not exist, call `create_bank` with `name` "Grok Bot: shared".
5. Call `list_mental_models` on `grok-bot::shared`. If there is no mental model named "About the user", call `create_mental_model` on that bank with that name and the source query "Who is this user: their work, current projects, the people they mention most, and their stated preferences".
6. Tell the user which banks exist and which other banks you can read.

## Rules

- Never call `delete_bank`, `clear_memories`, `invalidate_memory`, `delete_document` or `delete_mental_model`. If something should be deleted, tell the user and let them do it.
- Never store passwords, one-time codes, API keys, card or account numbers.
