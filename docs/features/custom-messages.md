# Custom Messages Guide

## Overview

Stream Daemon uses a **flexible message system** that allows you to customize announcements for each streaming platform. Messages support variables, platform-specific sections, and fallback behavior.

**Message Files:**
- `messages.txt` - Stream start announcements
- `end_messages.txt` - Stream end messages

Both files use an **INI-style format** with sections for platform-specific customization.

---

## Quick Start

### Basic Setup

Create `messages.txt` in your project root:

```ini
[DEFAULT]
🔴 Now LIVE! Come watch: {stream_title}
Streaming {stream_title} right now!
{username} just went live!
```

Create `end_messages.txt`:

```ini
[DEFAULT]
Thanks for watching! See you next time! 💜
Stream ended! Catch the VOD!
That's a wrap! Thanks for joining!
```

Stream Daemon will:
1. Pick a random message from the file
2. Replace variables (`{stream_title}`, `{username}`)
3. Post to your social platforms

---

## File Format

### INI-Style Sections

```ini
# Comments start with #
# Blank lines are ignored

[DEFAULT]
Generic message for all platforms
Another generic message
Third message option

[TWITCH]
Twitch-specific message
https://twitch.tv/{username}

[YOUTUBE]
YouTube-specific message
https://youtube.com/@{username}/live

[KICK]
Kick-specific message
https://kick.com/{username}
```

### How Sections Work

Stream Daemon follows this priority:

1. **Platform-specific section** (e.g., `[TWITCH]`)
   - If found, uses those messages for that platform
2. **DEFAULT section** (fallback)
   - If no platform section exists, uses DEFAULT
3. **Error if neither exists**
   - At minimum, you need `[DEFAULT]`

---

## Variables

All messages support these variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `{stream_title}` | Current stream title | `"Elden Ring Boss Rush"` |
| `{username}` | Platform-specific username | `"chiefgyk3d"` |
| `{platform}` | Streaming platform name | `"Twitch"`, `"YouTube"`, `"Kick"` |

### Variable Usage Examples

**Simple:**
```ini
[DEFAULT]
{username} is live! Playing: {stream_title}
```
Output: `"chiefgyk3d is live! Playing: Elden Ring Boss Rush"`

**With URLs:**
```ini
[TWITCH]
🟣 {username} is streaming on Twitch!
{stream_title}
Watch: https://twitch.tv/{username}
```

**Multi-line:**
```ini
[YOUTUBE]
📺 YouTube LIVE!
{username} is streaming: {stream_title}

Subscribe and watch: https://youtube.com/@{username}/live
```

---

## Configuration Modes

### Mode 1: Platform-Specific (Default)

**Configuration:**
```bash
# In .env
MESSAGES_USE_PLATFORM_SPECIFIC_MESSAGES=True
```

**Behavior:**
- Twitch goes live → Uses `[TWITCH]` messages (or `[DEFAULT]` if no `[TWITCH]`)
- YouTube goes live → Uses `[YOUTUBE]` messages (or `[DEFAULT]` if no `[YOUTUBE]`)
- Kick goes live → Uses `[KICK]` messages (or `[DEFAULT]` if no `[KICK]`)

**Example `messages.txt`:**
```ini
[DEFAULT]
🔴 LIVE! {stream_title}

[TWITCH]
🟣 Twitch stream LIVE! {stream_title}
https://twitch.tv/{username}

[YOUTUBE]
📺 YouTube stream starting! {stream_title}
https://youtube.com/@{username}/live

# Kick will use [DEFAULT] since no [KICK] section
```

**Result:**
- Twitch: `"🟣 Twitch stream LIVE! Elden Ring"`
- YouTube: `"📺 YouTube stream starting! Elden Ring"`
- Kick: `"🔴 LIVE! Elden Ring"` (uses DEFAULT)

---

### Mode 2: Unified (All Platforms Same)

**Configuration:**
```bash
# In .env
MESSAGES_USE_PLATFORM_SPECIFIC_MESSAGES=False
```

**Behavior:**
- **Always** uses `[DEFAULT]` section
- Platform-specific sections are **ignored**
- Same message on every platform

**Example `messages.txt`:**
```ini
[DEFAULT]
🔴 LIVE NOW! {stream_title}
{username} is streaming!

[TWITCH]
This will be ignored!

[YOUTUBE]
This will also be ignored!
```

**Result:** All platforms use `[DEFAULT]` messages.

**When to use:**
- Want same branding across all platforms
- Simpler message management
- Don't need platform-specific URLs

---

## Configuration Reference

### Environment Variables

