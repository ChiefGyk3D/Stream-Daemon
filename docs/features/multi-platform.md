# Multi-Platform Streaming Guide

## Overview

Stream Daemon supports monitoring **multiple streaming platforms simultaneously** (Twitch, YouTube, Kick) and intelligently handles announcing to your social media. This guide covers strategies for multi-platform streaming and how to configure Stream Daemon's behavior.

---

## Quick Concepts

### Threading Modes

Stream Daemon offers **three threading modes** that control how announcements are posted:

| Mode | Description | Use Case |
|------|-------------|----------|
| **separate** | Each platform gets its own independent post | Maximum visibility |
| **thread** | Platforms are threaded/replied together | Clean, organized feeds |
| **combined** | Single post announces all platforms | Minimal post count |

You can configure threading separately for:
- **Stream start messages** (`MESSAGES_LIVE_THREADING_MODE`)
- **Stream end messages** (`MESSAGES_END_THREADING_MODE`)

### Special Mode: Wait for All

**`single_when_all_end`** - Only post "stream ended" when ALL platforms have ended

**Use case:** Prevents confusing "stream ended" posts while you're still live on other platforms.

---

## Configuration

### Basic Setup

Add to your `.env` file:

```bash
# ================================================
# MULTI-PLATFORM THREADING CONFIGURATION
# ================================================

# How to handle stream start announcements
# Options: separate, thread, combined
MESSAGES_LIVE_THREADING_MODE=separate

# How to handle stream end announcements
# Options: separate, thread, combined, single_when_all_end
MESSAGES_END_THREADING_MODE=single_when_all_end
```

---

## Scenario 1: Separate Posts (Maximum Visibility)

### Configuration

```bash
MESSAGES_LIVE_THREADING_MODE=separate
MESSAGES_END_THREADING_MODE=separate
```

### Behavior

**When you go live on Twitch and YouTube:**
```
Post 1: "🟣 LIVE on Twitch! Playing Elden Ring"
Post 2: "🔴 LIVE on YouTube! Playing Elden Ring"
```

**When streams end:**
```
Post 3: "Thanks for watching the Twitch stream!"
Post 4: "Thanks for watching the YouTube stream!"
```

### Pros & Cons

**Pros:**
- ✅ Each post appears in followers' feeds individually
- ✅ Maximum visibility
- ✅ Clear which platform each announcement is for
- ✅ Platform-specific audiences see relevant posts

**Cons:**
- ⚠️ More posts = potentially more notifications
- ⚠️ Can feel spammy if streaming to many platforms
- ⚠️ Fills up followers' feeds

**Best For:**
- Solo platform streaming (mostly streaming to one, occasionally multi-streaming)
- Platforms with different audiences
- When you want maximum engagement

---

## Scenario 2: Threaded Announcements (Clean Feeds)

### Configuration

```bash
MESSAGES_LIVE_THREADING_MODE=thread
MESSAGES_END_THREADING_MODE=thread
```

### Behavior

**When you go live on Twitch, then YouTube:**
```
Post 1: "🟣 LIVE on Twitch! Playing Elden Ring"
  ↳ Post 2 (reply): "Also live on YouTube! https://youtube.com/..."
```

**When streams end:**
```
Post 1: "🟣 LIVE on Twitch! Playing Elden Ring"
  ↳ Post 3 (reply): "Twitch stream ended! Thanks for watching!"
  
Post 2: "Also live on YouTube! https://youtube.com/..."
  ↳ Post 4 (reply): "YouTube stream ended! Thanks for watching!"
```

### How Threading Works

1. **First platform goes live** → Creates new post
2. **Second platform goes live** → Replies to first post
3. **Third platform goes live** → Replies to second post (chain)
4. **Platforms end** → Each replies to its own announcement

**Result:** Clean thread showing your streaming session timeline.

### Pros & Cons

**Pros:**
- ✅ Keeps followers' feeds organized
- ✅ Clear timeline of streaming session
- ✅ Less overwhelming than separate posts
- ✅ Well-supported on Mastodon and Bluesky

