# Matrix Setup Guide

## Overview

Matrix is a decentralized, open-source communication platform. Stream Daemon can post stream notifications to Matrix rooms using the Matrix Client-Server API.

**Important Limitations:**
- ⚠️ **Matrix does NOT support editing messages** (unlike Discord)
- ⚠️ **No live viewer count updates** - messages post once and stay static
- ⚠️ Messages are simpler than Discord (just stream title and link)

**Unlike Discord webhooks**, Matrix uses:
- ✅ **Access Tokens** OR Username/Password (not webhooks)
- ✅ **Room IDs** (where messages are posted)
- ✅ **Homeserver URL** (your Matrix server)

**Authentication Options:**
1. **Access Token** (recommended) - More secure, manually managed
2. **Username/Password** - Auto-generates token, allows rotation

---

## 📋 Prerequisites

1. **Matrix Account** - Create account on any Matrix homeserver:
   - https://matrix.org (official)
   - https://app.element.io (Element client)
   - Any other Matrix homeserver
2. **Matrix Room** - Create or have access to a room for notifications
3. **Access Token** - Generate from your Matrix account

---

## 🔑 Getting Your Matrix Credentials

### Step 1: Create a Matrix Account

1. Go to https://app.element.io
2. Click **"Create Account"**
3. Choose a homeserver (e.g., `matrix.org`)
4. Create username and password
5. Verify email (if required)

**Your Matrix ID will be:** `@username:homeserver.com`

### Step 2: Create a Room for Notifications

1. In Element, click **"+"** → **"New Room"**
2. Name it (e.g., "Stream Notifications")
3. Set visibility:
   - **Private** (recommended) - only invited users
   - **Public** - anyone can join
4. Click **"Create Room"**

### Step 3: Get Your Room ID

**Method 1: Element Web/Desktop**
1. Open the room
2. Click room name → **"Settings"** → **"Advanced"**
3. Copy **"Internal room ID"**
   - Format: `!AbCdEf12345:matrix.org`

**Method 2: Element Mobile**
1. Open the room
2. Tap room name → **"Room info"** → **"Advanced"**
3. Copy **"Room ID"**

**Method 3: Via API**
```bash
# Get list of rooms you're in
curl -X GET "https://matrix.org/_matrix/client/r0/joined_rooms" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Step 4: Get Your Access Token

**⚠️ WARNING: Access tokens are VERY sensitive! Treat like a password!**

**You have TWO authentication options:**

#### Option 1: Access Token (Recommended - More Secure)

**Method 1: Element Web (Recommended)**
1. Go to https://app.element.io
2. Log in to your account
3. Click your **profile picture** (top left) → **"All settings"**
4. Go to **"Help & About"** tab
5. Scroll to **"Advanced"** section
6. Click **"Access Token"** → **&lt;click to reveal&gt;**
7. Copy the token (starts with `syt_` or similar)

**Method 2: Element Desktop**
1. Open Element Desktop
2. Settings → Help & About → Advanced
3. Click to reveal access token

**Method 3: Via API (Manual Login)**
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

**Access Token Pros:**
- ✅ More secure (password not in config)
- ✅ Manually managed
- ✅ Never expires (unless revoked)
- ✅ Can revoke from Element settings if compromised

**Access Token Cons:**
- ⚠️ Must manually rotate/revoke
- ⚠️ If lost, must generate new one manually

---

#### Option 2: Username/Password (Auto Token Rotation)

Instead of manually managing an access token, you can provide your Matrix username and password. Stream Daemon will:
- Log in each time it starts
- Automatically obtain a fresh access token
- Allow for automatic token rotation

**Configuration:**
```bash
# In .env or Doppler
MATRIX_HOMESERVER=https://matrix.org
MATRIX_USERNAME=@youruser:matrix.org
MATRIX_PASSWORD=your_matrix_password
MATRIX_ROOM_ID=!YourRoomId:matrix.org

# Don't set MATRIX_ACCESS_TOKEN - it will be auto-generated
```

**Username/Password Pros:**
- ✅ Automatic token generation
- ✅ Fresh token on each startup
- ✅ No manual token management

**Username/Password Cons:**
- ⚠️ Less secure (password stored in config/secrets)
- ⚠️ Password must be in secrets manager or .env
- ⚠️ If password changes, must update config

**🔒 Recommendation:** 
- **Production:** Use access token + secrets manager (Doppler)
- **Development:** Either method works (access token slightly more secure)
- **Bot accounts:** Use access token (safer for automation)

---

### Token Rotation & Revocation

**How to rotate access tokens:**

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
3. **Generate new token** and update configuration

**Automatic rotation with username/password:**

If using username/password auth, Stream Daemon automatically gets a new token on each startup. Old tokens remain valid until manually revoked.

---

## 🔧 Configuration

### Matrix Limitations vs Discord

**Matrix does NOT support:**
- ❌ Editing messages (can't update viewer counts live)
- ❌ Rich embeds like Discord (only HTML text)
- ❌ Thumbnail images in message body
- ❌ Color-coded messages

**What Matrix DOES support:**
- ✅ HTML formatted text
- ✅ Clickable links
- ✅ Platform emojis (🟣/🔴/🟢)
- ✅ Threading/replies
- ✅ Decentralized (self-hostable)

**Message Style:**

Discord (rich embed with live updates):
```
🟣 Live on Twitch
chiefgyk3d is streaming!
Amazing gameplay!

