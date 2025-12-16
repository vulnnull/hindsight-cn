# Services

Hindsight consists of two services that can run together or separately depending on your deployment needs.

## API Service

The core memory engine. Handles all memory operations:

- **Retain**: Ingests content, extracts facts, builds knowledge graph
- **Recall**: Semantic search across memories
- **Reflect**: Disposition-aware answer generation

```
hindsight-api        # Default port: 8888
```

The API service is stateless and can be horizontally scaled behind a load balancer. All state is stored in PostgreSQL.

## Control Plane

Web UI for managing and exploring your memory banks:

- Browse agents and memory banks
- Explore entities and relationships
- View ingestion history and operations
- Test recall queries interactively

```
hindsight-control-plane    # Default port: 9999
```

The Control Plane connects to the API service and provides a visual interface for development and debugging.

## Deployment Options

| Deployment | Services | Use Case |
|------------|----------|----------|
| **Docker (single container)** | Both bundled | Development, quick start |
| **Helm / Kubernetes** | Separate pods | Production, scaling |
| **Bare metal** | Run independently | Custom deployments |

In the Docker quickstart, both services run in a single container. For production Kubernetes deployments, they run as separate pods with independent scaling.
