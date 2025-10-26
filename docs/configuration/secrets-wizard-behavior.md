# Secrets Wizard Behavior - Config vs Secrets Separation

## Overview

The `create-secrets.sh` wizard intelligently separates **configuration** from **secrets** based on your chosen secrets manager. This document explains exactly what gets stored where.

---

## Visual Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    create-secrets.sh Wizard                      │
│                                                                   │
│  Collects:                                                       │
│  • Platform credentials (API keys, tokens, passwords)            │
│  • Configuration (usernames, URLs, settings)                     │
│  • Webhooks (Discord)                                            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
         ┌───────────────────────────────┐
         │  Which secrets manager?        │
         └───────────────┬───────────────┘
                         │
         ┌───────────────┼───────────────┬───────────────┐
         │               │               │               │
         ▼               ▼               ▼               ▼
  ┌──────────┐    ┌──────────┐   ┌──────────┐   ┌──────────┐
  │ Doppler  │    │   AWS    │   │  Vault   │   │   .env   │
  │          │    │ Secrets  │   │          │   │   File   │
  └────┬─────┘    └────┬─────┘   └────┬─────┘   └────┬─────┘
       │               │              │              │
       ▼               ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   Doppler    │ │     AWS      │ │    Vault     │ │              │
│              │ │              │ │              │ │              │
│ • API keys   │ │ • API keys   │ │ • API keys   │ │              │
│ • Tokens     │ │ • Tokens     │ │ • Tokens     │ │              │
│ • Passwords  │ │ • Passwords  │ │ • Passwords  │ │              │
│ • Webhooks   │ │ • Webhooks   │ │ • Webhooks   │ │              │
└──────────────┘ └──────────────┘ └──────────────┘ │              │
       +               +              +             │  EVERYTHING  │
       │               │              │             │              │
       ▼               ▼              ▼             │ • Configs    │
┌──────────────────────────────────────────┐       │ • Secrets    │
│              .env File                    │       │ • Usernames  │
│                                           │       │ • Settings   │
│ • Connection info (token/region/URL)     │       │ • API keys   │
│ • Platform enable flags                  │       │ • Webhooks   │
│ • Usernames (Twitch, YouTube, Kick)      │       │ • Everything │
│ • URLs (Mastodon, Matrix homeserver)     │       └──────────────┘
│ • Channel IDs                             │
│ • Settings (intervals, threading)         │
│ • Model names                             │
│                                           │
│ ✅ Git-safe (no secrets!)                │
└───────────────────────────────────────────┘
```

---

## Key Concept: Config vs Secrets

### Configuration (Non-Sensitive)
- Platform usernames
- Channel IDs
- Instance URLs  
- Enable/disable flags
- Settings (check intervals, threading modes)
- Model names
- Homeserver URLs
- Room IDs

### Secrets (Sensitive)
- API keys
- Client IDs and secrets
- Access tokens
- App passwords
- Webhooks
- Authentication credentials

---

## Behavior by Secrets Manager

### Option 1: Doppler

**What gets stored in Doppler:**
```
TWITCH_CLIENT_ID
TWITCH_CLIENT_SECRET
YOUTUBE_API_KEY
KICK_CLIENT_ID (if using OAuth)
KICK_CLIENT_SECRET (if using OAuth)
MASTODON_CLIENT_ID
MASTODON_CLIENT_SECRET
MASTODON_ACCESS_TOKEN
BLUESKY_APP_PASSWORD
DISCORD_WEBHOOK_URL
DISCORD_WEBHOOK_URL_TWITCH (if configured)
DISCORD_WEBHOOK_URL_YOUTUBE (if configured)
DISCORD_WEBHOOK_URL_KICK (if configured)
MATRIX_ACCESS_TOKEN (if using token auth)
MATRIX_PASSWORD (if using password auth)
LLM_GEMINI_API_KEY
```

**What gets stored in .env:**
```ini
# Doppler connection
DOPPLER_TOKEN=dp.st.xxx  # Service token (if generated)
# OR instructions to use: doppler run --project stream-daemon --config dev

