# Per-Username Social Platform Configuration

This guide explains how to configure per-username social platform accounts for multi-streamer monitoring. This feature allows each monitored streamer to post to different social media accounts.

---

## Overview

The Stream Daemon supports **per-username configuration** for all social platforms:

- **Discord**: Different webhooks and role mentions per streamer
- **Bluesky**: Different Bluesky accounts per streamer
- **Mastodon**: Different Mastodon instances/accounts per streamer
- **Matrix**: Different Matrix rooms per streamer

### Configuration Priority

All platforms follow a **two-tier fallback system**:

1. **Per-Username** (Highest Priority): `PLATFORM_SETTING_PLATFORMNAME_USERNAME`
2. **Default** (Fallback): `PLATFORM_SETTING`

The system tries per-username configuration first, then falls back to default if not found.

---

## Discord Per-Username Configuration

### Use Case

Monitor multiple Twitch streamers, each posting to their own Discord channel with their own role mention.

### Configuration Format

```bash
# Per-Username Discord Webhooks
DISCORD_WEBHOOK_<PLATFORM>_<USERNAME>=https://discord.com/api/webhooks/...

# Per-Username Discord Roles
DISCORD_ROLE_<PLATFORM>_<USERNAME>=123456789012345678

# Examples:
DISCORD_WEBHOOK_TWITCH_ALICE=https://discord.com/api/webhooks/111/aaa
DISCORD_WEBHOOK_TWITCH_BOB=https://discord.com/api/webhooks/222/bbb
DISCORD_ROLE_TWITCH_ALICE=111111111111111111
DISCORD_ROLE_TWITCH_BOB=222222222222222222
```

**Note**: All letters must be uppercase. Platform and username are separated by underscore.

### Example Scenario

```bash
# Stream Daemon Config
TWITCH_USERNAME=alice,bob,carol

# Discord Per-Username Config
DISCORD_WEBHOOK_TWITCH_ALICE=https://discord.com/api/webhooks/111/aaa
DISCORD_WEBHOOK_TWITCH_BOB=https://discord.com/api/webhooks/222/bbb
DISCORD_WEBHOOK_TWITCH_CAROL=https://discord.com/api/webhooks/333/ccc

DISCORD_ROLE_TWITCH_ALICE=111111111111111111
DISCORD_ROLE_TWITCH_BOB=222222222222222222
DISCORD_ROLE_TWITCH_CAROL=333333333333333333
```

**Result**: 
- Alice's streams → `#alice-streams` channel, mentions `@Alice Squad`
- Bob's streams → `#bob-streams` channel, mentions `@Bob Fans`
- Carol's streams → `#carol-streams` channel, mentions `@Carol Community`

### Documentation

See [Discord Platform Documentation](../platforms/social/discord.md) for complete details.

---

## Bluesky Per-Username Configuration

### Use Case

Monitor multiple streamers, each posting to their own Bluesky account.

### Configuration Format

```bash
# Per-Username Bluesky Accounts
BLUESKY_HANDLE_<PLATFORM>_<USERNAME>=handle.bsky.social
BLUESKY_APP_PASSWORD_<PLATFORM>_<USERNAME>=app-password-here

# Examples:
BLUESKY_HANDLE_TWITCH_ALICE=alice-streams.bsky.social
BLUESKY_APP_PASSWORD_TWITCH_ALICE=xxxx-xxxx-xxxx-xxxx

BLUESKY_HANDLE_YOUTUBE_CREATOR1=creator1-updates.bsky.social
BLUESKY_APP_PASSWORD_YOUTUBE_CREATOR1=yyyy-yyyy-yyyy-yyyy
```

**Note**: Requires Bluesky App Password (not main account password). Create at Settings → Advanced → App Passwords.

### Example Scenario

