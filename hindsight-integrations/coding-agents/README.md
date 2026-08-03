# hindsight-coding-agents

Long-term project memory for **coding agents**, backed by [Hindsight](https://vectorize.io/hindsight).
One package, several agents: a shared reflect-and-inject core with a thin entry point per agent
(**opencode**, **Kilo CLI**, **Cline CLI**, **Claude Code**, **Codex CLI**, **Antigravity CLI**, **Cursor CLI**, **GitHub Copilot CLI**, **Grok Build**). Ingestion is fully
automatic — there is no setup command: a repo's git history and conversations flow into its memory
bank in the background as you work.

The premise: most of a real fix is derivable from the code, but the _last mile_ often hinges on a
project-specific decision that isn't in the code at all — a rounding rule, a retry allowlist, a
tie-break policy. Those decisions live in git history and past conversations. This package puts them
in front of the agent at the moment it starts working, and keeps a curated set of **knowledge pages**
(architecture, conventions, in-flight initiatives) that future sessions start from.

## How it works

1. **Seed a cold repo (automatic, once).** The first time an agent opens a repo whose bank is empty,
   the entry point deterministically kicks off a background **seed**: it aggregates the last N commit
   **messages** into a single cheap document (`gitlog` strategy) and spawns a short headless
   **codebase survey** — run under the current agent's own CLI (claude/codex/antigravity/opencode),
   read-only sandboxed — to map the structure. Both feed the knowledge pages.
1. **Deepen progressively (automatic, every session).** Every session start also fires the
   idempotent background **deepen engine**: it ingests any conversations not yet in the bank and the
   next batch of recent commits **individually with their full diffs, newest first** — so full
   decision-level precision arrives across sessions without a big-bang ingest. A per-bank lock and
   document-id dedup make concurrent or repeated runs a no-op. Ask the agent
   `hindsight_sync_status` to see where ingestion stands (`synced: true` = seeded memory fully
   queryable).
1. **Reflect once per session.** On the session's first prompt, the entry point runs Hindsight
   `reflect` — an agentic synthesis over the bank that returns the past decision explaining the task
   at hand, with its exact rule and literal values. The answer is cached for the session and
   re-injected on every turn, wrapped in a visible-attribution directive so the agent surfaces a
   `🧠 Using Hindsight Memories` header when memory informs its answer.
1. **Knowledge-page sections every turn.** The repo's knowledge pages are fetched on a cadence and
   matched **locally** against each prompt (a lexical section index — no server round-trip, no LLM
   call, ~ms): the top-scoring page sections are injected with provenance and a pointer to the full
   page. Fast like recall, organized like reflect; below a relevance floor nothing is injected.
1. **Knowledge pages + tools.** At session start the agent is given the repo's page roster plus a
   guide to the `hindsight_*` tools; it lists/reads pages to ground itself, searches raw memory for
   specifics (`hindsight_search_memory` is where recall lives now), and calls
   `hindsight_capture_initiative` right after a plan is approved to record a new feature as a tracked
   page. On opencode these tools are registered natively; the hook harnesses get them through the
   bundled **MCP server**.
1. **Write back.** The live session is upserted into the bank as a JSON transcript — user/assistant
   turns plus a compact `action` turn per tool call (tool name + primary target, e.g.
   `Edit boltons/strutils.py`; no arguments or outputs) — so sessions compound into memory without
   burying decisions in mechanical noise. On Stop for the hook harnesses; for the plugin harnesses
   (opencode, Kilo) on the turn cadence **and** again when the session goes idle. The idle pass is
   what captures the agent's reply: the per-turn hook fires while the host is building a request, so
   the transcript it sees always stops short of the answer that request produces — without the idle
   pass, write-back lagged a turn and a session's final exchange was never stored at all.
1. **Never break the agent — never fail silently.** A failed reflect or page fetch degrades to
   no-memory, but every outcome (`reflect_ok` / `reflect_empty` / `reflect_failed`, `pages_ok` /
   `pages_failed`, with duration and error) is appended to a diagnostics file, so a memory-less
   session can't masquerade as a memory session.

If the configured Hindsight server predates knowledge pages, the client detects that capability at
session start, skips page seeding and page lookups, and records `knowledge_pages_unavailable`.
Legacy bank configuration, git/session ingestion, reflection, and retention continue normally.

When memories **conflict** on the same rule, reflect prefers the latest/superseding decision — a rule
amended in a later conversation wins over the original.

## Harnesses

Every harness runs the same surface (seed → session reflect → per-turn page sections → knowledge
tools → write-back); they differ only in how that surface is delivered.

| harness                   | kind              | lifecycle wiring                                                                                                                   | install                                                             |
| ------------------------- | ----------------- | ---------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `opencode`                | persistent plugin | one process: load-time seed, session reflect + page sections, native tools, write-back                                             | add the package dir to `opencode.json` → `"plugin": [...]`          |
| `kilo`                    | persistent plugin | identical to `opencode` — Kilo CLI is an opencode fork, so it loads the same runtime (no hooks system)                             | `hindsight-coding-agents install kilo` → `kilo.json[c]` `"plugin"`  |
| `claude-code`             | per-prompt hooks  | `SessionStart` (seed) + `UserPromptSubmit` (reflect + pages) + `Stop` (write-back) + MCP                                           | `hindsight-coding-agents install claude-code`                       |
| `codex`                   | per-prompt hooks  | same three hooks in `~/.codex/hooks.json` (+ `codex_hooks = true`, CLI ≥ 0.116)                                                    | `hindsight-coding-agents install codex`                             |
| `antigravity-cli` (`agy`) | lifecycle hooks   | Antigravity CLI lifecycle hooks (`PreInvocation` + `Stop`) + MCP, plus a native colored `Hindsight · <bank>` status-line indicator | `hindsight-coding-agents install agy`                               |
| `cursor-cli`              | lifecycle hooks   | `sessionStart` (seed + pages) + `beforeSubmitPrompt` (reflect) + `stop` (write-back)                                               | hooks in Cursor `hooks.json`                                        |
| `copilot-cli`             | lifecycle hooks   | `sessionStart` (seed + pages) + `userPromptTransformed` (reflect) + `agentStop` (write-back) + MCP                                 | `~/.copilot/hooks/hindsight-coding-agents.json` + `mcp-config.json` |
| `grok-build`              | lifecycle hooks   | `SessionStart` (seed) + `Stop` (write-back) + MCP                                                                                  | native `~/.grok/config.toml` — no Claude Code dependency            |
| `cline-cli`               | persistent plugin | native `beforeModel` (seed/reflect/pages) + `afterRun` (write-back) + MCP                                                          | `cline plugin install` (run by the installer)                       |

The hook-based harnesses share one runtime (`src/core/hook.ts`) plus their SessionStart/Stop
entrypoints. Persistent-plugin hosts (opencode/Kilo/Cline) delegate to the same `RuntimeCore`,
which in turn calls those shared session-start, prompt, and retain operations; only their host API
adapters differ. Opencode and Kilo can register the knowledge tools natively; Cline uses the shared
MCP server. All support opt-in **incremental git-sync** (retain commits new since the seed on load).

Antigravity renders the Hindsight indicator with its documented custom status-line command. It is
local and never calls the Hindsight API while the TUI redraws. If you already configured an
Antigravity custom status line, the installer leaves it untouched rather than replacing it.

### Grok Build limitation

Grok Build executes `UserPromptSubmit` hooks but ignores their stdout. Hindsight can therefore not
inject a reflect result, memory block, or banner into Grok's model-visible conversation. Grok still
gets native bank setup and transcript retention plus Hindsight MCP tools and the companion skill;
ask it to call `hindsight_reflect` or `hindsight_search_knowledge_pages` when needed. Automatic
injection requires a future Grok prompt-transform API.

### Cline CLI scope

Cline's external file hooks cannot alter a model request, so Hindsight uses Cline's native plugin
API instead. Its `beforeModel` hook injects the shared reflect/page context and
its `afterRun` hook upserts Cline's runtime transcript. `hindsight-coding-agents install cline-cli`
runs `cline plugin install --force <package-path>` and configures MCP plus the companion skill.
Cline CLI sandboxes plugin hooks with a three-second limit, so a slow first reflect finishes in the
background and is injected on a subsequent model call or turn rather than aborting the session.
Its write-back retains only user-visible user/assistant text; tool arguments, tool results and
command output, tool-role messages, reasoning parts, and Hindsight's injected context are excluded.
Cline IDE extensions are not currently supported by this CLI integration.

### Install — one command, every agent

```bash
npm install -g @vectorize-io/hindsight-coding-agents
hindsight-coding-agents install            # detects your agents, wires each natively
hindsight-coding-agents install codex      # or pick specific harnesses
hindsight-coding-agents uninstall          # removes exactly what install added
```

Install globally (not `npx`): the wiring points at this package's files, so it must live at a
stable path — the installer refuses to run from an npx cache. **Updating** is just
`npm update -g @vectorize-io/hindsight-coding-agents`: the wired paths stay valid, every new session runs the
new version; re-run `install` (idempotent) only when a release note says the wiring changed.

`install` merges the native wiring (hooks + MCP registration where the host wants them) into each
agent's own config, preserving everything already there; it is idempotent (re-run after moving the
package) and backs up any pre-existing file it touches as `<file>.hindsight-backup`. `uninstall`
removes only our entries. On Claude Code the install also ships a **companion skill**
(`~/.claude/skills/hindsight-coding-agent`) that teaches the agent how this memory works — what
"store this in hindsight" should do, the tool surface, per-repo configuration, debugging — so users
can ask the agent itself. Manual wiring per harness, if you prefer:

