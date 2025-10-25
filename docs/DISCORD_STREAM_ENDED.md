# Discord Stream Ended Messages

## Overview

When a stream ends, Discord embeds can be automatically updated to show a "stream ended" message while preserving the VOD (Video On Demand) link and final stream statistics. This prevents dead links and provides a better user experience for viewers who discover the notification after the stream has ended.

## Features

✨ **Customizable Messages**: Set different "stream ended" messages for each platform or use a single default message  
🔗 **VOD Link Preservation**: Keep the stream URL in the embed so viewers can watch the replay  
📊 **Final Stats**: Display peak viewer count and category from when the stream ended  
🖼️ **Thumbnail Retention**: Keep the final stream thumbnail for visual continuity  
🎨 **Muted Colors**: Ended streams use slightly muted embed colors to differentiate from live streams

## Configuration

### Environment Variables

Add these to your `.env` file or Doppler/AWS Secrets Manager:

## Configuration

### Environment Variables (.env file)

**IMPORTANT**: Stream ended messages are **configuration**, not secrets. They should be stored in your `.env` file, NOT in Doppler/AWS Secrets Manager/Vault. Only actual secrets (API keys, tokens, webhooks) belong in secrets managers.

Add these to your `.env` file:

```bash
# Default stream ended message (used for all platforms)
DISCORD_ENDED_MESSAGE=Thanks for joining! Tune in next time 💜

# Per-platform messages (optional - overrides default for specific platforms)
DISCORD_ENDED_MESSAGE_TWITCH=Thanks for the amazing stream! Catch the VOD below 💜
DISCORD_ENDED_MESSAGE_YOUTUBE=Stream has ended! Watch the replay below 🎬
DISCORD_ENDED_MESSAGE_KICK=That was epic! Check out the VOD 🎮
```

### Why Not in Doppler/Secrets Manager?