```bash
# Stream Daemon Config
TWITCH_USERNAME=alice,bob
YOUTUBE_CHANNEL_ID=UCxxxxxx,UCyyyyyy

# Default Bluesky Account (fallback)
BLUESKY_ENABLE_POSTING=True
BLUESKY_HANDLE=default-bot.bsky.social
BLUESKY_APP_PASSWORD=default-app-password

# Per-Username Bluesky Accounts (optional)
BLUESKY_HANDLE_TWITCH_ALICE=alice-twitch.bsky.social
BLUESKY_APP_PASSWORD_TWITCH_ALICE=alice-app-password

BLUESKY_HANDLE_YOUTUBE_UCXXXXXX=creator1-youtube.bsky.social
BLUESKY_APP_PASSWORD_YOUTUBE_UCXXXXXX=creator1-app-password
```

**Result**:
- Alice's Twitch streams → Post from `alice-twitch.bsky.social`
- Bob's Twitch streams → Post from `default-bot.bsky.social` (fallback)
- Creator1's YouTube streams → Post from `creator1-youtube.bsky.social`

### Threading Behavior

Each Bluesky account maintains its own thread:
- Start message → New post with embed card
- End message → Reply to start message (forms thread)

Per-username accounts allow separate threads per streamer on different Bluesky accounts.

---

## Mastodon Per-Username Configuration

### Use Case

Monitor multiple streamers, each posting to different Mastodon instances or accounts.

### Configuration Format

```bash
# Per-Username Mastodon Accounts
MASTODON_API_BASE_URL_<PLATFORM>_<USERNAME>=https://mastodon.social
MASTODON_CLIENT_ID_<PLATFORM>_<USERNAME>=client-id
MASTODON_CLIENT_SECRET_<PLATFORM>_<USERNAME>=client-secret
MASTODON_ACCESS_TOKEN_<PLATFORM>_<USERNAME>=access-token

# Examples:
MASTODON_API_BASE_URL_TWITCH_ALICE=https://mastodon.social
MASTODON_CLIENT_ID_TWITCH_ALICE=alice_client_id
MASTODON_CLIENT_SECRET_TWITCH_ALICE=alice_client_secret
MASTODON_ACCESS_TOKEN_TWITCH_ALICE=alice_access_token

MASTODON_API_BASE_URL_TWITCH_BOB=https://fosstodon.org
MASTODON_CLIENT_ID_TWITCH_BOB=bob_client_id
MASTODON_CLIENT_SECRET_TWITCH_BOB=bob_client_secret
MASTODON_ACCESS_TOKEN_TWITCH_BOB=bob_access_token
```

**Note**: Each Mastodon account requires client ID, client secret, and access token. Obtain these from your Mastodon instance's Developer Settings.

### Example Scenario

```bash
# Stream Daemon Config
TWITCH_USERNAME=alice,bob

# Default Mastodon Account (fallback)
MASTODON_ENABLE_POSTING=True
MASTODON_API_BASE_URL=https://mastodon.example
MASTODON_CLIENT_ID=default_client_id
MASTODON_CLIENT_SECRET=default_client_secret
MASTODON_ACCESS_TOKEN=default_access_token

# Per-Username Mastodon Accounts
MASTODON_API_BASE_URL_TWITCH_ALICE=https://mastodon.social
MASTODON_CLIENT_ID_TWITCH_ALICE=alice_client_id
MASTODON_CLIENT_SECRET_TWITCH_ALICE=alice_client_secret
MASTODON_ACCESS_TOKEN_TWITCH_ALICE=alice_access_token

# Bob uses default account (no per-username config)
```

**Result**:
- Alice's streams → Post from `@alice@mastodon.social`
- Bob's streams → Post from default account on `mastodon.example`

### Cross-Instance Posting

Per-username configuration supports posting to different Mastodon instances:
- Alice → `mastodon.social`
- Bob → `fosstodon.org`
- Carol → `mastodon.gamedev.place`

Each instance requires separate authentication credentials.

---

## Matrix Per-Username Configuration

### Use Case

