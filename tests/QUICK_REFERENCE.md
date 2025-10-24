# Quick Reference - Doppler Secrets

## Environment Setup

```bash
# In .env file
SECRETS_SECRET_MANAGER=doppler
DOPPLER_TOKEN=dp.st.your_token_here  # Environment-specific (dev/stg/prd)
DOPPLER_CONFIG=dev  # Must match your token's environment
```

> **📌 Important:** Doppler tokens are environment-specific. Generate your token from the correct environment (`dev`/`stg`/`prd`) in the Doppler dashboard and set `DOPPLER_CONFIG` to match. A `dev` token cannot access `prd` secrets. See [DOPPLER_GUIDE.md](../DOPPLER_GUIDE.md).

## Required Doppler Secrets

### Twitch
```bash
# In Doppler dashboard, create:
TWITCH_CLIENT_ID=your_twitch_client_id
TWITCH_CLIENT_SECRET=your_twitch_client_secret

# In .env file:
SECRETS_DOPPLER_TWITCH_SECRET_NAME=TWITCH
TWITCH_USERNAME=your_twitch_username
```

### YouTube
```bash
# In Doppler dashboard, create:
YOUTUBE_API_KEY=your_youtube_api_key

# In .env file:
SECRETS_DOPPLER_YOUTUBE_SECRET_NAME=YOUTUBE
YOUTUBE_CHANNEL_ID=your_channel_id
```

### Kick
```bash
# In Doppler dashboard, create (optional but recommended):
KICK_CLIENT_ID=your_kick_client_id
KICK_CLIENT_SECRET=your_kick_client_secret

# In .env file:
SECRETS_DOPPLER_KICK_SECRET_NAME=KICK
KICK_ENABLE=True
KICK_USERNAME=your_kick_username
```

### Mastodon
```bash
# In Doppler dashboard, create:
MASTODON_CLIENT_ID=your_mastodon_client_id
MASTODON_CLIENT_SECRET=your_mastodon_client_secret
MASTODON_ACCESS_TOKEN=your_mastodon_access_token

# In .env file:
SECRETS_DOPPLER_MASTODON_SECRET_NAME=MASTODON
MASTODON_ENABLE_POSTING=True
MASTODON_API_BASE_URL=https://mastodon.social
MASTODON_APP_NAME=StreamDaemon
```

### Bluesky
```bash
# In Doppler dashboard, create:
BLUESKY_APP_PASSWORD=your_bluesky_app_password

# In .env file:
SECRETS_DOPPLER_BLUESKY_SECRET_NAME=BLUESKY
BLUESKY_ENABLE_POSTING=True
BLUESKY_HANDLE=yourname.bsky.social
```

### Discord
```bash
# In Doppler dashboard, create:
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

# In .env file:
SECRETS_DOPPLER_DISCORD_SECRET_NAME=DISCORD
DISCORD_ENABLE_POSTING=True
# Optional role mentions:
DISCORD_ROLE_TWITCH=123456789
DISCORD_ROLE_YOUTUBE=123456789
DISCORD_ROLE_KICK=123456789
```

## Testing Commands

```bash
# Test everything
python tests/test_doppler_all.py

# Test streaming platforms
python tests/test_doppler_twitch.py
python tests/test_doppler_youtube.py
python tests/test_doppler_kick.py

# Test social platforms
python tests/test_doppler_mastodon.py
python tests/test_doppler_bluesky.py
python tests/test_doppler_discord.py
python tests/test_doppler_matrix.py  # Placeholder only

# Test by category
./run_tests.sh streaming  # All streaming platforms
./run_tests.sh social     # All social platforms
```

## Secret Naming Pattern

**Pattern:** `{PREFIX}_{KEY}`

Example:
- Prefix: `TWITCH`
- Keys: `CLIENT_ID`, `CLIENT_SECRET`
- Doppler secrets: `TWITCH_CLIENT_ID`, `TWITCH_CLIENT_SECRET`

The code extracts everything after the prefix as the key name:
- `TWITCH_CLIENT_ID` → `client_id`
- `TWITCH_CLIENT_SECRET` → `client_secret`

## Troubleshooting

```bash
# List Doppler secrets
doppler secrets

# Test Doppler connection
doppler secrets get TWITCH_CLIENT_ID --plain

# Run with Doppler CLI
doppler run -- python tests/test_doppler_all.py
```
