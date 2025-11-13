# Release Guide

## Release Process

### 1. Generate OpenAPI Spec

```bash
uv sync
cd memora-dev
uv run generate-openapi
cd ..
```

### 2. Generate API Clients

```bash
./scripts/generate-clients.sh
```

This regenerates Python and TypeScript clients from `openapi.json`.


### 3. Commit Everything

```bash
git add openapi.json memora-clients/
git commit -m "Update OpenAPI spec and regenerate clients"
```

### 4. Run Release Script

```bash
./scripts/release.sh 0.0.6
```

This will:
- Update versions in all core components
- Commit changes
- Create and push tag `v0.0.6`
- Trigger GitHub Actions (builds Python package, Rust CLI, Docker images, Helm chart)

