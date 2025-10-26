#!/bin/bash
# Stream Daemon - Secrets Management Setup Script
# This script helps create and configure secrets in Doppler, AWS Secrets Manager, or HashiCorp Vault

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script directory and project directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Banner
echo -e "${CYAN}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════╗
║        Stream Daemon - Secrets Setup Wizard              ║
║  Configure secrets for Doppler, AWS, or HashiCorp Vault  ║
╚═══════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"
echo ""

# Function to display section headers
section_header() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo ""
}

# Function to prompt for input with default value
prompt_with_default() {
    local prompt="$1"
    local default="$2"
    local var_name="$3"
    
    if [ -n "$default" ]; then
        read -p "$(echo -e ${GREEN}${prompt}${NC} [${YELLOW}${default}${NC}]: )" value
        eval $var_name="${value:-$default}"
    else
        read -p "$(echo -e ${GREEN}${prompt}${NC}: )" value
        eval $var_name="$value"
    fi
}

# Function to prompt for sensitive input (hidden)
prompt_secret() {
    local prompt="$1"
    local var_name="$2"
    
    read -s -p "$(echo -e ${GREEN}${prompt}${NC}: )" value
    echo ""
    eval $var_name="$value"
}

# Function to prompt yes/no
prompt_yes_no() {
    local prompt="$1"
    local default="${2:-N}"
    
    if [ "$default" = "Y" ]; then
        read -p "$(echo -e ${GREEN}${prompt}${NC} [${YELLOW}Y/n${NC}]): )" -n 1 -r response
    else
        read -p "$(echo -e ${GREEN}${prompt}${NC} [${YELLOW}y/N${NC}]): )" -n 1 -r response
    fi
    echo ""
    
    if [ "$default" = "Y" ]; then
        [[ ! $response =~ ^[Nn]$ ]]
    else
        [[ $response =~ ^[Yy]$ ]]
    fi
}

# Check if .env exists and offer to load it
if [ -f "$PROJECT_DIR/.env" ]; then
    echo -e "${YELLOW}Found existing .env file${NC}"
    if prompt_yes_no "Load existing values from .env as defaults?" "Y"; then
        source "$PROJECT_DIR/.env"
        LOAD_FROM_ENV=true
        echo -e "${GREEN}✓${NC} Loaded values from .env"
    else
        LOAD_FROM_ENV=false
    fi
else
    LOAD_FROM_ENV=false
fi

# Select secrets manager
section_header "Select Secrets Manager"
echo "Choose where you want to store your secrets:"
echo "  1) Doppler (Recommended - Modern secrets platform)"
echo "  2) AWS Secrets Manager (AWS cloud integration)"
echo "  3) HashiCorp Vault (Self-hosted, enterprise)"
echo "  4) Create .env file only (No secrets manager)"
echo ""

while true; do
    read -p "$(echo -e ${GREEN}Select option [1-4]${NC}: )" -n 1 -r SECRETS_MANAGER
    echo ""
    
    case $SECRETS_MANAGER in
        1) MANAGER="doppler"; break ;;
        2) MANAGER="aws"; break ;;
        3) MANAGER="vault"; break ;;
        4) MANAGER="env"; break ;;
        *) echo -e "${RED}Invalid option${NC}" ;;
    esac
done

echo ""
echo -e "${GREEN}✓${NC} Selected: ${CYAN}${MANAGER}${NC}"

# Collect streaming platform credentials
section_header "Streaming Platforms Configuration"

# Twitch
if prompt_yes_no "Configure Twitch?" "Y"; then
    TWITCH_ENABLE="True"
    prompt_with_default "Twitch Username" "${TWITCH_USERNAME}" "TWITCH_USERNAME"
    echo ""
    echo -e "${YELLOW}Twitch API credentials (get from: https://dev.twitch.tv/console)${NC}"
    prompt_with_default "Twitch Client ID" "${TWITCH_CLIENT_ID}" "TWITCH_CLIENT_ID"
    prompt_secret "Twitch Client Secret" "TWITCH_CLIENT_SECRET"
else
    TWITCH_ENABLE="False"
fi

# YouTube
if prompt_yes_no "Configure YouTube?" "Y"; then
    YOUTUBE_ENABLE="True"
    echo ""
    echo -e "${YELLOW}You can use either Channel ID or @Username${NC}"
    prompt_with_default "YouTube Channel ID (or leave empty)" "${YOUTUBE_CHANNEL_ID}" "YOUTUBE_CHANNEL_ID"
    if [ -z "$YOUTUBE_CHANNEL_ID" ]; then
        prompt_with_default "YouTube @Username" "${YOUTUBE_USERNAME}" "YOUTUBE_USERNAME"
    fi
    echo ""
    echo -e "${YELLOW}YouTube API Key (get from: https://console.cloud.google.com/apis/credentials)${NC}"
    prompt_secret "YouTube API Key" "YOUTUBE_API_KEY"
else
    YOUTUBE_ENABLE="False"
fi

# Kick
if prompt_yes_no "Configure Kick?" "N"; then
    KICK_ENABLE="True"
    prompt_with_default "Kick Username" "${KICK_USERNAME}" "KICK_USERNAME"
    
    if prompt_yes_no "Use Kick OAuth? (better rate limits)" "N"; then
        echo ""
        echo -e "${YELLOW}Kick OAuth requires 2FA enabled on your account${NC}"
        prompt_with_default "Kick Client ID" "${KICK_CLIENT_ID}" "KICK_CLIENT_ID"
        prompt_secret "Kick Client Secret" "KICK_CLIENT_SECRET"
    fi
else
    KICK_ENABLE="False"
fi

# Collect social platform credentials
section_header "Social Media Platforms Configuration"

# Mastodon
if prompt_yes_no "Configure Mastodon?" "Y"; then
    MASTODON_ENABLE_POSTING="True"
    prompt_with_default "Mastodon Instance URL" "${MASTODON_API_BASE_URL:-https://mastodon.social}" "MASTODON_API_BASE_URL"
    echo ""
    echo -e "${YELLOW}Get credentials from: ${MASTODON_API_BASE_URL}/settings/applications${NC}"
    prompt_with_default "Mastodon Client ID" "${MASTODON_CLIENT_ID}" "MASTODON_CLIENT_ID"
    prompt_secret "Mastodon Client Secret" "MASTODON_CLIENT_SECRET"
    prompt_secret "Mastodon Access Token" "MASTODON_ACCESS_TOKEN"
else
    MASTODON_ENABLE_POSTING="False"
fi

# Bluesky
if prompt_yes_no "Configure Bluesky?" "Y"; then
    BLUESKY_ENABLE_POSTING="True"
    prompt_with_default "Bluesky Handle" "${BLUESKY_HANDLE}" "BLUESKY_HANDLE"
    echo ""
    echo -e "${YELLOW}Create app password at: https://bsky.app/settings/app-passwords${NC}"
    prompt_secret "Bluesky App Password" "BLUESKY_APP_PASSWORD"
else
    BLUESKY_ENABLE_POSTING="False"
fi

