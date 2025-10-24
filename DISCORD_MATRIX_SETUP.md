# Discord & Matrix Setup Guide

Complete guide for setting up Discord and Matrix integration with Stream Daemon, including rich embed cards for live stream announcements.

## 🎮 Discord Setup

### Configuration Flexibility

Stream Daemon supports **three flexible Discord configuration modes**:

1. **Single Webhook & Role** - All platforms use the same webhook and role
2. **Single Webhook, Multiple Roles** - One webhook, different @mentions per platform
3. **Multiple Webhooks & Roles** - Complete separation (e.g., different channels per platform)

### Step 1: Create Discord Webhook(s)

**Option A: Single Webhook (Simplest)**

1. **Open Discord** → Navigate to your server
2. **Server Settings** → **Integrations** → **Webhooks**
3. Click **"Create Webhook"**
4. **Configure:**
   - **Name:** "Stream Announcements"
   - **Channel:** Select announcement channel
   - **Avatar:** (Optional) Upload custom avatar
5. **Copy the Webhook URL**
6. Click **Save**

**Option B: Multiple Webhooks (Advanced)**

Repeat the above for each platform you want in a separate channel:
- Create "Twitch Streams" webhook → Copy URL
- Create "YouTube Streams" webhook → Copy URL
- Create "Kick Streams" webhook → Copy URL

### Step 2: Get Role IDs (Optional - for @mentions)

To mention specific roles when going live:

1. **Enable Developer Mode**:
   - User Settings → Advanced → Developer Mode (toggle ON)
2. **Get Role IDs:**
   - Right-click role in Server Settings → Roles
   - Click "Copy Role ID"
   - The ID is a long number like: `987654321098765432`

You can create:
- One role for all platforms (e.g., "Stream Viewers")
- Separate roles per platform (e.g., "Twitch Subs", "YouTube Members", "Kick Fans")

### Step 3: Configure Stream Daemon

**Configuration Mode 1: Single Webhook & Role**

```bash
# .env
DISCORD_ENABLE_POSTING=True

# One webhook for all platforms
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/123456789/abcdefgh

# One role mentioned for all platforms
DISCORD_ROLE=987654321098765432
```

**Configuration Mode 2: Single Webhook, Per-Platform Roles**

```bash
# .env
DISCORD_ENABLE_POSTING=True

# One webhook for all platforms
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/123456789/abcdefgh

# Different roles per platform
DISCORD_ROLE_TWITCH=111111111111111111
DISCORD_ROLE_YOUTUBE=222222222222222222
DISCORD_ROLE_KICK=333333333333333333
```

**Configuration Mode 3: Per-Platform Webhooks & Roles**

```bash
# .env
DISCORD_ENABLE_POSTING=True

# Separate webhooks per platform
DISCORD_WEBHOOK_TWITCH=https://discord.com/api/webhooks/111/aaa
DISCORD_WEBHOOK_YOUTUBE=https://discord.com/api/webhooks/222/bbb
DISCORD_WEBHOOK_KICK=https://discord.com/api/webhooks/333/ccc

# Separate roles per platform (optional)
DISCORD_ROLE_TWITCH=444444444444444444
DISCORD_ROLE_YOUTUBE=555555555555555555
DISCORD_ROLE_KICK=666666666666666666
```

**Doppler/Secrets Manager Setup:**

When using Doppler or other secrets managers, create each as a **separate secret** (not JSON):

```
discord_webhook_url = "https://discord.com/api/webhooks/default/token"
discord_webhook_twitch = "https://discord.com/api/webhooks/twitch/token"
discord_webhook_youtube = "https://discord.com/api/webhooks/youtube/token"
discord_webhook_kick = "https://discord.com/api/webhooks/kick/token"
discord_role = "default_role_id"
discord_role_twitch = "twitch_role_id"
discord_role_youtube = "youtube_role_id"
discord_role_kick = "kick_role_id"
```

