# Discord Platform Guide

## Overview

Discord is a popular communication platform for communities. Stream Daemon integrates with Discord using **webhooks** to post rich embed announcements when you go live or end your streams.

**Key Features:**
- 🎨 Rich embed cards with thumbnails and viewer counts
- 🔄 Live updates - embeds update in-place (no duplicate posts)
- 🏷️ Role mentions - ping specific roles per platform
- ⏹️ Stream ended messages - custom messages with VOD links preserved
- 🎯 Flexible configuration - single or per-platform webhooks
- 📝 Platform-specific customization

---

## Quick Start

1. **Create webhook** in your Discord server
2. **Get role IDs** (optional, for @mentions)
3. **Add credentials** to `.env` or Doppler
4. **Test** the integration
5. **Configure custom messages** (optional)

---

## Prerequisites

- Discord server with "Manage Webhooks" permission
- (Optional) Discord role IDs for mentions
- (Optional) Developer Mode enabled for copying IDs

---

## Step 1: Create Discord Webhook

### Option A: Single Webhook (Simplest)

Use one webhook for all streaming platforms:

1. **Open Discord** → Navigate to your server
2. **Right-click the channel** where you want announcements
3. **Edit Channel** → **Integrations** → **Webhooks**
4. Click **"Create Webhook"** (or **"New Webhook"**)
5. **Configure the webhook:**
   - **Name:** "Stream Announcements" (or your choice)
   - **Avatar:** (Optional) Upload custom avatar
6. **Copy the Webhook URL**
   - Format: `https://discord.com/api/webhooks/123456789/abcdefg...`
   - **Keep this secret!** Anyone with it can post to your channel
7. Click **"Save Changes"**

### Option B: Multiple Webhooks (Advanced)

Create separate webhooks for each platform (different channels):

**For Twitch streams:**
1. Create webhook in #twitch-streams channel
2. Copy webhook URL

**For YouTube streams:**
1. Create webhook in #youtube-streams channel
2. Copy webhook URL

**For Kick streams:**
1. Create webhook in #kick-streams channel
2. Copy webhook URL

**Use case:** Separate channels for each platform, different communities per platform

---

## Step 2: Get Role IDs (Optional - For Mentions)

To mention specific roles when going live:

### Enable Developer Mode

1. **User Settings** → **Advanced**
2. **Developer Mode** → Toggle ON
3. Now you can copy IDs from Discord

### Copy Role IDs

1. **Server Settings** → **Roles**
2. **Right-click any role** → **"Copy Role ID"**
3. The ID is a long number like: `987654321098765432`
4. Repeat for each role you want to mention

**Role Strategy Options:**

**Option 1: Single Role for All Platforms**
- Create one role: "Stream Notifications"
- All platforms mention the same role
- Simplest setup

**Option 2: Per-Platform Roles**
- Create separate roles: "Twitch Subs", "YouTube Members", "Kick Fans"
- Each platform mentions its own role
- More targeted notifications

**Option 3: No Role Mentions**
- Skip this step entirely
- Posts go to channel without mentions
- Quieter, less intrusive

---

## Step 3: Configure Stream Daemon

### Configuration Mode 1: Single Webhook & Role

**Use when:** All platforms post to same channel, same role

```bash
# In .env
DISCORD_ENABLE_POSTING=True

# One webhook for all platforms
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/123456789/abcdefgh

# One role mentioned for all platforms (optional)
DISCORD_ROLE=987654321098765432
```

---

### Configuration Mode 2: Single Webhook, Per-Platform Roles

**Use when:** All platforms post to same channel, different roles

```bash
# In .env
DISCORD_ENABLE_POSTING=True

# One webhook for all platforms
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/123456789/abcdefgh

# Different roles per platform
DISCORD_ROLE_TWITCH=111111111111111111
DISCORD_ROLE_YOUTUBE=222222222222222222
DISCORD_ROLE_KICK=333333333333333333
```

---

