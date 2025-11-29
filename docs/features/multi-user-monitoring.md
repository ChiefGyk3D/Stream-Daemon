# Multi-User Stream Monitoring

Monitor multiple streamers across platforms with flexible per-user social media routing.

## Features

- **Multiple Streamers Per Platform**: Monitor multiple Twitch/YouTube/Kick channels simultaneously
- **Multiple Social Accounts**: Configure multiple accounts per social platform (Discord, Mastodon, Bluesky, Matrix)
- **Per-User Routing**: Each streamer can post to different combinations of social accounts
- **Shared Accounts**: Multiple streamers can share the same social account (e.g., shared Discord server)
- **Backward Compatible**: Existing single-user setups continue to work without changes

## Configuration Modes

### Simple Mode (Backward Compatible)

Uses existing `USERNAME`/`USERNAMES` environment variables. All streamers post to all enabled social platforms.

```bash
# Monitor multiple Twitch streamers
TWITCH_USERNAMES=gamer1,gamer2,gamer3

# Posts go to all enabled platforms
MASTODON_ENABLE_POSTING=true
DISCORD_ENABLE_POSTING=true
```

### Advanced Mode (Multi-User)

Uses `MULTI_USER_CONFIG` environment variable pointing to a JSON configuration file or JSON string.

```bash
# Point to config file
MULTI_USER_CONFIG=/path/to/multi-user-config.json

# Or inline JSON
MULTI_USER_CONFIG='{"streamers":[...]}'
```

## Configuration Structure

### JSON Schema

```json
{
  "streamers": [
    {
      "platform": "Twitch",
      "username": "streamer_name",
      "social_accounts": [
        {
          "platform": "discord",
          "account_id": "gaming_server"
        },
        {
          "platform": "mastodon",
          "account_id": "personal"
        }
      ]
    }
  ]
}
```

### Fields

- **platform**: Streaming platform name (`Twitch`, `YouTube`, `Kick`)
- **username**: Streamer's username/handle
- **social_accounts**: Array of social accounts to post to
  - **platform**: Social platform name (`discord`, `mastodon`, `bluesky`, `matrix`)
  - **account_id**: Unique identifier for this account (use `default` for single account)

## Example Scenarios

### Scenario 1: Two Streamers, Shared Discord, Separate Mastodon

```json
{
  "streamers": [
    {
      "platform": "Twitch",
      "username": "gamer1",
      "social_accounts": [
        {"platform": "discord", "account_id": "gaming"},
        {"platform": "mastodon", "account_id": "personal"}
      ]
    },
    {
      "platform": "Twitch",
      "username": "gamer2",
      "social_accounts": [
        {"platform": "discord", "account_id": "gaming"},
        {"platform": "mastodon", "account_id": "work"}
      ]
    }
  ]
}
```

**Environment Variables:**
```bash
# Shared Discord
DISCORD_GAMING_WEBHOOK_URL=https://discord.com/api/webhooks/...

# Separate Mastodon accounts
MASTODON_PERSONAL_API_BASE_URL=https://mastodon.social
MASTODON_PERSONAL_ACCESS_TOKEN=...

MASTODON_WORK_API_BASE_URL=https://mastodon.work
MASTODON_WORK_ACCESS_TOKEN=...
```

### Scenario 2: Multi-Platform Streamer with Platform-Specific Social Accounts

```json
{
  "streamers": [
    {
      "platform": "Twitch",
      "username": "pro_gamer",
      "social_accounts": [
        {"platform": "discord", "account_id": "twitch_fans"},
        {"platform": "bluesky", "account_id": "gaming"}
      ]
    },
    {
      "platform": "YouTube",
      "username": "@ProGamer",
      "social_accounts": [
        {"platform": "discord", "account_id": "youtube_fans"},
        {"platform": "mastodon", "account_id": "content"}
      ]
    }
  ]
}
```

### Scenario 3: Team/Organization with Multiple Streamers

```json
{
  "streamers": [
    {
      "platform": "Twitch",
      "username": "team_member_1",
      "social_accounts": [
        {"platform": "discord", "account_id": "team_server"},
        {"platform": "mastodon", "account_id": "member1"}
      ]
    },
    {
      "platform": "Twitch",
      "username": "team_member_2",
      "social_accounts": [
        {"platform": "discord", "account_id": "team_server"},
        {"platform": "bluesky", "account_id": "member2"}
      ]
    },
    {
      "platform": "YouTube",
      "username": "@TeamChannel",
      "social_accounts": [
        {"platform": "discord", "account_id": "team_server"},
        {"platform": "mastodon", "account_id": "official"}
      ]
    }
  ]
}
```

## Environment Variable Naming

For each `account_id`, append `_ACCOUNTID` (uppercase) to the standard environment variable names.

### Pattern

```
<PLATFORM>_<ACCOUNTID>_<SETTING>=value
```

