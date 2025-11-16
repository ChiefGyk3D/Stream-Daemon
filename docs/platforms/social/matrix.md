# Matrix Platform Guide

## Overview

Matrix is a decentralized, open-source communication platform. Stream Daemon can post stream notifications to Matrix rooms using the Matrix Client-Server API.

**🆕 NEW: Per-Username Configuration** - Monitor multiple streamers, each posting to different Matrix rooms! See [Per-Username Configuration Guide](../../configuration/per-username-social-platforms.md#matrix-per-username-configuration).

**Important Limitations:**
- ⚠️ **Matrix does NOT support editing messages** (unlike Discord)
- ⚠️ **No live viewer count updates** - messages post once and stay static
- ⚠️ Messages are simpler than Discord (just stream title and link)

**Unlike Discord webhooks**, Matrix uses:
- ✅ **Access Tokens** OR Username/Password (not webhooks)
- ✅ **Room IDs** (where messages are posted)
- ✅ **Homeserver URL** (your Matrix server)

**Matrix Features:**
- ✅ HTML formatted text
- ✅ Clickable links
- ✅ Platform emojis (🟣/🔴/🟢)
- ✅ Decentralized (self-hostable)
- ✅ End-to-end encryption capable
- ❌ No rich embeds like Discord
- ❌ No thumbnail images in message body
- ❌ No color-coded embeds

---

## Quick Start

1. **Create bot account** on your Matrix server
2. **Get room ID** from your notification room
3. **Add credentials** to Doppler or `.env`
4. **Invite bot** to your room
5. **Test** the integration

---

## Prerequisites

1. **Matrix Account** - Create account on any Matrix homeserver:
   - https://matrix.org (official)
   - https://app.element.io (Element client)
   - Any other Matrix homeserver
2. **Matrix Room** - Create or have access to a room for notifications
3. **Authentication** - Access Token OR Username/Password

---

## Step 1: Create a Matrix Account

### Option A: Using Element Web Client

1. Go to https://app.element.io
2. Click **"Create Account"**
3. Choose a homeserver (e.g., `matrix.org`)
4. Create username and password
5. Verify email (if required)

**Your Matrix ID will be:** `@username:homeserver.com`

**For a dedicated bot account:**
1. **Log out** of your current account (if logged in)
2. **Register new account**:
   - Username: `streambot` (or your preferred bot name)
   - Full Matrix ID: `@streambot:matrix.org`
   - Set a strong password
3. **Save credentials** securely

### Option B: Using Synapse CLI (if you have server access)

```bash
# SSH into your Matrix server
register_new_matrix_user -c /path/to/homeserver.yaml http://localhost:8008

# Follow prompts:
# Username: streambot
# Password: (your password)
# Make admin: No
```

---

## Step 2: Create a Room for Notifications

1. In Element, click **"+"** → **"New Room"**
2. Name it (e.g., "Stream Notifications")
3. Set visibility:
   - **Private** (recommended) - only invited users
   - **Public** - anyone can join
4. Click **"Create Room"**

---

## Step 3: Get Your Room ID

### Method 1: Element Web/Desktop

1. Open the room
2. Click room name → **"Settings"** → **"Advanced"**
3. Copy **"Internal room ID"**
   - Format: `!AbCdEf12345:matrix.org`
   - **Note**: The `!` prefix is required!

### Method 2: Element Mobile

1. Open the room
2. Tap room name → **"Room info"** → **"Advanced"**
3. Copy **"Room ID"**

### Method 3: Via API

```bash
# Get list of rooms you're in
curl -X GET "https://matrix.org/_matrix/client/r0/joined_rooms" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Room ID Format:**
```
!KHzbUMYDd0VnJyFqMXiPyfLipv4DKwn-stVz6RYD1VY:matrix.org
```

**Parts:**
- `!` - Required prefix (indicates it's a room ID)
- `KHzbUMYDd0VnJyFqMXiPyfLipv4DKwn-stVz6RYD1VY` - Unique room identifier
- `:matrix.org` - Your homeserver domain

---

## Step 4: Choose Authentication Method

Stream Daemon supports two authentication methods:

### Method 1: Username/Password (RECOMMENDED for bots)

**Advantages:**
- ✅ Automatic token generation
- ✅ Fresh token on each startup
- ✅ Easier to set up (no manual token extraction)
- ✅ Allows automatic token rotation
- ✅ **Takes priority if both methods are configured**

**Disadvantages:**
- ⚠️ Password stored in config/secrets

**Configuration:**
```bash
# In .env or Doppler
MATRIX_HOMESERVER=https://matrix.org
MATRIX_USERNAME=@streambot:matrix.org
MATRIX_PASSWORD=your_matrix_password
MATRIX_ROOM_ID=!YourRoomId:matrix.org

# Don't set MATRIX_ACCESS_TOKEN - it will be auto-generated
```

### Method 2: Access Token

**Advantages:**
- ✅ More secure (password not in config)
- ✅ Manually managed
- ✅ Never expires (unless revoked)
- ✅ Can revoke from Element settings if compromised

**Disadvantages:**
- ⚠️ Must manually extract token
- ⚠️ No automatic rotation
- ⚠️ **Ignored if username/password are set**

**How to get Access Token:**

**Element Web/Desktop (Recommended):**
1. Go to https://app.element.io
2. Log in to your account
3. Click your **profile picture** (top left) → **"All settings"**
4. Go to **"Help & About"** tab
5. Scroll to **"Advanced"** section
6. Click **"Access Token"** → **&lt;click to reveal&gt;**
7. Copy the token (starts with `syt_` or similar)

**Via API (Manual Login):**
```bash
# Login to get access token
curl -X POST "https://matrix.org/_matrix/client/r0/login" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "m.login.password",
    "identifier": {
      "type": "m.id.user",
      "user": "your_username"
    },
    "password": "your_password"
  }'