Add to your `.env` file:

```bash
# ================================================
# MESSAGE CONFIGURATION
# ================================================

# Message files (INI format)
MESSAGES_MESSAGES_FILE=messages.txt
MESSAGES_END_MESSAGES_FILE=end_messages.txt

# Use platform-specific sections or always [DEFAULT]
# True = Use [TWITCH], [YOUTUBE], [KICK] sections when available
# False = Always use [DEFAULT] for all platforms
MESSAGES_USE_PLATFORM_SPECIFIC_MESSAGES=True

# Post "stream ended" messages when streams end
MESSAGES_POST_END_STREAM_MESSAGE=True
```

### Custom File Paths

Want to use different file names or locations?

```bash
# Custom paths
MESSAGES_MESSAGES_FILE=/path/to/custom_live_messages.txt
MESSAGES_END_MESSAGES_FILE=/path/to/custom_end_messages.txt
```

---

## Advanced Examples

### Example 1: Platform URLs Only

Want same message, but add platform-specific URLs?

```ini
[DEFAULT]
🔴 LIVE NOW! {stream_title}

[TWITCH]
🔴 LIVE NOW! {stream_title}
https://twitch.tv/{username}

[YOUTUBE]
🔴 LIVE NOW! {stream_title}
https://youtube.com/@{username}/live

[KICK]
🔴 LIVE NOW! {stream_title}
https://kick.com/{username}
```

### Example 2: Different Tone Per Platform

```ini
[DEFAULT]
Stream is live! Playing {stream_title}

[TWITCH]
🟣 LET'S GOOOO! {stream_title} LIVE ON TWITCH!
Drop by and say hi! 💜
https://twitch.tv/{username}

[YOUTUBE]
📺 New stream just started! {stream_title}
Don't forget to like and subscribe!
https://youtube.com/@{username}/live

[KICK]
🟢 LIVE ON KICK! Come hang out!
{stream_title}
https://kick.com/{username}
```

### Example 3: Multiple Message Variants

Add variety by including multiple messages per section:

```ini
[TWITCH]
🟣 LIVE on Twitch! {stream_title} https://twitch.tv/{username}
🎮 Going live! {stream_title} - Join me! https://twitch.tv/{username}
💜 Stream starting NOW! {stream_title} https://twitch.tv/{username}
⚡ Time to stream! {stream_title} https://twitch.tv/{username}
🔴 {username} is live! Playing {stream_title} https://twitch.tv/{username}
```

Stream Daemon picks one randomly for each announcement.

### Example 4: Minimal Setup

Simplest possible configuration:

```ini
[DEFAULT]
🔴 {username} is live! {stream_title}
```

That's it! Works for all platforms.

---

## Stream End Messages

### Basic End Messages

`end_messages.txt`:

```ini
[DEFAULT]
Thanks for watching! See you next time! 💜
Stream ended! Thanks for joining!
That's a wrap! Catch you later!
```

### Platform-Specific End Messages

```ini
[DEFAULT]
Thanks for watching!

[TWITCH]
Thanks for the amazing stream! Catch the VOD below! 💜
That was epic! See you next time on Twitch!

[YOUTUBE]
Stream complete! Don't forget to like and subscribe! 🔴
Thanks for watching! VOD will be available soon!

[KICK]
Kick stream done! Thanks for the support! 🟢
That was fun! See you in the next one!
```

### Disabling End Messages

Don't want "stream ended" announcements?

```bash
# In .env
MESSAGES_POST_END_STREAM_MESSAGE=False
```

Only stream start messages will be posted.

---

## Best Practices

### 1. Include Stream URLs

Make it easy for followers to find your stream:

```ini
[TWITCH]
🟣 LIVE: {stream_title}
Watch: https://twitch.tv/{username}
```

**Platform URLs:**
- **Twitch:** `https://twitch.tv/{username}`
- **YouTube:** `https://youtube.com/@{username}/live`
- **Kick:** `https://kick.com/{username}`

### 2. Use Platform Emojis

Visual branding helps:

| Platform | Emoji | Example |
|----------|-------|---------|
| Twitch | 🟣 💜 🎮 | `🟣 LIVE on Twitch!` |
| YouTube | 🔴 📺 🎥 | `📺 YouTube stream!` |
| Kick | 🟢 ⚡ 💚 | `🟢 LIVE on Kick!` |

### 3. Add Variety

Include 5-10 messages per section to avoid repetition:

```ini
[TWITCH]
🟣 Message 1
🟣 Message 2
🟣 Message 3
🟣 Message 4
🟣 Message 5
```

### 4. Match Platform Culture

