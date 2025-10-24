<div align="center">

![Stream Daemon Banner](media/stream_daemon_banner.png)

# Stream Daemon

**Automate your streams across Twitch, YouTube, Kick, Mastodon, Bluesky, and Discord**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MPL 2.0](https://img.shields.io/badge/License-MPL%202.0-brightgreen.svg)](https://www.mozilla.org/en-US/MPL/2.0/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Monitor multiple streaming platforms and automatically post to your social media when you go live!

[Features](#-features) • [Quick Start](#-quick-start) • [Configuration](#-configuration) • [Documentation](#-documentation) • [Contributing](#-contributing)

</div>

---

## 🎯 What is Stream Daemon?

Stream Daemon is a powerful, open-source automation tool that monitors your live streams across **Twitch, YouTube, and Kick**, and automatically posts announcements to your social media platforms including **Mastodon, Bluesky, and Discord** when you go live or end your stream.

**Perfect for streamers who want to:**
- 📢 Automatically notify followers when going live
- 🌐 Post to multiple social platforms simultaneously
- ✨ Customize messages per platform
- 🔒 Keep credentials secure with secrets managers
- 🐳 Deploy easily with Docker
- ⚡ Run efficiently on any platform (Raspberry Pi, VPS, Cloud)

---

## ✨ Features

### 🎥 Multi-Platform Streaming Support
- **Twitch** - Full API integration with async support
- **YouTube Live** - Auto-resolves channel from @handle
- **Kick** - OAuth authentication with automatic fallback

### 📱 Social Media Integration
- **Mastodon** - Post to any Mastodon instance
- **Bluesky** - Native Bluesky protocol support
- **Discord** - Webhook support with role mentions

### 🔐 Enterprise-Grade Security
- **AWS Secrets Manager** - Store credentials in AWS
- **HashiCorp Vault** - Vault integration for secrets
- **Doppler** - Modern secrets management platform
- Environment variable fallback for all platforms

### 🎨 Customization
- **Platform-specific messages** - Different messages per platform
- **Message templates** - Use variables like stream title, viewers, URLs
- **Multi-platform strategies** - Control how announcements are posted when streaming to multiple platforms
  - Separate posts per platform or combined announcements
  - Thread announcements together or keep them independent
  - Wait for all platforms to end or post individually
- **Flexible scheduling** - Configurable check intervals
- **Clickable URLs** - Auto-generated stream links

### 🐳 Deployment Options
- **Docker** - Production-ready container
- **Docker Compose** - Multi-container orchestration
- **Systemd** - Native Linux service
- **Bare Metal** - Direct Python execution
- **Cloud** - AWS Lambda, Google Cloud Run, etc.

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- API credentials for your streaming platforms
- Social media platform credentials (Mastodon/Bluesky/Discord)
- (Optional) Doppler, AWS, or Vault account for secrets management

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/ChiefGyk3D/twitch-and-toot.git
   cd twitch-and-toot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   nano .env
   ```

4. **Configure message templates** (optional)
   ```bash
   # Edit messages.txt and end_messages.txt
   # Use [DEFAULT], [TWITCH], [YOUTUBE], [KICK] sections
   nano messages.txt
   ```

5. **Run the daemon**
   ```bash
   python3 stream-daemon.py
   ```

### Docker Quick Start

```bash
# Build and run with Docker Compose
cd Docker
docker-compose up -d

# View logs
docker-compose logs -f
```

---

## ⚙️ Configuration

Stream Daemon uses **pure environment variables** for configuration - no config files needed! This makes it perfect for Docker, Kubernetes, and cloud deployments.

### Basic Configuration

```bash
# Streaming Platforms
TWITCH_ENABLE=True
TWITCH_USERNAME=your_username
# Credentials via Doppler/Vault/AWS or direct:
TWITCH_CLIENT_ID=your_client_id
TWITCH_CLIENT_SECRET=your_client_secret

YOUTUBE_ENABLE=True
YOUTUBE_USERNAME=@YourHandle
# Channel ID is optional - auto-resolves from username!

KICK_ENABLE=True
KICK_USERNAME=your_username
# Optional authentication for better rate limits
```

### Social Media Platforms

```bash
# Mastodon
MASTODON_ENABLE=True
MASTODON_INSTANCE_URL=https://mastodon.social
MASTODON_ACCESS_TOKEN=your_token

# Bluesky
BLUESKY_ENABLE=True
BLUESKY_HANDLE=your.handle.bsky.social
BLUESKY_APP_PASSWORD=your_app_password

# Discord
DISCORD_ENABLE=True
DISCORD_WEBHOOK_URL=your_webhook_url
DISCORD_ROLE_TWITCH=@everyone  # Role to mention for Twitch
```

### Secrets Management (Recommended)

```bash
# Use Doppler (recommended)
SECRETS_SECRET_MANAGER=doppler
DOPPLER_TOKEN=your_doppler_token  # Get from Doppler dashboard (env-specific)
DOPPLER_CONFIG=dev  # Doppler environment: dev, stg, or prd
SECRETS_DOPPLER_TWITCH_SECRET_NAME=twitch
SECRETS_DOPPLER_YOUTUBE_SECRET_NAME=youtube

# Or AWS Secrets Manager
SECRETS_SECRET_MANAGER=aws
SECRETS_AWS_TWITCH_SECRET_NAME=prod/stream-daemon/twitch

# Or HashiCorp Vault
SECRETS_SECRET_MANAGER=vault
SECRETS_VAULT_URL=https://vault.example.com
SECRETS_VAULT_TOKEN=your_vault_token
```

**📌 Doppler Note:** Doppler tokens are environment-specific. A `dev` token only accesses `dev` secrets. See [DOPPLER_GUIDE.md](DOPPLER_GUIDE.md) for complete setup.

### Message Customization

Edit `messages.txt` and `end_messages.txt` with INI-style sections:

```ini
[DEFAULT]
🔴 I'm live! Come watch: {url}

[TWITCH]
🎮 Live on Twitch! Playing {title}
Watch: {url}

[YOUTUBE]
📺 Streaming now on YouTube!
{url}

[KICK]
⚡ Live on Kick! {url}
```

**Toggle behavior:**
```bash
# Use platform-specific messages if available, fall back to DEFAULT
MESSAGES_USE_PLATFORM_SPECIFIC_MESSAGES=True

# Only use DEFAULT section for all platforms
MESSAGES_USE_PLATFORM_SPECIFIC_MESSAGES=False
```

---

## 📚 Documentation

### Core Documentation
- [Platform Guide](PLATFORM_GUIDE.md) - Detailed platform setup guides
- [Doppler Guide](DOPPLER_GUIDE.md) - Secrets management with Doppler
- [Messages Format](MESSAGES_FORMAT.md) - Message customization guide
- [Multi-Platform Examples](MULTI_PLATFORM_EXAMPLES.md) - **NEW!** Multi-streaming posting strategies
- [Migration Guide](MIGRATION.md) - Upgrading from v1 to v2

### Test Suite Documentation
- [Test Suite Overview](tests/README.md) - Running the test suite
- [Doppler Secrets Guide](tests/DOPPLER_SECRETS.md) - Secret naming conventions
- [Quick Reference](tests/QUICK_REFERENCE.md) - Commands cheat sheet
- [Kick Auth Guide](tests/KICK_AUTH_GUIDE.md) - Kick API authentication

### Docker Documentation
- [Docker Setup](Docker/README.md) - Running in Docker
- [Docker Compose](Docker/docker-compose.yml) - Multi-container setup

---

## 🧪 Testing

Stream Daemon includes a comprehensive test suite to validate your configuration:

```bash
# Test all platforms
python3 tests/test_doppler_all.py

# Test individual platforms
python3 tests/test_doppler_twitch.py
python3 tests/test_doppler_youtube.py
python3 tests/test_doppler_kick.py

# Or use the test runner
./run_tests.sh all
./run_tests.sh twitch
```

**Tests validate:**
- ✅ Secret fetching from Doppler/AWS/Vault
- ✅ API authentication for each platform
- ✅ Stream detection functionality
- ✅ Credential security (all secrets are masked)

---

## 🏗️ Architecture

```
stream-daemon.py          # Main daemon application
├── Streaming Platforms   # Monitor live streams
│   ├── TwitchPlatform   # Twitch API (async)
│   ├── YouTubePlatform  # YouTube Data API v3
│   └── KickPlatform     # Kick OAuth + fallback
├── Social Platforms     # Post announcements
│   ├── MastodonPlatform # Mastodon API
│   ├── BlueskyPlatform  # AT Protocol
│   └── DiscordPlatform  # Webhook API
└── Secrets Management   # Secure credentials
    ├── Doppler SDK
    ├── AWS Secrets Manager
    └── HashiCorp Vault
```

**Flow:**
1. Daemon checks configured streaming platforms every `CHECK_INTERVAL` (default: 5min)
2. Detects when stream goes live or ends
3. Posts to all enabled social platforms once (not repeatedly!)
4. While live: continues checking every `POST_INTERVAL` minutes to detect when stream ends
5. When offline: checks every `CHECK_INTERVAL` minutes to detect when you go live

**Note:** Stream Daemon only posts when state **changes** (offline→live or live→offline). It won't spam your followers with posts every check cycle.

---

## 🔧 Advanced Configuration

### Intervals

```bash
# How often to check when OFFLINE (minutes)
SETTINGS_CHECK_INTERVAL=5

# How often to check when LIVE (minutes)
# Should be same or lower than CHECK_INTERVAL for fast stream-end detection
SETTINGS_POST_INTERVAL=5
```

### Message Files

```bash
MESSAGES_MESSAGES_FILE=messages.txt          # Live stream messages
MESSAGES_END_MESSAGES_FILE=end_messages.txt  # Stream ended messages
```

### Multi-Platform Posting Strategies

When streaming to multiple platforms simultaneously (e.g., Twitch + YouTube + Kick), you can control how announcements are posted:

#### Live Stream Announcements

```bash
# MESSAGES_LIVE_THREADING_MODE controls "going live" posts
# Options: separate | thread | combined

# SEPARATE (default): Each platform gets its own standalone post
#   Example: "Live on Twitch!" then "Live on YouTube!" as separate posts
MESSAGES_LIVE_THREADING_MODE=separate

# THREAD: Each platform announcement is threaded to the previous one
#   Example: "Live on Twitch!" → "Also live on YouTube!" as a reply
MESSAGES_LIVE_THREADING_MODE=thread

# COMBINED: Single post announcing all platforms at once
#   Example: "Live on Twitch, YouTube, and Kick!"
MESSAGES_LIVE_THREADING_MODE=combined
```

#### Stream Ended Announcements

```bash
# MESSAGES_END_THREADING_MODE controls "stream ended" posts
# Options: disabled | separate | thread | combined | single_when_all_end

# DISABLED: Don't post any stream end messages
MESSAGES_END_THREADING_MODE=disabled

# SEPARATE: Each platform end gets its own post (no threading)
#   Example: "Twitch stream ended!" "YouTube stream ended!"
MESSAGES_END_THREADING_MODE=separate

# THREAD (default): Reply to each platform's live announcement
#   Example: "Live on Twitch!" → "Stream ended, thanks!"
MESSAGES_END_THREADING_MODE=thread

# COMBINED: Single post when each platform ends
#   Example: "Twitch and YouTube streams ended!"
MESSAGES_END_THREADING_MODE=combined

# SINGLE_WHEN_ALL_END: Wait until ALL platforms have ended
#   Perfect for handling platform failures gracefully
#   Example: If streaming to 3 platforms, waits until all 3 
#   are offline before posting one final "All streams ended!"
MESSAGES_END_THREADING_MODE=single_when_all_end
```

**Use Case Example:** You're streaming to Twitch, YouTube, and Kick. Twitch crashes mid-stream but YouTube and Kick continue. With `single_when_all_end`, the daemon won't post "stream ended" until YouTube and Kick also finish, giving you one clean end message instead of confusing partial announcements.

### Discord Role Mentions

```bash
DISCORD_ROLE_TWITCH=@Twitch Viewers
DISCORD_ROLE_YOUTUBE=@YouTube Subscribers
DISCORD_ROLE_KICK=@everyone
```

---

## 🐳 Docker Deployment

### Using Docker Compose (Recommended)

```yaml
version: '3.8'
services:
  stream-daemon:
    build: .
    environment:
      - DOPPLER_TOKEN=${DOPPLER_TOKEN}
      - TWITCH_ENABLE=True
      - TWITCH_USERNAME=your_username
      # ... other config
    volumes:
      - ./messages.txt:/app/messages.txt
      - ./end_messages.txt:/app/end_messages.txt
    restart: unless-stopped
```

```bash
cd Docker
docker-compose up -d
```

### Manual Docker Build

```bash
docker build -t stream-daemon .
docker run -d \
  --name stream-daemon \
  --env-file .env \
  -v $(pwd)/messages.txt:/app/messages.txt \
  stream-daemon
```

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Report Bugs** - Open an issue with details and reproduction steps
2. **Suggest Features** - Share your ideas for improvements
3. **Submit PRs** - Fix bugs or add features
4. **Improve Docs** - Help make documentation clearer
5. **Test** - Try it on different platforms and report issues

### Development Setup

```bash
# Clone and setup
git clone https://github.com/ChiefGyk3D/twitch-and-toot.git
cd twitch-and-toot

# Install dev dependencies
pip install -r requirements.txt

# Configure Doppler for testing
cp .env.example .env
# Add your test credentials

# Run tests
./run_tests.sh all
```

---

## 📋 Roadmap

### Coming Soon
- [ ] **Discord Support** - Post to Discord Channels
- [ ] **Matrix Support** - Post to Matrix rooms
- [ ] **LLM Integration** - AI-generated stream announcements
- [ ] **Systemd Service Files** - Easy Linux service setup

### Under Consideration
- **Web Dashboard** - Configure and monitor via web UI
- **Webhooks** - Trigger custom actions on stream events
- **Analytics** - Track stream performance across platforms

Want to see a feature? [Open an issue](https://github.com/ChiefGyk3D/twitch-and-toot/issues)!

---

## ⚠️ Known Limitations

### Link Preview Cards
- **Kick.com** - Due to CloudFlare security policies, Kick blocks automated requests for metadata scraping. 
  - Kick URLs will still be **clickable links** in posts
  - Rich preview cards (with thumbnails) are **not available** for Kick streams on Bluesky
  - Mastodon may or may not show Kick preview cards (depends on whether Kick blocks Mastodon's servers)
  - **Twitch and YouTube** work perfectly with full preview cards and thumbnails

---

## 📄 License

Stream Daemon is available under a dual-license model:

- **Open Source License:** Mozilla Public License 2.0 (MPL 2.0)
- **Commercial License:** Available for organizations that cannot comply with MPL 2.0 terms.

For commercial licensing inquiries, please contact:

See [LICENSE.md](LICENSE.md) for details.

---

## 🙏 Acknowledgments

- Built with [twitchAPI](https://github.com/Teekeks/pyTwitchAPI)
- Powered by [Doppler](https://www.doppler.com/) for secrets management
- Inspired by the open-source streaming community

---

## 💬 Support

- **Issues**: [GitHub Issues](https://github.com/ChiefGyk3D/twitch-and-toot/issues)
- **Discussions**: [GitHub Discussions](https://github.com/ChiefGyk3D/twitch-and-toot/discussions)
- **Documentation**: See the [docs folder](#-documentation)

---

## 💝 Donations and Tips

If you find Stream Daemon useful, consider supporting development:

**Donate**: [links.chiefgyk3d.com](https://links.chiefgyk3d.com)

**Cryptocurrency**:
- Bitcoin: `bc1q5grpa7ramcct4kjmwexfrh74dvjuw9wczn4w2f`
- Monero: `85YxVz8Xd7sW1xSiyzUC5PNqSjYLYk4W8FMERVkvznR38jGTBEViWQSLCnzRYZjmxgUkUKGhxTt2JSFNpJuAqghQLhHgPS5`
- PIVX: `DS1CuBQkiidwwPhkfVfQAGUw4RTWPnBXVM`
- Ethereum: `0x2a460d48ab404f191b14e9e0df05ee829cbf3733`

---

<div align="center">

Made with ❤️ by [ChiefGyk3D](https://github.com/ChiefGyk3D)

**If Stream Daemon helps you, consider ⭐ starring the repo!**

</div>