# Platform enable flags
TWITCH_ENABLE=True
YOUTUBE_ENABLE=True
MASTODON_ENABLE_POSTING=True
# etc...

# Configuration (non-secrets)
TWITCH_USERNAME=yourname
YOUTUBE_USERNAME=@YourChannel
YOUTUBE_CHANNEL_ID=UC_xxx
KICK_USERNAME=kickuser
MASTODON_API_BASE_URL=https://mastodon.social
BLUESKY_HANDLE=you.bsky.social
DISCORD_ROLE_MENTION_TWITCH=@TwitchLive
DISCORD_UPDATE_LIVE_MESSAGE=True
DISCORD_UPDATE_INTERVAL=60
MATRIX_HOMESERVER=https://matrix.org
MATRIX_ROOM_ID=!abc:matrix.org
MATRIX_USERNAME=@bot:matrix.org
LLM_PROVIDER=gemini
LLM_GEMINI_MODEL=gemini-2.0-flash-exp

# Settings
SETTINGS_CHECK_INTERVAL=5
SETTINGS_POST_INTERVAL=60
MESSAGES_LIVE_THREADING_MODE=combined
MESSAGES_END_THREADING_MODE=single_when_all_end
```

**How to run:**
```bash
# Development (recommended)
doppler run --project stream-daemon --config dev -- python stream-daemon.py

# Production (with service token in .env)
python stream-daemon.py
```

**Multiple environments:**
```bash
# Create separate configs
doppler run --config dev -- python stream-daemon.py    # Development
doppler run --config stg -- python stream-daemon.py    # Staging  
doppler run --config prd -- python stream-daemon.py    # Production
```

---

### Option 2: AWS Secrets Manager

**What gets stored in AWS Secrets Manager:**

Secret: `stream-daemon/twitch`
```json
{
  "client_id": "abc123",
  "client_secret": "secret123"
}
```

Secret: `stream-daemon/youtube`
```json
{
  "api_key": "AIza..."
}
```

Secret: `stream-daemon/mastodon`
```json
{
  "client_id": "abc",
  "client_secret": "secret",
  "access_token": "token123"
}
```

Secret: `stream-daemon/bluesky`
```json
{
  "app_password": "pass"
}
```

Secret: `stream-daemon/discord`
```json
{
  "webhook_url": "https://discord.com/api/webhooks/...",
  "webhook_url_twitch": "https://...",
  "webhook_url_youtube": "https://..."
}
```

Secret: `stream-daemon/matrix`
```json
{
  "access_token": "token123"
}
```

Secret: `stream-daemon/llm`
```json
{
  "gemini_api_key": "AIza..."
}
```

**What gets stored in .env:**
```ini
# AWS connection
SECRETS_SECRET_MANAGER=aws
AWS_REGION=us-east-1
SECRETS_AWS_PREFIX=stream-daemon

# Secret names (auto-configured)
SECRETS_AWS_TWITCH_SECRET_NAME=stream-daemon/twitch
SECRETS_AWS_YOUTUBE_SECRET_NAME=stream-daemon/youtube
SECRETS_AWS_MASTODON_SECRET_NAME=stream-daemon/mastodon
SECRETS_AWS_BLUESKY_SECRET_NAME=stream-daemon/bluesky
SECRETS_AWS_DISCORD_SECRET_NAME=stream-daemon/discord
SECRETS_AWS_MATRIX_SECRET_NAME=stream-daemon/matrix
SECRETS_AWS_LLM_SECRET_NAME=stream-daemon/llm

# Platform enable flags
TWITCH_ENABLE=True
YOUTUBE_ENABLE=True
# etc...

