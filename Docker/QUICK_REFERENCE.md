# Stream Daemon - Docker Quick Reference

## 🚀 Quick Start

```bash
cd Docker
cp docker-compose.example.yml docker-compose.yml
# Edit docker-compose.yml with your API credentials
docker-compose up -d
```

## 📋 Essential Commands

### Container Management
```bash
# Start container
docker-compose up -d

# Stop container
docker-compose down

# Restart container
docker-compose restart

# View status
docker-compose ps

# View resource usage
docker stats stream-daemon
```

### Logs & Debugging
```bash
# View all logs
docker-compose logs

# Follow logs (live)
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100

# Logs for specific time
docker-compose logs --since 1h
```

### Building
```bash
# Build normally
docker-compose build

# Build from scratch (no cache)
docker-compose build --no-cache

# Pull and rebuild
docker-compose pull && docker-compose build
```

### Updates & Maintenance
```bash
# Update and restart
docker-compose down
docker-compose pull
docker-compose up -d

# Rebuild after code changes
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Clean up old images
docker image prune -a
```

## ⚙️ Configuration

### Minimum Required Environment Variables

```yaml
# One Streaming Platform
TWITCH_ENABLE: 'True'
TWITCH_USERNAME: 'yourname'
TWITCH_CLIENT_ID: 'your_id'
TWITCH_CLIENT_SECRET: 'your_secret'

# One Social Platform
MASTODON_ENABLE_POSTING: 'True'
MASTODON_API_BASE_URL: 'https://mastodon.social'
MASTODON_CLIENT_ID: 'your_id'
MASTODON_CLIENT_SECRET: 'your_secret'
MASTODON_ACCESS_TOKEN: 'your_token'
```

### Optional Features

```yaml
# LLM/AI Messages
LLM_ENABLE: 'True'
LLM_PROVIDER: 'gemini'
LLM_GEMINI_API_KEY: 'your_key'

# Multiple Platforms
YOUTUBE_ENABLE: 'True'
KICK_ENABLE: 'True'
BLUESKY_ENABLE_POSTING: 'True'
DISCORD_ENABLE_POSTING: 'True'
MATRIX_ENABLE_POSTING: 'True'

# Secret Manager
SECRET_MANAGER: 'doppler'
DOPPLER_TOKEN: 'dp.st.xxxxx'
```

## 🔍 Troubleshooting

### Check if container is running
```bash
docker-compose ps
```

### View recent errors
```bash
docker-compose logs --tail=50 | grep -i error
```

### Restart after config changes
```bash
docker-compose restart
```

### Full reset
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Test module imports
```bash
docker-compose exec stream-daemon python -c "import stream_daemon; print('OK')"
```

### Interactive shell (debugging)
```bash
docker-compose exec stream-daemon /bin/bash
```

## 📊 Monitoring

### Real-time logs
```bash
docker-compose logs -f | grep -E "(LIVE|Posted|Error)"
```

### Container stats
```bash
docker stats stream-daemon
```

### Check memory usage
```bash
docker-compose exec stream-daemon free -h
```

### Check disk usage
```bash
docker system df
```

## 🔐 Secrets Management

### Using Doppler
```yaml
environment:
  SECRET_MANAGER: 'doppler'
  DOPPLER_TOKEN: '${DOPPLER_TOKEN}'  # From .env file
```

### Using .env file
```bash
# Create .env in Docker directory
echo "DOPPLER_TOKEN=dp.st.your_token" > .env
docker-compose up -d
```

## 🎯 Common Tasks

### Update credentials
1. Edit `docker-compose.yml`
2. Run `docker-compose restart`

### Add new platform
1. Edit `docker-compose.yml`
2. Add platform environment variables
3. Run `docker-compose restart`

### Enable LLM
1. Get Gemini API key from https://aistudio.google.com/apikey
2. Add to `docker-compose.yml`:
   ```yaml
   LLM_ENABLE: 'True'
   LLM_GEMINI_API_KEY: 'your_key'
   ```
3. Restart container

### Change check interval
```yaml
SETTINGS_POST_INTERVAL: '60'   # Minutes when live
SETTINGS_CHECK_INTERVAL: '5'   # Minutes when offline
```

## 📁 File Locations

### In Container
- App: `/app/stream-daemon.py`
- Package: `/app/stream_daemon/`
- Messages: `/app/messages.txt`, `/app/end_messages.txt`
- Venv: `/opt/venv/`

### On Host
- Config: `Docker/docker-compose.yml`
- Dockerfile: `Docker/Dockerfile`
- Example: `Docker/docker-compose.example.yml`
- Docs: `Docker/README.md`

## 🆘 Getting Help

1. Check `Docker/README.md` for detailed documentation
2. Review logs: `docker-compose logs`
3. Verify config: `docker-compose config`
4. Check main docs: `../README.md`
5. Platform guides: `../PLATFORM_GUIDE.md`

## 📞 Support Resources

- Main README: `../README.md`
- Platform Setup: `../PLATFORM_GUIDE.md`
- Doppler Guide: `../DOPPLER_GUIDE.md`
- Docker README: `README.md`
- Update Notes: `DOCKER_UPDATE.md`

---

**Quick Tip**: Always use `docker-compose` commands from the `Docker/` directory or specify `-f Docker/docker-compose.yml` from project root.
