# Installation Guide

> **📦 Complete installation instructions for all deployment methods**

This guide covers all ways to install and run Stream Daemon, from simple Python execution to production Docker deployments.

---

## 📋 Table of Contents

- [System Requirements](#-system-requirements)
- [Python Installation](#-python-installation-recommended)
- [Docker Installation](#-docker-installation)
- [Systemd Service (Linux)](#-systemd-service-linux)
- [Cloud Deployment](#-cloud-deployment)
- [Development Setup](#-development-setup)
- [Troubleshooting](#-troubleshooting)

---

## 💻 System Requirements

### Minimum Requirements

- **OS:** Linux, macOS, Windows, or any Docker-compatible platform
- **Python:** 3.10 or higher (3.11+ recommended)
- **RAM:** 128MB minimum, 256MB recommended
- **Disk:** 100MB for code + dependencies
- **Network:** Internet connection for API calls

### Supported Platforms

✅ **Linux** (Ubuntu, Debian, Fedora, CentOS, Arch, etc.)  
✅ **macOS** (10.14 Mojave or later)  
✅ **Windows** (10/11, via Python or WSL2)  
✅ **Docker** (any platform with Docker support)  
✅ **Raspberry Pi** (3B+ or newer with 1GB+ RAM)  
✅ **Cloud** (AWS EC2, Google Cloud, Azure, DigitalOcean, etc.)

---

## 🐍 Python Installation (Recommended)

### Step 1: Install Python

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv git -y
```

**Linux (Fedora/CentOS):**
```bash
sudo dnf install python3 python3-pip git -y
```

**macOS:**
```bash
# Install Homebrew if needed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python3 git
```

**Windows:**
1. Download Python from [python.org/downloads](https://www.python.org/downloads/)
2. Run installer, **check "Add Python to PATH"**
3. Install Git from [git-scm.com](https://git-scm.com/)

**Verify installation:**
```bash
python3 --version  # Should be 3.10 or higher
pip3 --version
```

### Step 2: Clone Repository

```bash
# Clone from GitHub
git clone https://github.com/ChiefGyk3D/Stream-Daemon.git
cd Stream-Daemon

# Or download ZIP
curl -LO https://github.com/ChiefGyk3D/Stream-Daemon/archive/refs/heads/main.zip
unzip main.zip
cd Stream-Daemon-main
```

### Step 3: Install Dependencies

**Option A: System Python (Simple)**
```bash
pip3 install -r requirements.txt
```

**Option B: Virtual Environment (Recommended)**
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**Why virtual environment?**
- ✅ Isolates dependencies from system Python
- ✅ Avoids version conflicts
- ✅ Easy to delete and recreate

### Step 4: Configure

```bash
# Create configuration file
cp .env.example .env

# Edit with your credentials
nano .env  # or vim, emacs, code, etc.
```

See [Quick Start Guide](quickstart.md#step-2-configure-credentials-5-minutes) for configuration examples.

### Step 5: Test

```bash
# Test your configuration
python3 tests/test_doppler_all.py

# Or test specific platforms
python3 tests/test_doppler_twitch.py
python3 tests/test_mastodon.py
```

### Step 6: Run

```bash
# Run directly
python3 stream-daemon.py

# Or with virtual environment active
source venv/bin/activate
python stream-daemon.py
```

**Keep it running:**
```bash
# Background process (Linux/macOS)
nohup python3 stream-daemon.py > stream-daemon.log 2>&1 &

# Or use systemd (see below)
```

---

## 🐳 Docker Installation

### Prerequisites

**Install Docker:**

**Linux:**
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
# Log out and back in for group to take effect

# Fedora
sudo dnf install docker docker-compose -y
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
```

**macOS:**
- Download [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop)
- Install and start Docker Desktop

**Windows:**
- Download [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)
- Requires WSL2

**Verify:**
```bash
docker --version
docker-compose --version
```

### Method 1: Docker Compose (Recommended)

**Step 1: Clone repository**
```bash
git clone https://github.com/ChiefGyk3D/Stream-Daemon.git
cd Stream-Daemon/Docker
```

**Step 2: Configure**

Edit `docker-compose.yml`:
```yaml
version: '3.8'
services:
  stream-daemon:
    build: ..
    container_name: stream-daemon
    restart: unless-stopped
    
    environment:
      # Streaming Platforms
      TWITCH_ENABLE: 'True'
      TWITCH_USERNAME: your_username
      TWITCH_CLIENT_ID: your_client_id
      TWITCH_CLIENT_SECRET: your_client_secret
      
      YOUTUBE_ENABLE: 'True'
      YOUTUBE_USERNAME: '@YourHandle'
      YOUTUBE_API_KEY: your_api_key
      
      # Social Platforms
      MASTODON_ENABLE: 'True'
      MASTODON_INSTANCE_URL: https://mastodon.social
      MASTODON_ACCESS_TOKEN: your_token
      
      DISCORD_ENABLE: 'True'
      DISCORD_WEBHOOK_URL: your_webhook_url
      
      # Intervals
      SETTINGS_CHECK_INTERVAL: 5
      SETTINGS_POST_INTERVAL: 5
    
    volumes:
      - ./messages.txt:/app/messages.txt
      - ./end_messages.txt:/app/end_messages.txt
    
    healthcheck:
      test: ["CMD", "python3", "-c", "import sys; sys.exit(0)"]
      interval: 30s
      timeout: 10s
      retries: 3
```

**Or use `.env` file (more secure):**

Create `.env` in Docker directory:
```bash
TWITCH_CLIENT_ID=your_client_id
TWITCH_CLIENT_SECRET=your_client_secret
YOUTUBE_API_KEY=your_api_key
MASTODON_ACCESS_TOKEN=your_token
DISCORD_WEBHOOK_URL=your_webhook_url
```

Update `docker-compose.yml`:
```yaml
services:
  stream-daemon:
    build: ..
    env_file:
      - .env
    environment:
      TWITCH_ENABLE: 'True'
      TWITCH_USERNAME: your_username
      # Sensitive values from .env file
```

**Step 3: Build and run**
```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f stream-daemon

# Stop
docker-compose down

# Restart
docker-compose restart stream-daemon
```

### Method 2: Manual Docker Build

```bash
# Build image
docker build -t stream-daemon:latest .

# Run with environment file
docker run -d \
  --name stream-daemon \
  --restart unless-stopped \
  --env-file .env \
  -v $(pwd)/messages.txt:/app/messages.txt \
  -v $(pwd)/end_messages.txt:/app/end_messages.txt \
  stream-daemon:latest

# View logs
docker logs -f stream-daemon

# Stop
docker stop stream-daemon

# Remove
docker rm stream-daemon
```

### Method 3: Pre-built Image (Future)

```bash
# Pull from Docker Hub (when available)
docker pull chiefgyk3d/stream-daemon:latest

# Run
docker run -d \
  --name stream-daemon \
  --restart unless-stopped \
  --env-file .env \
  chiefgyk3d/stream-daemon:latest
```

### Docker with Doppler

**Recommended for production:**

```yaml
version: '3.8'
services:
  stream-daemon:
    build: ..
    environment:
      # Secrets Manager
      SECRETS_MANAGER: doppler
      DOPPLER_TOKEN: ${DOPPLER_TOKEN}  # From .env file
      
      # Secret prefixes
      SECRETS_DOPPLER_TWITCH_SECRET_NAME: TWITCH
      SECRETS_DOPPLER_YOUTUBE_SECRET_NAME: YOUTUBE
      SECRETS_DOPPLER_MASTODON_SECRET_NAME: MASTODON
      
      # Platform config (non-sensitive)
      TWITCH_ENABLE: 'True'
      TWITCH_USERNAME: your_username
      YOUTUBE_ENABLE: 'True'
      YOUTUBE_USERNAME: '@YourHandle'
```

Create `.env` with only Doppler token:
```bash
DOPPLER_TOKEN=dp.st.prd.your_production_token_here
```

**All credentials stay in Doppler!** No secrets in Docker config. ✅

---

## 🔧 Systemd Service (Linux)

For production Linux deployments, run Stream Daemon as a systemd service for automatic startup and restart.

### Step 1: Create Service File

```bash
sudo nano /etc/systemd/system/stream-daemon.service
```

**For Python installation:**
```ini
[Unit]
Description=Stream Daemon - Multi-platform stream announcement bot
Documentation=https://github.com/ChiefGyk3D/Stream-Daemon
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=your_username
Group=your_username
WorkingDirectory=/home/your_username/Stream-Daemon

# Use virtual environment if created
ExecStart=/home/your_username/Stream-Daemon/venv/bin/python stream-daemon.py
# Or system Python
# ExecStart=/usr/bin/python3 /home/your_username/Stream-Daemon/stream-daemon.py

# Environment file
EnvironmentFile=/home/your_username/Stream-Daemon/.env

# Restart on failure
Restart=always
RestartSec=10

# Resource limits (optional)
MemoryMax=256M
CPUQuota=25%

# Security hardening (optional)
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=/home/your_username/Stream-Daemon

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=stream-daemon

[Install]
WantedBy=multi-user.target
```

**For Docker installation:**
```ini
[Unit]
Description=Stream Daemon (Docker)
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/your_username/Stream-Daemon/Docker

ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down

[Install]
WantedBy=multi-user.target
```

### Step 2: Enable and Start

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable stream-daemon

# Start service
sudo systemctl start stream-daemon

# Check status
sudo systemctl status stream-daemon
```

### Step 3: Manage Service

```bash
# Stop service
sudo systemctl stop stream-daemon

# Restart service
sudo systemctl restart stream-daemon

# Disable service (prevent auto-start)
sudo systemctl disable stream-daemon

# View logs
sudo journalctl -u stream-daemon -f

# View logs from last boot
sudo journalctl -u stream-daemon -b
```

---

## ☁️ Cloud Deployment

### AWS EC2

**Launch instance:**
1. Choose Ubuntu 22.04 LTS AMI
2. t3.micro (free tier eligible, sufficient for Stream Daemon)
3. Security group: Allow SSH (22) and HTTPS (443) outbound
4. Create or use existing key pair

**Connect and install:**
```bash
ssh -i your-key.pem ubuntu@your-instance-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python
sudo apt install python3 python3-pip python3-venv git -y

# Clone and install (follow Python Installation above)
git clone https://github.com/ChiefGyk3D/Stream-Daemon.git
cd Stream-Daemon
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
nano .env

# Setup systemd service (see above)
sudo nano /etc/systemd/system/stream-daemon.service
sudo systemctl enable --now stream-daemon
```

**Use IAM roles for AWS Secrets:**
```bash
# No AWS credentials needed! Use instance role
SECRETS_MANAGER=aws
AWS_REGION=us-east-1
SECRETS_AWS_TWITCH_SECRET_NAME=stream-daemon/twitch
```

### Google Cloud (Cloud Run)

**Build and deploy:**
```bash
# Install gcloud CLI
curl https://sdk.cloud.google.com | bash

# Build container
gcloud builds submit --tag gcr.io/your-project/stream-daemon

# Deploy
gcloud run deploy stream-daemon \
  --image gcr.io/your-project/stream-daemon \
  --platform managed \
  --region us-central1 \
  --memory 256Mi \
  --cpu 1 \
  --set-env-vars TWITCH_ENABLE=True,TWITCH_USERNAME=your_username \
  --set-secrets TWITCH_CLIENT_ID=twitch-client-id:latest \
  --allow-unauthenticated
```

### DigitalOcean Droplet

**Create droplet:**
1. Choose Ubuntu 22.04 LTS
2. Basic plan ($4/mo sufficient)
3. Add SSH key

**Same as EC2 setup above:**
```bash
ssh root@your-droplet-ip
# Follow Python installation steps
```

### Heroku

**Deploy to Heroku:**
```bash
# Install Heroku CLI
curl https://cli-assets.heroku.com/install.sh | sh

# Login
heroku login

# Create app
heroku create your-stream-daemon

# Set config vars
heroku config:set TWITCH_ENABLE=True
heroku config:set TWITCH_USERNAME=your_username
heroku config:set TWITCH_CLIENT_ID=your_client_id
heroku config:set TWITCH_CLIENT_SECRET=your_secret

# Deploy
git push heroku main

# View logs
heroku logs --tail
```

---

## 💻 Development Setup

For contributors and developers:

### Step 1: Clone and Setup

```bash
# Fork repository on GitHub first

# Clone your fork
git clone https://github.com/YOUR_USERNAME/Stream-Daemon.git
cd Stream-Daemon

# Add upstream remote
git remote add upstream https://github.com/ChiefGyk3D/Stream-Daemon.git

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install black flake8 pytest
```

### Step 2: Configure Development Environment

```bash
# Copy example
cp .env.example .env.dev

# Use Doppler dev environment
SECRETS_MANAGER=doppler
DOPPLER_TOKEN=dp.st.dev.your_dev_token
# Or set up .env.dev with test credentials
```

### Step 3: Code Formatting

```bash
# Format code with Black
black stream-daemon.py stream_daemon/

# Check linting
flake8 stream-daemon.py stream_daemon/
```

### Step 4: Run Tests

```bash
# Run all tests
python3 tests/test_doppler_all.py

# Run specific platform tests
python3 tests/test_doppler_twitch.py
```

### Step 5: Create Pull Request

```bash
# Create feature branch
git checkout -b feature/amazing-feature

# Make changes, commit
git add .
git commit -m "Add amazing feature"

# Push to your fork
git push origin feature/amazing-feature

# Open PR on GitHub
```

---

## 🔧 Troubleshooting

### Python Installation Issues

**"python3: command not found"**
```bash
# Install Python
# Ubuntu/Debian:
sudo apt install python3

# macOS:
brew install python3

# Verify
python3 --version
```

**"pip: command not found"**
```bash
# Install pip
# Ubuntu/Debian:
sudo apt install python3-pip

# macOS (usually included with Python)
python3 -m ensurepip

# Verify
pip3 --version
```

**Dependency installation fails**
```bash
# Upgrade pip
python3 -m pip install --upgrade pip

# Install with verbose output
pip3 install -r requirements.txt --verbose

# If specific package fails, install separately
pip3 install package-name --verbose
```

### Docker Issues

**"docker: command not found"**
```bash
# Install Docker (Linux)
curl -fsSL https://get.docker.com | sudo sh

# Add user to docker group
sudo usermod -aG docker $USER

# Log out and back in
```

**"permission denied while trying to connect to the Docker daemon"**
```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Log out and back in, or:
newgrp docker
```

**"docker-compose: command not found"**
```bash
# Install docker-compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

**Container won't start**
```bash
# Check logs
docker logs stream-daemon

# Check for port conflicts
docker ps

# Remove and recreate
docker-compose down
docker-compose up -d
```

### Systemd Service Issues

**Service won't start**
```bash
# Check status
sudo systemctl status stream-daemon

# View logs
sudo journalctl -u stream-daemon -n 50

# Common issues:
# - Wrong path in ExecStart
# - Missing .env file
# - Wrong user/group
# - Python not found
```

**Service starts but stops immediately**
```bash
# Check for errors in code
sudo journalctl -u stream-daemon -n 100

# Test running manually
cd /path/to/Stream-Daemon
python3 stream-daemon.py

# Check permissions
ls -la .env
# Should be readable by service user
```

### Memory Issues (Raspberry Pi, etc.)

**Out of memory errors**
```bash
# Add swap space (Linux)
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Reduce check interval to lower memory usage
SETTINGS_CHECK_INTERVAL=10  # Check less frequently
```

---

## 📚 Next Steps

Now that Stream Daemon is installed:

- **[Quick Start Guide](quickstart.md)** - Get up and running in 10 minutes
- **[Platform Setup](../platforms/)** - Configure Twitch, YouTube, Kick, Mastodon, etc.
- **[Secrets Management](../configuration/secrets.md)** - Secure your credentials with Doppler
- **[Custom Messages](../features/custom-messages.md)** - Personalize announcements

---

## 💬 Need Help?

- 📖 **Documentation:** [docs/README.md](../README.md)
- 🐛 **Bug Reports:** [GitHub Issues](https://github.com/ChiefGyk3D/Stream-Daemon/issues)
- 💬 **Questions:** [GitHub Discussions](https://github.com/ChiefGyk3D/Stream-Daemon/discussions)
