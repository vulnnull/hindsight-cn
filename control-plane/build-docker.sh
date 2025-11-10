#!/bin/bash
set -e

# Default values
IMAGE_NAME="memora-control-plane"
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
            echo "  --name NAME        Docker image name (default: control-plane)"
            echo "  --tag TAG          Docker image tag (default: latest)"
            echo "  --registry REG     Docker registry URL (optional)"
            echo "  --help             Show this help message"
            echo ""
            echo "Example:"
            echo "  $0 --name myapp --tag v1.0.0"
            echo "  $0 --registry docker.io/myuser --name control-plane --tag v1.0.0"
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

echo "Building Docker image: ${FULL_IMAGE_NAME}"
echo "========================================"

# Build the Docker image
docker build -t "${FULL_IMAGE_NAME}"  .

echo ""
echo "Build completed successfully!"
echo "Image: ${FULL_IMAGE_NAME}"
echo ""
echo "To run the container:"
echo "  docker run -p 3000:3000 \\"
echo "    -e DATAPLANE_API_URL=http://your-api-url:8080 \\"
echo "    ${FULL_IMAGE_NAME}"
echo ""
echo "Or with an env file:"
echo "  docker run -p 3000:3000 --env-file .env.local ${FULL_IMAGE_NAME}"
echo ""
echo "To push to registry (if registry specified):"
if [ -n "$REGISTRY" ]; then
    echo "  docker push ${FULL_IMAGE_NAME}"
fi
