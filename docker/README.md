# Hindsight Docker

Run Hindsight with Docker in standalone or distributed mode.

## Quick Start (Standalone)

```bash
cd docker
./start.sh
```

**Force rebuild after code changes:**
```bash
./start.sh --build        # Quick: rebuild and start
# or
./rebuild.sh              # Complete: rebuild from scratch (no cache)
```

Access:
- **Control Plane**: http://localhost:3000
- **API**: http://localhost:8888

Press `Ctrl+C` to stop.

## What You Get

**Standalone** (default, simple):
- One container with API + Control Plane + embedded database
- Perfect for local development and simple deployments

**Distributed** (advanced):
- Separate containers for API and Control Plane
- Better for production, scaling, or custom configurations

## Deployment Modes

### 1. Standalone (Recommended)

All-in-one container with embedded pg0 database.

```bash
./start.sh
# or
cd standalone
docker-compose up
```

**Data storage:** `/app/data` volume

### 2. Distributed (Advanced)

Separate API and Control Plane containers.

```bash
cd services
docker-compose up
```

**Data storage:** `api_data` volume

See `services/README.md` for details.

## Data Management

**Reset data:**
```bash
# Standalone
cd standalone && docker-compose down -v

# Distributed
cd services && docker-compose down -v
```

## Building Images

```bash
# Standalone
cd standalone
docker build -f Dockerfile -t hindsight:latest ../..

# Services
cd services
./build-all.sh
```

## Using External Database

Both modes use embedded pg0 by default. To use external PostgreSQL:

```bash
export HINDSIGHT_API_DATABASE_URL=postgresql://user:pass@host:5432/db
```

## Directory Structure

```
docker/
├── start.sh              # Quick start (standalone)
├── README.md             # This file
├── standalone/           # All-in-one deployment
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── start-all.sh
└── services/             # Distributed deployment
    ├── docker-compose.yml
    ├── api.Dockerfile
    ├── control-plane.Dockerfile
    ├── build-all.sh
    └── README.md
```

## Advanced Usage

**Background mode:**
```bash
cd standalone
docker-compose up -d
docker-compose logs -f
docker-compose down
```

**Custom configuration:**
Edit `standalone/docker-compose.yml` or `services/docker-compose.yml`

## Environment Variables

Hindsight requires configuration through environment variables (all prefixed with `HINDSIGHT_`).

### Required:
- `HINDSIGHT_API_LLM_API_KEY` - Your LLM API key (OpenAI, Anthropic, etc.)

### Optional:
- `HINDSIGHT_API_LLM_MODEL` - Model name (default: gpt-4o-mini)
- `HINDSIGHT_API_LLM_BASE_URL` - API base URL (default: https://api.openai.com/v1)
- `HINDSIGHT_API_LOG_LEVEL` - Logging level: debug, info, warning, error
- `HINDSIGHT_API_DATABASE_URL` - External PostgreSQL connection (uses embedded pg0 by default)

### Setup Options:

**Option 1: .env file (recommended)**
```bash
# Copy example file
cp .env.example .env

# Edit .env and add your API key
HINDSIGHT_API_LLM_API_KEY=sk-...
```

**Option 2: Export in shell**
```bash
export HINDSIGHT_API_LLM_API_KEY=sk-...
export HINDSIGHT_API_LLM_MODEL=gpt-4o-mini
```

The `start.sh` script automatically loads `.env` if it exists and validates the API key is set.
