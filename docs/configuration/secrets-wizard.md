# Secrets Setup Wizard

The `create-secrets.sh` script is an interactive wizard that helps you create and configure secrets for Stream Daemon across different secrets management platforms.

> **📖 New to secrets management?** See [Config vs Secrets Behavior Guide](secrets-wizard-behavior.md) to understand what gets stored where.

## Quick Start

```bash
# Run the wizard
./scripts/create-secrets.sh
```

The wizard will guide you through:
1. Selecting a secrets manager (Doppler, AWS, Vault, or .env file)
2. Configuring streaming platforms (Twitch, YouTube, Kick)
3. Configuring social platforms (Mastodon, Bluesky, Discord, Matrix)
4. Setting up AI/LLM (Google Gemini)
5. Configuring Stream Daemon settings
6. Creating secrets in your chosen platform

---

## Features

### 🎯 Interactive Configuration
- **Smart Defaults**: Loads existing values from `.env` if available
- **Platform-Specific Guidance**: Links to credential pages for each service
- **Optional Features**: Only configure what you need
- **Validation**: Checks for required tools and credentials

### 🔐 Multi-Platform Support

### 🔐 Multi-Platform Support

**Doppler (Recommended)**
- Automatic CLI installation guidance
- Project and config creation
- Bulk secret upload
- Token generation instructions
- **Separates secrets from config**: Secrets in Doppler, config in .env

**AWS Secrets Manager**
- JSON-structured secrets
- Regional deployment support
- Automatic create/update
- IAM integration ready
- **Separates secrets from config**: Secrets in AWS, config in .env

**HashiCorp Vault**
- KV v2 secrets engine support
- Custom path configuration
- Token authentication
- Self-hosted friendly
- **Separates secrets from config**: Secrets in Vault, config in .env

**.env File**
- Development-friendly
- Well-commented output
- Automatic permission setting (`chmod 600`)
- Git-safe (auto-ignored)
- **Everything in one file**: Both config and secrets

> **🔑 Key Concept:** When you choose Doppler/AWS/Vault, the wizard:
> 1. Stores **secrets** (API keys, tokens, webhooks) in the secrets manager
> 2. Stores **config** (usernames, URLs, settings) in `.env` file
> 3. Creates `.env` with connection info to fetch secrets at runtime
>
> When you choose .env file, everything (config + secrets) goes into `.env`.
>
> See [Config vs Secrets Behavior](secrets-wizard-behavior.md) for detailed examples.

### 🎨 User-Friendly Interface
- Color-coded output
- Progress indicators
- Clear section headers
- Helpful error messages
- Next steps guidance

---

## Usage Guide

### Initial Setup

```bash
# First time setup
./scripts/create-secrets.sh
```

**Follow the prompts:**
1. Select secrets manager
2. Answer yes/no for each platform
3. Enter credentials when prompted
4. Review summary and next steps

### Updating Existing Secrets

```bash
# Update with existing .env as defaults
./scripts/create-secrets.sh
```

The wizard will:
- Load current values from `.env`
- Show them as defaults `[yellow_text]`
- Allow you to press Enter to keep existing values
- Only update what you change

### Switching Secrets Managers

```bash
# Example: Moving from .env to Doppler
./scripts/create-secrets.sh
```

1. Select new secrets manager (e.g., Doppler)
2. Wizard loads values from existing `.env`
3. Confirm or update each value
4. Secrets created in new platform
5. `.env` kept as backup

---

## Platform Configuration

### Streaming Platforms

<details>
<summary><b>Twitch</b></summary>

**Required:**
- Username
- Client ID
- Client Secret

**How to get credentials:**
1. Go to https://dev.twitch.tv/console
2. Register your application
3. Copy Client ID and generate Client Secret

**Wizard prompts:**
```
Configure Twitch? [Y/n]: Y
Twitch Username: your_username
Twitch Client ID: abc123def456
Twitch Client Secret: ************
```
</details>

<details>
<summary><b>YouTube</b></summary>

**Required:**
- API Key
- Channel ID OR @Username

**How to get credentials:**
1. Go to https://console.cloud.google.com/apis/credentials
2. Create API key
3. Enable YouTube Data API v3

**Wizard prompts:**
```
Configure YouTube? [Y/n]: Y
YouTube Channel ID (or leave empty): UC_abc123
YouTube @Username: @YourChannel
YouTube API Key: ************
```
</details>

