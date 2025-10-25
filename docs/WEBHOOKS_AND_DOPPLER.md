# Complete Webhook & Doppler Setup Guide

## Overview

This guide covers how to create webhooks and format secrets in Doppler for ALL supported platforms in Stream Daemon.

---

## 🎯 Quick Reference: Webhook vs Token Auth

| Platform | Auth Type | What You Need |
|----------|-----------|---------------|
| **Discord** | Webhook URL | Create webhook in Discord server |
| **Matrix** | Access Token | Generate from Matrix account |
| **Mastodon** | OAuth Tokens | Register app in Mastodon settings |
| **Bluesky** | App Password | Generate from Bluesky settings |
| **Twitch** | OAuth Client | Register app in Twitch Developer Console |
| **YouTube** | API Key | Create in Google Cloud Console |
| **Kick** | OAuth Client (optional) | Register app in Kick Developer Portal |

---

## 📢 Discord Webhooks

### Creating Discord Webhooks

**Per-Server Setup (Recommended for different webhooks per platform):**

1. **Open Discord** → Go to your server
2. **Server Settings** → **Integrations** → **Webhooks**
3. **Create Webhook** for each platform you want:

   **Example: Twitch Webhook**
   - Name: `Twitch Stream Notifications`
   - Channel: `#twitch-streams` (or your choice)
   - Avatar: Upload Twitch logo (optional)
   - **Copy Webhook URL**
   
   **Example: YouTube Webhook**
   - Name: `YouTube Stream Notifications`
   - Channel: `#youtube-streams`
   - Avatar: Upload YouTube logo (optional)
   - **Copy Webhook URL**
   
   **Example: Kick Webhook**
   - Name: `Kick Stream Notifications`
   - Channel: `#kick-streams`
   - Avatar: Upload Kick logo (optional)
   - **Copy Webhook URL**

4. **Default Webhook** (catches all if no platform-specific):
   - Name: `Stream Notifications`
   - Channel: `#live-streams`
   - **Copy Webhook URL**

### Discord Webhook URL Format

```
https://discord.com/api/webhooks/{webhook_id}/{webhook_token}
```

**Example:**
```
https://discord.com/api/webhooks/1234567890/AbCdEfGhIjKlMnOpQrStUvWxYz1234567890
```

### Role Mentions (Optional)

To mention roles when going live:

1. **Server Settings** → **Roles**
2. **Create Role** or select existing:
   - Name: `Twitch Viewers`, `YouTube Subscribers`, etc.
   - Enable **"Allow anyone to @mention this role"**
3. **Right-click role** → **Copy Role ID** (Developer Mode must be enabled)
4. Add role ID to configuration

### Doppler Configuration for Discord

**Doppler Secret Names (when `SECRETS_DOPPLER_DISCORD_SECRET_NAME=DISCORD`):**

```bash
# Default webhook (used if no platform-specific webhook)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/123/abc...

# Platform-specific webhooks (optional)
DISCORD_WEBHOOK_TWITCH=https://discord.com/api/webhooks/456/def...
DISCORD_WEBHOOK_YOUTUBE=https://discord.com/api/webhooks/789/ghi...
DISCORD_WEBHOOK_KICK=https://discord.com/api/webhooks/012/jkl...

# Default role (optional - mention when any stream goes live)
DISCORD_ROLE=1234567890

# Platform-specific roles (optional)
DISCORD_ROLE_TWITCH=1111111111
DISCORD_ROLE_YOUTUBE=2222222222
DISCORD_ROLE_KICK=3333333333
```

**Command to set in Doppler:**
```bash
# Default webhook
doppler secrets set DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/YOUR_WEBHOOK"

# Platform-specific webhooks
doppler secrets set DISCORD_WEBHOOK_TWITCH="https://discord.com/api/webhooks/TWITCH_WEBHOOK"
doppler secrets set DISCORD_WEBHOOK_YOUTUBE="https://discord.com/api/webhooks/YOUTUBE_WEBHOOK"
doppler secrets set DISCORD_WEBHOOK_KICK="https://discord.com/api/webhooks/KICK_WEBHOOK"

# Role IDs (without <>)
doppler secrets set DISCORD_ROLE="1234567890"
doppler secrets set DISCORD_ROLE_TWITCH="1111111111"
doppler secrets set DISCORD_ROLE_YOUTUBE="2222222222"
doppler secrets set DISCORD_ROLE_KICK="3333333333"
```

