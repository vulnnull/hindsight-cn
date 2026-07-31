---
sidebar_position: 6
title: "Coding Agents Memory Plugin (opencode, Kilo, Cline, Claude Code, Codex, Antigravity, Cursor, Copilot, Grok) | Integration Guide"
description: "One Hindsight memory plugin for coding agents — opencode, Kilo CLI, Cline CLI, Claude Code, Codex CLI, Antigravity CLI, Cursor CLI, GitHub Copilot CLI, Grok Build: per-repo memory banks built automatically from git history and sessions, session-level memory synthesis, and knowledge-page search."
---

# Coding Agents

Long-term **project memory** for coding agents, from one package: a shared reflect-and-inject core
with a thin entry point per agent — **opencode**, **Kilo CLI**, **Cline CLI**, **Claude Code**, **Codex CLI**, **Antigravity CLI**, **Cursor CLI**, **GitHub Copilot CLI**, **Grok Build** —
Ingestion into a [Hindsight](https://vectorize.io/hindsight) memory bank is fully automatic — no
setup command: git history and conversations flow in as you work.

The premise: most of a real fix is derivable from the code, but the *last mile* often hinges on a
project-specific decision that isn't in the code at all — a rounding rule, a retry allowlist, a
tie-break policy. Those decisions live in git history and past conversations. This plugin puts them
in front of the agent at the moment it starts working.

## How it works

1. **Automatic ingestion (no setup).** A cold repo is seeded in the background the first time an
   agent opens it (aggregated commit-message history + a headless codebase survey), and every
   session start fires an idempotent background **deepen engine** that ingests recent commits
   individually with their full diffs — newest first, a bounded batch per session — plus any
   conversations not yet in the bank. Retain strategies are tuned per content type, knowledge pages
   are synthesized from the extracted facts, and every item carries a `REF-ID` tracer. The
   `hindsight_sync_status` tool reports where ingestion stands (`synced: true` = seeded memory
   fully queryable).
2. **Reflect once per session.** On the session's first task message, the entry point sends that
   message to Hindsight `reflect`, which reasons over the bank and returns a synthesized
   **root-cause answer** — the exact rule and literal values that were decided, with citations.
3. **Inject every turn.** The reflect answer is pushed into the agent's context (system prompt on
   opencode; hook context on the hook harnesses, cached per session and re-injected on later
   prompts) so it survives long sessions and correction rounds. Alongside it, the repo's
   **knowledge pages** are matched *locally* against each prompt (a lexical section index — no
   server round-trip, no LLM call) and the top-scoring page sections are injected with provenance
   and a pointer to the full page; below a relevance floor nothing is injected.
4. **Write back.** Each session is upserted into the bank as a JSON transcript — user/assistant
   turns plus a compact `action` turn per tool call (tool name + primary target, no arguments or
   outputs) — so sessions compound into memory. On Stop for the hook harnesses; for the plugin
   harnesses (opencode, Kilo) on the turn cadence and again once the session goes idle, so the
   agent's own answer — including the last exchange before you close the session — is stored, not
   just your side of it. Cold repos are auto-seeded (aggregated git log + a short headless codebase
   survey) the first time an agent opens them.
5. **Never break the agent — never fail silently.** A failed reflect or page fetch degrades to
   no-memory, but every outcome (`reflect_ok` / `reflect_empty` / `reflect_failed`, `pages_ok` /
   `pages_failed`, with duration and error) is appended to a diagnostics file, so a memory-less
   session can't masquerade as a memory session.

If the configured Hindsight server predates knowledge pages, the client detects that capability at
session start, skips page seeding and page lookups, and records `knowledge_pages_unavailable`.
Legacy bank configuration, git/session ingestion, reflection, and retention continue normally.

When memories **conflict** on the same rule, reflect prefers the latest/superseding decision — a
rule amended in a later conversation wins over the original, and the superseded rule is reported as
no longer in effect.

## Supported agents

