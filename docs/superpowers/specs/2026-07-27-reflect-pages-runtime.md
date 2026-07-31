# Reflect + Pages Runtime — Design Spec

**Status:** decided (2026-07-27), reconciles the earlier reflect-based runtime with the recall-based v2 into one opinionated path
**Scope:** `hindsight-integrations/hindsight-coding-agents` (shared TS core) + `claude-code-v2` wrapper
**Motivation:** the 33-task coding benchmark showed the v2 recall-per-prompt runtime *underperforms no memory* (35.0 mean corrections vs 32.0 baseline), while the earlier reflect-injection runtime beats baseline by 22% (25.0). This spec restores reflect as the only deep-memory path and replaces raw per-turn recall with lightweight injection from knowledge pages — "fast like recall, organized like reflect" — keeping v2's page/curation machinery where it earned its place and deleting it where it didn't.

---

## 1. Problem

Two prior iterations, each half right:

1. **Reflect runtime (v1):** one agentic REFLECT over the bank at session start, cached and re-injected every turn. Benchmark-proven (25.0 mean corrections) — but nothing surfaced mid-session; a task that drifted away from the first message got stale context.
2. **Recall runtime (v2):** per-prompt recall injection for turn-by-turn visibility, plus knowledge pages as a trust surface. But raw recall injects unsynthesized fact fragments — noise that *hurt*: 35.0 mean corrections, worse than running with no memory at all.

| Runtime | Mean corrections (33-task benchmark) | vs no-memory (32.0) |
| --- | --- | --- |
| Reflect-injection (v1) | **25.0** | **−22%** |
| Recall-per-prompt (v2) | 35.0 | +9% (regression) |
| No memory | 32.0 | baseline |

The reconciliation: keep reflect's synthesis quality as the deep path, keep v2's per-turn visibility principle, but source the per-turn material from the already-synthesized knowledge pages instead of raw recall.

## 2. Decisions

Explicit, decided — not options:

1. **Reflect restored** as the only deep-memory path (session-start, agentic synthesis, cached + re-injected every turn).
2. **Recall removed from the runtime** entirely. No per-prompt `recall` call.
3. **No `memoryMode` flag.** One opinionated path; config is for environment, naming, and harness wiring only — never behavior selection.
4. **Sections, not pages, are the per-turn injection unit** — locally matched, budget-trimmed, provenance-labeled.
5. **JSON turn transcripts** replace the markdown tool-call transcript in the Stop-hook write-back, with compact action entries.
6. **No tags / no `entity_labels`.** The server re-synthesizes pages after consolidation; "living pages" needs no client-side tagging machinery.

## 3. Runtime path — session start

Three steps, in order, all inside existing hooks (no out-of-band CLI):

### 3a. Cold-repo bootstrap (kept from v2)

On a bank with no prior memories: automatic shallow gitlog seed + codebase survey, exactly as v2 does it. The user never runs a setup command; the first session self-seeds. (Deep ingestion of that history is §7 — the seed here stays instant.)

### 3b. REFLECT once, on the first task message

The benchmark-proven core:

- On the first user prompt of the session, run one **REFLECT** — agentic synthesis over the whole bank, prompted to return the *root-cause decision with exact values* (concrete file paths, config values, version numbers — not summaries of summaries).
- Cache the result per session; **re-inject it every turn**. It is the session's durable deep context.
- One LLM-backed call per session, on the message that actually states the task — not on session-open, where there is nothing to reflect about.

### 3c. Page index build

Fetch all knowledge pages once (existing `listPages` + page reads), split each page at headings into **sections**, and build a **local section index** in the hook process. This index is what every subsequent turn matches against (§4) — no further server calls on the hot path.

## 4. Runtime path — every turn

Per-turn visibility, satisfied at ~zero latency and ~zero cost. Injection sources from **knowledge pages, not raw recall** — the material is already synthesized and organized; the turn hook only *selects* from it.

Mechanism (local, deterministic — no server call, no LLM call):

| Aspect | Design |
| --- | --- |
| Unit | Page **sections** (pages split at headings at index-build time) |
| Matching | Lexical: prompt scored against each section by weighted term overlap; **heading hits weighted higher** than body hits |
| Selection | Top 2–3 sections |
| Budget | Trimmed to a **~700-token total** |
| Provenance | Each snippet labeled `From <page> › <section>` + a tool pointer to read the full page |
| Floor | A minimum-score threshold below which **nothing is injected** — silence over noise |
| Refresh | Section index rebuilt on the existing 10-turn roster cadence (`pageRefreshEveryTurns`) |