**opencode** installs directly — point `opencode.json` at the package dir:

```json
{ "plugin": ["/path/to/hindsight-coding-agents"] }
```

**Claude Code** and **Codex** get their full three-hook + MCP wiring from this package's own
installer — `hindsight-coding-agents install claude-code` / `install codex`. This package's `bin`
entries (`hindsight-claude-hook`, `hindsight-codex-hook`,
`hindsight-cursor-hook`) are the individual injection-only `UserPromptSubmit` entrypoints for a
minimal, hand-wired setup.

Adding an agent: hook-based → write a `HookSpec` entry point (see `src/cursor-hook.ts`) and register
a `hookAdapter` in `src/harness/registry.ts`; persistent-plugin → implement `HarnessAdapter`
(`src/core/types.ts`) fully (see `src/harness/opencode.ts`).

## Configuration

All configuration is **ONE JSON file, no environment variables** (exception: `HINDSIGHT_DIAG_FILE`
for the diagnostics path): `~/.hindsight/coding-agent.json`. Layering, later wins per field:

1. built-in defaults
2. the file's top level
3. its `harnesses.<name>` section — per-agent override

There is deliberately no repo-carried config file — per-repo bank routing is `mapPathToBank`,
per-agent differences are `harnesses.<name>`.

Each entry point knows which harness it _is_ (the opencode plugin is loaded by opencode, the codex
hook by Codex...), so one shared config serves several agents side by side:

