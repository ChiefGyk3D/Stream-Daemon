# Doppler Secrets Management Guide

> **TL;DR:** Doppler is the easiest way to keep your API keys secure. It's free, takes 10 minutes to setup, and you never have to worry about accidentally committing secrets to GitHub.

---

## 🎯 Why Doppler? (And Why I Prefer It)

**Doppler is the recommended secrets manager for Stream Daemon.** Here's why:

### The Best Reasons

✅ **Completely Free** - No credit card required, unlimited secrets for personal projects  
✅ **Dead Simple** - Sign up → Add secrets → Get token → Done in 10 minutes  
✅ **Zero Infrastructure** - No servers to maintain (unlike Vault) or AWS accounts needed  
✅ **Beautiful UI** - Actually enjoyable to use, unlike AWS Console  
✅ **Great CLI** - Works perfectly for local development  
✅ **Version History** - See every secret change with full audit trail  
✅ **Multi-Environment** - Easy dev/staging/prod separation  

### Compared to Alternatives

| Feature | Doppler | AWS Secrets | Vault | .env Files |
|---------|---------|-------------|-------|------------|
| **Free Tier** | ✅ Unlimited | ❌ Paid only | ✅ Self-host | ✅ Free |
| **Setup Time** | 10 mins | 30+ mins | Hours | 2 mins |
| **Infrastructure** | ☁️ Managed | ☁️ AWS required | 🏠 Self-host | 💻 Local only |
| **Team Sharing** | ✅ Easy | ⚠️ IAM complex | ⚠️ Policy complex | ❌ Insecure |
| **Git Safety** | ✅ Never committed | ✅ Never committed | ✅ Never committed | ⚠️ Easy to commit |
| **Local Dev** | ✅ Excellent | ⚠️ AWS CLI needed | ⚠️ Network required | ✅ Simple |

**My Opinion:** If you're a solo dev or small team, Doppler is perfect. AWS/Vault are overkill unless you're already using them enterprise-wide.

---

## 🚨 Critical Concept: Why You MUST Comment Out Credentials

**This is mistake #1 that breaks secrets managers!**

### The Problem

Stream Daemon follows this priority order for credentials:

1. **Environment variables** (from `.env` file) ← **HIGHEST PRIORITY**
2. Secrets manager (Doppler/AWS/Vault)
3. Error if not found

If you have this in your `.env`:
```bash
TWITCH_CLIENT_ID=abc123xyz789
TWITCH_CLIENT_SECRET=supersecret
```

Stream Daemon will **use those values directly** and **never call Doppler**. This defeats the entire purpose of using a secrets manager!

### The Solution

**Comment out ALL sensitive credentials in your `.env` file:**

```bash
# ✅ KEEP THESE (non-sensitive configuration)
TWITCH_ENABLE=True
TWITCH_USERNAME=chiefgyk3d
YOUTUBE_USERNAME=@ChiefGyk3D

# ❌ COMMENT THESE OUT (sensitive credentials)
# TWITCH_CLIENT_ID=abc123
# TWITCH_CLIENT_SECRET=xyz789
# YOUTUBE_API_KEY=AIzaSy...
# MASTODON_ACCESS_TOKEN=xxx
# BLUESKY_APP_PASSWORD=xxx
# DISCORD_WEBHOOK_URL=https://...
```

Now when Stream Daemon looks for `TWITCH_CLIENT_ID`:
1. Checks environment variables → Not found (commented out)
2. Calls Doppler to fetch it → Success! ✅

### What To Keep vs Comment Out

**✅ Keep in .env (non-sensitive):**
- Platform enable flags (`TWITCH_ENABLE`, `MASTODON_ENABLE_POSTING`)
- Usernames (`TWITCH_USERNAME`, `YOUTUBE_USERNAME`)
- Public URLs (`MASTODON_API_BASE_URL`)
- App names (`MASTODON_APP_NAME`)
- Intervals and settings
- Doppler configuration itself (`SECRETS_SECRET_MANAGER=doppler`, `DOPPLER_TOKEN`)

**❌ Comment out (sensitive):**
- API Keys (`YOUTUBE_API_KEY`)
- Client IDs and Secrets (`TWITCH_CLIENT_ID`, `TWITCH_CLIENT_SECRET`)
- Access Tokens (`MASTODON_ACCESS_TOKEN`)
- Passwords (`BLUESKY_APP_PASSWORD`)
- Webhook URLs (`DISCORD_WEBHOOK_URL`)