The score floor is load-bearing: the benchmark showed that injecting weak matches is worse than injecting nothing (v2's regression). An empty injection is a correct outcome, not a failure mode.

## 5. Write-back

The Stop-hook session retain is **kept** — same trigger, same fail-open behavior. What changes is the transcript format handed to extraction:

- **JSON turns**, not markdown: an array of `{ "role": "user" | "assistant", "text": ... }` entries for the conversational content.
- Tool calls collapse to **compact one-line action entries**: `{ "role": "action", "text": "Edit boltons/strutils.py" }` — tool name + primary target only, **no arguments, no outputs**.

Rationale: extraction keeps the concrete artifacts (which files were touched, what actions occurred) without the transcript noise of full tool payloads — the markdown tool-call dumps were volume without signal.

## 6. Knowledge pages

Simplified from the v2 spec:

- **Dropped: tags and `entity_labels`** (v2 spec §4–5). The server already re-synthesizes pages after consolidation, so pages stay "living" with no client-side routing machinery. The extractor-never-knows-about-pages principle now holds trivially — there is nothing to route.
- **Creation paths:**
  1. **Seeded taxonomy** at bank creation (the fixed page set, as today, minus tag triggers).
  2. **Agent-driven `capture_initiative`** at plan approval — the one active capture verb survives from v2.
  3. **Organic splitting** of pages that outgrow their scope is a **server/curator concern**, not a client feature.

## 7. Ingestion — progressive background deepening

*Status: design accepted, implementation phased separately.*

Replaces the manual backfill CLI as the user-facing path (the CLI was out-of-band burden; nobody runs it). The principle: converge to full-depth history through normal usage, with zero user action.

1. **Instant shallow seed** — the gitlog seed from §3a; the session is useful immediately.
2. **Background deepening** — a background worker deep-ingests **per-commit-with-diffs, incrementally**, never blocking a turn.
3. **Working-set prioritization** — commits are ingested in order of relevance to what the agent is actually doing: files the agent reads/edits get their commit histories ingested **first**. Depth arrives where it pays off.
4. **Checkpointing** — progress persists across sessions; each session resumes deepening where the last left off, converging to full depth over normal usage.

The **backfill CLI survives as an internal tool** (benchmark setup, CI bank preparation) — it is no longer a documented user path.

## 8. Gap analysis — v2 principles under this design

| v2 principle | How this design satisfies it |
| --- | --- |
| See-it-working (automatic, visible value) | Reflect answer visible from turn 1; page-section snippets appear with explicit `From <page> › <section>` provenance, so the user sees memory working — and the score floor keeps it from visibly misfiring. |
| No out-of-band CLI | Cold-repo auto-seed kept (§3a); backfill CLI demoted to internal-only, replaced by background deepening (§7). Nothing requires a terminal command. |
| Reuse-over-reinvent | Reflect, `listPages`, Stop-hook retain, `capture_initiative`, and the 10-turn refresh cadence are all existing machinery recombined; the only new code is the local section index and matcher — deliberately dumb (lexical, no LLM). |
| Preserve-intent | Reflect is prompted for root-cause decisions with exact values; JSON transcripts keep concrete action artifacts; per-commit-with-diffs deepening captures *why* the code changed, not just that it did. |
| Near-zero-burden | No config flags to choose, no CLI to run, no tags to maintain; one LLM call per session start, everything else local. |

## 9. Verification gates

Ship gates, in order:

1. **Reflect-restored benchmark:** the restored runtime must recover **~25 mean corrections at n=2 on identical banks** to the original reflect run. This proves the restoration is faithful before anything is layered on.
2. **Reflect+pages benchmark:** with per-turn section injection enabled, the score **must not regress** vs reflect-alone. Section injection earns its place by not hurting; any regression points at the floor/budget tuning.
3. **Live system suite:** existing hook/integration suite updated for the new path — reflect caching + per-turn re-injection, section index build/refresh, score-floor silence, JSON transcript shape, action-entry compaction. Deterministic pieces (matcher scoring, budget trim, provenance formatting, transcript serialization) as fast unit tests.

## 10. Non-goals / deferred

- Any per-turn LLM or server call for injection (explicitly excluded — the local matcher is the whole point).
- Semantic/embedding-based section matching (revisit only if lexical matching demonstrably misses; start dumb).
- Client-side page splitting or curation (server/curator concern, §6).
- Progressive-deepening implementation details (worker scheduling, checkpoint format) — phased separately per §7.

## 11. File map (anticipated)

- `src/core/reflect.ts` (restored) — session reflect call + per-session cache.
- `src/core/section-index.ts` (new) — page → sections split, lexical scorer, budget trim, provenance formatting; pure/unit-testable.
- `src/core/hook.ts` — drop recall; inject cached reflect + matched sections; index refresh on roster cadence.
- `src/core/session-start.ts` — cold-repo seed (unchanged) + reflect trigger wiring + initial index build.
- `src/core/transcript.ts` (new or reworked) — JSON turn serialization + action-entry compaction for the Stop hook.
- `src/core/missions.ts` / `src/core/hindsight.ts` — remove `entity_labels` and tag-scoped page triggers; keep seeded taxonomy + `capture_initiative`.
- `src/core/config.ts` — remove any behavior flags; keep env/naming/harness + `pageRefreshEveryTurns`.
- Tests alongside each.
