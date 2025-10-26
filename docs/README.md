# Stream Daemon Documentation

> **📚 Complete guides for Stream Daemon - multi-platform stream announcement automation**

Welcome to the Stream Daemon documentation! This directory contains comprehensive guides for setting up, configuring, and using Stream Daemon.

---

## 🚀 Getting Started

**New to Stream Daemon?** Start here:

- **[Quickstart Guide](getting-started/quickstart.md)** - Get up and running in 10 minutes
- **[Installation Guide](getting-started/installation.md)** - Detailed installation for all platforms (Python, Docker, systemd, cloud)

---

## 🎮 Streaming Platform Setup

Configure Stream Daemon to monitor your live streams:

### Supported Platforms

- **[Twitch](platforms/streaming/twitch.md)** - OAuth 2.0 setup, client ID/secret, rate limits, troubleshooting
- **[YouTube Live](platforms/streaming/youtube.md)** - API key, channel ID resolution, quota management
- **[Kick](platforms/streaming/kick.md)** - OAuth authentication, 2FA requirements, public API fallback

---

## 📱 Social Media Platform Setup

Configure where Stream Daemon posts your announcements:

### Supported Platforms

- **[Mastodon](platforms/social/mastodon.md)** - Instance setup, access tokens, app creation, custom instances
- **[Bluesky](platforms/social/bluesky.md)** - App passwords, handle configuration, AT Protocol
- **[Discord](platforms/social/discord.md)** - Webhooks, rich embeds, role mentions, live updates, stream ended messages
- **[Matrix](platforms/social/matrix.md)** - Bot creation, room setup, authentication methods (token/password)

---

## ⚙️ Configuration

### Core Configuration

- **[Secrets Wizard](configuration/secrets-wizard.md)** 🪄 **NEW!** - Interactive setup tool
  - Step-by-step credential configuration
  - Supports Doppler, AWS, Vault, and .env files
  - Loads existing values as defaults
  - Platform-specific guidance with credential links
- **[Secrets Management](configuration/secrets.md)** ⭐ **RECOMMENDED** - Secure your credentials
  - Doppler setup (free, 10-minute setup, recommended)
  - AWS Secrets Manager (for AWS-heavy infrastructure)
  - HashiCorp Vault (for enterprise/self-hosted)
  - Priority system and best practices
  - Docker integration

---

## ✨ Features

Enhance your stream announcements with powerful features:

- **[AI-Powered Messages](features/ai-messages.md)** 🤖 **NEW!** - Google Gemini LLM integration
  - Generate unique announcements for every stream
  - Platform-aware character limits
  - Cost-effective (~ $0.0001 per message)
  - Automatic fallback to static messages
  
- **[Custom Messages](features/custom-messages.md)** - Personalize announcements
  - Platform-specific templates (Twitch, YouTube, Kick)
  - Variables: `{url}`, `{title}`, `{game}`, `{viewers}`
  - INI-style configuration
  - Migration from old format

- **[Multi-Platform Streaming](features/multi-platform.md)** - Stream to multiple platforms simultaneously
  - Threading modes: separate, thread, combined
  - "Stream ended" strategies
  - Handle platform failures gracefully
  - Examples and scenarios

---

## 🔄 Migration

Upgrading from an older version?

- **[v1 to v2 Migration](migration/v1-to-v2.md)** - Breaking changes, new features, configuration updates

---

## 📖 Platform-Specific Guides

### By Category

**Streaming Platforms:**
- [Twitch](platforms/streaming/twitch.md) - Most popular streaming platform
- [YouTube Live](platforms/streaming/youtube.md) - Google's streaming service  
- [Kick](platforms/streaming/kick.md) - New competitor to Twitch

**Social Media:**
- [Mastodon](platforms/social/mastodon.md) - Federated microblogging
- [Bluesky](platforms/social/bluesky.md) - Decentralized social network
- [Discord](platforms/social/discord.md) - Chat and community platform
- [Matrix](platforms/social/matrix.md) - Decentralized messaging

---

## 🎯 Common Tasks

