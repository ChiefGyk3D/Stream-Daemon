# Quick Reference - Doppler Secrets

## Environment Setup

```bash
# In .env file
SECRETS_SECRET_MANAGER=doppler
DOPPLER_TOKEN=dp.st.your_token_here
```

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

## Testing Commands

```bash
# Test everything
python tests/test_doppler_all.py

# Test individual platforms
python tests/test_doppler_twitch.py
python tests/test_doppler_youtube.py
python tests/test_doppler_kick.py
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
