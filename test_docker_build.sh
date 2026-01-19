#!/bin/bash
# Docker build and test script for Stream Daemon

set -e  # Exit on error

echo "======================================================================"
echo "🐳 Stream Daemon - Docker Build & Test"
echo "======================================================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Check Docker is installed
echo ""
echo "[1/6] Checking Docker installation..."
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    echo -e "${GREEN}✅ ${DOCKER_VERSION}${NC}"
else
    echo -e "${RED}❌ Docker not installed${NC}"
    echo "Install from: https://docs.docker.com/get-docker/"
    exit 1
fi

# Test 2: Check Docker is running
echo ""
echo "[2/6] Checking Docker daemon..."
if docker info &> /dev/null; then
    echo -e "${GREEN}✅ Docker daemon is running${NC}"
else
    echo -e "${RED}❌ Docker daemon not running${NC}"
    echo "Start Docker and try again"
    exit 1
fi

# Test 3: Build Docker image
echo ""
echo "[3/6] Building Docker image..."
echo "This may take a few minutes..."
if docker build -t stream-daemon:test -f Docker/Dockerfile .; then
    echo -e "${GREEN}✅ Docker image built successfully${NC}"
else
    echo -e "${RED}❌ Docker build failed${NC}"
    exit 1
fi

# Test 4: Check image size
echo ""
echo "[4/6] Checking image size..."
IMAGE_SIZE=$(docker images stream-daemon:test --format "{{.Size}}")
echo -e "${GREEN}✅ Image size: ${IMAGE_SIZE}${NC}"

# Test 5: Test Python in container
echo ""
echo "[5/6] Testing Python environment in container..."
if docker run --rm stream-daemon:test python3 --version; then
    echo -e "${GREEN}✅ Python working in container${NC}"
else
    echo -e "${RED}❌ Python test failed${NC}"
    exit 1
fi

# Test 6: Test dependencies in container
echo ""
echo "[6/6] Testing dependencies in container..."
cat > /tmp/test_deps.py << 'EOF'
import sys
print("Testing imports...")
try:
    import twitchAPI
    import mastodon
    import atproto
    import discord
    import nio
    import google.genai
    import ollama
    import boto3
    import hvac
    import dopplersdk
    print("✅ All core dependencies importable")
    sys.exit(0)
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)
EOF

if docker run --rm -v /tmp/test_deps.py:/test_deps.py stream-daemon:test python3 /test_deps.py; then
    echo -e "${GREEN}✅ All dependencies working in container${NC}"
else
    echo -e "${RED}❌ Dependency test failed${NC}"
    exit 1
fi

# Test 7: Test with docker-compose (if available)
echo ""
echo "[OPTIONAL] Testing docker-compose..."
if [ -f "Docker/docker-compose.yml" ]; then
    if command -v docker-compose &> /dev/null; then
        echo "Found docker-compose.yml, validating..."
        if docker-compose -f Docker/docker-compose.yml config > /dev/null 2>&1; then
            echo -e "${GREEN}✅ docker-compose.yml is valid${NC}"
        else
            echo -e "${YELLOW}⚠️  docker-compose.yml has issues${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  docker-compose not installed (optional)${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  docker-compose.yml not found${NC}"
fi

# Summary
echo ""
echo "======================================================================"
echo -e "${GREEN}✅ SUCCESS - Docker build and tests passed!${NC}"
echo "======================================================================"
echo ""
echo "Your Docker image is ready to use: stream-daemon:test"
echo ""
echo "Next steps:"
echo "  1. Create .env file with your configuration"
echo "  2. Run with: docker run --env-file .env stream-daemon:test"
echo "  3. Or use docker-compose: docker-compose -f Docker/docker-compose.yml up"
echo ""
echo "To test Ollama integration with Docker:"
echo "  docker run --rm --env-file .env \\"
echo "    -e LLM_ENABLE=True \\"
echo "    -e LLM_PROVIDER=ollama \\"
echo "    -e LLM_OLLAMA_HOST=http://YOUR_OLLAMA_IP:11434 \\"
echo "    stream-daemon:test python3 test_ollama.py"
echo ""

# Cleanup prompt
echo "Clean up test image? (y/n)"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    docker rmi stream-daemon:test
    echo "Test image removed"
fi