### Examples

#### Discord

```bash
# Default account
DISCORD_WEBHOOK_URL=https://...

# Named accounts
DISCORD_GAMING_WEBHOOK_URL=https://...
DISCORD_YOUTUBE_FANS_WEBHOOK_URL=https://...
DISCORD_TEAM_SERVER_WEBHOOK_URL=https://...
```

#### Mastodon

```bash
# Default account
MASTODON_API_BASE_URL=https://mastodon.social
MASTODON_ACCESS_TOKEN=...

# Named accounts
MASTODON_PERSONAL_API_BASE_URL=https://mastodon.social
MASTODON_PERSONAL_ACCESS_TOKEN=...

MASTODON_WORK_API_BASE_URL=https://other.instance
MASTODON_WORK_ACCESS_TOKEN=...
```

#### Bluesky

```bash
# Default account
BLUESKY_HANDLE=user.bsky.social
BLUESKY_APP_PASSWORD=...

# Named accounts
BLUESKY_GAMING_HANDLE=gamer.bsky.social
BLUESKY_GAMING_APP_PASSWORD=...

BLUESKY_TECH_HANDLE=tech.bsky.social
BLUESKY_TECH_APP_PASSWORD=...
```

#### Matrix

```bash
# Default account
MATRIX_HOMESERVER=https://matrix.org
MATRIX_ACCESS_TOKEN=...
MATRIX_ROOM_ID=!abc:matrix.org

# Named accounts
MATRIX_GAMING_HOMESERVER=https://matrix.org
MATRIX_GAMING_ACCESS_TOKEN=...
MATRIX_GAMING_ROOM_ID=!xyz:matrix.org
```

## Configuration File Location

Recommended locations:

```bash
# Same directory as .env
MULTI_USER_CONFIG=./multi-user-config.json

# Docker volume mount
MULTI_USER_CONFIG=/config/multi-user-config.json

# Absolute path
MULTI_USER_CONFIG=/etc/stream-daemon/multi-user.json
```

## Validation

The daemon will validate your configuration on startup:

- ✅ All streamers have valid platform names
- ✅ All social accounts have valid platform names
- ✅ No duplicate streamer configurations
- ⚠️  Warning if streamer has no social accounts
- ❌ Error if required environment variables are missing for configured accounts

## Migration from Simple to Advanced Mode

1. **Backup your current `.env` file**

2. **Create `multi-user-config.json`** with your streamers

3. **Update environment variables** with account IDs if using multiple accounts per platform

4. **Add to `.env`:**
   ```bash
   MULTI_USER_CONFIG=./multi-user-config.json
   ```

5. **Test configuration:**
   ```bash
   # Check logs for validation messages
   docker-compose logs -f stream-daemon
   ```

6. **Rollback if needed:** Remove `MULTI_USER_CONFIG` to return to simple mode

## Logging

The daemon logs configuration mode on startup:

```
✓ Using advanced multi-user configuration mode
  • Monitoring Twitch/gamer1 → [discord:gaming, mastodon:personal]
  • Monitoring Twitch/gamer2 → [discord:gaming, bluesky:tech]
  • Monitoring YouTube/@Channel → [discord:youtube, mastodon:official]
```

Or:

```
✓ Using simple configuration mode (backward compatible)
  • Monitoring Twitch/gamer1
  • Monitoring Twitch/gamer2
  • Posting to: Mastodon, Discord, Bluesky
```

## Best Practices

1. **Use descriptive account IDs**: `gaming_server`, `personal_account`, `team_official`
2. **Start with simple mode**: Test basic functionality before adding complexity
3. **Test one streamer at a time**: Validate configuration incrementally
4. **Use JSON validator**: Ensure your config file is valid JSON before deploying
5. **Document your setup**: Add comments to your JSON (they're ignored by parser)
6. **Version control**: Keep your config file in git (exclude secrets in .env)

## Troubleshooting

### "No streamers configured"
- Check JSON syntax
- Ensure `MULTI_USER_CONFIG` path is correct
- Verify file is readable by daemon

### "Invalid multi-user config, falling back to simple mode"
- Check JSON structure matches schema
- Validate platform names are correct case
- Ensure social_accounts is an array

### "Streamer X has no social accounts configured"
- Add at least one social account to `social_accounts` array
- Or intentionally leave empty if testing streaming platform only

### Environment variable not found
- Check account_id matches between JSON and env vars
- Remember to use uppercase: `DISCORD_GAMING_WEBHOOK_URL` not `discord_gaming_webhook_url`
- Default account uses no suffix: `DISCORD_WEBHOOK_URL` not `DISCORD_DEFAULT_WEBHOOK_URL`

## See Also

- [Configuration Guide](../configuration/secrets.md)
- [Platform Setup Guides](../platforms/)
- [Example Config File](../../multi-user-config.example.json)
