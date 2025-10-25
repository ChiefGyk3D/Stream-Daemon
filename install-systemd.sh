#!/bin/bash
# Stream Daemon - systemd Service Installation Script
# This script installs Stream Daemon as a systemd service

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

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$SCRIPT_DIR"

# Get the user who invoked sudo (or current user if not using sudo)
ACTUAL_USER="${SUDO_USER:-$USER}"
ACTUAL_HOME=$(eval echo ~$ACTUAL_USER)

echo -e "${GREEN}Stream Daemon - systemd Service Installer${NC}"
echo "=========================================="
echo ""
echo "Project Directory: $PROJECT_DIR"
echo "Running as user: $ACTUAL_USER"
echo ""

# Check if stream-daemon.py exists
if [ ! -f "$PROJECT_DIR/stream-daemon.py" ]; then
    echo -e "${RED}ERROR: stream-daemon.py not found in $PROJECT_DIR${NC}"
    exit 1
fi

# Ask user which deployment mode they want
echo "Choose deployment mode:"
echo "  1) Python (uses Python virtual environment)"
echo "  2) Docker (uses Docker containers)"
echo ""
read -p "Select option [1-2]: " -n 1 -r DEPLOYMENT_MODE
echo ""
echo ""

if [[ ! $DEPLOYMENT_MODE =~ ^[1-2]$ ]]; then
    echo -e "${RED}ERROR: Invalid option selected${NC}"
    exit 1
fi

# Check if .env exists
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo -e "${YELLOW}WARNING: .env file not found!${NC}"
    echo "You'll need to create .env before starting the service."
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

if [ "$DEPLOYMENT_MODE" = "1" ]; then
    # Python deployment mode
    echo -e "${GREEN}Setting up Python deployment...${NC}"
    echo ""
    
    # Detect Python command
    PYTHON_CMD=""
    if command -v python3.13 &> /dev/null; then
        PYTHON_CMD="python3.13"
    elif command -v python3.11 &> /dev/null; then
        PYTHON_CMD="python3.11"
    elif command -v python3.10 &> /dev/null; then
        PYTHON_CMD="python3.10"
    elif command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    else
        echo -e "${RED}ERROR: Python 3 not found!${NC}"
        exit 1
    fi

    PYTHON_VERSION=$($PYTHON_CMD --version)
    echo -e "${GREEN}✓${NC} Found Python: $PYTHON_VERSION ($PYTHON_CMD)"

    # Check if virtual environment exists, create if not
    if [ ! -d "$PROJECT_DIR/venv" ]; then
        echo ""
        echo "Creating Python virtual environment..."
        sudo -u $ACTUAL_USER $PYTHON_CMD -m venv "$PROJECT_DIR/venv"
        echo -e "${GREEN}✓${NC} Virtual environment created"
    fi

    # Install/upgrade dependencies
    echo ""
    echo "Installing Python dependencies..."
    sudo -u $ACTUAL_USER "$PROJECT_DIR/venv/bin/pip" install --upgrade pip > /dev/null 2>&1
    sudo -u $ACTUAL_USER "$PROJECT_DIR/venv/bin/pip" install -r "$PROJECT_DIR/requirements.txt" > /dev/null 2>&1
    echo -e "${GREEN}✓${NC} Dependencies installed"

    # Create systemd service file
    SERVICE_FILE="/etc/systemd/system/stream-daemon.service"
    echo ""
    echo "Creating systemd service file..."

    cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Stream Daemon - Multi-platform Live Stream Monitor
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$ACTUAL_USER
Group=$ACTUAL_USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=$PROJECT_DIR/venv/bin/python $PROJECT_DIR/stream-daemon.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=stream-daemon

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=$PROJECT_DIR

[Install]
WantedBy=multi-user.target
EOF