### Configuration Mode 3: Per-Platform Webhooks & Roles

**Use when:** Each platform has its own channel

```bash
# In .env
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

---

### Configuration Mode 4: Per-Username Webhooks & Roles (NEW!)

**Use when:** Monitoring multiple streamers per platform, each needs their own channel/role

This is the **most granular** configuration option, perfect for:
- Communities with multiple streamers
- Different channels per streamer
- Different role mentions per streamer
- Any combination of the above

```bash
# In .env
DISCORD_ENABLE_POSTING=True

# Monitor multiple streamers
TWITCH_USERNAME=streamer1,streamer2,streamer3

# Per-username webhooks (format: DISCORD_WEBHOOK_PLATFORM_USERNAME)
DISCORD_WEBHOOK_TWITCH_STREAMER1=https://discord.com/api/webhooks/aaa/xxx
DISCORD_WEBHOOK_TWITCH_STREAMER2=https://discord.com/api/webhooks/bbb/yyy
DISCORD_WEBHOOK_TWITCH_STREAMER3=https://discord.com/api/webhooks/ccc/zzz

# Per-username roles (format: DISCORD_ROLE_PLATFORM_USERNAME)
DISCORD_ROLE_TWITCH_STREAMER1=111111111111111111  # @Streamer1Fans
DISCORD_ROLE_TWITCH_STREAMER2=222222222222222222  # @Streamer2Squad
DISCORD_ROLE_TWITCH_STREAMER3=333333333333333333  # @Streamer3Viewers

# Works with any platform
YOUTUBE_USERNAME=creator1,creator2
DISCORD_WEBHOOK_YOUTUBE_CREATOR1=https://discord.com/api/webhooks/ddd/aaa
DISCORD_WEBHOOK_YOUTUBE_CREATOR2=https://discord.com/api/webhooks/eee/bbb
```

**Priority Chain (most specific to least):**
1. Per-username: `DISCORD_WEBHOOK_TWITCH_STREAMER1`
2. Per-platform: `DISCORD_WEBHOOK_TWITCH`
3. Default: `DISCORD_WEBHOOK_URL`

**Example Scenario:**
```bash
# Server with 3 Twitch streamers, each in their own channel
TWITCH_USERNAME=alice,bob,carol

# Alice streams go to #alice-live with @AliceFans role
DISCORD_WEBHOOK_TWITCH_ALICE=https://discord.com/api/webhooks/alice/token
DISCORD_ROLE_TWITCH_ALICE=111111111111111111

# Bob streams go to #bob-streams with @BobSquad role  
DISCORD_WEBHOOK_TWITCH_BOB=https://discord.com/api/webhooks/bob/token
DISCORD_ROLE_TWITCH_BOB=222222222222222222

# Carol streams go to #carol-gaming with @CarolViewers role
DISCORD_WEBHOOK_TWITCH_CAROL=https://discord.com/api/webhooks/carol/token
DISCORD_ROLE_TWITCH_CAROL=333333333333333333
```

**100% Backward Compatible!** Existing single-streamer setups work without any changes.

---

### Using Secrets Manager (Recommended for Production)

**In your `.env` file:**
```bash
# Enable Discord
DISCORD_ENABLE_POSTING=True

# Configure secrets manager
SECRETS_MANAGER=doppler
SECRETS_DOPPLER_DISCORD_SECRET_NAME=DISCORD
```

**In Doppler (or your secrets manager):**

```bash
# For single webhook setup
doppler secrets set DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
doppler secrets set DISCORD_ROLE="987654321098765432"

# For per-platform webhooks
doppler secrets set DISCORD_WEBHOOK_TWITCH="https://discord.com/api/webhooks/111/aaa"
doppler secrets set DISCORD_WEBHOOK_YOUTUBE="https://discord.com/api/webhooks/222/bbb"
doppler secrets set DISCORD_WEBHOOK_KICK="https://discord.com/api/webhooks/333/ccc"

