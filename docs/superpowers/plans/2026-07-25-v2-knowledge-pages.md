# v2 Knowledge Pages — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make v2 knowledge pages a reliable, cleanly-tiered "wiki" surface: passive `entity_labels` tier-tagging + tag-scoped seeded pages, a `hindsight_*` MCP surface with one active `capture_initiative` verb that creates per-initiative pages linked by tag, and SessionStart/UserPromptSubmit page-roster injection.

**Architecture:** Shared TS core (`hindsight-integrations/hindsight-coding-agents`). Extraction stays blind to "pages"; classification is intrinsic (`knowledge:<tier>` tags), pages are tag-scoped saved views. Per-initiative navigation via a `relatedPageId:<id>` tag the synthesizer renders into `[[page:<id>]]`, with the Initiatives folder/roster as the guaranteed fallback.

**Tech Stack:** TypeScript, vitest, tsup bundling. Hindsight REST API (`/knowledge-base/*`, `/mental-models`, `/memories`, bank `/config`).

**Spec:** `docs/superpowers/specs/2026-07-25-v2-knowledge-pages-design.md`

**Working dir for all commands:** `hindsight-integrations/hindsight-coding-agents`
**Test command:** `npx vitest run <file>` (fast suite; excludes `*.live.test.ts`). Full check: `npx vitest run && npx tsc --noEmit`.

**Conventions to follow (existing patterns):**
- `HindsightClient` HTTP via `this.req("METHOD", this.bankUrl(path), body?)`; JSON via `await r.json()`.
- MCP tools are SDK-free `ToolSpec { name, description, inputSchema (ZodRawShape), handler }`; wrap handler bodies in `guarded(...)`; `ok(value)` / `err(e)` result helpers.
- Fail-open everywhere in hooks; pure logic separated from stdin/stdout plumbing.
- Do NOT add a Claude co-author trailer to any commit.

---

## Task 1: Config field `pageRefreshEveryTurns`

**Files:**
- Modify: `src/core/config.ts`
- Test: `src/core/config.test.ts`

- [ ] **Step 1: Write failing test** — assert the default resolves to 10 and an override wins.

```ts
it("pageRefreshEveryTurns defaults to 10 and is overridable", () => {
  expect(loadConfig({ harness: "claude-code", projectDir: process.cwd() }).pageRefreshEveryTurns).toBe(10);
});
```
(Add an override case mirroring the existing override tests in this file.)

- [ ] **Step 2: Run** `npx vitest run src/core/config.test.ts` → FAIL (property missing).
- [ ] **Step 3: Implement** — add `pageRefreshEveryTurns: number` to the `Config` type and default `10` in the same place `recallMaxTokens`/`reflectTimeoutMs` are defined/merged. Follow the exact merge/layering pattern already used for numeric fields.
- [ ] **Step 4: Run** the test → PASS.
- [ ] **Step 5: Commit** `git add src/core/config.ts src/core/config.test.ts && git commit -m "feat(core): add pageRefreshEveryTurns config (default 10)"`

---

## Task 2: `knowledge-injection.ts` — roster/preamble formatting (pure, new)

**Files:**
- Create: `src/core/knowledge-injection.ts`
- Test: `src/core/knowledge-injection.test.ts`

Pure, SDK-free, no network. Parses the `listPages()` payload and formats the two injections.

- [ ] **Step 1: Write failing tests**

```ts
import { describe, expect, it } from "vitest";
import { parsePageList, buildKnowledgePreamble, buildRosterRefresh } from "./knowledge-injection";

describe("parsePageList", () => {
  it("extracts {id,title} from the mental-model list shape, tolerating junk", () => {
    const raw = { items: [{ id: "p1", name: "Component map" }, { id: "p2", name: "Core concepts" }, { nope: 1 }] };
    expect(parsePageList(raw)).toEqual([{ id: "p1", title: "Component map" }, { id: "p2", title: "Core concepts" }]);
  });
  it("returns [] for null/garbage", () => {
    expect(parsePageList(null)).toEqual([]);
    expect(parsePageList(42 as unknown)).toEqual([]);
  });
});

describe("buildKnowledgePreamble", () => {
  it("includes guidance, a roster of pages, and a refresh note", () => {
    const out = buildKnowledgePreamble([{ id: "p1", title: "Component map" }]);
    expect(out).toContain("<hindsight_knowledge>");
    expect(out).toContain("Component map");
    expect(out).toContain("p1");
    expect(out).toMatch(/hindsight_read_knowledge_page/);
  });
  it("has an empty-state line when there are no pages", () => {
    const out = buildKnowledgePreamble([]);
    expect(out).toMatch(/no knowledge pages yet|still learning/i);
  });
});

describe("buildRosterRefresh", () => {
  it("is a compact 'current pages' block listing ids+titles", () => {
    const out = buildRosterRefresh([{ id: "p1", title: "Component map" }]);
    expect(out).toContain("Component map");
    expect(out).toContain("p1");
  });
  it("returns undefined when there are no pages (nothing to refresh)", () => {
    expect(buildRosterRefresh([])).toBeUndefined();
  });
});
```

