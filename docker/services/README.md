# Distributed Hindsight Setup

Run API and Control Plane as separate containers.

## Start

```bash
cd services
docker-compose up
```

Access:
- **Control Plane**: http://localhost:3000  
- **API**: http://localhost:8888

## What's Running

Two separate containers:
- `api` - Hindsight API with embedded pg0 database
- `control-plane` - Web UI

## Build Images

```bash
./build-all.sh
```

Creates:
- `hindsight/api:latest`
- `hindsight/control-plane:latest`

## Configuration

The API uses embedded pg0 by default. Database files are stored in the `api_data` volume.

To use an external PostgreSQL database, add to `docker-compose.yml`:

```yaml
services:
  api:
    environment:
      HINDSIGHT_API_DATABASE_URL: postgresql://user:pass@host:5432/db
```

## Data Persistence

```bash
docker-compose down -v  # Remove volumes
```

## Why Use This?

The distributed setup is useful when you want to:
- Scale API and UI independently
- Use an external database in production
- Deploy to Kubernetes/orchestration
- Run UI on different infrastructure

For simple deployments, use the main `docker-compose.yml` (standalone all-in-one).