<details>
<summary><b>Kick</b></summary>

**Required:**
- Username

**Optional (better rate limits):**
- Client ID
- Client Secret (requires 2FA)

**Wizard prompts:**
```
Configure Kick? [y/N]: y
Kick Username: your_username
Use Kick OAuth? (better rate limits) [y/N]: y
Kick Client ID: abc123
Kick Client Secret: ************
```
</details>

### Social Platforms

<details>
<summary><b>Mastodon</b></summary>

**Required:**
- Instance URL
- Client ID
- Client Secret
- Access Token

**How to get credentials:**
1. Go to your instance settings
2. Navigate to Development → Your applications
3. Create new application
4. Copy credentials

**Wizard prompts:**
```
Configure Mastodon? [Y/n]: Y
Mastodon Instance URL [https://mastodon.social]: https://your.instance
Mastodon Client ID: abc123
Mastodon Client Secret: ************
Mastodon Access Token: ************
```
</details>

<details>
<summary><b>Bluesky</b></summary>

**Required:**
- Handle
- App Password

**How to get credentials:**
1. Go to https://bsky.app/settings/app-passwords
2. Create new app password
3. Name it "Stream Daemon"

**Wizard prompts:**
```
Configure Bluesky? [Y/n]: Y
Bluesky Handle: yourname.bsky.social
Bluesky App Password: ************
```
</details>

<details>
<summary><b>Discord</b></summary>

**Required:**
- Webhook URL

**Optional:**
- Platform-specific webhooks
- Role mentions
- Live embed updates

**How to get credentials:**
1. Server Settings → Integrations → Webhooks
2. Create webhook
3. Copy webhook URL

**Wizard prompts:**
```
Configure Discord? [Y/n]: Y
Discord Webhook URL: https://discord.com/api/webhooks/...
Use different webhooks for each streaming platform? [y/N]: n
Configure role mentions? [y/N]: y
Twitch Role Mention (e.g., @Twitch Viewers): @TwitchLive
Enable live embed updates? [Y/n]: Y
Update interval (seconds) [60]: 60
```
</details>

<details>
<summary><b>Matrix</b></summary>

**Required:**
- Homeserver URL
- Room ID
- Access Token OR Username/Password

**How to get credentials:**
1. Create bot account
2. Get access token from Element: Settings → Help & About → Advanced → Access Token
3. Invite bot to room and note room ID

**Wizard prompts:**
```
Configure Matrix? [y/N]: y
Matrix Homeserver [https://matrix.org]: https://matrix.org
Matrix Room ID: !abc123:matrix.org
Use access token? (recommended) [Y/n]: Y
Matrix Access Token: ************
```
</details>

### AI/LLM Configuration

<details>
<summary><b>Google Gemini</b></summary>

**Required:**
- API Key

**Optional:**
- Custom model

**How to get credentials:**
1. Go to https://aistudio.google.com/app/apikey
2. Create API key

**Wizard prompts:**
```
Enable AI-powered messages with Google Gemini? [Y/n]: Y
Gemini API Key: ************
Gemini Model [gemini-2.0-flash-exp]: gemini-2.0-flash-exp
```
</details>

---

## Secrets Manager Setup

### Doppler

**Prerequisites:**
- Doppler account (free tier available)
- Internet connection

**Setup Flow:**
1. Wizard checks for Doppler CLI
2. If not found, provides installation command
3. Prompts for login
4. Creates/selects project and config
5. Uploads all secrets in bulk

**Output Example:**
```
✓ Doppler CLI installed
✓ Logged in to Doppler
✓ Project 'stream-daemon' exists
✓ Config 'dev' exists
Uploading secrets to Doppler...
✓ Secrets uploaded to Doppler!

To use these secrets, set:
  export DOPPLER_TOKEN=$(doppler configs tokens create cli --project stream-daemon --config dev --plain)

Or run Stream Daemon with:
  doppler run --project stream-daemon --config dev -- python stream-daemon.py
```

**Environments:**
- `dev` - Development
- `stg` - Staging
- `prd` - Production

### AWS Secrets Manager

**Prerequisites:**
- AWS account
- AWS CLI installed and configured
- IAM permissions for Secrets Manager

**Setup Flow:**
1. Checks for AWS CLI
2. Validates AWS credentials
3. Prompts for region
4. Creates JSON secrets for each platform
5. Uses create/update pattern (idempotent)

