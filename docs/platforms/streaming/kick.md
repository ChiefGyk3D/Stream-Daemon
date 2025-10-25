# Kick Platform Guide

## Overview

Kick is a live streaming platform that competes with Twitch. Stream Daemon monitors your Kick channel for live streams using the Kick API with optional OAuth authentication.

**Features:**
- ✅ OAuth 2.0 client credentials flow
- ✅ Automatic fallback to public API
- ✅ Stream status detection
- ✅ Viewer count tracking
- ✅ Stream title extraction
- ✅ Works without authentication (public API)

**API Rate Limits:** Higher with OAuth authentication, lower with public API

---

## Requirements

### Option A: Public API (No Authentication)
- **Nothing!** Just a Kick username
- ✅ Works immediately
- ⚠️ Lower rate limits
- ⚠️ May be less reliable

### Option B: OAuth Authentication (Recommended)
- Kick account with 2FA enabled
- Kick Developer Application
- Client ID and Client Secret

---

## Setup Instructions

### Option A: Public API (Quick Start)

**No setup required!** Just add your username:

```bash
# In .env
KICK_ENABLE=True
KICK_USERNAME=your_kick_username

# That's it! No credentials needed.
```

Stream Daemon will use Kick's public API to check stream status.

**Limitations:**
- Lower rate limits
- Potentially less reliable during high traffic
- No authentication benefits

---

### Option B: OAuth Authentication (Recommended)

#### Step 1: Enable 2FA on Your Kick Account

**Important:** Kick requires 2FA to access Developer settings

