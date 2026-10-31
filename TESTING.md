# Testing Scripts

Quick reference for all testing scripts in the Stream Daemon project.

## Test Scripts Overview

| Script | Purpose | Environment | Run Time |
|--------|---------|-------------|----------|
| `tests/test_connection.py` | Full production integration test | Local | 30s-1min |
| `tests/test_local_install.py` | Validate local Python installation | Local | 5-10s |
| `tests/test_ollama.py` | Test Ollama AI integration | Local/Docker | 30s |
| `test_ollama_quick.sh` | Quick Ollama connectivity check | Local | 5s |
| `test_docker_build.sh` | Build and test Docker image | Docker | 2-5min |
| `tests/run_all_tests.py` | Full test suite | Local | 1-2min |

## Quick Start

### Test Production Integration (Recommended)

```bash
# Run comprehensive production test with real .env data
python3 tests/test_connection.py
```

**Tests:**
- ✅ Streaming platform authentication (Twitch, YouTube, Kick)
- ✅ Social platform authentication (Mastodon, Bluesky, Discord, Matrix)
- ✅ LLM provider authentication (Ollama or Gemini)
- ✅ Live stream detection
- ✅ AI message generation with real stream data
- ✅ Optional: Post AI message to all social platforms
- ✅ Production readiness validation

### Test Local Installation

```bash
# Run comprehensive local environment test
python3 tests/test_local_install.py
```

**Tests:**
- ✅ Python 3.11+ version
- ✅ Core dependencies (Twitch, Mastodon, Bluesky, Discord, Matrix)
- ✅ AI dependencies (Gemini, Ollama) - optional
- ✅ Security providers (AWS, Vault, Doppler) - optional
- ✅ Stream Daemon module imports
- ✅ CVE security patches

### Test Docker Build

```bash
# Run comprehensive Docker build test
./test_docker_build.sh
```

**Tests:**
- ✅ Docker installation
- ✅ Docker daemon status
- ✅ Image build
- ✅ Python in container
- ✅ Dependencies in container
- ✅ docker-compose validation

### Test Ollama Integration

```bash
# Quick connectivity test
./test_ollama_quick.sh

# Full AI generation test
python3 tests/test_ollama.py
```

**Requirements:**
- Ollama server running (local or remote)
- `.env` configured with Ollama settings

### Run Full Test Suite

```bash
# Run all unit and integration tests
python3 tests/run_all_tests.py
```

## Test Script Details

### test_connection.py ⭐

**Purpose:** Comprehensive production integration test that validates your entire setup using real .env configuration and live stream data.

**Usage:**
```bash
python3 tests/test_connection.py
```

**What it tests:**
1. **Streaming Platforms** - Authenticates and checks live status for all enabled platforms (Twitch, YouTube, Kick)
2. **Social Platforms** - Authenticates all enabled social media platforms (Mastodon, Bluesky, Discord, Matrix)
3. **LLM Provider** - Tests AI message generation using real live stream data
4. **End-to-End Flow** - Optionally posts AI-generated messages to all social platforms

**Exit Codes:**
- `0` - All tests passed, production ready
- `1` - One or more tests failed

**Output Example:**
```
🔬 Stream Daemon - Production Integration Test
================================================

📡 Testing Streaming Platforms...
  ✅ Twitch - LIVE - 110 viewers
  ✅ YouTube - LIVE - 245 viewers
  ✅ Kick - LIVE - 11,002 viewers

💬 Testing Social Platforms...
  ✅ Mastodon - Authenticated
  ✅ Bluesky - Authenticated
  ✅ Discord - Authenticated
  ✅ Matrix - Authenticated

🤖 Testing LLM Generation...
  ✅ Generated AI message (258 chars)
  
  Would you like to post this to all social platforms? (yes/no): yes
  
  ✅ Mastodon - Posted (ID: 115923811563045709)
  ✅ Bluesky - Posted (ID: 3mcskic5row2b)
  ✅ Discord - Posted (ID: 1462916988945825874)
  ✅ Matrix - Posted (ID: $rpa3cON...)

================================================
✅ PRODUCTION READY - All systems operational!
================================================
```

### test_local_install.py

**Purpose:** Validates that your local Python environment has all required dependencies and meets security requirements.

**Usage:**
```bash
python3 tests/test_local_install.py
```

**Exit Codes:**
- `0` - All tests passed
- `1` - One or more tests failed

**Output Example:**
```
Stream Daemon - Local Installation Test
========================================

[1/7] Checking Python version...
✅ Python 3.11.2

[2/7] Checking core dependencies...
✅ All core dependencies installed

[3/7] Checking AI/LLM dependencies...
✅ Gemini client available
✅ Ollama client available

[4/7] Checking security dependencies...
✅ AWS Secrets Manager available
⚠️  Vault client not installed (optional)

[5/7] Checking requirements.txt...
✅ requirements.txt found and readable

[6/7] Testing Stream Daemon imports...
✅ All Stream Daemon modules importable

[7/7] Checking CVE-affected packages...
✅ requests >= 2.32.5
✅ urllib3 >= 2.5.0
✅ protobuf >= 6.33.1

====================================
✅ SUCCESS: 7/7 tests passed
====================================
```

