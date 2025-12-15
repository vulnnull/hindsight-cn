---
sidebar_position: 1
---

# Changelog

For full release details, see [GitHub Releases](https://github.com/vectorize-io/hindsight/releases).

## [0.1.5](https://github.com/vectorize-io/hindsight/releases/tag/v0.1.5)

**Features**

- Added LiteLLM integration so Hindsight can capture and manage memories from LiteLLM-based LLM calls. ([`dfccbf2`](https://github.com/vectorize-io/hindsight/commit/dfccbf2))
- Added an optional graph-based retriever (MPFP) to improve recall by leveraging relationships between memories. ([`7445cef`](https://github.com/vectorize-io/hindsight/commit/7445cef))

**Improvements**

- Switched the embedded Postgres layer to pg0-embedded for a smoother local/standalone experience. ([`94c2b85`](https://github.com/vectorize-io/hindsight/commit/94c2b85))

**Bug Fixes**

- Fixed repeated retries on 400 errors from the LLM, preventing unnecessary request loops and failures. ([`70983f5`](https://github.com/vectorize-io/hindsight/commit/70983f5))
- Fixed recall trace visualization in the control plane so search/recall debugging displays correctly. ([`922164e`](https://github.com/vectorize-io/hindsight/commit/922164e))
- Fixed the CLI installer to make installation more reliable. ([`158a6aa`](https://github.com/vectorize-io/hindsight/commit/158a6aa))
- Updated Next.js to patch security vulnerabilities (CVE-2025-55184, CVE-2025-55183). ([`f018cc5`](https://github.com/vectorize-io/hindsight/commit/f018cc5))

## [0.1.3](https://github.com/vectorize-io/hindsight/releases/tag/v0.1.3)

**Improvements**

- Improved CLI and UI branding/polish, including new banner/logo assets and updated interface styling. ([`fa554b8`](https://github.com/vectorize-io/hindsight/commit/fa554b8))


## [0.1.2](https://github.com/vectorize-io/hindsight/releases/tag/v0.1.2)

**Bug Fixes**

- Fixed the standalone Docker image so it builds/runs correctly. ([`1056a20`](https://github.com/vectorize-io/hindsight/commit/1056a20))