# Discord
if prompt_yes_no "Configure Discord?" "Y"; then
    DISCORD_ENABLE_POSTING="True"
    echo ""
    echo -e "${YELLOW}Create webhook in Discord: Server Settings → Integrations → Webhooks${NC}"
    prompt_with_default "Discord Webhook URL" "${DISCORD_WEBHOOK_URL}" "DISCORD_WEBHOOK_URL"
    
    # Optional: Platform-specific webhooks
    if prompt_yes_no "Use different webhooks for each streaming platform?" "N"; then
        prompt_with_default "Twitch Discord Webhook" "${DISCORD_WEBHOOK_URL_TWITCH}" "DISCORD_WEBHOOK_URL_TWITCH"
        prompt_with_default "YouTube Discord Webhook" "${DISCORD_WEBHOOK_URL_YOUTUBE}" "DISCORD_WEBHOOK_URL_YOUTUBE"
        prompt_with_default "Kick Discord Webhook" "${DISCORD_WEBHOOK_URL_KICK}" "DISCORD_WEBHOOK_URL_KICK"
    fi
    
    # Optional: Role mentions
    if prompt_yes_no "Configure role mentions?" "N"; then
        prompt_with_default "Twitch Role Mention (e.g., @Twitch Viewers)" "${DISCORD_ROLE_MENTION_TWITCH}" "DISCORD_ROLE_MENTION_TWITCH"
        prompt_with_default "YouTube Role Mention" "${DISCORD_ROLE_MENTION_YOUTUBE}" "DISCORD_ROLE_MENTION_YOUTUBE"
        prompt_with_default "Kick Role Mention" "${DISCORD_ROLE_MENTION_KICK}" "DISCORD_ROLE_MENTION_KICK"
    fi
    
    # Optional: Live embed updates
    if prompt_yes_no "Enable live embed updates?" "Y"; then
        DISCORD_UPDATE_LIVE_MESSAGE="True"
        prompt_with_default "Update interval (seconds)" "${DISCORD_UPDATE_INTERVAL:-60}" "DISCORD_UPDATE_INTERVAL"
    fi
else
    DISCORD_ENABLE_POSTING="False"
fi

# Matrix
if prompt_yes_no "Configure Matrix?" "N"; then
    MATRIX_ENABLE_POSTING="True"
    prompt_with_default "Matrix Homeserver" "${MATRIX_HOMESERVER:-https://matrix.org}" "MATRIX_HOMESERVER"
    prompt_with_default "Matrix Room ID" "${MATRIX_ROOM_ID}" "MATRIX_ROOM_ID"
    
    if prompt_yes_no "Use access token? (recommended)" "Y"; then
        prompt_secret "Matrix Access Token" "MATRIX_ACCESS_TOKEN"
    else
        prompt_with_default "Matrix Username (e.g., @bot:matrix.org)" "${MATRIX_USERNAME}" "MATRIX_USERNAME"
        prompt_secret "Matrix Password" "MATRIX_PASSWORD"
    fi
else
    MATRIX_ENABLE_POSTING="False"
fi

# AI/LLM Configuration
section_header "AI/LLM Configuration (Optional)"

if prompt_yes_no "Enable AI-powered messages with Google Gemini?" "Y"; then
    LLM_ENABLE="True"
    LLM_PROVIDER="gemini"
    echo ""
    echo -e "${YELLOW}Get API key from: https://aistudio.google.com/app/apikey${NC}"
    prompt_secret "Gemini API Key" "LLM_GEMINI_API_KEY"
    prompt_with_default "Gemini Model" "${LLM_GEMINI_MODEL:-gemini-2.0-flash-exp}" "LLM_GEMINI_MODEL"
else
    LLM_ENABLE="False"
fi

# Settings
section_header "Stream Daemon Settings"

prompt_with_default "Check interval when offline (minutes)" "${SETTINGS_CHECK_INTERVAL:-5}" "SETTINGS_CHECK_INTERVAL"
prompt_with_default "Check interval when live (minutes)" "${SETTINGS_POST_INTERVAL:-60}" "SETTINGS_POST_INTERVAL"

# Message threading options
echo ""
echo "Multi-platform posting options:"
echo "  - separate: Individual posts per platform"
echo "  - thread: Reply chain"
echo "  - combined: Single post for all platforms"
prompt_with_default "Live announcement mode" "${MESSAGES_LIVE_THREADING_MODE:-combined}" "MESSAGES_LIVE_THREADING_MODE"
prompt_with_default "Stream end announcement mode" "${MESSAGES_END_THREADING_MODE:-single_when_all_end}" "MESSAGES_END_THREADING_MODE"

# Now create the secrets based on selected manager
section_header "Creating Secrets"