---

## 🚀 Complete Setup Guide (10 Minutes)

### Step 1: Create Doppler Account (2 minutes)

1. Go to [https://doppler.com](https://doppler.com) and sign up
2. Use GitHub, Google, or email (no credit card required)
3. Click **"Create Project"** → Name it **"stream-daemon"**
4. You'll be in the `dev` environment automatically

**📌 Important: Doppler Environments**

Doppler organizes secrets into **environments** within each project:
- **`dev`** - Development (default, created automatically)
- **`stg`** - Staging (optional, create if needed)
- **`prd`** - Production (optional, create if needed)

Each environment has its own set of secrets. For most users, the **`dev` environment is sufficient**. If you want to separate testing credentials from production credentials, you can create additional environments and generate separate tokens for each.

**For this guide, we'll use the `dev` environment.**

### Step 2: Add Secrets to Doppler (5 minutes)

Click **"Add Secret"** for each credential below. Make sure you're in the **`dev` environment** (check the dropdown at the top of the Doppler dashboard).
 

**Note:** Secret names can be uppercase (`TWITCH_CLIENT_ID`) or lowercase (`twitch_client_id`) - Stream Daemon matches case-insensitively. **UPPERCASE is recommended** as it's more visible and follows standard environment variable naming.

#### 🟣 Twitch (Required if TWITCH_ENABLE=True)

```
Secret Name: TWITCH_CLIENT_ID  (or twitch_client_id)
Value: abc123xyz789

Secret Name: TWITCH_CLIENT_SECRET  (or twitch_client_secret)
Value: your_secret_here
```

**Where to get:** [Twitch Developer Console](https://dev.twitch.tv/console/apps)
- Create an Application
- Copy Client ID and Generate/Copy Client Secret
- Set OAuth Redirect URL to `http://localhost` (required but not used)

#### 📺 YouTube (Required if YOUTUBE_ENABLE=True)

```
Secret Name: YOUTUBE_API_KEY
Value: AIzaSyABC123XYZ789...
```

**Where to get:** [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
- Create Project → Enable YouTube Data API v3
- Create Credentials → API Key
- Restrict key to YouTube Data API v3 (recommended)

#### ⚡ Kick (Optional but recommended)

```
Secret Name: KICK_CLIENT_ID
Value: your_kick_client_id

Secret Name: KICK_CLIENT_SECRET
Value: your_kick_secret
```

**Where to get:** Kick Developer Portal
1. Login to kick.com (ensure 2FA is enabled)
2. Go to Settings → Developer
3. Create a new application
4. **Scopes:** Select "Read Access" (required for stream status checks)
5. Copy Client ID and Client Secret
- If unavailable, Stream Daemon uses public API (works but limited)

#### 🐘 Mastodon (Required if MASTODON_ENABLE_POSTING=True)

```
Secret Name: MASTODON_CLIENT_ID
Value: your_mastodon_client_id

Secret Name: MASTODON_CLIENT_SECRET
Value: your_mastodon_client_secret

Secret Name: MASTODON_ACCESS_TOKEN
Value: your_access_token
```

**Where to get:** Your Mastodon Instance
1. Go to Settings → Development
2. Click "New Application"
3. **Scopes:** Check `read:accounts` (required) and `write:statuses` (required), optionally `write:media` (for images/videos)
4. Copy the three credentials shown on the Mastodon page:
   - "Client key" → Add to Doppler as `MASTODON_CLIENT_ID`
   - "Client secret" → Add to Doppler as `MASTODON_CLIENT_SECRET`
   - "Your access token" → Add to Doppler as `MASTODON_ACCESS_TOKEN`

#### 🦋 Bluesky (Required if BLUESKY_ENABLE_POSTING=True)

```
Secret Name: BLUESKY_APP_PASSWORD
Value: your-app-password-here
```

**Where to get:** [Bluesky Settings](https://bsky.app/settings/app-passwords)
- Click "Add App Password"
- Name it "Stream Daemon"
- Copy the password (NOT your main account password!)

#### 💬 Discord (Required if DISCORD_ENABLE_POSTING=True)

```
Secret Name: DISCORD_WEBHOOK_URL
Value: https://discord.com/api/webhooks/123456789/abcdefg...
```

**Where to get:** Discord Server
1. Go to Server Settings → Integrations → Webhooks
2. Create Webhook
3. Copy the Webhook URL

**Important Notes:**
- Secret names can be uppercase or lowercase (case-insensitive matching)
- **UPPERCASE recommended** for visibility and standard naming
- Use **underscores** not hyphens (`TWITCH_CLIENT_ID` not `TWITCH-CLIENT-ID`)
- The prefix before `_` must match your config (default: `twitch`, `youtube`, etc.)

### Step 3: Get Your Doppler Token (1 minute)

You need a token to authenticate Stream Daemon with Doppler. The token is **environment-specific** - it only has access to secrets in the environment you select.

**🔑 Important: Choose Your Environment**

When generating a token, you must select which Doppler environment it accesses:
- **`dev`** - For development/testing (recommended for most users)
- **`prd`** - For production deployments
- **`stg`** - For staging environments

**For this guide, use the `dev` environment.**

#### Option A: Service Token (Recommended for Production)

1. In Doppler dashboard, select your project ("stream-daemon")
2. Click **Access** → **Service Tokens**
3. Click **Generate Service Token**
4. Name: "stream-daemon-dev" (or "stream-daemon-production" for prod)
5. **Environment:** Select **"dev"** (or whichever environment you're using)
6. **Copy the token** - it starts with `dp.st.`
7. Store it safely - you can't see it again!

**⚠️ The token is locked to the environment you select.** If you need access to multiple environments, generate separate tokens for each.

#### Option B: CLI + Personal Token (Best for Development)

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
# Select: stream-daemon → dev (this sets your environment)

# Now you can run without setting DOPPLER_TOKEN
doppler run -- python3 stream-daemon.py
```

### Step 4: Configure Stream Daemon (2 minutes)

Edit your `.env` file:

```bash
# =====================================
# SECRETS MANAGER CONFIGURATION
# =====================================
SECRETS_SECRET_MANAGER=doppler
DOPPLER_TOKEN=dp.st.your_service_token_here_abc123xyz

# Configure secret name prefixes (lowercase!)
SECRETS_DOPPLER_TWITCH_SECRET_NAME=twitch
SECRETS_DOPPLER_YOUTUBE_SECRET_NAME=youtube
SECRETS_DOPPLER_KICK_SECRET_NAME=kick
SECRETS_DOPPLER_MASTODON_SECRET_NAME=mastodon
SECRETS_DOPPLER_BLUESKY_SECRET_NAME=bluesky
SECRETS_DOPPLER_DISCORD_SECRET_NAME=discord

# =====================================
# PLATFORM CONFIGURATION (non-sensitive)
# =====================================
TWITCH_ENABLE=True
TWITCH_USERNAME=your_username

YOUTUBE_ENABLE=True
YOUTUBE_USERNAME=@YourHandle

MASTODON_ENABLE_POSTING=True
MASTODON_API_BASE_URL=https://mastodon.social

# =====================================
# COMMENT OUT ALL CREDENTIALS! ❌
# =====================================
# TWITCH_CLIENT_ID=...
# TWITCH_CLIENT_SECRET=...
# YOUTUBE_API_KEY=...
# MASTODON_CLIENT_ID=...
# MASTODON_CLIENT_SECRET=...
# MASTODON_ACCESS_TOKEN=...
# BLUESKY_APP_PASSWORD=...
# DISCORD_WEBHOOK_URL=...
```

### Step 5: Test Everything (1 minute)

Run the test suite to verify Doppler is working:

```bash
# Test all platforms
python3 tests/test_doppler_all.py

# Test individual platforms
python3 tests/test_doppler_twitch.py
python3 tests/test_doppler_youtube.py
python3 tests/test_doppler_kick.py
```

You should see:
```
✅ Doppler connection successful
✅ Fetched Twitch secrets (client_id: xxxx...yyyy)
✅ Twitch authentication successful
✅ Stream detection working
```

---

## 🔧 How It Works (Technical Details)

### Secret Fetching Logic

When you configure `SECRETS_DOPPLER_TWITCH_SECRET_NAME=twitch`, here's what happens:

1. Stream Daemon calls Doppler API with your token
2. Fetches **all** secrets from your project/environment
3. Filters for secrets starting with `twitch_` (lowercase)
4. Strips the prefix: `twitch_client_id` → `client_id`
5. Returns a dict: `{'client_id': 'xxx', 'client_secret': 'yyy'}`
6. Uses these credentials for the Twitch platform

### Prefix Matching

The prefix name in `.env` must match the prefix in Doppler secret names:

```bash
# .env configuration
SECRETS_DOPPLER_TWITCH_SECRET_NAME=twitch

# Doppler secrets (must start with 'twitch_')
twitch_client_id       ✅ Matches
twitch_client_secret   ✅ Matches
TWITCH_CLIENT_ID       ❌ Uppercase doesn't match
twitch-client-id       ❌ Hyphens don't match
youtube_api_key        ❌ Different prefix
```

### Why Lowercase?

Stream Daemon's Doppler integration uses lowercase matching for consistency with Python naming conventions. All Doppler secret names should be lowercase with underscores.

---

## 🐳 Using Doppler with Docker

### Method 1: Pass Token via Environment (Recommended)

**docker-compose.yml:**
```yaml
version: '3.8'
services:
  stream-daemon:
    build: .
    restart: unless-stopped
    environment:
      # Secrets Manager Config
      SECRETS_SECRET_MANAGER: doppler
      DOPPLER_TOKEN: ${DOPPLER_TOKEN}
      SECRETS_DOPPLER_TWITCH_SECRET_NAME: twitch
      SECRETS_DOPPLER_YOUTUBE_SECRET_NAME: youtube
      SECRETS_DOPPLER_MASTODON_SECRET_NAME: mastodon
      
      # Platform Config (non-sensitive)
      TWITCH_ENABLE: 'True'
      TWITCH_USERNAME: your_username
      YOUTUBE_ENABLE: 'True'
      YOUTUBE_USERNAME: '@YourHandle'
      MASTODON_ENABLE_POSTING: 'True'
      MASTODON_API_BASE_URL: 'https://mastodon.social'
    volumes:
      - ./messages.txt:/app/messages.txt
      - ./end_messages.txt:/app/end_messages.txt
```

**.env file** (for docker-compose):
```bash
DOPPLER_TOKEN=dp.st.your_token_here
```

**Run:**
```bash
docker-compose up -d
```

### Method 2: Doppler CLI Integration

```bash
# Doppler automatically injects secrets
doppler run -- docker-compose up -d

# Or for development
doppler run -- docker-compose up
```

---

## 🧪 Testing Your Setup

Stream Daemon includes comprehensive tests for Doppler:

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

# Kick
python3 tests/test_doppler_kick.py
```

### What Tests Validate
- ✅ Doppler connection and authentication
- ✅ Secret fetching with correct prefixes
- ✅ Credential masking (security)
- ✅ API authentication for each platform
- ✅ Stream detection functionality

### Example Test Output
```
=== Testing Doppler Integration ===
Test 1: Fetching Twitch secrets from Doppler
✅ Success! Got credentials:
   client_id: xxxx...yyyy (masked)
   client_secret: xxxx...zzzz (masked)

Test 2: Authenticating with Twitch API
✅ Success! Access token: xxxx...wwww (masked)

Test 3: Checking stream status
✅ Success! Stream detected: is_live=True
   Title: "Testing Stream Daemon | Coding & Cybersecurity"
   Viewers: 3
```

---

## 🔍 Troubleshooting

### "Secret not found" Error

**Problem:** Stream Daemon can't find secrets in Doppler

**Solutions:**
1. Verify secret names are **lowercase with underscores**
2. Check prefix matches: `SECRETS_DOPPLER_TWITCH_SECRET_NAME=twitch` → secrets must start with `twitch_`
3. Confirm you're in the right Doppler project/environment
4. Verify `DOPPLER_TOKEN` is set correctly
5. Check token hasn't expired (service tokens don't expire)

### Still Using .env Credentials

**Problem:** Stream Daemon isn't calling Doppler

**Solution:** Make sure ALL credentials are commented out in `.env`:
```bash
# TWITCH_CLIENT_ID=abc123  ← Must be commented!
# TWITCH_CLIENT_SECRET=xyz ← Must be commented!
```

Run this to check:
```bash
grep -E "^(TWITCH_CLIENT_ID|YOUTUBE_API_KEY|MASTODON_ACCESS_TOKEN)" .env
```
Should return nothing (or commented lines only).

### Authentication Fails with Doppler Secrets

**Problem:** Credentials from Doppler don't work

**Solutions:**
1. Test credentials manually to verify they're correct
2. Check secret values in Doppler (View Secret)
3. Regenerate API keys if they've expired
4. Verify no extra spaces/newlines in Doppler secret values

### Permission Denied

**Problem:** "Doppler API returned 403 Forbidden"

**Solutions:**
1. Verify token is for the correct project
2. Check token hasn't been revoked
3. Service token must have Read access (should be default)
4. Try regenerating the service token

### Docker Container Can't Reach Doppler

**Problem:** "Connection timeout" or "Network unreachable"

**Solutions:**
1. Verify Docker has internet access: `docker run alpine ping -c 3 doppler.com`
2. Check firewall rules aren't blocking `api.doppler.com`
3. If behind corporate proxy, configure Docker proxy settings
4. Try `docker-compose down && docker-compose up` to recreate network

---

## 💡 Best Practices

### Development
- ✅ Use `doppler run` CLI for local development
- ✅ Use `dev` environment in Doppler
- ✅ Keep `.env` in `.gitignore`
- ✅ Share Doppler project access with team members

### Production
- ✅ Use separate Doppler environments (`prd`, `staging`)
- ✅ Use service tokens, not personal tokens
- ✅ Rotate service tokens periodically
- ✅ Use Docker secrets or Kubernetes secrets for token itself
- ✅ Enable Doppler audit logs
- ✅ Set up Doppler webhooks for secret change notifications

### Security
- ✅ Never commit `.env` with `DOPPLER_TOKEN`
- ✅ Use read-only service tokens when possible
- ✅ Revoke old tokens when regenerating
- ✅ Use different Doppler projects for different environments
- ✅ Enable 2FA on your Doppler account

---

## 📚 Additional Resources

- [Doppler Documentation](https://docs.doppler.com/)
- [Doppler CLI Reference](https://docs.doppler.com/docs/cli)
- [Stream Daemon Test Suite](tests/README.md)
- [Doppler Secret Naming Guide](tests/DOPPLER_SECRETS.md)
- [Platform Setup Guide](PLATFORM_GUIDE.md)

---

## 🆚 Comparison with Other Secrets Managers

### AWS Secrets Manager

**When to use AWS:**
- Already heavily invested in AWS ecosystem
- Need AWS IAM integration
- Enterprise compliance requires AWS

**Why I prefer Doppler:**
- Free tier (AWS charges $0.40/secret/month)
- Simpler setup (no IAM policies)
- Better local development experience
- No AWS account needed

### HashiCorp Vault

**When to use Vault:**
- Already running Vault infrastructure
- Need on-premises secrets management
- Enterprise with complex policy requirements

**Why I prefer Doppler:**
- No infrastructure to maintain
- No complex policy setup
- Better UI/UX
- Faster setup (minutes vs hours)

### Environment Files (.env)

**When to use .env:**
- Personal project, never sharing
- Single developer
- Okay with manual secret management

**Why I prefer Doppler:**
- Never risk committing secrets
- Easy team collaboration
- Version history
- Multi-environment support

---

## ❓ FAQ

**Q: Is Doppler really free?**  
A: Yes! Free tier includes unlimited secrets for up to 5 users. Perfect for personal projects and small teams.

**Q: Can I switch from .env to Doppler without downtime?**  
A: Yes! Keep your `.env` credentials until Doppler is working, then comment them out. No downtime needed.

**Q: Can I use Doppler AND .env together?**  
A: Kind of - you can have non-sensitive config in `.env` and secrets in Doppler. But if a secret is in both places, `.env` takes priority (which defeats the purpose).

**Q: What if Doppler goes down?**  
A: Stream Daemon caches secrets for the current run. If Doppler is down at restart, you can temporarily uncomment credentials in `.env` as a backup.

**Q: Can I self-host Doppler?**  
A: No, Doppler is cloud-only. If you need self-hosting, use HashiCorp Vault instead.

**Q: How do I migrate from AWS Secrets Manager to Doppler?**  
A: 
1. Copy all secrets from AWS to Doppler (same names, lowercase with underscores)
2. Change `SECRETS_SECRET_MANAGER=aws` to `SECRETS_SECRET_MANAGER=doppler`
3. Add `DOPPLER_TOKEN` and secret name configs
4. Test with test suite
5. Once confirmed working, delete AWS secrets

**Q: Is my DOPPLER_TOKEN a secret?**  
A: Yes! Never commit it to git. Use environment variables or Docker secrets for the token itself.

---

**Questions? Open an issue on GitHub or check the [test suite documentation](tests/README.md) for more examples.**
