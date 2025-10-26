# Stream Daemon Scripts

This directory contains utility scripts for Stream Daemon setup, configuration, and management.

## 🔧 Installation & Setup

### create-secrets.sh
**Interactive secrets setup wizard**

Helps you configure credentials across multiple secrets management platforms.

**Usage:**
```bash
./scripts/create-secrets.sh
```

**Features:**
- ✅ Supports Doppler, AWS Secrets Manager, HashiCorp Vault, and .env files
- ✅ Interactive prompts for all platforms
- ✅ Loads existing .env values as defaults
- ✅ Separates config from secrets (when using secrets managers)
- ✅ Environment-aware (dev/staging/production)

**Documentation:**
- [Secrets Wizard Guide](../docs/configuration/secrets-wizard.md)
- [Config vs Secrets Behavior](../docs/configuration/secrets-wizard-behavior.md)
- [Quick Reference](../docs/configuration/secrets-quick-reference.md)

---

### install-systemd.sh
**systemd service installation script**

Installs Stream Daemon as a Linux systemd service with automatic startup.

**Usage:**
```bash
sudo ./scripts/install-systemd.sh
```

**Features:**
- ✅ Supports both Python and Docker deployments
- ✅ Creates Python virtual environment (Python mode)
- ✅ Builds and manages Docker containers (Docker mode)
- ✅ Configures automatic restart on failure
- ✅ Sets up proper permissions and security
- ✅ Loads configuration from .env file

**Documentation:**
- [systemd Service Guide](../docs/getting-started/systemd-service.md)

---

### uninstall-systemd.sh
**systemd service removal script**

Removes the Stream Daemon systemd service and optionally cleans up Docker resources.

**Usage:**
```bash
sudo ./scripts/uninstall-systemd.sh
```

**Features:**
- ✅ Stops and disables service
- ✅ Removes systemd service file
- ✅ Cleans up Docker containers (Docker mode)
- ✅ Optionally removes Docker images
- ✅ Preserves .env and project files by default

---

### setup_matrix_bot.sh
**Matrix bot configuration helper**

Helps set up Matrix bot credentials and room configuration.

**Usage:**
```bash
./scripts/setup_matrix_bot.sh
```

---

## 📋 Prerequisites

**All scripts require:**
- Linux operating system
- Bash shell
- Run from the project root directory (not from within scripts/)

**create-secrets.sh requires:**
- Python 3.10+ installed
- Platform-specific tools (optional):
  - Doppler CLI for Doppler integration
  - AWS CLI for AWS Secrets Manager
  - Vault CLI for HashiCorp Vault

**install-systemd.sh requires:**
- Root/sudo access
- systemd (Linux)
- For Python mode: Python 3.10+, pip
- For Docker mode: Docker, Docker Compose

**uninstall-systemd.sh requires:**
- Root/sudo access
- systemd (Linux)

---

## 🚀 Quick Start

**First-time setup:**

1. **Configure secrets:**
   ```bash
   ./scripts/create-secrets.sh
   ```

2. **Install as service:**
   ```bash
   sudo ./scripts/install-systemd.sh
   ```

3. **Manage service:**
   ```bash
   sudo systemctl status stream-daemon
   sudo systemctl stop stream-daemon
   sudo systemctl start stream-daemon
   sudo journalctl -u stream-daemon -f
   ```

**To uninstall:**
```bash
sudo ./scripts/uninstall-systemd.sh
```

---

## 🔍 How Scripts Find the Project

All scripts automatically detect the project directory:

```bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
```

This means:
- Scripts can be run from anywhere
- `PROJECT_DIR` always points to the project root
- `.env` file is looked for in `PROJECT_DIR/.env`
- No manual path configuration needed

---

## 🛠️ Development

**Adding a new script:**

1. Create script in `scripts/` directory
2. Make it executable: `chmod +x scripts/your-script.sh`
3. Use proper path detection:
   ```bash
   SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
   PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
   ```
4. Reference project files via `$PROJECT_DIR`:
   ```bash
   source "$PROJECT_DIR/.env"
   python "$PROJECT_DIR/stream-daemon.py"
   ```
5. Update this README with script documentation
6. Update main README.md if it's a user-facing script

---

## 📚 See Also

- [Stream Daemon Documentation](../docs/README.md)
- [Installation Guide](../docs/getting-started/installation.md)
- [Secrets Management](../docs/configuration/secrets.md)
- [Contributing Guide](../CONTRIBUTING.md)

---

**Happy scripting! 🚀**