# Function to create Doppler secrets
create_doppler_secrets() {
    echo "Setting up Doppler secrets..."
    echo ""
    
    # Check if doppler CLI is installed
    if ! command -v doppler &> /dev/null; then
        echo -e "${YELLOW}Doppler CLI not found. Installing...${NC}"
        echo ""
        echo "Run these commands to install Doppler CLI:"
        echo "  curl -Ls https://cli.doppler.com/install.sh | sh"
        echo ""
        read -p "Press Enter after installing Doppler CLI..."
        
        if ! command -v doppler &> /dev/null; then
            echo -e "${RED}ERROR: Doppler CLI still not found${NC}"
            return 1
        fi
    fi
    
    echo -e "${GREEN}✓${NC} Doppler CLI installed"
    
    # Login check
    if ! doppler me &> /dev/null; then
        echo ""
        echo "Please login to Doppler:"
        doppler login
    fi
    
    echo -e "${GREEN}✓${NC} Logged in to Doppler"
    
    # Select or create project
    echo ""
    prompt_with_default "Doppler Project Name" "stream-daemon" "DOPPLER_PROJECT"
    prompt_with_default "Doppler Config (environment)" "dev" "DOPPLER_CONFIG"
    
    # Setup project
    if doppler projects get "$DOPPLER_PROJECT" &> /dev/null; then
        echo -e "${GREEN}✓${NC} Project '$DOPPLER_PROJECT' exists"
    else
        echo "Creating project '$DOPPLER_PROJECT'..."
        doppler projects create "$DOPPLER_PROJECT" --description "Stream Daemon secrets"
        echo -e "${GREEN}✓${NC} Project created"
    fi
    
    # Setup config
    if doppler configs get "$DOPPLER_CONFIG" --project "$DOPPLER_PROJECT" &> /dev/null; then
        echo -e "${GREEN}✓${NC} Config '$DOPPLER_CONFIG' exists"
    else
        echo "Creating config '$DOPPLER_CONFIG'..."
        doppler configs create "$DOPPLER_CONFIG" --project "$DOPPLER_PROJECT"
        echo -e "${GREEN}✓${NC} Config created"
    fi
    
    echo ""
    echo "Uploading secrets to Doppler..."
    
    # Create temporary env file with ONLY secrets/webhooks
    TEMP_ENV=$(mktemp)
    
    # Streaming platform SECRETS only
    [ "$TWITCH_ENABLE" = "True" ] && {
        echo "TWITCH_CLIENT_ID=$TWITCH_CLIENT_ID" >> "$TEMP_ENV"
        echo "TWITCH_CLIENT_SECRET=$TWITCH_CLIENT_SECRET" >> "$TEMP_ENV"
    }
    
    [ "$YOUTUBE_ENABLE" = "True" ] && {
        echo "YOUTUBE_API_KEY=$YOUTUBE_API_KEY" >> "$TEMP_ENV"
    }
    
    [ "$KICK_ENABLE" = "True" ] && {
        [ -n "$KICK_CLIENT_ID" ] && echo "KICK_CLIENT_ID=$KICK_CLIENT_ID" >> "$TEMP_ENV"
        [ -n "$KICK_CLIENT_SECRET" ] && echo "KICK_CLIENT_SECRET=$KICK_CLIENT_SECRET" >> "$TEMP_ENV"
    }
    
    # Social platform SECRETS/WEBHOOKS only
    [ "$MASTODON_ENABLE_POSTING" = "True" ] && {
        echo "MASTODON_CLIENT_ID=$MASTODON_CLIENT_ID" >> "$TEMP_ENV"
        echo "MASTODON_CLIENT_SECRET=$MASTODON_CLIENT_SECRET" >> "$TEMP_ENV"
        echo "MASTODON_ACCESS_TOKEN=$MASTODON_ACCESS_TOKEN" >> "$TEMP_ENV"
    }
    
    [ "$BLUESKY_ENABLE_POSTING" = "True" ] && {
        echo "BLUESKY_APP_PASSWORD=$BLUESKY_APP_PASSWORD" >> "$TEMP_ENV"
    }
    
    [ "$DISCORD_ENABLE_POSTING" = "True" ] && {
        echo "DISCORD_WEBHOOK_URL=$DISCORD_WEBHOOK_URL" >> "$TEMP_ENV"
        [ -n "$DISCORD_WEBHOOK_URL_TWITCH" ] && echo "DISCORD_WEBHOOK_URL_TWITCH=$DISCORD_WEBHOOK_URL_TWITCH" >> "$TEMP_ENV"
        [ -n "$DISCORD_WEBHOOK_URL_YOUTUBE" ] && echo "DISCORD_WEBHOOK_URL_YOUTUBE=$DISCORD_WEBHOOK_URL_YOUTUBE" >> "$TEMP_ENV"
        [ -n "$DISCORD_WEBHOOK_URL_KICK" ] && echo "DISCORD_WEBHOOK_URL_KICK=$DISCORD_WEBHOOK_URL_KICK" >> "$TEMP_ENV"
    }
    
    [ "$MATRIX_ENABLE_POSTING" = "True" ] && {
        [ -n "$MATRIX_ACCESS_TOKEN" ] && echo "MATRIX_ACCESS_TOKEN=$MATRIX_ACCESS_TOKEN" >> "$TEMP_ENV"
        [ -n "$MATRIX_PASSWORD" ] && echo "MATRIX_PASSWORD=$MATRIX_PASSWORD" >> "$TEMP_ENV"
    }
    
    # LLM API keys
    [ "$LLM_ENABLE" = "True" ] && {
        echo "LLM_GEMINI_API_KEY=$LLM_GEMINI_API_KEY" >> "$TEMP_ENV"
    }
    
    # Upload to Doppler
    doppler secrets upload "$TEMP_ENV" --project "$DOPPLER_PROJECT" --config "$DOPPLER_CONFIG"
    
    rm -f "$TEMP_ENV"
    
    # Generate Doppler token
    echo ""
    echo "Generating Doppler service token..."
    DOPPLER_TOKEN=$(doppler configs tokens create cli-token --project "$DOPPLER_PROJECT" --config "$DOPPLER_CONFIG" --plain 2>/dev/null || echo "")
    
    if [ -z "$DOPPLER_TOKEN" ]; then
        echo -e "${YELLOW}Note: Service token already exists or couldn't be created${NC}"
        echo "You can create one manually with:"
        echo "  doppler configs tokens create <name> --project $DOPPLER_PROJECT --config $DOPPLER_CONFIG --plain"
    fi
    
    echo ""
    echo -e "${GREEN}✓${NC} Secrets uploaded to Doppler!"
    echo ""
    
    # Store Doppler project/config for .env creation
    export DOPPLER_PROJECT_NAME="$DOPPLER_PROJECT"
    export DOPPLER_CONFIG_NAME="$DOPPLER_CONFIG"
    export DOPPLER_SERVICE_TOKEN="$DOPPLER_TOKEN"
}