- [ ] **Step 2: Run** `npx vitest run src/core/knowledge-injection.test.ts` → FAIL.
- [ ] **Step 3: Implement**

```ts
export interface PageRef { id: string; title: string; }

/** Defensive parse of HindsightClient.listPages() (GET /mental-models?detail=metadata → {items:[{id,name}]}). */
export function parsePageList(raw: unknown): PageRef[] {
  const items = (raw as { items?: unknown })?.items;
  if (!Array.isArray(items)) return [];
  const out: PageRef[] = [];
  for (const it of items) {
    const id = (it as { id?: unknown })?.id;
    const name = (it as { name?: unknown })?.name;
    if (typeof id === "string" && typeof name === "string") out.push({ id, title: name });
  }
  return out;
}

function roster(pages: PageRef[]): string {
  return pages.map((p) => `- ${p.title} (${p.id})`).join("\n");
}

/** SessionStart: teach when/why to use pages + list what exists. Empty-state aware. */
export function buildKnowledgePreamble(pages: PageRef[]): string {
  const body = pages.length
    ? `Knowledge pages available in this repository:\n${roster(pages)}`
    : "No knowledge pages yet — Hindsight is still learning this repo; they'll appear as it processes.";
  return (
    "<hindsight_knowledge>\n" +
    "This repository has a Hindsight knowledge base: curated, continuously-updated pages summarizing its " +
    "durable engineering knowledge (architecture, components, conventions, key decisions, and in-flight initiatives).\n" +
    "Before substantial work, consult the relevant pages instead of re-deriving understanding from the code: read " +
    "Conventions before writing new code, the Component map before changing a subsystem, and an initiative's page " +
    "before continuing that feature.\n" +
    `${body}\n` +
    "Read one with hindsight_read_knowledge_page(page_id). Follow any [[page:<id>]] links you see. The list is " +
    "re-injected for you periodically as it changes.\n" +
    "</hindsight_knowledge>"
  );
}

/** Periodic UserPromptSubmit refresh — compact, or undefined when there's nothing to show. */
export function buildRosterRefresh(pages: PageRef[]): string | undefined {
  if (!pages.length) return undefined;
  return (
    "<hindsight_knowledge_refresh>\n" +
    `Current Hindsight knowledge pages (may have changed):\n${roster(pages)}\n` +
    "Read any with hindsight_read_knowledge_page(page_id).\n" +
    "</hindsight_knowledge_refresh>"
  );
}
```

- [ ] **Step 4: Run** the test → PASS.
- [ ] **Step 5: Commit** `git add src/core/knowledge-injection.ts src/core/knowledge-injection.test.ts && git commit -m "feat(core): knowledge-injection roster/preamble formatting"`

---

## Task 3: `entity_labels` tier vocabulary + configureBank wiring

**Files:**
- Modify: `src/core/missions.ts` (add `KNOWLEDGE_LABELS`)
- Modify: `src/core/hindsight.ts` (`configureBank` PATCH sets `entity_labels`)
- Test: `src/core/hindsight.*.test.ts` (add/extend a config test with a mock client)

- [ ] **Step 1: Write failing test** — assert `configureBank` PATCHes `/config` with `entity_labels` containing the `knowledge` group and its five values, and `entities_allow_free_form: true`. Use the existing fetch/req mock pattern from `hindsight.*.test.ts`; capture the PATCH body to `/config` and assert on it.

- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement**
  - In `missions.ts`, export `KNOWLEDGE_LABELS` — the exact object from the spec §4 (`key:"knowledge"`, `type:"multi-values"`, `optional:true`, `tag:true`, the verbose group `description`, and the five value `{value,description}` entries: feature-work, decision, convention, component, concept).
  - In `hindsight.ts::configureBank`, extend the existing `PATCH .../config` `updates` object to include `entity_labels: [KNOWLEDGE_LABELS]` and `entities_allow_free_form: true`. Import `KNOWLEDGE_LABELS`.
  - Update the `[bank] configured …` log to mention `entity_labels`.
- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Commit** `git add src/core/missions.ts src/core/hindsight.ts src/core/hindsight.*.test.ts && git commit -m "feat(core): passive knowledge entity_labels tier vocabulary + configureBank wiring"`

---

## Task 4: Tag-scoped seeded pages + Initiatives folder + link source_query

**Files:**
- Modify: `src/core/missions.ts` (`PAGES` gain `tags`; Initiatives `source_query` link instruction)
- Modify: `src/core/hindsight.ts` (`ensureFolder`, `createPages` sets page `tags` + parents Initiatives under the folder)
- Test: `src/core/hindsight.pages.test.ts`

- [ ] **Step 1: Write failing tests** (mock client `req`):
  - Each seeded page POST to `/knowledge-base/pages` includes `tags: ["knowledge:<tier>"]` mapped per the spec §5 table.
  - The Initiatives page is created with `parent_id` equal to the id returned by an Initiatives folder POST to `/knowledge-base/folders`.
  - `ensureFolder("Initiatives")` returns an existing root folder's id when the tree already contains it (GET `/knowledge-base/tree`) and does NOT POST a duplicate.

- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement**
  - `missions.ts`: add `tags: string[]` to each `PAGES` entry (feature-work/decision/convention/component/concept mapping). Append to the Initiatives `source_query`: *"When a source memory carries a tag of the form `relatedPageId:<id>`, include a Markdown link `[[page:<id>]]` to that page in the summary, so each initiative links to its detailed page."*
  - `hindsight.ts`: add
    ```ts
    /** Find a root folder by name (case-insensitive) or create it; returns its id. */
    async ensureFolder(name: string): Promise<string | undefined> {
      try {
        const tree = (await (await this.req("GET", this.bankUrl("/knowledge-base/tree"))).json()) as
          { roots?: { id?: string; kind?: string; name?: string }[] };
        const hit = (tree.roots || []).find((n) => n.kind === "folder" && (n.name || "").toLowerCase() === name.toLowerCase());
        if (hit?.id) return hit.id;
      } catch { /* fall through to create */ }
      try {
        const r = await this.req("POST", this.bankUrl("/knowledge-base/folders"), { name });
        return ((await r.json()) as { id?: string }).id;
      } catch { return undefined; }
    }
    ```
  - In `createPages()`: before the loop, `const initiativesFolderId = await this.ensureFolder("Initiatives");`. For each page, build body `{ name, source_query, tags: p.tags, parent_id: <initiativesFolderId if this is the Initiatives page else undefined>, trigger: { fact_types:[...], refresh_after_consolidation:true } }`. (Page-level `tags` drives synthesis scoping via `RefreshTagFiltering`; `tags_match` defaults to `all_strict` when tags present.)
- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Commit** `git add src/core/missions.ts src/core/hindsight.ts src/core/hindsight.pages.test.ts && git commit -m "feat(core): tag-scope seeded pages, Initiatives folder, relatedPageId link source_query"`

---

## Task 5: Client helpers — per-initiative page + marker retain

**Files:**
- Modify: `src/core/hindsight.ts` (`captureInitiative`)
- Test: `src/core/hindsight.pages.test.ts`

- [ ] **Step 1: Write failing tests** (mock `req`):
  - `captureInitiative({title:"Retry backoff for the uploader", summary:"…"})` → derives slug `retry-backoff-for-the-uploader`, POSTs a page id `initiative-<slug>` to `/knowledge-base/pages` with `parent_id` = the Initiatives folder and `tags: ["knowledge:feature-work"]`, AND POSTs a marker to `/memories` (via `retain`) tagged `["knowledge:feature-work","relatedPageId:initiative-<slug>"]`, strategy `session` or `document` (pick `document`), `async:true`. Returns `{ page_id: "initiative-<slug>" }`.
  - Slug is deterministic and identical between the page id and the `relatedPageId:` tag value.
  - Enhancement path: `captureInitiative({title, summary, relatesToPageId:"initiative-x"})` POSTs NO new page; marker tagged `relatedPageId:initiative-x`; returns `{ page_id: "initiative-x" }`.

- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement**

```ts
private slugify(s: string): string {
  return s.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 60) || "initiative";
}

/** Active-path capture: register a major feature as a per-initiative page + a tagged marker memory. */
async captureInitiative(args: { title: string; summary: string; relatesToPageId?: string }): Promise<{ page_id: string }> {
  const pageId = args.relatesToPageId ?? `initiative-${this.slugify(args.title)}`;
  if (!args.relatesToPageId) {
    const folderId = await this.ensureFolder("Initiatives");
    await this.req("POST", this.bankUrl("/knowledge-base/pages"), {
      name: args.title,
      source_query: `Summarize the "${args.title}" initiative: what is being built or changed and why, and its current state — drawn from the project's memory.`,
      parent_id: folderId,
      tags: ["knowledge:feature-work", `relatedPageId:${pageId}`],
      trigger: { fact_types: ["world", "experience", "observation"], refresh_after_consolidation: true },
    });
  }
  const verb = args.relatesToPageId ? "Enhancement to an existing initiative" : "New initiative";
  const content = `${verb}: ${args.title}. ${args.summary}`;
  await this.retain(content, "initiative marker", pageId /* not a stable doc id requirement; see note */,
    ["knowledge:feature-work", `relatedPageId:${pageId}`], "document", { async: true });
  return { page_id: pageId };
}
```
  - NOTE: use a UNIQUE document id per marker (e.g. `initiative-marker-<slug>-<n>`), NOT `pageId`, so repeated enhancement captures accrue instead of replacing. Since `Date.now()` is fine here (runtime, not a workflow script), suffix with a timestamp: `initiative-marker-${this.slugify(args.title)}-${Date.now()}`. Keep the `relatedPageId` tag equal to `pageId`.
  - Confirm `retain(content, context, documentId, tags, strategy, opts)` signature matches current `HindsightClient.retain`.

- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Commit** `git add src/core/hindsight.ts src/core/hindsight.pages.test.ts && git commit -m "feat(core): captureInitiative — per-initiative page + relatedPageId marker"`

---

## Task 6: MCP surface — `hindsight_*` grounding + `capture_initiative`; drop page CRUD

**Files:**
- Modify: `src/core/knowledge-tools.ts`
- Modify: `src/mcp-server.ts` (only if it references removed tool names)
- Test: `src/core/knowledge-tools.test.ts`, `src/mcp-server.test.ts` (tool-count assertions)

- [ ] **Step 1: Write failing tests**
  - `buildKnowledgeTools(client, bankId)` returns exactly these tool names: `hindsight_get_current_bank`, `hindsight_list_knowledge_pages`, `hindsight_read_knowledge_page`, `hindsight_search_memory`, `hindsight_capture_initiative`, `hindsight_ingest_document`. (Assert the set; update any count assertion.)
  - `hindsight_capture_initiative` handler calls `client.captureInitiative` with `{title, summary, relatesToPageId?}` and returns the page id (mock client).
  - No `create_page` / `update_page` / `delete_page` tools are present.
  - Each tool still fails closed via `guarded` (a thrown client error → `isError:true`, no throw).

- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement**
  - Rebuild the `buildKnowledgeTools` list: rename read/recall/ingest/bank tools to the `hindsight_*` names; drop `create_page`/`update_page`/`delete_page`; add `hindsight_capture_initiative` with `inputSchema { title: z.string(), summary: z.string(), relates_to_page_id: z.string().optional() }` calling `client.captureInitiative({ title, summary, relatesToPageId: relates_to_page_id })`.
  - Use the **verbatim agent-facing `description` strings** from the spec §6 / the brainstorm (grounding tools + the explicit WHEN/WHEN-NOT `capture_initiative` description).
  - Update `mcp-server.ts` only if it enumerates tool names; otherwise it consumes `buildKnowledgeTools` generically and needs no change.
- [ ] **Step 4: Run** `npx vitest run src/core/knowledge-tools.test.ts src/mcp-server.test.ts` → PASS.
- [ ] **Step 5: Commit** `git add src/core/knowledge-tools.ts src/mcp-server.ts src/core/knowledge-tools.test.ts src/mcp-server.test.ts && git commit -m "feat(mcp): hindsight_* grounding tools + capture_initiative; remove raw page CRUD from agent"`

---

## Task 7: SessionStart — preamble + roster

**Files:**
- Modify: `src/core/session-start.ts`
- Test: `src/core/session-start.test.ts`

- [ ] **Step 1: Write failing tests**
  - `buildSessionStartContext` now fetches pages via the client and injects `buildKnowledgePreamble(...)` instead of the static `KNOWLEDGE_MISSION`. Extend the `SeedContextClient` interface with `listPages(): Promise<unknown>`; the mock returns `{items:[{id:"p1",name:"Component map"}]}` and the output contains "Component map".
  - listPages failure is fail-open: the preamble still renders (empty-state) and the seed logic is unaffected.

- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement**
  - Add `listPages` to `SeedContextClient`.
  - Replace the `parts.push(KNOWLEDGE_MISSION)` line with: fetch `const pages = parsePageList(await client.listPages().catch(() => null));` then `parts.push(buildKnowledgePreamble(pages));`. Import from `./knowledge-injection`.
  - Remove the now-unused `KNOWLEDGE_MISSION` export if nothing else references it (grep first; keep if referenced).
- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Commit** `git add src/core/session-start.ts src/core/session-start.test.ts && git commit -m "feat(core): SessionStart injects page roster + guidance preamble"`

---

## Task 8: UserPromptSubmit — hook-counted periodic roster refresh

**Files:**
- Modify: `src/core/hook.ts`
- Test: `src/core/hook.test.ts`

- [ ] **Step 1: Write failing tests**
  - The session cache round-trips `{answer, turns}`; each `buildHookOutput` call increments `turns`.
  - Add `listPages` to the `HookClient` interface. On a turn where `turns % cfg.pageRefreshEveryTurns === 0`, the output includes `buildRosterRefresh(...)` content (assert "Component map" appears); on other turns it does not.
  - Refresh is fail-open (a `listPages` rejection doesn't break recall/injection).
  - First-turn behavior (reflect) unchanged.

- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement**
  - Extend the cache read/write to `{ answer?: string; turns?: number }`. Compute `const turns = (cached.turns ?? 0) + 1;` and persist it alongside `answer`.
  - Add `listPages(): Promise<unknown>` to `HookClient`.
  - After computing `memBlock`, if `cfg.pageRefreshEveryTurns > 0 && turns % cfg.pageRefreshEveryTurns === 0`, `try { const refresh = buildRosterRefresh(parsePageList(await client.listPages())); if (refresh) blocks.push(refresh); } catch { /* fail-open */ }`. Kick the `listPages` call off concurrently with recall to avoid added latency.
  - Import from `./knowledge-injection`.
- [ ] **Step 4: Run** `npx vitest run src/core/hook.test.ts` → PASS.
- [ ] **Step 5: Commit** `git add src/core/hook.ts src/core/hook.test.ts && git commit -m "feat(core): UserPromptSubmit hook-counted periodic page-roster refresh"`

---

## Task 9: Full check + LLM behavior (live) verification

**Files:**
- Modify: `src/system.live.test.ts` (add coverage; runs only under `HINDSIGHT_LIVE_E2E=1`)

- [ ] **Step 1: Full fast suite + types** — `npx vitest run && npx tsc --noEmit` → all green.
- [ ] **Step 2: Add a live assertion** (guarded by the existing live env flag) that after seeding a small repo + one `captureInitiative`, the Initiatives page content contains a `[[page:initiative-…]]` link (verifies the `relatedPageId` → link rendering end-to-end). Keep it in the live suite; do not run in the fast job.
- [ ] **Step 3: Manual/live run** (optional, operator): `HINDSIGHT_API_URL=http://localhost:8888 npm run test:live`.
- [ ] **Step 4: Commit** `git add src/system.live.test.ts && git commit -m "test(live): initiative page renders relatedPageId link end-to-end"`

---

## Final review

- [ ] Dispatch a final code-reviewer over the whole change set against the spec (`docs/superpowers/specs/2026-07-25-v2-knowledge-pages-design.md`).
- [ ] Rebuild + dev-install the `claude-code-v2` bundle so the running plugin picks up the new hooks/MCP (`bash scripts/dev-install.sh`); do not push/PR without explicit consent.
- [ ] Note deferred follow-ups: session drill-down tag, `capture_decision`, `gotcha` tier, older-bank reseed requirement.