elif [ "$DEPLOYMENT_MODE" = "2" ]; then
    # Docker deployment mode
    echo -e "${GREEN}Setting up Docker deployment...${NC}"
    echo ""
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}ERROR: Docker is not installed!${NC}"
        echo "Please install Docker first: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    echo -e "${GREEN}✓${NC} Docker is installed: $(docker --version)"
    
    # Check if docker-compose is installed
    COMPOSE_CMD=""
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
        echo -e "${GREEN}✓${NC} Found docker-compose: $(docker-compose --version)"
    elif docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
        echo -e "${GREEN}✓${NC} Found docker compose plugin: $(docker compose version)"
    else
        echo -e "${RED}ERROR: docker-compose is not installed!${NC}"
        echo "Please install docker-compose: https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    # Check if user is in docker group
    if ! groups $ACTUAL_USER | grep -q docker; then
        echo -e "${YELLOW}WARNING: User $ACTUAL_USER is not in the docker group${NC}"
        echo "You may need to add the user to the docker group:"
        echo "  sudo usermod -aG docker $ACTUAL_USER"
        echo "  (then log out and back in)"
        echo ""
        read -p "Continue anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    # Check if Docker image exists or needs to be built
    IMAGE_NAME="stream-daemon"
    if docker images | grep -q "$IMAGE_NAME"; then
        echo -e "${GREEN}✓${NC} Docker image '$IMAGE_NAME' found"
    else
        echo -e "${YELLOW}Docker image '$IMAGE_NAME' not found${NC}"
        echo "Building Docker image..."
        echo ""
        
        # Check if Dockerfile exists
        if [ ! -f "$PROJECT_DIR/Docker/Dockerfile" ]; then
            echo -e "${RED}ERROR: Docker/Dockerfile not found!${NC}"
            exit 1
        fi
        
        # Build the image
        cd "$PROJECT_DIR"
        if sudo -u $ACTUAL_USER docker build -t $IMAGE_NAME -f Docker/Dockerfile .; then
            echo -e "${GREEN}✓${NC} Docker image built successfully"
        else
            echo -e "${RED}ERROR: Failed to build Docker image${NC}"
            exit 1
        fi
    fi
    
    # Create systemd service file for Docker
    SERVICE_FILE="/etc/systemd/system/stream-daemon.service"
    echo ""
    echo "Creating systemd service file for Docker..."

    cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Stream Daemon - Multi-platform Live Stream Monitor (Docker)
After=docker.service network-online.target
Requires=docker.service
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
User=$ACTUAL_USER
Group=$ACTUAL_USER
WorkingDirectory=$PROJECT_DIR

# Start the Docker container
ExecStart=/usr/bin/docker run -d \\
    --name stream-daemon \\
    --restart unless-stopped \\
    --env-file $PROJECT_DIR/.env \\
    -v $PROJECT_DIR/messages.txt:/app/messages.txt:ro \\
    -v $PROJECT_DIR/end_messages.txt:/app/end_messages.txt:ro \\
    $IMAGE_NAME

# Stop and remove the container
ExecStop=/usr/bin/docker stop stream-daemon
ExecStopPost=/usr/bin/docker rm -f stream-daemon

StandardOutput=journal
StandardError=journal
SyslogIdentifier=stream-daemon

[Install]
WantedBy=multi-user.target
EOF
fi

echo -e "${GREEN}✓${NC} Service file created: $SERVICE_FILE"


# Reload systemd
echo ""
echo "Reloading systemd..."
systemctl daemon-reload
echo -e "${GREEN}✓${NC} systemd reloaded"

# Enable service
echo ""
read -p "Enable Stream Daemon to start on boot? (Y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    systemctl enable stream-daemon.service
    echo -e "${GREEN}✓${NC} Service enabled (will start on boot)"
fi

# Start service
echo ""
read -p "Start Stream Daemon now? (Y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    systemctl start stream-daemon.service
    sleep 2
    if systemctl is-active --quiet stream-daemon.service; then
        echo -e "${GREEN}✓${NC} Service started successfully!"
    else
        echo -e "${RED}✗${NC} Service failed to start. Check status with: sudo systemctl status stream-daemon"
    fi
fi

echo ""
echo -e "${GREEN}Installation complete!${NC}"
echo ""
echo "Service management commands:"
echo "  Start:   sudo systemctl start stream-daemon"
echo "  Stop:    sudo systemctl stop stream-daemon"
echo "  Restart: sudo systemctl restart stream-daemon"
echo "  Status:  sudo systemctl status stream-daemon"
echo "  Logs:    sudo journalctl -u stream-daemon -f"
echo "  Enable:  sudo systemctl enable stream-daemon"
echo "  Disable: sudo systemctl disable stream-daemon"
echo ""