# Function to create AWS secrets
create_aws_secrets() {
    echo "Setting up AWS Secrets Manager..."
    echo ""
    
    # Check if AWS CLI is installed
    if ! command -v aws &> /dev/null; then
        echo -e "${RED}ERROR: AWS CLI not found${NC}"
        echo "Install with: pip install awscli"
        echo "Or see: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
        return 1
    fi
    
    echo -e "${GREEN}✓${NC} AWS CLI installed"
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        echo -e "${RED}ERROR: AWS credentials not configured${NC}"
        echo "Run: aws configure"
        return 1
    fi
    
    echo -e "${GREEN}✓${NC} AWS credentials configured"
    
    # Select region
    prompt_with_default "AWS Region" "${AWS_REGION:-us-east-1}" "AWS_REGION_CONFIG"
    
    # Create secrets
    SECRET_PREFIX="stream-daemon"
    
    echo ""
    echo "Creating secrets in AWS Secrets Manager (SECRETS ONLY)..."
    
    # Streaming platforms - SECRETS ONLY
    if [ "$TWITCH_ENABLE" = "True" ]; then
        SECRET_VALUE=$(cat <<EOF
{
  "client_id": "$TWITCH_CLIENT_ID",
  "client_secret": "$TWITCH_CLIENT_SECRET"
}
EOF
)
        aws secretsmanager create-secret \
            --name "${SECRET_PREFIX}/twitch" \
            --description "Twitch API credentials for Stream Daemon" \
            --secret-string "$SECRET_VALUE" \
            --region "$AWS_REGION_CONFIG" 2>/dev/null || \
        aws secretsmanager update-secret \
            --secret-id "${SECRET_PREFIX}/twitch" \
            --secret-string "$SECRET_VALUE" \
            --region "$AWS_REGION_CONFIG"
        
        echo -e "${GREEN}✓${NC} Twitch secrets created/updated"
    fi
    
    if [ "$YOUTUBE_ENABLE" = "True" ]; then
        SECRET_VALUE=$(cat <<EOF
{
  "api_key": "$YOUTUBE_API_KEY"
}
EOF
)
        aws secretsmanager create-secret \
            --name "${SECRET_PREFIX}/youtube" \
            --description "YouTube API credentials for Stream Daemon" \
            --secret-string "$SECRET_VALUE" \
            --region "$AWS_REGION_CONFIG" 2>/dev/null || \
        aws secretsmanager update-secret \
            --secret-id "${SECRET_PREFIX}/youtube" \
            --secret-string "$SECRET_VALUE" \
            --region "$AWS_REGION_CONFIG"
        
        echo -e "${GREEN}✓${NC} YouTube secrets created/updated"
    fi
    
    if [ "$KICK_ENABLE" = "True" ] && [ -n "$KICK_CLIENT_ID" ]; then
        SECRET_VALUE=$(cat <<EOF
{
  "client_id": "$KICK_CLIENT_ID",
  "client_secret": "$KICK_CLIENT_SECRET"
}
EOF
)
        aws secretsmanager create-secret \
            --name "${SECRET_PREFIX}/kick" \
            --description "Kick API credentials for Stream Daemon" \
            --secret-string "$SECRET_VALUE" \
            --region "$AWS_REGION_CONFIG" 2>/dev/null || \
        aws secretsmanager update-secret \
            --secret-id "${SECRET_PREFIX}/kick" \
            --secret-string "$SECRET_VALUE" \
            --region "$AWS_REGION_CONFIG"
        
        echo -e "${GREEN}✓${NC} Kick secrets created/updated"
    fi
    
    if [ "$MASTODON_ENABLE_POSTING" = "True" ]; then
        SECRET_VALUE=$(cat <<EOF
{
  "client_id": "$MASTODON_CLIENT_ID",
  "client_secret": "$MASTODON_CLIENT_SECRET",
  "access_token": "$MASTODON_ACCESS_TOKEN"
}
EOF
)
        aws secretsmanager create-secret \
            --name "${SECRET_PREFIX}/mastodon" \
            --description "Mastodon API credentials for Stream Daemon" \
            --secret-string "$SECRET_VALUE" \
            --region "$AWS_REGION_CONFIG" 2>/dev/null || \
        aws secretsmanager update-secret \
            --secret-id "${SECRET_PREFIX}/mastodon" \
            --secret-string "$SECRET_VALUE" \
            --region "$AWS_REGION_CONFIG"
        
        echo -e "${GREEN}✓${NC} Mastodon secrets created/updated"
    fi
    
    if [ "$BLUESKY_ENABLE_POSTING" = "True" ]; then
        SECRET_VALUE=$(cat <<EOF
{
  "app_password": "$BLUESKY_APP_PASSWORD"
}
EOF
)
        aws secretsmanager create-secret \
            --name "${SECRET_PREFIX}/bluesky" \
            --description "Bluesky API credentials for Stream Daemon" \
            --secret-string "$SECRET_VALUE" \
            --region "$AWS_REGION_CONFIG" 2>/dev/null || \
        aws secretsmanager update-secret \
            --secret-id "${SECRET_PREFIX}/bluesky" \
            --secret-string "$SECRET_VALUE" \
            --region "$AWS_REGION_CONFIG"
        
        echo -e "${GREEN}✓${NC} Bluesky secrets created/updated"
    fi
    
    if [ "$DISCORD_ENABLE_POSTING" = "True" ]; then
        SECRET_VALUE="{"
        SECRET_VALUE="$SECRET_VALUE\"webhook_url\": \"$DISCORD_WEBHOOK_URL\""
        [ -n "$DISCORD_WEBHOOK_URL_TWITCH" ] && SECRET_VALUE="$SECRET_VALUE,\"webhook_url_twitch\": \"$DISCORD_WEBHOOK_URL_TWITCH\""
        [ -n "$DISCORD_WEBHOOK_URL_YOUTUBE" ] && SECRET_VALUE="$SECRET_VALUE,\"webhook_url_youtube\": \"$DISCORD_WEBHOOK_URL_YOUTUBE\""
        [ -n "$DISCORD_WEBHOOK_URL_KICK" ] && SECRET_VALUE="$SECRET_VALUE,\"webhook_url_kick\": \"$DISCORD_WEBHOOK_URL_KICK\""
        SECRET_VALUE="$SECRET_VALUE}"
        
        aws secretsmanager create-secret \
            --name "${SECRET_PREFIX}/discord" \
            --description "Discord webhooks for Stream Daemon" \
            --secret-string "$SECRET_VALUE" \
            --region "$AWS_REGION_CONFIG" 2>/dev/null || \
        aws secretsmanager update-secret \
            --secret-id "${SECRET_PREFIX}/discord" \
            --secret-string "$SECRET_VALUE" \
            --region "$AWS_REGION_CONFIG"
        
        echo -e "${GREEN}✓${NC} Discord webhooks created/updated"
    fi
    
    if [ "$MATRIX_ENABLE_POSTING" = "True" ]; then
        SECRET_VALUE="{"
        [ -n "$MATRIX_ACCESS_TOKEN" ] && SECRET_VALUE="$SECRET_VALUE\"access_token\": \"$MATRIX_ACCESS_TOKEN\""
        [ -n "$MATRIX_PASSWORD" ] && SECRET_VALUE="$SECRET_VALUE\"password\": \"$MATRIX_PASSWORD\""
        SECRET_VALUE="$SECRET_VALUE}"
        
        if [ "$SECRET_VALUE" != "{}" ]; then
            aws secretsmanager create-secret \
                --name "${SECRET_PREFIX}/matrix" \
                --description "Matrix credentials for Stream Daemon" \
                --secret-string "$SECRET_VALUE" \
                --region "$AWS_REGION_CONFIG" 2>/dev/null || \
            aws secretsmanager update-secret \
                --secret-id "${SECRET_PREFIX}/matrix" \
                --secret-string "$SECRET_VALUE" \
                --region "$AWS_REGION_CONFIG"
            
            echo -e "${GREEN}✓${NC} Matrix secrets created/updated"
        fi
    fi
    
    if [ "$LLM_ENABLE" = "True" ]; then
        SECRET_VALUE=$(cat <<EOF
{
  "gemini_api_key": "$LLM_GEMINI_API_KEY"
}
EOF
)
        aws secretsmanager create-secret \
            --name "${SECRET_PREFIX}/llm" \
            --description "LLM API keys for Stream Daemon" \
            --secret-string "$SECRET_VALUE" \
            --region "$AWS_REGION_CONFIG" 2>/dev/null || \
        aws secretsmanager update-secret \
            --secret-id "${SECRET_PREFIX}/llm" \
            --secret-string "$SECRET_VALUE" \
            --region "$AWS_REGION_CONFIG"
        
        echo -e "${GREEN}✓${NC} LLM secrets created/updated"
    fi
    
    echo ""
    echo -e "${GREEN}✓${NC} Secrets created in AWS Secrets Manager!"
    echo ""
    
    # Store AWS config for .env creation
    export AWS_SECRETS_REGION="$AWS_REGION_CONFIG"
    export AWS_SECRET_PREFIX="$SECRET_PREFIX"
}

