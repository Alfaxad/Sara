#!/bin/bash
set -e

# Check if docker-buildx-plugin is installed.
if ! dpkg -s docker-buildx-plugin >/dev/null 2>&1; then
    echo "docker-buildx-plugin is not installed. Installing..."
    sudo apt-get update && sudo apt-get install -y docker-buildx-plugin
fi

IMAGE_NAME="agentic-medgemma-fhir:latest"
CONTAINER_NAME="agentic-medgemma-fhir"

# Function to stop the container
stop() {
    echo "Stopping container: $CONTAINER_NAME..."
    # Check if the container is running before trying to stop it
    if [ "$(docker ps -q -f name=^${CONTAINER_NAME}$)" ]; then
        docker stop "$CONTAINER_NAME"
        echo "✅ Container stopped."
    else
        echo "Container '$CONTAINER_NAME' is not running."
    fi
}

echo "Building Docker image: $IMAGE_NAME"
DOCKER_BUILDKIT=1 docker build -t "$IMAGE_NAME" .

stop
docker rm "${CONTAINER_NAME}" 2>/dev/null || true

echo "Killing any process on port 8080..."
fuser -k 8080/tcp || true

ENV_FILE=~/agentic_medgemma_fhir.env

if [ ! -f "$ENV_FILE" ]; then
    echo "Error: Environment file not found at $ENV_FILE"
    exit 1
fi

echo "Running Docker image: $IMAGE_NAME"
echo "Access the viewer at http://localhost:8080"
docker run --rm --name "${CONTAINER_NAME}" -p 8080:8080 \
  --env-file ~/agentic_medgemma_fhir.env \
  "$IMAGE_NAME"