# Response includes: "access_token": "syt_..."
```

**Configuration:**
```bash
# In .env or Doppler
MATRIX_HOMESERVER=https://matrix.org
MATRIX_ACCESS_TOKEN=syt_your_access_token_here
MATRIX_ROOM_ID=!YourRoomId:matrix.org

# Don't set MATRIX_USERNAME/MATRIX_PASSWORD
```

### Authentication Priority

**IMPORTANT**: The daemon uses this priority order:

1. **Username/Password (FIRST PRIORITY)** - If both `MATRIX_USERNAME` and `MATRIX_PASSWORD` are set
   - Logs in to get fresh access token on each startup
   - Automatic token rotation
   - **If these are set, any MATRIX_ACCESS_TOKEN is IGNORED**

2. **Access Token (FALLBACK)** - Only if username/password are NOT set
   - Uses static `MATRIX_ACCESS_TOKEN`
   - No automatic rotation
   - Manual management required

**Recommendation:**
- **Production:** Username/Password with secrets manager (Doppler) for auto-rotation
- **Development:** Either method works (Username/Password is simpler)
- **Bot accounts:** Username/Password (easier setup)

---

## Step 5: Configure Stream Daemon

### Option 1: Environment Variables (.env)

Add to your `.env` file:

```bash
# Matrix Configuration
MATRIX_ENABLE_POSTING=True

# Matrix homeserver URL (without trailing slash)
MATRIX_HOMESERVER=https://matrix.org

# Method 1: Username/Password (recommended for bots)
MATRIX_USERNAME=@streambot:matrix.org
MATRIX_PASSWORD=your_bot_password
MATRIX_ROOM_ID=!your_room_id:matrix.org

# Method 2: Access Token (alternative - don't use both!)
# MATRIX_ACCESS_TOKEN=syt_your_token_here
# MATRIX_ROOM_ID=!your_room_id:matrix.org
```

### Option 2: Doppler Secrets Manager (Recommended for Production)

**Step 1: Configure .env**
```bash
# Matrix Configuration
MATRIX_ENABLE_POSTING=True