**Twitch** - Casual, gaming-focused:
```
🟣 LET'S GOOO! Time to grind in {stream_title}! 🎮
```

**YouTube** - Professional, broader audience:
```
📺 New stream: {stream_title}. Like and subscribe for more!
```

**Kick** - Community-focused, energetic:
```
🟢 LIVE NOW! Join the community! {stream_title} ⚡
```

### 5. Keep It Concise

**Social platform character limits:**
- Bluesky: 300 characters
- Mastodon: 500 characters (instance-dependent)
- Discord: No strict limit (but keep under 2000 for embed descriptions)
- Matrix: No strict limit (but keep reasonable)

**Tip:** Aim for **200-250 characters** for cross-platform compatibility.

---

## Troubleshooting

### "No messages found"

**Problem:** Stream Daemon can't find message file

**Solutions:**
1. **Check file exists:**
   ```bash
   ls messages.txt end_messages.txt
   ```
2. **Check file path:**
   ```bash
   # In .env
   MESSAGES_MESSAGES_FILE=messages.txt  # Relative to project root
   ```
3. **Use absolute path if needed:**
   ```bash
   MESSAGES_MESSAGES_FILE=/full/path/to/messages.txt
   ```

### "No [DEFAULT] section found"

**Problem:** Message file has no `[DEFAULT]` section

**Solution:** Add a `[DEFAULT]` section:

```ini
[DEFAULT]
🔴 LIVE! {stream_title}

[TWITCH]
🟣 Twitch specific
```

Even if you use platform-specific messages, `[DEFAULT]` is required as fallback.

### "Variables not replaced"

**Problem:** `{stream_title}` appears literally in posts

**Check:**
1. **Correct variable syntax:**
   - ✅ `{stream_title}`
   - ❌ `{{stream_title}}`
   - ❌ `${stream_title}`
   - ❌ `%stream_title%`

2. **Variables are case-sensitive:**
   - ✅ `{stream_title}`
   - ❌ `{STREAM_TITLE}`
   - ❌ `{streamtitle}`

3. **Supported variables:**
   - `{stream_title}` ✅
   - `{username}` ✅
   - `{platform}` ✅
   - `{viewer_count}` ❌ (not supported in messages.txt)

### "Same message every time"

**Problem:** No randomization happening

**Cause:** Only one message in the section

**Solution:** Add multiple messages:

```ini
[TWITCH]
Message 1
Message 2
Message 3
```

Stream Daemon randomly picks one.

### "Platform section ignored"

**Problem:** Platform-specific messages not being used

**Check:**
1. **Configuration:**
   ```bash
   MESSAGES_USE_PLATFORM_SPECIFIC_MESSAGES=True  # Must be True
   ```

2. **Section names are uppercase:**
   - ✅ `[TWITCH]`
   - ❌ `[twitch]`
   - ❌ `[Twitch]`

3. **Section name matches platform:**
   - Twitch: `[TWITCH]`
   - YouTube: `[YOUTUBE]`
   - Kick: `[KICK]`

---

## Migration Guide

### From Old Format (Separate Files)

**Old setup** (9 files):
```
messages.txt
messages_twitch.txt
messages_youtube.txt
messages_kick.txt
end_messages.txt
end_messages_twitch.txt
end_messages_youtube.txt
end_messages_kick.txt
```

**New setup** (2 files):

**messages.txt:**
```ini
[DEFAULT]
<contents of old messages.txt>

[TWITCH]
<contents of old messages_twitch.txt>

[YOUTUBE]
<contents of old messages_youtube.txt>

[KICK]
<contents of old messages_kick.txt>
```

**end_messages.txt:**
```ini
[DEFAULT]
<contents of old end_messages.txt>

[TWITCH]
<contents of old end_messages_twitch.txt>

[YOUTUBE]
<contents of old end_messages_youtube.txt>

[KICK]
<contents of old end_messages_kick.txt>
```

### Benefits of New Format

✅ **Fewer files** - 2 instead of 9  
✅ **Clearer organization** - All messages in one place  
✅ **Flexible** - Easy to enable/disable platform-specific mode  
✅ **Easier to maintain** - Edit one file instead of many  
✅ **Better version control** - Fewer files to track  

---

## See Also

- [AI Messages Guide](ai-messages.md) - Use AI to generate dynamic messages
- [Multi-Platform Guide](multi-platform.md) - Multi-streaming strategies
- [Discord Setup](../platforms/social/discord.md) - Discord-specific message features
- [Quick Start Guide](../getting-started/quickstart.md) - Initial setup

---

**Last Updated:** 2024