**Cons:**
- ⚠️ Threading support varies by platform
- ⚠️ Followers may miss replies (depending on client)
- ⚠️ Discord doesn't support threading (uses separate posts)

**Best For:**
- Mastodon and Bluesky (excellent threading support)
- Regular multi-platform streamers
- Keeping feeds clean and organized

---

## Scenario 3: Combined Announcements (Minimal Posts)

### Configuration

```bash
MESSAGES_LIVE_THREADING_MODE=combined
MESSAGES_END_THREADING_MODE=combined
```

### Behavior

**When you go live on Twitch and YouTube simultaneously:**
```
Post 1: "🔴 LIVE on Twitch, YouTube! Playing Elden Ring"
```

**When both streams end:**
```
Post 2: "Thanks for watching! Streams ended on Twitch, YouTube"
```

### Important Notes

**If platforms go live at different times:**
```
12:00 PM - Twitch goes live
  Post 1: "🔴 LIVE on Twitch! ..."

12:05 PM - YouTube goes live
  Post 2: "🔴 LIVE on YouTube! ..."
```

Platforms must go live **within the same check interval** to be combined.

### Pros & Cons

**Pros:**
- ✅ Minimal post count
- ✅ Simple, clean announcements
- ✅ No threading complexity

**Cons:**
- ⚠️ Only works if platforms go live simultaneously
- ⚠️ Less platform-specific customization
- ⚠️ May not be clear which platforms you're on

**Best For:**
- Always streaming to all platforms at once
- Want absolute minimal social media posts
- Platforms reliably go live at same time

---

## Scenario 4: Wait for All Platforms (Smart End Messages)

### The Problem

You're streaming to **Twitch, YouTube, and Kick**:
```
12:00 PM - All three go live
1:00 PM - Twitch crashes 💥
2:30 PM - YouTube ends normally
3:00 PM - Kick ends
```

**Without `single_when_all_end`:**
```
1:00 PM Post: "Twitch stream ended"  ← Confusing! You're still live!
2:30 PM Post: "YouTube stream ended" ← Still live on Kick!
3:00 PM Post: "Kick stream ended"
```

**With `single_when_all_end`:**
```
(No posts at 1:00 PM or 2:30 PM - waiting)
3:00 PM Post: "All streams have ended! Thanks for watching!"
```

### Configuration

```bash
MESSAGES_LIVE_THREADING_MODE=separate  # or thread/combined
MESSAGES_END_THREADING_MODE=single_when_all_end
```

### Behavior

**Timeline:**
```
12:00 PM - Go live on Twitch, YouTube, Kick
  Post 1: "🟣 LIVE on Twitch!"
  Post 2: "🔴 LIVE on YouTube!"
  Post 3: "🟢 LIVE on Kick!"

1:00 PM - Twitch crashes/ends
  (No post - waiting for all platforms)

2:30 PM - YouTube stream ends
  (No post - still waiting for Kick)

3:00 PM - Kick stream ends
  Post 4: "Thanks for watching! All streams have ended."
```

### Pros & Cons

**Pros:**
- ✅ Prevents confusing "ended" posts while still live
- ✅ Handles platform instability gracefully
- ✅ Clean, professional end announcement
- ✅ Perfect for multi-platform streamers

**Cons:**
- ⚠️ Delay in end announcement (waits for all platforms)
- ⚠️ If one platform hangs, no end message until it resolves

**Best For:**
- Regular multi-platform streamers
- Platforms that occasionally crash/disconnect
- Professional streaming setups

---

## Advanced Combinations

### Recommendation: Threaded Live, Single End

**Configuration:**
```bash
MESSAGES_LIVE_THREADING_MODE=thread
MESSAGES_END_THREADING_MODE=single_when_all_end
```

**Result:**
```
Post 1: "🟣 LIVE on Twitch!"
  ↳ Post 2: "Also live on YouTube!"
    ↳ Post 3: "Also live on Kick!"
      ↳ Post 4: "All streams ended! Thanks for watching!"
```

**Benefits:**
- ✅ Clean organized thread
- ✅ No confusing partial "ended" messages
- ✅ Complete timeline in one thread
- ✅ Professional appearance

---

### Recommendation: Separate Live, Single End