1. **Login to Kick:**
   - Go to [https://kick.com](https://kick.com)
   - Log in to your account

2. **Enable 2FA:**
   - Click your profile (top right) → **Settings**
   - Go to **Security** tab
   - Enable **Two-Factor Authentication (2FA)**
   - Follow the setup process (usually via authenticator app)
   - Save backup codes securely

#### Step 2: Create Kick Developer Application

1. **Go to Developer Settings:**
   - In Kick, go to **Settings** → **Developer**
   - Or visit the Developer Portal (if available)

2. **Create New Application:**
   - Click **"Create Application"** or **"New App"**
   - **Application Name:** "Stream Daemon" (or your choice)
   - **Description:** Optional - describe your bot
   - **Scopes/Permissions:** Select **"Read Access"** or **"read:channel"**
     - This allows checking stream status
     - No write permissions needed
   - Click **"Create"** or **"Submit"**

3. **Get Credentials:**
   - After creation, you'll see:
     - **Client ID** - Copy this
     - **Client Secret** - Copy this immediately (may not be shown again)
   - Store both securely

**Note:** Kick's Developer Portal may vary in layout. Look for "Developer", "Applications", or "API" in settings.

---

#### Step 3: Configure Stream Daemon

**Option A: Using Environment Variables (.env)**

```bash
# Enable Kick monitoring
KICK_ENABLE=True

# Your Kick username
KICK_USERNAME=your_kick_username

# Kick OAuth credentials
KICK_CLIENT_ID=your_kick_client_id
KICK_CLIENT_SECRET=your_kick_client_secret
```

**Option B: Using Secrets Manager (Recommended for Production)**

**In your `.env` file:**
```bash
# Enable Kick monitoring
KICK_ENABLE=True

# Your Kick username
KICK_USERNAME=your_kick_username

# Configure secrets manager
SECRETS_SECRET_MANAGER=doppler
SECRETS_DOPPLER_KICK_SECRET_NAME=KICK
```

**In Doppler (or your secrets manager):**
```bash
# Add Kick credentials to Doppler
doppler secrets set KICK_CLIENT_ID="your_kick_client_id"
doppler secrets set KICK_CLIENT_SECRET="your_kick_client_secret"
```

**See [Secrets Management Guide](../../configuration/secrets.md) for complete setup.**

---

## Configuration Reference

### Required Settings

| Variable | Description | Example |
|----------|-------------|---------|
| `KICK_ENABLE` | Enable Kick monitoring | `True` |
| `KICK_USERNAME` | Channel to monitor | `yourstreamer` |

### Optional Settings (OAuth)

| Variable | Description | Example |
|----------|-------------|---------|
| `KICK_CLIENT_ID` | Application Client ID | `abc123xyz789` |
| `KICK_CLIENT_SECRET` | Application Secret | `secretkey123` |

### Other Optional Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `SETTINGS_CHECK_INTERVAL` | Check frequency (minutes) | `5` |
| `SETTINGS_OFFLINE_CHECK_INTERVAL` | Frequency when offline | `5` |
| `SETTINGS_ONLINE_CHECK_INTERVAL` | Frequency when live | `2` |

---

## How It Works

### Authentication Modes

Stream Daemon supports two modes for Kick:

#### Mode 1: OAuth (Client Credentials)

**When:** `KICK_CLIENT_ID` and `KICK_CLIENT_SECRET` are set

1. Exchanges credentials for OAuth access token
2. Uses authenticated API endpoints
3. Higher rate limits
4. More reliable

#### Mode 2: Public API (Fallback)

**When:** No credentials set, or OAuth fails

1. Uses Kick's public API endpoints
2. No authentication needed
3. Lower rate limits
4. May be less reliable during peak times

**Automatic Fallback:** If OAuth fails, Stream Daemon automatically tries public API.

### Stream Detection

Stream Daemon checks your channel every `SETTINGS_CHECK_INTERVAL` minutes:

1. **When Offline:**
   - Checks every `SETTINGS_OFFLINE_CHECK_INTERVAL` minutes
   - Waits for stream to go live

2. **When Live:**
   - Checks every `SETTINGS_ONLINE_CHECK_INTERVAL` minutes
   - Monitors viewer count
   - Detects when stream ends

3. **State Transitions:**
   - **Offline → Live:** Posts "Stream Started" announcement
   - **Live → Offline:** Posts "Stream Ended" message (if enabled)

---

## Platform-Specific Messages

Create custom messages just for Kick using platform-specific message files.

### Quick Setup

Create these files in your project root:

**`messages_kick.txt`** (Stream started messages):
```
🟢 LIVE on Kick! {stream_title} - https://kick.com/{username}
Kick stream starting: {stream_title} - Watch at https://kick.com/{username}
Now live on Kick with {stream_title}! ⚡ https://kick.com/{username}
Going live on Kick! {stream_title} - https://kick.com/{username}
⚡ Streaming on Kick: {stream_title} - https://kick.com/{username}
```

**`end_messages_kick.txt`** (Stream ended messages):
```
Stream ended! Thanks for watching on Kick! 🟢
That's a wrap! See you next time! ⚡
Stream offline - Thanks for hanging out! ❤️
Offline now - Don't forget to follow! https://kick.com/{username}
```

### Available Variables

- `{stream_title}` - Current stream title from Kick
- `{username}` - Your Kick username
- `{platform}` - Will be "Kick"

### Fallback Behavior

If `messages_kick.txt` doesn't exist, Stream Daemon falls back to:
- Global `messages.txt` file
- Built-in default messages

**See [Messages Guide](../../features/custom-messages.md) for complete message customization.**

---

## Discord Integration

### Role Mentions

When your Kick stream goes live, mention a specific Discord role:

```bash
# In .env
DISCORD_ENABLE_POSTING=True
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

# Mention this role when Kick goes live
DISCORD_ROLE_KICK=1234567890123456789
```

### Getting Role IDs

1. Enable **Developer Mode** in Discord:
   - User Settings → Advanced → Developer Mode (toggle ON)
2. Right-click any role → **"Copy Role ID"**
3. Paste into `DISCORD_ROLE_KICK`

**Example Discord Post:**
```
@KickNotifications
🟢 LIVE on Kick!
yourstreamer is live on Kick!
Epic Gaming Session
https://kick.com/yourstreamer
```

---

## Testing

### Quick Test

Test your Kick configuration without going live:

```bash
# Run Kick-specific test
python3 tests/test_doppler_kick.py

# Or with Doppler
doppler run -- python3 tests/test_doppler_kick.py
```

### Expected Output

**With OAuth:**
```
🔐 Testing Kick OAuth authentication...
✓ Kick OAuth authenticated successfully
📡 Testing Kick API...
✓ Stream status detected
✅ Kick test completed successfully!
```

**With Public API:**
```
🔐 No Kick credentials - using public API...
📡 Testing Kick public API...
✓ Stream status detected
✅ Kick test completed successfully!
```

### What Gets Tested

- ✅ OAuth credentials work (if provided)
- ✅ Can access Kick API
- ✅ Channel username is valid
- ✅ Stream detection is functional
- ✅ Public API fallback works

---

## Troubleshooting

### "Kick Authentication Failed"

**Problem:** OAuth credentials invalid

**Solutions:**
1. Verify Client ID is correct
   - Check for typos
   - Ensure no extra spaces
2. Verify Client Secret is correct
   - Regenerate if lost
3. Check 2FA is enabled on your Kick account
   - Developer settings require 2FA
4. Verify application wasn't deleted
   - Check Kick Settings → Developer
5. **Try public API mode** - comment out credentials:
   ```bash
   # KICK_CLIENT_ID=...
   # KICK_CLIENT_SECRET=...
   ```

### "Username Not Found"

**Problem:** Cannot find Kick channel

**Solutions:**
1. Verify username is correct
   - Use exact Kick username
   - **Do not** include `@` symbol
   - Example: `xqc` not `@xqc`
2. Check channel exists:
   - Visit `https://kick.com/your_username`
   - Verify channel is accessible
3. Check for username changes
   - Kick allows username changes

### "Stream Not Detected" (when you're live)

**Problem:** Stream Daemon doesn't see your live stream

**Solutions:**
1. Verify stream is actually live:
   - Check `https://kick.com/your_username`
2. Check `SETTINGS_CHECK_INTERVAL`:
   - Default is 5 minutes
   - Reduce if needed for faster detection
3. Try with OAuth credentials:
   - Public API may have delays
4. Check Kick platform status:
   - Service might be experiencing issues

### "Rate Limit Exceeded"

**Problem:** Too many API requests

**Solutions:**
1. **Use OAuth authentication:**
   - Higher rate limits than public API
   - Set up Client ID + Secret
2. **Increase check interval:**
   ```bash
   SETTINGS_CHECK_INTERVAL=10  # Check every 10 minutes
   ```
3. **Check for multiple instances:**
   - Ensure you're not running duplicates

### "Public API Not Working"

**Problem:** Fallback to public API fails

**Solutions:**
1. **Set up OAuth credentials:**
   - Public API may be unreliable
   - OAuth is recommended
2. **Check Kick platform status:**
   - Public API may be down
3. **Wait and retry:**
   - Transient network issues
4. **Check network connectivity:**
   - Ensure you can access kick.com

### "Secrets Not Found" (when using secrets manager)

**Problem:** Can't fetch credentials from Doppler/AWS/Vault

**Solutions:**
1. Verify secrets manager configuration
2. Check secret names match:
   - Doppler: `KICK_CLIENT_ID`, `KICK_CLIENT_SECRET`
3. Ensure `.env` doesn't have credentials
   - Comment them out when using secrets manager
4. Test secrets manager connection

**See [Secrets Management Guide](../../configuration/secrets.md) for detailed troubleshooting.**

---

## API Information

### Kick API Endpoints

**Note:** Kick's API is less documented than Twitch/YouTube. Endpoints may change.

**OAuth Endpoints:**
1. **Token:** `POST https://kick.com/api/v2/oauth/token`
   - Get access token from credentials
   - Client credentials flow

2. **Channel:** `GET https://kick.com/api/v2/channels/{username}`
   - Get channel info and livestream status

**Public API Endpoints:**
1. **Channel:** `GET https://kick.com/api/v1/channels/{username}`
   - Public channel information
   - No authentication required

### Rate Limits

**OAuth Authentication:**
- Higher rate limits (exact limits undocumented)
- More reliable access
- Recommended for production

**Public API:**
- Lower rate limits (exact limits undocumented)
- May be throttled during high traffic
- OK for development/testing

**Stream Daemon Usage:**
- ~12 requests/hour at default 5-minute intervals
- Should be well under limits with OAuth

### API Documentation

**Note:** Kick doesn't have extensive public API documentation yet.

- **Kick Platform:** [https://kick.com](https://kick.com)
- **Developer Settings:** Kick → Settings → Developer (requires 2FA)
- **Community Documentation:** Check Kick developer communities

---

## Security Best Practices

### DO:
- ✅ Store Client Secret in secrets manager
- ✅ Enable 2FA on your Kick account
- ✅ Use separate applications for dev/production
- ✅ Regenerate credentials periodically

### DON'T:
- ❌ Commit Client Secret to git
- ❌ Share Client Secret in screenshots/logs
- ❌ Use production credentials in development
- ❌ Disable 2FA (required for Developer access)

### Credential Rotation

**How to rotate credentials:**

1. **Create new application** in Kick Developer settings
2. **Update secrets manager:**
   ```bash
   doppler secrets set KICK_CLIENT_ID="new_id"
   doppler secrets set KICK_CLIENT_SECRET="new_secret"
   ```
3. **Restart Stream Daemon**
4. **Delete old application** from Kick settings

---

## Advanced Configuration

### Comparing OAuth vs Public API

| Feature | OAuth | Public API |
|---------|-------|------------|
| **Setup** | Requires credentials | No setup |
| **Rate Limits** | Higher | Lower |
| **Reliability** | More reliable | Less reliable |
| **Authentication** | Client credentials flow | None |
| **Recommended For** | Production | Development/testing |

### Multiple Kick Accounts

To monitor multiple Kick channels, run separate instances:

**Instance 1:**
```bash
# .env.channel1
KICK_USERNAME=channel1
KICK_CLIENT_ID=app1_id
KICK_CLIENT_SECRET=app1_secret
```

**Instance 2:**
```bash
# .env.channel2
KICK_USERNAME=channel2
KICK_CLIENT_ID=app2_id
KICK_CLIENT_SECRET=app2_secret
```

### Custom Check Intervals

Fine-tune checking frequency:

```bash
# Check every 10 minutes when offline
SETTINGS_OFFLINE_CHECK_INTERVAL=10

# Check every 1 minute when live
SETTINGS_ONLINE_CHECK_INTERVAL=1
```

---

## Platform Comparison

| Feature | Kick | Twitch | YouTube |
|---------|------|--------|---------|
| **Auth Required** | Optional | Required | Required |
| **Public API** | ✅ Yes | ❌ No | ❌ No |
| **OAuth Support** | ✅ Yes | ✅ Yes | N/A (API Key) |
| **Rate Limits** | Variable | 800/min | 10K quota/day |
| **API Maturity** | 🟡 Developing | 🟢 Mature | 🟢 Mature |
| **Documentation** | ⚠️ Limited | ✅ Extensive | ✅ Extensive |

---

## Known Issues

### API Stability

**Issue:** Kick's API is newer and may have occasional changes or downtime.

**Mitigation:**
- Stream Daemon has automatic fallback to public API
- Errors are logged for debugging
- Retry logic handles transient failures

### Documentation Gaps

**Issue:** Kick doesn't have comprehensive public API docs yet.

**Mitigation:**
- Stream Daemon uses community-discovered endpoints
- Code includes comments explaining API usage
- Updates will be released as Kick's API matures

### 2FA Requirement

**Issue:** Developer settings require 2FA enabled.

**Not an issue:**
- 2FA is good security practice anyway
- One-time setup
- Protects your account

---

## See Also

- [Twitch Setup Guide](twitch.md) - Twitch monitoring
- [YouTube Setup Guide](youtube.md) - YouTube Live monitoring
- [Discord Setup Guide](../social/discord.md) - Discord notifications
- [Messages Guide](../../features/custom-messages.md) - Custom message formatting
- [Secrets Management](../../configuration/secrets.md) - Doppler/AWS/Vault setup
- [Quick Start Guide](../../getting-started/quickstart.md) - Initial setup

---

**Last Updated:** 2024
**API Status:** Kick's API is actively developing. This guide will be updated as their API matures.