👥 Viewers: 1,234 ← Updates every 5 minutes
🎮 Category: Just Chatting
```

Matrix (simple HTML, posted once):
```
🟣 Live on Twitch!
chiefgyk3d is streaming!
Amazing gameplay!
https://twitch.tv/chiefgyk3d
```

**Why no viewer counts in Matrix?**
- Matrix messages can't be edited after posting
- Posting every 5 minutes would spam the room
- Better to keep Matrix messages simple and clean

### Option 1: Environment Variables (.env)

Add to your `.env` file:

```bash
# Matrix Configuration
MATRIX_ENABLE_POSTING=True

# Matrix homeserver URL (without trailing slash)
MATRIX_HOMESERVER=https://matrix.org

# Matrix access token (very sensitive - use secrets manager in production!)
MATRIX_ACCESS_TOKEN=syt_your_access_token_here

# Matrix room ID (where notifications will be posted)
MATRIX_ROOM_ID=!AbCdEfGhIjKlMnOp:matrix.org
```

### Option 2: Doppler Secrets Manager (Recommended for Production)

**Step 1: Add to `.env`**
```bash
# Matrix Configuration
MATRIX_ENABLE_POSTING=True

# Doppler secret configuration
SECRETS_SECRET_MANAGER=doppler
SECRETS_DOPPLER_MATRIX_SECRET_NAME=MATRIX
```

**Step 2: Add Secrets to Doppler**

```bash
# Set Matrix secrets in Doppler
doppler secrets set MATRIX_HOMESERVER="https://matrix.org"
doppler secrets set MATRIX_ACCESS_TOKEN="syt_your_token_here"
doppler secrets set MATRIX_ROOM_ID="!YourRoomId:matrix.org"
```

**Or via Doppler Dashboard:**
1. Go to https://dashboard.doppler.com
2. Select your project → environment (dev/stg/prd)
3. Click **"Add Secret"**
4. Add each secret:

| Secret Name | Value | Example |
|-------------|-------|---------|
| `MATRIX_HOMESERVER` | Your homeserver URL | `https://matrix.org` |
| `MATRIX_ACCESS_TOKEN` | Your access token | `syt_dGVzdA...` |
| `MATRIX_ROOM_ID` | Your room ID | `!AbCdEf:matrix.org` |

---

## 📝 Doppler Secret Naming Convention

### Matrix Secrets Structure

When using Doppler with `SECRETS_DOPPLER_MATRIX_SECRET_NAME=MATRIX`:

**Doppler will look for secrets with prefix `MATRIX_`:**

```
MATRIX_HOMESERVER      → Used for homeserver URL
MATRIX_ACCESS_TOKEN    → Used for authentication
MATRIX_ROOM_ID         → Used for room destination
```

### Complete Doppler Setup Example

**In `.env`:**
```bash
# Enable Matrix posting
MATRIX_ENABLE_POSTING=True

# Configure secrets manager
SECRETS_SECRET_MANAGER=doppler
DOPPLER_TOKEN=dp.st.dev.your_doppler_token

# Matrix secret name (tells Stream Daemon to look for MATRIX_* secrets)
SECRETS_DOPPLER_MATRIX_SECRET_NAME=MATRIX
```

**In Doppler Dashboard:**
```
Project: stream-daemon
Environment: dev (or prd/stg)

Secrets:
├── MATRIX_HOMESERVER = https://matrix.org
├── MATRIX_ACCESS_TOKEN = syt_dGVzdA...
└── MATRIX_ROOM_ID = !AbCdEfGhIjKlMnOp:matrix.org
```

**Priority System:**
1. Doppler secrets (if `SECRETS_SECRET_MANAGER=doppler`)
2. `.env` file (fallback for local development)

---

## 🧪 Testing

### Test Matrix Configuration

Create `tests/test_matrix.py`:

