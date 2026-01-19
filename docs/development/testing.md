# Testing Guide

This guide covers testing procedures for Stream Daemon in both local and Docker environments.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Local Environment Testing](#local-environment-testing)
- [Docker Environment Testing](#docker-environment-testing)
- [Ollama Integration Testing](#ollama-integration-testing)
- [Continuous Integration](#continuous-integration)

## Prerequisites

### General Requirements
- Git
- Access to streaming platform APIs (Twitch, YouTube, Kick)
- Access to social platform APIs (Bluesky, Mastodon, Discord, Matrix)

### Local Testing Requirements
- Python 3.10+
- pip or pip3
- Virtual environment (recommended)

### Docker Testing Requirements
- Docker Engine 20.10+
- docker-compose (optional)
- 2GB+ free disk space

## Local Environment Testing

### 1. Quick Installation Test

Run the comprehensive installation test:

```bash
python3 test_local_install.py
```

This test validates:
- ✅ Python version (3.10+)
- ✅ Core dependencies (TwitchAPI, Mastodon, Bluesky, Discord, Matrix)
- ✅ AI/LLM dependencies (Gemini, Ollama)
- ✅ Security providers (AWS Secrets, Vault, Doppler)
- ✅ Stream Daemon module imports
- ✅ CVE-affected package versions

**Expected Output:**
```
✅ SUCCESS: 7/7 tests passed
```

### 2. Manual Dependency Check

If you prefer to check manually:

```bash
# Check Python version
python3 --version

# Install dependencies
pip3 install -r requirements.txt

# Test imports
python3 -c "import twitchAPI; import mastodon; import atproto; print('Core deps OK')"
python3 -c "import google.genai; import ollama; print('AI deps OK')"
```

### 3. Module Import Test

Test that all Stream Daemon modules load correctly:

```bash
python3 -c "from stream_daemon import messaging, publisher; print('Modules OK')"
python3 -c "from stream_daemon.ai import generator; print('AI module OK')"
python3 -c "from stream_daemon.platforms.streaming import twitch, youtube, kick; print('Streaming OK')"
python3 -c "from stream_daemon.platforms.social import bluesky, mastodon, discord, matrix; print('Social OK')"
```

### 4. CVE Security Check

Verify critical packages meet minimum versions:

```bash
pip3 list | grep -E "requests|urllib3|protobuf"
```

**Required versions:**
- `requests >= 2.32.5`
- `urllib3 >= 2.5.0`
- `protobuf >= 6.33.1`

## Docker Environment Testing

### 1. Full Docker Build Test

Run the comprehensive Docker test:

```bash
./test_docker_build.sh
```

This test validates:
- ✅ Docker installation
- ✅ Docker daemon running
- ✅ Image builds successfully
- ✅ Python works in container
- ✅ All dependencies install
- ✅ docker-compose configuration (if present)

**Expected Output:**
```
✅ SUCCESS - Docker build and tests passed!
```

### 2. Manual Docker Build

Build the image manually:

```bash
cd /path/to/twitch-and-toot
docker build -t stream-daemon:test -f Docker/Dockerfile .
```

**Troubleshooting build failures:**
- Check Dockerfile syntax
- Verify requirements.txt is present
- Ensure base image is accessible
- Check Docker daemon logs: `docker system events`

### 3. Test Container Runtime

Start a test container:

```bash
# Create test .env
cp .env.example .env
# Edit .env with your credentials

# Run container
docker run --rm --env-file .env stream-daemon:test python3 --version

# Test with actual daemon
docker run --rm --env-file .env stream-daemon:test python3 stream-daemon.py
```

### 4. docker-compose Testing

If using docker-compose:

```bash
# Validate configuration
docker-compose -f Docker/docker-compose.yml config

# Start services
docker-compose -f Docker/docker-compose.yml up -d

# Check logs
docker-compose -f Docker/docker-compose.yml logs -f

# Stop services
docker-compose -f Docker/docker-compose.yml down
```

## Ollama Integration Testing

### Local Ollama Testing

#### Quick Connection Test

```bash
./test_ollama_quick.sh
```

This tests basic connectivity to your Ollama server.

#### Comprehensive Ollama Test

```bash
# Ensure .env is configured with Ollama settings
python3 test_ollama.py
```

**Expected output:**
```
✅ Ollama connection initialized
✅ Connected to: http://YOUR_IP:11434
✅ Model: gemma3:4b

Generated Bluesky message (202 chars):
[AI-generated message content]

Generated Mastodon message (286 chars):
[AI-generated message content]

Generated stream end message (208 chars):
[AI-generated message content]

✅ SUCCESS: All Ollama tests passed!
```

#### Required .env Configuration

```bash
LLM_ENABLE=True
LLM_PROVIDER=ollama
LLM_OLLAMA_HOST=http://192.168.1.100
LLM_OLLAMA_PORT=11434
LLM_MODEL=gemma3:4b
```

### Docker Ollama Testing

Test Ollama from within Docker container:

```bash
docker run --rm --env-file .env \
  -e LLM_ENABLE=True \
  -e LLM_PROVIDER=ollama \
  -e LLM_OLLAMA_HOST=http://YOUR_OLLAMA_IP:11434 \
  -e LLM_MODEL=gemma3:4b \
  stream-daemon:test python3 test_ollama.py
```

**Note:** Ensure Docker container can reach your Ollama server's IP address. Do not use `localhost` - use actual IP or Docker network names.

### Ollama Network Troubleshooting

If Docker can't reach Ollama:

```bash
# Test connectivity from container
docker run --rm stream-daemon:test ping -c 3 YOUR_OLLAMA_IP

# Check Ollama is listening on all interfaces
curl http://YOUR_OLLAMA_IP:11434/api/tags

# Verify firewall rules allow Docker bridge network
sudo iptables -L | grep 11434
```

## Continuous Integration

### Pre-commit Checks

Before committing code:

```bash
# Run all tests
python3 tests/run_all_tests.py

# Check for security issues
pip3 check

# Validate syntax
python3 -m py_compile stream_daemon/**/*.py
```

### Test Matrix

| Test Type | Local | Docker | CI/CD |
|-----------|-------|--------|-------|
| Installation | ✅ | ✅ | ✅ |
| Unit Tests | ✅ | ✅ | ✅ |
| Integration | ✅ | ✅ | ⚠️ |
| Ollama | ✅ | ✅ | ❌ |
| Gemini | ✅ | ✅ | ⚠️ |

**Legend:**
- ✅ Fully supported
- ⚠️ Requires credentials/configuration
- ❌ Not available (requires local server)

## Common Issues

### Python Version Mismatch

**Error:** `Python 3.10+ required, found 3.9.x`

**Solution:**
```bash
# Ubuntu/Debian
sudo apt install python3.10 python3.10-venv

# Update alternatives
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1
```

### Missing Dependencies

**Error:** `ModuleNotFoundError: No module named 'X'`

**Solution:**
```bash
# Reinstall dependencies
pip3 install -r requirements.txt --force-reinstall

# Or install specific package
pip3 install X
```

### Docker Build Failures

**Error:** `ERROR: failed to solve`

**Solution:**
```bash
# Clear Docker cache
docker builder prune -a

# Rebuild without cache
docker build --no-cache -t stream-daemon:test -f Docker/Dockerfile .
```

### Ollama Connection Refused

**Error:** `Connection refused` or `Failed to connect`

**Solution:**
1. Verify Ollama is running: `curl http://YOUR_IP:11434/api/tags`
2. Check firewall: `sudo ufw allow 11434/tcp`
3. Use IP address, not `localhost` from Docker
4. Verify .env has correct `LLM_OLLAMA_HOST` and `LLM_OLLAMA_PORT`

## Next Steps

After successful testing:

1. **Configure platforms:** Set up API credentials in `.env`
2. **Start monitoring:** Run `python3 stream-daemon.py` or use Docker
3. **Monitor logs:** Check for successful connections and message posts
4. **Production deployment:** Follow [systemd-service.md](../getting-started/systemd-service.md) for persistent service

## Additional Resources

- [Running Tests](../../tests/RUNNING_TESTS.md) - Detailed test suite documentation
- [AI Messages](../features/ai-messages.md) - AI/LLM setup guide
- [Ollama Migration](../features/ollama-migration.md) - Ollama-specific setup
- [Quick Reference](../../scripts/README.md) - Helper scripts
