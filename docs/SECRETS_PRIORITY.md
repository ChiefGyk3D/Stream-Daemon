# Secrets Manager Priority System

## Overview

Stream Daemon uses a **priority-based system** for loading secrets and webhooks. When a secrets manager (Doppler, AWS Secrets Manager, or HashiCorp Vault) is enabled, it **automatically overrides** values in your `.env` file for credentials.

## Priority Order

For secrets, API keys, tokens, and webhooks:

```
1. Secrets Manager (Doppler/AWS/Vault) ← HIGHEST PRIORITY
2. .env file                            ← FALLBACK
3. None (not found)
```

This means:
- ✅ Production secrets in Doppler/AWS/Vault **always win**
- ✅ `.env` values serve as **fallback** for development
- ✅ You can safely keep credentials in `.env` for local dev
- ✅ Production deployments automatically use secrets manager

## What Gets Overridden

When a secrets manager is enabled (`SECRETS_SECRET_MANAGER=doppler/aws/vault`), the following values are **overridden** if found in the secrets manager:

### API Keys & Tokens
- `YOUTUBE_API_KEY`
- `MASTODON_ACCESS_TOKEN`
- `MASTODON_CLIENT_ID`
- `MASTODON_CLIENT_SECRET`
- `BLUESKY_APP_PASSWORD`
- `MATRIX_ACCESS_TOKEN` (only used if `MATRIX_USERNAME`/`MATRIX_PASSWORD` not set)
- `MATRIX_USERNAME` (takes priority over access token)
- `MATRIX_PASSWORD` (takes priority over access token)

### OAuth Credentials
- `TWITCH_CLIENT_ID`
- `TWITCH_CLIENT_SECRET`
- `KICK_CLIENT_ID`
- `KICK_CLIENT_SECRET`

### Webhooks
- `DISCORD_WEBHOOK_URL`
- `DISCORD_WEBHOOK_TWITCH`
- `DISCORD_WEBHOOK_YOUTUBE`
- `DISCORD_WEBHOOK_KICK`

## What Stays in .env

These values are **configuration**, not secrets, and are **always read from `.env`**:

### Platform Enables
- `TWITCH_ENABLE`
- `YOUTUBE_ENABLE`
- `KICK_ENABLE`
- `MASTODON_ENABLE_POSTING`
- `BLUESKY_ENABLE_POSTING`
- `DISCORD_ENABLE_POSTING`

### Usernames & Handles
- `TWITCH_USERNAME`
- `YOUTUBE_USERNAME`
- `KICK_USERNAME`
- `BLUESKY_HANDLE`
- `MASTODON_API_BASE_URL`

### Messages & Settings
- `DISCORD_ENDED_MESSAGE`
- `DISCORD_ENDED_MESSAGE_TWITCH`
- `DISCORD_ENDED_MESSAGE_YOUTUBE`
- `DISCORD_ENDED_MESSAGE_KICK`
- `SETTINGS_CHECK_INTERVAL`
- `SETTINGS_MULTISTREAMING_STRATEGY`

### Secrets Manager Config
- `SECRETS_SECRET_MANAGER`
- `DOPPLER_TOKEN`
- `SECRETS_DOPPLER_*_SECRET_NAME`
- `SECRETS_AWS_*_SECRET_NAME`
- `SECRETS_VAULT_*_PATH`

## Special Case: Matrix Authentication Priority

Matrix supports two authentication methods, and they have their own priority order:

### Matrix Auth Priority (within each source)

```
1. Username/Password (if BOTH are set) ← HIGHEST
2. Access Token (fallback)             ← LOWEST
```

**Important**: If you configure BOTH username/password AND access_token, the daemon will:
- ✅ Use username/password to login and get a fresh token
- ✅ Ignore the access_token value completely
- ✅ Log "Using username/password authentication (auto-rotation enabled)"

This prevents issues with stale or placeholder access tokens.

**Example - Both Configured:**
```bash
# Doppler secrets
MATRIX_USERNAME=@streambot:matrix.chiefgyk3d.com
MATRIX_PASSWORD=secret_pass_123
MATRIX_ACCESS_TOKEN=syt_old_token_here  # This will be IGNORED
```

**Result**: Daemon uses username/password, ignores access token.

**Example - Access Token Only:**
```bash
# Doppler secrets
MATRIX_ACCESS_TOKEN=syt_valid_token_here
# No username or password set
```

**Result**: Daemon uses access token.

---

## Usage Examples

### Scenario 1: Local Development
`.env` file:
```bash
TWITCH_ENABLE=True
TWITCH_USERNAME=chiefgyk3d
TWITCH_CLIENT_ID=dev_client_id_12345
TWITCH_CLIENT_SECRET=dev_client_secret_67890

SECRETS_SECRET_MANAGER=none
```

**Result:** Uses `.env` values (no secrets manager)

---

### Scenario 2: Production with Doppler
`.env` file:
```bash
TWITCH_ENABLE=True
TWITCH_USERNAME=chiefgyk3d
TWITCH_CLIENT_ID=dev_client_id_12345      # ← Ignored!
TWITCH_CLIENT_SECRET=dev_client_secret_67890  # ← Ignored!

SECRETS_SECRET_MANAGER=doppler
SECRETS_DOPPLER_TWITCH_SECRET_NAME=TWITCH
```