# Function to create Vault secrets
create_vault_secrets() {
    echo "Setting up HashiCorp Vault secrets..."
    echo ""
    
    # Check if vault CLI is installed
    if ! command -v vault &> /dev/null; then
        echo -e "${RED}ERROR: Vault CLI not found${NC}"
        echo "Install from: https://www.vaultproject.io/downloads"
        return 1
    fi
    
    echo -e "${GREEN}✓${NC} Vault CLI installed"
    
    # Get Vault config
    prompt_with_default "Vault URL" "${VAULT_ADDR:-http://127.0.0.1:8200}" "VAULT_ADDR_CONFIG"
    prompt_secret "Vault Token" "VAULT_TOKEN_CONFIG"
    
    export VAULT_ADDR="$VAULT_ADDR_CONFIG"
    export VAULT_TOKEN="$VAULT_TOKEN_CONFIG"
    
    # Test connection
    if ! vault status &> /dev/null; then
        echo -e "${RED}ERROR: Cannot connect to Vault${NC}"
        return 1
    fi
    
    echo -e "${GREEN}✓${NC} Connected to Vault"
    
    # Create secrets
    prompt_with_default "Vault secret path prefix" "secret/stream-daemon" "SECRET_PATH"
    
    echo ""
    echo "Creating secrets in Vault (SECRETS ONLY)..."
    
    if [ "$TWITCH_ENABLE" = "True" ]; then
        vault kv put "${SECRET_PATH}/twitch" \
            client_id="$TWITCH_CLIENT_ID" \
            client_secret="$TWITCH_CLIENT_SECRET"
        echo -e "${GREEN}✓${NC} Twitch secrets created"
    fi
    
    if [ "$YOUTUBE_ENABLE" = "True" ]; then
        vault kv put "${SECRET_PATH}/youtube" \
            api_key="$YOUTUBE_API_KEY"
        echo -e "${GREEN}✓${NC} YouTube secrets created"
    fi
    
    if [ "$KICK_ENABLE" = "True" ] && [ -n "$KICK_CLIENT_ID" ]; then
        vault kv put "${SECRET_PATH}/kick" \
            client_id="$KICK_CLIENT_ID" \
            client_secret="$KICK_CLIENT_SECRET"
        echo -e "${GREEN}✓${NC} Kick secrets created"
    fi
    
    if [ "$MASTODON_ENABLE_POSTING" = "True" ]; then
        vault kv put "${SECRET_PATH}/mastodon" \
            client_id="$MASTODON_CLIENT_ID" \
            client_secret="$MASTODON_CLIENT_SECRET" \
            access_token="$MASTODON_ACCESS_TOKEN"
        echo -e "${GREEN}✓${NC} Mastodon secrets created"
    fi
    
    if [ "$BLUESKY_ENABLE_POSTING" = "True" ]; then
        vault kv put "${SECRET_PATH}/bluesky" \
            app_password="$BLUESKY_APP_PASSWORD"
        echo -e "${GREEN}✓${NC} Bluesky secrets created"
    fi
    
    if [ "$DISCORD_ENABLE_POSTING" = "True" ]; then
        VAULT_CMD="vault kv put ${SECRET_PATH}/discord webhook_url=\"$DISCORD_WEBHOOK_URL\""
        [ -n "$DISCORD_WEBHOOK_URL_TWITCH" ] && VAULT_CMD="$VAULT_CMD webhook_url_twitch=\"$DISCORD_WEBHOOK_URL_TWITCH\""
        [ -n "$DISCORD_WEBHOOK_URL_YOUTUBE" ] && VAULT_CMD="$VAULT_CMD webhook_url_youtube=\"$DISCORD_WEBHOOK_URL_YOUTUBE\""
        [ -n "$DISCORD_WEBHOOK_URL_KICK" ] && VAULT_CMD="$VAULT_CMD webhook_url_kick=\"$DISCORD_WEBHOOK_URL_KICK\""
        eval "$VAULT_CMD"
        echo -e "${GREEN}✓${NC} Discord webhooks created"
    fi
    
    if [ "$MATRIX_ENABLE_POSTING" = "True" ]; then
        VAULT_CMD="vault kv put ${SECRET_PATH}/matrix"
        [ -n "$MATRIX_ACCESS_TOKEN" ] && VAULT_CMD="$VAULT_CMD access_token=\"$MATRIX_ACCESS_TOKEN\""
        [ -n "$MATRIX_PASSWORD" ] && VAULT_CMD="$VAULT_CMD password=\"$MATRIX_PASSWORD\""
        if [ "$VAULT_CMD" != "vault kv put ${SECRET_PATH}/matrix" ]; then
            eval "$VAULT_CMD"
            echo -e "${GREEN}✓${NC} Matrix secrets created"
        fi
    fi
    
    if [ "$LLM_ENABLE" = "True" ]; then
        vault kv put "${SECRET_PATH}/llm" \
            gemini_api_key="$LLM_GEMINI_API_KEY"
        echo -e "${GREEN}✓${NC} LLM secrets created"
    fi
    
    echo ""
    echo -e "${GREEN}✓${NC} Secrets created in Vault!"
    echo ""
    
    # Store Vault config for .env creation
    export VAULT_URL_CONFIG="$VAULT_ADDR_CONFIG"
    export VAULT_SECRET_PATH="$SECRET_PATH"
    export VAULT_TOKEN_VALUE="$VAULT_TOKEN_CONFIG"
}

# Function to create .env file for secrets managers (CONFIG ONLY + connection info)
create_env_config_only() {
    local secrets_manager="$1"
    ENV_FILE="$PROJECT_DIR/.env"
    
    echo ""
    echo "Creating .env with configuration (secrets stored in $secrets_manager)..."
    echo ""
    
    if [ -f "$ENV_FILE" ]; then
        if prompt_yes_no ".env already exists. Overwrite?" "N"; then
            rm "$ENV_FILE"
        else
            echo -e "${YELLOW}Keeping existing .env${NC}"
            return 0
        fi
    fi
    
    cat > "$ENV_FILE" << EOF
# Stream Daemon Configuration
# Generated by create-secrets.sh on $(date)
# Secrets stored in: $secrets_manager

# ============================================
# Secrets Manager Configuration
# ============================================

EOF

    # Add secrets manager specific config
    case "$secrets_manager" in
        doppler)
            cat >> "$ENV_FILE" << EOF
# Doppler Configuration
# Secrets are stored in Doppler and pulled at runtime
# Option 1: Use service token (recommended for production)
EOF
            if [ -n "$DOPPLER_SERVICE_TOKEN" ]; then
                cat >> "$ENV_FILE" << EOF
DOPPLER_TOKEN=$DOPPLER_SERVICE_TOKEN
EOF
            else
                cat >> "$ENV_FILE" << EOF
# DOPPLER_TOKEN=<your-service-token>
# Generate with: doppler configs tokens create <name> --project $DOPPLER_PROJECT_NAME --config $DOPPLER_CONFIG_NAME --plain
EOF
            fi
            cat >> "$ENV_FILE" << EOF

# Option 2: Run with Doppler CLI (recommended for development)
# doppler run --project $DOPPLER_PROJECT_NAME --config $DOPPLER_CONFIG_NAME -- python stream-daemon.py

EOF
            ;;
        aws)
            cat >> "$ENV_FILE" << EOF
# AWS Secrets Manager Configuration
SECRETS_SECRET_MANAGER=aws
AWS_REGION=$AWS_SECRETS_REGION
SECRETS_AWS_PREFIX=$AWS_SECRET_PREFIX

