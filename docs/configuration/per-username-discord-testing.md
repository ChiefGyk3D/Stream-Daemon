# Testing Per-Username Discord Configuration

This guide walks you through testing the new per-username Discord webhook and role configuration feature.

---

## Overview

The per-username feature allows each streamer to post to a different Discord channel and mention a different role. This is ideal for communities monitoring multiple content creators across various platforms.

### Configuration Tiers (Priority Order)

1. **Per-Username** (Highest Priority): `DISCORD_WEBHOOK_TWITCH_ALICE`
2. **Per-Platform**: `DISCORD_WEBHOOK_TWITCH`
3. **Default** (Lowest Priority): `DISCORD_WEBHOOK_URL`

The system tries each tier in order and uses the first match found.

---

## Prerequisites

### 1. Multiple Streams Feature

Ensure you're using comma-separated usernames for at least one platform:

```bash
# In your secrets or environment
TWITCH_USERNAME=alice,bob,carol
# or
YOUTUBE_CHANNEL_ID=UCxxxxxx,UCyyyyyy,UCzzzzzz
```

### 2. Multiple Discord Webhooks

Create separate webhooks for each streamer:

1. Navigate to Discord Server Settings → Integrations → Webhooks
2. Click "New Webhook" for each streamer
3. Configure each webhook:
   - **Name**: `Alice Twitch Alerts`, `Bob Twitch Alerts`, etc.
   - **Channel**: Select different channels for each streamer
   - **Avatar**: Optional custom icon
4. Copy each webhook URL (format: `https://discord.com/api/webhooks/{id}/{token}`)

### 3. Discord Role IDs (Optional but Recommended)

For each channel where you want role mentions:

1. Enable Developer Mode (User Settings → Advanced → Developer Mode)
2. Right-click the role → Copy ID
3. Note the 18-digit snowflake ID (e.g., `987654321098765432`)

---

## Test Scenario 1: Single Platform, Multiple Streamers

**Goal:** Monitor 3 Twitch streamers, each posting to their own Discord channel with their own role mention.

### Configuration

```bash
# Stream Daemon Configuration
TWITCH_USERNAME=alice,bob,carol

# Discord Per-Username Configuration (in secrets)
DISCORD_WEBHOOK_TWITCH_ALICE=https://discord.com/api/webhooks/111111/aaaaaa
DISCORD_WEBHOOK_TWITCH_BOB=https://discord.com/api/webhooks/222222/bbbbbb
DISCORD_WEBHOOK_TWITCH_CAROL=https://discord.com/api/webhooks/333333/cccccc

DISCORD_ROLE_TWITCH_ALICE=111111111111111111
DISCORD_ROLE_TWITCH_BOB=222222222222222222
DISCORD_ROLE_TWITCH_CAROL=333333333333333333
```

### Expected Behavior

- **Alice goes live** → Posts to `#alice-streams` channel, mentions `@Alice Squad` role
- **Bob goes live** → Posts to `#bob-streams` channel, mentions `@Bob Fans` role  
- **Carol goes live** → Posts to `#carol-streams` channel, mentions `@Carol Community` role
- All use same Twitch platform icon (🟣) and color scheme

### Verification Steps

1. Start Stream Daemon: `python3 stream-daemon.py`
2. Wait for check interval to detect live streams
3. Check Discord server:
   - Verify each streamer posts to correct channel
   - Verify each post mentions correct role
   - Verify embeds show correct streamer data (title, thumbnail, viewers)
4. Check logs for per-user webhook loading:
   ```
   INFO - Discord: Using per-user webhook for twitch/alice
   INFO - Discord: Using per-user webhook for twitch/bob
   INFO - Discord: Using per-user webhook for twitch/carol
   ```

---

## Test Scenario 2: Multiple Platforms, Mixed Configuration

**Goal:** Use per-username config for Twitch, per-platform config for YouTube, default for Kick.

### Configuration

```bash
# Stream Daemon Configuration
TWITCH_USERNAME=alice,bob
YOUTUBE_CHANNEL_ID=UCxxxxxx,UCyyyyyy
KICK_USERNAME=gamer99

# Discord Configuration (mix of tiers)
# Default (fallback for Kick)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/000000/default
DISCORD_ROLE=000000000000000000

# Per-Platform (for all YouTube streamers)
DISCORD_WEBHOOK_YOUTUBE=https://discord.com/api/webhooks/999999/youtube
DISCORD_ROLE_YOUTUBE=999999999999999999

# Per-Username (specific Twitch streamers)
DISCORD_WEBHOOK_TWITCH_ALICE=https://discord.com/api/webhooks/111111/alice
DISCORD_WEBHOOK_TWITCH_BOB=https://discord.com/api/webhooks/222222/bob
DISCORD_ROLE_TWITCH_ALICE=111111111111111111
DISCORD_ROLE_TWITCH_BOB=222222222222222222
```

