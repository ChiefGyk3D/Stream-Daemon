# Doppler Secret Naming Convention

This document describes how to name secrets in Doppler for Stream Daemon.

## How Doppler Secrets Work

Stream Daemon uses **prefix-based secret fetching**. When you set `SECRETS_DOPPLER_TWITCH_SECRET_NAME=twitch`, the code:
1. Fetches all secrets from Doppler
2. Filters for secrets starting with `twitch_` (case-insensitive matching)
3. Extracts the suffix after `twitch_` as the key name
4. Returns a dict like `{'client_id': 'xxx', 'client_secret': 'yyy'}`

**Important:** Secret names in Doppler can be uppercase (`TWITCH_CLIENT_ID`) or lowercase (`twitch_client_id`) - the code matches case-insensitively. However, **UPPERCASE is recommended** as it's more visible in the Doppler dashboard and matches standard environment variable naming.

## Required Secrets Per Platform

### Twitch
**Doppler Secret Name (in .env):** `SECRETS_DOPPLER_TWITCH_SECRET_NAME=TWITCH`

**Required Doppler Secrets:**
- `TWITCH_CLIENT_ID` - Your Twitch application client ID
- `TWITCH_CLIENT_SECRET` - Your Twitch application client secret

**Get credentials from:** https://dev.twitch.tv/console/apps

---

### YouTube
**Doppler Secret Name (in .env):** `SECRETS_DOPPLER_YOUTUBE_SECRET_NAME=YOUTUBE`

**Required Doppler Secrets:**
- `YOUTUBE_API_KEY` - Your YouTube Data API v3 key

**Get credentials from:** https://console.cloud.google.com/apis/credentials

---

### Kick
**Doppler Secret Name (in .env):** `SECRETS_DOPPLER_KICK_SECRET_NAME=KICK`

**Required Doppler Secrets:**
- `KICK_CLIENT_ID` - Your Kick application client ID
- `KICK_CLIENT_SECRET` - Your Kick application client secret

**Get credentials from:** Kick Developer Portal (developer.kick.com or similar)

**Note:** Kick can also work without authentication using the public API, but the authenticated API is more reliable and has higher rate limits.

---

### Mastodon
**Doppler Secret Name (in .env):** `SECRETS_DOPPLER_MASTODON_SECRET_NAME=MASTODON`

**Required Doppler Secrets:**
- `MASTODON_CLIENT_ID` - Your Mastodon app client ID
- `MASTODON_CLIENT_SECRET` - Your Mastodon app client secret
- `MASTODON_ACCESS_TOKEN` - Your Mastodon access token

**Get credentials from:** Your Mastodon instance → Settings → Development

---

### Bluesky
**Doppler Secret Name (in .env):** `SECRETS_DOPPLER_BLUESKY_SECRET_NAME=BLUESKY`

**Required Doppler Secrets:**
- `BLUESKY_APP_PASSWORD` - Your Bluesky app password (NOT your main password)

**Get credentials from:** Bluesky Settings → App Passwords

---

### Discord
**Doppler Secret Name (in .env):** `SECRETS_DOPPLER_DISCORD_SECRET_NAME=DISCORD`

**Required Doppler Secrets:**
- `DISCORD_WEBHOOK_URL` - Your Discord webhook URL

**Get credentials from:** Discord Server → Channel Settings → Integrations → Webhooks

---

## Example Doppler Setup

In your Doppler project, create these secrets:

```
# Twitch
TWITCH_CLIENT_ID=abc123xyz789
TWITCH_CLIENT_SECRET=secret123secret456

# YouTube
YOUTUBE_API_KEY=AIzaSyABC123XYZ789

# Mastodon
MASTODON_CLIENT_ID=client123
MASTODON_CLIENT_SECRET=secret456
MASTODON_ACCESS_TOKEN=token789

# Bluesky
BLUESKY_APP_PASSWORD=apppass123

# Discord
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/123/abc
```

## Environment Variables

In your `.env` file, configure Doppler:

```bash
# Enable Doppler
SECRETS_SECRET_MANAGER=doppler
DOPPLER_TOKEN=dp.st.xxxxxxxxxxxx

# Point to Doppler secrets by prefix
SECRETS_DOPPLER_TWITCH_SECRET_NAME=TWITCH
SECRETS_DOPPLER_YOUTUBE_SECRET_NAME=YOUTUBE
SECRETS_DOPPLER_MASTODON_SECRET_NAME=MASTODON
SECRETS_DOPPLER_BLUESKY_SECRET_NAME=BLUESKY
SECRETS_DOPPLER_DISCORD_SECRET_NAME=DISCORD
```

## Testing

Run the test suite to validate your Doppler secrets:

```bash
# Test all platforms
python tests/test_doppler_all.py

# Test individual platforms
python tests/test_doppler_twitch.py
python tests/test_doppler_youtube.py
python tests/test_doppler_kick.py
```

## Troubleshooting

### Secret not found
- Verify the secret exists in Doppler with exact name (case-sensitive)
- Check that `DOPPLER_TOKEN` is set correctly
- Ensure `SECRETS_SECRET_MANAGER=doppler`

### Wrong prefix
- If `SECRETS_DOPPLER_TWITCH_SECRET_NAME=TWITCH`, secrets must start with `TWITCH_`
- If you named them differently, update the env var accordingly
- Example: If secrets are `STREAM_TWITCH_ID`, use `SECRETS_DOPPLER_TWITCH_SECRET_NAME=STREAM_TWITCH`

### Authentication fails
- Run test scripts to validate credentials are correct
- Check credential format (some APIs need specific formats)
- Verify credentials haven't expired