This makes it easier to update individual values without editing JSON.

**Priority/Fallback Logic:**
- Per-platform webhook overrides default webhook
- Per-platform role overrides default role
- If neither exists, no mention is sent (embed only)

### Discord Features

✅ **Rich Embed Cards** with:
- Platform-specific colors (Purple for Twitch, Red for YouTube, Green for Kick)
- Stream title as description
- Clickable URL to stream
- Platform emoji indicators

✅ **Flexible Webhooks:**
- Single webhook for simplicity
- Multiple webhooks for organization
- Mix and match as needed

✅ **Flexible Role Mentions:**
- Single role for all platforms
- Platform-specific roles
- No mentions (embeds only)

✅ **Clean Formatting:**
- Embeds separate from role mentions for cleaner appearance
- Footer with call-to-action

---

## 🔷 Matrix Setup

### Step 1: Create a Matrix Account

1. Go to https://app.element.io (or your Matrix homeserver)
2. **Sign up** for a new account or **log in**
3. Note your **homeserver URL** (e.g., `https://matrix.org`)

### Step 2: Create a Room for Announcements

1. Click the **"+"** button → **Create Room**
2. **Configure the room:**
   - **Name:** "Stream Notifications"
   - **Topic:** "Live stream announcements"
   - **Room visibility:** Public or Private (your choice)
3. Click **"Create Room"**
4. **Get the Room ID:**
   - Click Room name → Room Settings → Advanced
   - Copy the **"Internal Room ID"**
   - Format: `!abc123def456:matrix.org`

### Step 3: Get Your Access Token

**Option A: Via Element Web (Easiest)**

1. Click your avatar → **Settings**
2. Go to **Help & About** → **Advanced**
3. Find **"Access Token"**
4. Click **"Click to reveal"**
5. Copy the access token (⚠️ Keep this secret!)

**Option B: Via API (Advanced)**

```bash
curl -XPOST -d '{
  "type": "m.login.password",
  "user": "YOUR_USERNAME",
  "password": "YOUR_PASSWORD"
}' "https://matrix.org/_matrix/client/r0/login"
```

Response will include `access_token`.

### Step 4: Configure Stream Daemon

Add to your `.env` file:

```bash
# Enable Matrix
MATRIX_ENABLE_POSTING=True

# Homeserver URL
MATRIX_HOMESERVER=https://matrix.org

# Access Token (from Step 3)
MATRIX_ACCESS_TOKEN=your_access_token_here

# Room ID (from Step 2)
MATRIX_ROOM_ID=!your_room_id:matrix.org
```

**Doppler/Secrets Manager Setup:**

When using Doppler or other secrets managers, create each as a **separate secret** (not JSON):

```
matrix_homeserver = "https://matrix.org"
matrix_access_token = "syt_abc123..."
matrix_room_id = "!abc123:matrix.org"
```

This makes it easier to update individual values and rotate tokens.

### Matrix Features

✅ **Rich HTML Messages** with:
- Clickable URLs (HTML formatting)
- Platform-specific headers with emoji
- Clean fallback for plain text clients

✅ **Threading Support:**
- Replies link to previous messages
- Creates conversation threads

✅ **Native Matrix Protocol:**
- Uses Matrix Client-Server API
- Returns event IDs for threading

---

## 🧪 Testing Your Setup

### Test Discord

1. **Manually trigger webhook:**
```bash
curl -X POST "YOUR_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "embeds": [{
      "title": "🟣 Live on Twitch",
      "description": "Test Stream Title",
      "url": "https://twitch.tv/test",
      "color": 9520895
    }]
  }'
```

2. **Run Stream Daemon test:**
```bash
python3 tests/test_posting.py
```

### Test Matrix

