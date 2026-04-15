---
hide_table_of_contents: true
---

# Paperclip Integration Changelog

Changelog for [`@vectorize-io/hindsight-paperclip`](https://www.npmjs.com/package/@vectorize-io/hindsight-paperclip).

For the source code, see [`hindsight-integrations/paperclip`](https://github.com/vectorize-io/hindsight/tree/main/hindsight-integrations/paperclip).

← [Back to main changelog](/changelog)

## [0.2.0](https://github.com/vectorize-io/hindsight/tree/integrations/paperclip/v0.2.0)

**Breaking Changes**

- Rewritten as a proper Paperclip plugin (installed via `pnpm paperclipai plugin install`). No code changes required — memory hooks run automatically via the event system.
- Works with all adapter types (Claude, Codex, Cursor, HTTP, Process). Previously required manual `recall()`/`retain()` calls and only supported HTTP adapter agents.

**Features**

- `agent.run.started` hook: auto-recalls context keyed to issue title + description
- `agent.run.finished` hook: auto-retains agent output with `runId` as document ID
- `hindsight_recall` and `hindsight_retain` agent tools for mid-run memory access
- `onValidateConfig`: live connectivity check when operator saves settings
- Configurable bank granularity (company+agent, company-only, agent-only)

## [0.1.2](https://github.com/vectorize-io/hindsight/tree/integrations/paperclip/v0.1.2)

**Improvements**

- Paperclip integration now sends an identifying User-Agent on all HTTP requests for better request tracing and compatibility. ([`9372462e`](https://github.com/vectorize-io/hindsight/commit/9372462e))

## [0.1.1](https://github.com/vectorize-io/hindsight/tree/integrations/paperclip/v0.1.1)

**Features**

- Added the Hindsight Paperclip TypeScript integration. ([`81441ee9`](https://github.com/vectorize-io/hindsight/commit/81441ee9))

**Bug Fixes**

- Fixed issues in the Paperclip integration based on review feedback. ([`7863ffeb`](https://github.com/vectorize-io/hindsight/commit/7863ffeb))