### test_docker_build.sh

**Purpose:** Builds a Docker image and validates the containerized environment.

**Usage:**
```bash
./test_docker_build.sh
```

**What it does:**
1. Checks Docker installation
2. Verifies Docker daemon is running
3. Builds image from `Docker/Dockerfile`
4. Reports image size
5. Tests Python in container
6. Tests dependency imports in container
7. Validates docker-compose.yml (if present)

**Output Example:**
```
🐳 Stream Daemon - Docker Build & Test
======================================

[1/6] Checking Docker installation...
✅ Docker version 24.0.5

[2/6] Checking Docker daemon...
✅ Docker daemon is running

[3/6] Building Docker image...
✅ Docker image built successfully

[4/6] Checking image size...
✅ Image size: 1.2GB

[5/6] Testing Python environment...
✅ Python 3.11.2

[6/6] Testing dependencies...
✅ All dependencies working

====================================
✅ SUCCESS - Docker build passed!
====================================
```

### test_ollama.py

**Purpose:** Comprehensive test of Ollama AI integration with message generation.

**Prerequisites:**
```bash
# .env must contain:
LLM_ENABLE=True
LLM_PROVIDER=ollama
LLM_OLLAMA_HOST=http://192.168.1.100
LLM_OLLAMA_PORT=11434
LLM_MODEL=gemma2:2b
```

**Usage:**
```bash
# Local testing
python3 tests/test_ollama.py

# Docker testing
docker run --rm --env-file .env stream-daemon:test python3 test_ollama.py
```

**What it tests:**
- ✅ Ollama server connectivity
- ✅ Model availability
- ✅ Bluesky message generation (300 char limit)
- ✅ Mastodon message generation (500 char limit)
- ✅ Stream end message generation

**Output Example:**
```
Testing Ollama Integration
===========================

✅ Ollama connection initialized
✅ Connected to: http://192.168.1.100:11434
✅ Model: gemma3:4b

Generated Bluesky message (202 chars):
🎮 Live now! Join us for an epic gaming session...

Generated Mastodon message (286 chars):
Hey everyone! 👋 We're going live right now...

Generated stream end message (208 chars):
That's a wrap! 🎬 Thanks to everyone...

✅ SUCCESS: All Ollama tests passed!
```

### test_ollama_quick.sh

**Purpose:** Quick connectivity check to Ollama server.

**Usage:**
```bash
./test_ollama_quick.sh
```

**What it does:**
- Loads Ollama settings from `.env`
- Tests HTTP connection to Ollama API
- Lists available models

**Output Example:**
```
Quick Ollama Connectivity Test
===============================

Testing connection to: http://192.168.1.100:11434

✅ Ollama server is reachable

Available models:
- gemma3:4b
- llama3.2:3b
- mistral:7b

✅ Connection test passed!
```

## Troubleshooting

### test_local_install.py fails

**Common issues:**
1. **Python version too old**
   ```bash
   sudo apt install python3.11
   ```

2. **Missing dependencies**
   ```bash
   pip3 install -r requirements.txt
   ```

3. **CVE warnings**
   ```bash
   pip3 install --upgrade requests urllib3 protobuf
   ```

### test_docker_build.sh fails

**Common issues:**
1. **Docker not installed**
   - Install: https://docs.docker.com/get-docker/

2. **Docker daemon not running**
   ```bash
   sudo systemctl start docker
   ```

3. **Build fails**
   ```bash
   # Clear cache and rebuild
   docker builder prune -a
   docker build --no-cache -t stream-daemon:test -f Docker/Dockerfile .
   ```

### test_ollama.py fails

**Common issues:**
1. **Connection refused**
   - Check Ollama is running: `curl http://YOUR_IP:11434/api/tags`
   - Verify `.env` has correct IP/port
   - Check firewall: `sudo ufw allow 11434/tcp`

2. **Model not found**
   ```bash
   # List available models
   ollama list
   
   # Pull missing model
   ollama pull gemma3:4b
   ```

3. **From Docker container**
   - Use actual IP address, not `localhost`
   - Ensure Docker network can reach Ollama server
   - Test: `docker run --rm stream-daemon:test ping YOUR_OLLAMA_IP`

## Integration with CI/CD

These test scripts can be integrated into continuous integration pipelines:

```yaml
# Example GitHub Actions workflow
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Test installation
        run: python3 test_local_install.py
      - name: Build Docker
        run: ./test_docker_build.sh
      - name: Run test suite
        run: python3 tests/run_all_tests.py
```

## Additional Resources

- [Full Testing Guide](docs/development/testing.md)
- [Running Tests](tests/RUNNING_TESTS.md)
- [Ollama Setup](docs/features/ai-messages.md)
- [Docker Setup](Docker/README.md)

## Need Help?

- Check [docs/development/testing.md](docs/development/testing.md) for detailed troubleshooting
- Review test output carefully - it shows specific remediation steps
- Open an issue on GitHub with test output if problems persist
