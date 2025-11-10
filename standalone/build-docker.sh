#!/bin/bash
set -e

cd "$(dirname "$0")/.."

# Default values
IMAGE_NAME="memora-standalone"
IMAGE_TAG="latest"
REGISTRY=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --name)
            IMAGE_NAME="$2"
            shift 2
            ;;
        --tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
        --registry)
            REGISTRY="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --name NAME        Docker image name (default: memora-standalone)"
            echo "  --tag TAG          Docker image tag (default: latest)"
            echo "  --registry REG     Docker registry URL (optional)"
            echo "  --help             Show this help message"
            echo ""
            echo "Example:"
            echo "  $0 --name myapp --tag v1.0.0"
            echo "  $0 --registry docker.io/myuser --name memora-standalone --tag v1.0.0"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Construct full image name
if [ -n "$REGISTRY" ]; then
    FULL_IMAGE_NAME="${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
else
    FULL_IMAGE_NAME="${IMAGE_NAME}:${IMAGE_TAG}"
fi

echo "Building Memora Standalone Docker image: ${FULL_IMAGE_NAME}"
echo "============================================================="
echo "This image includes:"
echo "  - PostgreSQL database"
echo "  - Dataplane API (FastAPI)"
echo "  - Control Plane (Next.js)"
echo ""

# Build the Docker image
docker build -f standalone/Dockerfile -t "${FULL_IMAGE_NAME}" .

echo ""
echo "Build completed successfully!"
echo "Image: ${FULL_IMAGE_NAME}"
echo ""
echo "To run the container:"
echo "  docker run -p 3000:3000 -p 8080:8080 ${FULL_IMAGE_NAME}"
echo ""
echo "Services will be available at:"
echo "  - Control Plane: http://localhost:3000"
echo "  - Dataplane API: http://localhost:8080"
echo "  - PostgreSQL: localhost:5432"
echo ""
echo "For persistent data, mount a volume:"
echo "  docker run -p 3000:3000 -p 8080:8080 \\"
echo "    -v memora-data:/var/lib/postgresql/data \\"
echo "    ${FULL_IMAGE_NAME}"
echo ""
if [ -n "$REGISTRY" ]; then
    echo "To push to registry:"
    echo "  docker push ${FULL_IMAGE_NAME}"
    echo ""
fi