| harness       | kind              | entry point             | install |
| ------------- | ----------------- | ----------------------- | ------- |
| `opencode`    | persistent plugin | package default export  | add the package dir to `opencode.json` → `"plugin": [...]` |
| `kilo`        | persistent plugin | `dist/kilo.js` default export | `hindsight-coding-agents install kilo` adds a `file://` entry to `"plugin"` in `~/.config/kilo/kilo.json[c]`. Kilo CLI is an opencode fork and runs the identical plugin runtime |
| `claude-code` | per-prompt hook   | `hindsight-claude-hook` | `UserPromptSubmit` hook in Claude Code `settings.json` |
| `codex`       | per-prompt hook   | `hindsight-codex-hook`  | `UserPromptSubmit` hook in `~/.codex/hooks.json` (+ `codex_hooks = true`, Codex CLI ≥ 0.116) |
| `antigravity-cli` | lifecycle hooks | Antigravity hooks | `PreInvocation` + `Stop` in `~/.gemini/config/hooks.json`; MCP in `~/.gemini/config/mcp_config.json`; native colored `Hindsight · <bank>` status line |
| `cursor-cli`  | lifecycle hooks   | `hindsight-cursor-hook` | `sessionStart` seeds/pages; `beforeSubmitPrompt` recalls; `stop` retains in Cursor `hooks.json` |
| `copilot-cli` | lifecycle hooks   | `hindsight-copilot-hook` | `sessionStart` seeds/pages; `userPromptTransformed` appends recall to the model-facing prompt; `agentStop` retains in `~/.copilot/hooks/` |
| `grok-build` | lifecycle hooks   | `hindsight-grok-hook` | native `SessionStart` seeds the bank and `Stop` retains in `~/.grok/config.toml`; MCP is registered there too — no Claude Code dependency |
| `cline-cli` | persistent plugin | `dist/cline.js` default export | native `beforeModel` injects reflect/pages and `afterRun` retains the runtime transcript; `cline plugin install` is run by the installer |

One-command install (detects the coding agents on the machine, wires each natively — hooks + MCP;
idempotent, with `uninstall` removing exactly what it added):

```bash
npm install -g hindsight-coding-agents && hindsight-coding-agents install
```

On Claude Code the install also ships a companion skill (`hindsight-coding-agent`) so the agent
answers "how does this memory work / store this in hindsight / configure per-repo memory" from an
authoritative reference. Update with `npm update -g hindsight-coding-agents` — wired paths stay valid; re-run `install`
(idempotent) only when a release notes a wiring change.

Antigravity's status line is a local formatter that identifies the resolved Hindsight bank without
calling the API during TUI redraws. An existing custom Antigravity status-line command is preserved
and is not replaced by the installer.

### Grok Build limitation

Grok Build's `UserPromptSubmit` hook is **passive**: it runs the Hindsight reflect request, but
Grok ignores hook stdout, so it cannot place the resulting `<hindsight_memory>` block, bank banner,
or automatic first-prompt synthesis into the model-visible conversation. The Grok integration
therefore provides native bank setup and session retention, plus the Hindsight MCP tools and
companion skill. Ask Grok to call `hindsight_reflect` or `hindsight_search_knowledge_pages` when
memory is useful. Automatic prompt injection requires a future Grok prompt-transform API.

### Cline CLI scope

Cline uses its native plugin API rather than file hooks: `beforeModel` injects the
shared Hindsight reflect/pages context and `afterRun` upserts Cline's runtime transcript. The
installer runs `cline plugin install --force <package-path>` and also configures MCP and the
companion skill. Cline CLI currently sandboxes plugin hooks with a three-second limit, so a slow
first reflect is allowed to finish in the background and is injected on a subsequent model call or
turn rather than aborting the session.

For privacy and signal quality, Cline write-back retains only user-visible user and assistant text.
It excludes tool-call arguments, tool results and command output, tool-role messages, reasoning
parts, and Hindsight's own injected context. This covers Cline CLI only, not its VS Code or JetBrains extensions.

Manual wiring per harness:

```json title="opencode.json"
{ "plugin": ["/path/to/hindsight-coding-agents"] }
```

```json title="Claude Code settings.json — Codex ~/.codex/hooks.json is identical (command: hindsight-codex-hook)"
{ "hooks": { "UserPromptSubmit": [ { "hooks": [
    { "type": "command", "command": "hindsight-claude-hook" } ] } ] } }
```

