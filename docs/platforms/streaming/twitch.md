# Twitch Platform Guide

## Overview

Twitch is the world's leading live streaming platform for gamers. Stream Daemon monitors your Twitch channel for live streams using the official Twitch API with OAuth 2.0 authentication.

**Features:**
- ✅ Async API support (twitchAPI v4+)
- ✅ OAuth 2.0 authentication
- ✅ Real-time stream status
- ✅ Viewer count detection
- ✅ Stream title extraction
- ✅ Automatic token management

**API Rate Limits:** 800 requests per minute (handled automatically)

---

## Requirements

- Twitch Developer Application
- Client ID and Client Secret

---

## Setup Instructions

### Step 1: Create Twitch Developer Application

1. **Go to Twitch Developer Console:**
   - Visit [https://dev.twitch.tv/console/apps](https://dev.twitch.tv/console/apps)
   - Log in with your Twitch account

2. **Register Your Application:**
   - Click **"Register Your Application"**
   - **Name:** "Stream Daemon" (or your choice)
   - **OAuth Redirect URL:** `http://localhost` 
     - *Required but not actually used by Stream Daemon*
     - Can use any valid URL like `http://localhost:3000`
   - **Category:** Choose relevant category
     - "Application Integration" recommended
     - "Broadcasting Suite" also works
   - Click **"Create"**

3. **Get Your Credentials:**
   - After creation, you'll see your application listed
   - **Client ID:** Displayed on the application page - copy it
   - **Client Secret:** Click **"New Secret"** to generate
     - **Important:** Copy immediately - you can't view it again!
     - If lost, generate a new one (old one will be revoked)

---

### Step 2: Configure Stream Daemon

#### Option A: Using Environment Variables (.env)

```bash
# Enable Twitch monitoring
TWITCH_ENABLE=True

# Your Twitch username (the channel to monitor)
TWITCH_USERNAME=your_twitch_username

# Twitch API credentials
TWITCH_CLIENT_ID=your_client_id_here
TWITCH_CLIENT_SECRET=your_client_secret_here
```

#### Option B: Using Secrets Manager (Recommended for Production)

**In your `.env` file:**
```bash
# Enable Twitch monitoring
TWITCH_ENABLE=True

# Your Twitch username
TWITCH_USERNAME=your_twitch_username

# Configure secrets manager
SECRETS_SECRET_MANAGER=doppler
SECRETS_DOPPLER_TWITCH_SECRET_NAME=TWITCH
```

**In Doppler (or your secrets manager):**
```bash
# Add Twitch credentials to Doppler
doppler secrets set TWITCH_CLIENT_ID="your_client_id_here"
doppler secrets set TWITCH_CLIENT_SECRET="your_client_secret_here"
```

**See [Secrets Management Guide](../../configuration/secrets.md) for complete setup.**

---

## Configuration Reference

### Required Settings

| Variable | Description | Example |
|----------|-------------|---------|
| `TWITCH_ENABLE` | Enable Twitch monitoring | `True` |
| `TWITCH_USERNAME` | Channel to monitor | `ninja` |
| `TWITCH_CLIENT_ID` | Application Client ID | `abc123xyz789` |
| `TWITCH_CLIENT_SECRET` | Application Secret | `secretkey123` |

### Optional Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `SETTINGS_CHECK_INTERVAL` | Check frequency (minutes) | `5` |
| `SETTINGS_OFFLINE_CHECK_INTERVAL` | Frequency when offline | `5` |
| `SETTINGS_ONLINE_CHECK_INTERVAL` | Frequency when live | `2` |

---

## How It Works

### Authentication Flow

1. Stream Daemon uses **OAuth 2.0 Client Credentials** flow
2. Exchanges Client ID + Secret for an **access token**
3. Access token used for all API requests
4. Tokens are **automatically refreshed** when expired

**No manual token management needed!**

### Stream Detection

Stream Daemon checks your channel status every `SETTINGS_CHECK_INTERVAL` minutes:

1. **When Offline:**
   - Checks every `SETTINGS_OFFLINE_CHECK_INTERVAL` minutes
   - Waits for stream to go live

2. **When Live:**
   - Checks every `SETTINGS_ONLINE_CHECK_INTERVAL` minutes
   - Monitors viewer count
   - Detects when stream ends

3. **State Transitions:**
   - **Offline → Live:** Posts "Stream Started" announcement to social platforms
   - **Live → Offline:** Posts "Stream Ended" message (if enabled)

---

## Platform-Specific Messages

You can create custom messages just for Twitch using platform-specific message files.

### Quick Setup

Create these files in your project root:

**`messages_twitch.txt`** (Stream started messages):
```
🔴 LIVE on Twitch! {stream_title} - https://twitch.tv/{username}
Going live with {stream_title}! 🎮 https://twitch.tv/{username}
Twitch stream starting NOW: {stream_title} - https://twitch.tv/{username}
Time to stream! {stream_title} on Twitch - https://twitch.tv/{username}
Live on Twitch: {stream_title} - Come hang out! 💜 https://twitch.tv/{username}
```

**`end_messages_twitch.txt`** (Stream ended messages):
```
Stream ended! Thanks for watching! 💜
That's a wrap! See you next time on Twitch! 🎮
Stream offline - Thanks for hanging out! ❤️
Offline now - Don't forget to follow! https://twitch.tv/{username}
```

### Available Variables

- `{stream_title}` - Current stream title from Twitch
- `{username}` - Your Twitch username
- `{platform}` - Will be "Twitch"

### Fallback Behavior

If `messages_twitch.txt` doesn't exist, Stream Daemon falls back to:
- Global `messages.txt` file
- Built-in default messages

**See [Messages Guide](../../features/custom-messages.md) for complete message customization.**

---

## Discord Integration

### Role Mentions

When your Twitch stream goes live, Stream Daemon can mention a specific Discord role:

```bash
# In .env
DISCORD_ENABLE_POSTING=True
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

# Mention this role when Twitch goes live
DISCORD_ROLE_TWITCH=1234567890123456789
```

### Getting Role IDs

1. Enable **Developer Mode** in Discord:
   - User Settings → Advanced → Developer Mode (toggle ON)
2. Right-click any role in your server → **"Copy Role ID"**
3. Paste the ID into `DISCORD_ROLE_TWITCH`

**Example Discord Post:**
```
@TwitchNotifications
🔴 LIVE on Twitch!
ninja is live on Twitch!
Fortnite Arena Practice
https://twitch.tv/ninja
```

---

## Testing

### Quick Test

Test your Twitch configuration without going live:

```bash
# Run Twitch-specific test
python3 tests/test_doppler_twitch.py

# Or with Doppler
doppler run -- python3 tests/test_doppler_twitch.py
```

### Expected Output

```
🔐 Testing Twitch authentication...
✓ Twitch authenticated successfully
📡 Testing Twitch API...
✓ Stream status detected
✅ Twitch test completed successfully!
```

### What Gets Tested

- ✅ Client ID and Secret are valid
- ✅ OAuth token generation works
- ✅ Can fetch channel information
- ✅ Stream detection is functional

---

## Troubleshooting

### "Invalid Client ID"

**Problem:** Twitch API returns authentication error

**Solutions:**
1. Verify Client ID is correct
   - Check for typos
   - Ensure no extra spaces
2. Verify Client Secret is correct
   - Regenerate if lost (old one will be revoked)
3. Check application status in [Twitch Developer Console](https://dev.twitch.tv/console/apps)
   - Make sure application wasn't deleted
4. Ensure OAuth redirect URL is set
   - Even though not used, it's required by Twitch

### "Username not found"

**Problem:** Cannot find Twitch channel

**Solutions:**
1. Verify username is correct
   - Use exact Twitch username
   - **Do not** include `@` symbol
   - Example: `ninja` not `@ninja`
2. Check if channel exists and is public
3. Try visiting `https://twitch.tv/your_username` in browser

### "Stream not detected" (when you're actually live)

**Problem:** Stream Daemon doesn't see your live stream

**Solutions:**
1. Check `SETTINGS_CHECK_INTERVAL` isn't too long
   - Default is 5 minutes - reduce if needed
2. Verify stream is actually live on Twitch
3. Check Twitch API status: [https://status.twitch.tv](https://status.twitch.tv)
4. Run test script to verify API access works

### "Rate limit exceeded"

**Problem:** Too many API requests

**Solutions:**
1. Increase `SETTINGS_CHECK_INTERVAL`
   - Don't check more than once per minute
2. Check you're not running multiple instances
3. Twitch allows 800 requests/minute normally - should be plenty

### "Secrets not found" (when using secrets manager)

**Problem:** Can't fetch credentials from Doppler/AWS/Vault

**Solutions:**
1. Verify secrets manager is configured correctly
2. Check secret names match:
   - Doppler: `TWITCH_CLIENT_ID`, `TWITCH_CLIENT_SECRET`
3. Ensure `.env` doesn't have credentials
   - Comment them out when using secrets manager
4. Check secrets manager connection
   - Doppler: Valid `DOPPLER_TOKEN`

**See [Secrets Management Guide](../../configuration/secrets.md) for detailed troubleshooting.**

---

## API Information

### Twitch API Endpoints Used

Stream Daemon uses these Twitch API endpoints:

1. **OAuth Token:**
   - `POST https://id.twitch.tv/oauth2/token`
   - Gets access token from Client ID + Secret

2. **Get Streams:**
   - `GET https://api.twitch.tv/helix/streams?user_login={username}`
   - Checks if channel is live
   - Returns stream title, viewer count, game

3. **Get Users:**
   - `GET https://api.twitch.tv/helix/users?login={username}`
   - Validates username exists

### Rate Limits

**Official Limits:**
- 800 requests per minute
- Automatic retry with exponential backoff if exceeded

**Stream Daemon Usage:**
- ~12 requests/hour at default 5-minute intervals
- Well under rate limits

### API Documentation

- **Twitch API Reference:** [https://dev.twitch.tv/docs/api](https://dev.twitch.tv/docs/api)
- **OAuth Guide:** [https://dev.twitch.tv/docs/authentication](https://dev.twitch.tv/docs/authentication)
- **API Status:** [https://status.twitch.tv](https://status.twitch.tv)

---

## Security Best Practices

### DO:
- ✅ Store Client Secret in secrets manager (Doppler/AWS/Vault)
- ✅ Use separate applications for dev/staging/production
- ✅ Regenerate Client Secret periodically
- ✅ Keep OAuth redirect URL simple (`http://localhost`)

### DON'T:
- ❌ Commit Client Secret to git
- ❌ Share Client Secret in screenshots/logs
- ❌ Use production credentials in development
- ❌ Hardcode credentials in source code

### Credential Rotation

**How to rotate credentials:**

1. **Generate new Client Secret** in Twitch Developer Console
2. **Update secrets manager:**
   ```bash
   doppler secrets set TWITCH_CLIENT_SECRET="new_secret_here"
   ```
3. **Restart Stream Daemon** - will use new secret automatically
4. **Old secret is revoked** - can no longer be used

---

## Advanced Configuration

### Multiple Twitch Accounts

To monitor multiple Twitch channels, run separate instances:

**Instance 1:**
```bash
# .env.channel1
TWITCH_USERNAME=channel1
TWITCH_CLIENT_ID=app1_id
TWITCH_CLIENT_SECRET=app1_secret
```

**Instance 2:**
```bash
# .env.channel2
TWITCH_USERNAME=channel2
TWITCH_CLIENT_ID=app2_id
TWITCH_CLIENT_SECRET=app2_secret
```

Run each with its own config:
```bash
doppler run --config dev_channel1 -- python3 stream-daemon.py
doppler run --config dev_channel2 -- python3 stream-daemon.py
```

### Custom Check Intervals

Fine-tune checking frequency:

```bash
# Check every 10 minutes when offline (save API quota)
SETTINGS_OFFLINE_CHECK_INTERVAL=10

# Check every 1 minute when live (faster updates)
SETTINGS_ONLINE_CHECK_INTERVAL=1
```

---

## See Also

- [YouTube Setup Guide](youtube.md) - YouTube Live monitoring
- [Kick Setup Guide](kick.md) - Kick streaming platform
- [Discord Setup Guide](../social/discord.md) - Discord notifications
- [Messages Guide](../../features/custom-messages.md) - Custom message formatting
- [Secrets Management](../../configuration/secrets.md) - Doppler/AWS/Vault setup
- [Quick Start Guide](../../getting-started/quickstart.md) - Initial setup

---

**Last Updated:** 2024