# For per-platform roles
doppler secrets set DISCORD_ROLE_TWITCH="111111111111111111"
doppler secrets set DISCORD_ROLE_YOUTUBE="222222222222222222"
doppler secrets set DISCORD_ROLE_KICK="333333333333333333"
```

**Important:** Create each as a **separate secret**, not as JSON. Stream Daemon fetches them individually.

**See [Secrets Management Guide](../../configuration/secrets.md) for complete setup.**

---

## Rich Embed Features

### Live Stream Embeds

When a stream goes live, Discord receives a rich embed with:

**Twitch Example:**
```
@TwitchNotifications
🟣 Live on Twitch
chiefgyk3d is live on Twitch!

Amazing gameplay session!

👥 Viewers: 1,234
🎮 Category: Just Chatting

[Stream Thumbnail]

Last updated: 14:32:45 • Click to watch!
```

**Embed Components:**
- **Color Bar:** Platform-specific (Purple for Twitch, Red for YouTube, Green for Kick)
- **Title:** "🟣 Live on Twitch" (with platform emoji)
- **Description:** Custom message or default
- **Stream Title:** Shows current stream title
- **Viewer Count:** Live viewer count (updates every check interval)
- **Category/Game:** What game/category you're streaming
- **Thumbnail:** Live stream thumbnail (refreshes with cache-busting)
- **Footer:** Last updated timestamp
- **URL:** Clickable link to watch stream

### Live Updates

**No duplicate posts!** When your stream is live:

1. **First check:** Posts new embed
2. **Subsequent checks:** Updates same embed in-place
   - Fresh viewer count
   - Updated thumbnail
   - New "last updated" timestamp
3. **Result:** One clean embed per stream, always current

**Update Frequency:** Every `SETTINGS_CHECK_INTERVAL` minutes (default: 5)

---

## Stream Ended Messages

When a stream ends, the embed transforms to show:

### Stream Ended Embed

**Example:**
```
⏹️ Stream Ended - Twitch
Thanks for the amazing stream! Catch the VOD below 💜

Amazing gameplay session!

👥 Peak Viewers: 1,234
🎮 Category: Just Chatting

[Final Thumbnail]

Stream ended at 14:45:30 • Click for VOD
```

**Changes from Live:**
- **Icon:** Changes from 🟣/🔴/🟢 to ⏹️
- **Title:** "Stream Ended - Twitch"
- **Message:** Custom "thanks for watching" message
- **Viewer Count:** Labeled as "Peak Viewers"
- **Footer:** Shows end time instead of "last updated"
- **URL:** Still clickable - viewers can watch VOD/replay
- **Color:** Slightly muted to differentiate from live

### Configuring Ended Messages

**Important:** Stream ended messages are **configuration**, not secrets. They belong in `.env`, **NOT** in Doppler/AWS/Vault.

**In your `.env` file:**

```bash
# Default message for all platforms
DISCORD_ENDED_MESSAGE=Thanks for joining! Tune in next time 💜