# Doppler secret configuration
SECRETS_MANAGER=doppler
SECRETS_DOPPLER_MATRIX_SECRET_NAME=MATRIX
```

**Step 2: Add Secrets to Doppler**

**For Username/Password Method:**
```bash
doppler secrets set MATRIX_HOMESERVER="https://matrix.org"
doppler secrets set MATRIX_USERNAME="@streambot:matrix.org"
doppler secrets set MATRIX_PASSWORD="your_bot_password"
doppler secrets set MATRIX_ROOM_ID="!your_room_id:matrix.org"
```

**For Access Token Method:**
```bash
doppler secrets set MATRIX_HOMESERVER="https://matrix.org"
doppler secrets set MATRIX_ACCESS_TOKEN="syt_your_token_here"
doppler secrets set MATRIX_ROOM_ID="!your_room_id:matrix.org"
```

**Verify Secrets:**
```bash
doppler secrets get MATRIX_HOMESERVER --plain
doppler secrets get MATRIX_USERNAME --plain
doppler secrets get MATRIX_ROOM_ID --plain

# Don't show password in terminal history
doppler secrets get MATRIX_PASSWORD
```

### Secrets Priority

**If using secrets manager (Doppler/AWS/Vault):**
1. ✅ Secrets manager values (FIRST - overrides everything)
2. ✅ `.env` values (FALLBACK only if secrets manager not set)

**Authentication method priority:**
1. ✅ Username/password (FIRST - if both are set, generates fresh token)
2. ✅ Access token (FALLBACK - only if username/password not set)

---

## Step 6: Invite Bot to Room

**CRITICAL STEP** - The bot CANNOT post without being in the room!

### Using Element

1. **Log into your personal account** (not the bot)
2. **Open your stream notifications room**
3. **Click room name** → **"Invite"**
4. **Type**: `@streambot:matrix.org` (your bot's Matrix ID)
5. **Click Invite**

### Accept Invitation (Bot Account)

1. **Log into bot account** (`@streambot:matrix.org`)
2. **Check invitations** (bell icon or left sidebar)
3. **Accept invitation** to the room

**Note:** The daemon will NOT auto-accept invitations. You must manually accept the invitation first.

---

## Step 7: Test the Integration

### Quick Test

```bash
# Run the Matrix test
doppler run -- python3 tests/test_matrix.py

# Or without Doppler
python3 tests/test_matrix.py
```

### Expected Output

```
🔐 Authenticating Matrix...
✓ Matrix authenticated successfully
📝 Testing Matrix posting...
✓ Matrix message posted
✓ Matrix message posted
✓ Matrix message posted
✅ Matrix test completed successfully!
```

### Manual Test via API

```bash
# Test Matrix API connection
curl -X POST "https://matrix.org/_matrix/client/r0/rooms/!YourRoomId:matrix.org/send/m.room.message" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "msgtype": "m.text",
    "body": "Test from curl"
  }'

