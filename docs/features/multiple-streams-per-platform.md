# Multiple Streams Per Platform

Stream Daemon supports monitoring multiple streamers on each platform simultaneously. This allows you to track and announce when any of your favorite streamers go live, all from a single daemon instance.

## ⚠️ No Breaking Changes - Drop-In Upgrade

**This feature requires ZERO configuration changes.** Your existing Doppler secrets, `.env` files, and environment variables work without modification. Simply update the daemon and optionally add comma-separated usernames to monitor multiple streams.

## Supported Platforms

This feature works with **all three streaming platforms**:
- ✅ **Twitch** - Monitor multiple Twitch streamers
- ✅ **YouTube** - Monitor multiple YouTube channels  
- ✅ **Kick** - Monitor multiple Kick streamers

Each platform can independently monitor 3-5+ streamers with separate state tracking.

## Configuration

### ✅ 100% Backward Compatible - No Changes Required!

**Your existing configuration works without modification.** This feature is a drop-in upgrade that requires zero changes to your Doppler secrets or `.env` files.

### Single Username (Existing Configuration - Still Works!)

Your current configuration continues to work exactly as before:

```bash
# EXISTING CONFIG - No changes needed!
TWITCH_USERNAME=chiefgyk3d
YOUTUBE_USERNAME=@chiefgyk3d
KICK_USERNAME=chiefgyk3d
```

### Multiple Usernames (New Feature - Optional Upgrade)

To monitor multiple streamers, simply add comma-separated usernames to your **existing** environment variable:

```bash
# OPTION 1: Use existing variable name (RECOMMENDED)
TWITCH_USERNAME=chiefgyk3d,shroud,summit1g
YOUTUBE_USERNAME=@chiefgyk3d,@markiplier,@jacksepticeye
KICK_USERNAME=chiefgyk3d,adin,xqc
```

**Alternative: Use plural form (optional):**

```bash
# OPTION 2: Use plural variable names (optional)
TWITCH_USERNAMES=chiefgyk3d,shroud,summit1g
YOUTUBE_USERNAMES=@chiefgyk3d,@markiplier,@jacksepticeye
KICK_USERNAMES=chiefgyk3d,adin,xqc
```

**How it works:**
- Daemon checks for `PLATFORM_USERNAMES` (plural) first
- Falls back to `PLATFORM_USERNAME` (singular) - your existing variable
- Both accept comma-separated lists
- Single username works in both forms (no breaking changes)

## How It Works

### Independent Tracking

Each username gets its own independent state tracking:

- **Separate Live/Offline States**: Each streamer is tracked individually
- **Individual Announcements**: Separate posts for each streamer (or combined, depending on threading mode)
- **Per-Stream Debouncing**: Each stream has its own debounce counter to avoid false positives

### Announcement Behavior

The announcement behavior depends on your `MESSAGES_LIVE_THREADING_MODE` setting:

#### Separate Mode (Default)
```bash
MESSAGES_LIVE_THREADING_MODE=separate
```
- Each streamer gets their own separate announcement post
- Posts are not threaded together
- Example: If 3 streamers go live, you get 3 separate social media posts

#### Thread Mode
```bash
MESSAGES_LIVE_THREADING_MODE=thread
```
- Each streamer gets their own post, but they're threaded together
- Second and subsequent posts reply to the previous ones
- Example: If 3 streamers go live, post 2 replies to post 1, post 3 replies to post 2

#### Combined Mode
```bash
MESSAGES_LIVE_THREADING_MODE=combined
```
- All streamers that go live simultaneously are combined into one post
- Lists all platform names and titles in a single announcement
- Example: "ChiefGyk3D, Shroud, and Summit1g are now live!"

### Rate Limiting

When multiple streamers are configured:

- **API Checks**: Each streamer is checked independently using the platform's API
- **Burst Protection**: 4-second delay between announcements prevents Gemini API rate limiting
- **Sequential Processing**: Streaming platforms are processed one at a time to avoid quota issues

## Examples

### Example 1: Monitor Multiple Twitch Streamers

