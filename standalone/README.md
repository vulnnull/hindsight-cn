# Memora Standalone Docker Image

This directory contains the configuration to build a standalone Docker image that includes all Memora components in a single container:

- **PostgreSQL**: Database backend
- **Dataplane**: FastAPI backend service
- **Control Plane**: Next.js web interface

## Quick Start with Docker Compose

The easiest way to run the standalone image:

```bash
cd standalone
docker-compose up -d
```

This will build and start all services with persistent data storage.

To stop:
```bash
docker-compose down
```

To remove data and start fresh:
```bash
docker-compose down -v
```

## Building Manually

```bash
./standalone/build-docker.sh
```

With custom options:
```bash
./standalone/build-docker.sh --name my-memora --tag v1.0.0
./standalone/build-docker.sh --registry docker.io/myuser --tag latest
```

## Running Manually

Using the run script (recommended):
```bash
./standalone/run-docker.sh --persist
```

With custom ports:
```bash
./standalone/run-docker.sh --persist --port-control 3001 --port-api 8081
```

Direct docker run:
```bash
docker run -p 3000:3000 -p 8080:8080 memora-standalone:latest
```

With persistent data:
```bash
docker run -p 3000:3000 -p 8080:8080 \
  -v memora-data:/var/lib/postgresql/data \
  memora-standalone:latest
```

With custom environment variables:
```bash
docker run -p 3000:3000 -p 8080:8080 \
  -e OPENAI_API_KEY=your-key \
  -e EMBEDDING_MODEL_NAME=custom-model \
  memora-standalone:latest
```

## Accessing Services

Once running, services are available at:

- **Control Plane**: http://localhost:3000
- **Dataplane API**: http://localhost:8080
- **PostgreSQL**: localhost:5432 (username: postgres, password: postgres, database: memora)

## Architecture

The container uses `supervisord` to manage three processes:
1. PostgreSQL (started first)
2. Dataplane API (started after PostgreSQL)
3. Control Plane (started after dataplane)

The `init.sh` script handles:
- PostgreSQL initialization
- Database creation
- Running migrations
- Starting all services via supervisord

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/memora` | PostgreSQL connection string |
| `DATAPLANE_API_URL` | `http://localhost:8080` | Dataplane API URL for control plane |
| `EMBEDDING_MODEL_NAME` | `sentence-transformers/all-MiniLM-L6-v2` | Sentence transformer model |
| `EMBEDDING_DIM` | `384` | Embedding dimension |
| `OPENAI_API_KEY` | - | Optional OpenAI API key |

## Logs

View logs from all services:
```bash
docker logs -f <container-id>
```

## Production Considerations

This standalone image is designed for:
- Development environments
- Demos and testing
- Small deployments

For production use, consider:
- Using separate containers for each service
- External PostgreSQL database
- Load balancing for the control plane
- Persistent volume for PostgreSQL data
- Environment-specific configurations