# Secret names (auto-configured)
EOF
            [ "$TWITCH_ENABLE" = "True" ] && echo "SECRETS_AWS_TWITCH_SECRET_NAME=$AWS_SECRET_PREFIX/twitch" >> "$ENV_FILE"
            [ "$YOUTUBE_ENABLE" = "True" ] && echo "SECRETS_AWS_YOUTUBE_SECRET_NAME=$AWS_SECRET_PREFIX/youtube" >> "$ENV_FILE"
            [ "$KICK_ENABLE" = "True" ] && echo "SECRETS_AWS_KICK_SECRET_NAME=$AWS_SECRET_PREFIX/kick" >> "$ENV_FILE"
            [ "$MASTODON_ENABLE_POSTING" = "True" ] && echo "SECRETS_AWS_MASTODON_SECRET_NAME=$AWS_SECRET_PREFIX/mastodon" >> "$ENV_FILE"
            [ "$BLUESKY_ENABLE_POSTING" = "True" ] && echo "SECRETS_AWS_BLUESKY_SECRET_NAME=$AWS_SECRET_PREFIX/bluesky" >> "$ENV_FILE"
            [ "$DISCORD_ENABLE_POSTING" = "True" ] && echo "SECRETS_AWS_DISCORD_SECRET_NAME=$AWS_SECRET_PREFIX/discord" >> "$ENV_FILE"
            [ "$MATRIX_ENABLE_POSTING" = "True" ] && echo "SECRETS_AWS_MATRIX_SECRET_NAME=$AWS_SECRET_PREFIX/matrix" >> "$ENV_FILE"
            [ "$LLM_ENABLE" = "True" ] && echo "SECRETS_AWS_LLM_SECRET_NAME=$AWS_SECRET_PREFIX/llm" >> "$ENV_FILE"
            echo "" >> "$ENV_FILE"
            ;;
        vault)
            cat >> "$ENV_FILE" << EOF
# HashiCorp Vault Configuration
SECRETS_SECRET_MANAGER=vault
SECRETS_VAULT_URL=$VAULT_URL_CONFIG
SECRETS_VAULT_TOKEN=$VAULT_TOKEN_VALUE

# Secret paths (auto-configured)
EOF
            [ "$TWITCH_ENABLE" = "True" ] && echo "SECRETS_VAULT_TWITCH_SECRET_PATH=$VAULT_SECRET_PATH/twitch" >> "$ENV_FILE"
            [ "$YOUTUBE_ENABLE" = "True" ] && echo "SECRETS_VAULT_YOUTUBE_SECRET_PATH=$VAULT_SECRET_PATH/youtube" >> "$ENV_FILE"
            [ "$KICK_ENABLE" = "True" ] && echo "SECRETS_VAULT_KICK_SECRET_PATH=$VAULT_SECRET_PATH/kick" >> "$ENV_FILE"
            [ "$MASTODON_ENABLE_POSTING" = "True" ] && echo "SECRETS_VAULT_MASTODON_SECRET_PATH=$VAULT_SECRET_PATH/mastodon" >> "$ENV_FILE"
            [ "$BLUESKY_ENABLE_POSTING" = "True" ] && echo "SECRETS_VAULT_BLUESKY_SECRET_PATH=$VAULT_SECRET_PATH/bluesky" >> "$ENV_FILE"
            [ "$DISCORD_ENABLE_POSTING" = "True" ] && echo "SECRETS_VAULT_DISCORD_SECRET_PATH=$VAULT_SECRET_PATH/discord" >> "$ENV_FILE"
            [ "$MATRIX_ENABLE_POSTING" = "True" ] && echo "SECRETS_VAULT_MATRIX_SECRET_PATH=$VAULT_SECRET_PATH/matrix" >> "$ENV_FILE"
            [ "$LLM_ENABLE" = "True" ] && echo "SECRETS_VAULT_LLM_SECRET_PATH=$VAULT_SECRET_PATH/llm" >> "$ENV_FILE"
            echo "" >> "$ENV_FILE"
            ;;
    esac
    
    cat >> "$ENV_FILE" << EOF
# ============================================
# Platform Enable/Disable Flags
# ============================================

EOF
    
    # Platform enable flags
    [ "$TWITCH_ENABLE" = "True" ] && echo "TWITCH_ENABLE=True" >> "$ENV_FILE"
    [ "$YOUTUBE_ENABLE" = "True" ] && echo "YOUTUBE_ENABLE=True" >> "$ENV_FILE"
    [ "$KICK_ENABLE" = "True" ] && echo "KICK_ENABLE=True" >> "$ENV_FILE"
    [ "$MASTODON_ENABLE_POSTING" = "True" ] && echo "MASTODON_ENABLE_POSTING=True" >> "$ENV_FILE"
    [ "$BLUESKY_ENABLE_POSTING" = "True" ] && echo "BLUESKY_ENABLE_POSTING=True" >> "$ENV_FILE"
    [ "$DISCORD_ENABLE_POSTING" = "True" ] && echo "DISCORD_ENABLE_POSTING=True" >> "$ENV_FILE"
    [ "$MATRIX_ENABLE_POSTING" = "True" ] && echo "MATRIX_ENABLE_POSTING=True" >> "$ENV_FILE"
    [ "$LLM_ENABLE" = "True" ] && echo "LLM_ENABLE=True" >> "$ENV_FILE"
    
    cat >> "$ENV_FILE" << EOF

# ============================================
# Platform Configuration (NON-SECRET)
# ============================================

EOF
    
    # Twitch config
    if [ "$TWITCH_ENABLE" = "True" ]; then
        cat >> "$ENV_FILE" << EOF
# Twitch
TWITCH_USERNAME=$TWITCH_USERNAME

EOF
    fi
    
    # YouTube config
    if [ "$YOUTUBE_ENABLE" = "True" ]; then
        cat >> "$ENV_FILE" << EOF
# YouTube
EOF
        [ -n "$YOUTUBE_CHANNEL_ID" ] && echo "YOUTUBE_CHANNEL_ID=$YOUTUBE_CHANNEL_ID" >> "$ENV_FILE"
        [ -n "$YOUTUBE_USERNAME" ] && echo "YOUTUBE_USERNAME=$YOUTUBE_USERNAME" >> "$ENV_FILE"
        echo "" >> "$ENV_FILE"
    fi
    
    # Kick config
    if [ "$KICK_ENABLE" = "True" ]; then
        cat >> "$ENV_FILE" << EOF
# Kick
KICK_USERNAME=$KICK_USERNAME

EOF
    fi
    
    # Mastodon config
    if [ "$MASTODON_ENABLE_POSTING" = "True" ]; then
        cat >> "$ENV_FILE" << EOF
# Mastodon
MASTODON_API_BASE_URL=$MASTODON_API_BASE_URL

EOF
    fi
    
    # Bluesky config
    if [ "$BLUESKY_ENABLE_POSTING" = "True" ]; then
        cat >> "$ENV_FILE" << EOF
# Bluesky
BLUESKY_HANDLE=$BLUESKY_HANDLE

EOF
    fi
    
    # Discord config (non-webhook settings)
    if [ "$DISCORD_ENABLE_POSTING" = "True" ]; then
        cat >> "$ENV_FILE" << EOF
