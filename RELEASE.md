# Release Guide

## Release Process

### 1. Generate OpenAPI Spec

```bash
uv sync
cd hindsight-dev
uv run generate-openapi
cd ..
```

### 2. Generate API Clients

```bash
./scripts/generate-clients.sh
```

This regenerates Python and TypeScript clients from `openapi.json`.

**Note:** Your `pyproject.toml` and `package.json` are preserved - only code is regenerated.

### 3. Commit Everything

```bash
git add openapi.json hindsight-clients/
git commit -m "Update OpenAPI spec and regenerate clients"
```

### 4. Run Release Script

```bash
./scripts/release.sh 0.0.6
```

This will:
- Update version to `0.0.6` in **all** components (core, clients, CLI, UI, Helm)
- Commit changes
- Create and push tag `v0.0.6`
- Trigger GitHub Actions (builds Python package, Rust CLI, Docker images, Helm chart)

---

## After GitHub Actions Complete

### Publish Python Client to PyPI

```bash
cd hindsight-clients/python
uv build
uv publish
```

### Publish TypeScript Client to NPM

```bash
cd hindsight-clients/typescript
npm install
npm run build
npm publish --access public
```

---

## Pre-Release Checklist

- [ ] Tests passing: `cd hindsight-api && uv run pytest tests`
- [ ] No uncommitted changes: `git status`
- [ ] On `main` branch

---

## Versioning

**Semantic Versioning: `MAJOR.MINOR.PATCH`**

- **PATCH** (0.0.6): Bug fixes, no API changes
- **MINOR** (0.1.0): New features, backward compatible
- **MAJOR** (1.0.0): Breaking changes

**All components use the same version** - coordinated releases for simplicity.

---

## Troubleshooting

**Tag already exists:**
```bash
git tag -d v0.0.6
git push origin :refs/tags/v0.0.6
```

**Working directory not clean:**
```bash
git status
# Commit or stash changes first
```

**GitHub Actions failed:**
- Check: https://github.com/vectorize-io/hindsight/actions
- Re-run failed jobs or fix and release new patch version

**Rollback:**
```bash
git tag -d v0.0.6
git push origin :refs/tags/v0.0.6
git revert HEAD
git push
```

---

## Quick Reference

```bash
# Full release workflow
uv sync
cd hindsight-dev && uv run generate-openapi && cd ..
./scripts/generate-clients.sh
git add openapi.json hindsight-clients/
git commit -m "Update OpenAPI spec and regenerate clients"
./scripts/release.sh 0.0.6

# After GH Actions complete:
cd hindsight-clients/python && uv build && uv publish
cd ../typescript && npm run build && npm publish --access public
```