```python
#!/usr/bin/env python3
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import importlib.util
spec = importlib.util.spec_from_file_location(
    "stream_daemon",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "stream-daemon.py")
)
stream_daemon = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stream_daemon)

MatrixPlatform = stream_daemon.MatrixPlatform

print("=" * 80)
print("MATRIX CONNECTION TEST")
print("=" * 80)
print()

# Initialize and authenticate
matrix = MatrixPlatform()
success = matrix.authenticate()

if success:
    print("✅ Matrix authenticated successfully!")
    print(f"   Homeserver: {matrix.homeserver}")
    print(f"   Room ID: {matrix.room_id}")
    print()
    
    # Test post
    print("Posting test message...")
    message = "🔴 Test notification from Stream Daemon!"
    event_id = matrix.post(message)
    
    if event_id:
        print(f"✅ Test message posted successfully!")
        print(f"   Event ID: {event_id}")
    else:
        print("❌ Failed to post test message")
else:
    print("❌ Matrix authentication failed")
    print()
    print("Check your configuration:")
    print("  1. MATRIX_ENABLE_POSTING=True")
    print("  2. MATRIX_HOMESERVER is set")
    print("  3. MATRIX_ACCESS_TOKEN is set")
    print("  4. MATRIX_ROOM_ID is set")

print()
print("=" * 80)
```

**Run the test:**
```bash
# With Doppler
doppler run -- python3 tests/test_matrix.py

# Without Doppler
python3 tests/test_matrix.py
```

---

## 🎨 Message Features

Stream Daemon sends rich HTML messages to Matrix with:

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

---

## 🔒 Security Best Practices

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
3. Generate access token for the bot
4. Use bot's token in Stream Daemon
5. Your personal account stays secure

---

## 🆚 Matrix vs Discord vs Others

| Feature | Discord | Matrix | Mastodon | Bluesky |
|---------|---------|--------|----------|---------|
| **Auth Method** | Webhook URL | Access Token | OAuth | App Password |
| **Destination** | Webhook URL | Room ID | N/A (own feed) | N/A (own feed) |
| **Rich Embeds** | ✅ Full | ⚠️ HTML only | ⚠️ Limited | ✅ External |
| **Live Updates** | ✅ Edit messages | ❌ No editing | ❌ No editing | ❌ No editing |
| **Role Mentions** | ✅ Yes | ⚠️ Via username | ❌ No | ❌ No |
| **Decentralized** | ❌ No | ✅ Yes | ✅ Yes | ✅ Yes |
| **Self-Hosted** | ❌ No | ✅ Yes | ✅ Yes | ❌ No |

---

## 🐛 Troubleshooting

### "Matrix authentication failed"

**Check:**
1. Is `MATRIX_ENABLE_POSTING=True` set?
2. Are all three credentials configured?
   - `MATRIX_HOMESERVER`
   - `MATRIX_ACCESS_TOKEN`
   - `MATRIX_ROOM_ID`
3. Is homeserver URL correct? (must start with `https://`)
4. For Doppler: Is `SECRETS_DOPPLER_MATRIX_SECRET_NAME=MATRIX` set?

### "Matrix post failed with status 401"

**Error:** Unauthorized (invalid token)

**Solutions:**
1. Regenerate access token from Element
2. Verify token is correctly copied (no extra spaces)
3. Check if token was revoked
4. Try logging out and back in to get new token

### "Matrix post failed with status 403"

**Error:** Forbidden (no permission)

**Solutions:**
1. Verify bot/user is member of the room
2. Check room permissions (posting allowed?)
3. Invite bot to room if not already member
4. Check if you were banned/kicked from room

### "Matrix post failed with status 404"

**Error:** Room not found

**Solutions:**
1. Verify room ID is correct (format: `!abc123:matrix.org`)
2. Check if room still exists
3. Verify you're still a member of the room
4. Try rejoining the room

### "Invalid homeserver URL"

**Solutions:**
1. Must start with `https://` (will auto-add if missing)
2. No trailing slash: `https://matrix.org` ✅, `https://matrix.org/` ❌
3. Use full URL, not just domain
4. Common homeservers:
   - `https://matrix.org` (official)
   - `https://matrix.envs.net`
   - `https://tchncs.de`

### Testing Manually

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

## 📚 Additional Resources

- **Matrix Specification:** https://spec.matrix.org/
- **Element (Matrix Client):** https://element.io/
- **Matrix.org:** https://matrix.org/
- **Client-Server API Docs:** https://spec.matrix.org/latest/client-server-api/
- **Homeserver List:** https://publiclist.anchel.nl/

---

## 🔗 See Also

- [DISCORD_SETUP.md](DISCORD_SETUP.md) - Discord webhook setup
- [DOPPLER_GUIDE.md](DOPPLER_GUIDE.md) - Secrets manager configuration
- [SECRETS_PRIORITY.md](SECRETS_PRIORITY.md) - Secret priority system
- [README.md](../README.md) - Main documentation
