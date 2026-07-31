# v2 Knowledge Pages — Design Spec

**Status:** approved in brainstorm (2026-07-25), pending implementation plan
**Scope:** `hindsight-integrations/hindsight-coding-agents` (shared TS core) + `claude-code-v2` wrapper
**Motivation:** make knowledge pages a real, trustworthy "wiki" surface for the vectorize-crm demo (the `knowledge-pages-as-trust-surface` principle) — the agent reliably knows what pages exist, pages are cleanly tiered instead of blended, and major initiatives become first-class, linkable pages.

---

## 1. Problem

Three gaps in the current v2 branch:

1. **Page discovery is a blind fetch.** SessionStart injects a static `KNOWLEDGE_MISSION` telling the agent to call `agent_knowledge_list_pages`, but hands it **no roster** — the agent never learns a page exists unless it independently decides to call the tool. Per-turn recall injects facts, not pages.
2. **Pages are blended.** Neither the seeded `PAGES` nor the agent's `create_page` tool scope synthesis by tag, so every page synthesizes from the whole bank filtered only by `fact_type`. Git-log, session, and survey memories all bleed into every page.
3. **No first-class initiative tracking / linking.** Hindsight has no native page-to-page links. A "major feature" leaves no durable, navigable page a future session can pick up.

## 2. Principles applied

- Automatic/visible value; zero out-of-band CLI; memory beats code search; knowledge pages as a trust surface; minimal post-setup burden.
- Modular units, small files, follow existing patterns (per-hook specs, fail-open, unit-testable pure cores).
- The **memory extractor never knows what a "page" is.** Classification is by the fact's *intrinsic* nature; pages are application-side saved views. No abstraction leak into extraction.

## 3. Architecture overview

Two complementary curation paths + a discovery layer:

- **Passive (automatic):** `entity_labels` schema-forces the extractor to tag qualifying facts `knowledge:<tier>`. Seeded **tier pages** each filter on one tier tag. No agent effort.
- **Active (high-signal):** one intent-named MCP verb, `hindsight_capture_initiative`, lets the agent register a major feature as a **per-initiative page** with a tag-based link back from the aggregate Initiatives page.
- **Discovery:** SessionStart injects guidance + the page roster; the UserPromptSubmit hook re-injects a fresh roster on a fixed cadence (hook-counted, not model-counted).

## 4. `entity_labels` — passive tier tagging

One hierarchical bank config group, set by `configureBank` at seed time:

```jsonc
{
  "key": "knowledge",
  "type": "multi-values",   // 0, 1, or several — empty is normal
  "optional": true,
  "tag": true,               // emits knowledge:<value> onto the fact's tags
  "description": "Routing labels for this project's Hindsight KNOWLEDGE PAGES — curated, human-readable summaries of the repo's DURABLE engineering knowledge (architecture, key decisions, conventions, ongoing initiatives), each page rebuilt automatically from the facts labeled for it. Mark a fact only when it is durable, reusable knowledge a developer would still want surfaced in future sessions. IMPORTANT: leave this EMPTY for routine, transient, or operational facts — a passing test, a one-off command, a status update, a debugging dead-end. MOST facts should get no label here. Assign more than one value only when the fact genuinely fits several.",
  "values": [
    { "value": "feature-work", "description": "A new feature, initiative, or enhancement being planned or built — the capability being added and the intent behind it. Not routine bug-fixes or chores." },
    { "value": "decision",     "description": "A technical decision that will constrain future work, with its rationale — why this approach was chosen over alternatives, or a rule deliberately adopted." },
    { "value": "convention",   "description": "An established way this project does things — naming, structure, testing, error handling, or another recurring pattern a contributor is expected to follow." },
    { "value": "component",    "description": "What a specific module, file, service, or subsystem is responsible for, or how components depend on and connect to one another." },
    { "value": "concept",      "description": "A domain concept, key abstraction, or piece of project vocabulary a new contributor must understand to work effectively." }
  ]
}
```

Notes:
- `tag: true` → `_inject_label_tags` copies each `knowledge:<value>` onto the fact's `tags` (no extra query infra).
- Selectivity (multi-values + "mostly empty" instruction) prevents force-fitting routine facts into a tier.

## 5. Seeded tier pages (tag-scoped)

Created via `/knowledge-base/pages` (supports `tags`, `trigger`, `parent_id`) — **not** `/mental-models`. Each `PAGES` entry gains a `trigger.tags` pin:

| Page | `trigger.tags` |
| --- | --- |
| Initiatives and enhancements | `["knowledge:feature-work"]` |
| Key decisions and rationale | `["knowledge:decision"]` |
| Conventions and patterns | `["knowledge:convention"]` |
| Component map | `["knowledge:component"]` |
| Core concepts | `["knowledge:concept"]` |

`tags_match` strict enough to exclude untagged facts (`all_strict`/`any_strict`). Tag matching is exact set-ops (no wildcards) — this is *why* the vocabulary is fixed, not per-feature.

## 6. MCP surface

Raw page CRUD (`create_page`/`update_page`/`delete_page`) is **removed** from the agent. The agent sees grounding tools + one capture verb. Naming convention: `hindsight_*`.

**Grounding**
- `hindsight_list_knowledge_pages` `{}` — roster: id, title, one-line coverage. (agent-facing description as drafted in brainstorm)
- `hindsight_read_knowledge_page` `{ page_id }` — full page content; follow `[[page:<id>]]` links by re-calling.
- `hindsight_search_memory` `{ query, max_tokens? }` — raw fact recall for specifics pages don't cover.
- `hindsight_get_current_bank` `{}` — minor introspection (kept).

