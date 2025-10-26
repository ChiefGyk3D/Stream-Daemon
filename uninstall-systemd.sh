#!/bin/bash
# Stream Daemon - systemd Service Uninstallation Script
# This script removes the Stream Daemon systemd service

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}ERROR: This script must be run as root (use sudo)${NC}"
    exit 1
fi

SERVICE_FILE="/etc/systemd/system/stream-daemon.service"

echo -e "${YELLOW}Stream Daemon - systemd Service Uninstaller${NC}"
echo "============================================="
echo ""

# Check if service exists
if [ ! -f "$SERVICE_FILE" ]; then
    echo -e "${YELLOW}Service file not found. Stream Daemon may not be installed.${NC}"
    exit 0
fi

# Detect if this is a Docker or Python service
IS_DOCKER=false
if grep -q "Docker" "$SERVICE_FILE" || grep -q "docker run" "$SERVICE_FILE"; then
    IS_DOCKER=true
    echo "Detected Docker-based deployment"
else
    echo "Detected Python-based deployment"
fi

# Stop the service if running
if systemctl is-active --quiet stream-daemon.service; then
    echo "Stopping Stream Daemon service..."
    systemctl stop stream-daemon.service
    echo -e "${GREEN}✓${NC} Service stopped"
fi

# If Docker deployment, also clean up Docker container
if [ "$IS_DOCKER" = true ]; then
    if command -v docker &> /dev/null; then
        # Check if container exists
        if docker ps -a --format '{{.Names}}' | grep -q '^stream-daemon$'; then
            echo "Removing Docker container..."
            docker rm -f stream-daemon 2>/dev/null || true
            echo -e "${GREEN}✓${NC} Docker container removed"
        fi
        
        # Ask about removing Docker image
        if docker images --format "{{.Repository}}" | grep -q "^stream-daemon$"; then
            IMAGE_SIZE=$(docker images --format "{{.Size}}" stream-daemon | head -n 1)
            echo ""
            read -p "Also remove Docker image 'stream-daemon' (${IMAGE_SIZE})? (y/N) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                docker rmi stream-daemon 2>/dev/null || true
                echo -e "${GREEN}✓${NC} Docker image removed"
            else
                echo -e "${YELLOW}ℹ${NC} Docker image kept (remove manually with: docker rmi stream-daemon)"
            fi
        fi
    fi
fi

# Disable the service
if systemctl is-enabled --quiet stream-daemon.service 2>/dev/null; then
    echo "Disabling Stream Daemon service..."
    systemctl disable stream-daemon.service
    echo -e "${GREEN}✓${NC} Service disabled"
fi

# Remove service file
echo "Removing service file..."
rm -f "$SERVICE_FILE"
echo -e "${GREEN}✓${NC} Service file removed"

# Reload systemd
echo "Reloading systemd..."
systemctl daemon-reload
systemctl reset-failed
echo -e "${GREEN}✓${NC} systemd reloaded"

echo ""
echo -e "${GREEN}Uninstallation complete!${NC}"
echo ""
echo -e "${YELLOW}Note: This script does NOT automatically remove:${NC}"
echo "  - The project directory and files"
if [ "$IS_DOCKER" = true ]; then
    if docker images --format "{{.Repository}}" | grep -q "^stream-daemon$"; then
        echo "  - Docker image 'stream-daemon' (kept - remove with: docker rmi stream-daemon)"
    fi
    echo "  - Other Docker resources (volumes, networks)"
else
    echo "  - Python virtual environment (venv/)"
fi
echo "  - Your .env configuration"
echo "  - Message template files (messages.txt, end_messages.txt)"
echo ""
echo "To completely remove Stream Daemon:"
if [ "$IS_DOCKER" = true ]; then
    echo "  1. Remove Docker image: docker rmi stream-daemon"
    echo "  2. Clean Docker cache: docker system prune"
    echo "  3. Delete project directory: rm -rf $PROJECT_DIR"
else
    echo "  1. Delete project directory including venv: rm -rf $PROJECT_DIR"
fi
echo ""
