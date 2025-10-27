# Secrets Management Guide

> **🔐 Keep your API keys secure with enterprise-grade secrets management**

Stream Daemon supports multiple secrets management solutions to keep your credentials safe and out of version control.

---

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [Supported Secrets Managers](#-supported-secrets-managers)
- [Priority System](#-priority-system)
- [Doppler Setup](#-doppler-recommended)
- [AWS Secrets Manager Setup](#-aws-secrets-manager)
- [HashiCorp Vault Setup](#-hashicorp-vault)
- [Docker Integration](#-docker-integration)
- [Testing](#-testing)
- [Troubleshooting](#-troubleshooting)
- [Best Practices](#-best-practices)

---

## 🚀 Quick Start

### ⭐ Automated Setup (Recommended)

**Use the interactive wizard to set up everything automatically:**

```bash
./scripts/create-secrets.sh
```

The wizard will:
- ✅ Guide you through choosing a secrets platform (Doppler/AWS/Vault/.env)
- ✅ Interactively collect all your credentials
- ✅ Set up secrets in your chosen platform
- ✅ Generate the appropriate `.env` configuration file
- ✅ Load existing values if re-running

📖 **[Complete Wizard Documentation](secrets-wizard.md)** - Full interactive setup guide

---

### Manual Setup

**Choose your secrets manager:**

| Solution | Best For | Setup Time | Cost |
|----------|----------|------------|------|
| **[Doppler](#-doppler-recommended)** | Personal projects, small teams | 10 min | Free |
| **[AWS Secrets Manager](#-aws-secrets-manager)** | AWS-heavy infrastructure | 30 min | ~$0.40/secret/month |
| **[HashiCorp Vault](#-hashicorp-vault)** | Enterprise, on-premises | 1-2 hours | Self-hosted |
| **Environment Variables** | Quick testing only | 2 min | Free |

**Recommended:** Start with Doppler - it's free, simple, and production-ready.

---

## 🔒 Supported Secrets Managers

### Doppler (Recommended) ⭐

**Why Doppler:**
- ✅ Completely free for personal projects
- ✅ Beautiful UI that's actually enjoyable
- ✅ Zero infrastructure to maintain
- ✅ Excellent CLI for development
- ✅ Built-in version history and audit logs
- ✅ Multi-environment support (dev/staging/prod)
- ✅ 10-minute setup

**When to use:** Default choice for most users, especially solo developers and small teams.

### AWS Secrets Manager

**Why AWS:**
- ✅ Deep AWS ecosystem integration
- ✅ IAM role-based access (no credentials needed on EC2/ECS)
- ✅ Automatic rotation capabilities
- ✅ Enterprise compliance features

**When to use:** Already heavily invested in AWS, running on EC2/ECS/Lambda.

### HashiCorp Vault

**Why Vault:**
- ✅ On-premises deployment
- ✅ Advanced policy-based access control
- ✅ Dynamic secrets generation
- ✅ Extensive audit logging

**When to use:** Enterprise environments, complex policy requirements, self-hosted infrastructure.

---

## 🎯 Priority System

Stream Daemon uses a **priority-based** system for loading secrets:

```
1. Secrets Manager (Doppler/AWS/Vault) ← HIGHEST PRIORITY
2. Environment Variables (.env file)    ← FALLBACK
3. None (error if not found)
```

### What This Means

**Secrets managers override environment variables:**
- If a secret exists in Doppler, the `.env` value is **ignored**
- Allows safe development: keep dev credentials in `.env`, production in secrets manager
- No accidental production credential commits to git

**What gets overridden:**
- API keys: `YOUTUBE_API_KEY`, `GEMINI_API_KEY`
- OAuth credentials: `TWITCH_CLIENT_ID`, `TWITCH_CLIENT_SECRET`
- Access tokens: `MASTODON_ACCESS_TOKEN`, `MATRIX_ACCESS_TOKEN`
- App passwords: `BLUESKY_APP_PASSWORD`
- Webhooks: `DISCORD_WEBHOOK_URL`

**What stays in .env (not secrets):**
- Platform enables: `TWITCH_ENABLE`, `MASTODON_ENABLE`
- Usernames: `TWITCH_USERNAME`, `YOUTUBE_USERNAME`
- Public URLs: `MASTODON_INSTANCE_URL`, `MATRIX_HOMESERVER`
- Intervals: `SETTINGS_CHECK_INTERVAL`, `SETTINGS_POST_INTERVAL`
- Secrets manager config: `SECRETS_MANAGER`, `DOPPLER_TOKEN`

### Example: Priority in Action

**.env file:**
```bash
TWITCH_ENABLE=True
TWITCH_USERNAME=chiefgyk3d
TWITCH_CLIENT_ID=dev_client_id_12345        # ← IGNORED if in Doppler
TWITCH_CLIENT_SECRET=dev_client_secret_67890  # ← IGNORED if in Doppler

SECRETS_MANAGER=doppler
DOPPLER_TOKEN=dp.st.dev.xxxxx
```

**Doppler secrets:**
```bash
TWITCH_CLIENT_ID=prod_client_id_abcxyz
TWITCH_CLIENT_SECRET=prod_client_secret_qwerty
```

**Result:**
- ✅ Uses Doppler's `prod_client_id_abcxyz` (overrides `.env`)
- ✅ Uses Doppler's `prod_client_secret_qwerty` (overrides `.env`)
- ✅ Uses `.env` for `TWITCH_USERNAME` (configuration, not secret)

**Pro Tip:** Comment out sensitive credentials in `.env` to avoid confusion:
```bash
# TWITCH_CLIENT_ID=dev_client_id_12345  ← Commented = clear it's not used
# TWITCH_CLIENT_SECRET=dev_client_secret  ← Commented = clear it's not used
```

---

## 🔷 Doppler (Recommended)

### Quick Setup

**Option 1: Use the Interactive Wizard** ⭐
```bash
./scripts/create-secrets.sh
# Select "Doppler" when prompted
```

The wizard will guide you through the entire setup process automatically.

**Option 2: Manual Setup** (if you prefer doing it yourself)

### Why Doppler is Recommended

**My personal take:** After trying AWS Secrets Manager, Vault, and various solutions, Doppler is the sweet spot for Stream Daemon:

- **Free forever** - No credit card, unlimited secrets for personal use
- **Dead simple** - Sign up → Add secrets → Get token → Done
- **No infrastructure** - Unlike Vault (servers) or AWS (account complexity)
- **Great UX** - Best-in-class web UI and CLI
- **Version history** - See every change, rollback anytime
- **Team-friendly** - Easy sharing without complex IAM policies

### Complete Setup (10 Minutes)

#### Step 1: Create Doppler Account (2 min)

1. Go to [doppler.com](https://doppler.com)
2. Sign up (GitHub, Google, or email - no credit card)
3. Create project: **"stream-daemon"**
4. You're automatically in the `dev` environment

**Environments:** Doppler organizes secrets by environment:
- **`dev`** - Development (default, perfect for most users)
- **`stg`** - Staging (optional)
- **`prd`** - Production (optional)

For solo streamers, **just use `dev`**. Create additional environments only if you need separate credentials for testing vs production.

#### Step 2: Add Secrets (5 min)

Click **"Add Secret"** for each platform you're using. Make sure you're in the **`dev` environment** (check dropdown).

**🎯 Naming Convention:** Use UPPERCASE with underscores. Secret names must start with the prefix you configure.

**Twitch:**
```bash
TWITCH_CLIENT_ID=your_client_id_here
TWITCH_CLIENT_SECRET=your_client_secret_here
```
Get from: [Twitch Developer Console](https://dev.twitch.tv/console/apps)

**YouTube:**
```bash
YOUTUBE_API_KEY=AIzaSyABC123XYZ789...
```
Get from: [Google Cloud Console](https://console.cloud.google.com/apis/credentials)

**Kick (optional):**
```bash
KICK_CLIENT_ID=your_kick_client_id
KICK_CLIENT_SECRET=your_kick_secret
```
Get from: Kick Settings → Developer (requires 2FA)

**Mastodon:**
```bash
MASTODON_CLIENT_ID=your_client_id
MASTODON_CLIENT_SECRET=your_client_secret
MASTODON_ACCESS_TOKEN=your_access_token
```
Get from: Instance Settings → Development → New Application

**Bluesky:**
```bash
BLUESKY_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
```
Get from: [Bluesky App Passwords](https://bsky.app/settings/app-passwords)

**Discord:**
```bash
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/123/abc...
# Optional: Platform-specific webhooks
DISCORD_WEBHOOK_TWITCH=https://discord.com/api/webhooks/456/def...
DISCORD_WEBHOOK_YOUTUBE=https://discord.com/api/webhooks/789/ghi...
```
Get from: Discord Server Settings → Integrations → Webhooks

**Matrix:**
```bash
MATRIX_HOMESERVER=https://matrix.org
MATRIX_ACCESS_TOKEN=syt_abc123...
MATRIX_ROOM_ID=!AbCdEfGhIjKl:matrix.org
# OR use username/password (takes priority over token)
MATRIX_USERNAME=@streambot:matrix.org
MATRIX_PASSWORD=your_matrix_password
```
Get from: Element → Settings → Help & About → Access Token

**AI Messages (optional):**
```bash
GEMINI_API_KEY=AIzaSyABC123XYZ789...
```
Get from: [Google AI Studio](https://aistudio.google.com)

#### Step 3: Get Doppler Token (1 min)

You need a token to authenticate Stream Daemon with Doppler.

**⚠️ Token is environment-specific:** A `dev` token only accesses `dev` secrets. A `prd` token only accesses `prd` secrets.

**Option A: Service Token (Recommended for Production)**

1. In Doppler dashboard → **Access** → **Service Tokens**
2. **Generate Service Token**
3. Name: `stream-daemon-dev` (or `stream-daemon-prd` for production)
4. **Environment:** Select **`dev`** (or whichever you're using)
5. **Copy the token** (starts with `dp.st.dev.` or `dp.st.prd.`)
6. Save it - you can't see it again!

**Option B: CLI + Personal Token (Best for Development)**

```bash
# Install Doppler CLI
# macOS:
brew install dopplerhq/cli/doppler

# Linux:
curl -Ls https://cli.doppler.com/install.sh | sh

# Windows (PowerShell):
iwr -useb https://cli.doppler.com/install.ps1 | iex

# Login
doppler login

# Setup in project directory
cd /path/to/stream-daemon
doppler setup
# Select: stream-daemon → dev

# Run without manually setting DOPPLER_TOKEN
doppler run -- python3 stream-daemon.py
```

#### Step 4: Configure Stream Daemon (2 min)

Edit your `.env` file:

```bash
# =====================================
# SECRETS MANAGER
# =====================================
SECRETS_MANAGER=doppler
DOPPLER_TOKEN=dp.st.dev.your_token_here_abc123xyz

# Secret name prefix (must match Doppler secret names)
# Example: SECRETS_DOPPLER_TWITCH_SECRET_NAME=TWITCH means
# secrets in Doppler must be: TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET
SECRETS_DOPPLER_TWITCH_SECRET_NAME=TWITCH
SECRETS_DOPPLER_YOUTUBE_SECRET_NAME=YOUTUBE
SECRETS_DOPPLER_KICK_SECRET_NAME=KICK
SECRETS_DOPPLER_MASTODON_SECRET_NAME=MASTODON
SECRETS_DOPPLER_BLUESKY_SECRET_NAME=BLUESKY
SECRETS_DOPPLER_DISCORD_SECRET_NAME=DISCORD
SECRETS_DOPPLER_MATRIX_SECRET_NAME=MATRIX
SECRETS_DOPPLER_GEMINI_SECRET_NAME=GEMINI

# =====================================
# PLATFORM CONFIGURATION (non-sensitive)
# =====================================
TWITCH_ENABLE=True
TWITCH_USERNAME=your_username

YOUTUBE_ENABLE=True
YOUTUBE_USERNAME=@YourHandle

MASTODON_ENABLE=True
MASTODON_INSTANCE_URL=https://mastodon.social

# =====================================
# COMMENT OUT CREDENTIALS! ❌
# =====================================
# These are now in Doppler, comment them out:
# TWITCH_CLIENT_ID=...
# TWITCH_CLIENT_SECRET=...
# YOUTUBE_API_KEY=...
# MASTODON_ACCESS_TOKEN=...
# BLUESKY_APP_PASSWORD=...
# DISCORD_WEBHOOK_URL=...
```

### How Doppler Fetching Works

When configured with `SECRETS_DOPPLER_TWITCH_SECRET_NAME=TWITCH`:

1. Stream Daemon connects to Doppler API
2. Fetches **all** secrets starting with `TWITCH_`
3. Strips the prefix: `TWITCH_CLIENT_ID` → `CLIENT_ID`
4. Returns credentials dict to platform

**Matching logic:**
- `TWITCH_CLIENT_ID` ✅ Matches (starts with `TWITCH_`)
- `TWITCH_CLIENT_SECRET` ✅ Matches
- `twitch_client_id` ❌ Case-sensitive (use UPPERCASE)
- `YOUTUBE_API_KEY` ❌ Different prefix

### Doppler Environments Explained

**What are environments?**
- Separate sets of secrets within one project
- Common setup: `dev` (development), `stg` (staging), `prd` (production)
- Each environment has its own token
- Tokens can't cross-access environments (security feature)

**Example workflow:**
```bash
# Development
DOPPLER_TOKEN=dp.st.dev.xxxx  # Accesses dev environment
# Uses dev Twitch app, dev Discord webhook, test credentials

# Production  
DOPPLER_TOKEN=dp.st.prd.yyyy  # Accesses prd environment
# Uses production Twitch app, real Discord webhook, live credentials
```

**When to use multiple environments:**
- ✅ Testing new integrations without breaking production
- ✅ Different webhooks for test vs production
- ✅ Team collaboration with separated access
- ❌ Solo streamer with one set of credentials (just use `dev`)

### Doppler with Docker

**docker-compose.yml:**
```yaml
version: '3.8'
services:
  stream-daemon:
    build: .
    environment:
      # Secrets Manager
      SECRETS_MANAGER: doppler
      DOPPLER_TOKEN: ${DOPPLER_TOKEN}  # From host .env
      
      # Secret prefixes
      SECRETS_DOPPLER_TWITCH_SECRET_NAME: TWITCH
      SECRETS_DOPPLER_YOUTUBE_SECRET_NAME: YOUTUBE
      
      # Platform config (non-sensitive)
      TWITCH_ENABLE: 'True'
      TWITCH_USERNAME: your_username
    volumes:
      - ./messages.txt:/app/messages.txt
```

**Host .env (for docker-compose):**
```bash
DOPPLER_TOKEN=dp.st.dev.your_token_here
```

**Run:**
```bash
docker-compose up -d
```

**Or use Doppler CLI:**
```bash
doppler run -- docker-compose up -d
```

---

## ☁️ AWS Secrets Manager

### Quick Setup

**Option 1: Use the Interactive Wizard** ⭐
```bash
./scripts/create-secrets.sh
# Select "AWS Secrets Manager" when prompted
```

The wizard will create all secrets in AWS Secrets Manager automatically.

**Option 2: Manual Setup** (if you prefer doing it yourself)

### When to Use AWS

- Already running on EC2, ECS, or Lambda
- Need IAM role-based access (no credentials in containers)
- Enterprise compliance requires AWS
- Want automatic credential rotation

### Setup

#### Step 1: Create Secrets in AWS

```bash
# Install AWS CLI
pip install awscli

# Configure credentials
aws configure

# Create secret for Twitch
aws secretsmanager create-secret \
  --name stream-daemon/twitch \
  --description "Twitch API credentials" \
  --secret-string '{
    "client_id": "your_client_id",
    "client_secret": "your_client_secret"
  }'

# Create secret for YouTube
aws secretsmanager create-secret \
  --name stream-daemon/youtube \
  --secret-string '{
    "api_key": "AIzaSyABC123XYZ789..."
  }'

# Create secret for Discord
aws secretsmanager create-secret \
  --name stream-daemon/discord \
  --secret-string '{
    "webhook_url": "https://discord.com/api/webhooks/123/abc..."
  }'
```

#### Step 2: Configure Stream Daemon

```bash
# .env
SECRETS_MANAGER=aws
AWS_REGION=us-east-1

# Secret names in AWS
SECRETS_AWS_TWITCH_SECRET_NAME=stream-daemon/twitch
SECRETS_AWS_YOUTUBE_SECRET_NAME=stream-daemon/youtube
SECRETS_AWS_DISCORD_SECRET_NAME=stream-daemon/discord

# AWS credentials (or use IAM role)
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

#### Step 3: IAM Permissions

Create policy allowing secret access:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:us-east-1:123456789012:secret:stream-daemon/*"
    }
  ]
}
```

Attach to:
- IAM user (if using access keys)
- EC2 instance role (if running on EC2)
- ECS task role (if running on ECS)

### AWS with Docker

**docker-compose.yml:**
```yaml
version: '3.8'
services:
  stream-daemon:
    build: .
    environment:
      SECRETS_MANAGER: aws
      AWS_REGION: us-east-1
      AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID}
      AWS_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY}
      SECRETS_AWS_TWITCH_SECRET_NAME: stream-daemon/twitch
```

**On EC2/ECS:** Skip `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` - use IAM roles instead!

---

## 🔐 HashiCorp Vault

### Quick Setup

**Option 1: Use the Interactive Wizard** ⭐
```bash
./scripts/create-secrets.sh
# Select "HashiCorp Vault" when prompted
```

The wizard will store all secrets in your Vault instance automatically.

**Option 2: Manual Setup** (if you prefer doing it yourself)

### When to Use Vault

- On-premises or self-hosted infrastructure
- Complex policy requirements
- Need dynamic secrets (auto-rotation)
- Enterprise audit logging requirements

### Setup

#### Step 1: Install and Configure Vault

```bash
# Start Vault server (development mode)
vault server -dev

# Set environment variables
export VAULT_ADDR='http://127.0.0.1:8200'
export VAULT_TOKEN='your_vault_token'

# Enable kv secrets engine
vault secrets enable -path=secret kv-v2
```

#### Step 2: Add Secrets

```bash
# Twitch credentials
vault kv put secret/stream-daemon/twitch \
  client_id="your_client_id" \
  client_secret="your_client_secret"

# YouTube credentials
vault kv put secret/stream-daemon/youtube \
  api_key="AIzaSyABC123XYZ789..."

# Discord webhook
vault kv put secret/stream-daemon/discord \
  webhook_url="https://discord.com/api/webhooks/123/abc..."
```

#### Step 3: Configure Stream Daemon

```bash
# .env
SECRETS_MANAGER=vault
SECRETS_VAULT_URL=http://127.0.0.1:8200
SECRETS_VAULT_TOKEN=your_vault_token

# Secret paths in Vault
SECRETS_VAULT_TWITCH_SECRET_PATH=secret/data/stream-daemon/twitch
SECRETS_VAULT_YOUTUBE_SECRET_PATH=secret/data/stream-daemon/youtube
SECRETS_VAULT_DISCORD_SECRET_PATH=secret/data/stream-daemon/discord
```

**Note:** Path includes `/data/` for KV v2 engine (`secret/data/path`).

---

## 🐳 Docker Integration

### Best Practices for Secrets in Docker

**❌ Don't:** Put secrets in Dockerfile or docker-compose.yml
**✅ Do:** Use environment variables or Docker secrets

### Doppler + Docker

```yaml
version: '3.8'
services:
  stream-daemon:
    image: stream-daemon:latest
    environment:
      SECRETS_MANAGER: doppler
      DOPPLER_TOKEN: ${DOPPLER_TOKEN}
      # All other secrets fetched from Doppler
```

### AWS + Docker (EC2/ECS)

```yaml
version: '3.8'
services:
  stream-daemon:
    image: stream-daemon:latest
    environment:
      SECRETS_MANAGER: aws
      AWS_REGION: us-east-1
      # No AWS credentials - uses IAM role
```

### Docker Secrets (Swarm)

```yaml
version: '3.8'
services:
  stream-daemon:
    image: stream-daemon:latest
    secrets:
      - doppler_token
    environment:
      SECRETS_MANAGER: doppler
      DOPPLER_TOKEN_FILE: /run/secrets/doppler_token

secrets:
  doppler_token:
    external: true
```

---

## 🧪 Testing

Stream Daemon includes tests to validate secrets management:

### Test All Platforms

```bash
python3 tests/test_doppler_all.py
```

### Test Individual Platforms

```bash
# Twitch
python3 tests/test_doppler_twitch.py

# YouTube
python3 tests/test_doppler_youtube.py

# Discord
python3 tests/test_discord.py
```

### What Tests Validate

- ✅ Secrets manager connection
- ✅ Secret fetching with correct prefixes
- ✅ Credential masking (security)
- ✅ Platform authentication
- ✅ Priority system (secrets override .env)

### Example Output

```
=== Testing Doppler Integration ===
✅ Doppler connection successful
✅ Fetched Twitch secrets (client_id: xxxx...yyyy)
✅ Twitch authentication successful
✅ All secrets properly masked in logs

🎉 All tests passed!
```

---

## 🔧 Troubleshooting

### "Secret not found" Error

**Problem:** Stream Daemon can't find secrets

**Solutions:**
1. Verify secret names match configured prefix:
   ```bash
   # Config says TWITCH, so secrets must be:
   SECRETS_DOPPLER_TWITCH_SECRET_NAME=TWITCH
   # Secrets in Doppler:
   TWITCH_CLIENT_ID  ✅
   TWITCH_CLIENT_SECRET  ✅
   ```

2. Check you're in the correct environment (Doppler)
3. Verify token hasn't expired or been revoked
4. Test connection:
   ```bash
   python3 -c "from doppler_sdk import DopplerSDK; \
     sdk = DopplerSDK(); \
     sdk.set_access_token('YOUR_TOKEN'); \
     print(sdk.secrets.list())"
   ```

### Still Using .env Credentials

**Problem:** Secrets manager not being called

**Solution:** Comment out ALL credentials in `.env`:
```bash
# ❌ This will be used instead of Doppler:
TWITCH_CLIENT_ID=abc123

# ✅ This allows Doppler to be used:
# TWITCH_CLIENT_ID=abc123
```

Verify with:
```bash
grep -E "^(TWITCH_CLIENT_ID|YOUTUBE_API_KEY)" .env
# Should return nothing (or only commented lines)
```

### Doppler Token Environment Mismatch

**Problem:** Token can't access expected secrets

**Cause:** Token is for `dev` environment but trying to access `prd` secrets

**Solution:**
1. Check token prefix: `dp.st.dev.xxx` = dev environment
2. In Doppler dashboard, verify which environment you're viewing
3. Generate new token for correct environment if needed

### AWS Permissions Error

**Problem:** "Access Denied" from AWS

**Solutions:**
1. Verify IAM permissions include `secretsmanager:GetSecretValue`
2. Check secret ARN in policy matches actual secret
3. If using EC2/ECS, verify instance/task role is attached
4. Test credentials:
   ```bash
   aws secretsmanager get-secret-value \
     --secret-id stream-daemon/twitch
   ```

### Vault Connection Timeout

**Problem:** Can't connect to Vault

**Solutions:**
1. Verify Vault server is running: `vault status`
2. Check `SECRETS_VAULT_URL` is correct
3. Verify network connectivity: `curl $SECRETS_VAULT_URL/v1/sys/health`
4. Check Vault token is valid: `vault token lookup`

---

## 💡 Best Practices

### Development

✅ **Use `doppler run` for local development**
```bash
doppler run -- python3 stream-daemon.py
```

✅ **Keep `.env` in `.gitignore`**
```gitignore
.env
.env.local
.env.*.local
```

✅ **Use `dev` environment in Doppler**
- Separate testing credentials from production
- Safe to experiment without breaking production

✅ **Share Doppler project access with team**
- Easier than passing credentials manually
- Built-in audit logging

### Production

✅ **Use separate environments** (`prd`, `staging`)
```bash
# Production deployment
DOPPLER_TOKEN=dp.st.prd.xxx  # Production token
```

✅ **Use service tokens, not personal tokens**
- Service tokens are scoped to one environment
- Easier to rotate without affecting team

✅ **Rotate tokens periodically**
- Doppler: Generate new service token, update deployment, revoke old
- AWS: Use automatic rotation features
- Vault: Use dynamic secrets with TTL

✅ **Use IAM roles on cloud platforms**
```yaml
# ECS task definition
taskRoleArn: arn:aws:iam::123456789012:role/stream-daemon-task-role
# No AWS credentials needed in environment!
```

✅ **Enable audit logging**
- Doppler: Automatic audit logs
- AWS: Enable CloudTrail
- Vault: Enable audit device

### Security

✅ **Never commit tokens to git**
```bash
# Bad
DOPPLER_TOKEN=dp.st.dev.abc123xyz  # In .env, committed to git

# Good
DOPPLER_TOKEN=dp.st.dev.abc123xyz  # In .env.local, in .gitignore
```

✅ **Use read-only permissions where possible**
- Doppler service tokens are read-only by default ✅
- AWS IAM: Only grant `GetSecretValue`, not `PutSecretValue`
- Vault: Use restrictive policies

✅ **Revoke old tokens when rotating**
- Doppler: Revoke old service token after deploying new one
- AWS: Delete old IAM access keys
- Vault: Revoke old token after issuing new one

✅ **Use different projects/paths for different environments**
```bash
# Doppler: Separate environments
dev environment: dp.st.dev.xxx
prd environment: dp.st.prd.yyy

# AWS: Separate paths
stream-daemon-dev/twitch
stream-daemon-prd/twitch

# Vault: Separate paths
secret/dev/stream-daemon/twitch
secret/prd/stream-daemon/twitch
```

✅ **Enable 2FA on secrets manager accounts**
- Doppler: Enable 2FA in account settings
- AWS: Enable MFA for root and IAM users
- Vault: Use AppRole or OIDC authentication

---

## 📚 See Also

- **[Doppler Documentation](https://docs.doppler.com/)** - Official Doppler docs
- **[AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/)** - AWS documentation
- **[HashiCorp Vault](https://www.vaultproject.io/docs)** - Vault documentation
- **[Platform Setup Guides](../platforms/)** - How to get API credentials
- **[Docker Deployment](../../Docker/README.md)** - Docker and docker-compose examples

---

## 💬 Questions?

Having issues with secrets management? 

- 📖 Check [Troubleshooting](#-troubleshooting) above
- 🐛 [Open an issue](https://github.com/ChiefGyk3D/Stream-Daemon/issues)
- 💬 [Ask in discussions](https://github.com/ChiefGyk3D/Stream-Daemon/discussions)