**Capture**
- `hindsight_capture_initiative` `{ title, summary, relates_to_page_id? }` — the one active verb. Explicit WHEN / WHEN-NOT description (as drafted). Returns the initiative page id.
- `hindsight_ingest_document` `{ title, content }` — existing `agent_knowledge_ingest`, reframed.

(Full agent-facing descriptions are captured verbatim in the brainstorm thread and will be reproduced in the implementation plan.)

## 7. `hindsight_capture_initiative` mechanism

- Derive one slug `S` from `title`. Page id = `initiative-<S>`. **The slug in the tag and the page id are the same token, derived once** (cannot drift).
- **New initiative** (`relates_to_page_id` omitted):
  1. Create page `initiative-<S>` (title from `title`, `source_query` about that initiative) under an **"Initiatives" folder** (tag-scoped).
  2. Retain a marker memory (text = title + summary) tagged `["knowledge:feature-work", "relatedPageId:initiative-<S>"]`. **No session tag** (decided — the MCP server has no Claude session id; faking one wouldn't link to the Stop write-back's `conversation:<sessionId>` doc anyway).
- **Enhancement** (`relates_to_page_id` given): marker only, `relatedPageId = relates_to_page_id`; no new page. Re-invoking for the same initiative accrues markers → the page re-synthesizes with progress.

### Link survival (why `relatedPageId` as a tag, not in prose)

A tag is set directly via the retain `tags` param — it **bypasses LLM extraction entirely**, so it's guaranteed present verbatim (no REF-ID-style preservation needed at extraction). Verified: the reflect/synthesis path SELECTs `tags` and serializes facts via `_prune_nulls(model_dump())`, which keeps non-empty tags → **the synthesis LLM sees the tag.** The **Initiatives page `source_query`** instructs: *"when a memory carries a `relatedPageId:<id>` tag, emit a `[[page:<id>]]` link to it."* The link id is generated from the tag value at synthesis time, so it always matches the created page id.

- Only **Stage 2 (synthesis)** is probabilistic now (bounded token budget may omit some entries when there are many).
- **Guaranteed fallback:** the per-initiative page always exists (created via API, independent of any LLM stage) and appears in the **Initiatives folder / injected roster**, so navigation works even if a synthesized inline link drops.

## 8. Page-access injection

- **SessionStart** (`session-start.ts`): replace static `KNOWLEDGE_MISSION` with a preamble = (a) guidance on *when/why* to consult pages, (b) the roster fetched via `client.listPages()` (`- <title> (<id>)`, empty-state aware), (c) a note that the list refreshes periodically. Cold repo → empty roster line; roster comes alive mid-session as seeding/survey complete.
- **UserPromptSubmit** (`hook.ts`): extend the per-session cache (`{answer}` → `{answer, turns}`); the **hook** counts user turns and, roughly every `pageRefreshEveryTurns` (default 10, approximate), calls `listPages()` and injects a compact roster refresh. Runs concurrently with recall; **fail-open** (a refresh error never blocks the turn).
- **Shared formatting** (new `core/knowledge-injection.ts`, SDK-free/unit-testable): `parsePageList(raw) -> {id,title}[]`, `buildKnowledgePreamble(pages)`, `buildRosterRefresh(pages)`.
- **Config:** `pageRefreshEveryTurns` (default 10).

## 9. Non-goals / deferred

- Session drill-down tag on captured markers (dropped — see §7).
- `hindsight_capture_decision` and other capture verbs (passive path covers those tiers; revisit if the aggregate pages aren't sharp enough).
- A `gotcha`/`pitfall` tier (five tiers for now).
- Native page-to-page links / backlinks (Hindsight has none; we approximate via folder tree + `relatedPageId`-driven `[[page:<id>]]`).

## 10. Risks / migration

- **Older banks** need re-seeding to pick up the new `entity_labels`, the `session` retain strategy, and the tag-scoped page triggers (`configureBank` sets them). User is starting fresh with v2 banks, so acceptable; live retain fails open otherwise.
- **Stage-2 synthesis omission** for large initiative counts — mitigated by the folder/roster fallback.
- **Instruction adherence** for the `source_query` link-rendering and the label selectivity — both are LLM-following behaviors; cover with an `hs_llm_core` judge test, and the deterministic mechanics (tag injection, roster formatting, slug/id equality, hook turn-counting) with fast unit tests.

## 11. Testing

- **Deterministic unit tests:** `knowledge-injection` formatting + empty-state; hook turn-counter + cadence; `capture_initiative` slug→id→tag equality and request shape (mock client); tag-scoped page request bodies; entity_labels config emitted by `configureBank`.
- **LLM judge test (`hs_llm_core`):** label selectivity (routine facts get no `knowledge:*`), and `relatedPageId` → `[[page:<id>]]` rendering in a synthesized Initiatives page.

## 12. File map (anticipated)

- `src/core/knowledge-injection.ts` (new) — roster/preamble formatting.
- `src/core/session-start.ts` — preamble + roster.
- `src/core/hook.ts` — cache `{answer,turns}` + periodic roster refresh.
- `src/core/config.ts` — `pageRefreshEveryTurns`.
- `src/core/missions.ts` — `entity_labels` group; tag-scoped `PAGES`; Initiatives `source_query` link instruction.
- `src/core/hindsight.ts` — `configureBank` sets `entity_labels`; `createPages` pins `trigger.tags` + Initiatives folder; new `createInitiativePage`/marker retain helpers.
- `src/core/knowledge-tools.ts` — new `hindsight_*` grounding + `capture_initiative` tools; remove raw page CRUD from agent surface.
- Tests alongside each.