---

## 🔷 Matrix Access Tokens

### Creating Matrix Access Token

**See [docs/MATRIX_SETUP.md](MATRIX_SETUP.md) for detailed instructions.**

Quick steps:
1. Go to https://app.element.io
2. **Settings** → **Help & About** → **Advanced**
3. Click **"Access Token"** → Reveal
4. **Copy the token**

### Matrix Room ID

1. Open your notification room in Element
2. **Room Settings** → **Advanced**
3. Copy **"Internal room ID"** (format: `!abc123:matrix.org`)

### Doppler Configuration for Matrix

**Doppler Secret Names (when `SECRETS_DOPPLER_MATRIX_SECRET_NAME=MATRIX`):**

```bash
MATRIX_HOMESERVER=https://matrix.org
MATRIX_ACCESS_TOKEN=syt_abc123...
MATRIX_ROOM_ID=!AbCdEfGhIjKl:matrix.org
```

**Command to set in Doppler:**
```bash
doppler secrets set MATRIX_HOMESERVER="https://matrix.org"
doppler secrets set MATRIX_ACCESS_TOKEN="syt_your_token_here"
doppler secrets set MATRIX_ROOM_ID="!YourRoomId:matrix.org"
```

---

## 🐘 Mastodon OAuth Tokens

### Creating Mastodon App

1. **Log into your Mastodon instance** (e.g., mastodon.social)
2. **Preferences** → **Development** → **New Application**
3. Fill in:
   - **Application name:** `Stream Daemon`
   - **Application website:** (optional)
   - **Redirect URI:** `urn:ietf:wg:oauth:2.0:oob` (for command-line apps)
   - **Scopes:** Check `write:statuses` (to post)
4. **Submit**
5. **Copy these values:**
   - Client key (Client ID)
   - Client secret
   - Your access token

### Doppler Configuration for Mastodon

**Doppler Secret Names (when `SECRETS_DOPPLER_MASTODON_SECRET_NAME=MASTODON`):**

```bash
MASTODON_CLIENT_ID=your_client_key_here
MASTODON_CLIENT_SECRET=your_client_secret_here
MASTODON_ACCESS_TOKEN=your_access_token_here
```

**Command to set in Doppler:**
```bash
doppler secrets set MASTODON_CLIENT_ID="your_client_key"
doppler secrets set MASTODON_CLIENT_SECRET="your_client_secret"
doppler secrets set MASTODON_ACCESS_TOKEN="your_access_token"
```

**Note:** API base URL and app name stay in `.env` (not secrets):
```bash
MASTODON_API_BASE_URL=https://mastodon.social
MASTODON_APP_NAME=Stream Daemon
```

---

## 🦋 Bluesky App Password

### Creating Bluesky App Password

1. **Log into Bluesky** at https://bsky.app
2. **Settings** → **Privacy and Security** → **App Passwords**
3. **Add App Password**
4. **Name it:** `Stream Daemon`
5. **Copy the generated password** (shown only once!)

### Doppler Configuration for Bluesky

**Doppler Secret Names (when `SECRETS_DOPPLER_BLUESKY_SECRET_NAME=BLUESKY`):**

```bash
BLUESKY_APP_PASSWORD=your-app-password-here
```

**Command to set in Doppler:**
```bash
doppler secrets set BLUESKY_APP_PASSWORD="your-app-password"
```

**Note:** Handle stays in `.env` (not secret):
```bash
BLUESKY_HANDLE=yourusername.bsky.social
```

---

## 🎮 Twitch OAuth Credentials

### Creating Twitch App