# Should return: {"event_id": "$abc123..."}
```

---

## Message Features

### Platform-Specific Formatting

**Twitch:**
```
🟣 Live on Twitch!
{username} is live on Twitch!
{stream_title}
https://twitch.tv/{username}
```

**YouTube:**
```
🔴 Live on YouTube!
{username} is live on YouTube!
{stream_title}
https://youtube.com/{username}/live
```

**Kick:**
```
🟢 Live on Kick!
{username} is live on Kick!
{stream_title}
https://kick.com/{username}
```

### HTML Formatting

Messages use `org.matrix.custom.html` format for:
- ✅ Clickable URLs
- ✅ Bold platform headers
- ✅ Platform emojis (🟣/🔴/🟢)
- ✅ Clean link previews

### Matrix vs Discord Comparison

| Feature | Discord | Matrix |
|---------|---------|--------|
| **Auth Method** | Webhook URL | Access Token / User+Pass |
| **Rich Embeds** | ✅ Full | ⚠️ HTML only |
| **Live Updates** | ✅ Edit messages | ❌ No editing |
| **Thumbnails** | ✅ Yes | ❌ No |
| **Color Coding** | ✅ Yes | ❌ No |
| **Viewer Counts** | ✅ Live updates | ❌ Static (no editing) |
| **Role Mentions** | ✅ Yes | ⚠️ Via username |
| **Decentralized** | ❌ No | ✅ Yes |
| **Self-Hosted** | ❌ No | ✅ Yes |

**Why no viewer counts in Matrix?**
- Matrix messages can't be edited after posting
- Posting every 5 minutes would spam the room
- Better to keep Matrix messages simple and clean

---

## Security Best Practices

### Access Token Security

**DO:**
- ✅ Store in secrets manager (Doppler/AWS/Vault)
- ✅ Use separate tokens for dev/staging/production
- ✅ Revoke and regenerate if compromised
- ✅ Use bot accounts for automation (not your main account)

**DON'T:**
- ❌ Commit tokens to git
- ❌ Share tokens in screenshots/logs
- ❌ Use your personal account token in production
- ❌ Store tokens in plain text

### Creating a Bot Account (Recommended)

1. Create a new Matrix account: `@streambot:matrix.org`
2. Invite the bot to your notification room
3. Use bot's credentials in Stream Daemon
4. Your personal account stays secure

### Token Rotation & Revocation

**Username/Password Method (Automatic):**
- New token generated on each daemon startup
- Old tokens remain valid until manually revoked
- No manual rotation needed

**Access Token Method (Manual):**

1. **Generate new token** (Element → Settings → Advanced → Access Token)
2. **Update configuration:**
   - In Doppler: `doppler secrets set MATRIX_ACCESS_TOKEN="new_token"`
   - In .env: Update `MATRIX_ACCESS_TOKEN=new_token`
3. **Restart Stream Daemon**
4. **Revoke old token** (optional but recommended):
   - Element → Settings → Sessions → Find old session → Sign out

**How to revoke compromised tokens:**

1. **Element:** Settings → Sessions → Find the session → Sign out
2. **Via API:**
   ```bash
   curl -X POST "https://matrix.org/_matrix/client/r0/logout" \
     -H "Authorization: Bearer OLD_ACCESS_TOKEN"
   ```
3. **Generate new token/password** and update configuration

---

## Troubleshooting

### "Matrix authentication failed"

**Check:**
1. Is `MATRIX_ENABLE_POSTING=True` set?
2. Are credentials configured?
   - **Username/Password:** `MATRIX_USERNAME` + `MATRIX_PASSWORD` + `MATRIX_ROOM_ID`
   - **Access Token:** `MATRIX_ACCESS_TOKEN` + `MATRIX_ROOM_ID`
3. Is homeserver URL correct? (must start with `https://`)
4. For Doppler: Is `SECRETS_DOPPLER_MATRIX_SECRET_NAME=MATRIX` set?

### "Matrix post failed with status 401"

**Error:** Unauthorized (invalid credentials)

**Solutions:**
1. **Username/Password:** Verify username format and password are correct
2. **Access Token:** Regenerate access token from Element
3. Verify token is correctly copied (no extra spaces)
4. Check if token was revoked
5. Try logging out and back in to get new token

### "Matrix post failed with status 403"

**Error:** Forbidden (no permission)

**Solutions:**
1. **MOST COMMON:** Verify bot/user is member of the room
2. **Invite bot to room** if not already member
3. **Accept room invitation** (check bot account)
4. Check room permissions (posting allowed?)
5. Check if you were banned/kicked from room

### "Matrix post failed with status 404"

**Error:** Room not found

