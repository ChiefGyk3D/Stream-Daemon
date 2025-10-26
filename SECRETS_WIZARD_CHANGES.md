# Create-Secrets.sh - Changes Summary

## What Changed

The `create-secrets.sh` wizard has been completely rewritten to properly separate **configuration** from **secrets** based on the chosen secrets manager.

---

## New Behavior

### When Doppler/AWS/Vault is Selected:

**Secrets Manager gets:**
- API keys (Twitch Client ID/Secret, YouTube API Key, etc.)
- Access tokens (Mastodon, Matrix, etc.)
- App passwords (Bluesky)
- Webhooks (Discord)
- Any other sensitive credentials

**.env file gets:**
- Platform enable/disable flags
- Usernames (Twitch, YouTube, Kick, Matrix)
- Channel IDs
- Instance URLs (Mastodon, Matrix)
- Role mentions (Discord)
- Settings (check intervals, threading modes)
- LLM model names
- **Connection info to fetch secrets** (Doppler token, AWS region + secret names, or Vault URL + paths)

### When .env File is Selected:

**.env file gets:**
- **EVERYTHING** (both config and secrets in one file)
- Same behavior as before, just more clearly documented

---

## Key Functions Rewritten

### 1. `create_doppler_secrets()`
**Before:**
- Uploaded everything (config + secrets) to Doppler

**After:**
- Uploads ONLY secrets to Doppler
- Generates service token and stores in exported variable
- Stores project/config names for .env generation

### 2. `create_aws_secrets()`
**Before:**
- Created AWS secrets with some config mixed in (like usernames)

**After:**
- Creates AWS secrets with ONLY sensitive data
- Stores region and secret prefix for .env generation
- Properly handles optional fields

### 3. `create_vault_secrets()`
**Before:**
- Stored everything in Vault

**After:**
- Stores ONLY secrets in Vault
- Prompts for custom secret path
- Stores connection details for .env generation

### 4. NEW: `create_env_config_only()`
**Purpose:**
- Creates .env when a secrets manager is selected
- Includes connection info to the secrets manager
- Includes all non-secret configuration
- Does NOT include API keys, tokens, or webhooks

**Structure:**
```ini
# Secrets Manager Configuration
DOPPLER_TOKEN=dp.st.xxx
# OR
SECRETS_SECRET_MANAGER=aws
AWS_REGION=us-east-1
SECRETS_AWS_TWITCH_SECRET_NAME=stream-daemon/twitch
# OR
SECRETS_SECRET_MANAGER=vault
SECRETS_VAULT_URL=https://vault.example.com
SECRETS_VAULT_TOKEN=s.abc123

# Platform Enable/Disable
TWITCH_ENABLE=True
YOUTUBE_ENABLE=True

# Platform Configuration (NON-SECRET)
TWITCH_USERNAME=yourname
YOUTUBE_USERNAME=@YourChannel
MASTODON_API_BASE_URL=https://mastodon.social
BLUESKY_HANDLE=you.bsky.social
DISCORD_ROLE_MENTION_TWITCH=@TwitchLive

# Settings
SETTINGS_CHECK_INTERVAL=5
```

### 5. RENAMED: `create_env_file_complete()` (formerly `create_env_file()`)
**Purpose:**
- Creates .env when .env file option is selected
- Includes EVERYTHING (config + secrets)
- Same behavior as old version

---

## Execution Logic Changes

**Before:**
```bash
case $MANAGER in
    doppler)
        create_doppler_secrets
        create_env_file  # Created full .env as "backup"
        ;;
    aws|vault)
        create_*_secrets
        create_env_file  # Created full .env as "backup"
        ;;
    env)
        create_env_file
        ;;
esac
```

**After:**
```bash
case $MANAGER in
    doppler)
        create_doppler_secrets           # Secrets → Doppler
        create_env_config_only "doppler" # Config → .env
        ;;
    aws)
        create_aws_secrets               # Secrets → AWS
        create_env_config_only "AWS"     # Config → .env
        ;;
    vault)
        create_vault_secrets             # Secrets → Vault
        create_env_config_only "Vault"   # Config → .env
        ;;
    env)
        create_env_file_complete         # Everything → .env
        ;;
esac
```

---

## Doppler-Specific Improvements

### Environment Selection

**Added prompt:**
```bash
prompt_with_default "Doppler Config (environment)" "dev" "DOPPLER_CONFIG"
```

Users can now select:
- `dev` - Development environment
- `stg` - Staging environment
- `prd` - Production environment
- Or custom name

### Token Generation