```bash
# .env file
TWITCH_USERNAME=chiefgyk3d,shroud,summit1g,lirik

# Results in monitoring:
# - Twitch/chiefgyk3d
# - Twitch/shroud
# - Twitch/summit1g
# - Twitch/lirik
```

When any of these go live, Stream Daemon will post an announcement with their specific stream title, URL, and metadata.

### Example 2: Mixed Single and Multiple

```bash
# Monitor multiple on some platforms, single on others
TWITCH_USERNAMES=chiefgyk3d,shroud,summit1g
YOUTUBE_USERNAME=@chiefgyk3d
KICK_USERNAME=chiefgyk3d

# Results in monitoring 5 total streams:
# - Twitch/chiefgyk3d
# - Twitch/shroud
# - Twitch/summit1g
# - YouTube/@chiefgyk3d
# - Kick/chiefgyk3d
```

### Example 3: All Platforms with Multiple Streamers

```bash
# Monitor multiple streamers on every platform
TWITCH_USERNAMES=chiefgyk3d,shroud,summit1g
YOUTUBE_USERNAMES=@chiefgyk3d,@markiplier
KICK_USERNAMES=chiefgyk3d,adin

# Results in monitoring 7 total streams across 3 platforms
```

## Logging Output

With multiple streams configured, you'll see output like:

```
📺 Monitoring: Twitch/chiefgyk3d, Twitch/shroud, Twitch/summit1g, YouTube/@chiefgyk3d, Kick/chiefgyk3d
📱 Posting to: Mastodon, Bluesky, Discord, Matrix
⏰ Check: 5min (offline) / 1min (live)

🔍 Checking streams...
  Twitch/chiefgyk3d: Still offline (2 checks)
  Twitch/shroud: Still offline (2 checks)
  Twitch/summit1g: Still offline (2 checks)
🔴 YouTube/@chiefgyk3d went LIVE: Building a Stream Monitoring Bot
📢 Posting 'LIVE' announcement for YouTube/@chiefgyk3d
✓ Posted to 4/4 platform(s)
```

## Performance Considerations

### API Quotas

Each monitored streamer counts toward API quota usage:

- **Twitch**: No significant quota concerns (generous rate limits)
- **YouTube**: 3 units per check × number of streamers
  - Example: 3 streamers × 3 units = 9 units per check
  - With default 2-minute intervals: ~21,600 units/day for 3 streamers (well under 10,000 daily quota)
- **Kick**: Public API, no authentication required, minimal rate limits

### Memory Usage

Minimal impact - each `StreamStatus` object uses approximately 1KB of memory. Monitoring 20 streamers uses ~20KB additional memory.

### Recommendation

For typical usage, monitoring 3-5 streamers per platform is reasonable. If you need to monitor more than 10 streamers per platform, consider:

1. Increasing check intervals (`SETTINGS_CHECK_INTERVAL`) when offline
2. Running multiple daemon instances with different user sets
3. Using platform-specific rate limiting strategies

## Backward Compatibility

This feature is **100% backward compatible**:

- Existing single-username configurations continue to work
- No breaking changes to environment variable names
- Daemon behavior is identical for single-user setups
- Plural form (`USERNAMES`) is optional - singular (`USERNAME`) still works

## Troubleshooting

### "No username(s) configured for Platform"

Make sure you've set either:
- `PLATFORM_USERNAME=username` or
- `PLATFORM_USERNAMES=user1,user2`

### Only monitoring one user despite comma-separated list

- Check for extra spaces: `user1, user2` works (spaces are stripped)
- Verify environment variable is being loaded (use `docker run --env-file .env image env | grep USERNAME`)
- Restart daemon after changing `.env` file

### Too many API calls

If you're hitting rate limits:
- Reduce number of monitored streamers
- Increase `SETTINGS_CHECK_INTERVAL` (default: 5 minutes)
- For YouTube specifically, increase `YOUTUBE_CHECK_INTERVAL`

## Related Configuration

- [Threading Modes](./custom-messages.md#threading-modes) - Control how multiple announcements are grouped
- [Check Intervals](../configuration/secrets.md#timing-settings) - Configure polling frequency
- [Platform Messages](./custom-messages.md) - Customize messages per platform