Monitor multiple streamers, each posting to different Matrix rooms (same or different homeservers).

### Configuration Format

```bash
# Per-Username Matrix Rooms
MATRIX_HOMESERVER_<PLATFORM>_<USERNAME>=https://matrix.org
MATRIX_ROOM_ID_<PLATFORM>_<USERNAME>=!roomid:matrix.org
MATRIX_USERNAME_<PLATFORM>_<USERNAME>=@bot:matrix.org
MATRIX_PASSWORD_<PLATFORM>_<USERNAME>=password
# OR
MATRIX_ACCESS_TOKEN_<PLATFORM>_<USERNAME>=access_token

# Examples:
MATRIX_HOMESERVER_TWITCH_ALICE=https://matrix.org
MATRIX_ROOM_ID_TWITCH_ALICE=!abc123:matrix.org
MATRIX_USERNAME_TWITCH_ALICE=@alice-bot:matrix.org
MATRIX_PASSWORD_TWITCH_ALICE=alice_password

MATRIX_HOMESERVER_TWITCH_BOB=https://matrix.example.com
MATRIX_ROOM_ID_TWITCH_BOB=!xyz789:matrix.example.com
MATRIX_ACCESS_TOKEN_TWITCH_BOB=bob_access_token
```

**Note**: Can use either `username+password` (preferred, auto-rotation) OR `access_token` (static).

### Example Scenario

```bash
# Stream Daemon Config
TWITCH_USERNAME=alice,bob,carol

# Default Matrix Room (fallback)
MATRIX_ENABLE_POSTING=True
MATRIX_HOMESERVER=https://matrix.org
MATRIX_ROOM_ID=!default:matrix.org
MATRIX_USERNAME=@default-bot:matrix.org
MATRIX_PASSWORD=default_password

# Per-Username Matrix Rooms (same homeserver, different rooms)
MATRIX_ROOM_ID_TWITCH_ALICE=!alice-room:matrix.org
MATRIX_ROOM_ID_TWITCH_BOB=!bob-room:matrix.org
# Carol uses default room (no per-username config)

# Credentials: Reuse default homeserver/credentials, just different rooms
# OR provide separate credentials per user:
MATRIX_USERNAME_TWITCH_ALICE=@alice-bot:matrix.org
MATRIX_PASSWORD_TWITCH_ALICE=alice_password
```

**Result**:
- Alice's streams → Post to `!alice-room:matrix.org` (using Alice's bot account)
- Bob's streams → Post to `!bob-room:matrix.org` (using Bob's bot account)
- Carol's streams → Post to `!default:matrix.org` (using default bot account)

### Same vs Different Homeservers

**Same Homeserver, Different Rooms:**
```bash
MATRIX_ROOM_ID_TWITCH_ALICE=!alice:matrix.org
MATRIX_ROOM_ID_TWITCH_BOB=!bob:matrix.org
# Reuses default homeserver and credentials
```

**Different Homeservers:**
```bash
MATRIX_HOMESERVER_TWITCH_ALICE=https://matrix.org
MATRIX_ROOM_ID_TWITCH_ALICE=!room:matrix.org
MATRIX_USERNAME_TWITCH_ALICE=@alice-bot:matrix.org
MATRIX_PASSWORD_TWITCH_ALICE=alice_password

MATRIX_HOMESERVER_TWITCH_BOB=https://private.matrix.server
MATRIX_ROOM_ID_TWITCH_BOB=!room:private.matrix.server
MATRIX_USERNAME_TWITCH_BOB=@bob-bot:private.matrix.server
MATRIX_PASSWORD_TWITCH_BOB=bob_password
```

---

## Mixed Configuration Examples

### Scenario 1: Discord Per-Username Only

