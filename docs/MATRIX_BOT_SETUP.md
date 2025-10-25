# Matrix Bot Setup Guide

Complete guide to setting up a Matrix bot for stream notifications.

## Quick Start

1. **Create bot account** on your Matrix server
2. **Get room ID** from your notification room
3. **Add credentials** to Doppler or `.env`
4. **Invite bot** to your room
5. **Test** the integration

---

## Step 1: Create a Bot Account

### Option A: Using Element Web Client

1. **Log out** of your current account (if logged in)
2. **Register new account**:
   - Go to https://matrix.chiefgyk3d.com (or use Element with your homeserver)
   - Click "Create Account"
   - Username: `streambot` (or your preferred bot name)
   - Full Matrix ID will be: `@streambot:matrix.chiefgyk3d.com`
   - Set a strong password
3. **Save credentials**:
   - Username: `@streambot:matrix.chiefgyk3d.com`
   - Password: (your chosen password)

### Option B: Using Synapse CLI (if you have server access)

```bash
# SSH into your Matrix server
register_new_matrix_user -c /path/to/homeserver.yaml http://localhost:8008

# Follow prompts:
# Username: streambot
# Password: (your password)
# Make admin: No
```

---

## Step 2: Get Room ID

### Method 1: Element Web/Desktop

1. **Log into your personal account** (not the bot)
2. **Go to your stream notifications room**
3. **Click room name** at the top → **Settings**
4. **Scroll to "Advanced"** section
5. **Copy "Internal Room ID"**
   - Format: `!KHzbUMYDd0VnJyFqMXiPyfLipv4DKwn-stVz6RYD1VY:matrix.chiefgyk3d.com`
   - Note the `!` at the start - this is required!

### Method 2: Element Mobile

1. **Long press the room name**
2. **Room Details** → **Settings** → **Advanced**
3. **Copy Internal Room ID**

---

## Step 3: Add to Doppler (Recommended)

Using username/password authentication is easier for bot accounts since you don't need to manually extract access tokens.

### Add Secrets to Doppler

```bash
# Set homeserver
doppler secrets set MATRIX_HOMESERVER="https://matrix.chiefgyk3d.com"

# Set bot credentials (username/password method)
doppler secrets set MATRIX_USERNAME="@streambot:matrix.chiefgyk3d.com"
doppler secrets set MATRIX_PASSWORD="your_bot_password_here"

# Set room ID (include the ! prefix)
doppler secrets set MATRIX_ROOM_ID="!KHzbUMYDd0VnJyFqMXiPyfLipv4DKwn-stVz6RYD1VY:matrix.chiefgyk3d.com"
```

### Verify Secrets

```bash
# Check what's stored
doppler secrets get MATRIX_HOMESERVER --plain
doppler secrets get MATRIX_USERNAME --plain
doppler secrets get MATRIX_ROOM_ID --plain

# Don't show password in terminal history
doppler secrets get MATRIX_PASSWORD
```

---

## Step 4: Alternative - Use .env File (Development)

If you prefer to use `.env` file instead of Doppler:

```bash
# Edit your .env file
nano .env

# Update these lines:
MATRIX_ENABLE_POSTING=True
MATRIX_HOMESERVER=https://matrix.chiefgyk3d.com
MATRIX_ROOM_ID=!KHzbUMYDd0VnJyFqMXiPyfLipv4DKwn-stVz6RYD1VY:matrix.chiefgyk3d.com

# Method 2: Username/Password (recommended for bots)
MATRIX_USERNAME=@streambot:matrix.chiefgyk3d.com
MATRIX_PASSWORD=your_bot_password_here

# Comment out Method 1 if present:
#MATRIX_ACCESS_TOKEN=your_access_token_here
```

---

## Step 5: Invite Bot to Your Room

**IMPORTANT**: The bot cannot post messages to a room it's not a member of!

### Using Element

1. **Log into your personal account** (not the bot)
2. **Open your stream notifications room**
3. **Click room name** → **Invite**
4. **Type**: `@streambot:matrix.chiefgyk3d.com`
5. **Click Invite**

### Accept Invitation (Bot Account)

1. **Log into bot account** (`@streambot:matrix.chiefgyk3d.com`)
2. **Check invitations** (bell icon or left sidebar)
3. **Accept invitation** to the room

**OR** the daemon will auto-accept if you give it permission (advanced).

---

## Step 6: Test the Integration

### Quick Test

```bash
# Run the Matrix test
doppler run -- python3 tests/test_matrix.py

# Or without Doppler
python3 tests/test_matrix.py
```

### What Should Happen

1. ✓ Daemon connects to `https://matrix.chiefgyk3d.com`
2. ✓ Logs in with username/password
3. ✓ Gets temporary access token
4. ✓ Posts 3 test messages to the room
5. ✓ Messages appear in your Matrix room

