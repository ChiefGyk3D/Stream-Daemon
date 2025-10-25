# Migration Guide: v1.x to Stream Daemon v2.x

> **Note:** This guide is for users upgrading from the old **twitch-and-toot v1.x** (using `config.ini`) to **Stream Daemon v2.x** (using `.env`). If you're a new user, skip this and follow the main [README.md](README.md) setup guide.

## Overview

Stream Daemon v2.x has moved from `config.ini` to `.env` files for configuration. This provides better security, easier Docker/container deployment, and integration with modern secrets management platforms.

**Major Changes:**
- ❌ `config.ini` → ✅ `.env` environment variables
- ❌ Old script name → ✅ `stream-daemon.py`
- ✅ Added YouTube Live support
- ✅ Added Kick support
- ✅ Added Discord webhook support
- ✅ Improved Doppler secrets management

## Why This Change?

1. **Better Security**: Secrets can now be managed by AWS Secrets Manager, HashiCorp Vault, or Doppler
2. **Container Native**: Environment variables are the standard for Docker/Kubernetes
3. **Simpler**: No more dual config.ini + environment variable system
4. **Industry Standard**: `.env` files are the de facto standard for 12-factor apps

## Quick Migration

### Step 1: Copy the Template

```bash
cp .env.example .env
```

### Step 2: Convert Your Settings

If you have an old `config.ini` file, here's how to convert each section:

#### Old config.ini Format:
```ini
[Twitch]
enable = True
username = YourUsername
client_id = abc123
client_secret = xyz789
```

#### New .env Format:
```bash
TWITCH_ENABLE=True
TWITCH_USERNAME=YourUsername
TWITCH_CLIENT_ID=abc123
TWITCH_CLIENT_SECRET=xyz789
```

### Conversion Pattern:
- Section names become prefixes: `[Twitch]` → `TWITCH_`
- Keys become UPPERCASE: `client_id` → `CLIENT_ID`
- Combine them: `TWITCH_CLIENT_ID`

## Platform-Specific Examples

### Twitch
```bash
# Old: [Twitch] section
TWITCH_ENABLE=True
TWITCH_USERNAME=your_username
TWITCH_CLIENT_ID=your_client_id
TWITCH_CLIENT_SECRET=your_client_secret
```

### YouTube Live
```bash
# Old: [YouTube] section
YOUTUBE_ENABLE=True
YOUTUBE_CHANNEL_ID=your_channel_id
YOUTUBE_API_KEY=your_api_key
```

### Kick
```bash
# Old: [Kick] section
KICK_ENABLE=True
KICK_USERNAME=your_username
```

### Mastodon
```bash
# Old: [Mastodon] section
MASTODON_ENABLE_POSTING=True
MASTODON_APP_NAME=StreamDaemon
MASTODON_API_BASE_URL=https://mastodon.social
MASTODON_CLIENT_ID=your_client_id
MASTODON_CLIENT_SECRET=your_client_secret
MASTODON_ACCESS_TOKEN=your_access_token
```

### Bluesky
```bash
# Old: [Bluesky] section
BLUESKY_ENABLE_POSTING=True
BLUESKY_HANDLE=yourname.bsky.social
BLUESKY_APP_PASSWORD=your_app_password
```

### Discord
```bash
# Old: [Discord] section
DISCORD_ENABLE_POSTING=True
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK
```

### Messages
```bash
# Old: [Messages] section
MESSAGES_MESSAGES_FILE=messages.txt
MESSAGES_END_MESSAGES_FILE=end_messages.txt
MESSAGES_POST_END_STREAM_MESSAGE=True
```

### Settings
```bash
# Old: [Settings] section
SETTINGS_POST_INTERVAL=1
SETTINGS_CHECK_INTERVAL=5
```

## Using Secrets Managers (Recommended for Production)

Instead of putting sensitive credentials directly in `.env`, you can use a secrets manager:

### Option 1: AWS Secrets Manager

```bash
SECRETS_SECRET_MANAGER=aws

# Create secrets in AWS with these names:
SECRETS_AWS_TWITCH_SECRET_NAME=twitch-api-keys
SECRETS_AWS_MASTODON_SECRET_NAME=mastodon-api-keys
# etc...
```

The AWS secret should be JSON:
```json
{
  "client_id": "your_client_id",
  "client_secret": "your_client_secret"
}
```

### Option 2: HashiCorp Vault

```bash
SECRETS_SECRET_MANAGER=vault
SECRETS_VAULT_URL=https://vault.example.com
SECRETS_VAULT_TOKEN=your_vault_token
SECRETS_VAULT_TWITCH_SECRET_PATH=secret/twitch
```

### Option 3: Doppler

```bash
SECRETS_SECRET_MANAGER=doppler
DOPPLER_TOKEN=dp.st.your_token_here
```

Doppler automatically injects all secrets as environment variables.

## Priority Order

Credentials are loaded in this order (highest priority first):

1. **Direct environment variables** (e.g., `TWITCH_CLIENT_ID=...`)
2. **Secrets manager** (AWS/Vault/Doppler)
3. **Not found** (authentication will fail for that platform)

This means you can:
- Use secrets managers for production
- Override specific values with env vars for testing
- Mix and match approaches per platform

## Docker Users

Update your `docker-compose.yml` environment section using the same format:

```yaml
environment:
  TWITCH_ENABLE: 'True'
  TWITCH_USERNAME: your_username
  TWITCH_CLIENT_ID: your_client_id
  TWITCH_CLIENT_SECRET: your_client_secret
```

Or use an `.env` file with Docker Compose:

```yaml
env_file:
  - .env
```

## Troubleshooting

### "Authentication failed" errors

Check that your environment variables are set correctly:

```bash
# Verify .env file is loaded
cat .env | grep TWITCH

# Check if variables are in environment
echo $TWITCH_CLIENT_ID
```

### "No platforms enabled" error

Make sure at least one streaming and one social platform is enabled:

```bash
TWITCH_ENABLE=True          # At least one of: Twitch, YouTube, Kick
MASTODON_ENABLE_POSTING=True  # At least one of: Mastodon, Bluesky, Discord
```

### Secrets manager not working

1. Verify `SECRETS_SECRET_MANAGER` is set to `aws`, `vault`, or `doppler`
2. Check credentials for the secrets manager itself
3. Verify secret names/paths are correct
4. Check logs for specific error messages

## Need Help?

- Check `.env.example` for complete examples
- See `DOPPLER_GUIDE.md` for Doppler setup
- Review logs for specific error messages
- Open an issue on GitHub

---

**Note**: After migrating, you can safely delete any old `config.ini` files. They are no longer used.