```bash
# Monitor 3 Twitch streamers
TWITCH_USERNAME=alice,bob,carol

# Each has own Discord channel
DISCORD_ENABLE_POSTING=True
DISCORD_WEBHOOK_TWITCH_ALICE=https://discord.com/api/webhooks/111/aaa
DISCORD_WEBHOOK_TWITCH_BOB=https://discord.com/api/webhooks/222/bbb
DISCORD_WEBHOOK_TWITCH_CAROL=https://discord.com/api/webhooks/333/ccc

# All share same Bluesky/Mastodon/Matrix (default)
BLUESKY_ENABLE_POSTING=True
BLUESKY_HANDLE=shared-bot.bsky.social
BLUESKY_APP_PASSWORD=shared_password
```

**Result**: Each streamer has dedicated Discord channel, but all post to same Bluesky account.

### Scenario 2: Full Per-Username for Alice, Default for Others

```bash
# Monitor 3 Twitch streamers
TWITCH_USERNAME=alice,bob,carol

# Alice has dedicated accounts on all platforms
DISCORD_WEBHOOK_TWITCH_ALICE=https://discord.com/api/webhooks/111/aaa
BLUESKY_HANDLE_TWITCH_ALICE=alice.bsky.social
BLUESKY_APP_PASSWORD_TWITCH_ALICE=alice_password
MASTODON_API_BASE_URL_TWITCH_ALICE=https://mastodon.social
MASTODON_ACCESS_TOKEN_TWITCH_ALICE=alice_token
MATRIX_ROOM_ID_TWITCH_ALICE=!alice:matrix.org

# Bob and Carol use defaults for all platforms
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/999/default
BLUESKY_HANDLE=default-bot.bsky.social
BLUESKY_APP_PASSWORD=default_password
MASTODON_API_BASE_URL=https://mastodon.example
MASTODON_ACCESS_TOKEN=default_token
MATRIX_ROOM_ID=!default:matrix.org
```

**Result**: Alice has fully customized social media presence, Bob and Carol share defaults.

### Scenario 3: Multi-Platform with Per-Username

```bash
# Monitor streamers across multiple platforms
TWITCH_USERNAME=alice,bob
YOUTUBE_CHANNEL_ID=UCxxxxxx
KICK_USERNAME=streamer1

# Discord: Per-username for all
DISCORD_WEBHOOK_TWITCH_ALICE=https://discord.com/api/webhooks/111/aaa
DISCORD_WEBHOOK_TWITCH_BOB=https://discord.com/api/webhooks/222/bbb
DISCORD_WEBHOOK_YOUTUBE_UCXXXXXX=https://discord.com/api/webhooks/333/ccc
DISCORD_WEBHOOK_KICK_STREAMER1=https://discord.com/api/webhooks/444/ddd

# Bluesky: Only Twitch streamers have custom accounts
BLUESKY_HANDLE_TWITCH_ALICE=alice.bsky.social
BLUESKY_APP_PASSWORD_TWITCH_ALICE=alice_password
BLUESKY_HANDLE_TWITCH_BOB=bob.bsky.social
BLUESKY_APP_PASSWORD_TWITCH_BOB=bob_password
# YouTube and Kick use default Bluesky account
BLUESKY_HANDLE=default-bot.bsky.social
BLUESKY_APP_PASSWORD=default_password
```

**Result**: Granular control per platform and per streamer.

---

## Configuration Best Practices

### 1. Naming Conventions

**Secret Keys:**
```bash
✅ DISCORD_WEBHOOK_TWITCH_ALICE
✅ BLUESKY_HANDLE_YOUTUBE_CREATOR1
✅ MASTODON_API_BASE_URL_KICK_GAMER99

❌ discord_webhook_twitch_alice (lowercase)
❌ DISCORD_WEBHOOK_TWITCH_Alice (mixed case username)
❌ DISCORD_WEBHOOK_TWITCH-ALICE (hyphen instead of underscore)
```

**Usernames in Keys:**
- Must match configured usernames exactly (case-insensitive in lookup)
- Convert to uppercase in secret key
- Use underscores, not hyphens

