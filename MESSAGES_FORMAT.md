# Message Customization Guide

## Overview

Stream Daemon uses a **simple, flexible message system** with just **2 files**:
- `messages.txt` - Live stream announcements
- `end_messages.txt` - Stream ended messages

Each file supports **platform-specific sections** so you can customize messages for Twitch, YouTube, and Kick independently.

## 📝 File Format

Messages use an **INI-style format** with sections:

```ini
# Comments start with #
# Variables: {stream_title}, {username}

[DEFAULT]
Generic message that works for all platforms
Another generic message

[TWITCH]
Twitch-specific message with https://twitch.tv/{username}
Another Twitch message

[YOUTUBE]
YouTube-specific message with https://youtube.com/@{username}/live

[KICK]
Kick-specific message with https://kick.com/{username}
```

## How It Works

### Platform-Specific Mode (Default)
When `USE_PLATFORM_SPECIFIC_MESSAGES=True` (default):
1. Stream Daemon looks for a `[PLATFORM]` section matching the streaming platform (TWITCH, YOUTUBE, KICK)
2. If found, uses those messages for that platform
3. If not found, falls back to `[DEFAULT]` messages
4. If no `[DEFAULT]` exists either, exits with error

**Example:**
- Twitch goes live → Uses `[TWITCH]` messages
- YouTube goes live → Uses `[YOUTUBE]` messages  
- Kick goes live → Uses `[KICK]` messages
- Platform has no section → Uses `[DEFAULT]` messages

### Unified Mode
When `USE_PLATFORM_SPECIFIC_MESSAGES=False`:
- **Always** uses `[DEFAULT]` section for all platforms
- Platform-specific sections are ignored
- Same message on every platform

## Variables

All messages support these variables:
- `{stream_title}` - The title of the current stream
- `{username}` - Platform-specific username (e.g., TWITCH_USERNAME, YOUTUBE_USERNAME)

## Configuration

Control message behavior in `.env`:

```bash
# Message files (consolidated format)
MESSAGES_MESSAGES_FILE=messages.txt
MESSAGES_END_MESSAGES_FILE=end_messages.txt

# Use platform-specific sections or always use [DEFAULT]
MESSAGES_USE_PLATFORM_SPECIFIC_MESSAGES=True

# Whether to post end messages when stream ends
MESSAGES_POST_END_STREAM_MESSAGE=True
```

## Migration from Old Format

**Old format** (9 separate files):
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

**New format** (2 consolidated files):
```
messages.txt          (contains [DEFAULT], [TWITCH], [YOUTUBE], [KICK] sections)
end_messages.txt      (contains [DEFAULT], [TWITCH], [YOUTUBE], [KICK] sections)
```

## Benefits

✅ **Fewer files** - 2 instead of 9  
✅ **Clearer organization** - All messages in one place  
✅ **Flexible** - Choose platform-specific or unified messages with one variable  
✅ **Easier to maintain** - Edit one file instead of many  
✅ **Better version control** - Fewer files to track

## Example Usage

### Same message everywhere
Set `USE_PLATFORM_SPECIFIC_MESSAGES=False`, only define `[DEFAULT]`:

```ini
[DEFAULT]
🔴 Now LIVE! Come watch: {stream_title}
Stream starting: {stream_title}
```

### Different messages per platform
Set `USE_PLATFORM_SPECIFIC_MESSAGES=True`, define platform sections:

```ini
[DEFAULT]
🔴 Now LIVE! {stream_title}

[TWITCH]
🟣 LIVE on Twitch! {stream_title} - https://twitch.tv/{username}

[YOUTUBE]
📺 YouTube LIVE! {stream_title} - https://youtube.com/@{username}/live

[KICK]
🟢 Streaming on Kick! {stream_title} - https://kick.com/{username}
```

### Mixed approach
Define `[DEFAULT]` for most platforms, override specific ones:

```ini
[DEFAULT]
🔴 Now LIVE! {stream_title}
Stream starting now!

[TWITCH]
🟣 Twitch stream LIVE! {stream_title} - https://twitch.tv/{username}
# YouTube and Kick will use DEFAULT messages
```