**Solutions:**
1. Verify room ID is correct (format: `!abc123:matrix.org`)
2. **Check room ID includes `!` prefix**
3. Check if room still exists
4. Verify you're still a member of the room
5. Verify homeserver domain matches (`:matrix.org`)
6. Try rejoining the room

### "Invalid homeserver URL"

**Solutions:**
1. Must start with `https://` (will auto-add if missing)
2. No trailing slash: `https://matrix.org` ✅, `https://matrix.org/` ❌
3. Use full URL, not just domain
4. Common homeservers:
   - `https://matrix.org` (official)
   - `https://matrix.envs.net`
   - `https://tchncs.de`

### "WordPress 404 Page" or "Wrong Homeserver"

**Problem:** Getting website 404 page instead of Matrix API

**Solution:** 
- Make sure you're using `https://matrix.yourdomain.com` not `https://yourdomain.com`
- The Matrix server must be on a subdomain/port, not the root domain
- Test homeserver is responding:
  ```bash
  curl -s https://matrix.org/_matrix/client/versions
  
  # Should return JSON like:
  # {"versions":["r0.0.1","r0.1.0",...]}
  ```

### Homeserver Connection Test

```bash
# Test homeserver is responding
curl -s https://matrix.org/_matrix/client/versions

# Should return JSON like:
# {"versions":["r0.0.1","r0.1.0","r0.2.0",...]}

# If you get HTML or 404, your homeserver URL is wrong
```

---

## Advanced Configuration

### Using Custom Homeserver

If you're running your own Matrix server:

```bash
# Replace matrix.org with your homeserver domain
MATRIX_HOMESERVER=https://matrix.yourdomain.com

# Your Matrix ID will use your domain
MATRIX_USERNAME=@streambot:yourdomain.com

# Room ID will also use your domain
MATRIX_ROOM_ID=!RoomIdentifier:yourdomain.com
```

### Multiple Notification Rooms

To post to multiple rooms, you'll need to run multiple instances of Stream Daemon with different configurations, or modify the code to support multiple room IDs.

---

## Platform Comparison

| Feature | Mastodon | Bluesky | Discord | Matrix |
|---------|----------|---------|---------|--------|
| **Auth Method** | OAuth | App Password | Webhook URL | Token/User+Pass |
| **Destination** | Own feed | Own feed | Webhook URL | Room ID |
| **Rich Embeds** | ⚠️ Limited | ✅ External | ✅ Full | ⚠️ HTML only |
| **Live Updates** | ❌ No editing | ❌ No editing | ✅ Edit messages | ❌ No editing |
| **Thumbnails** | ✅ Yes | ✅ Yes | ✅ Yes | ❌ No |
| **Mentions** | ✅ Yes | ✅ Yes | ✅ Roles | ⚠️ Username |
| **Decentralized** | ✅ Yes | ✅ Yes | ❌ No | ✅ Yes |
| **Self-Hosted** | ✅ Yes | ❌ No | ❌ No | ✅ Yes |
| **E2E Encryption** | ❌ No | ❌ No | ❌ No | ✅ Yes |

---

## Additional Resources

- **Matrix Specification:** https://spec.matrix.org/
- **Element (Matrix Client):** https://element.io/
- **Matrix.org:** https://matrix.org/
- **Client-Server API Docs:** https://spec.matrix.org/latest/client-server-api/
- **Homeserver List:** https://publiclist.anchel.nl/
- **Synapse Documentation:** https://matrix-org.github.io/synapse/

---

## See Also

- [Discord Setup Guide](discord.md) - Discord webhook configuration
- [Mastodon Setup Guide](mastodon.md) - Mastodon OAuth setup
- [Bluesky Setup Guide](bluesky.md) - Bluesky app password setup
- [Secrets Management](../../configuration/secrets.md) - Using Doppler for secrets
- [Quick Start Guide](../../getting-started/quickstart.md) - Initial setup

---

**Last Updated:** 2024