**Output Example:**
```
✓ AWS CLI installed
✓ AWS credentials configured
AWS Region [us-east-1]: us-east-1
Creating secrets in AWS Secrets Manager...
✓ Twitch secrets created/updated
✓ YouTube secrets created/updated
✓ Mastodon secrets created/updated
✓ Secrets created in AWS Secrets Manager!

Set these environment variables to use AWS Secrets:
  export SECRETS_MANAGER=aws
  export AWS_REGION=us-east-1
  export SECRETS_AWS_TWITCH_SECRET_NAME=stream-daemon/twitch
  export SECRETS_AWS_YOUTUBE_SECRET_NAME=stream-daemon/youtube
  export SECRETS_AWS_MASTODON_SECRET_NAME=stream-daemon/mastodon
```

**Secret Structure:**
```json
{
  "client_id": "abc123",
  "client_secret": "secret123",
  "username": "streamer"
}
```

### HashiCorp Vault

**Prerequisites:**
- Vault server running
- Vault CLI installed
- Vault token with write permissions

**Setup Flow:**
1. Checks for Vault CLI
2. Prompts for Vault URL and token
3. Tests connection
4. Creates KV secrets for each platform

**Output Example:**
```
✓ Vault CLI installed
Vault URL [http://127.0.0.1:8200]: https://vault.example.com
Vault Token: ************
✓ Connected to Vault
Creating secrets in Vault...
✓ Twitch secrets created
✓ YouTube secrets created
✓ Mastodon secrets created
✓ Secrets created in Vault!

Set these environment variables to use Vault:
  export SECRETS_MANAGER=vault
  export SECRETS_VAULT_URL=https://vault.example.com
  export SECRETS_VAULT_TOKEN=s.abc123
  export SECRETS_VAULT_TWITCH_SECRET_PATH=secret/stream-daemon/twitch
  export SECRETS_VAULT_YOUTUBE_SECRET_PATH=secret/stream-daemon/youtube
  export SECRETS_VAULT_MASTODON_SECRET_PATH=secret/stream-daemon/mastodon
```

**Secret Path Structure:**
```
secret/stream-daemon/
  ├── twitch
  ├── youtube
  ├── kick
  ├── mastodon
  ├── bluesky
  ├── discord
  └── matrix
```

### .env File

**Setup Flow:**
1. Checks if `.env` exists
2. Prompts to overwrite if exists
3. Creates well-formatted `.env` file
4. Sets secure permissions (`chmod 600`)

**Output Example:**
```
Creating .env file...
✓ Created .env file: /path/to/stream-daemon/.env

⚠ WARNING: .env contains sensitive credentials!
  - Do NOT commit .env to git
  - Keep it secure with: chmod 600 .env
```

**.env Format:**
```ini
# Stream Daemon Configuration
# Generated by create-secrets.sh on 2025-10-25

# ============================================
# Streaming Platforms
# ============================================

# Twitch
TWITCH_ENABLE=True
TWITCH_USERNAME=your_username
TWITCH_CLIENT_ID=abc123
TWITCH_CLIENT_SECRET=secret123

# YouTube
YOUTUBE_ENABLE=True
YOUTUBE_USERNAME=@YourChannel
YOUTUBE_API_KEY=api_key_123

# ============================================
# Social Media Platforms
# ============================================

# Mastodon
MASTODON_ENABLE_POSTING=True
MASTODON_API_BASE_URL=https://mastodon.social
MASTODON_CLIENT_ID=client_id
MASTODON_CLIENT_SECRET=client_secret
MASTODON_ACCESS_TOKEN=access_token

# ... and so on
```

---

## Advanced Features

### Loading Existing Configuration

If `.env` exists, the wizard offers to load it:

```
Found existing .env file
Load existing values from .env as defaults? [Y/n]: Y
✓ Loaded values from .env
```

Then all prompts show current values:
```
Twitch Username [your_current_username]: 
```

Press Enter to keep, or type new value to change.

### Sensitive Input Handling

- Passwords/tokens are hidden during input
- Shown as `************` in output
- Never logged to console
- Stored securely in chosen platform

### Validation

**Checks performed:**
- Required tools installed (doppler, aws, vault CLI)
- Authentication successful
- Credentials valid
- Permissions correct