### 2. Secrets Organization

Organize secrets in your secrets manager by platform and user:

```bash
[Discord - Per-Username]
DISCORD_WEBHOOK_TWITCH_ALICE=...
DISCORD_WEBHOOK_TWITCH_BOB=...
DISCORD_ROLE_TWITCH_ALICE=...
DISCORD_ROLE_TWITCH_BOB=...

[Bluesky - Per-Username]
BLUESKY_HANDLE_TWITCH_ALICE=...
BLUESKY_APP_PASSWORD_TWITCH_ALICE=...

[Default Accounts]
DISCORD_WEBHOOK_URL=...
BLUESKY_HANDLE=...
MASTODON_API_BASE_URL=...
MATRIX_HOMESERVER=...
```

### 3. Gradual Rollout

Start with defaults, add per-username configs incrementally:

**Step 1**: All streamers use defaults
```bash
TWITCH_USERNAME=alice,bob,carol
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/999/default
```

**Step 2**: Add per-username for Alice only
```bash
DISCORD_WEBHOOK_TWITCH_ALICE=https://discord.com/api/webhooks/111/alice
# Bob and Carol still use default
```

**Step 3**: Add per-username for all
```bash
DISCORD_WEBHOOK_TWITCH_ALICE=...
DISCORD_WEBHOOK_TWITCH_BOB=...
DISCORD_WEBHOOK_TWITCH_CAROL=...
```

### 4. Testing Strategy

Test per-username configs one at a time:

1. Start with default config (verify all streamers work)
2. Add per-username config for one streamer
3. Restart Stream Daemon
4. Verify streamer uses per-username config
5. Verify other streamers still use default
6. Repeat for additional streamers

### 5. Fallback Safety

Always configure defaults as fallback:

```bash
# ✅ GOOD: Default configured as safety net
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/999/default
DISCORD_WEBHOOK_TWITCH_ALICE=https://discord.com/api/webhooks/111/alice

# ❌ RISKY: No default, breaks if per-username missing
# (Only per-username config, no default)
DISCORD_WEBHOOK_TWITCH_ALICE=https://discord.com/api/webhooks/111/alice
```

---

## Troubleshooting

### Per-Username Config Not Loading

**Symptoms:**
- Streamer posts to wrong account/room
- Logs show "Using default" instead of "Using per-user"

**Diagnosis:**
```bash
# Check secret key format (must be exact)
# Correct: BLUESKY_HANDLE_TWITCH_ALICE
# Wrong: BLUESKY_HANDLE_TWITCH_alice (lowercase username)
# Wrong: BLUESKY_HANDLE_PLATFORM_USERNAME (literal, not substituted)

# Verify username matches configured streamer
# If TWITCH_USERNAME=AliceGaming, then:
# Correct: BLUESKY_HANDLE_TWITCH_ALICEGAMING
# Wrong: BLUESKY_HANDLE_TWITCH_ALICE
```

**Solution:**
1. Verify secret key format matches `PLATFORM_SETTING_PLATFORMNAME_USERNAME` (all uppercase)
2. Ensure username portion matches configured username (case-insensitive)
3. Check secrets are present in secrets manager
4. Restart Stream Daemon after updating secrets

### Authentication Failures

**Symptoms:**
- Error: "Per-user authentication failed"
- Streamer falls back to default account

**Diagnosis:**
```bash
# Check all required credentials present
# Bluesky: BLUESKY_HANDLE_* AND BLUESKY_APP_PASSWORD_*
# Mastodon: MASTODON_API_BASE_URL_*, CLIENT_ID_*, CLIENT_SECRET_*, ACCESS_TOKEN_*
# Matrix: MATRIX_HOMESERVER_*, ROOM_ID_*, (USERNAME_* + PASSWORD_*) OR ACCESS_TOKEN_*

# Verify credentials are valid (test manually)
```