### Expected Behavior

| Streamer | Platform | Uses Config | Posts To | Mentions Role |
|----------|----------|-------------|----------|---------------|
| Alice | Twitch | Per-Username | Alice's channel | Alice's role |
| Bob | Twitch | Per-Username | Bob's channel | Bob's role |
| Creator1 | YouTube | Per-Platform | Shared YouTube channel | Shared YouTube role |
| Creator2 | YouTube | Per-Platform | Shared YouTube channel | Shared YouTube role |
| Gamer99 | Kick | Default | Default channel | Default role |

### Verification Steps

1. Start Stream Daemon
2. Wait for all platforms to be checked
3. Verify configuration tier selection in logs:
   ```
   INFO - Discord: Using per-user webhook for twitch/alice
   INFO - Discord: Using per-user webhook for twitch/bob
   INFO - Discord: Using platform webhook for youtube
   INFO - Discord: Using platform webhook for youtube
   INFO - Discord: Using default webhook for kick
   ```
4. Verify posts appear in correct channels with correct roles

---

## Test Scenario 3: Backward Compatibility

**Goal:** Ensure existing single-streamer configurations work without changes.

### Configuration (Pre-Per-Username Setup)

```bash
# Stream Daemon Configuration (single streamer)
TWITCH_USERNAME=oldstreamer

# Discord Configuration (old style, should still work)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/123456/oldhook
DISCORD_ROLE=123456789012345678
```

### Expected Behavior

- Stream posts to default webhook (exactly like before)
- Role mention uses default role (exactly like before)
- **No changes required** - existing setup works unchanged

### Verification Steps

1. Start Stream Daemon with old configuration
2. Verify stream posts successfully
3. Check logs show default webhook usage:
   ```
   INFO - Discord: Using default webhook for twitch
   ```
4. Confirm no errors or warnings about missing per-user config

---

## Test Scenario 4: Partial Per-Username Config

**Goal:** Test mixed configuration where only some streamers have per-username config.

### Configuration

```bash
# Stream Daemon Configuration
TWITCH_USERNAME=alice,bob,carol

# Discord Configuration (partial per-username)
# Only Alice has per-username config
DISCORD_WEBHOOK_TWITCH_ALICE=https://discord.com/api/webhooks/111111/alice
DISCORD_ROLE_TWITCH_ALICE=111111111111111111

# Bob and Carol fall back to per-platform
DISCORD_WEBHOOK_TWITCH=https://discord.com/api/webhooks/999999/twitch
DISCORD_ROLE_TWITCH=999999999999999999
```

### Expected Behavior

- **Alice** → Uses per-username webhook and role (highest priority)
- **Bob** → Falls back to per-platform webhook and role
- **Carol** → Falls back to per-platform webhook and role

### Verification Steps

1. Start Stream Daemon
2. Check logs for configuration tier selection:
   ```
   INFO - Discord: Using per-user webhook for twitch/alice
   INFO - Discord: Using platform webhook for twitch/bob
   INFO - Discord: Using platform webhook for twitch/carol
   ```
3. Verify Alice posts to dedicated channel, Bob and Carol share platform channel

---

## Troubleshooting

### Issue: Per-Username Config Not Loading

**Symptoms:**
- Streamer posts to wrong channel
- Logs show "Using platform webhook" instead of "Using per-user webhook"

**Diagnosis:**
```bash
# Check secret key format (must be uppercase)
# Correct: DISCORD_WEBHOOK_TWITCH_ALICE
# Wrong: discord_webhook_twitch_alice
# Wrong: DISCORD_WEBHOOK_TWITCH_Alice

# Check username matches exactly (case-insensitive in lookup)
# If TWITCH_USERNAME=AliceGaming, then:
# Correct: DISCORD_WEBHOOK_TWITCH_ALICEGAMING
# Wrong: DISCORD_WEBHOOK_TWITCH_ALICE
```