# Per-platform overrides (optional)
DISCORD_ENDED_MESSAGE_TWITCH=Thanks for the amazing stream! Catch the VOD below 💜
DISCORD_ENDED_MESSAGE_YOUTUBE=Stream has ended! Watch the replay below 🎬
DISCORD_ENDED_MESSAGE_KICK=That was epic! Check out the VOD 🎮
```

**Why not in secrets managers?**
- ❌ Not sensitive data (they're shown publicly in Discord)
- ❌ Don't need encryption or access control
- ✅ Should be easy to edit without API calls
- ✅ Belong in version control with other configuration

**What SHOULD go in secrets managers:**
- ✅ Discord webhook URLs (contain tokens)
- ✅ Platform API keys and secrets
- ✅ Access tokens

### Customization Examples

**Casual streaming:**
```bash
DISCORD_ENDED_MESSAGE_TWITCH=That was fun! See y'all next time 💜
DISCORD_ENDED_MESSAGE_YOUTUBE=Thanks for hanging out! Don't forget to like and subscribe! 🎥
```

**Professional streaming:**
```bash
DISCORD_ENDED_MESSAGE=Thank you for watching today's stream. VOD will be available shortly.
```

**Call-to-action:**
```bash
DISCORD_ENDED_MESSAGE_TWITCH=Stream complete! Follow for notifications 💜
DISCORD_ENDED_MESSAGE_YOUTUBE=Missed it? Watch the VOD! Subscribe for more 🔔
```

**No custom message:**
- Leave undefined/commented out
- Stream Daemon will use a generic default

---

## Message Lifecycle

### Complete Stream Lifecycle

**1. Stream Goes Live**
- Discord embed posted with live indicator (🟣/🔴/🟢)
- Role mention sent (if configured)
- Rich embed with current data
- Message ID stored for tracking

**2. Stream Updates (every CHECK_INTERVAL)**
- **Same embed** updated in-place
- Fresh viewer count
- Updated thumbnail (cache-busting prevents Discord caching)
- "Last updated" timestamp refreshed
- No duplicate posts

**3. Stream Ends**
- Embed transformed to "ended" state
- Custom ended message applied
- "Peak Viewers" label
- VOD link preserved
- Footer shows end time
- Message tracking cleared

### Visual Comparison

| Feature | Live Embed | Ended Embed |
|---------|-----------|-------------|
| **Icon** | 🟣/🔴/🟢 | ⏹️ |
| **Title** | "Live on Twitch" | "Stream Ended - Twitch" |
| **Message** | Custom live message | Custom ended message |
| **Viewer Label** | "Viewers: 1,234" | "Peak Viewers: 1,234" |
| **Footer** | "Last updated: 14:32:45" | "Stream ended at 14:45:30" |
| **Color** | Bright platform color | Muted color |
| **URL** | Stream link | VOD link (same URL) |
| **Updates** | Every check interval | Final state (no updates) |

---

## Configuration Reference

### Required Settings

| Variable | Description | Example |
|----------|-------------|---------|
| `DISCORD_ENABLE_POSTING` | Enable Discord integration | `True` |
| `DISCORD_WEBHOOK_URL` | Default webhook URL (all platforms) | `https://discord.com/api/webhooks/...` |

### Optional Settings (Single Webhook Mode)

| Variable | Description | Example |
|----------|-------------|---------|
| `DISCORD_ROLE` | Default role ID (all platforms) | `987654321098765432` |

### Optional Settings (Per-Platform Mode)

| Variable | Description | Example |
|----------|-------------|---------|
| `DISCORD_WEBHOOK_TWITCH` | Twitch-specific webhook | `https://discord.com/api/webhooks/111/aaa` |
| `DISCORD_WEBHOOK_YOUTUBE` | YouTube-specific webhook | `https://discord.com/api/webhooks/222/bbb` |
| `DISCORD_WEBHOOK_KICK` | Kick-specific webhook | `https://discord.com/api/webhooks/333/ccc` |
| `DISCORD_ROLE_TWITCH` | Twitch role ID | `111111111111111111` |
| `DISCORD_ROLE_YOUTUBE` | YouTube role ID | `222222222222222222` |
| `DISCORD_ROLE_KICK` | Kick role ID | `333333333333333333` |

### Optional Settings (Per-Username Mode)

| Variable | Description | Example |
|----------|-------------|---------|
| `DISCORD_WEBHOOK_TWITCH_ALICE` | Alice's Twitch webhook | `https://discord.com/api/webhooks/111/aaa` |
| `DISCORD_WEBHOOK_YOUTUBE_CREATOR1` | Creator1's YouTube webhook | `https://discord.com/api/webhooks/222/bbb` |
| `DISCORD_WEBHOOK_KICK_GAMER99` | Gamer99's Kick webhook | `https://discord.com/api/webhooks/333/ccc` |
| `DISCORD_ROLE_TWITCH_ALICE` | Alice's Twitch role ID | `111111111111111111` |
| `DISCORD_ROLE_YOUTUBE_CREATOR1` | Creator1's YouTube role ID | `222222222222222222` |
| `DISCORD_ROLE_KICK_GAMER99` | Gamer99's Kick role ID | `333333333333333333` |

