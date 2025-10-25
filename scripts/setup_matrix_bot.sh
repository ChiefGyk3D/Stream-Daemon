#!/bin/bash
#
# Matrix Bot Setup Helper
# Interactively configure Matrix bot credentials in Doppler
#

set -e

echo "=============================================="
echo "  Matrix Bot Setup for Stream Daemon"
echo "=============================================="
echo ""

# Check if doppler is installed
if ! command -v doppler &> /dev/null; then
    echo "❌ Error: Doppler CLI not installed"
    echo "   Install: https://docs.doppler.com/docs/install-cli"
    exit 1
fi

# Check if we're in a doppler project
if ! doppler secrets get SECRETS_MANAGER_ENABLED &> /dev/null; then
    echo "❌ Error: Not in a Doppler project or not logged in"
    echo "   Run: doppler login"
    echo "   Then: doppler setup"
    exit 1
fi

echo "✓ Doppler CLI ready"
echo ""

# Get homeserver
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 1: Homeserver URL"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Enter your Matrix homeserver URL"
read -p "Homeserver [https://matrix.org]: " homeserver
homeserver=${homeserver:-https://matrix.org}

# Verify homeserver is accessible
echo "Testing connection to $homeserver..."
if curl -s "$homeserver/_matrix/client/versions" | grep -q "versions"; then
    echo "✓ Homeserver is accessible"
else
    echo "⚠ Warning: Could not verify homeserver connection"
    read -p "Continue anyway? (y/N): " continue
    if [[ ! $continue =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi
fi
echo ""

# Get bot username
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 2: Bot Username"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Enter your bot's Matrix username (full format)"
echo "Example: @streambot:matrix.org"
read -p "Username: " username

if [[ ! $username =~ ^@[a-z0-9._=-]+:.+ ]]; then
    echo "⚠ Warning: Username should start with @ and include :domain"
    echo "   Example: @streambot:matrix.org"
    read -p "Continue anyway? (y/N): " continue
    if [[ ! $continue =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi
fi
echo ""

# Get bot password
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 3: Bot Password"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
read -sp "Password: " password
echo ""

if [ -z "$password" ]; then
    echo "❌ Error: Password cannot be empty"
    exit 1
fi
echo ""

# Get room ID
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 4: Room ID"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Enter the room ID where notifications will be posted"
echo "Get from: Element → Room Settings → Advanced → Internal Room ID"
echo "Example: !KHzbUMYDd0VnJyFqMXiPyfLipv4DKwn-stVz6RYD1VY:matrix.org"
read -p "Room ID: " room_id

if [[ ! $room_id =~ ^![A-Za-z0-9]+:.+ ]]; then
    echo "⚠ Warning: Room ID should start with ! and include :domain"
    echo "   Example: !abc123xyz:matrix.org"
    read -p "Continue anyway? (y/N): " continue
    if [[ ! $continue =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi
fi
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Configuration Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Homeserver: $homeserver"
echo "Username:   $username"
echo "Password:   ********"
echo "Room ID:    $room_id"
echo ""

read -p "Save these secrets to Doppler? (y/N): " confirm
if [[ ! $confirm =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi
echo ""

# Save to Doppler
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Saving to Doppler..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

doppler secrets set MATRIX_HOMESERVER="$homeserver"
echo "✓ Saved MATRIX_HOMESERVER"

doppler secrets set MATRIX_USERNAME="$username"
echo "✓ Saved MATRIX_USERNAME"

doppler secrets set MATRIX_PASSWORD="$password"
echo "✓ Saved MATRIX_PASSWORD"

doppler secrets set MATRIX_ROOM_ID="$room_id"
echo "✓ Saved MATRIX_ROOM_ID"

echo ""
echo "=============================================="
echo "✅ Matrix bot credentials saved to Doppler!"
echo "=============================================="
echo ""
echo "Next Steps:"
echo "  1. Make sure your bot account exists on the homeserver"
echo "  2. IMPORTANT: Invite the bot to your room:"
echo "     - Open room in Element"
echo "     - Room → Invite → Enter: $username"
echo "  3. Accept the invitation (log into bot account)"
echo "  4. Test the integration:"
echo "     doppler run -- python3 tests/test_matrix.py"
echo ""
echo "Documentation: docs/MATRIX_BOT_SETUP.md"
echo ""