**Configuration:**
```bash
MESSAGES_LIVE_THREADING_MODE=separate
MESSAGES_END_THREADING_MODE=single_when_all_end
```

**Result:**
```
Post 1: "🟣 LIVE on Twitch!"
Post 2: "🔴 LIVE on YouTube!"
Post 3: "🟢 LIVE on Kick!"
(later...)
Post 4: "All streams ended! Thanks for watching!"
```

**Benefits:**
- ✅ Maximum visibility for live announcements
- ✅ Clean single end message
- ✅ No confusion while still live on some platforms
- ✅ Best of both worlds

---

## Platform-Specific Considerations

### Mastodon

**Threading:** ✅ Excellent support  
**Recommendation:** `thread` mode works great

**Notes:**
- Threads appear as conversations
- Followers see threaded replies
- Character limit: 500 (instance-dependent)

### Bluesky

**Threading:** ✅ Good support  
**Recommendation:** `thread` mode works well

**Notes:**
- Threads appear as quote posts or replies
- Character limit: 300
- Keep messages concise

### Discord

**Threading:** ⚠️ Limited (no traditional threading)  
**Recommendation:** `separate` mode

**Notes:**
- Each platform gets separate embed
- Threading mode falls back to separate posts
- Rich embeds with live updates

### Matrix

**Threading:** ⚠️ Limited  
**Recommendation:** `separate` mode

**Notes:**
- Each platform gets separate message
- Messages can't be edited (no live updates)
- Simple HTML formatting

---

## Message File Configuration

### For Combined Mode

When using `combined` mode, the `{platform}` variable contains **all active platforms**:

**messages.txt:**
```ini
[DEFAULT]
🔴 LIVE on {platform}! Come watch: {stream_title}
Streaming {stream_title} right now on {platform}!
```

**Result:** `"🔴 LIVE on Twitch, YouTube! Come watch: Elden Ring"`

### For Platform-Specific Messages

Use platform sections for custom branding:

**messages.txt:**
```ini
[DEFAULT]
🔴 LIVE! Playing: {stream_title}

[TWITCH]
🟣 LIVE on Twitch! {stream_title}
https://twitch.tv/{username}

[YOUTUBE]
🔴 LIVE on YouTube! {stream_title}
https://youtube.com/@{username}/live

[KICK]
🟢 LIVE on Kick! {stream_title}
https://kick.com/{username}
```

**See [Custom Messages Guide](custom-messages.md) for complete message configuration.**

---

## Troubleshooting

### "Combined mode not working"

**Problem:** Platforms post separately even with `combined` mode

**Cause:** Platforms went live at different times

**Solution:**
- Platforms must go live **within the same check interval**
- Default check interval: 5 minutes
- Reduce interval for tighter synchronization:
  ```bash
  SETTINGS_CHECK_INTERVAL=1  # Check every minute
  ```

### "Threading not working on Discord"

**Cause:** Discord doesn't support traditional threading

**Solution:** Discord automatically falls back to separate embeds

**This is expected behavior** - each platform gets its own rich embed.

### "End message never posts"

**Problem:** Using `single_when_all_end` but no end message appears

**Check:**
1. **Are all platforms actually offline?**
   - Check stream status manually
   - One platform may still be detected as live

2. **Is Stream Daemon still running?**
   - Daemon must be running to detect stream end
   - Check logs for errors

3. **Platform API issues?**
   - One platform may not be reporting offline status
   - Check platform API status

**Workaround:** Switch to `separate` mode temporarily:
```bash
MESSAGES_END_THREADING_MODE=separate
```

### "Messages missing platform emoji"

**Problem:** Want different emojis per platform in combined mode

**Solution:** Use message variables with conditional logic (not currently supported)

**Workaround:** Use `separate` or `thread` mode with platform-specific messages

---

## See Also

- [Custom Messages Guide](custom-messages.md) - Configure message content
- [AI Messages Guide](ai-messages.md) - Use AI for dynamic messages
- [Discord Setup](../platforms/social/discord.md) - Discord-specific features
- [Quick Start Guide](../getting-started/quickstart.md) - Initial setup

---

**Last Updated:** 2024
