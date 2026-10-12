---
hide_table_of_contents: true
---

import PageHero from '@site/src/components/PageHero';

<PageHero title="Cursor Changelog" subtitle="hindsight-memory - Hindsight memory plugin for Cursor." />

[← Cursor integration](../../sdks/integrations/cursor.md)

## [0.2.1](https://github.com/vectorize-io/hindsight/tree/integrations/cursor/v0.2.1)

[Commits in this release →](https://github.com/vectorize-io/hindsight/commits/integrations/cursor/v0.2.1)

**Features**

- Cursor Agent CLI can now be used as an LLM provider.<span style={{color: "var(--ifm-color-emphasis-500)", margin: "0 0.3em"}}>·</span><a href="https://github.com/nicoloboschi" target="_blank" rel="noopener noreferrer" style={{color: "var(--ifm-color-primary)", textDecoration: "none", display: "inline-flex", alignItems: "center", gap: "4px", verticalAlign: "middle"}}>@nicoloboschi</a><span style={{color: "var(--ifm-color-emphasis-500)", margin: "0 0.3em"}}>·</span><a href="https://github.com/vectorize-io/hindsight/commit/8bc5ab103" target="_blank" rel="noopener noreferrer" style={{fontFamily: "var(--ifm-font-family-monospace, monospace)", fontSize: "0.85em", color: "var(--ifm-color-emphasis-600)"}}>8bc5ab103</a>

**Improvements**

- Cursor and other integrations now identify themselves with integration-specific User-Agent headers.<span style={{color: "var(--ifm-color-emphasis-500)", margin: "0 0.3em"}}>·</span><a href="https://github.com/nicoloboschi" target="_blank" rel="noopener noreferrer" style={{color: "var(--ifm-color-primary)", textDecoration: "none", display: "inline-flex", alignItems: "center", gap: "4px", verticalAlign: "middle"}}>@nicoloboschi</a><span style={{color: "var(--ifm-color-emphasis-500)", margin: "0 0.3em"}}>·</span><a href="https://github.com/vectorize-io/hindsight/commit/5d4f5cfcd" target="_blank" rel="noopener noreferrer" style={{fontFamily: "var(--ifm-font-family-monospace, monospace)", fontSize: "0.85em", color: "var(--ifm-color-emphasis-600)"}}>5d4f5cfcd</a>
- Integrations launched through uvx now select a Python version compatible with the daemon.<span style={{color: "var(--ifm-color-emphasis-500)", margin: "0 0.3em"}}>·</span><a href="https://github.com/r266-tech" target="_blank" rel="noopener noreferrer" style={{color: "var(--ifm-color-primary)", textDecoration: "none", display: "inline-flex", alignItems: "center", gap: "4px", verticalAlign: "middle"}}>@r266-tech</a><span style={{color: "var(--ifm-color-emphasis-500)", margin: "0 0.3em"}}>·</span><a href="https://github.com/vectorize-io/hindsight/commit/6c8a92c31" target="_blank" rel="noopener noreferrer" style={{fontFamily: "var(--ifm-font-family-monospace, monospace)", fontSize: "0.85em", color: "var(--ifm-color-emphasis-600)"}}>6c8a92c31</a>

**Bug Fixes**

- Cursor now accepts BOM-prefixed input and correctly scopes memory banks to workspace roots.<span style={{color: "var(--ifm-color-emphasis-500)", margin: "0 0.3em"}}>·</span><a href="https://github.com/nicoloboschi" target="_blank" rel="noopener noreferrer" style={{color: "var(--ifm-color-primary)", textDecoration: "none", display: "inline-flex", alignItems: "center", gap: "4px", verticalAlign: "middle"}}>@nicoloboschi</a><span style={{color: "var(--ifm-color-emphasis-500)", margin: "0 0.3em"}}>·</span><a href="https://github.com/vectorize-io/hindsight/commit/ab27418eb" target="_blank" rel="noopener noreferrer" style={{fontFamily: "var(--ifm-font-family-monospace, monospace)", fontSize: "0.85em", color: "var(--ifm-color-emphasis-600)"}}>ab27418eb</a>
- Cursor reliably installs its hooks and rules and flushes pending memories when a session ends.<span style={{color: "var(--ifm-color-emphasis-500)", margin: "0 0.3em"}}>·</span><a href="https://github.com/nicoloboschi" target="_blank" rel="noopener noreferrer" style={{color: "var(--ifm-color-primary)", textDecoration: "none", display: "inline-flex", alignItems: "center", gap: "4px", verticalAlign: "middle"}}>@nicoloboschi</a><span style={{color: "var(--ifm-color-emphasis-500)", margin: "0 0.3em"}}>·</span><a href="https://github.com/vectorize-io/hindsight/commit/682f77a22" target="_blank" rel="noopener noreferrer" style={{fontFamily: "var(--ifm-font-family-monospace, monospace)", fontSize: "0.85em", color: "var(--ifm-color-emphasis-600)"}}>682f77a22</a>
- In-flight Cursor integration requests are no longer terminated by the daemon idle timeout.<span style={{color: "var(--ifm-color-emphasis-500)", margin: "0 0.3em"}}>·</span><a href="https://github.com/nicoloboschi" target="_blank" rel="noopener noreferrer" style={{color: "var(--ifm-color-primary)", textDecoration: "none", display: "inline-flex", alignItems: "center", gap: "4px", verticalAlign: "middle"}}>@nicoloboschi</a><span style={{color: "var(--ifm-color-emphasis-500)", margin: "0 0.3em"}}>·</span><a href="https://github.com/vectorize-io/hindsight/commit/d7d137fa1" target="_blank" rel="noopener noreferrer" style={{fontFamily: "var(--ifm-font-family-monospace, monospace)", fontSize: "0.85em", color: "var(--ifm-color-emphasis-600)"}}>d7d137fa1</a>

## [0.2.0](https://github.com/vectorize-io/hindsight/tree/integrations/cursor/v0.2.0)

**Features**

- Added a Hindsight memory plugin integration for Cursor.<span style={{color: "var(--ifm-color-emphasis-500)", margin: "0 0.3em"}}>·</span><a href="https://github.com/DK09876" target="_blank" rel="noopener noreferrer" style={{color: "var(--ifm-color-primary)", textDecoration: "none", display: "inline-flex", alignItems: "center", gap: "4px", verticalAlign: "middle"}}>@DK09876</a><span style={{color: "var(--ifm-color-emphasis-500)", margin: "0 0.3em"}}>·</span><a href="https://github.com/vectorize-io/hindsight/commit/91d767cdc" target="_blank" rel="noopener noreferrer" style={{fontFamily: "var(--ifm-font-family-monospace, monospace)", fontSize: "0.85em", color: "var(--ifm-color-emphasis-600)"}}>91d767cdc</a>

## [0.1.0](https://github.com/vectorize-io/hindsight/tree/main/hindsight-integrations/cursor)

**Features**

- Added a Hindsight memory plugin for Cursor using Cursor's plugin hooks for automatic recall and retain.
- Added Cursor-native extras including an always-on rule and an on-demand `hindsight-recall` skill.
- Added support for local daemon mode, external Hindsight APIs, and native MCP as an alternative integration path.
- Added automated tests covering config loading, bank derivation, content formatting, and hook behavior.