**Error messages:**
```
ERROR: Doppler CLI not found
Install with: curl -Ls https://cli.doppler.com/install.sh | sh

ERROR: AWS credentials not configured
Run: aws configure

ERROR: Cannot connect to Vault
```

---

## Troubleshooting

### Doppler CLI Not Found

**Solution:**
```bash
# Install Doppler CLI
curl -Ls https://cli.doppler.com/install.sh | sh

# Verify installation
doppler --version
```

### AWS CLI Not Found

**Solution:**
```bash
# Install AWS CLI
pip install awscli

# Or use official installer
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

### Vault Connection Failed

**Possible causes:**
- Vault server not running
- Incorrect URL
- Invalid token
- Network issues

**Solutions:**
```bash
# Check Vault status
vault status

# Test connection
vault login

# Verify environment
echo $VAULT_ADDR
echo $VAULT_TOKEN
```

### .env Permission Denied

**Solution:**
```bash
# Fix permissions
chmod 600 .env

# Verify
ls -la .env
# Should show: -rw------- (owner read/write only)
```

---

## Best Practices

### Development Workflow

1. **Initial Setup:**
   ```bash
   ./scripts/create-secrets.sh
   # Select: 4) Create .env file only
   ```

2. **Test Locally:**
   ```bash
   python3 stream-daemon.py --test
   ```

3. **Move to Production:**
   ```bash
   ./scripts/create-secrets.sh
   # Select: 1) Doppler
   # Wizard loads from .env
   ```

### Security Recommendations

**DO:**
- ✅ Use Doppler/AWS/Vault for production
- ✅ Use different environments (dev/stg/prd)
- ✅ Rotate secrets regularly
- ✅ Use minimum required permissions
- ✅ Keep `.env` in `.gitignore`

**DON'T:**
- ❌ Commit `.env` to git
- ❌ Share secrets in plaintext
- ❌ Use production secrets in development
- ❌ Store secrets in code
- ❌ Use weak passwords

### Multiple Environments

**Setup:**
```bash
# Development
./scripts/create-secrets.sh
# Select Doppler, config: dev

# Staging
./scripts/create-secrets.sh
# Select Doppler, config: stg

# Production
./scripts/create-secrets.sh
# Select Doppler, config: prd
```

**Usage:**
```bash
# Development
doppler run --config dev -- python3 stream-daemon.py

# Staging
doppler run --config stg -- python3 stream-daemon.py

# Production
doppler run --config prd -- python3 stream-daemon.py
```

---

## Integration with Other Tools

### systemd Service

```bash
# Create secrets
./scripts/create-secrets.sh

# Install service
sudo ./scripts/install-systemd.sh
```

The install script will use secrets from:
- Doppler (if configured)
- .env file (as fallback)

### Docker

```bash
# Create secrets
./scripts/create-secrets.sh

# Docker run
docker run --env-file .env stream-daemon

# Or with Doppler
doppler run -- docker-compose up
```

### GitHub Actions

```yaml
- name: Setup secrets
  run: |
    # Install Doppler CLI
    curl -Ls https://cli.doppler.com/install.sh | sh
    
    # Set token from GitHub secret
    export DOPPLER_TOKEN=${{ secrets.DOPPLER_TOKEN }}
    
    # Run with Doppler
    doppler run -- python stream-daemon.py
```

---

## See Also

- [Secrets Management Guide](secrets.md)
- [Doppler Integration](secrets.md#doppler)
- [AWS Secrets Manager](secrets.md#aws-secrets-manager)
- [HashiCorp Vault](secrets.md#hashicorp-vault)
- [Installation Guide](../getting-started/installation.md)

---

## Script Options

### Environment Variables

Control wizard behavior with environment variables:

```bash
# Skip prompts (CI/CD)
export NONINTERACTIVE=true

# Force specific manager
export SECRETS_MANAGER=doppler

# Pre-set values
export TWITCH_USERNAME=streamer
export TWITCH_CLIENT_ID=abc123
# ... etc

# Run wizard
./scripts/create-secrets.sh
```

### Command Line Flags

*(Future enhancement)*
```bash
# Quick Doppler setup
./scripts/create-secrets.sh --doppler

# Update existing
./scripts/create-secrets.sh --update

# Dry run
./scripts/create-secrets.sh --dry-run
```

---

**Happy Secret Management! 🔐**