### Expected Output

```
🔐 Authenticating Matrix...
✓ Matrix authenticated successfully
📝 Testing Matrix posting...
✓ Matrix message posted
✓ Matrix message posted
✓ Matrix message posted
✅ Matrix test completed successfully!
```

---

## Troubleshooting

### "403 Forbidden" Error

**Problem**: Bot not a member of the room

**Solution**:
1. Verify bot was invited to room
2. Check bot accepted the invitation
3. Confirm room ID is correct (includes `!` prefix)

### "401 Unauthorized" Error

**Problem**: Invalid credentials

**Solution**:
1. Verify username format: `@streambot:matrix.chiefgyk3d.com`
2. Check password is correct
3. Ensure homeserver URL is correct
4. Try resetting bot password

### "404 Not Found" Error

**Problem**: Room doesn't exist or wrong room ID

**Solution**:
1. Double-check room ID (must start with `!`)
2. Verify you copied the full room ID including `:matrix.chiefgyk3d.com`
3. Ensure room wasn't deleted

### Homeserver Connection Issues

**Problem**: Can't connect to `https://matrix.chiefgyk3d.com`

**Solution**:
```bash
# Test homeserver is responding
curl -s https://matrix.chiefgyk3d.com/_matrix/client/versions

# Should return JSON like:
# {"versions":["r0.0.1","r0.1.0",...]}
```

### Wrong Homeserver (404 HTML Response)

**Problem**: Getting WordPress 404 page instead of Matrix API

**Solution**: 
- Make sure you're using `https://matrix.chiefgyk3d.com` not `https://chiefgyk3d.com`
- The Matrix server must be on a different subdomain/port than your website

---

## Security Best Practices

### For Production

1. **Use Doppler** (or AWS/Vault) - never commit credentials to git
2. **Dedicated bot account** - don't use your personal account
3. **Strong password** - use password manager to generate
4. **Limit bot permissions** - don't make it a room admin
5. **Rotate credentials** - change password periodically

### For Development

1. **Use .env** - already in `.gitignore`
2. **Separate bot account** - don't use production bot
3. **Test room** - use different room than production

---

## Advanced: Access Token Method

If you prefer to use access tokens instead of username/password:

### Get Access Token

1. **Log into bot account** in Element
2. **Settings** → **Help & About** → **Advanced**
3. **Access Token** → **Click to reveal**
4. **Copy the token** (starts with `syt_`)

### Add to Doppler

```bash
# Remove username/password
doppler secrets delete MATRIX_USERNAME
doppler secrets delete MATRIX_PASSWORD

# Add access token
doppler secrets set MATRIX_ACCESS_TOKEN="syt_your_token_here"
```

### Add to .env

```bash
# Comment out username/password
#MATRIX_USERNAME=@streambot:matrix.chiefgyk3d.com
#MATRIX_PASSWORD=your_bot_password_here

# Add access token
MATRIX_ACCESS_TOKEN=syt_your_token_here
```

**Note**: Access tokens don't expire but can't be rotated automatically like username/password auth.

---

## Authentication Priority

The daemon uses this priority order for authentication:

1. **Username/Password (FIRST PRIORITY)** - If both `MATRIX_USERNAME` and `MATRIX_PASSWORD` are set
   - Logs in to get fresh access token on each startup
   - Automatic token rotation
   - **If these are set, any MATRIX_ACCESS_TOKEN is IGNORED**

2. **Access Token (FALLBACK)** - Only if username/password are NOT set
   - Uses static `MATRIX_ACCESS_TOKEN`
   - No automatic rotation
   - Manual management required

**Important**: If you have BOTH username/password AND access_token configured, the daemon will ALWAYS use username/password and ignore the access token. This prevents issues with stale or placeholder tokens.

If using Doppler/AWS/Vault, secrets manager values **always override** `.env` values.

---

## Next Steps

After successful setup:

1. Enable posting in your `.env`: `MATRIX_ENABLE_POSTING=True`
2. Run the full daemon: `doppler run -- python3 stream-daemon.py`
3. Monitor logs for Matrix notifications
4. Check your Matrix room for stream announcements

## Room ID Format

Your room ID should look like:
```
!KHzbUMYDd0VnJyFqMXiPyfLipv4DKwn-stVz6RYD1VY:matrix.chiefgyk3d.com
```

**Parts**:
- `!` - Required prefix (indicates it's a room ID)
- `KHzbUMYDd0VnJyFqMXiPyfLipv4DKwn-stVz6RYD1VY` - Unique room identifier
- `:matrix.chiefgyk3d.com` - Your homeserver domain

---

## Need Help?

- **Matrix Support**: https://matrix.org/docs/
- **Element Support**: https://element.io/help
- **Synapse Docs**: https://matrix-org.github.io/synapse/