**Messages are configuration, not secrets:**
- ❌ Not sensitive data (they're shown publicly in Discord)
- ❌ Don't need encryption or access control
- ❌ Don't need rotation or auditing
- ✅ Should be easy to edit and version control
- ✅ Belong in `.env` with other configuration

**What SHOULD go in secrets managers:**
- ✅ Discord webhook URLs (contain tokens)
- ✅ API keys and tokens
- ✅ Client IDs and secrets
- ✅ Access tokens and passwords

## How It Works

### Live Stream Lifecycle

1. **Stream Goes Live**
   - Discord embed posted with live indicator (🟣/🔴/🟢)
   - Role mention sent (if configured)
   - Rich embed with viewer count, thumbnail, category
   - Message ID stored for tracking

2. **Stream Updates** (every CHECK_INTERVAL_SECONDS)
   - Embed updated in-place with fresh viewer count
   - Thumbnail refreshed with cache-busting
   - "Last updated" timestamp in footer
   - Same message, no duplicates

3. **Stream Ends**
   - Embed updated with "stream ended" message
   - Live indicator changed to ended indicator (⏹️)
   - Viewer count labeled as "Peak Viewers"
   - VOD link preserved in embed URL
   - Footer shows "Stream ended at HH:MM:SS"
   - Message tracking cleared

### Visual Changes

**Live Stream Embed:**
```
🟣 Live on Twitch
Amazing gameplay stream!

👥 Viewers: 1,234
🎮 Category: Just Chatting

[Stream Thumbnail]

Last updated: 14:32:45 • Click to watch!
```

**Ended Stream Embed:**
```
⏹️ Stream Ended - Twitch
Thanks for the amazing stream! Catch the VOD below 💜

Amazing gameplay stream!

👥 Peak Viewers: 1,234
🎮 Category: Just Chatting

[Final Thumbnail]

Stream ended at 14:45:30 • Click for VOD
```

## Code Integration

### Using in Stream Daemon

```python
# In your main daemon loop
for platform_name, username, platform in active_streams:
    is_live, stream_data = platform.is_live(username)
    
    if is_live:
        # Stream is live - update or post
        if platform_name in posted_streams:
            # Update existing embed
            discord.update_stream(platform_name, stream_data, stream_url)
        else:
            # Post new notification
            discord.post(message, platform_name=platform_name, stream_data=stream_data)
            posted_streams.add(platform_name)
    else:
        # Stream ended - mark as ended
        if platform_name in posted_streams:
            # Get last known stream data for final stats
            discord.end_stream(platform_name, last_stream_data, stream_url)
            posted_streams.remove(platform_name)
```

### API Methods

#### `end_stream(platform_name: str, stream_data: dict, stream_url: str) -> bool`

Updates a Discord embed to show a stream has ended.

**Parameters:**
- `platform_name`: Platform identifier ('Twitch', 'YouTube', 'Kick')
- `stream_data`: Final stream metadata dict with:
  - `title`: Stream title
  - `viewer_count`: Final/peak viewer count
  - `thumbnail_url`: Final thumbnail URL
  - `game_name`: Category/game name
- `stream_url`: VOD link (same as live link for most platforms)

**Returns:**
- `True` if embed was updated successfully
- `False` if update failed or no active message exists

**Behavior:**
1. Looks up active Discord message for the platform
2. Fetches custom "ended" message (per-platform or default)
3. Updates embed with:
   - Muted color scheme
   - "Stream Ended" title with platform icon
   - Custom ended message in description
   - Stream title preserved
   - "Peak Viewers" instead of "Viewers"
   - Final thumbnail (no cache-busting needed)
   - "Stream ended at HH:MM:SS" footer
4. Removes platform from active message tracking
5. Preserves VOD link in embed URL

## Testing

Run the test script to see the full lifecycle:

```bash
cd /home/chiefgyk3d/src/twitch-and-toot
doppler run -- python3 tests/test_discord_stream_ended.py
```

### Test Phases

1. **Initial Post**: Posts stream notifications for all live streams
2. **Update**: Waits 10 seconds, updates embeds with fresh data
3. **End**: Waits 10 seconds, marks streams as ended with custom messages

### Expected Output

```
Discord Stream Ended Test
================================================================================

🔧 Initializing platforms...
🔑 Authenticating...
✓ All platforms authenticated

📤 Phase 1: Posting initial stream notifications...
--------------------------------------------------------------------------------

Kick: Checking asmongold...
  ✓ LIVE: Daily Dose of Chaos
    👥 8,413 viewers
    🎮 Just Chatting
  ✓ Posted to Discord (Message ID: 1234567890)

Twitch: Checking lilypita...
  ✓ LIVE: Morning DJ Set
    👥 56 viewers
    🎮 DJs
  ✓ Posted to Discord (Message ID: 1234567891)

YouTube: Checking grndpagaming...
  ✓ LIVE: Casino Games Live
    👥 617 viewers
    🎮 Slots
  ✓ Posted to Discord (Message ID: 1234567892)

================================================================================
✓ Posted 3 stream notification(s)

📤 Phase 2: Updating embeds (simulating stream updates)...
--------------------------------------------------------------------------------
⏳ Waiting 10 seconds before first update...

Kick: Fetching fresh data for asmongold...
  👥 8,396 viewers (-17)
  ✓ Discord embed updated

Twitch: Fetching fresh data for lilypita...
  👥 56 viewers (±0)
  ✓ Discord embed updated

YouTube: Fetching fresh data for grndpagaming...
  👥 599 viewers (-18)
  ✓ Discord embed updated

================================================================================
✓ Updated all embeds with fresh data

📤 Phase 3: Marking streams as ended...
--------------------------------------------------------------------------------
⏳ Waiting 10 seconds before marking as ended...

Kick: Marking stream as ended for asmongold...
  ✓ Stream still live (using current stats as final)
  ✓ Discord embed updated to show stream ended
    💬 Custom ended message applied
    🔗 VOD link preserved: https://kick.com/asmongold

Twitch: Marking stream as ended for lilypita...
  ✓ Stream still live (using current stats as final)
  ✓ Discord embed updated to show stream ended
    💬 Custom ended message applied
    🔗 VOD link preserved: https://twitch.tv/lilypita

YouTube: Marking stream as ended for grndpagaming...
  ✓ Stream still live (using current stats as final)
  ✓ Discord embed updated to show stream ended
    💬 Custom ended message applied
    🔗 VOD link preserved: https://youtube.com/@grndpagaming/live

================================================================================
✓ Test complete!

📋 Summary:
  • Posted 3 initial stream notification(s)
  • Updated embeds with fresh viewer counts
  • Marked streams as ended with custom messages
  • VOD links preserved in all ended embeds

💡 TIP: Check your Discord channel to see:
  1. Initial embeds with role mentions
  2. Updated viewer counts
  3. Final 'stream ended' messages with VOD links
```

## Customization Examples

### Friendly Casual Streamer
```bash
DISCORD_ENDED_MESSAGE=Thanks for hanging out! 💜 See you next stream!
```

### Professional Broadcaster
```bash
DISCORD_ENDED_MESSAGE_TWITCH=Stream concluded. VOD available below for 14 days.
DISCORD_ENDED_MESSAGE_YOUTUBE=Broadcast complete. Replay available immediately.
```

### Gaming Community
```bash
DISCORD_ENDED_MESSAGE_TWITCH=GG! Thanks for the epic session 🎮
DISCORD_ENDED_MESSAGE_KICK=That was INSANE! Catch the highlights 🔥
```

### Multi-Language Support
```bash
# English default
DISCORD_ENDED_MESSAGE=Thanks for watching! See you next time 💜

# Spanish for YouTube
DISCORD_ENDED_MESSAGE_YOUTUBE=¡Gracias por ver! Vuelve pronto 🎬

# French for Twitch
DISCORD_ENDED_MESSAGE_TWITCH=Merci d'avoir regardé! À bientôt 💜
```

## Fallback Behavior

### No Configuration
If no ended messages are configured, a default message is used:
```
Thanks for joining! Tune in next time 💜
```

### Missing Stream Data
If stream data is incomplete when marking as ended:
- Title: Uses last known title or "Stream"
- Viewer count: Omitted if not available
- Thumbnail: Omitted if not available
- Category: Omitted if not available

### No Active Message
If `end_stream()` is called but no tracked message exists:
- Returns `False`
- Logs debug message: "No active Discord message for {platform} to mark as ended"
- No Discord API call made

## Best Practices

1. **Use Per-Platform Messages**: Different platforms have different audiences and VOD behaviors
2. **Keep VOD Link Context**: Mention if VOD expires (e.g., "VOD available for 14 days on Twitch")
3. **Stay On-Brand**: Match your stream personality and community culture
4. **Be Concise**: Discord embeds have character limits, keep messages brief
5. **Test Messages**: Use test script to preview how messages look before going live
6. **Consider Timing**: VODs may not be immediately available on some platforms

## Troubleshooting

### Message Not Updating
- Check that stream was tracked: `end_stream()` only works if `post()` was called first
- Verify webhook URL is valid and has permission to edit messages
- Check logs for error messages

### Wrong Message Displayed
- Verify secret naming: `discord_ended_message_twitch` not `discord_ended_message_Twitch`
- Check secrets manager: Ensure secrets are loaded correctly
- Test with `.env` first before using secrets manager

### VOD Link Not Working
- Some platforms change URLs after stream ends (YouTube especially)
- Test VOD links manually to verify they work
- Consider adding "(may take a few minutes)" to message if VOD isn't instant

## Technical Details

### Color Scheme

| Platform | Live Color | Ended Color |
|----------|-----------|-------------|
| Twitch   | `#9146FF` (bright purple) | `#6441A5` (muted purple) |
| YouTube  | `#FF0000` (bright red) | `#CC0000` (muted red) |
| Kick     | `#53FC18` (bright green) | `#42C814` (muted green) |
| Default  | `#9146FF` (purple) | `#808080` (gray) |

### Message Lifecycle

```
┌─────────────────┐
│  Stream Live    │
│  post()         │
└────────┬────────┘
         │
         │ Store message_id
         ▼
┌─────────────────┐
│  Active Message │◄──── Periodic updates
│  update_stream()│      (every CHECK_INTERVAL_SECONDS)
└────────┬────────┘
         │
         │ Stream ends
         ▼
┌─────────────────┐
│ Stream Ended    │
│ end_stream()    │──────► Clear tracking
└─────────────────┘
```

### Performance Considerations

- **No Duplicate Posts**: Edits existing message, doesn't create new ones
- **Single API Call**: One PATCH request per stream end
- **Automatic Cleanup**: Tracking cleared after successful update
- **No Polling**: Only updates when explicitly called

## Related Documentation

- [DISCORD_MATRIX_SETUP.md](DISCORD_MATRIX_SETUP.md) - Discord initial setup and configuration
- [DOPPLER_GUIDE.md](DOPPLER_GUIDE.md) - Doppler secrets manager integration
- [README.md](README.md) - Main project documentation

## Contributing

Found a bug or have a feature request? Please open an issue on GitHub!

### Feature Ideas
- [ ] Automatic stream duration calculation
- [ ] Add peak viewer timestamp
- [ ] Support for multiple ended message templates
- [ ] Localization system for multi-language communities
- [ ] Custom embed colors per streamer
- [ ] Integration with Discord threads for VOD discussions
