#!/bin/bash
set -e

# Default values
IMAGE_NAME="memora-standalone:latest"
CONTAINER_NAME="memora-standalone"
PERSIST_DATA=false
PORT_CONTROL=3000
PORT_API=8080
PORT_DB=5432

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --image)
            IMAGE_NAME="$2"
            shift 2
            ;;
        --name)
            CONTAINER_NAME="$2"
            shift 2
            ;;
        --persist)
            PERSIST_DATA=true
            shift
            ;;
        --port-control)
            PORT_CONTROL="$2"
            shift 2
            ;;
        --port-api)
            PORT_API="$2"
            shift 2
            ;;
        --port-db)
            PORT_DB="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --image NAME           Docker image name (default: memora-standalone:latest)"
            echo "  --name NAME            Container name (default: memora-standalone)"
            echo "  --persist              Use persistent volume for data"
            echo "  --port-control PORT    Control plane port (default: 3000)"
            echo "  --port-api PORT        Dataplane API port (default: 8080)"
            echo "  --port-db PORT         PostgreSQL port (default: 5432)"
            echo "  --help                 Show this help message"
            echo ""
            echo "Example:"
            echo "  $0 --persist --port-control 3001"
            echo ""
            echo "To stop the container:"
            echo "  docker stop ${CONTAINER_NAME}"
            echo ""
            echo "To remove the container:"
            echo "  docker rm ${CONTAINER_NAME}"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Check if container already exists
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "⚠️  Container '${CONTAINER_NAME}' already exists"
    echo ""
    read -p "Do you want to remove it and create a new one? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🗑️  Removing existing container..."
        docker rm -f "${CONTAINER_NAME}" 2>/dev/null || true
    else
        echo "Exiting..."
        exit 0
    fi
fi

echo "🚀 Starting Memora Standalone Container"
echo "========================================"
echo "Image: ${IMAGE_NAME}"
echo "Container: ${CONTAINER_NAME}"
echo ""

# Build docker run command
DOCKER_CMD="docker run -d --name ${CONTAINER_NAME}"
DOCKER_CMD="${DOCKER_CMD} -p ${PORT_CONTROL}:3000"
DOCKER_CMD="${DOCKER_CMD} -p ${PORT_API}:8080"
DOCKER_CMD="${DOCKER_CMD} -p ${PORT_DB}:5432"

if [ "$PERSIST_DATA" = true ]; then
    DOCKER_CMD="${DOCKER_CMD} -v memora-data:/var/lib/postgresql/data"
    echo "📦 Using persistent volume: memora-data"
fi

DOCKER_CMD="${DOCKER_CMD} ${IMAGE_NAME}"

# Run the container
eval $DOCKER_CMD

echo ""
echo "✅ Container started successfully!"
echo ""
echo "Services are available at:"
echo "  - Control Plane: http://localhost:${PORT_CONTROL}"
echo "  - Dataplane API: http://localhost:${PORT_API}"
echo "  - PostgreSQL: localhost:${PORT_DB}"
echo ""
echo "View logs:"
echo "  docker logs -f ${CONTAINER_NAME}"
echo ""
echo "Stop container:"
echo "  docker stop ${CONTAINER_NAME}"
echo ""
echo "Remove container:"
echo "  docker rm -f ${CONTAINER_NAME}"
echo ""
