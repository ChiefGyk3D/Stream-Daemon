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

# Stop the service if running
if systemctl is-active --quiet stream-daemon.service; then
    echo "Stopping Stream Daemon service..."
    systemctl stop stream-daemon.service
    echo -e "${GREEN}✓${NC} Service stopped"
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
echo -e "${YELLOW}Note: This script does NOT remove:${NC}"
echo "  - The project directory and files"
echo "  - Python virtual environment (venv/)"
echo "  - Your .env configuration"
echo ""
echo "To completely remove Stream Daemon, manually delete the project directory."
echo ""