```json title="Cursor hooks.json"
{ "hooks": { "sessionStart": [ { "command": "hindsight-cursor-sessionstart-hook" } ], "beforeSubmitPrompt": [ { "command": "hindsight-cursor-hook" } ], "stop": [ { "command": "hindsight-cursor-stop-hook" } ] } }
```

```json title="GitHub Copilot CLI ~/.copilot/hooks/hindsight-coding-agents.json"
{ "version": 1, "hooks": { "sessionStart": [ { "command": "hindsight-copilot-sessionstart-hook" } ], "userPromptTransformed": [ { "command": "hindsight-copilot-hook" } ], "agentStop": [ { "command": "hindsight-copilot-stop-hook" } ] } }
```

```toml title="Grok Build ~/.grok/config.toml"
[[hooks.SessionStart]]
  [[hooks.SessionStart.hooks]]
  type = "command"
  command = "hindsight-grok-sessionstart-hook"
  timeout = 30

[[hooks.Stop]]
  [[hooks.Stop.hooks]]
  type = "command"
  command = "hindsight-grok-stop-hook"
  timeout = 60

[mcp_servers.hindsight]
command = "node"
args = ["/absolute/path/to/hindsight-coding-agents/dist/mcp-server.js"]
```

Every harness gets the same agent tools (`hindsight_search_knowledge_pages`, `hindsight_reflect`,
page list/read, `hindsight_capture_initiative`, `hindsight_ingest_document`,
`hindsight_sync_status`) — natively on opencode, via the bundled MCP server elsewhere. Session
write-back is on by default everywhere; staying current with git needs no separate sync — the
ingestion engine re-runs idempotently at every session start.

## Configuration

All configuration is **one JSON file**: `~/.hindsight/coding-agent.json` (no environment
variables; exceptions: `HINDSIGHT_CONFIG` to relocate the file, `HINDSIGHT_DIAG_FILE` /
`HINDSIGHT_LOG_FILE` / `HINDSIGHT_LOG_LEVEL` for diagnostics). Later wins per field: built-in
defaults → the file's top level → its `harnesses.<name>` section for the asking agent → the
`banks.<resolvedBankId>` section for the repo's bank (applied AFTER bank resolution). There is no
repo-carried config — per-repo routing is `mapPathToBank`, per-repo behavior (including renaming
the bank) is `banks.<id>`, per-agent differences are `harnesses.<name>`.

Each entry point knows which harness it *is*, so one shared config serves several agents side by
side:

```jsonc
{
  "apiUrl": "http://localhost:8888",
  "harnesses": {
    "opencode":    { "reflectTimeoutMs": 60000 },
    "claude-code": { "disabled": true }          // memory off for Claude only
  },
  "banks": {
    "coding-agent::secret-client": { "disabled": true },      // per-repo blacklist
    "coding-agent::old-name": { "bank": "team::shared" },     // rename / converge banks
    "coding-agent::big-mono": { "gitIngest": "full", "retainSessions": false }
  }
}
```

### Reference

