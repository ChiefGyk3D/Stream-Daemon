# Matrix Bot Setup - Quick Reference

## What I Fixed

1. ✅ Updated `.env.example` to use `https://matrix.org` (correct homeserver)
2. ✅ Set username/password as the default method (better for bot accounts)
3. ✅ Created comprehensive setup guide in `docs/MATRIX_BOT_SETUP.md`

## Quick Setup Steps

### 1. Create Bot Account

**Option A - Web Interface:**
- Go to https://matrix.org or use Element app
- Create account: `@streambot:matrix.org` (or your preferred name)
- Set a strong password

**Option B - Server CLI (if you have SSH access):**
```bash
register_new_matrix_user -c /path/to/homeserver.yaml http://localhost:8008
```

### 2. Get Room ID

- Open your stream notification room in Element
- Room Settings → Advanced → Internal Room ID
- Copy the ID (starts with `!` like `!KHzbUMYDd0VnJyFqMXiPyfLipv4DKwn-stVz6RYD1VY:matrix.org`)

### 3. Add to Doppler

```bash
doppler secrets set MATRIX_HOMESERVER="https://matrix.org"
doppler secrets set MATRIX_USERNAME="@streambot:matrix.org"
doppler secrets set MATRIX_PASSWORD="your_bot_password"
doppler secrets set MATRIX_ROOM_ID="!your_room_id:matrix.org"
```

**Verify:**
```bash
doppler secrets get MATRIX_HOMESERVER --plain
doppler secrets get MATRIX_USERNAME --plain
doppler secrets get MATRIX_ROOM_ID --plain
```

### 4. Invite Bot to Room

**CRITICAL STEP** - The bot CANNOT post without being in the room!

1. Log into your personal account
2. Open the stream notification room
3. Click room name → Invite
4. Enter: `@streambot:matrix.org`
5. Click Invite

**Accept Invitation:**
1. Log into bot account
2. Check invitations (bell icon)
3. Accept the room invitation

### 5. Test

```bash
doppler run -- python3 tests/test_matrix.py
```

## Using .env Instead of Doppler

Edit your `.env` file:

```bash
MATRIX_ENABLE_POSTING=True
MATRIX_HOMESERVER=https://matrix.org
MATRIX_USERNAME=@streambot:matrix.org
MATRIX_PASSWORD=your_bot_password
MATRIX_ROOM_ID=!your_room_id:matrix.org
```

Then test without Doppler:
```bash
python3 tests/test_matrix.py
```

## Two Authentication Methods

### Method 1: Username/Password (RECOMMENDED for bots)
✅ Automatic token rotation
✅ Fresh token on each startup
✅ Easier to set up (no manual token extraction)
❌ Password stored in config

## Two Authentication Methods

### Method 1: Username/Password (RECOMMENDED for bots)
✅ Automatic token rotation
✅ Fresh token on each startup
✅ Easier to set up (no manual token extraction)
✅ **Takes priority if both methods are configured**
❌ Password stored in config

**In Doppler/env:**
```
MATRIX_USERNAME=@streambot:matrix.chiefgyk3d.com
MATRIX_PASSWORD=your_password
```

### Method 2: Access Token
✅ No password in config
✅ Token never expires
❌ Manual extraction required
❌ No automatic rotation
❌ **Ignored if username/password are set**

**To get access token:**
1. Log into bot in Element
2. Settings → Help & About → Advanced → Access Token
3. Click to reveal and copy

**In Doppler/env:**
```
MATRIX_ACCESS_TOKEN=syt_your_token_here
```

**IMPORTANT**: If you have both username/password AND access_token configured, the daemon will use username/password and ignore the access token. This is by design to prevent stale token issues.

### Method 2: Access Token
✅ No password in config
✅ Token never expires
❌ Manual extraction required
❌ No automatic rotation

**To get access token:**
1. Log into bot in Element
2. Settings → Help & About → Advanced → Access Token
3. Click to reveal and copy

**In Doppler/env:**
```
MATRIX_ACCESS_TOKEN=syt_your_token_here
```

## Common Issues

### 403 Forbidden
- **Cause**: Bot not in room
- **Fix**: Invite bot and accept invitation

### 401 Unauthorized
- **Cause**: Wrong credentials
- **Fix**: Verify username format and password

### 404 Not Found
- **Cause**: Wrong room ID or homeserver
- **Fix**: 
  - Verify room ID starts with `!`
  - Confirm using `matrix.org` not `chiefgyk3d.com`

### WordPress 404 Page
- **Cause**: Wrong homeserver URL
- **Fix**: Must use `https://matrix.org` (the Matrix subdomain)

## Secrets Priority

**If using secrets manager (Doppler/AWS/Vault):**
1. Secrets manager values (FIRST - overrides everything)
2. `.env` values (FALLBACK only if secrets manager not set)

**Authentication method priority:**
1. Username/password (FIRST - if both are set, generates fresh token)
2. Access token (FALLBACK - only if username/password not set)

**Key Point**: If you configure BOTH username/password AND access_token, username/password will be used and the access_token will be ignored. This prevents stale token issues.

## Files Updated

- `.env.example` - Updated default homeserver and auth method
- `docs/MATRIX_BOT_SETUP.md` - Complete setup guide
- `docs/MATRIX_BOT_QUICK_START.md` - This quick reference

## Next Steps

1. Create your bot account
2. Get your room ID
3. Add credentials to Doppler (or `.env`)
4. **INVITE BOT TO ROOM** (don't forget this!)
5. Run test: `doppler run -- python3 tests/test_matrix.py`
6. Enable posting: Set `MATRIX_ENABLE_POSTING=True`
7. Run daemon: `doppler run -- python3 stream-daemon.py`

For detailed instructions, see `docs/MATRIX_BOT_SETUP.md`.
