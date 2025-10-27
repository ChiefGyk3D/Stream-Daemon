# Quick Start Guide

> **🚀 Get Stream Daemon running in 10 minutes**

This guide gets you from zero to posting stream announcements as fast as possible.

---

## 📋 Prerequisites

Before starting, make sure you have:

- **Python 3.10+** installed ([python.org/downloads](https://www.python.org/downloads/))
- API credentials for **at least one** streaming platform (Twitch, YouTube, or Kick)
- Account on **at least one** social platform (Mastodon, Bluesky, Discord, or Matrix)
- (Optional) [Doppler account](https://doppler.com) for secure credential storage

**Don't have credentials yet?** See [Platform Setup Guides](../platforms/) for detailed instructions.

---

## ⚡ 10-Minute Setup

### Step 1: Install (2 minutes)

```bash
# Clone repository
git clone https://github.com/ChiefGyk3D/Stream-Daemon.git
cd Stream-Daemon

# Install dependencies
pip install -r requirements.txt
```

**Having issues?** See [Installation Guide](installation.md) for troubleshooting.

### Step 2: Configure Credentials (5 minutes)

Create a `.env` file with your credentials:

```bash
# Copy example configuration
cp .env.example .env

# Edit with your credentials
nano .env  # or use your preferred editor
```

**Minimal working example:**

```bash
# =====================================
# STREAMING PLATFORMS
# =====================================
TWITCH_ENABLE=True
TWITCH_USERNAME=your_twitch_username
TWITCH_CLIENT_ID=your_client_id_here
TWITCH_CLIENT_SECRET=your_client_secret_here

# =====================================
# SOCIAL PLATFORMS
# =====================================
MASTODON_ENABLE=True
MASTODON_INSTANCE_URL=https://mastodon.social
MASTODON_ACCESS_TOKEN=your_mastodon_token_here

# =====================================
# INTERVALS (optional)
# =====================================
SETTINGS_CHECK_INTERVAL=5  # Check every 5 minutes
```

**Where to get credentials:**
- **Twitch:** [dev.twitch.tv/console/apps](https://dev.twitch.tv/console/apps)
- **Mastodon:** Your instance → Settings → Development → New Application

**Want more platforms?** See [configuration examples](#configuration-examples) below.

### Step 3: Test (2 minutes)

Verify your configuration works:

```bash
# Test Twitch connection
python3 tests/test_doppler_twitch.py

# Test Mastodon connection
python3 tests/test_mastodon.py
```

**Expected output:**
```
✅ Authentication successful
✅ Stream detection working
✅ Mastodon posting enabled
```

**Errors?** See [Troubleshooting](#troubleshooting) below.

### Step 4: Run (1 minute)

Start the daemon:

```bash
python3 stream-daemon.py
```

**You should see:**
```
🔷 Stream Daemon v2.0 Starting...
✅ Twitch: Enabled (@your_username)
✅ Mastodon: Enabled (mastodon.social)
🔄 Checking for live streams every 5 minutes...
```

**That's it!** Stream Daemon is now monitoring your Twitch streams and will post to Mastodon when you go live.

---

## 🎯 Configuration Examples

### Example 1: Twitch + Discord

Perfect for streamers with a Discord community:

```bash
# Streaming
TWITCH_ENABLE=True
TWITCH_USERNAME=your_username
TWITCH_CLIENT_ID=your_client_id
TWITCH_CLIENT_SECRET=your_client_secret

# Social
DISCORD_ENABLE=True
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/123/abc...
DISCORD_ROLE_TWITCH=@Twitch Viewers  # Optional: mention role
DISCORD_UPDATE_LIVE_MESSAGE=True     # Update embed with viewer count
```

**Bonus:** Discord will show live viewer counts and update the embed in real-time!

### Example 2: Multi-Platform Streaming

Streaming to Twitch + YouTube + Kick simultaneously:

```bash
# Streaming Platforms
TWITCH_ENABLE=True
TWITCH_USERNAME=your_twitch
TWITCH_CLIENT_ID=xxx
TWITCH_CLIENT_SECRET=yyy

YOUTUBE_ENABLE=True
YOUTUBE_USERNAME=@YourHandle  # Auto-resolves to channel ID!
YOUTUBE_API_KEY=AIzaSy...

KICK_ENABLE=True
KICK_USERNAME=your_kick

# Social Platform
MASTODON_ENABLE=True
MASTODON_INSTANCE_URL=https://mastodon.social
MASTODON_ACCESS_TOKEN=your_token

# Multi-Platform Strategy
MESSAGES_LIVE_THREADING_MODE=combined  # Single post: "Live on Twitch, YouTube, and Kick!"
MESSAGES_END_THREADING_MODE=thread     # Reply to original post when ending
```

### Example 3: AI-Powered Messages

Use Google Gemini to generate unique announcements:

```bash
# Streaming
TWITCH_ENABLE=True
TWITCH_USERNAME=your_username
TWITCH_CLIENT_ID=xxx
TWITCH_CLIENT_SECRET=yyy

# Social
MASTODON_ENABLE=True
MASTODON_INSTANCE_URL=https://mastodon.social
MASTODON_ACCESS_TOKEN=your_token

BLUESKY_ENABLE=True
BLUESKY_HANDLE=yourhandle.bsky.social
BLUESKY_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx

# AI Messages
LLM_PROVIDER=gemini
GEMINI_API_KEY=AIzaSyABC123...  # From aistudio.google.com
LLM_MAX_LENGTH_MASTODON=500
LLM_MAX_LENGTH_BLUESKY=300
```

**Result:** Every stream gets a unique, engaging announcement tailored to the platform!

### Example 4: Secure with Doppler

Keep credentials safe with enterprise secrets management:

```bash
# Secrets Manager (10-min setup, free!)
SECRETS_MANAGER=doppler
DOPPLER_TOKEN=dp.st.dev.your_token_here
SECRETS_DOPPLER_TWITCH_SECRET_NAME=TWITCH
SECRETS_DOPPLER_MASTODON_SECRET_NAME=MASTODON

# Platform Config (non-sensitive)
TWITCH_ENABLE=True
TWITCH_USERNAME=your_username

MASTODON_ENABLE=True
MASTODON_INSTANCE_URL=https://mastodon.social

# NO CREDENTIALS IN .env!
# All secrets (client IDs, tokens, etc.) stored securely in Doppler
```

**See:** [Secrets Management Guide](../configuration/secrets.md) for full Doppler setup.

---

## 🎨 Customize Messages

Create custom announcements for each platform:

### Step 1: Create Message Templates

Edit `messages.txt`:

```ini
[DEFAULT]
🔴 I'm live! Come watch: {url}

[TWITCH]
🎮 Live on Twitch! Playing {title}
Viewers: {viewers}
👉 {url}

[YOUTUBE]
📺 Streaming now on YouTube!
{url}

[KICK]
⚡ Live on Kick right now!
{url}
```

### Step 2: Enable Platform-Specific Messages

```bash
# .env
MESSAGES_USE_PLATFORM_SPECIFIC_MESSAGES=True
MESSAGES_MESSAGES_FILE=messages.txt
```

### Available Variables

- `{url}` - Stream URL (auto-generated)
- `{title}` - Stream title
- `{game}` - Game/category being played
- `{viewers}` - Current viewer count
- `{platform}` - Platform name (Twitch, YouTube, Kick)

**See:** [Custom Messages Guide](../features/custom-messages.md) for advanced templating.

---

## 🐳 Docker Quick Start

Prefer containers? Here's the fast track:

### Step 1: Edit docker-compose.yml

```yaml
version: '3.8'
services:
  stream-daemon:
    build: .
    restart: unless-stopped
    environment:
      # Streaming
      TWITCH_ENABLE: 'True'
      TWITCH_USERNAME: your_username
      TWITCH_CLIENT_ID: your_client_id
      TWITCH_CLIENT_SECRET: your_client_secret
      
      # Social
      MASTODON_ENABLE: 'True'
      MASTODON_INSTANCE_URL: https://mastodon.social
      MASTODON_ACCESS_TOKEN: your_token
      
      # Intervals
      SETTINGS_CHECK_INTERVAL: 5
    
    volumes:
      - ./messages.txt:/app/messages.txt
      - ./end_messages.txt:/app/end_messages.txt
```

### Step 2: Run

```bash
cd Docker
docker-compose up -d

# View logs
docker-compose logs -f stream-daemon
```

**See:** [Installation Guide](installation.md#docker) for detailed Docker setup.

---

## 🧪 Testing Your Setup

Before going live, test everything:

### Test Individual Platforms

```bash
# Streaming platforms
python3 tests/test_doppler_twitch.py
python3 tests/test_doppler_youtube.py
python3 tests/test_doppler_kick.py

# Social platforms
python3 tests/test_mastodon.py
python3 tests/test_bluesky.py
python3 tests/test_discord.py
python3 tests/test_matrix.py
```

### Test All Platforms

```bash
python3 tests/test_doppler_all.py
```

### What Tests Check

- ✅ API credentials are valid
- ✅ Connections successful
- ✅ Stream detection working
- ✅ No secrets leaked in logs

**All tests pass?** You're ready to go live! 🎉

---

## 🔧 Troubleshooting

### "Module not found" Error

**Problem:** Missing Python dependencies

**Solution:**
```bash
pip install -r requirements.txt

# Or upgrade dependencies
pip install --upgrade -r requirements.txt
```

### "Authentication failed" Error

**Problem:** Invalid credentials

**Solutions:**
1. **Twitch:** Verify client ID and secret from [developer console](https://dev.twitch.tv/console/apps)
2. **YouTube:** Check API key from [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
3. **Mastodon:** Regenerate access token in instance settings
4. **Discord:** Verify webhook URL is correct and webhook wasn't deleted

### "Stream not detected" Error

**Problem:** Can't find your stream

**Solutions:**
1. **Check username:** Exact match required (case-sensitive on some platforms)
2. **Verify you're live:** Actually start streaming to test
3. **Lower check interval:** Set `SETTINGS_CHECK_INTERVAL=1` for faster detection (1 minute)
4. **Check permissions:** API keys need read access to stream status

### "No announcements posting" Error

**Problem:** Daemon running but not posting

**Solutions:**
1. **Check platform enabled:** `MASTODON_ENABLE=True` not `MASTODON_ENABLE_POSTING=True`
2. **Verify credentials:** Run platform-specific test
3. **Check logs:** Look for errors in output
4. **Test manually:** Try posting directly to platform to verify credentials

### Doppler "Secret not found" Error

**Problem:** Can't fetch secrets from Doppler

**Solutions:**
1. **Verify token:** Check `DOPPLER_TOKEN` starts with `dp.st.`
2. **Check environment:** Token for `dev` can't access `prd` secrets
3. **Verify secret names:** Must match configured prefix (e.g., `TWITCH_CLIENT_ID`)
4. **Test connection:**
   ```bash
   python3 -c "from doppler_sdk import DopplerSDK; \
     sdk = DopplerSDK(); \
     sdk.set_access_token('YOUR_TOKEN'); \
     print(sdk.secrets.list())"
   ```

**Still stuck?** 
- 📖 See [detailed troubleshooting](../configuration/secrets.md#troubleshooting)
- 🐛 [Open an issue](https://github.com/ChiefGyk3D/Stream-Daemon/issues)
- 💬 [Ask in discussions](https://github.com/ChiefGyk3D/Stream-Daemon/discussions)

---

## ⚙️ Advanced Configuration

### Running as a Service (Linux)

Create systemd service for automatic startup:

```bash
# Create service file
sudo nano /etc/systemd/system/stream-daemon.service
```

```ini
[Unit]
Description=Stream Daemon - Multi-platform stream announcements
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/Stream-Daemon
Environment="PATH=/usr/bin:/usr/local/bin"
ExecStart=/usr/bin/python3 /path/to/Stream-Daemon/stream-daemon.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable stream-daemon
sudo systemctl start stream-daemon

# Check status
sudo systemctl status stream-daemon

# View logs
sudo journalctl -u stream-daemon -f
```

### Custom Check Intervals

Different intervals for different states:

```bash
# Check every 5 minutes when offline
SETTINGS_CHECK_INTERVAL=5

# Check every 1 minute when live (detect stream end faster)
SETTINGS_POST_INTERVAL=1

# Update Discord embeds every 30 seconds (viewer counts)
DISCORD_UPDATE_INTERVAL=30
```

### Multiple Discord Webhooks

Different webhooks for each streaming platform:

```bash
# Default webhook
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/default/xxx

# Platform-specific webhooks (override default)
DISCORD_WEBHOOK_TWITCH=https://discord.com/api/webhooks/twitch/xxx
DISCORD_WEBHOOK_YOUTUBE=https://discord.com/api/webhooks/youtube/xxx
DISCORD_WEBHOOK_KICK=https://discord.com/api/webhooks/kick/xxx

# Platform-specific roles
DISCORD_ROLE_TWITCH=@Twitch Viewers
DISCORD_ROLE_YOUTUBE=@YouTube Subscribers
DISCORD_ROLE_KICK=@everyone
```

**See:** [Discord Setup Guide](../platforms/social/discord.md) for advanced Discord configuration.

---

## 📚 Next Steps

Now that Stream Daemon is running:

### Learn More

- **[Platform Setup Guides](../platforms/)** - Detailed setup for all 7 platforms
- **[AI Messages](../features/ai-messages.md)** - Generate unique announcements with Gemini
- **[Custom Messages](../features/custom-messages.md)** - Advanced message templating
- **[Multi-Platform Strategies](../features/multi-platform.md)** - Stream to multiple platforms
- **[Secrets Management](../configuration/secrets.md)** - Secure credential storage with Doppler/AWS/Vault

### Get Involved

- ⭐ **[Star the repo](https://github.com/ChiefGyk3D/Stream-Daemon)** - Support the project!
- 🐛 **[Report issues](https://github.com/ChiefGyk3D/Stream-Daemon/issues)** - Found a bug?
- 💡 **[Suggest features](https://github.com/ChiefGyk3D/Stream-Daemon/discussions)** - Have an idea?
- 🔧 **[Contribute](../../README.md#contributing)** - Submit a pull request!

---

## 💬 Need Help?

- 📖 **Documentation:** [docs/README.md](../README.md)
- 🐛 **Bug Reports:** [GitHub Issues](https://github.com/ChiefGyk3D/Stream-Daemon/issues)
- 💬 **Questions:** [GitHub Discussions](https://github.com/ChiefGyk3D/Stream-Daemon/discussions)

**Happy streaming!** 🎉
