# systemd Service Installation

Run Stream Daemon as a systemd service for automatic startup, monitoring, and logging.

## Quick Install

```bash
# Run the installer (requires sudo)
sudo ./install-systemd.sh
```

The installer will:
- ✅ Prompt for deployment mode selection (Python or Docker)
- ✅ Python mode: Create a Python virtual environment (if needed) and install dependencies
- ✅ Docker mode: Check for Docker installation and build the Docker image if needed
- ✅ **Docker mode: Detect existing images and offer to rebuild**
- ✅ **Docker mode: Provide detailed error messages and solutions if build fails**
- ✅ Create systemd service file
- ✅ Optionally enable service on boot
- ✅ Optionally start the service immediately

### Installation Features

**Smart Docker Image Detection:**
- Checks if `stream-daemon` image already exists
- Shows image details (tag, size, ID)
- Offers option to rebuild existing images
- Detects and reports build failures with specific solutions

**Automated Error Recovery:**
The installer analyzes build failures and provides solutions for:
- No space left on device → Suggests cleaning Docker cache
- Cannot connect to Docker daemon → Instructions to start Docker
- Permission denied → Guidance on adding user to docker group
- Missing Dockerfile → Shows expected path
- Missing dependencies → Verification steps

**Prerequisites Checking:**
- Validates Docker and docker-compose installation
- Checks if user is in docker group
- Warns about missing .env file (with option to continue)
- Verifies all required files exist before building

### Deployment Modes

**Python Mode:**
- Uses Python virtual environment
- Dependencies installed locally
- Lighter weight
- Suitable for development and simple deployments

**Docker Mode:**
- Uses Docker containers
- Isolated environment
- Consistent deployment
- Suitable for production and complex deployments
- Requires Docker and docker-compose to be installed

---

## Manual Installation

If you prefer to install manually:

### Python Deployment

#### 1. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 2. Create Service File

Create `/etc/systemd/system/stream-daemon.service`:

```ini
[Unit]
Description=Stream Daemon - Multi-platform Live Stream Monitor
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=YOUR_USERNAME
Group=YOUR_USERNAME
WorkingDirectory=/path/to/stream-daemon
Environment="PATH=/path/to/stream-daemon/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/path/to/stream-daemon/venv/bin/python /path/to/stream-daemon/stream-daemon.py
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
ReadWritePaths=/path/to/stream-daemon

[Install]
WantedBy=multi-user.target
```

**Replace:**
- `YOUR_USERNAME` with your Linux username
- `/path/to/stream-daemon` with the full path to your project directory

#### 3. Enable and Start

```bash
sudo systemctl daemon-reload
sudo systemctl enable stream-daemon
sudo systemctl start stream-daemon
```

---

### Docker Deployment

#### 1. Build Docker Image

```bash
cd /path/to/stream-daemon
docker build -t stream-daemon -f Docker/Dockerfile .
```

#### 2. Create Service File

Create `/etc/systemd/system/stream-daemon.service`:

```ini
[Unit]
Description=Stream Daemon - Multi-platform Live Stream Monitor (Docker)
After=docker.service network-online.target
Requires=docker.service
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
User=YOUR_USERNAME
Group=YOUR_USERNAME
WorkingDirectory=/path/to/stream-daemon

# Start the Docker container
ExecStart=/usr/bin/docker run -d \
    --name stream-daemon \
    --restart unless-stopped \
    --env-file /path/to/stream-daemon/.env \
    -v /path/to/stream-daemon/messages.txt:/app/messages.txt:ro \
    -v /path/to/stream-daemon/end_messages.txt:/app/end_messages.txt:ro \
    stream-daemon

# Stop and remove the container
ExecStop=/usr/bin/docker stop stream-daemon
ExecStopPost=/usr/bin/docker rm -f stream-daemon

StandardOutput=journal
StandardError=journal
SyslogIdentifier=stream-daemon

[Install]
WantedBy=multi-user.target
```

**Replace:**
- `YOUR_USERNAME` with your Linux username
- `/path/to/stream-daemon` with the full path to your project directory

#### 3. Enable and Start

```bash
sudo systemctl daemon-reload
sudo systemctl enable stream-daemon
sudo systemctl start stream-daemon
```

---

## Service Management

### Start/Stop/Restart

```bash
# Start the service
sudo systemctl start stream-daemon

# Stop the service
sudo systemctl stop stream-daemon

# Restart the service
sudo systemctl restart stream-daemon

# Check status
sudo systemctl status stream-daemon
```

### Enable/Disable Auto-Start

```bash
# Enable (start on boot)
sudo systemctl enable stream-daemon

# Disable (don't start on boot)
sudo systemctl disable stream-daemon
```

### View Logs

```bash
# View recent logs
sudo journalctl -u stream-daemon

# Follow logs in real-time
sudo journalctl -u stream-daemon -f

# View logs since last boot
sudo journalctl -u stream-daemon -b

# View last 100 lines
sudo journalctl -u stream-daemon -n 100
```

---

## Uninstall

```bash
# Run the uninstaller (requires sudo)
sudo ./uninstall-systemd.sh
```

The uninstaller will:
- Stop the service
- Disable auto-start
- Remove the service file
- Reload systemd

**Note:** Project files, virtual environment, and `.env` are NOT deleted.

---

## Troubleshooting

### Service Won't Start

**Check the status:**
```bash
sudo systemctl status stream-daemon
```

**Common issues:**

1. **Missing .env file:**
   ```bash
   # Copy and configure
   cp .env.example .env
   nano .env
   ```

