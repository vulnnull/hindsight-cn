---
hide_table_of_contents: true
---

import PageHero from '@site/src/components/PageHero';

<PageHero title="Vercel Chat SDK Changelog" subtitle="@vectorize-io/hindsight-chat — memory integration for Vercel Chat SDK." />

[← Vercel Chat SDK integration](../../sdks/integrations/chat.md)

## [0.4.21](https://github.com/vectorize-io/hindsight/tree/integrations/chat/v0.4.21)

[Commits in this release →](https://github.com/vectorize-io/hindsight/commits/integrations/chat/v0.4.21)

**Bug Fixes**

- Configured recall tag filters are now forwarded so chat memory searches return only appropriately tagged memories.<span style={{color: "var(--ifm-color-emphasis-500)", margin: "0 0.3em"}}>·</span><a href="https://github.com/rudycelekli" target="_blank" rel="noopener noreferrer" style={{color: "var(--ifm-color-primary)", textDecoration: "none", display: "inline-flex", alignItems: "center", gap: "4px", verticalAlign: "middle"}}>@rudycelekli</a><span style={{color: "var(--ifm-color-emphasis-500)", margin: "0 0.3em"}}>·</span><a href="https://github.com/vectorize-io/hindsight/commit/7a526ae8e" target="_blank" rel="noopener noreferrer" style={{fontFamily: "var(--ifm-font-family-monospace, monospace)", fontSize: "0.85em", color: "var(--ifm-color-emphasis-600)"}}>7a526ae8e</a>

## [0.4.20](https://github.com/vectorize-io/hindsight/tree/integrations/chat/v0.4.20)

**Features**

- Added Chat SDK integration to enable persistent memory for chat bots. ([`fed987f9`](https://github.com/vectorize-io/hindsight/commit/fed987f9))
- Added Deno compatibility for the TypeScript client. ([`72c25c97`](https://github.com/vectorize-io/hindsight/commit/72c25c97))

**Bug Fixes**

- Resolved security vulnerabilities in dependencies used across integrations. ([`b6a4f17c`](https://github.com/vectorize-io/hindsight/commit/b6a4f17c))