# Discord
EOF
        [ -n "$DISCORD_ROLE_MENTION_TWITCH" ] && echo "DISCORD_ROLE_MENTION_TWITCH=$DISCORD_ROLE_MENTION_TWITCH" >> "$ENV_FILE"
        [ -n "$DISCORD_ROLE_MENTION_YOUTUBE" ] && echo "DISCORD_ROLE_MENTION_YOUTUBE=$DISCORD_ROLE_MENTION_YOUTUBE" >> "$ENV_FILE"
        [ -n "$DISCORD_ROLE_MENTION_KICK" ] && echo "DISCORD_ROLE_MENTION_KICK=$DISCORD_ROLE_MENTION_KICK" >> "$ENV_FILE"
        [ "$DISCORD_UPDATE_LIVE_MESSAGE" = "True" ] && echo "DISCORD_UPDATE_LIVE_MESSAGE=True" >> "$ENV_FILE"
        [ -n "$DISCORD_UPDATE_INTERVAL" ] && echo "DISCORD_UPDATE_INTERVAL=$DISCORD_UPDATE_INTERVAL" >> "$ENV_FILE"
        echo "" >> "$ENV_FILE"
    fi
    
    # Matrix config
    if [ "$MATRIX_ENABLE_POSTING" = "True" ]; then
        cat >> "$ENV_FILE" << EOF
# Matrix
MATRIX_HOMESERVER=$MATRIX_HOMESERVER
MATRIX_ROOM_ID=$MATRIX_ROOM_ID
EOF
        [ -n "$MATRIX_USERNAME" ] && echo "MATRIX_USERNAME=$MATRIX_USERNAME" >> "$ENV_FILE"
        echo "" >> "$ENV_FILE"
    fi
    
    # LLM config
    if [ "$LLM_ENABLE" = "True" ]; then
        cat >> "$ENV_FILE" << EOF
# LLM Configuration
LLM_PROVIDER=$LLM_PROVIDER
LLM_GEMINI_MODEL=$LLM_GEMINI_MODEL

EOF
    fi
    
    # Settings
    cat >> "$ENV_FILE" << EOF
# ============================================
# Stream Daemon Settings
# ============================================

SETTINGS_CHECK_INTERVAL=$SETTINGS_CHECK_INTERVAL
SETTINGS_POST_INTERVAL=$SETTINGS_POST_INTERVAL
MESSAGES_LIVE_THREADING_MODE=$MESSAGES_LIVE_THREADING_MODE
MESSAGES_END_THREADING_MODE=$MESSAGES_END_THREADING_MODE
EOF
    
    echo -e "${GREEN}✓${NC} Created .env file: $ENV_FILE"
    echo -e "${CYAN}ℹ${NC}  Configuration stored in .env, secrets in $secrets_manager"
    chmod 600 "$ENV_FILE"
}

# Function to create .env file with EVERYTHING (when .env is chosen as secrets manager)
create_env_file_complete() {
    ENV_FILE="$PROJECT_DIR/.env"
    
    echo "Creating .env file..."
    echo ""
    
    if [ -f "$ENV_FILE" ]; then
        if prompt_yes_no ".env already exists. Overwrite?" "N"; then
            rm "$ENV_FILE"
        else
            echo -e "${YELLOW}Keeping existing .env${NC}"
            return 0
        fi
    fi
    
    cat > "$ENV_FILE" << EOF
# Stream Daemon Configuration
# Generated by create-secrets.sh on $(date)

# ============================================
# Streaming Platforms
# ============================================

EOF
    
    # Twitch
    if [ "$TWITCH_ENABLE" = "True" ]; then
        cat >> "$ENV_FILE" << EOF
# Twitch
TWITCH_ENABLE=True
TWITCH_USERNAME=$TWITCH_USERNAME
TWITCH_CLIENT_ID=$TWITCH_CLIENT_ID
TWITCH_CLIENT_SECRET=$TWITCH_CLIENT_SECRET

EOF
    fi
    
    # YouTube
    if [ "$YOUTUBE_ENABLE" = "True" ]; then
        cat >> "$ENV_FILE" << EOF
# YouTube
YOUTUBE_ENABLE=True
EOF
        [ -n "$YOUTUBE_CHANNEL_ID" ] && echo "YOUTUBE_CHANNEL_ID=$YOUTUBE_CHANNEL_ID" >> "$ENV_FILE"
        [ -n "$YOUTUBE_USERNAME" ] && echo "YOUTUBE_USERNAME=$YOUTUBE_USERNAME" >> "$ENV_FILE"
        cat >> "$ENV_FILE" << EOF
YOUTUBE_API_KEY=$YOUTUBE_API_KEY

EOF
    fi
    
    # Kick
    if [ "$KICK_ENABLE" = "True" ]; then
        cat >> "$ENV_FILE" << EOF
# Kick
KICK_ENABLE=True
KICK_USERNAME=$KICK_USERNAME
EOF
        [ -n "$KICK_CLIENT_ID" ] && echo "KICK_CLIENT_ID=$KICK_CLIENT_ID" >> "$ENV_FILE"
        [ -n "$KICK_CLIENT_SECRET" ] && echo "KICK_CLIENT_SECRET=$KICK_CLIENT_SECRET" >> "$ENV_FILE"
        echo "" >> "$ENV_FILE"
    fi
    
    cat >> "$ENV_FILE" << EOF
# ============================================
# Social Media Platforms
# ============================================

EOF
    
    # Mastodon
    if [ "$MASTODON_ENABLE_POSTING" = "True" ]; then
        cat >> "$ENV_FILE" << EOF
# Mastodon
MASTODON_ENABLE_POSTING=True
MASTODON_API_BASE_URL=$MASTODON_API_BASE_URL
MASTODON_CLIENT_ID=$MASTODON_CLIENT_ID
MASTODON_CLIENT_SECRET=$MASTODON_CLIENT_SECRET
MASTODON_ACCESS_TOKEN=$MASTODON_ACCESS_TOKEN

EOF
    fi
    
    # Bluesky
    if [ "$BLUESKY_ENABLE_POSTING" = "True" ]; then
        cat >> "$ENV_FILE" << EOF
# Bluesky
BLUESKY_ENABLE_POSTING=True
BLUESKY_HANDLE=$BLUESKY_HANDLE
BLUESKY_APP_PASSWORD=$BLUESKY_APP_PASSWORD

EOF
    fi
    
    # Discord
    if [ "$DISCORD_ENABLE_POSTING" = "True" ]; then
        cat >> "$ENV_FILE" << EOF
# Discord
DISCORD_ENABLE_POSTING=True
DISCORD_WEBHOOK_URL=$DISCORD_WEBHOOK_URL
EOF
        [ -n "$DISCORD_WEBHOOK_URL_TWITCH" ] && echo "DISCORD_WEBHOOK_URL_TWITCH=$DISCORD_WEBHOOK_URL_TWITCH" >> "$ENV_FILE"
        [ -n "$DISCORD_WEBHOOK_URL_YOUTUBE" ] && echo "DISCORD_WEBHOOK_URL_YOUTUBE=$DISCORD_WEBHOOK_URL_YOUTUBE" >> "$ENV_FILE"
        [ -n "$DISCORD_WEBHOOK_URL_KICK" ] && echo "DISCORD_WEBHOOK_URL_KICK=$DISCORD_WEBHOOK_URL_KICK" >> "$ENV_FILE"
        [ -n "$DISCORD_ROLE_MENTION_TWITCH" ] && echo "DISCORD_ROLE_MENTION_TWITCH=$DISCORD_ROLE_MENTION_TWITCH" >> "$ENV_FILE"
        [ -n "$DISCORD_ROLE_MENTION_YOUTUBE" ] && echo "DISCORD_ROLE_MENTION_YOUTUBE=$DISCORD_ROLE_MENTION_YOUTUBE" >> "$ENV_FILE"
        [ -n "$DISCORD_ROLE_MENTION_KICK" ] && echo "DISCORD_ROLE_MENTION_KICK=$DISCORD_ROLE_MENTION_KICK" >> "$ENV_FILE"
        [ "$DISCORD_UPDATE_LIVE_MESSAGE" = "True" ] && echo "DISCORD_UPDATE_LIVE_MESSAGE=True" >> "$ENV_FILE"
        [ -n "$DISCORD_UPDATE_INTERVAL" ] && echo "DISCORD_UPDATE_INTERVAL=$DISCORD_UPDATE_INTERVAL" >> "$ENV_FILE"
        echo "" >> "$ENV_FILE"
    fi
    
    # Matrix
    if [ "$MATRIX_ENABLE_POSTING" = "True" ]; then
        cat >> "$ENV_FILE" << EOF
# Matrix
MATRIX_ENABLE_POSTING=True
MATRIX_HOMESERVER=$MATRIX_HOMESERVER
MATRIX_ROOM_ID=$MATRIX_ROOM_ID
EOF
        [ -n "$MATRIX_ACCESS_TOKEN" ] && echo "MATRIX_ACCESS_TOKEN=$MATRIX_ACCESS_TOKEN" >> "$ENV_FILE"
        [ -n "$MATRIX_USERNAME" ] && echo "MATRIX_USERNAME=$MATRIX_USERNAME" >> "$ENV_FILE"
        [ -n "$MATRIX_PASSWORD" ] && echo "MATRIX_PASSWORD=$MATRIX_PASSWORD" >> "$ENV_FILE"
        echo "" >> "$ENV_FILE"
    fi
    
    # LLM
    if [ "$LLM_ENABLE" = "True" ]; then
        cat >> "$ENV_FILE" << EOF
# ============================================
# AI/LLM Configuration
# ============================================

LLM_ENABLE=True
LLM_PROVIDER=$LLM_PROVIDER
LLM_GEMINI_API_KEY=$LLM_GEMINI_API_KEY
LLM_GEMINI_MODEL=$LLM_GEMINI_MODEL

EOF
    fi
    
    # Settings
    cat >> "$ENV_FILE" << EOF
# ============================================
# Settings
# ============================================

SETTINGS_CHECK_INTERVAL=$SETTINGS_CHECK_INTERVAL
SETTINGS_POST_INTERVAL=$SETTINGS_POST_INTERVAL
MESSAGES_LIVE_THREADING_MODE=$MESSAGES_LIVE_THREADING_MODE
MESSAGES_END_THREADING_MODE=$MESSAGES_END_THREADING_MODE
EOF
    
    echo -e "${GREEN}✓${NC} Created .env file: $ENV_FILE"
    echo ""
    echo -e "${YELLOW}⚠ WARNING: .env contains sensitive credentials!${NC}"
    echo "  - Do NOT commit .env to git"
    echo "  - Keep it secure with: chmod 600 .env"
    
    chmod 600 "$ENV_FILE"
}

