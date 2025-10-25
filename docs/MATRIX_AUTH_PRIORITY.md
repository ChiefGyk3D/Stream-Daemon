# Matrix Authentication Priority - Fixed

## The Problem

Previously, if you had both `MATRIX_ACCESS_TOKEN` and `MATRIX_USERNAME`/`MATRIX_PASSWORD` configured, the daemon would:
- Try the access token first
- Only fall back to username/password if the access token was missing

This caused issues when:
- You had a placeholder access token (like `syt_your_access_token_here`)
- You had an old/stale access token
- You wanted to use username/password but forgot to remove the access token

## The Solution

**New behavior**: Username/password authentication now takes **PRIORITY** over access tokens.

```
Priority 1: Username/Password (if BOTH are set)
Priority 2: Access Token (only if username/password NOT set)
```

## Benefits

✅ **No more stale token issues** - Fresh token on every startup when using username/password
✅ **Clear authentication method** - Logs show which method is being used
✅ **Automatic token rotation** - Best security practice for bot accounts
✅ **Predictable behavior** - If you set username/password, that's what's used

## How It Works

### Case 1: Username/Password Set (Recommended)
```bash
# In Doppler or .env
MATRIX_USERNAME=@streambot:matrix.chiefgyk3d.com
MATRIX_PASSWORD=your_password
MATRIX_ACCESS_TOKEN=syt_old_token  # This will be IGNORED
```

**Daemon logs:**
```
Using username/password authentication (auto-rotation enabled)
✓ Obtained Matrix access token (expires: never)
✓ Matrix logged in and obtained access token
✓ Matrix authenticated (!room_id)
```

**Result**: Fresh token generated on each startup, old access token ignored.

---

### Case 2: Access Token Only
```bash
# In Doppler or .env
MATRIX_ACCESS_TOKEN=syt_valid_token_here
# Username and password NOT set
```

**Daemon logs:**
```
Using static access token authentication
✓ Matrix authenticated (!room_id)
```

**Result**: Uses the static access token, no login performed.

---

### Case 3: Neither Set
```bash
# Nothing configured
```

**Daemon logs:**
```
✗ Matrix authentication failed - need either access_token OR username+password
```

**Result**: Authentication fails, Matrix posting disabled.

---

## Code Changes

### stream-daemon.py
Changed authentication logic to check username/password FIRST:

```python
# OLD (Wrong priority):
if self.access_token:
    # Use access token
else:
    if self.username and self.password:
        # Use username/password

# NEW (Correct priority):
if self.username and self.password:
    # Use username/password (PRIORITY)
else:
    # Fall back to access token
```

### Key Lines
- **Line ~1655**: Check for username/password first
- **Line ~1670**: Log which authentication method is being used
- **Line ~1675**: Only check access token if username/password not set

## Migration Guide

### If you were using ACCESS_TOKEN:

**No changes needed** - as long as you don't have username/password set, access tokens still work.

### If you were using USERNAME/PASSWORD:

**Check for leftover access tokens:**

```bash
# In Doppler
doppler secrets get MATRIX_ACCESS_TOKEN 2>&1 | grep "Could not find"
# Should show "Could not find" - that's good!

# In .env
grep "^MATRIX_ACCESS_TOKEN" .env
# Should be commented out or not exist
```

**If found, remove them:**

```bash
# Doppler
doppler secrets delete MATRIX_ACCESS_TOKEN

# .env
sed -i 's/^MATRIX_ACCESS_TOKEN=/#MATRIX_ACCESS_TOKEN=/' .env
```

## Testing

Test that authentication works correctly:

```bash
# Run Matrix test
doppler run -- python3 tests/test_matrix.py

# Look for this log line:
# "Using username/password authentication (auto-rotation enabled)"
# OR
# "Using static access token authentication"
```

## Documentation Updates

Updated files:
- ✅ `.env.example` - Clarified authentication priority
- ✅ `docs/MATRIX_BOT_SETUP.md` - Updated priority section
- ✅ `docs/MATRIX_BOT_QUICK_START.md` - Added warning about both methods
- ✅ `docs/SECRETS_PRIORITY.md` - Added Matrix special case section
- ✅ `docs/MATRIX_AUTH_PRIORITY.md` - This file!

## Best Practices

### For Bot Accounts (Recommended)
```bash
# Use username/password for automatic rotation
MATRIX_USERNAME=@streambot:matrix.chiefgyk3d.com
MATRIX_PASSWORD=strong_random_password
# DON'T set MATRIX_ACCESS_TOKEN
```

### For Personal Accounts (Alternative)
```bash
# Use access token (manual management)
MATRIX_ACCESS_TOKEN=syt_your_token_here
# DON'T set MATRIX_USERNAME or MATRIX_PASSWORD
```

### Never Do This
```bash
# BAD: Both methods configured
MATRIX_USERNAME=@bot:matrix.org
MATRIX_PASSWORD=password
MATRIX_ACCESS_TOKEN=syt_token  # Will be ignored! Confusing!
```

If you configure both, username/password wins and the access token is silently ignored.

## Troubleshooting

### "Using static access token authentication" but I set username/password

**Cause**: Username or password not being loaded from secrets manager/env

**Fix**:
```bash
# Check what's actually loaded
doppler secrets get MATRIX_USERNAME --plain
doppler secrets get MATRIX_PASSWORD  # Will be masked
```

### "M_UNKNOWN_TOKEN" errors

**Cause**: Invalid credentials

**Fix**:
1. Verify bot account exists
2. Check password is correct
3. Ensure bot is member of room
4. Verify homeserver URL

### Still using old access token

**Cause**: Username or password missing

**Fix**: Make sure BOTH are set, not just one:
```bash
doppler secrets set MATRIX_USERNAME="@bot:matrix.org"
doppler secrets set MATRIX_PASSWORD="your_password"
```

---

## Summary

- ✅ Username/password now takes priority over access tokens
- ✅ Automatic token rotation for better security
- ✅ Clear logging shows which method is active
- ✅ No more confusion from stale/placeholder tokens
- ✅ All documentation updated to reflect new behavior

**Bottom line**: Set username/password for bot accounts, remove any old access tokens, enjoy automatic token rotation! 🎉