1. Go to https://dev.twitch.tv/console/apps
2. **Register Your Application**
3. Fill in:
   - **Name:** `Stream Daemon`
   - **OAuth Redirect URLs:** `http://localhost` (required but not used)
   - **Category:** Application Integration
4. **Create**
5. **Manage** → Copy **Client ID**
6. **New Secret** → Copy **Client Secret**

### Doppler Configuration for Twitch

**Doppler Secret Names (when `SECRETS_DOPPLER_TWITCH_SECRET_NAME=TWITCH`):**

```bash
TWITCH_CLIENT_ID=your_client_id_here
TWITCH_CLIENT_SECRET=your_client_secret_here
```

**Command to set in Doppler:**
```bash
doppler secrets set TWITCH_CLIENT_ID="your_client_id"
doppler secrets set TWITCH_CLIENT_SECRET="your_client_secret"
```

---

## ▶️ YouTube API Key

### Creating YouTube API Key

1. Go to https://console.cloud.google.com/
2. **Create New Project** or select existing
3. **Enable APIs** → Search "YouTube Data API v3" → **Enable**
4. **Credentials** → **Create Credentials** → **API Key**
5. **Copy API Key**
6. **(Recommended) Restrict key:**
   - Application restrictions: None
   - API restrictions: YouTube Data API v3

### Doppler Configuration for YouTube

**Doppler Secret Names (when `SECRETS_DOPPLER_YOUTUBE_SECRET_NAME=YOUTUBE`):**

```bash
YOUTUBE_API_KEY=AIza...your_key_here
```

**Command to set in Doppler:**
```bash
doppler secrets set YOUTUBE_API_KEY="AIzaSy..."
```

---

## 🦶 Kick OAuth Credentials (Optional)

**Note:** Kick authentication is OPTIONAL. Stream Daemon works fine without it (uses public API).

### Creating Kick OAuth App

1. Go to https://kick.com/settings/developer
2. **Create New Application**
3. Fill in:
   - **Name:** `Stream Daemon`
   - **Redirect URI:** `http://localhost` (not used)
4. **Copy Client ID and Client Secret**

### Doppler Configuration for Kick

**Doppler Secret Names (when `SECRETS_DOPPLER_KICK_SECRET_NAME=KICK`):**

```bash
KICK_CLIENT_ID=your_client_id
KICK_CLIENT_SECRET=your_client_secret
```

**Command to set in Doppler:**
```bash
doppler secrets set KICK_CLIENT_ID="your_client_id"
doppler secrets set KICK_CLIENT_SECRET="your_client_secret"
```

---

## 📋 Complete Doppler Setup Example

### Step 1: Configure .env

```bash
# Enable secrets manager
SECRETS_SECRET_MANAGER=doppler
DOPPLER_TOKEN=dp.st.dev.your_token_here
DOPPLER_PROJECT=stream-daemon
DOPPLER_CONFIG=dev

# Configure secret name mappings
SECRETS_DOPPLER_TWITCH_SECRET_NAME=TWITCH
SECRETS_DOPPLER_YOUTUBE_SECRET_NAME=YOUTUBE
SECRETS_DOPPLER_KICK_SECRET_NAME=KICK
SECRETS_DOPPLER_MASTODON_SECRET_NAME=MASTODON
SECRETS_DOPPLER_BLUESKY_SECRET_NAME=BLUESKY
SECRETS_DOPPLER_DISCORD_SECRET_NAME=DISCORD
SECRETS_DOPPLER_MATRIX_SECRET_NAME=MATRIX
```

### Step 2: Set All Secrets in Doppler