```jsonc
{
  "apiUrl": "https://api.hindsight.vectorize.io",
  "harnesses": {
    "opencode": { "reflectTimeoutMs": 60000 },
    "claude-code": { "disabled": true }, // e.g. memory off for Claude only
  },
}
```

### Reference

| field                   | default                              | meaning                                                                                                                                                                                                                             |
| ----------------------- | ------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `apiUrl`                | `https://api.hindsight.vectorize.io` | Hindsight API base URL (set to `http://localhost:8888` for a local server)                                                                                                                                                          |
| `apiToken`              | —                                    | bearer token (Hindsight Cloud)                                                                                                                                                                                                      |
| `bankId`                | —                                    | **explicit static bank**; unset ⇒ per-repo dynamic resolution (below)                                                                                                                                                               |
| `dynamicBankId`         | dynamic iff no `bankId`              | force dynamic (`true`) or static (`false`) resolution                                                                                                                                                                               |
| `bankIdTemplate`        | `"coding-agent::{gitProject}"`       | dynamic bank id format; the default makes every agent share one bank per repo                                                                                                                                                       |
| `mapPathToBank`         | —                                    | absolute path → bank; **longest prefix wins**; overrides everything                                                                                                                                                                 |
| `resolveWorktrees`      | `true`                               | `{gitProject}`: linked worktrees share the main repo's bank                                                                                                                                                                         |
| `disabled`              | `false`                              | hard off-switch (inert plugin/hook — a no-memory baseline)                                                                                                                                                                          |
| `reflectTimeoutMs`      | `120000`                             | session-reflect timeout (hook harnesses additionally cap it at 25s to fit the host's hook window); on timeout the session runs without reflect (recorded)                                                                           |
| `pageRefreshEveryTurns` | `10`                                 | refetch the knowledge pages and re-inject the page roster + tool guide every N user turns                                                                                                                                           |
| `autoSeed`              | `true`                               | SessionStart: auto-seed a cold repo's bank from git history                                                                                                                                                                         |
| `seedLimit`             | `300`                                | auto-seed: most-recent-N-commits cap                                                                                                                                                                                                |
| `codebaseSurvey`        | `true`                               | SessionStart: headless survey of a cold repo's structure, run under the current harness's own CLI (claude/codex/antigravity/opencode), falling back to any available agent                                                          |
| `surveyModel`           | `haiku`                              | model for the survey — Claude recipe only (`claude -p --model`); other agents use their configured default                                                                                                                          |
| `surveyBudgetUsd`       | `2`                                  | survey spend cap — Claude recipe only (`claude -p --max-budget-usd`); other agents rely on their read-only sandbox                                                                                                                  |
| `retainSessions`        | `true`                               | plugin-harness write-back (opencode, Kilo): async upsert of the session transcript every turn, plus an idle flush that captures the reply the per-turn pass can't see (set `false` to opt out; hook harnesses always write on Stop) |
| `retainEveryTurns`      | `1`                                  | opencode write-back cadence (user turns)                                                                                                                                                                                            |
| `logLevel`              | `"info"`                             | plugin-log verbosity (`"debug"` \| `"info"` \| `"warn"` \| `"error"`); `HINDSIGHT_LOG_LEVEL` env overrides                                                                                                                          |
| `gitIngest`             | `"message"`                          | git depth for seeding AND staying current (same engine): `"message"` = commit messages only (one doc, re-upserted when HEAD moves); `"full"` = messages + per-commit full diffs (progressive, newest first); `"none"` = git off     |
| `harnesses.<name>`      | —                                    | per-harness override of any field above                                                                                                                                                                                             |
| `harness`               | `opencode`                           | **deepen engine only**: which session format `--conversations` is read as                                                                                                                                                           |

### Per-repo opt-in/out — `banks.<bankId>`

Per-repo control lives in the SAME file, keyed by the **resolved bank id** (shown in the session
banner) and applied AFTER bank resolution — so it works regardless of where the repo lives, and
survives directory moves:

```jsonc
{
  "banks": {
    "coding-agent::secret-client": { "disabled": true }, // blacklist: no memory at all
    "coding-agent::old-name": { "bank": "team::shared" }, // rename / converge banks
    "coding-agent::big-mono": { "gitIngest": "full", "retainSessions": false },
  },
}
```

Any behavioral field can be overridden per bank, and `bank` **renames the destination** (single
hop: the section is selected by the resolved id, the target is literal — several ids may converge
on one shared bank, and the target's own section is not consulted). Other bank-resolution fields
are ignored inside a bank section.

#### Recipe: two repos, one shared bank

Two ways, by what the natural key is:

**By resolved id** — you know the repo names; works wherever the repos live (and keeps working if
they move). Both ids converge on one literal target:

```jsonc
{
  "banks": {
    "coding-agent::backend": { "bank": "team::product" },
    "coding-agent::frontend": { "bank": "team::product" },
  },
}
```

**By path prefix** — the repos live under one directory; a single `mapPathToBank` entry covers
every repo (present and future) beneath it:

```jsonc
{
  "mapPathToBank": { "/Users/me/work/client-x": "client-x-memory" },
}
```

Rule of thumb: converge by **id** for a hand-picked set of repos; map by **path** when a folder is
the boundary ("everything I clone under `work/client-x` shares memory").

### Bank resolution

Coding memory is **per repository**. Resolution order for the working directory:

1. `mapPathToBank` — longest matching absolute-path prefix (mapping a repo root covers every
   subdirectory; deeper mappings win; overrides even an explicit `bankId`).
2. Static — `bankId` set (or `dynamicBankId: false`).
3. Dynamic — `bankIdTemplate` with placeholders:
   - `{gitProject}` — worktree-aware repo name: `git rev-parse --git-common-dir` resolves every
     linked worktree to the **main** worktree's basename, so all worktrees of a repo share one bank
     (bare repos use the bare dir name; non-git directories fall back to the dir basename)
   - `{project}` — plain working-directory basename
   - `{harness}` — the entry point asking (`opencode`, `claude-code`, `codex`, `antigravity-cli`, `cursor-cli`, `copilot-cli`)
   - `{channel}` / `{user}` — `$HINDSIGHT_CHANNEL_ID` / `$HINDSIGHT_USER_ID`

The default `"coding-agent::{gitProject}"` is **harness-neutral**, so opencode, Claude Code, and Codex
all share one memory per repo — use `"{harness}-{gitProject}"` to split per agent instead.

## Ingestion internals (no CLI)

There is no user-facing ingest command — the deepen engine (`dist/deepen.js`) is spawned by every
session start and does only the missing work: bank configuration, conversation import (dedup by
document id), the one-time gitlog seed, the next per-commit diff batch (newest first, bounded per
run), then knowledge pages once extraction has drained. Harnesses that need deterministic ingestion
(benchmarks, e2e suites) run the same engine directly and poll `dist/status.js` until
`"synced": true` — the exact readiness contract the `hindsight_sync_status` agent tool reports.

Past-conversation import accepts a normalized interchange file (engine `--conversations` flag):
`[{ "id": "s1", "turns": [{ "role": "user", "text": "...", "timestamp?": "ISO" }, ...] }, ...]`,
chronological (a later chat can amend an earlier one). Day-to-day, conversations simply accrue from
the live session write-back — no export step.

Local Hindsight for trying it out:

```bash
docker run -d -p 8888:8888 -p 9999:9999 -e HINDSIGHT_API_LLM_PROVIDER=gemini \
  -e HINDSIGHT_API_LLM_API_KEY=$GEMINI_API_KEY -e HINDSIGHT_API_LLM_MODEL=gemini-2.5-flash \
  ghcr.io/vectorize-io/hindsight:latest
```

## Diagnostics & logging

Two files, two audiences:

**Leveled plugin log** (humans debugging): `$TMPDIR/hindsight-coding-agent/plugin.log` (override
`HINDSIGHT_LOG_FILE`) — timestamped `LEVEL [scope] message` lines from every component, including
the ingestion engine. Level defaults to `info`; set `"logLevel": "debug"` in config or
`HINDSIGHT_LOG_LEVEL=debug` for ad-hoc debugging (at `debug`, every diag event below is mirrored
here too, so one file tells the whole story).

**Structured diag events** (machines/harnesses): every reflect and page-fetch outcome is appended
as a JSON line to `/tmp/hindsight-plugin.log` (override with `HINDSIGHT_DIAG_FILE`):

```json
{
  "ts": "2026-07-27T07:05:52Z",
  "harness": "claude-code",
  "event": "reflect_ok",
  "ms": 14210,
  "chars": 792,
  "query": "..."
}
```

`reflect_failed` / `pages_failed` record the error; if you're comparing memory-on vs memory-off,
check this file — a run whose reflects failed is a no-memory run. Seed starts are logged as
`seed_started`.

## Layout

```
src/
  core/          # harness-agnostic: config (layered), bank resolution, hindsight client, missions,
                 # git + chat ingest, git-sync, seed + survey, pages-index (local section matching),
                 # knowledge-injection, knowledge-tools, session-start, transcript readers,
                 # hook runtime, RuntimeCore
  harness/       # per-agent adapters + registry (opencode persistent; claude/codex/antigravity/cursor/copilot as hooks)
  index.ts       # opencode plugin entrypoint
  claude-hook.ts / claude-sessionstart-hook.ts / claude-stop-hook.ts   # Claude Code entrypoints
  codex-hook.ts  / codex-sessionstart-hook.ts  / codex-stop-hook.ts    # Codex CLI entrypoints
  antigravity-hook.ts / antigravity-stop-hook.ts # Antigravity CLI entrypoints
  cursor-hook.ts # Cursor CLI hook entrypoint   (bin: hindsight-cursor-hook)
  copilot-*.ts   # GitHub Copilot CLI SessionStart/prompt/agentStop entrypoints
  mcp-server.ts  # hindsight_* knowledge/recall tools for the hook harnesses (MCP)
  backfill.ts    # backfill CLI                  (bin: hindsight-coding-backfill)
```