Doppler secrets:
```bash
TWITCH_CLIENT_ID=prod_client_id_abcxyz
TWITCH_CLIENT_SECRET=prod_client_secret_qwerty
```

**Result:** 
- ✅ Uses Doppler's `prod_client_id_abcxyz` (overrides `.env`)
- ✅ Uses Doppler's `prod_client_secret_qwerty` (overrides `.env`)
- ✅ Uses `.env` for `TWITCH_USERNAME` (configuration, not secret)

---

### Scenario 3: Partial Doppler Configuration
`.env` file:
```bash
TWITCH_ENABLE=True
TWITCH_USERNAME=chiefgyk3d
TWITCH_CLIENT_ID=fallback_client_id
TWITCH_CLIENT_SECRET=fallback_secret

SECRETS_SECRET_MANAGER=doppler
SECRETS_DOPPLER_TWITCH_SECRET_NAME=TWITCH
```

Doppler secrets (only has client_id):
```bash
TWITCH_CLIENT_ID=prod_client_id
# TWITCH_CLIENT_SECRET not configured in Doppler
```

**Result:**
- ✅ Uses Doppler's `prod_client_id` (found in secrets manager)
- ✅ Falls back to `.env` `fallback_secret` (not found in Doppler)

---

### Scenario 4: Safe Development Workflow
1. **Development:**
   ```bash
   # .env - contains working dev credentials
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/123/dev
   SECRETS_SECRET_MANAGER=none
   ```
   
   Works locally with dev webhook.

2. **Deploy to Production:**
   ```bash
   # Same .env file, just change secrets manager
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/123/dev  # ← Ignored in prod
   SECRETS_SECRET_MANAGER=doppler
   ```
   
   Production automatically uses Doppler's webhook, `.env` value ignored.

3. **No need to modify .env** - secrets manager automatically takes priority!

## Benefits

### 🔒 Security
- Production secrets never need to be in `.env` (can stay in Doppler)
- `.env` can be safely committed with dummy/dev values
- No risk of accidentally using dev credentials in production

### 🛠️ Development
- Keep working credentials in `.env` for local testing
- No need to configure secrets manager for development
- Easy to switch between dev and prod environments

### 🚀 Deployment
- Same `.env` file works in dev and prod
- Just enable secrets manager and deploy
- No manual credential copying or environment-specific `.env` files

### 🔄 Fallback Safety
- If secrets manager is unavailable, falls back to `.env`
- Prevents total failure if secrets manager has issues
- Development workflow unchanged if secrets manager disabled

## Testing Priority

To verify the priority system is working:

```bash
# Run the priority test
doppler run -- python3 tests/test_secrets_priority.py
```

This test checks:
- ✅ Which secrets manager is enabled
- ✅ Whether secrets manager values override `.env`
- ✅ Fallback behavior when secrets not found
- ✅ Displays masked values for security

## Migration Guide

### From .env-only to Secrets Manager

1. **Keep your current `.env` file** - don't delete or comment out credentials yet
2. **Configure secrets in Doppler/AWS/Vault** with production values
3. **Enable secrets manager** in `.env`:
   ```bash
   SECRETS_SECRET_MANAGER=doppler  # or aws/vault
   ```
4. **Test** - verify production credentials are being used:
   ```bash
   doppler run -- python3 tests/test_secrets_priority.py
   ```
5. **Optional:** Comment out secrets in `.env` (but not required - they're ignored anyway)

### From Old Priority (env-first) to New Priority (secrets-first)

If you were using the old priority system where `.env` took precedence:

**Before (old behavior):**
- `.env` values always won
- Had to comment out `.env` credentials to use secrets manager
- Error-prone - easy to forget to comment out

**After (new behavior):**
- Secrets manager values always win
- `.env` values serve as fallback
- No need to comment out - just works

**Action Required:**
- ✅ None! The new system is safer and more intuitive
- ✅ Your existing setup will work even better
- ✅ `.env` values now serve as safe fallbacks

## Troubleshooting

### "Using .env value instead of Doppler"

Check:
1. Is `SECRETS_SECRET_MANAGER=doppler` set?
2. Is the secret name configured? (e.g., `SECRETS_DOPPLER_TWITCH_SECRET_NAME=TWITCH`)
3. Does the secret exist in Doppler? Run `doppler secrets` to verify
4. Is the key name correct? (e.g., `client_id`, not `clientId`)

### "No value found"

If neither secrets manager nor `.env` has a value:
1. Add to `.env` as fallback
2. Add to secrets manager for production
3. Check for typos in variable names

### "Values match (can't verify override)"

This means `.env` and secrets manager have identical values. To verify override:
1. Change `.env` value to something different (e.g., `TWITCH_CLIENT_ID=TEST_OVERRIDE`)
2. Run test again
3. Verify `get_secret()` still uses Doppler value (not `TEST_OVERRIDE`)
4. Change `.env` back when done testing

## See Also

- [DOPPLER_GUIDE.md](DOPPLER_GUIDE.md) - Complete Doppler setup
- [.env.example](.env.example) - Configuration template
- [tests/test_secrets_priority.py](tests/test_secrets_priority.py) - Priority test script
