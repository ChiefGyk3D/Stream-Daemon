# Platform Configuration Guide

## Overview

Stream Daemon is a universal streaming-to-social automation tool that supports:

**Streaming Platforms (Monitor):**
- 🟣 **Twitch** - Full async API with OAuth
- 📺 **YouTube Live** - Auto-resolves @handle to channel ID
- ⚡ **Kick** - OAuth authentication with public API fallback

**Social Platforms (Post):**
- 🐘 **Mastodon** - Any Mastodon-compatible instance
- 🦋 **Bluesky** - AT Protocol native support
- 💬 **Discord** - Webhook with role mentions

This guide covers platform-specific configuration, credential setup, and features.

---

## 🎮 Streaming Platforms

### Twitch

**Requirements:**
- Twitch Developer Application
- Client ID and Client Secret

**Setup:**

1. **Create Twitch Application:**
   - Go to [Twitch Developer Console](https://dev.twitch.tv/console/apps)
   - Click **"Register Your Application"**
   - **Name:** "Stream Daemon" (or your choice)
   - **OAuth Redirect URL:** `http://localhost` (required but not used by Stream Daemon)
   - **Category:** Choose relevant category (e.g., "Application Integration")
   - Click **"Create"**

2. **Get Credentials:**
   - After creation, you'll see your application listed
   - Copy your **Client ID**
   - Click **"New Secret"** to generate a **Client Secret**
   - **Important:** Copy the secret immediately - you can't view it again!

3. **Configure Stream Daemon:**

```bash
# In .env
TWITCH_ENABLE=True
TWITCH_USERNAME=your_twitch_username

# Option 1: Direct credentials (not recommended for production)
TWITCH_CLIENT_ID=your_client_id_here
TWITCH_CLIENT_SECRET=your_client_secret_here

# Option 2: Use secrets manager (recommended)
# Comment out credentials above, configure in Doppler/AWS/Vault
# See DOPPLER_GUIDE.md for details
```

**Features:**
- ✅ Async API support (twitchAPI v4+)
- ✅ OAuth 2.0 authentication
- ✅ Real-time stream status
- ✅ Viewer count detection
- ✅ Stream title extraction

**API Rate Limits:** 800 requests per minute (handled automatically)

---

### YouTube Live

**Requirements:**
- Google Cloud Project
- YouTube Data API v3 enabled
- API Key

**Setup:**

1. **Create Google Cloud Project:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Click **"Create New Project"**
   - **Name:** "Stream Daemon" (or your choice)
   - Click **"Create"** and select the project

2. **Enable YouTube Data API v3:**
   - Go to **"APIs & Services"** → **"Library"**
   - Search for **"YouTube Data API v3"**
   - Click on it and click **"Enable"**

3. **Create API Key:**
   - Go to **"APIs & Services"** → **"Credentials"**
   - Click **"Create Credentials"** → **"API Key"**
   - Copy the generated API key
   - **(Optional but recommended)** Click **"Restrict Key"**:
     - Under "API restrictions", select "Restrict key"
     - Check **"YouTube Data API v3"**
     - This improves security by limiting what the key can access

4. **Configure Stream Daemon:**

```bash
# In .env
YOUTUBE_ENABLE=True
YOUTUBE_USERNAME=@YourHandle

# Channel ID is OPTIONAL - Stream Daemon auto-resolves from username!
# Only set this if you want to skip the channel lookup (slightly faster)
# YOUTUBE_CHANNEL_ID=UCvFY4KyqVBuYd7JAl3NRyiQ

# Option 1: Direct API key (not recommended for production)
YOUTUBE_API_KEY=AIzaSyABC123XYZ789...

# Option 2: Use secrets manager (recommended)
# Comment out API key above, configure in Doppler/AWS/Vault
```

**Username Formats Supported:**
- `@YourHandle` (recommended) - Modern YouTube handles
- `YourChannelName` - Legacy channel names

**Features:**
- ✅ Auto-resolves channel ID from @handle or username
- ✅ No manual channel ID lookup needed
- ✅ Stream status detection
- ✅ Concurrent viewer count
- ✅ Stream title extraction

**API Rate Limits:** 10,000 quota units/day (each check uses ~3 units)

---

### Kick

**Requirements:**
- Kick account
- (Optional) Kick Developer Application for OAuth

**Setup:**

**Option A: Public API (No Authentication):**

```bash
# In .env
KICK_ENABLE=True
KICK_USERNAME=your_kick_username

# No credentials needed!
```

- ✅ Works immediately, no setup
- ⚠️ Limited rate limits
- ⚠️ May be less reliable

**Option B: OAuth Authentication (Recommended):**

1. **Get Kick API Credentials:**
   - Login to [https://kick.com](https://kick.com)
   - Make sure 2FA is enabled: **Settings** → **Security**
   - Go to **Settings** → **Developer**
   - Create a new application
   - **Scopes/Permissions:** Select **"Read Access"** (required for stream status checks)
   - Copy your **Client ID** and **Client Secret**

2. **Configure Stream Daemon:**

```bash
# In .env
KICK_ENABLE=True
KICK_USERNAME=your_kick_username

# Option 1: Direct credentials (not recommended for production)
KICK_CLIENT_ID=your_kick_client_id
KICK_CLIENT_SECRET=your_kick_client_secret

# Option 2: Use secrets manager (recommended)
# Comment out credentials above, configure in Doppler/AWS/Vault
```

**Features:**
- ✅ OAuth 2.0 client credentials flow
- ✅ Automatic fallback to public API
- ✅ Stream status detection
- ✅ Viewer count
- ✅ Stream title extraction

**API Rate Limits:** Higher with OAuth authentication

---

## 📱 Social Platforms

### Mastodon

**Requirements:**
- Mastodon account on any instance
- Developer application credentials

**Setup:**

1. **Create Mastodon Application:**
   - Login to your Mastodon instance (e.g., mastodon.social, fosstodon.org, etc.)
   - Go to **Settings** → **Development**
   - Click **"New Application"**
   - Application name: "Stream Daemon"
   - **Scopes/Permissions:** 
     - Check `read:accounts` (required - allows verifying your credentials)
     - Check `write:statuses` (required - allows posting status updates)
     - Check `write:media` (optional - if you plan to attach images/videos)
   - Redirect URI: Leave default or use `urn:ietf:wg:oauth:2.0:oob`
   - Click **"Submit"**

2. **Get Credentials:**
   - After creating, you'll see three important values on the Mastodon page:
     - **"Client key"** → Copy this as `MASTODON_CLIENT_ID`
     - **"Client secret"** → Copy this as `MASTODON_CLIENT_SECRET`
     - **"Your access token"** → Copy this as `MASTODON_ACCESS_TOKEN`
   - Copy all three - you need ALL of them!

3. **Configure Stream Daemon:**

```bash
# In .env
MASTODON_ENABLE_POSTING=True
MASTODON_APP_NAME=StreamDaemon
MASTODON_API_BASE_URL=https://mastodon.social  # Your instance URL

# Option 1: Direct credentials (not recommended for production)
MASTODON_CLIENT_ID=your_client_id
MASTODON_CLIENT_SECRET=your_client_secret
MASTODON_ACCESS_TOKEN=your_access_token

# Option 2: Use secrets manager (recommended)
# Comment out credentials above, configure in Doppler/AWS/Vault
```

**Compatible Instances:**
- Mastodon (mastodon.social, fosstodon.org, etc.)
- Glitch-soc
- Hometown
- Any Mastodon API-compatible instance

**Features:**
- ✅ Works with any Mastodon instance
- ✅ Respects character limits automatically
- ✅ Posts with public visibility
- ✅ Supports custom messages per platform

**Important:** You need **all three credentials** (client_id, client_secret, and access_token) for Mastodon to work.

---

### Bluesky

**Requirements:**
- Bluesky account
- App Password (NOT your main password!)

**Setup:**

1. **Create App Password:**
   - Go to [Bluesky Settings](https://bsky.app/settings/app-passwords)
   - Click "Add App Password"
   - Name: "Stream Daemon"
   - Copy the generated password
   - **Important:** This is NOT your account password!

2. **Configure Stream Daemon:**

```bash
# In .env
BLUESKY_ENABLE_POSTING=True
BLUESKY_HANDLE=yourname.bsky.social

# Option 1: Direct app password (not recommended for production)
BLUESKY_APP_PASSWORD=your-app-password-here

# Option 2: Use secrets manager (recommended)
# Comment out app password above, configure in Doppler/AWS/Vault
```

**Features:**
- ✅ Native AT Protocol support
- ✅ Secure app password authentication
- ✅ Supports custom messages per platform
- ✅ Automatic post formatting

**Security Note:** App passwords can be revoked anytime from Bluesky settings without changing your main password.

**Developer Note:** Bluesky's app password approach is functional but less than ideal. We eagerly await proper OAuth 2.0 support for the masses. Currently, OAuth is only available to those who self-host their own Personal Data Servers (PDS), which is overkill for most users. Once Bluesky releases OAuth for everyone, Stream Daemon will be updated to use it!

---

### Discord

**Requirements:**
- Discord Server (admin or "Manage Webhooks" permission)
- Webhook URL

**Setup:**

1. **Create Discord Webhook:**
   - Go to your Discord server
   - Right-click the channel where you want stream announcements
   - Click **"Edit Channel"** → **"Integrations"** → **"Webhooks"**
   - Click **"Create Webhook"** (or **"New Webhook"**)
   - Customize webhook name and avatar (optional)
   - Click **"Copy Webhook URL"**
   - **Important:** Keep this URL secret - anyone with it can post to your channel!

2. **Get Role IDs (Optional, for mentions):**
   - Enable Developer Mode: **User Settings** → **Advanced** → **Developer Mode** (toggle ON)
   - Right-click any role in your server's role list → **"Copy Role ID"**
   - Paste the role ID into your `.env` for the corresponding platform
   - Do this for each streaming platform you want to mention a specific role

3. **Configure Stream Daemon:**

```bash
# In .env
DISCORD_ENABLE_POSTING=True

# Option 1: Direct webhook URL (not recommended for production)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/123456789/abcdefg...

# Option 2: Use secrets manager (recommended)
# Comment out webhook URL above, configure in Doppler/AWS/Vault

# Optional: Role mentions (requires Developer Mode to get IDs)
# When Twitch goes live, mention this role:
DISCORD_ROLE_TWITCH=1234567890123456789
# When YouTube goes live, mention this role:
DISCORD_ROLE_YOUTUBE=1234567890123456789
# When Kick goes live, mention this role:
DISCORD_ROLE_KICK=1234567890123456789
```

**Features:**
- ✅ Webhook-based posting (no bot required)
- ✅ Platform-specific role mentions
- ✅ Custom messages per streaming platform
- ✅ Rich embeds support

**Role Mention Behavior:**
- When Twitch goes live → Mentions `DISCORD_ROLE_TWITCH`
- When YouTube goes live → Mentions `DISCORD_ROLE_YOUTUBE`
- When Kick goes live → Mentions `DISCORD_ROLE_KICK`
- You can use the same role ID for all platforms, or different ones
- Leave blank (or don't set) to skip role mentions

**Tips:**
- Use `@everyone` role ID for server-wide notifications (not recommended)
- Create platform-specific roles like "Twitch Notifications" for better control
- Test the webhook after creation by sending a test message

---

## 🚧 Coming Soon

The following platforms are planned for future releases. This documentation will be updated when they're implemented:

### Matrix Protocol

**Status:** Planned  
**What it is:** Decentralized, open-source messaging protocol  
**Use case:** Post stream announcements to Matrix rooms

Planned features:
- Matrix homeserver integration
- Room-specific announcements
- End-to-end encryption support

### Enhanced Discord Features

**Status:** Planned  
**What's coming:**
- Discord bot integration (beyond webhooks)
- Rich embed customization
- Thread support
- Reaction-based features

### LLM Integration

**Status:** Planned  
**What it is:** AI-powered message generation  
**Use case:** Automatically generate engaging, context-aware stream announcements

Planned features:
- OpenAI, Anthropic, or local LLM support
- Dynamic message generation based on stream context
- Platform-optimized messaging
- Tone and style customization

**Note:** These features are not yet available. Check back for updates or watch the GitHub repository for release announcements!

---

## 🎯 Different Usernames Per Platform

You can monitor different channels on each streaming platform:

```bash
# Monitor different streamers or your different accounts
TWITCH_USERNAME=ProGamer123
YOUTUBE_USERNAME=ProGamer123Official  
KICK_USERNAME=ProGamer_Kick
```

**Use Cases:**
1. **Same creator, different names** - Your accounts have different usernames
2. **Multi-user setup** - Monitor different streamers on different platforms
3. **Multi-channel** - Monitor main channel vs VOD channel

---

## 📝 Platform-Specific Messages

Stream Daemon supports different messages for each streaming platform using INI-style sections in `messages.txt` and `end_messages.txt`.

**See [MESSAGES_FORMAT.md](MESSAGES_FORMAT.md) for complete message customization guide.**

### Quick Example

```ini
# messages.txt
[DEFAULT]
🔴 Now LIVE! Come watch: {stream_title}

[TWITCH]
🟣 Live on Twitch! {stream_title}
Watch: https://twitch.tv/{username}

[YOUTUBE]
📺 YouTube LIVE! {stream_title}
Watch: https://youtube.com/@{username}/live

[KICK]
⚡ Streaming on Kick! {stream_title}
Watch: https://kick.com/{username}
```

**Variables available:**
- `{stream_title}` - Current stream title
- `{username}` - Platform-specific username

**Configuration:**
```bash
# Use platform-specific sections when available
MESSAGES_USE_PLATFORM_SPECIFIC_MESSAGES=True

# Always use [DEFAULT] section for all platforms
MESSAGES_USE_PLATFORM_SPECIFIC_MESSAGES=False
```

---

## 🔒 Secrets Management

Stream Daemon supports multiple ways to manage credentials:

### Option 1: Doppler (Recommended)

**Why:** Free, simple, no infrastructure needed

```bash
SECRETS_SECRET_MANAGER=doppler
DOPPLER_TOKEN=dp.st.your_token_here
```

**See [DOPPLER_GUIDE.md](DOPPLER_GUIDE.md) for complete setup.**

### Option 2: AWS Secrets Manager

**Why:** Already using AWS

```bash
SECRETS_SECRET_MANAGER=aws
SECRETS_AWS_TWITCH_SECRET_NAME=prod/stream-daemon/twitch
# etc...
```

### Option 3: HashiCorp Vault

**Why:** Enterprise, self-hosted

```bash
SECRETS_SECRET_MANAGER=vault
SECRETS_VAULT_URL=https://vault.example.com
SECRETS_VAULT_TOKEN=your_vault_token
# etc...
```

### Option 4: Environment Variables (Not Recommended for Production)

```bash
# Direct credentials in .env (not recommended)
TWITCH_CLIENT_ID=abc123
TWITCH_CLIENT_SECRET=xyz789
```

**Important:** When using a secrets manager, **comment out** all credentials in `.env` so they're fetched from the secrets manager instead.

---

## 🧪 Testing Your Configuration

Stream Daemon includes comprehensive tests for all platforms:

```bash
# Test all platforms
python3 tests/test_doppler_all.py

# Test individual streaming platforms
python3 tests/test_doppler_twitch.py
python3 tests/test_doppler_youtube.py
python3 tests/test_doppler_kick.py

# Social platforms are tested as part of daemon execution
```

**Tests validate:**
- ✅ Credential fetching from secrets manager
- ✅ API authentication
- ✅ Stream detection functionality
- ✅ Proper error handling

---

## 🔍 Troubleshooting

### Twitch: "Invalid Client ID"
- Verify Client ID/Secret are correct
- Check application is active in Twitch Developer Console
- Ensure OAuth redirect URL is set (even if not used)

### YouTube: "API Key Invalid"
- Verify YouTube Data API v3 is enabled
- Check API key hasn't been restricted to wrong APIs
- Confirm quota hasn't been exceeded (10,000 units/day)

### YouTube: "Channel Not Found"
- Check username format: Use `@Handle` for handles
- Try legacy username format without `@`
- Verify channel exists and is public
- Try setting `YOUTUBE_CHANNEL_ID` directly if auto-resolve fails

### Kick: "Authentication Failed"
- Verify Client ID/Secret if using OAuth
- Try without credentials (public API fallback)
- Check Kick Developer Portal for API status

### Mastodon: "Unauthorized"
- Verify all three credentials (client_id, client_secret, access_token)
- Check application has `write:statuses` permission
- Confirm instance URL is correct (https://...)

### Bluesky: "Invalid Credentials"
- Ensure you're using **app password**, not main password
- Check handle format: `yourname.bsky.social`
- Verify app password hasn't been revoked

### Discord: "Webhook Not Found"
- Verify webhook URL is complete
- Check webhook wasn't deleted from Discord
- Ensure URL starts with `https://discord.com/api/webhooks/`

### "Secrets Not Found" (any platform)
- If using secrets manager: Check credentials are commented out in `.env`
- Verify secrets manager is configured correctly
- See [DOPPLER_GUIDE.md](DOPPLER_GUIDE.md) for Doppler-specific troubleshooting

---

## 📚 Additional Resources

- [Doppler Setup Guide](DOPPLER_GUIDE.md) - Complete Doppler integration guide
- [Messages Format Guide](MESSAGES_FORMAT.md) - Customize your announcements
- [Test Suite Documentation](tests/README.md) - Running and understanding tests
- [Docker Setup](Docker/README.md) - Running in containers
- [Main README](README.md) - Project overview

---

## ❓ FAQ

**Q: Can I monitor multiple channels on the same platform?**  
A: Not currently. Stream Daemon monitors one channel per platform. You can run multiple instances to monitor multiple channels.

**Q: Do I need all three streaming platforms enabled?**  
A: No! Enable only the platforms you want. Minimum one streaming platform required.

**Q: Do I need all social platforms?**  
A: No! Enable only where you want to post. Minimum one social platform required.

**Q: Can I use YouTube without Channel ID?**  
A: Yes! Stream Daemon auto-resolves channel ID from your @handle or username. Channel ID is optional.

**Q: Does Kick work without authentication?**  
A: Yes! Public API fallback works without credentials, though authenticated API is more reliable.

**Q: Can I post to multiple Mastodon instances?**  
A: Not currently. One instance per platform. Run multiple instances for multiple destinations.

**Q: How often does Stream Daemon check for streams?**  
A: Every `SETTINGS_CHECK_INTERVAL` minutes (default: 5 minutes) when offline. Checks more frequently when live.

**Q: Will it post every time it checks?**  
A: No! It only posts once when stream goes live, and optionally once when stream ends. Not on every check.

**Q: Can I test without going live?**  
A: Yes! Use the test suite (`tests/test_doppler_*.py`) to validate configuration without actually posting.

---

**Need help? Open an issue on GitHub or check the other documentation files!
TWITCH_USERNAME=streamer_alice
YOUTUBE_USERNAME=creator_bob
KICK_USERNAME=gamer_charlie
```

**3. Multi-Channel (Same Person):**
```bash
TWITCH_USERNAME=MainChannel
YOUTUBE_USERNAME=MainChannelVODs
KICK_USERNAME=MainChannel
```

---

## Platform-Specific Messages

### How It Works

Stream Daemon uses a **fallback system** for messages:

1. **First choice:** Platform-specific message file (e.g., `messages_twitch.txt`)
2. **Fallback:** Global message file (`messages.txt`)

This means you can:
- Use **global messages** for all platforms (simplest)
- Use **platform-specific messages** for custom branding (recommended)
- **Mix both** - some platforms custom, others use global

### File Structure

**Platform-Specific Files:**
```
messages_twitch.txt          # Twitch live announcements
end_messages_twitch.txt      # Twitch stream ended messages

messages_youtube.txt         # YouTube live announcements  
end_messages_youtube.txt     # YouTube stream ended messages

messages_kick.txt            # Kick live announcements
end_messages_kick.txt        # Kick stream ended messages
```

**Global Files (Fallback):**
```
messages.txt                 # Used if platform-specific file doesn't exist
end_messages.txt             # Used if platform-specific file doesn't exist
```

### Message Format

Messages support these variables:

- `{stream_title}` - The title of the stream
- `{username}` - The streamer's username on that platform
- `{platform}` - The platform name (Twitch, YouTube, or Kick)

**Best Practice:** Always include the stream URL so followers can click directly to watch!

**Platform URLs:**
- **Twitch:** `https://twitch.tv/{username}`
- **YouTube:** `https://youtube.com/@{username}/live`
- **Kick:** `https://kick.com/{username}`

### Example: Platform-Specific Messages

**messages_twitch.txt:**
```
🔴 LIVE on Twitch! {stream_title} - https://twitch.tv/{username}
Now streaming on Twitch: {stream_title} - Join at https://twitch.tv/{username}
Going live with {stream_title}! Drop by on Twitch! 🎮 https://twitch.tv/{username}
```

**messages_youtube.txt:**
```
📺 YouTube LIVE! {stream_title} - https://youtube.com/@{username}/live
Streaming now on YouTube: {stream_title} - Subscribe and watch! https://youtube.com/@{username}/live
New YouTube stream: {stream_title} 🎥 https://youtube.com/@{username}/live
```

**messages_kick.txt:**
```
🟢 LIVE on Kick! {stream_title} - https://kick.com/{username}
Kick stream starting: {stream_title} - Watch at https://kick.com/{username}
Now live on Kick with {stream_title}! ⚡ https://kick.com/{username}
```

### Example: Global Messages (Simpler)

If you don't want platform-specific branding, use one file:

**messages.txt:**
```
Now streaming: {stream_title} on {platform}! - https://twitch.tv/{username}
LIVE on {platform}: {stream_title} - https://twitch.tv/{username}
{username} is live on {platform} with {stream_title}! https://twitch.tv/{username}
```

**Note:** When using global messages, the URL will default to Twitch format. For multi-platform use, platform-specific files are recommended.

---

## Configuration Examples

### Example 1: Platform-Specific Everything

```bash
# Different usernames
TWITCH_USERNAME=GamerAlice
YOUTUBE_USERNAME=AliceGaming
KICK_USERNAME=AliceStreams

# Platform-specific message files (auto-detected)
# Just create the files, no config needed:
# - messages_twitch.txt
# - messages_youtube.txt  
# - messages_kick.txt
# - end_messages_twitch.txt
# - end_messages_youtube.txt
# - end_messages_kick.txt
```

### Example 2: Same Username, Different Messages

```bash
# Same username across platforms
TWITCH_USERNAME=ProStreamer
YOUTUBE_USERNAME=ProStreamer
KICK_USERNAME=ProStreamer

# But different branding per platform via message files
# messages_twitch.txt: "🔴 LIVE on Twitch..."
# messages_youtube.txt: "📺 YouTube stream..."
# messages_kick.txt: "🟢 Kick is live..."
```

### Example 3: Mixed Approach

```bash
# Different usernames
TWITCH_USERNAME=MainChannel
YOUTUBE_USERNAME=MainChannelVODs

# Custom messages for Twitch only
# - messages_twitch.txt (custom Twitch branding)
# - messages.txt (fallback for YouTube and Kick)
```

### Example 4: Simplest (Global Messages)

```bash
# Same username
TWITCH_USERNAME=MyChannel
YOUTUBE_USERNAME=MyChannel
KICK_USERNAME=MyChannel

# Only use global messages
# - messages.txt (used for all platforms)
# - end_messages.txt (used for all platforms)
```

---

## Advanced: Custom File Paths

You can override the default file paths via environment variables:

```bash
# Override Twitch message files
MESSAGES_TWITCH_MESSAGES_FILE=/custom/path/twitch_live.txt
MESSAGES_TWITCH_END_MESSAGES_FILE=/custom/path/twitch_end.txt

# Override YouTube message files
MESSAGES_YOUTUBE_MESSAGES_FILE=/custom/path/youtube_live.txt
MESSAGES_YOUTUBE_END_MESSAGES_FILE=/custom/path/youtube_end.txt

# Override Kick message files
MESSAGES_KICK_MESSAGES_FILE=/custom/path/kick_live.txt
MESSAGES_KICK_END_MESSAGES_FILE=/custom/path/kick_end.txt
```

---

## Platform-Specific Social Posts

When a stream goes live, Stream Daemon posts **separately for each streaming platform**:

### Scenario: Live on Both Twitch and YouTube

**If both are live simultaneously, you get TWO posts:**

```
Post 1: "🔴 LIVE on Twitch! Building a game engine"
Post 2: "📺 YouTube LIVE! Building a game engine"
```

Each post can:
- Have different wording (via platform-specific message files)
- Mention different Discord roles (via `DISCORD_ROLE_TWITCH`, `DISCORD_ROLE_YOUTUBE`)
- Be threaded when stream ends

### Benefits

✅ **Clear Notifications** - Followers know exactly where you're streaming  
✅ **Platform Branding** - Match each platform's culture and emoji style  
✅ **Multi-Stream Support** - Properly handle simultaneous streams  
✅ **Targeted Audiences** - Different messages for different communities

---

## Best Practices

### 1. Platform-Appropriate Emojis

**Twitch:** 🔴 🎮 💜 (purple for Twitch brand)  
**YouTube:** 📺 🎥 ▶️ 🔴 (red for YouTube)  
**Kick:** 🟢 ⚡ 💚 (green for Kick brand)

### 2. Include Platform Links

**Always include clickable URLs!** Makes it easy for followers to jump directly to the stream.

```
# Twitch
🔴 LIVE on Twitch! {stream_title} - https://twitch.tv/{username}

# YouTube  
📺 YouTube stream: {stream_title} - https://youtube.com/@{username}/live

# Kick
🟢 Streaming on Kick! {stream_title} - https://kick.com/{username}
```

### 3. Platform Culture

**Twitch:** More casual, gaming-focused  
```
🔴 Going live! Time to grind in {stream_title} 🎮 https://twitch.tv/{username}
```

**YouTube:** More professional, varied content  
```
📺 New video stream: {stream_title} - Don't forget to like & subscribe! https://youtube.com/@{username}/live
```

**Kick:** Community-focused, energetic  
```
🟢 LIVE NOW on Kick! {stream_title} - Let's gooooo! ⚡ https://kick.com/{username}
```

### 4. Variety in Messages

Add 5-10 different messages per file so posts don't feel repetitive:

```
# messages_twitch.txt
🔴 LIVE on Twitch! {stream_title} - https://twitch.tv/{username}
Going live with {stream_title}! 🎮 https://twitch.tv/{username}
Twitch stream starting NOW: {stream_title} - https://twitch.tv/{username}
🔴 Time to stream! {stream_title} on Twitch - https://twitch.tv/{username}
Live on Twitch: {stream_title} - Come hang out! 💜 https://twitch.tv/{username}
```

---

## Troubleshooting

### "No messages found for [Platform]"

**Problem:** Neither platform-specific nor global message file exists.

**Solution:** Create at least one of these:
- `messages_twitch.txt` (platform-specific) OR
- `messages.txt` (global fallback)

### Messages Look Wrong

**Check:**
1. File has actual content (not empty)
2. Variables are correct: `{stream_title}`, `{username}`, `{platform}`
3. No blank lines at start (first line should be a message)

### Want Same Messages for All

**Solution:** Just use global files, don't create platform-specific ones:
```bash
# Only create these two files:
messages.txt
end_messages.txt
```

Stream Daemon will use them for all platforms automatically.

---

## Migration from Old Setup

If you have existing `messages.txt` and `end_messages.txt`:

**Option 1: Keep using global (no changes needed)**
- Everything works as before
- Same messages for all platforms

**Option 2: Split into platform-specific**
```bash
# Copy your existing messages
cp messages.txt messages_twitch.txt
cp messages.txt messages_youtube.txt
cp messages.txt messages_kick.txt

# Now customize each file
nano messages_twitch.txt  # Add Twitch branding
nano messages_youtube.txt # Add YouTube branding
nano messages_kick.txt    # Add Kick branding
```

---

## Summary

| Feature | Configuration | Benefit |
|---------|--------------|---------|
| **Different Usernames** | `TWITCH_USERNAME=`, `YOUTUBE_USERNAME=`, `KICK_USERNAME=` | Monitor different channels per platform |
| **Platform-Specific Messages** | `messages_twitch.txt`, `messages_youtube.txt`, etc. | Custom branding per platform |
| **Global Fallback** | `messages.txt`, `end_messages.txt` | Simple setup, same messages everywhere |
| **Per-Platform Posts** | Automatic when multiple platforms are live | Clear notifications about where to watch |
| **Discord Role Mentions** | `DISCORD_ROLE_TWITCH=`, `DISCORD_ROLE_YOUTUBE=` | Targeted notifications |

Stream Daemon is **fully flexible** - use as much or as little customization as you need!