**Format:** `DISCORD_WEBHOOK_<PLATFORM>_<USERNAME>` and `DISCORD_ROLE_<PLATFORM>_<USERNAME>` (all uppercase)

### Stream Ended Messages (Configuration, not secrets!)

| Variable | Description | Example |
|----------|-------------|---------|
| `DISCORD_ENDED_MESSAGE` | Default ended message | `Thanks for watching! 💜` |
| `DISCORD_ENDED_MESSAGE_TWITCH` | Twitch ended message | `Catch the VOD below 💜` |
| `DISCORD_ENDED_MESSAGE_YOUTUBE` | YouTube ended message | `Watch the replay! 🎬` |
| `DISCORD_ENDED_MESSAGE_KICK` | Kick ended message | `Check out the VOD 🎮` |

---

## Testing

### Quick Test

```bash
# Run Discord-specific test
python3 tests/test_discord.py

# Or with Doppler
doppler run -- python3 tests/test_discord.py
```

### Full Lifecycle Test

Test live posting, updates, and stream ended messages:

```bash
# Test complete lifecycle with real streams
python3 tests/test_discord_stream_ended.py

# Or with Doppler
doppler run -- python3 tests/test_discord_stream_ended.py
```

### Expected Test Output

```
Discord Stream Ended Test
================================================================================

🔧 Initializing platforms...
✓ All platforms authenticated

📤 Phase 1: Posting initial stream notifications...
Twitch: chiefgyk3d
  ✓ LIVE: Amazing Gameplay
  ✓ Posted to Discord (Message ID: 1234567890)

⏳ Waiting 10 seconds...

📤 Phase 2: Updating stream embeds...
Twitch: chiefgyk3d
  ✓ Updated embed with fresh data

⏳ Waiting 10 seconds...

📤 Phase 3: Marking streams as ended...
Twitch: chiefgyk3d
  ✓ Stream marked as ended with custom message

✅ Test completed successfully!
```

---

## Troubleshooting

### "Webhook Not Found" (404 Error)

**Problem:** Discord can't find the webhook

**Solutions:**
1. Verify webhook URL is correct
   - Must start with `https://discord.com/api/webhooks/`
   - Check for typos or truncation
2. Check webhook wasn't deleted
   - Go to Discord → Channel Settings → Integrations → Webhooks
   - Verify webhook still exists
3. Ensure URL is complete
   - Should be ~120-150 characters long
   - Format: `https://discord.com/api/webhooks/[ID]/[TOKEN]`

### "Invalid Webhook Token" (401 Error)

**Problem:** Webhook token is invalid

**Solutions:**
1. Regenerate webhook in Discord
   - Delete old webhook
   - Create new one
   - Copy new URL
2. Check webhook wasn't regenerated
   - Old URLs become invalid when webhook is edited

### Role Mentions Not Working

**Problem:** Role isn't mentioned in posts

**Solutions:**
1. **Verify role ID is correct:**
   - Right-click role → Copy Role ID
   - Should be 18-19 digit number
2. **Check role is mentionable:**
   - Server Settings → Roles → Select role
   - Ensure "Allow anyone to @mention this role" is enabled
3. **Check permissions:**
   - Webhook must have permission to mention roles
   - Channel permissions allow role mentions

### Embeds Not Updating

**Problem:** New embed posted each time instead of updating

**Solutions:**
1. **Check message tracking:**
   - Stream Daemon stores message IDs
   - Restarting daemon clears tracking
   - First check after restart will post new embed
2. **Verify webhook is consistent:**
   - Same webhook URL used for all updates
   - Per-platform webhooks post separate embeds