| field | default | meaning |
| --- | --- | --- |
| `apiUrl` | `http://localhost:8888` | Hindsight API base URL |
| `apiToken` | — | bearer token (Hindsight Cloud) |
| `bankId` | — | **explicit static bank**; unset ⇒ per-repo dynamic resolution (below) |
| `dynamicBankId` | dynamic iff no `bankId` | force dynamic (`true`) or static (`false`) resolution |
| `bankIdTemplate` | `"{gitProject}"` | dynamic bank id format, e.g. `"hindsight-{gitProject}"` |
| `mapPathToBank` | — | absolute path → bank; **longest prefix wins**; overrides everything |
| `resolveWorktrees` | `true` | `{gitProject}`: linked worktrees share the main repo's bank |
| `disabled` | `false` | hard off-switch (inert plugin/hook — a no-memory baseline) |
| `reflectTimeoutMs` | `120000` | session-reflect timeout (hook harnesses cap it at 25s to fit the host's hook window); on timeout the session runs without reflect (recorded in diagnostics) |
| `autoReflect` | `true` | inject a one-time reflect synthesis on the session's first prompt; `false` = tool-only mode — nothing is injected, and the tool guide instead instructs the agent to call `hindsight_reflect` itself whenever a new task/goal is set |
| `pageRefreshEveryTurns` | `10` | refetch the knowledge pages and re-inject the page roster + tool guide every N user turns |
| `retainSessions` | `true` | plugin-harness write-back (opencode, Kilo): async upsert every turn plus a flush when the session goes idle (set `false` to opt out; hook harnesses always write on Stop) |
| `retainEveryTurns` | `1` | write-back cadence (user turns) |
| `gitIngest` | `"message"` | git depth for seeding and staying current: `"message"` (messages only), `"full"` (messages + per-commit diffs), `"none"` |
| `logLevel` | `"info"` | plugin-log verbosity (`"debug"` \| `"info"` \| `"warn"` \| `"error"`); `HINDSIGHT_LOG_LEVEL` env overrides |
| `autoSeed` / `seedLimit` | `true` / `300` | automatic cold-repo seeding and its commit-message cap |
| `codebaseSurvey` / `surveyModel` / `surveyBudgetUsd` | `true` / `haiku` / `2` | cold-repo structural survey (runs under your agent's own CLI, read-only, spend-capped) |
| `surveyRefreshCommits` | `0` (off) | re-run the survey after N new commits so structural pages track an evolving architecture |
| `banks.<bankId>` | — | per-repo opt-in/out keyed by the resolved bank id: any behavioral field, plus `bank` to rename/converge the destination (single hop); resolution fields ignored inside |
| `harnesses.<name>` | — | per-harness override of any field above |

### Bank resolution — per-repo by default

Coding memory is **per repository**. Resolution order for the working directory:

1. `mapPathToBank` — longest matching absolute-path prefix (mapping a repo root covers every
   subdirectory; deeper mappings win; overrides even an explicit `bankId`).
2. Static — `bankId` set (or `dynamicBankId: false`).
3. Dynamic — `bankIdTemplate` with placeholders:
   - `{gitProject}` — worktree-aware repo name: every linked worktree resolves to the **main**
     worktree's basename, so all worktrees of a repo share one bank (bare repos use the bare dir
     name; non-git directories fall back to the dir basename)
   - `{project}` — plain working-directory basename
   - `{harness}` — the entry point asking (`opencode`, `claude-code`, `codex`, `antigravity-cli`, `cursor-cli`, `copilot-cli`, `grok-build`)
   - `{channel}` / `{user}` — `$HINDSIGHT_CHANNEL_ID` / `$HINDSIGHT_USER_ID`

4. **`banks.<id>` last**: the resolved id selects its section, whose `bank` field (if any) renames
   the destination — rename a bank or converge several onto one shared bank without touching the
   template.

The default template means **all agents share one memory per repo** — use
`"{harness}-{gitProject}"` to split per agent instead.

#### Recipe: two repos, one shared bank

Two ways, by what the natural key is:

**By resolved id** — you know the repo names; works wherever the repos live (and keeps working if
they move). Both ids converge on one literal target:

```jsonc
{
  "banks": {
    "coding-agent::backend":  { "bank": "team::product" },
    "coding-agent::frontend": { "bank": "team::product" }
  }
}
```

**By path prefix** — the repos live under one directory; a single `mapPathToBank` entry covers
every repo (present and future) beneath it:

```jsonc
{
  "mapPathToBank": { "/Users/me/work/client-x": "client-x-memory" }
}
```

**Blacklist a whole directory tree** — compose the two primitives: map the tree to one bank, disable
that bank. Every current and future directory beneath the prefix (`~` expands) is memory-off:

```jsonc
{
  "mapPathToBank": { "~/scratch": "scratch" },
  "banks": { "scratch": { "disabled": true } }
}
```

Rule of thumb: converge by **id** for a hand-picked set of repos; map by **path** when a folder is
the boundary ("everything I clone under `work/client-x` shares memory").


## Diagnostics

Every reflect and page-fetch outcome is appended as a JSON line to `/tmp/hindsight-plugin.log` (override with
`HINDSIGHT_DIAG_FILE`):

```json
{"ts":"2026-07-23T07:05:52Z","harness":"claude-code","event":"reflect_ok","ms":15816,"chars":324,"query":"..."}
```

`reflect_failed` records the error; if you're comparing memory-on vs memory-off, check this file —
a run whose reflects failed is a no-memory run.