# Configuration (same as Doppler example above)
TWITCH_USERNAME=yourname
YOUTUBE_USERNAME=@YourChannel
# etc...
```

**How to run:**
```bash
# AWS credentials configured via aws configure or IAM role
python stream-daemon.py
```

---

### Option 3: HashiCorp Vault

**What gets stored in Vault:**

Path: `secret/stream-daemon/twitch`
```
client_id: abc123
client_secret: secret123
```

Path: `secret/stream-daemon/youtube`
```
api_key: AIza...
```

Path: `secret/stream-daemon/mastodon`
```
client_id: abc
client_secret: secret
access_token: token123
```

Path: `secret/stream-daemon/discord`
```
webhook_url: https://discord.com/api/webhooks/...
webhook_url_twitch: https://...
```

Path: `secret/stream-daemon/llm`
```
gemini_api_key: AIza...
```

**What gets stored in .env:**
```ini
# Vault connection
SECRETS_SECRET_MANAGER=vault
SECRETS_VAULT_URL=https://vault.example.com
SECRETS_VAULT_TOKEN=s.abc123xyz

# Secret paths (auto-configured)
SECRETS_VAULT_TWITCH_SECRET_PATH=secret/stream-daemon/twitch
SECRETS_VAULT_YOUTUBE_SECRET_PATH=secret/stream-daemon/youtube
SECRETS_VAULT_MASTODON_SECRET_PATH=secret/stream-daemon/mastodon
SECRETS_VAULT_BLUESKY_SECRET_PATH=secret/stream-daemon/bluesky
SECRETS_VAULT_DISCORD_SECRET_PATH=secret/stream-daemon/discord
SECRETS_VAULT_MATRIX_SECRET_PATH=secret/stream-daemon/matrix
SECRETS_VAULT_LLM_SECRET_PATH=secret/stream-daemon/llm

# Platform enable flags
TWITCH_ENABLE=True
# etc...

# Configuration (same as above)
TWITCH_USERNAME=yourname
# etc...
```

**How to run:**
```bash
python stream-daemon.py
```

---

### Option 4: .env File Only

**What gets stored in .env:**

**EVERYTHING** - both configuration and secrets in one file:

```ini
# Stream Daemon Configuration
# Generated by create-secrets.sh

# ============================================
# Streaming Platforms
# ============================================

# Twitch
TWITCH_ENABLE=True
TWITCH_USERNAME=yourname
TWITCH_CLIENT_ID=abc123              # ← SECRET
TWITCH_CLIENT_SECRET=secret123       # ← SECRET

# YouTube
YOUTUBE_ENABLE=True
YOUTUBE_USERNAME=@YourChannel
YOUTUBE_API_KEY=AIza...              # ← SECRET

# ============================================
# Social Media Platforms
# ============================================

# Mastodon
MASTODON_ENABLE_POSTING=True
MASTODON_API_BASE_URL=https://mastodon.social
MASTODON_CLIENT_ID=abc               # ← SECRET
MASTODON_CLIENT_SECRET=secret        # ← SECRET
MASTODON_ACCESS_TOKEN=token123       # ← SECRET

# Bluesky
BLUESKY_ENABLE_POSTING=True
BLUESKY_HANDLE=you.bsky.social
BLUESKY_APP_PASSWORD=pass123         # ← SECRET

# Discord
DISCORD_ENABLE_POSTING=True
DISCORD_WEBHOOK_URL=https://...      # ← WEBHOOK/SECRET
DISCORD_ROLE_MENTION_TWITCH=@TwitchLive
DISCORD_UPDATE_LIVE_MESSAGE=True
DISCORD_UPDATE_INTERVAL=60

# Matrix
MATRIX_ENABLE_POSTING=True
MATRIX_HOMESERVER=https://matrix.org
MATRIX_ROOM_ID=!abc:matrix.org
MATRIX_ACCESS_TOKEN=token123         # ← SECRET

# ============================================
# AI/LLM Configuration
# ============================================

LLM_ENABLE=True
LLM_PROVIDER=gemini
LLM_GEMINI_API_KEY=AIza...           # ← SECRET
LLM_GEMINI_MODEL=gemini-2.0-flash-exp

# ============================================
# Stream Daemon Settings
# ============================================

