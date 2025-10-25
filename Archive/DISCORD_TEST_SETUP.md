# Discord Doppler Test Setup Guide

This guide shows how to configure Doppler secrets for testing Discord integration with three platforms (Kick, Twitch, YouTube).

## Test Channels
- **Kick**: asmongold
- **Twitch**: lilypita  
- **YouTube**: grndpagaming

## Prerequisites

1. **Discord Webhook**: Create a webhook in your Discord channel
   - Server Settings → Integrations → Webhooks → Create Webhook
   - Copy the webhook URL

2. **Discord Role ID(s)** (optional): Get role IDs for @mentions
   - Enable Developer Mode: User Settings → Advanced → Developer Mode
   - Right-click role in Server Settings → Roles → Copy Role ID

## Test Scenario 1: One Webhook + One Role (All Platforms)

**Simplest configuration - all three platforms use the same webhook and role**

### Doppler Secrets to Create:

```bash
# Required
discord_webhook_url = "https://discord.com/api/webhooks/YOUR_ID/YOUR_TOKEN"

# Optional (for role mentions)
discord_role = "1234567890123456789"
```

### What This Tests:
- ✅ All three platforms post to same Discord channel
- ✅ All three platforms mention the same role
- ✅ Each platform gets correct embed color (Purple/Red/Green)

### Run Test:
```bash
doppler run -- python3 tests/test_discord_doppler.py
```

### Expected Result:
- 3 Discord messages in your channel
- Each with different color (Twitch=Purple, YouTube=Red, Kick=Green)
- All mention the same role (if configured)

---

## Test Scenario 2: One Webhook + Three Platform-Specific Roles

**More flexible - one webhook but different @mentions per platform**

### Doppler Secrets to Create:

```bash
# Required
discord_webhook_url = "https://discord.com/api/webhooks/YOUR_ID/YOUR_TOKEN"

# Optional - different roles per platform
discord_role_twitch = "1111111111111111111"
discord_role_youtube = "2222222222222222222"
discord_role_kick = "3333333333333333333"
```

### What This Tests:
- ✅ All three platforms post to same Discord channel
- ✅ Twitch mentions @TwitchSubs role
- ✅ YouTube mentions @YouTubeMembers role
- ✅ Kick mentions @KickFans role
- ✅ Each platform gets correct embed color

### Run Test:
```bash
doppler run -- python3 tests/test_discord_doppler.py
```

### Expected Result:
- 3 Discord messages in your channel
- Each with different color
- Each mentions a different role

---

## Test Scenario 3 (Bonus): Three Webhooks + Three Roles

**Maximum flexibility - separate channels per platform**

### Doppler Secrets to Create:

```bash
# Separate webhooks per platform
discord_webhook_twitch = "https://discord.com/api/webhooks/AAA/aaa"
discord_webhook_youtube = "https://discord.com/api/webhooks/BBB/bbb"
discord_webhook_kick = "https://discord.com/api/webhooks/CCC/ccc"

# Separate roles per platform (optional)
discord_role_twitch = "1111111111111111111"
discord_role_youtube = "2222222222222222222"
discord_role_kick = "3333333333333333333"
```

### What This Tests:
- ✅ Twitch posts to #twitch-streams channel
- ✅ YouTube posts to #youtube-streams channel
- ✅ Kick posts to #kick-streams channel
- ✅ Each mentions platform-specific role

---

## Verifying Results

After running the test, check your Discord channel(s) for:

1. **Embed Colors:**
   - 🟣 Twitch = Purple (#9146FF)
   - 🔴 YouTube = Red (#FF0000)
   - 🟢 Kick = Green (#53FC18)

2. **Embed Content:**
   - Title matches the stream title
   - URL is clickable
   - Platform name in header

3. **Role Mentions:**
   - Correct role(s) mentioned above embed
   - Format: `<@&ROLE_ID> is now live!`

4. **Message Count:**
   - Should see 3 messages (one per platform)

---

## Troubleshooting

### "Discord authentication failed"
- Verify Doppler is configured: `doppler secrets`
- Check secret names match exactly (lowercase with underscores)
- Ensure `discord_webhook_url` exists (required)

### "Failed to post"
- Check webhook URL is valid
- Ensure webhook hasn't been deleted in Discord
- Verify webhook has permission to post in channel

### Role mentions not working
- Verify role ID is correct (should be a long number)
- Check bot has permission to mention roles
- Role IDs are optional - embeds will still work without them

### Wrong colors
- This is a bug - each platform should have unique color
- Check `stream-daemon.py` DiscordPlatform.post() method

---

## Cleanup

After testing, you can:
- Delete the test messages in Discord
- Keep the Doppler secrets for production use
- Remove per-platform secrets if you prefer simple configuration