1. **Manually send message:**
```bash
curl -X POST "https://matrix.org/_matrix/client/r0/rooms/YOUR_ROOM_ID/send/m.room.message" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "msgtype": "m.text",
    "body": "Test message from Stream Daemon",
    "format": "org.matrix.custom.html",
    "formatted_body": "<p><strong>🟣 Live on Twitch!</strong></p><p>Test Stream</p>"
  }'
```

2. **Run Stream Daemon test:**
```bash
python3 tests/test_posting.py
```

---

## 📋 Comparison: Discord vs Matrix

| Feature | Discord | Matrix |
|---------|---------|---------|
| **Setup Difficulty** | Easy (Webhook only) | Moderate (Access token required) |
| **Rich Embeds** | ✅ Native embed cards | ✅ HTML formatted messages |
| **Threading** | ❌ Not supported via webhooks | ✅ Full threading support |
| **Role Mentions** | ✅ Supported | ✅ Via user mentions |
| **Platform Colors** | ✅ Per-platform embed colors | ⚠️ Depends on client |
| **Image Previews** | ✅ Auto-fetches from URLs | ⚠️ Depends on client |
| **Open Source** | ❌ Proprietary | ✅ Fully open protocol |
| **Self-Hostable** | ❌ No | ✅ Yes (Synapse, Dendrite, etc.) |

---

## 🔒 Security Best Practices

### Discord
- ✅ Never share your webhook URL publicly
- ✅ Use channel permissions to control who sees announcements
- ✅ Consider using Doppler or secrets manager for webhook URLs
- ⚠️ Webhooks can't be revoked individually - regenerate if compromised

### Matrix
- ✅ **Never commit access tokens to git**
- ✅ Use app-specific passwords if your homeserver supports them
- ✅ Store tokens in secrets manager (Doppler, Vault, AWS)
- ✅ Regenerate tokens periodically
- ✅ Use room permissions to control who can see announcements

---

## 🚀 Production Deployment

### Using Secrets Manager (Recommended)

**Doppler:**
```bash
# Discord
doppler secrets set DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."

# Matrix
doppler secrets set MATRIX_ACCESS_TOKEN="your_token"
doppler secrets set MATRIX_ROOM_ID="!roomid:matrix.org"
```

**AWS Secrets Manager:**
```bash
# Discord
aws secretsmanager create-secret \
  --name discord-webhook \
  --secret-string '{"webhook_url":"https://discord.com/api/webhooks/..."}'

# Matrix
aws secretsmanager create-secret \
  --name matrix-credentials \
  --secret-string '{"access_token":"your_token","room_id":"!roomid:matrix.org","homeserver":"https://matrix.org"}'
```

Update `.env`:
```bash
SECRETS_SECRET_MANAGER=doppler
# or
SECRETS_SECRET_MANAGER=aws
```

---

## 🐛 Troubleshooting

### Discord Issues

**Webhook returns 404:**
- Verify webhook URL is correct
- Check if webhook was deleted in Discord
- Regenerate webhook if necessary

**Role mentions not working:**
- Ensure Developer Mode is enabled
- Verify role ID is correct (should be all numbers)
- Check bot has permission to mention roles

**Embeds not showing:**
- Check webhook has "Embed Links" permission
- Verify JSON format is correct
- Test with curl command above

### Matrix Issues

**401 Unauthorized:**
- Access token expired or invalid
- Regenerate token from Element settings

**403 Forbidden:**
- Bot not in room (use access token from an account IN the room)
- Room is invite-only

**Messages not appearing:**
- Verify room ID format: `!abc123:matrix.org`
- Check homeserver URL is correct
- Ensure homeserver is reachable

**HTML formatting not showing:**
- Client may not support HTML
- Plain text fallback will still work

---

## 📚 Additional Resources

- [Discord Webhook Documentation](https://discord.com/developers/docs/resources/webhook)
- [Matrix Client-Server API](https://spec.matrix.org/v1.8/client-server-api/)
- [Element (Matrix Client)](https://app.element.io)
- [Stream Daemon Documentation](README.md)
