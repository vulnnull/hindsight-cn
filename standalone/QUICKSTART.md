# Memora Standalone - Quick Start

## What is this?

A single Docker image containing everything you need to run Memora:
- ✅ PostgreSQL database
- ✅ Dataplane API (FastAPI backend)
- ✅ Control Plane (Next.js web UI)

## Fastest Start (Docker Compose)

```bash
cd standalone
docker-compose up -d
```

Access the UI at: **http://localhost:3000**

## Manual Docker Build & Run

### Build the image:
```bash
./standalone/build-docker.sh
```

### Run with the helper script:
```bash
./standalone/run-docker.sh --persist
```

### Or run directly:
```bash
docker run -d \
  --name memora \
  -p 3000:3000 \
  -p 8080:8080 \
  -p 5432:5432 \
  -v memora-data:/var/lib/postgresql/data \
  memora-standalone:latest
```

## Access Points

| Service | URL | Purpose |
|---------|-----|---------|
| **Control Plane** | http://localhost:3000 | Web UI |
| **Dataplane API** | http://localhost:8080 | REST API |
| **PostgreSQL** | localhost:5432 | Database |

## View Logs

```bash
docker logs -f memora-standalone
```

## Stop & Remove

```bash
# Stop
docker-compose down

# Stop and remove data
docker-compose down -v
```

## Environment Variables

Set in `docker-compose.yml` or pass with `-e`:

- `EMBEDDING_MODEL_NAME` - Sentence transformer model (default: sentence-transformers/all-MiniLM-L6-v2)
- `EMBEDDING_DIM` - Embedding dimension (default: 384)
- `OPENAI_API_KEY` - Optional OpenAI API key

## Troubleshooting

**Container won't start:**
```bash
docker logs memora-standalone
```

**Database issues:**
```bash
docker exec -it memora-standalone su - postgres -c "psql memora"
```

**Reset everything:**
```bash
docker-compose down -v
docker-compose up -d
```

## Production Notes

This standalone image is ideal for:
- ✅ Development
- ✅ Demos
- ✅ Testing
- ✅ Small deployments

For production, consider:
- Separate containers for each service
- External PostgreSQL database
- Kubernetes/Docker Swarm orchestration
- Environment-specific configurations
