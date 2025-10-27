# YouTube Live Platform Guide

## Overview

YouTube Live is Google's live streaming platform. Stream Daemon monitors your YouTube channel for live streams using the YouTube Data API v3.

**Features:**
- ✅ Auto-resolves channel ID from @handle or username
- ✅ No manual channel ID lookup needed
- ✅ Stream status detection
- ✅ Concurrent viewer count
- ✅ Stream title extraction
- ✅ Supports both modern handles and legacy usernames

**API Rate Limits:** 10,000 quota units per day (each check uses ~3 units)

---

## Requirements

- Google Cloud Project
- YouTube Data API v3 enabled
- API Key

---

## Setup Instructions

### Step 1: Create Google Cloud Project

1. **Go to Google Cloud Console:**
   - Visit [https://console.cloud.google.com/](https://console.cloud.google.com/)
   - Log in with your Google account

2. **Create New Project:**
   - Click the project dropdown (top left)
   - Click **"New Project"**
   - **Project Name:** "Stream Daemon" (or your choice)
   - **Organization:** Leave as default (or select if you have one)
   - Click **"Create"**
   - Wait for project creation (takes a few seconds)

3. **Select Your Project:**
   - Click the project dropdown again
   - Select your newly created "Stream Daemon" project

---

### Step 2: Enable YouTube Data API v3

1. **Navigate to API Library:**
   - In Google Cloud Console, go to **"APIs & Services"** → **"Library"**
   - Or use quick link: [API Library](https://console.cloud.google.com/apis/library)

2. **Find YouTube Data API:**
   - Search for **"YouTube Data API v3"**
   - Click on the result

3. **Enable the API:**
   - Click **"Enable"** button
   - Wait for activation (takes a few seconds)

---

### Step 3: Create API Key

1. **Navigate to Credentials:**
   - Go to **"APIs & Services"** → **"Credentials"**
   - Or use quick link: [Credentials](https://console.cloud.google.com/apis/credentials)

2. **Create API Key:**
   - Click **"Create Credentials"** → **"API Key"**
   - Copy the generated API key immediately
   - **Important:** Store securely - anyone with this key can use your quota!

3. **Restrict API Key (Recommended):**
   - Click **"Restrict Key"** (or edit the key after creation)
   - Under **"API restrictions"**, select **"Restrict key"**
   - Check **"YouTube Data API v3"**
   - Optionally restrict by:
     - **Application:** IP addresses, HTTP referrers, etc.
     - **API:** Only YouTube Data API v3
   - Click **"Save"**

**Why restrict?** Improves security by limiting what the key can access if leaked.

---

### Step 4: Configure Stream Daemon

#### Option A: Using Environment Variables (.env)

```bash
# Enable YouTube monitoring
YOUTUBE_ENABLE=True

# Your YouTube username (auto-resolves to channel ID)
YOUTUBE_USERNAME=@YourHandle

# YouTube API credentials
YOUTUBE_API_KEY=AIzaSyABC123XYZ789...

# Channel ID is OPTIONAL - auto-resolved from username
# Only set this if you want to skip the channel lookup (slightly faster)
# YOUTUBE_CHANNEL_ID=UCvFY4KyqVBuYd7JAl3NRyiQ
```

#### Option B: Using Secrets Manager (Recommended for Production)

**In your `.env` file:**
```bash
# Enable YouTube monitoring
YOUTUBE_ENABLE=True

# Your YouTube username
YOUTUBE_USERNAME=@YourHandle

# Configure secrets manager
SECRETS_MANAGER=doppler
SECRETS_DOPPLER_YOUTUBE_SECRET_NAME=YOUTUBE
```

**In Doppler (or your secrets manager):**
```bash
# Add YouTube credentials to Doppler
doppler secrets set YOUTUBE_API_KEY="AIzaSyABC123XYZ789..."

# Optional: Add channel ID if you want to skip lookup
# doppler secrets set YOUTUBE_CHANNEL_ID="UCvFY4KyqVBuYd7JAl3NRyiQ"
```

**See [Secrets Management Guide](../../configuration/secrets.md) for complete setup.**

---

## Configuration Reference

### Required Settings

| Variable | Description | Example |
|----------|-------------|---------|
| `YOUTUBE_ENABLE` | Enable YouTube monitoring | `True` |
| `YOUTUBE_USERNAME` | Channel @handle or name | `@LinusTechTips` |
| `YOUTUBE_API_KEY` | YouTube Data API v3 key | `AIzaSyABC...` |

### Optional Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `YOUTUBE_CHANNEL_ID` | Channel ID (auto-resolved if not set) | None |
| `SETTINGS_CHECK_INTERVAL` | Check frequency (minutes) | `5` |
| `SETTINGS_OFFLINE_CHECK_INTERVAL` | Frequency when offline | `5` |
| `SETTINGS_ONLINE_CHECK_INTERVAL` | Frequency when live | `2` |

### Username Formats Supported

Stream Daemon automatically resolves channel IDs from these formats:

| Format | Example | Notes |
|--------|---------|-------|
| **Modern Handle** | `@LinusTechTips` | Recommended - new YouTube format |
| **Legacy Username** | `LinusTechTips` | Older channel names |
| **Channel URL** | `/c/LinusTechTips` | Also works (extracts username) |

**Recommendation:** Use modern `@handle` format - it's the YouTube standard now.

---

## How It Works

### Channel ID Resolution

1. **On First Run:**
   - Stream Daemon sees `YOUTUBE_USERNAME=@LinusTechTips`
   - Calls YouTube API: "Search for @LinusTechTips"
   - Gets back: `CHANNEL_ID=UCXuqSBlHAE6Xw-yeJA0Tunw`
   - Caches result in memory for session

2. **Subsequent Checks:**
   - Uses cached channel ID
   - No additional lookups needed during runtime

3. **Manual Override (Optional):**
   - Set `YOUTUBE_CHANNEL_ID=UC...` to skip lookup entirely
   - Saves ~1 API call on startup
   - Use if you know your channel ID

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

## API Optimization & Limitations

### Quota-Efficient Detection Method

Stream Daemon uses an **optimized** approach to detect YouTube live streams that uses only **3 quota units** per check instead of the standard 101 units:

**Standard Method (101 units):**
- Search for live streams: 100 units
- Get stream details: 1 unit
- **Total:** 101 units per check

**Optimized Method (3 units):**
- Get channel's uploads playlist: 1 unit
- Get most recent upload: 1 unit  
- Check if that video is live: 1 unit
- **Total:** 3 units per check

This gives you **33x more checks** with the same daily quota!

### Known Limitation

⚠️ **The optimized method only works if your live stream is the most recent video on your channel.**

**When this might be an issue:**
- You uploaded a VOD, Short, or premiere **after** starting your stream
- You have multiple concurrent live streams (rare)
- You're streaming for a very long time and uploaded other content during the stream

**Who this affects:**
- Channels that frequently upload content while streaming
- 24/7 live stream channels with regular uploads
- Multi-stream setups

**Who this doesn't affect (most streamers):**
- Typical streamers who go live without uploading other content
- Channels that only upload VODs after streams end
- Most gaming and talk show channels

### Alternative: Full Detection Mode

If you need 100% reliable detection regardless of upload activity, you can modify the code to use the standard search API:

```python
# In stream-daemon.py, YouTubePlatform.is_live() method
# Replace the optimized approach with:
search_request = self.client.search().list(
    part="snippet",
    channelId=channel_id_to_check,
    eventType="live",
    type="video",
    maxResults=1
)
```

**Trade-off:** Uses 101 units per check instead of 3 units, reducing your daily check capacity from ~3,300 to ~99 checks.

### Best Practices

1. **For most streamers:** Use the default optimized method (3 units)
2. **For high-upload channels:** Consider the full detection mode or increase quota
3. **Monitor quota usage:** Check Google Cloud Console regularly
4. **Adjust check intervals:** Reduce frequency if hitting quota limits

---

## Platform-Specific Messages

Create custom messages just for YouTube using platform-specific message files.

### Quick Setup

Create these files in your project root:

**`messages_youtube.txt`** (Stream started messages):
```
📺 YouTube LIVE! {stream_title} - https://youtube.com/@{username}/live
Streaming now on YouTube: {stream_title} - Subscribe and watch! https://youtube.com/@{username}/live
New YouTube stream: {stream_title} 🎥 https://youtube.com/@{username}/live
Going live on YouTube with {stream_title}! https://youtube.com/@{username}/live
🔴 LIVE: {stream_title} - Watch and subscribe! https://youtube.com/@{username}/live
```

**`end_messages_youtube.txt`** (Stream ended messages):
```
Stream ended! Thanks for watching! Don't forget to like and subscribe! 📺
That's a wrap! VOD will be available soon on YouTube! 🎥
Stream offline - Thanks for joining! Subscribe for notifications! ❤️
Offline now - Catch the VOD later! https://youtube.com/@{username}
```

### Available Variables

- `{stream_title}` - Current stream title from YouTube
- `{username}` - Your YouTube handle/username
- `{platform}` - Will be "YouTube"

### Fallback Behavior

If `messages_youtube.txt` doesn't exist, Stream Daemon falls back to:
- Global `messages.txt` file
- Built-in default messages

**See [Messages Guide](../../features/custom-messages.md) for complete message customization.**

---

## Discord Integration

### Role Mentions

When your YouTube stream goes live, mention a specific Discord role:

```bash
# In .env
DISCORD_ENABLE_POSTING=True
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

# Mention this role when YouTube goes live
DISCORD_ROLE_YOUTUBE=1234567890123456789
```

### Getting Role IDs

1. Enable **Developer Mode** in Discord:
   - User Settings → Advanced → Developer Mode (toggle ON)
2. Right-click any role → **"Copy Role ID"**
3. Paste into `DISCORD_ROLE_YOUTUBE`

**Example Discord Post:**
```
@YouTubeNotifications
📺 YouTube LIVE!
LinusTechTips is live on YouTube!
Building a Gaming PC in 2024
https://youtube.com/@LinusTechTips/live
```

---

## Testing

### Quick Test

Test your YouTube configuration without going live:

```bash
# Run YouTube-specific test
python3 tests/test_doppler_youtube.py

# Or with Doppler
doppler run -- python3 tests/test_doppler_youtube.py
```

### Expected Output

```
🔐 Testing YouTube authentication...
✓ YouTube API key valid
📡 Resolving channel ID from username...
✓ Channel ID: UCXuqSBlHAE6Xw-yeJA0Tunw
📡 Testing stream detection...
✓ Stream status detected
✅ YouTube test completed successfully!
```

### What Gets Tested

- ✅ API key is valid
- ✅ YouTube Data API v3 is enabled
- ✅ Username resolves to channel ID
- ✅ Can fetch channel information
- ✅ Stream detection works

---

## Troubleshooting

### "API Key Invalid"

**Problem:** YouTube API returns authentication error

**Solutions:**
1. Verify API key is correct
   - Check for typos
   - Ensure no extra spaces
   - Keys start with `AIza`
2. Check YouTube Data API v3 is enabled
   - Go to [API Library](https://console.cloud.google.com/apis/library)
   - Search "YouTube Data API v3"
   - Should show "API Enabled"
3. Verify API key restrictions
   - If restricted, ensure YouTube Data API v3 is allowed
4. Check quota hasn't been exceeded (see below)

### "Channel Not Found"

**Problem:** Cannot resolve username to channel ID

**Solutions:**
1. **Try different username formats:**
   - Modern handle: `@LinusTechTips` ✅
   - Legacy username: `LinusTechTips` ✅
   - Without @: `LinusTechTips` ✅
2. **Verify channel exists:**
   - Visit `https://youtube.com/@your_username`
   - Check channel is public
3. **Use channel ID directly:**
   - Find channel ID manually:
     - Go to your YouTube channel
     - View page source
     - Search for `"channelId"`
   - Set `YOUTUBE_CHANNEL_ID=UC...` in config

### "Quota Exceeded"

**Problem:** "quotaExceeded" error from YouTube API

**Understanding YouTube Quotas:**
- **Daily Limit:** 10,000 quota units per project
- **Cost per check:** ~3 units (channel lookup + stream status)
- **Max checks per day:** ~3,300 checks
- **Resets:** Daily at midnight Pacific Time

**Solutions:**
1. **Reduce check frequency:**
   ```bash
   SETTINGS_OFFLINE_CHECK_INTERVAL=10  # Check every 10 min when offline
   SETTINGS_ONLINE_CHECK_INTERVAL=5    # Check every 5 min when live
   ```
2. **Set channel ID directly** (saves 1 unit per check):
   ```bash
   YOUTUBE_CHANNEL_ID=UCXuqSBlHAE6Xw-yeJA0Tunw
   ```
3. **Request quota increase** (if legitimate high-volume use):
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - APIs & Services → Quotas
   - Request increase for YouTube Data API v3
4. **Check for other applications:**
   - Ensure no other apps are using same API key
   - Create separate project for Stream Daemon

**Quota Monitoring:**
```bash
# View quota usage:
# Google Cloud Console → APIs & Services → Dashboard
# Click on "YouTube Data API v3" → Quotas
```

### "Stream Not Detected" (when you're live)

**Problem:** Stream Daemon doesn't see your live stream

**Solutions:**
1. Check stream is actually live:
   - Visit `https://youtube.com/@your_username/live`
   - Should show your live stream
2. Verify channel ID is correct:
   - Check test output shows right channel ID
3. Check API status:
   - [YouTube API Status](https://status.cloud.google.com/)
4. Increase check frequency:
   ```bash
   SETTINGS_CHECK_INTERVAL=1  # Check every minute
   ```

### "Secrets Not Found" (when using secrets manager)

**Problem:** Can't fetch API key from Doppler/AWS/Vault

**Solutions:**
1. Verify secrets manager configuration
2. Check secret names match:
   - Doppler: `YOUTUBE_API_KEY`
   - AWS: As configured in `SECRETS_AWS_YOUTUBE_SECRET_NAME`
3. Ensure `.env` doesn't have API key
   - Comment out when using secrets manager
4. Test secrets manager connection

**See [Secrets Management Guide](../../configuration/secrets.md) for detailed troubleshooting.**

---

## API Information

### YouTube API Endpoints Used

Stream Daemon uses these YouTube Data API v3 endpoints with an **optimized quota-efficient approach**:

#### Current Implementation (Optimized - 3 units per check)

1. **Channels (Get Uploads Playlist):**
   - `GET https://www.googleapis.com/youtube/v3/channels?part=contentDetails&id={channel_id}`
   - Gets the channel's uploads playlist ID
   - **Cost:** 1 quota unit per call
   - **Called:** Every check interval

2. **PlaylistItems (Get Recent Upload):**
   - `GET https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId={uploads_playlist_id}&maxResults=1`
   - Gets the most recent video from the uploads playlist
   - **Cost:** 1 quota unit per call
   - **Called:** Every check interval

3. **Videos (Check if Live):**
   - `GET https://www.googleapis.com/youtube/v3/videos?part=liveStreamingDetails,snippet&id={video_id}`
   - Checks if the most recent video is currently live and gets stream details
   - **Cost:** 1 quota unit per call
   - **Called:** Every check interval

**Total per check:** 3 quota units  
**Daily capacity:** ~3,300 checks with standard 10,000 unit quota  
**Check every 5 min:** Uses ~288 checks/day (~864 units) - plenty of headroom!

#### Alternative Implementation (Standard - 101 units per check)

If you need 100% reliable detection regardless of upload patterns:

1. **Search (Channel Resolution - once per session):**
   - `GET https://www.googleapis.com/youtube/v3/search`
   - Resolves username/handle to channel ID
   - **Cost:** 100 quota units per call
   - **Called:** Once on startup (cached)

2. **Search (Live Streams - every check):**
   - `GET https://www.googleapis.com/youtube/v3/search?channelId={id}&eventType=live`
   - Searches for active live streams on channel
   - **Cost:** 100 quota units per call
   - **Called:** Every check interval

3. **Videos (Stream Details):**
   - `GET https://www.googleapis.com/youtube/v3/videos?id={video_id}`
   - Gets stream title, viewer count, thumbnails
   - **Cost:** 1 quota unit per call
   - **Called:** When stream is detected as live

**Total per check:** 101 quota units  
**Daily capacity:** ~99 checks with standard 10,000 unit quota  
**Check every 5 min:** Would require ~288 checks/day (~29,088 units) - **exceeds quota!**

### Rate Limits

**Official Limits:**
- 10,000 quota units per day
- Resets midnight Pacific Time
- No per-minute limits

**Stream Daemon Usage Examples:**

| Check Interval | Checks/Day | Quota Used | Status |
|----------------|------------|------------|--------|
| 5 minutes | 288 | ~28,800 | ⚠️ Over quota |
| 10 minutes | 144 | ~14,400 | ⚠️ Over quota |
| 15 minutes | 96 | ~9,600 | ✅ Under quota |
| 30 minutes | 48 | ~4,800 | ✅ Well under |

**Recommendation:** Use 15+ minute intervals unless you need faster detection.

### API Documentation

- **YouTube Data API:** [https://developers.google.com/youtube/v3](https://developers.google.com/youtube/v3)
- **Quota Calculator:** [https://developers.google.com/youtube/v3/determine_quota_cost](https://developers.google.com/youtube/v3/determine_quota_cost)
- **API Status:** [https://status.cloud.google.com/](https://status.cloud.google.com/)

---

## Security Best Practices

### DO:
- ✅ Store API key in secrets manager
- ✅ Restrict API key to YouTube Data API v3 only
- ✅ Use separate keys for dev/staging/production
- ✅ Monitor quota usage regularly

### DON'T:
- ❌ Commit API key to git
- ❌ Share API key in screenshots/logs
- ❌ Use production key in development
- ❌ Leave API key unrestricted

### API Key Rotation

**How to rotate API keys:**

1. **Create new API key** in Google Cloud Console
2. **Update secrets manager:**
   ```bash
   doppler secrets set YOUTUBE_API_KEY="new_key_here"
   ```
3. **Restart Stream Daemon**
4. **Delete old API key** from Google Cloud Console
   - Credentials → API Keys → Delete

---

## Advanced Configuration

### Using Channel ID Directly

If you know your channel ID, skip username resolution:

```bash
# Skip username lookup (saves API quota)
YOUTUBE_CHANNEL_ID=UCXuqSBlHAE6Xw-yeJA0Tunw
YOUTUBE_USERNAME=@LinusTechTips  # Still used for messages/URLs
```

**Finding Your Channel ID:**

**Method 1: YouTube Studio**
1. Go to [YouTube Studio](https://studio.youtube.com/)
2. Settings → Channel → Advanced settings
3. Look for "Channel ID"

**Method 2: Page Source**
1. Go to your channel page
2. View page source (Ctrl+U / Cmd+U)
3. Search for `"channelId"`
4. Copy the ID (starts with `UC`)

**Method 3: URL**
- If your URL is `youtube.com/channel/UCxxxxx`, that's your channel ID

### Multiple YouTube Channels

To monitor multiple YouTube channels, run separate instances:

```bash
# Instance 1
YOUTUBE_USERNAME=@MainChannel
YOUTUBE_CHANNEL_ID=UC11111111

# Instance 2  
YOUTUBE_USERNAME=@VODChannel
YOUTUBE_CHANNEL_ID=UC22222222
```

### Optimizing for Quota

**Best practices to minimize quota usage:**

1. **Set channel ID directly** - saves 100 units per startup
2. **Increase check intervals** - 15+ minutes recommended
3. **Use conditional logic** - check less often when unlikely to be live (e.g., midnight-6am)
4. **Monitor quota usage** - Google Cloud Console dashboard

---

## See Also

- [Twitch Setup Guide](twitch.md) - Twitch monitoring
- [Kick Setup Guide](kick.md) - Kick streaming platform
- [Discord Setup Guide](../social/discord.md) - Discord notifications
- [Messages Guide](../../features/custom-messages.md) - Custom message formatting
- [Secrets Management](../../configuration/secrets.md) - Doppler/AWS/Vault setup
- [Quick Start Guide](../../getting-started/quickstart.md) - Initial setup

---

**Last Updated:** 2024
