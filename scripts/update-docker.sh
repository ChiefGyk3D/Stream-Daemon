#!/bin/bash
# Stream Daemon - Docker Update Script
# Safely updates the Docker container with the latest code

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}Stream Daemon - Docker Update Script${NC}"
echo "==========================================="
echo ""

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Project directory is parent of scripts directory
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "Project Directory: $PROJECT_DIR"
echo ""

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo -e "${RED}ERROR: Not in a git repository!${NC}"
    echo "This script must be run from the Stream-Daemon project directory."
    exit 1
fi

# Check if docker is available
if ! command -v docker &> /dev/null; then
    echo -e "${RED}ERROR: Docker not found!${NC}"
    exit 1
fi

# Get current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo -e "${BLUE}Current branch:${NC} $CURRENT_BRANCH"

# Get current commit
CURRENT_COMMIT=$(git rev-parse --short HEAD)
echo -e "${BLUE}Current commit:${NC} $CURRENT_COMMIT"
echo ""

# Ask if they want to pull latest changes
read -p "Pull latest changes from origin? (Y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    echo "Pulling latest changes..."
    git pull origin "$CURRENT_BRANCH"
    
    NEW_COMMIT=$(git rev-parse --short HEAD)
    if [ "$CURRENT_COMMIT" = "$NEW_COMMIT" ]; then
        echo -e "${GREEN}✓${NC} Already up to date"
    else
        echo -e "${GREEN}✓${NC} Updated from $CURRENT_COMMIT to $NEW_COMMIT"
    fi
    echo ""
fi

# Ask about cache
echo ""
read -p "Force rebuild without cache? (Y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    BUILD_ARGS="--no-cache --pull"
    echo -e "${YELLOW}Building from scratch (no cache)...${NC}"
else
    BUILD_ARGS=""
    echo -e "${YELLOW}Building with cache...${NC}"
fi
echo ""

IMAGE_NAME="stream-daemon"
BUILD_TAG="${IMAGE_NAME}:latest"

if docker build $BUILD_ARGS -t "$BUILD_TAG" -f Docker/Dockerfile . ; then
    echo ""
    echo -e "${GREEN}✓${NC} Docker image built successfully!"
    
    # Show image info
    IMAGE_SIZE=$(docker images --format "{{.Size}}" "$IMAGE_NAME" | head -n 1)
    IMAGE_ID=$(docker images --format "{{.ID}}" "$IMAGE_NAME" | head -n 1)
    echo -e "${GREEN}✓${NC} Image: ${BUILD_TAG} (${IMAGE_SIZE}, ID: ${IMAGE_ID:0:12})"
else
    echo ""
    echo -e "${RED}✗${NC} Failed to build Docker image"
    exit 1
fi

echo ""
echo -e "${YELLOW}Restarting container...${NC}"
echo ""

# Check if container is running
CONTAINER_NAME="stream-daemon"
if docker ps -a --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
    echo "Found existing container: $CONTAINER_NAME"
    
    # Stop and remove old container
    echo "Stopping old container..."
    docker stop "$CONTAINER_NAME" 2>/dev/null || true
    echo "Removing old container..."
    docker rm "$CONTAINER_NAME" 2>/dev/null || true
    echo -e "${GREEN}✓${NC} Old container removed"
    echo ""
fi

# Try to start container
STARTED=false

# Check if docker-compose.yml exists in project root or Docker directory
if [ -f "docker-compose.yml" ]; then
    COMPOSE_FILE="docker-compose.yml"
    COMPOSE_DIR="$PROJECT_DIR"
elif [ -f "Docker/docker-compose.yml" ]; then
    COMPOSE_FILE="Docker/docker-compose.yml"
    COMPOSE_DIR="$PROJECT_DIR/Docker"
else
    COMPOSE_FILE=""
fi

if [ -n "$COMPOSE_FILE" ]; then
    echo "Using docker-compose to start container..."
    echo "Compose file: $COMPOSE_FILE"
    
    # Detect docker compose command
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    elif docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    else
        echo -e "${YELLOW}WARNING: docker-compose not found, using docker run${NC}"
        COMPOSE_CMD=""
    fi
    
    if [ -n "$COMPOSE_CMD" ]; then
        cd "$COMPOSE_DIR"
        if $COMPOSE_CMD up -d stream-daemon 2>/dev/null; then
            echo -e "${GREEN}✓${NC} Container started with docker-compose!"
            STARTED=true
        else
            echo -e "${YELLOW}WARNING: docker-compose failed, falling back to docker run${NC}"
        fi
        cd "$PROJECT_DIR"
    fi
fi

# Fallback to docker run if compose didn't work
if [ "$STARTED" = false ]; then
    echo "Starting container with docker run..."
    
    # Check if .env file exists
    if [ -f ".env" ]; then
        ENV_ARG="--env-file .env"
    else
        echo -e "${YELLOW}WARNING: .env file not found${NC}"
        ENV_ARG=""
    fi
    
    # Start container with docker run
    if docker run -d \
        --name "$CONTAINER_NAME" \
        --restart unless-stopped \
        $ENV_ARG \
        "$BUILD_TAG"; then
        echo -e "${GREEN}✓${NC} Container started with docker run!"
        STARTED=true
    else
        echo -e "${RED}✗${NC} Failed to start container"
        exit 1
    fi
fi

echo ""
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}Update Complete!${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo ""
echo "Container is now running with the latest code."
echo ""
echo "Useful commands:"
echo "  • View logs:    docker logs -f $CONTAINER_NAME"
echo "  • Check status: docker ps | grep $CONTAINER_NAME"
echo "  • Restart:      docker restart $CONTAINER_NAME"
echo "  • Stop:         docker stop $CONTAINER_NAME"
echo ""