```bash
# Twitch
doppler secrets set TWITCH_CLIENT_ID="your_twitch_client_id"
doppler secrets set TWITCH_CLIENT_SECRET="your_twitch_client_secret"

# YouTube
doppler secrets set YOUTUBE_API_KEY="your_youtube_api_key"

# Kick (optional)
doppler secrets set KICK_CLIENT_ID="your_kick_client_id"
doppler secrets set KICK_CLIENT_SECRET="your_kick_client_secret"

# Mastodon
doppler secrets set MASTODON_CLIENT_ID="your_mastodon_client_id"
doppler secrets set MASTODON_CLIENT_SECRET="your_mastodon_client_secret"
doppler secrets set MASTODON_ACCESS_TOKEN="your_mastodon_access_token"

# Bluesky
doppler secrets set BLUESKY_APP_PASSWORD="your_bluesky_app_password"

# Discord
doppler secrets set DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
doppler secrets set DISCORD_WEBHOOK_TWITCH="https://discord.com/api/webhooks/..."
doppler secrets set DISCORD_WEBHOOK_YOUTUBE="https://discord.com/api/webhooks/..."
doppler secrets set DISCORD_WEBHOOK_KICK="https://discord.com/api/webhooks/..."
doppler secrets set DISCORD_ROLE="1234567890"
doppler secrets set DISCORD_ROLE_TWITCH="1111111111"
doppler secrets set DISCORD_ROLE_YOUTUBE="2222222222"
doppler secrets set DISCORD_ROLE_KICK="3333333333"

# Matrix
doppler secrets set MATRIX_HOMESERVER="https://matrix.org"
doppler secrets set MATRIX_ACCESS_TOKEN="syt_..."
doppler secrets set MATRIX_ROOM_ID="!abc:matrix.org"
```

### Step 3: Verify Secrets

```bash
# List all secrets
doppler secrets

# Download and save to .env format (for backup)
doppler secrets download --no-file --format env > secrets-backup.env
```

---

## 🔒 Security Best Practices

### DO:
- ✅ Use different webhooks for dev/staging/production
- ✅ Regenerate tokens if compromised
- ✅ Use bot accounts for automation (not personal accounts)
- ✅ Store all credentials in secrets manager
- ✅ Enable Doppler audit logs to track access
- ✅ Use environment-specific Doppler configs (dev/stg/prd)

### DON'T:
- ❌ Commit webhook URLs or tokens to git
- ❌ Share tokens in screenshots or logs
- ❌ Use production credentials in development
- ❌ Store secrets in `.env` for production (use Doppler)
- ❌ Use same webhook for all platforms (makes debugging harder)

---

## 🧪 Testing Webhook/Token Configuration

```bash
# Test all platforms with Doppler
doppler run -- python3 tests/test_doppler_all.py

# Test specific platform
doppler run -- python3 tests/test_discord_doppler.py
doppler run -- python3 tests/test_matrix.py

# Verify secrets priority (Doppler overrides .env)
doppler run -- python3 tests/test_secrets_priority.py
```

---

## 📖 Platform-Specific Documentation

- [Discord Setup](DISCORD_MATRIX_SETUP.md) - Detailed Discord webhook guide
- [Matrix Setup](MATRIX_SETUP.md) - Complete Matrix access token guide
- [Doppler Guide](DOPPLER_GUIDE.md) - Full Doppler configuration
- [Secrets Priority](SECRETS_PRIORITY.md) - How secrets override .env

---

## 🆘 Troubleshooting

### "Webhook URL invalid"
- Check format starts with `https://discord.com/api/webhooks/`
- No spaces or extra characters
- Copy entire URL including token

### "Access token unauthorized"
- Regenerate token from platform
- Check if token was revoked
- Verify token has correct permissions

### "Doppler secret not found"
- Check secret name matches exactly (case-sensitive)
- Run `doppler secrets` to list all secrets
- Verify `SECRETS_DOPPLER_*_SECRET_NAME` is set

### "Room/Channel not found"
- Verify bot/user is member of room/channel
- Check ID format is correct
- Matrix: Room ID starts with `!`
- Discord: Role ID is numeric only (no `<@&>`)

---

## 📚 Additional Resources

- **Doppler Documentation:** https://docs.doppler.com/
- **Discord Webhooks Guide:** https://discord.com/developers/docs/resources/webhook
- **Matrix API Documentation:** https://spec.matrix.org/latest/client-server-api/
- **Mastodon API:** https://docs.joinmastodon.org/api/
- **Bluesky AT Protocol:** https://atproto.com/