2. **Permission errors:**
   ```bash
   # Ensure correct ownership
   sudo chown -R $USER:$USER /path/to/stream-daemon
   ```

3. **Missing dependencies:**
   ```bash
   # Reinstall dependencies
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Python path issues:**
   - Edit `/etc/systemd/system/stream-daemon.service`
   - Verify `ExecStart` path points to correct Python executable
   - Run `sudo systemctl daemon-reload` after editing

### View Detailed Logs

```bash
# Show all errors
sudo journalctl -u stream-daemon -p err

# Show logs from last 30 minutes
sudo journalctl -u stream-daemon --since "30 minutes ago"

# Show logs from specific date
sudo journalctl -u stream-daemon --since "2025-01-01 00:00:00"
```

### Docker-Specific Issues

**Docker image not found:**
```bash
# Check if image exists
docker images | grep stream-daemon

# Rebuild manually
cd /path/to/stream-daemon
docker build -t stream-daemon -f Docker/Dockerfile .
```

**Docker daemon not running:**
```bash
# Start Docker service
sudo systemctl start docker

# Enable Docker to start on boot
sudo systemctl enable docker

# Check Docker status
sudo systemctl status docker
```

**Permission denied errors:**
```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Log out and back in for changes to take effect
# Or use newgrp to apply immediately (in current shell)
newgrp docker
```

**Container won't start:**
```bash
# Check Docker logs
docker logs stream-daemon

# Inspect container
docker inspect stream-daemon

# Remove and recreate
docker rm -f stream-daemon
sudo systemctl restart stream-daemon
```

**Image build failures:**
```bash
# Common issue: No space left
docker system prune -a  # Clean up unused images/containers

# Common issue: Network timeout
# Try again or check internet connection

# Common issue: Missing files
ls -la Docker/Dockerfile requirements.txt  # Verify files exist

# View detailed build output
docker build -t stream-daemon -f Docker/Dockerfile . --progress=plain
```

**Environment file not loading:**
```bash
# Verify .env exists and has correct permissions
ls -la .env
cat .env  # Check contents (careful with secrets!)

# Ensure path in service file is absolute
grep "env-file" /etc/systemd/system/stream-daemon.service
```

### Restart After Crash

The service is configured with `Restart=always` and `RestartSec=10`:
- Automatically restarts if it crashes
- Waits 10 seconds between restart attempts
- Check logs to diagnose why it's crashing

### Manual Stop After Auto-Restart

```bash
# Stop and prevent restart until next boot
sudo systemctl stop stream-daemon

# Disable completely
sudo systemctl disable stream-daemon
sudo systemctl stop stream-daemon
```

---

## Configuration Updates

After changing `.env` or configuration:

```bash
# Restart to apply changes
sudo systemctl restart stream-daemon

# Verify it's running
sudo systemctl status stream-daemon

# Watch logs for errors
sudo journalctl -u stream-daemon -f
```

---

## Security Hardening

The service includes security options:

| Option | Description |
|--------|-------------|
| `NoNewPrivileges=true` | Prevents privilege escalation |
| `PrivateTmp=true` | Isolates /tmp directory |
| `ProtectSystem=strict` | Read-only system directories |
| `ProtectHome=read-only` | Read-only home directories |
| `ReadWritePaths=...` | Only project dir is writable |

**Additional hardening (optional):**

Edit `/etc/systemd/system/stream-daemon.service` and add:

```ini
[Service]
# ... existing options ...

# Network restrictions
PrivateNetwork=false
RestrictAddressFamilies=AF_INET AF_INET6

# Filesystem restrictions
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true

# Capabilities
CapabilityBoundingSet=
AmbientCapabilities=
```

Reload after editing:
```bash
sudo systemctl daemon-reload
sudo systemctl restart stream-daemon
```

---

## Performance Monitoring

### Check Resource Usage

```bash
# CPU and memory usage
systemctl status stream-daemon

# More detailed info
top -p $(pgrep -f stream-daemon)

# Or with htop
htop -p $(pgrep -f stream-daemon)
```

### Boot Time Analysis

```bash
# See how long Stream Daemon takes to start
systemd-analyze blame | grep stream-daemon

# Show service startup order
systemd-analyze critical-chain stream-daemon
```

---

## Multiple Instances

To run multiple Stream Daemon instances:

1. **Create separate project directories:**
   ```bash
   /home/user/stream-daemon-1/
   /home/user/stream-daemon-2/
   ```

2. **Create separate service files:**
   ```bash
   /etc/systemd/system/stream-daemon-1.service
   /etc/systemd/system/stream-daemon-2.service
   ```

3. **Update service names and paths in each file**

4. **Enable and start:**
   ```bash
   sudo systemctl enable stream-daemon-1
   sudo systemctl enable stream-daemon-2
   sudo systemctl start stream-daemon-1
   sudo systemctl start stream-daemon-2
   ```

---

## Docker Alternative

If you prefer Docker over systemd, see [Docker Installation Guide](getting-started/installation.md#docker).

**Pros of systemd:**
- Native Linux service management
- Direct access to logs via journalctl
- Lower resource overhead
- Easier local development

**Pros of Docker:**
- Consistent environment across systems
- Easier deployment and scaling
- Isolated dependencies
- Better for production deployments

---

## See Also

- [Installation Guide](getting-started/installation.md)
- [Configuration Guide](configuration/secrets.md)
- [Troubleshooting](README.md#troubleshooting)
