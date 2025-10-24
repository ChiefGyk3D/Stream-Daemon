# Multi-Platform Posting Examples

This guide shows how to configure Stream Daemon for different multi-platform streaming scenarios.

## 📋 Table of Contents

- [Scenario 1: Separate Posts for Each Platform](#scenario-1-separate-posts-for-each-platform)
- [Scenario 2: Threaded Announcements](#scenario-2-threaded-announcements)
- [Scenario 3: Combined Announcements](#scenario-3-combined-announcements)
- [Scenario 4: Handling Platform Failures](#scenario-4-handling-platform-failures)
- [Message File Examples](#message-file-examples)

---

## Scenario 1: Separate Posts for Each Platform

**Use Case:** You want each platform announcement to be its own independent post.

**Configuration:**
```bash
MESSAGES_LIVE_THREADING_MODE=separate
MESSAGES_END_THREADING_MODE=separate
```

**Result when you go live on Twitch and YouTube:**
```
Post 1: "🔴 LIVE on Twitch! Playing Elden Ring"
Post 2: "🔴 LIVE on YouTube! Playing Elden Ring"
```

**Result when streams end:**
```
Post 3: "Thanks for watching the Twitch stream!"
Post 4: "Thanks for watching the YouTube stream!"
```

**Best For:**
- ✅ Maximizing visibility (each post appears in followers' feeds)
- ✅ Platforms with different audiences
- ✅ When you want clear separation between platforms

---

## Scenario 2: Threaded Announcements

**Use Case:** Keep your followers' feeds clean by threading multiple platform announcements together.

**Configuration:**
```bash
MESSAGES_LIVE_THREADING_MODE=thread
MESSAGES_END_THREADING_MODE=thread
```

**Result when you go live on Twitch, then YouTube:**
```
Post 1: "🔴 LIVE on Twitch! Playing Elden Ring"
  ↳ Post 2 (reply): "Also live on YouTube! https://youtube.com/..."
```

**Result when streams end:**
```
Post 1: "🔴 LIVE on Twitch! Playing Elden Ring"
  ↳ Post 3 (reply): "Twitch stream ended! Thanks for watching!"
  
Post 2: "Also live on YouTube! https://youtube.com/..."
  ↳ Post 4 (reply): "YouTube stream ended! Thanks for watching!"
```

**Best For:**
- ✅ Keeping feeds organized
- ✅ Platforms where threading is well-supported (Mastodon, Bluesky)
- ✅ Reducing notification spam

---

## Scenario 3: Combined Announcements

**Use Case:** Single post announcing all platforms at once.

**Configuration:**
```bash
MESSAGES_LIVE_THREADING_MODE=combined
MESSAGES_END_THREADING_MODE=combined
```

**Result when you go live on Twitch and YouTube simultaneously:**
```
Post 1: "🔴 LIVE on Twitch, YouTube! Playing Elden Ring"
```

**Result when both end:**
```
Post 2: "Thanks for watching! Streams ended on Twitch, YouTube"
```

**Best For:**
- ✅ Minimal post count
- ✅ When platforms go live/offline at the same time
- ✅ Simple, clean announcements

**Note:** If platforms go live at different times (e.g., Twitch goes live, then YouTube 5 minutes later), you'll get separate combined posts:
```
Post 1: "🔴 LIVE on Twitch! ..." (when Twitch goes live)
Post 2: "🔴 LIVE on YouTube! ..." (when YouTube goes live 5min later)
```

---

## Scenario 4: Handling Platform Failures

**Use Case:** You're streaming to Twitch, YouTube, and Kick. Twitch crashes mid-stream but YouTube and Kick continue. You don't want to post "stream ended" until everything is actually done.

**Configuration:**
```bash
MESSAGES_LIVE_THREADING_MODE=separate  # or thread/combined
MESSAGES_END_THREADING_MODE=single_when_all_end
```

**Timeline:**
```
12:00 PM - Go live on Twitch, YouTube, Kick
  Post 1: "🔴 LIVE on Twitch!"
  Post 2: "🔴 LIVE on YouTube!"
  Post 3: "🔴 LIVE on Kick!"

1:00 PM - Twitch crashes 💥
  (No post - waiting for ALL platforms to end)

2:30 PM - YouTube stream ends normally
  (No post - waiting for Kick to end too)

3:00 PM - Kick stream ends
  Post 4: "Thanks for watching! All streams have ended."
```

**Best For:**
- ✅ Multi-platform streamers who want clean end announcements
- ✅ Handling platform instability gracefully
- ✅ Avoiding confusing "stream ended" posts while still live elsewhere

**Alternative with threading:**
```bash
MESSAGES_LIVE_THREADING_MODE=thread
MESSAGES_END_THREADING_MODE=single_when_all_end
```

Result:
```
Post 1: "🔴 LIVE on Twitch!"
  ↳ Post 2: "Also live on YouTube!"
    ↳ Post 3: "Also live on Kick!"
      ↳ Post 4: "All streams ended! Thanks for watching!"
```

---

## Message File Examples

### For Combined Mode (`messages.txt`)

When using `MESSAGES_LIVE_THREADING_MODE=combined`, your message will receive all platform names in the `{platform}` variable:

```
[DEFAULT]
🔴 LIVE on {platform}! Come watch: {stream_title}
Streaming {stream_title} right now on {platform}!
```

Result: `"🔴 LIVE on Twitch, YouTube! Come watch: Elden Ring Playthrough"`

### For Platform-Specific Messages (`messages.txt`)

```
[DEFAULT]
🔴 LIVE! Playing: {stream_title}

[TWITCH]
🟣 LIVE on Twitch! {stream_title} https://twitch.tv/{username}

[YOUTUBE]
🔴 LIVE on YouTube! {stream_title}

[KICK]
🟢 LIVE on Kick! {stream_title}
```

### End Messages (`end_messages.txt`)

```
[DEFAULT]
Thanks for watching! Stream has ended. See you next time!

[TWITCH]
Twitch stream ended! Thanks to all the viewers! 💜

[YOUTUBE]
YouTube stream offline! Thanks for subscribing! 🔴

[KICK]
Kick stream done! Thanks for the support! 🟢
```

### For Single "All Ended" Mode

When using `MESSAGES_END_THREADING_MODE=single_when_all_end`:

```
[DEFAULT]
All streams have ended! Thanks for watching on {platform}! ❤️
That's a wrap! {platform} streams are now offline. See you next time!
```

Result: `"All streams have ended! Thanks for watching on Twitch, YouTube, Kick! ❤️"`

---

## 🎯 Recommended Configurations

### Solo Streamer on Multiple Platforms
```bash
MESSAGES_LIVE_THREADING_MODE=combined
MESSAGES_END_THREADING_MODE=single_when_all_end
```
Minimal posts, clean feed, handles platform failures gracefully.

### Community Streamer with Platform-Specific Audiences
```bash
MESSAGES_LIVE_THREADING_MODE=separate
MESSAGES_END_THREADING_MODE=separate
```
Maximum visibility, each platform's community gets dedicated posts.

### Professional Streamer (Clean Feed)
```bash
MESSAGES_LIVE_THREADING_MODE=thread
MESSAGES_END_THREADING_MODE=thread
```
Organized threading, followers can expand threads for details.

---

## 📝 Variables Available in Messages

- `{stream_title}` - The title of your stream
- `{username}` - Your username on the streaming platform
- `{platform}` - Platform name (e.g., "Twitch" or "Twitch, YouTube" in combined mode)

---

## ⚠️ Important Notes

1. **Combined Mode Timing:** If platforms go live at different times, they'll still get separate posts. Combined mode only works when platforms transition states together (within the same check cycle).

2. **Single When All End:** This mode tracks which platforms went live in the current session. It will only post the final message when ALL of those platforms have gone offline.

3. **Threading Limitations:** Not all social platforms support threading equally well:
   - ✅ Mastodon: Excellent threading support
   - ✅ Bluesky: Full threading via AT Protocol
   - ⚠️ Discord: Webhooks don't support replies (threading is ignored)

4. **Message Templates:** Make sure your messages make sense for the mode you're using. Test with `{platform}` containing multiple names in combined mode.