SETTINGS_CHECK_INTERVAL=5
SETTINGS_POST_INTERVAL=60
MESSAGES_LIVE_THREADING_MODE=combined
MESSAGES_END_THREADING_MODE=single_when_all_end
```

**Security settings applied:**
- File permissions set to `chmod 600` (owner read/write only)
- `.gitignore` should exclude `.env`
- Wizard displays security warning

**How to run:**
```bash
python stream-daemon.py
```

---

## Comparison Table

| Aspect | Doppler | AWS Secrets | Vault | .env Only |
|--------|---------|-------------|-------|-----------|
| **Secrets stored** | Doppler cloud | AWS cloud | Vault server | .env file |
| **Config stored** | .env file | .env file | .env file | .env file |
| **.env has secrets?** | ❌ No | ❌ No | ❌ No | ✅ Yes |
| **.env git-safe?** | ✅ Yes* | ✅ Yes* | ✅ Yes* | ❌ No |
| **Rotation** | Easy | Medium | Easy | Manual |
| **Audit logging** | ✅ Yes | ✅ Yes | ✅ Yes | ❌ No |
| **Environments** | Built-in | Manual | Manual | Manual |
| **Cost** | Free tier | AWS pricing | Self-hosted | Free |

*Git-safe if you only commit non-secret config settings. Still recommended to keep .env in .gitignore.

---

## Security Best Practices

### When Using Secrets Managers (Doppler/AWS/Vault)

**DO:**
- ✅ Commit .env to git (it only has config, not secrets)
- ✅ Document which secrets manager is required
- ✅ Use different environments for dev/staging/prod
- ✅ Rotate secrets regularly via the secrets manager
- ✅ Use IAM roles/tokens with minimum required permissions

**DON'T:**
- ❌ Hard-code secrets in code
- ❌ Share secrets manager tokens publicly
- ❌ Use production secrets in development

### When Using .env File

**DO:**
- ✅ Add `.env` to `.gitignore`
- ✅ Set `chmod 600 .env`
- ✅ Back up .env securely
- ✅ Use different .env files per environment (.env.dev, .env.prod)
- ✅ Consider migrating to secrets manager for production

**DON'T:**
- ❌ Commit .env to git
- ❌ Share .env in plaintext
- ❌ Use same .env across environments
- ❌ Store .env in cloud storage without encryption

---

## Migration Paths

### From .env to Doppler
```bash
# Run wizard, select Doppler
./scripts/create-secrets.sh

# Wizard loads existing .env values
# Secrets → Doppler
# Config → new .env (safe to commit)
# Old .env → backup
```

### From Doppler to AWS
```bash
# Run wizard, select AWS
./scripts/create-secrets.sh

# Wizard asks for platform configs (Doppler has secrets only)
# You'll need to re-enter configs
# Or manually copy from old .env
```

### From .env to Production
1. Choose secrets manager (Doppler recommended)
2. Run wizard
3. Test with new setup
4. Update deployment scripts
5. Securely delete old .env

---

## Troubleshooting

### "I chose Doppler but .env still has secrets"
- You may have selected option 4 by mistake
- Re-run wizard and select option 1 (Doppler)
- Check that secrets went to Doppler: `doppler secrets --project stream-daemon --config dev`

### ".env doesn't have my usernames/configs"
- If you chose .env file option, everything should be there
- If you chose secrets manager, check .env for config section (after secrets manager connection details)

### "Stream Daemon can't find my secrets"
- **Doppler**: Run with `doppler run --project stream-daemon --config dev -- python stream-daemon.py`
- **AWS**: Check `SECRETS_SECRET_MANAGER=aws` is set in .env
- **Vault**: Check `SECRETS_SECRET_MANAGER=vault` and connection vars are set
- **.env**: Make sure .env is in the same directory as stream-daemon.py

---

## See Also

- [Secrets Wizard Guide](secrets-wizard.md) - Full interactive setup guide
- [Secrets Management](secrets.md) - Manual secrets configuration
- [Doppler Integration](secrets.md#doppler) - Doppler-specific setup
- [AWS Secrets Manager](secrets.md#aws-secrets-manager) - AWS-specific setup
- [HashiCorp Vault](secrets.md#hashicorp-vault) - Vault-specific setup