### Thumbnails Not Loading

**Problem:** Embed shows broken image

**Solutions:**
1. **Check stream is actually live:**
   - Thumbnails only available when streaming
2. **Wait for next update:**
   - Thumbnails update every check interval
   - Discord may cache old images
3. **Verify platform thumbnail URL:**
   - Different platforms have different thumbnail formats

### Stream Ended Message Not Appearing

**Problem:** Embed doesn't update when stream ends

**Solutions:**
1. **Verify messages are configured:**
   - Check `DISCORD_ENDED_MESSAGE` in `.env`
   - Make sure not in Doppler (configuration, not secret!)
2. **Check daemon is still running:**
   - Must detect stream end to update embed
   - If daemon stopped, won't update
3. **Verify stream actually ended:**
   - Platform API must report stream as offline

### "Secrets Not Found" (when using secrets manager)

**Problem:** Can't fetch webhook URLs from Doppler/AWS/Vault

**Solutions:**
1. Verify secrets manager configuration
2. Check secret names match:
   - Doppler: `DISCORD_WEBHOOK_URL`, `DISCORD_WEBHOOK_TWITCH`, etc.
3. Ensure `.env` doesn't have webhooks
   - Comment out when using secrets manager
4. Test secrets manager connection

**See [Secrets Management Guide](../../configuration/secrets.md) for detailed troubleshooting.**

---

## Advanced Configuration

### Multiple Servers

To post to multiple Discord servers:

**Option 1: Multiple Webhooks in `.env`**
```bash
# Post to Server A and Server B
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/111/aaa,https://discord.com/api/webhooks/222/bbb
```

**Option 2: Run Multiple Instances**
- Separate `.env` files
- Different Doppler configurations
- Each instance posts to different server

### Custom Embed Colors

Stream Daemon uses platform colors by default:
- **Twitch:** Purple (`#9146FF`)
- **YouTube:** Red (`#FF0000`)
- **Kick:** Green (`#53FC18`)

To customize, modify `DiscordPlatform` class in `stream_daemon/platforms/social/discord.py`

### Disabling Features

**Disable role mentions:**
```bash
# Don't set DISCORD_ROLE or DISCORD_ROLE_* variables
# Posts will go to channel without mentions
```

**Disable stream ended messages:**
```bash
# Don't set DISCORD_ENDED_MESSAGE* variables
# Embeds won't update when streams end
```

**Disable live updates:**
- Not currently configurable
- Embeds always update in-place

---

## Security Best Practices

### DO:
- ✅ Store webhook URLs in secrets manager
- ✅ Use separate webhooks for dev/staging/production
- ✅ Keep webhook URLs secret (treat like passwords)
- ✅ Regenerate webhooks periodically

### DON'T:
- ❌ Commit webhook URLs to git
- ❌ Share webhook URLs in screenshots/logs
- ❌ Use production webhooks in development
- ❌ Post webhook URLs publicly

### Webhook Rotation

**How to rotate webhooks:**

1. **Create new webhook** in Discord
2. **Update secrets manager:**
   ```bash
   doppler secrets set DISCORD_WEBHOOK_URL="new_webhook_url"
   ```
3. **Restart Stream Daemon**
4. **Delete old webhook** from Discord
   - Channel Settings → Integrations → Webhooks → Delete

---

## See Also

- [Twitch Setup Guide](../streaming/twitch.md) - Twitch monitoring
- [YouTube Setup Guide](../streaming/youtube.md) - YouTube monitoring
- [Kick Setup Guide](../streaming/kick.md) - Kick monitoring
- [Messages Guide](../../features/custom-messages.md) - Custom message formatting
- [Multi-Platform Guide](../../features/multi-platform.md) - Multi-streaming strategies
- [Secrets Management](../../configuration/secrets.md) - Doppler/AWS/Vault setup
- [Quick Start Guide](../../getting-started/quickstart.md) - Initial setup

---

**Last Updated:** 2024