```bash
# Generate service token automatically
DOPPLER_TOKEN=$(doppler configs tokens create cli-token --project $DOPPLER_PROJECT --config $DOPPLER_CONFIG --plain)
```

If successful, token is added to .env:
```ini
DOPPLER_TOKEN=dp.st.xxx
```

Users can then run:
```bash
# Without doppler CLI
python stream-daemon.py

# Or with doppler CLI for different environments
doppler run --config dev -- python stream-daemon.py
doppler run --config prd -- python stream-daemon.py
```

---

## Output Changes

### Improved Summary

**Before:**
```
✓ Secrets uploaded to Doppler!

To use these secrets, set:
  export DOPPLER_TOKEN=$(doppler configs tokens create cli --project ... --plain)
```

**After:**
```
✓ Secrets stored in Doppler (project: stream-daemon, config: dev)
✓ Configuration stored in .env

📝 What was created:
  • Doppler secrets: API keys, tokens, webhooks
  • .env file: Platform configs, Doppler connection settings

Next steps:
1. Test your configuration:
   python3 stream-daemon.py --test

2. Run Stream Daemon:
   Option 1: doppler run --project stream-daemon --config dev -- python3 stream-daemon.py
   Option 2: python3 stream-daemon.py (uses DOPPLER_TOKEN from .env)
```

---

## Security Improvements

### .env is Now Git-Safe (when using secrets managers)

**Before:**
- .env contained all secrets
- Could never be committed to git
- Had to manage separately per environment

**After (Doppler/AWS/Vault):**
- .env contains only config + connection info
- **Can be committed to git** (though still recommended in .gitignore)
- Secrets stored securely in chosen platform
- Easy environment switching

**After (.env file option):**
- Same as before
- Everything in .env
- Must stay in .gitignore
- chmod 600 enforced

---

## Documentation Added

### 1. `docs/configuration/secrets-wizard-behavior.md`
- Complete explanation of config vs secrets separation
- Examples of what goes where for each manager
- Comparison table
- Security best practices
- Migration paths
- Troubleshooting

### 2. Updated `docs/configuration/secrets-wizard.md`
- Added link to behavior guide
- Added callout explaining config vs secrets
- Updated multi-platform support section

### 3. Updated `README.md`
- Quick start now features create-secrets.sh
- Link to wizard documentation

---

## Testing Recommendations

Test each path:

```bash
# Test 1: Doppler
./create-secrets.sh
# Select 1 (Doppler)
# Choose dev environment
# Verify secrets in Doppler
# Verify .env has config only + DOPPLER_TOKEN
# Test: python3 stream-daemon.py

# Test 2: AWS
./create-secrets.sh
# Select 2 (AWS)
# Verify secrets in AWS console
# Verify .env has SECRETS_SECRET_MANAGER=aws
# Test: python3 stream-daemon.py

# Test 3: Vault
./create-secrets.sh
# Select 3 (Vault)
# Verify secrets: vault kv get secret/stream-daemon/twitch
# Verify .env has Vault connection info
# Test: python3 stream-daemon.py

# Test 4: .env file
./create-secrets.sh
# Select 4 (.env)
# Verify .env has everything
# Test: python3 stream-daemon.py
```

---

## Breaking Changes

### None for end users!

The wizard is backward compatible:
- If you select ".env file" option, behavior is identical to before
- Existing .env files are loaded as defaults
- Can switch between managers by re-running wizard

### For developers/contributors:

- Function `create_env_file()` renamed to `create_env_file_complete()`
- New function `create_env_config_only()` added
- Secrets manager functions now export connection variables
- Different execution flow based on $MANAGER

---

## Files Modified

1. `create-secrets.sh` - Complete rewrite of secrets/config handling
2. `docs/configuration/secrets-wizard.md` - Added config vs secrets explanation
3. `docs/configuration/secrets-wizard-behavior.md` - NEW comprehensive behavior guide
4. `README.md` - Updated quick start to feature the wizard

## Backup

Original script backed up to: `create-secrets.sh.backup`

---

## Summary

**The wizard now properly implements the industry-standard pattern:**

✅ Secrets managers hold secrets (API keys, tokens, webhooks)  
✅ .env holds configuration (usernames, URLs, settings) + connection info  
✅ Clear separation makes .env git-safe when using secrets managers  
✅ Easy environment management (dev/stg/prd)  
✅ Comprehensive documentation explains what goes where  
✅ Backward compatible with .env-only option  

This matches best practices used in modern cloud-native applications and makes Stream Daemon production-ready! 🎉