# Execute based on selected manager
case $MANAGER in
    doppler)
        create_doppler_secrets
        create_env_config_only "doppler"
        ;;
    aws)
        create_aws_secrets
        create_env_config_only "AWS Secrets Manager"
        ;;
    vault)
        create_vault_secrets
        create_env_config_only "HashiCorp Vault"
        ;;
    env)
        create_env_file_complete
        ;;
esac

# Final summary
section_header "Setup Complete!"

case $MANAGER in
    doppler)
        echo -e "${GREEN}✓${NC} Secrets stored in Doppler (project: $DOPPLER_PROJECT_NAME, config: $DOPPLER_CONFIG_NAME)"
        echo -e "${GREEN}✓${NC} Configuration stored in .env"
        echo ""
        echo -e "${CYAN}📝 What was created:${NC}"
        echo "  • Doppler secrets: API keys, tokens, webhooks"
        echo "  • .env file: Platform configs, Doppler connection settings"
        ;;
    aws)
        echo -e "${GREEN}✓${NC} Secrets stored in AWS Secrets Manager (region: $AWS_SECRETS_REGION)"
        echo -e "${GREEN}✓${NC} Configuration stored in .env"
        echo ""
        echo -e "${CYAN}📝 What was created:${NC}"
        echo "  • AWS secrets: API keys, tokens, webhooks"
        echo "  • .env file: Platform configs, AWS connection settings"
        ;;
    vault)
        echo -e "${GREEN}✓${NC} Secrets stored in HashiCorp Vault (path: $VAULT_SECRET_PATH)"
        echo -e "${GREEN}✓${NC} Configuration stored in .env"
        echo ""
        echo -e "${CYAN}📝 What was created:${NC}"
        echo "  • Vault secrets: API keys, tokens, webhooks"
        echo "  • .env file: Platform configs, Vault connection settings"
        ;;
    env)
        echo -e "${GREEN}✓${NC} All configuration and secrets stored in .env"
        echo ""
        echo -e "${CYAN}📝 What was created:${NC}"
        echo "  • .env file: Everything (configs + secrets)"
        echo ""
        echo -e "${YELLOW}⚠  Security Note:${NC}"
        echo "  • .env contains sensitive credentials"
        echo "  • Do NOT commit to git"
        echo "  • Consider migrating to Doppler/AWS/Vault for production"
        ;;
esac

echo ""
echo "Next steps:"
echo ""
echo "1. ${GREEN}Test your configuration:${NC}"
echo "   python3 stream-daemon.py --test"
echo ""
echo "2. ${GREEN}Run Stream Daemon:${NC}"

case $MANAGER in
    doppler)
        echo "   ${CYAN}Option 1:${NC} doppler run --project $DOPPLER_PROJECT_NAME --config $DOPPLER_CONFIG_NAME -- python3 stream-daemon.py"
        if [ -n "$DOPPLER_SERVICE_TOKEN" ]; then
            echo "   ${CYAN}Option 2:${NC} python3 stream-daemon.py (uses DOPPLER_TOKEN from .env)"
        fi
        ;;
    aws|vault|env)
        echo "   python3 stream-daemon.py"
        ;;
esac

echo ""
echo "3. ${GREEN}Install as systemd service:${NC}"
echo "   sudo ./install-systemd.sh"
echo ""

echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Happy streaming! 🎥${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""