### First-Time Setup

1. **[Install Stream Daemon](getting-started/installation.md)** - Choose Python, Docker, or cloud deployment
2. **[Get API Credentials](platforms/)** - Follow platform-specific guides
3. **[Configure Secrets](configuration/secrets.md)** - Use Doppler for secure credential storage (recommended)
4. **[Test Setup](getting-started/quickstart.md#testing-your-setup)** - Verify everything works
5. **[Customize Messages](features/custom-messages.md)** - Make announcements your own

### Advanced Configuration

- **[Set up AI Messages](features/ai-messages.md)** - Use Gemini for dynamic announcements
- **[Multi-Platform Streaming](features/multi-platform.md)** - Configure for simultaneous streaming
- **[Discord Live Updates](platforms/social/discord.md#live-embed-updates)** - Real-time viewer counts
- **[Production Deployment](getting-started/installation.md#systemd-service-linux)** - Systemd service, Docker, cloud

---

## 🔍 Quick Reference

### Configuration Files

| File | Purpose | Required |
|------|---------|----------|
| `.env` | Main configuration and credentials | ✅ Yes |
| `messages.txt` | Live stream announcement templates | ⚠️ Optional |
| `end_messages.txt` | Stream ended announcement templates | ⚠️ Optional |
| `docker-compose.yml` | Docker deployment configuration | Only for Docker |

### Environment Variables

**Essential:**
```bash
# Enable platforms
TWITCH_ENABLE=True
MASTODON_ENABLE=True

# Platform credentials (or use secrets manager)
TWITCH_CLIENT_ID=xxx
MASTODON_ACCESS_TOKEN=yyy

# Check intervals
SETTINGS_CHECK_INTERVAL=5  # Minutes when offline
SETTINGS_POST_INTERVAL=5   # Minutes when live
```

**Secrets Management (Recommended):**
```bash
SECRETS_SECRET_MANAGER=doppler
DOPPLER_TOKEN=dp.st.dev.xxx
SECRETS_DOPPLER_TWITCH_SECRET_NAME=TWITCH
```

See [Secrets Management Guide](configuration/secrets.md) for complete setup.

### Command Reference

```bash
# Run Stream Daemon
python3 stream-daemon.py

# Run with Doppler
doppler run -- python3 stream-daemon.py

# Run in Docker
docker-compose up -d

# Test configuration
python3 tests/test_doppler_all.py

# Test specific platform
python3 tests/test_doppler_twitch.py

# View logs (systemd)
sudo journalctl -u stream-daemon -f

# View logs (Docker)
docker-compose logs -f stream-daemon
```

---

## 🆘 Troubleshooting

### Common Issues

**Stream not detected:**
1. Verify username is correct (case-sensitive)
2. Check API credentials are valid
3. Ensure platform is enabled (`TWITCH_ENABLE=True`)
4. Lower check interval for faster detection

**Announcements not posting:**
1. Test social platform authentication
2. Verify webhooks/tokens are correct
3. Check platform is enabled
4. Review logs for errors

**Doppler secrets not working:**
1. Verify token is correct (`dp.st.dev.xxx`)
2. Check secret names match configured prefix
3. Ensure environment matches token (dev token = dev secrets)
4. Comment out credentials in `.env` (they override Doppler)

**See:** [Quickstart Troubleshooting](getting-started/quickstart.md#troubleshooting) for detailed solutions.

---

## 🏗️ Architecture

Stream Daemon uses a modular architecture:

```
stream_daemon/
├── platforms/
│   ├── streaming/          # Monitor live streams
│   │   ├── twitch.py
│   │   ├── youtube.py
│   │   └── kick.py
│   └── social/             # Post announcements
│       ├── mastodon.py
│       ├── bluesky.py
│       ├── discord.py
│       └── matrix.py
├── secrets/                # Secrets management
│   ├── doppler.py
│   ├── aws.py
│   └── vault.py
└── utils/
    ├── ai_messages.py      # Gemini LLM integration
    └── message_parser.py   # Template variables
```

**Flow:**
1. Daemon checks streaming platforms every `CHECK_INTERVAL`
2. Detects state changes (offline→live or live→offline)
3. Generates message (AI or template)
4. Posts to all enabled social platforms
5. Continues monitoring for stream end

---

## 📚 External Resources

### Official Documentation

- **[Twitch Developer Docs](https://dev.twitch.tv/docs)** - Twitch API reference
- **[YouTube Data API](https://developers.google.com/youtube/v3)** - YouTube API documentation
- **[Mastodon API](https://docs.joinmastodon.org/api/)** - Mastodon API reference
- **[Bluesky API](https://atproto.com/)** - AT Protocol documentation
- **[Discord Webhooks](https://discord.com/developers/docs/resources/webhook)** - Discord webhook guide
- **[Matrix Client-Server API](https://matrix.org/docs/spec/)** - Matrix API spec

### Secrets Management

- **[Doppler Documentation](https://docs.doppler.com/)** - Doppler setup and CLI
- **[AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/)** - AWS secrets guide
- **[HashiCorp Vault](https://www.vaultproject.io/docs)** - Vault documentation

### AI Integration

- **[Google AI Studio](https://aistudio.google.com/)** - Get Gemini API key
- **[Gemini API Docs](https://ai.google.dev/docs)** - Gemini API reference

---

## 🤝 Contributing

Want to improve Stream Daemon or its documentation?

### How to Contribute

1. **Documentation improvements:**
   - Fix typos or unclear sections
   - Add examples or troubleshooting tips
   - Translate guides to other languages

2. **Code contributions:**
   - Add new platform integrations
   - Improve existing features
   - Fix bugs

3. **Community support:**
   - Answer questions in [Discussions](https://github.com/ChiefGyk3D/Stream-Daemon/discussions)
   - Share your Stream Daemon setup
   - Report bugs and suggest features

See [Development Setup](getting-started/installation.md#development-setup) to get started.

---

## 📞 Support

### Getting Help

- 📖 **Search this documentation** - Most answers are here!
- 🔍 **[Search existing issues](https://github.com/ChiefGyk3D/Stream-Daemon/issues)** - Your question may be answered
- 💬 **[GitHub Discussions](https://github.com/ChiefGyk3D/Stream-Daemon/discussions)** - Ask questions, share setups
- 🐛 **[GitHub Issues](https://github.com/ChiefGyk3D/Stream-Daemon/issues)** - Report bugs, request features

### Before Asking

Include this information for faster help:

- **Stream Daemon version** - Check `stream-daemon.py` header
- **Python version** - Run `python3 --version`
- **OS and platform** - e.g., "Ubuntu 22.04", "macOS 13", "Docker"
- **Configuration** - Enabled platforms (no credentials!)
- **Error messages** - Full error output (secrets are auto-masked)
- **What you tried** - Steps to reproduce the issue

**Example:**
```
**Version:** Stream Daemon v2.0.0
**Python:** 3.11.4
**OS:** Ubuntu 22.04 LTS
**Platforms:** Twitch + YouTube → Mastodon + Discord
**Secrets:** Doppler (dev environment)

**Error:**
```
ERROR: Failed to post to Mastodon: 401 Unauthorized
```

**Steps:**
1. Configured Mastodon with access token from instance settings
2. Token visible in Doppler dashboard
3. Test script succeeds, but daemon fails
```

---

## ⭐ Show Your Support

If Stream Daemon helps you grow your streaming presence:

- ⭐ **[Star the repository](https://github.com/ChiefGyk3D/Stream-Daemon)** - Help others discover it!
- 📢 **Share with streamers** - Spread the word on social media
- 💝 **[Donate](https://links.chiefgyk3d.com)** - Support ongoing development
- 🔧 **Contribute** - Submit pull requests and improvements

---

<div align="center">

Made with ❤️ by [ChiefGyk3D](https://github.com/ChiefGyk3D)

**Stream Daemon** - Automate your multi-platform streaming presence

[⬆ Back to Top](#stream-daemon-documentation) • [Main README](../README.md)

</div>