**Solution:**
1. Ensure all required credentials configured for per-username account
2. Test credentials independently (use platform's API/web interface)
3. Check for typos in credentials (especially long tokens)
4. Verify API keys haven't expired or been revoked

### Posting to Wrong Account/Room

**Symptoms:**
- Alice's streams post to Bob's Discord channel
- Streamer posts to default account despite per-username config

**Diagnosis:**
```bash
# Check lookup key format in logs
# Should see: "Using per-user config for twitch/alice"
# If not, key format is wrong

# Verify username parameter passed through
# Should appear in publisher.py → social.post(username=username)
```

**Solution:**
1. Verify per-username secrets follow exact format
2. Check Stream Daemon logs for "Using per-user" vs "Using default"
3. Ensure username passed to post() method (should be automatic)
4. Restart Stream Daemon to reload configurations

---

## Security Considerations

### 1. Secrets Management

**Best Practices:**
- Store all credentials in secrets manager (Doppler, AWS Secrets Manager, HashiCorp Vault)
- Never commit credentials to git
- Rotate access tokens regularly
- Use separate bot accounts for each social platform

### 2. Access Control

**Recommendations:**
- Create dedicated bot accounts (not personal accounts)
- Grant minimum required permissions
- Use app-specific passwords where available (Bluesky)
- Regularly audit bot account access

### 3. Rate Limiting

**Considerations:**
- Multiple accounts = multiple rate limits (generally better)
- Discord: 30 requests/minute per webhook
- Bluesky: 300 posts/day per account (per-username = higher total limit)
- Mastodon: Varies by instance
- Matrix: Varies by homeserver

Per-username configs can help avoid rate limits by distributing posts across accounts.

---

## Migration Guide

### From Single Account to Per-Username

**Current Setup:**
```bash
TWITCH_USERNAME=alice
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/111/aaa
BLUESKY_HANDLE=bot.bsky.social
```

**Goal:** Add Bob and Carol with their own Discord channels.

**Step 1:** Add new streamers (keep default)
```bash
TWITCH_USERNAME=alice,bob,carol
# All post to same Discord webhook (backward compatible)
```

**Step 2:** Create dedicated webhooks in Discord
- Server Settings → Integrations → Webhooks
- Create "Alice Streams", "Bob Streams", "Carol Streams" webhooks
- Copy webhook URLs

**Step 3:** Add per-username configs
```bash
DISCORD_WEBHOOK_TWITCH_ALICE=https://discord.com/api/webhooks/111/aaa
DISCORD_WEBHOOK_TWITCH_BOB=https://discord.com/api/webhooks/222/bbb
DISCORD_WEBHOOK_TWITCH_CAROL=https://discord.com/api/webhooks/333/ccc
```

**Step 4:** Restart and verify
```bash
# Restart Stream Daemon
# Check logs for "Using per-user webhook for twitch/alice"
# Verify each streamer posts to correct channel
```

### From Per-Platform to Per-Username

If you're already using per-platform Discord webhooks (Mode 3), you can extend to per-username (Mode 4):

**Current (Per-Platform):**
```bash
DISCORD_WEBHOOK_TWITCH=https://discord.com/api/webhooks/111/twitch
DISCORD_WEBHOOK_YOUTUBE=https://discord.com/api/webhooks/222/youtube
```

**Enhanced (Per-Username):**
```bash
# Keep per-platform as fallback
DISCORD_WEBHOOK_TWITCH=https://discord.com/api/webhooks/111/twitch
DISCORD_WEBHOOK_YOUTUBE=https://discord.com/api/webhooks/222/youtube

# Add per-username for specific streamers
DISCORD_WEBHOOK_TWITCH_ALICE=https://discord.com/api/webhooks/333/alice
DISCORD_WEBHOOK_TWITCH_BOB=https://discord.com/api/webhooks/444/bob
# Other Twitch streamers use per-platform fallback
```

---

## Complete Example Configuration

### Scenario: 5 Streamers Across 3 Platforms

**Streamers:**
- Alice: Twitch only
- Bob: Twitch + YouTube
- Carol: Kick only
- Dave: YouTube only
- Eve: Twitch only

**Requirements:**
- Alice and Bob have dedicated Discord channels and Bluesky accounts
- Carol, Dave, Eve share default social accounts
- All Matrix posts go to same room

### Configuration

```bash
# Stream Daemon Config
TWITCH_USERNAME=alice,bob,eve
YOUTUBE_CHANNEL_ID=UCbobyyy,UCdavexxx
KICK_USERNAME=carol

# Discord: Per-username for Alice and Bob
DISCORD_ENABLE_POSTING=True
DISCORD_WEBHOOK_TWITCH_ALICE=https://discord.com/api/webhooks/111/alice
DISCORD_ROLE_TWITCH_ALICE=111111111111111111

DISCORD_WEBHOOK_TWITCH_BOB=https://discord.com/api/webhooks/222/bob
DISCORD_ROLE_TWITCH_BOB=222222222222222222

# Discord: Per-platform for Bob's YouTube (different channel than Twitch)
DISCORD_WEBHOOK_YOUTUBE_UCBOBYYY=https://discord.com/api/webhooks/333/bob-youtube
DISCORD_ROLE_YOUTUBE_UCBOBYYY=333333333333333333

# Discord: Default for Carol, Dave, Eve
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/999/default
DISCORD_ROLE=999999999999999999

# Bluesky: Per-username for Alice and Bob
BLUESKY_ENABLE_POSTING=True
BLUESKY_HANDLE_TWITCH_ALICE=alice-streams.bsky.social
BLUESKY_APP_PASSWORD_TWITCH_ALICE=alice_app_password

BLUESKY_HANDLE_TWITCH_BOB=bob-gaming.bsky.social
BLUESKY_APP_PASSWORD_TWITCH_BOB=bob_app_password

# Bluesky: Default for others
BLUESKY_HANDLE=default-bot.bsky.social
BLUESKY_APP_PASSWORD=default_app_password

# Mastodon: All use default
MASTODON_ENABLE_POSTING=True
MASTODON_API_BASE_URL=https://mastodon.social
MASTODON_CLIENT_ID=default_client_id
MASTODON_CLIENT_SECRET=default_client_secret
MASTODON_ACCESS_TOKEN=default_access_token

# Matrix: All use default room
MATRIX_ENABLE_POSTING=True
MATRIX_HOMESERVER=https://matrix.org
MATRIX_ROOM_ID=!streams:matrix.org
MATRIX_USERNAME=@streams-bot:matrix.org
MATRIX_PASSWORD=bot_password
```

### Expected Behavior

| Streamer | Platform | Discord Channel | Bluesky Account | Mastodon | Matrix |
|----------|----------|----------------|----------------|----------|---------|
| Alice | Twitch | `#alice-streams` (per-user) | `alice-streams.bsky.social` (per-user) | `default` | `!streams:matrix.org` |
| Bob | Twitch | `#bob-streams` (per-user) | `bob-gaming.bsky.social` (per-user) | `default` | `!streams:matrix.org` |
| Bob | YouTube | `#bob-youtube` (per-user) | `default-bot.bsky.social` | `default` | `!streams:matrix.org` |
| Carol | Kick | `#default` (default) | `default-bot.bsky.social` | `default` | `!streams:matrix.org` |
| Dave | YouTube | `#default` (default) | `default-bot.bsky.social` | `default` | `!streams:matrix.org` |
| Eve | Twitch | `#default` (default) | `default-bot.bsky.social` | `default` | `!streams:matrix.org` |

---

## See Also

- [Discord Platform Documentation](../platforms/social/discord.md)
- [Per-Username Discord Testing Guide](./per-username-discord-testing.md)
- [Multiple Streams Feature](../features/multi-platform.md)
- [Secrets Management Guide](./secrets.md)