**Solution:**
1. Verify secret key format: `DISCORD_WEBHOOK_<PLATFORM>_<USERNAME>` (all uppercase)
2. Ensure username portion matches configured username exactly (capitalization doesn't matter)
3. Check secrets are loaded in secrets manager (Doppler/AWS/Vault)
4. Restart Stream Daemon after updating secrets

### Issue: No Role Mention

**Symptoms:**
- Stream post appears in correct channel
- No role mention in message

**Diagnosis:**
```bash
# Check if role secret is configured
# For per-username: DISCORD_ROLE_TWITCH_ALICE
# For per-platform: DISCORD_ROLE_TWITCH
# For default: DISCORD_ROLE

# Verify role ID format (18-digit snowflake)
# Correct: 987654321098765432
# Wrong: @StreamAlerts (role name, not ID)
# Wrong: <@&987654321098765432> (mention format, not ID)
```

**Solution:**
1. Configure role secret matching webhook tier (per-username/per-platform/default)
2. Use raw role ID (digits only), not role name or mention format
3. Verify role exists in Discord server and bot has access
4. Check Discord webhook has permission to mention roles

### Issue: Webhook Returns 404 Not Found

**Symptoms:**
- Error log: `Discord webhook POST failed: 404`
- Stream not posted to Discord

**Diagnosis:**
```bash
# Test webhook manually
curl -X POST "https://discord.com/api/webhooks/YOUR_ID/YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "Test message"}'

# If 404: webhook was deleted or URL is incorrect
```

**Solution:**
1. Verify webhook still exists in Discord (Server Settings → Integrations → Webhooks)
2. If deleted, create new webhook and update secret
3. Double-check webhook URL format (must include both ID and token)
4. Ensure no extra spaces or characters in secret value

### Issue: Duplicate Posts

**Symptoms:**
- Same stream posted to multiple channels
- Multiple role mentions for same stream

**Diagnosis:**
```bash
# Check for overlapping configuration
# If both per-username AND per-platform are configured for same streamer,
# only per-username should be used (highest priority)

# Verify logs show only one webhook type:
# Good: "Using per-user webhook for twitch/alice"
# Bad: Both "Using per-user" and "Using platform" for same stream
```

**Solution:**
1. Review configuration - remove duplicate/conflicting webhook configs
2. Use configuration tiers intentionally (per-username OR per-platform, not both)
3. Check for multiple webhook URLs pointing to same channel
4. Ensure Stream Daemon is running only once (not multiple instances)

---

## Advanced Testing

### Dynamic Username Addition

Test that new streamers can be added without restarting:

1. Start Stream Daemon with `TWITCH_USERNAME=alice`
2. Add per-username config for new streamer: `DISCORD_WEBHOOK_TWITCH_BOB=...`
3. Update `TWITCH_USERNAME=alice,bob` in secrets
4. **Restart Stream Daemon** (required to reload username list)
5. Verify Bob's streams use new per-username config

**Note:** Currently requires restart to reload username list. Dynamic username loading is a potential future enhancement.

### Secrets Caching Behavior

Test that per-username secrets are cached after first load:

1. Start Stream Daemon with per-username config
2. Streamer goes live → First post triggers secret load
3. Check logs: `INFO - Discord: Loaded per-user webhook for twitch/alice`
4. Streamer updates (thumbnail/viewers change) → Post updated
5. Check logs: Should NOT show "Loaded per-user webhook" again (using cache)
6. Verify embed updates successfully (cache not blocking updates)

### Failover Testing

Test configuration tier failover:

1. Configure per-username webhook for Alice
2. Alice goes live → Verify uses per-username webhook
3. **Temporarily delete** per-username secret (simulate misconfiguration)
4. Restart Stream Daemon
5. Alice goes live again → Should failover to per-platform or default
6. Check logs: `WARNING - Discord: Per-user webhook not found for twitch/alice, falling back`

---

## Performance Considerations

### Many Streamers (10+)

When monitoring many streamers with per-username config:

- **Secret Loading**: First post per streamer loads config (< 100ms per streamer)
- **Caching**: Subsequent posts use cached config (no additional load time)
- **Memory**: Each streamer's config uses ~1KB memory (negligible)
- **API Calls**: Each webhook posts independently (parallel execution)

**Recommendation:** No performance concerns up to 50+ streamers with per-username config.

### API Rate Limits

Discord webhook rate limits:

- **Per Webhook**: 30 requests per minute
- **Per Server**: 50 webhooks total
- **Stream Updates**: Typically every 60-300 seconds (CHECK_INTERVAL)

**Safe Configuration:**
- Up to 30 streamers per webhook (if all update simultaneously)
- Up to 50 unique per-username webhooks per server
- CHECK_INTERVAL ≥ 60 seconds (recommended)

---

## Best Practices

### 1. Naming Conventions

Use consistent Discord webhook and channel names:

```
# Webhook Names (in Discord)
✅ Alice - Twitch Alerts
✅ Bob - YouTube Alerts
✅ Carol - Kick Alerts

❌ Webhook #1
❌ New Webhook (2)
❌ Copy of Alice alerts
```

### 2. Role Hierarchy

Structure Discord roles for clean mentions:

```
# Role Order (highest to lowest)
1. @Moderators
2. @Alice Squad (streamer-specific roles)
3. @Bob Fans
4. @Carol Community
5. @Stream Alerts (default role for all streamers)
6. @everyone
```

### 3. Channel Organization

Create dedicated categories for multi-streamer setups:

```
📁 TWITCH STREAMS
  #alice-live (Alice's per-username webhook)
  #bob-live (Bob's per-username webhook)
  #carol-live (Carol's per-username webhook)

📁 YOUTUBE STREAMS
  #youtube-live (per-platform webhook for all creators)

📁 OTHER PLATFORMS
  #kick-live (default webhook)
```

### 4. Secret Management

Organize secrets in your secrets manager:

```bash
# Group by tier for clarity
[Discord - Per-Username - Twitch]
DISCORD_WEBHOOK_TWITCH_ALICE=...
DISCORD_WEBHOOK_TWITCH_BOB=...
DISCORD_ROLE_TWITCH_ALICE=...
DISCORD_ROLE_TWITCH_BOB=...

[Discord - Per-Platform]
DISCORD_WEBHOOK_YOUTUBE=...
DISCORD_ROLE_YOUTUBE=...

[Discord - Default]
DISCORD_WEBHOOK_URL=...
DISCORD_ROLE=...
```

---

## Migration from Single to Multi-Streamer

### Step 1: Document Current Setup

```bash
# Note your current configuration
TWITCH_USERNAME=alice
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/111111/aaaaaa
DISCORD_ROLE=111111111111111111
```

### Step 2: Add New Streamers (Keep Default)

```bash
# Add new streamers, keep existing default webhook
TWITCH_USERNAME=alice,bob,carol
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/111111/aaaaaa  # Still works
DISCORD_ROLE=111111111111111111
```

**Result:** All streamers post to same channel (backward compatible).

### Step 3: Create Per-Username Webhooks (Gradual)

```bash
# Add per-username for Bob only (Alice still uses default)
DISCORD_WEBHOOK_TWITCH_BOB=https://discord.com/api/webhooks/222222/bbbbbb
DISCORD_ROLE_TWITCH_BOB=222222222222222222
```

**Result:** Bob posts to dedicated channel, Alice uses default.

### Step 4: Complete Migration

```bash
# Add per-username for all streamers
DISCORD_WEBHOOK_TWITCH_ALICE=https://discord.com/api/webhooks/111111/aaaaaa
DISCORD_WEBHOOK_TWITCH_BOB=https://discord.com/api/webhooks/222222/bbbbbb
DISCORD_WEBHOOK_TWITCH_CAROL=https://discord.com/api/webhooks/333333/cccccc

DISCORD_ROLE_TWITCH_ALICE=111111111111111111
DISCORD_ROLE_TWITCH_BOB=222222222222222222
DISCORD_ROLE_TWITCH_CAROL=333333333333333333
```

**Result:** Each streamer has dedicated channel and role.

### Step 5: Clean Up (Optional)

```bash
# Remove default webhook if all platforms use per-username/per-platform
# (Keep as fallback if desired)
# DISCORD_WEBHOOK_URL=...  # Can comment out or leave as safety net
```

---

## Conclusion

The per-username Discord configuration provides maximum flexibility for multi-streamer monitoring while maintaining 100% backward compatibility. Use this guide to test and validate your setup, and refer to the troubleshooting section if issues arise.

**Key Takeaways:**
- ✅ Per-username config takes priority over per-platform and default
- ✅ Existing single-streamer setups work unchanged
- ✅ Mix configuration tiers as needed (some per-username, some per-platform)
- ✅ Secrets loaded dynamically on first post per streamer (cached afterward)
- ✅ Each streamer can have unique Discord channel and role mention

For additional help, see:
- [Discord Platform Documentation](../platforms/social/discord.md)
- [Secrets Management Guide](./secrets.md)
- [Multiple Streams Feature](../features/multi-platform.md)
