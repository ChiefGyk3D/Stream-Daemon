#!/usr/bin/env python3
"""
Test Discord webhook and posting using Doppler secrets.
Tests that webhook URL is configured correctly and can post messages.
"""

import os
import sys
import importlib.util
from pathlib import Path
import requests

# Add parent directory to path to import from stream-daemon
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the stream-daemon module using importlib
stream_daemon_path = Path(__file__).parent.parent / "stream-daemon.py"
spec = importlib.util.spec_from_file_location("stream_daemon", stream_daemon_path)
stream_daemon = importlib.util.module_from_spec(spec)
sys.modules["stream_daemon"] = stream_daemon
spec.loader.exec_module(stream_daemon)

from dotenv import load_dotenv

# Load environment
load_dotenv()

def mask_secret(secret: str) -> str:
    """Mask a secret for safe display."""
    if not secret:
        return "NOT_SET"
    if len(secret) <= 50:
        return "***"
    # Show first part of domain, mask the webhook ID
    try:
        if secret.startswith('https://discord.com/api/webhooks/'):
            return f"https://discord.com/api/webhooks/***...***"
        return f"{secret[:20]}...{secret[-10:]}"
    except:
        return "***"

def test_doppler_fetch():
    """Test fetching Discord secrets from Doppler."""
    print("=" * 60)
    print("🔐 TEST: Doppler Secret Fetch (Discord)")
    print("=" * 60)
    
    # Use the imported module
    load_secrets_from_doppler = stream_daemon.load_secrets_from_doppler
    get_secret = stream_daemon.get_secret
    
    # Check if Doppler is configured
    secret_manager = os.getenv('SECRETS_SECRET_MANAGER', 'none').lower()
    doppler_token = os.getenv('DOPPLER_TOKEN')
    secret_name_env = os.getenv('SECRETS_DOPPLER_DISCORD_SECRET_NAME')
    
    print(f"Secret Manager: {secret_manager}")
    print(f"Doppler Token: {mask_secret(doppler_token) if doppler_token else 'NOT_SET'}")
    print(f"Discord Secret Name: {secret_name_env or 'NOT_SET'}")
    print()
    
    if secret_manager != 'doppler':
        print("❌ SECRETS_SECRET_MANAGER is not set to 'doppler'")
        return False
    
    if not doppler_token:
        print("❌ DOPPLER_TOKEN is not set")
        return False
    
    if not secret_name_env:
        print("❌ SECRETS_DOPPLER_DISCORD_SECRET_NAME is not set")
        return False
    
    # Fetch secrets
    print(f"Fetching secrets with prefix: {secret_name_env}")
    secrets = load_secrets_from_doppler(secret_name_env)
    
    if not secrets:
        print("❌ No Discord secrets found in Doppler")
        print("  Expected secret with prefix 'DISCORD_*':")
        print("    - DISCORD_WEBHOOK_URL (or discord_webhook_url)")
        print()
        print("  How to get a Discord webhook URL:")
        print("    1. Go to your Discord server")
        print("    2. Right-click the channel → Edit Channel")
        print("    3. Go to Integrations → Webhooks")
        print("    4. Click 'Create Webhook' or 'New Webhook'")
        print("    5. Copy the Webhook URL")
        print("    6. Add to Doppler as DISCORD_WEBHOOK_URL")
        return False
    
    print(f"✓ Received {len(secrets)} secret(s) from Doppler")
    print(f"  Keys found: {', '.join(secrets.keys())}")
    print()
    
    # Check required keys
    required = ['webhook_url']
    missing = [k for k in required if k not in secrets]
    
    if missing:
        print(f"❌ Missing required secrets: {', '.join(missing)}")
        print(f"   Expected Doppler secret: {secret_name_env}_WEBHOOK_URL")
        return False
    
    # Mask and display
    for key in required:
        print(f"  {key}: {mask_secret(secrets[key])}")
    
    print("✓ All required Discord secrets found")
    return True

def test_discord_webhook_validate():
    """Test Discord webhook URL validation."""
    print()
    print("=" * 60)
    print("🔑 TEST: Discord Webhook Validation")
    print("=" * 60)
    
    # Use the imported module
    get_secret = stream_daemon.get_secret
    
    # Fetch webhook URL
    webhook_url = get_secret('Discord', 'webhook_url',
                             secret_name_env='SECRETS_AWS_DISCORD_SECRET_NAME',
                             secret_path_env='SECRETS_VAULT_DISCORD_SECRET_PATH',
                             doppler_secret_env='SECRETS_DOPPLER_DISCORD_SECRET_NAME')
    
    print(f"Webhook URL: {mask_secret(webhook_url)}")
    print()
    
    if not webhook_url:
        print("❌ DISCORD_WEBHOOK_URL not found")
        print("   Create a webhook in Discord channel settings")
        return False
    
    # Validate URL format
    if not webhook_url.startswith('https://discord.com/api/webhooks/'):
        print("❌ Invalid webhook URL format")
        print(f"   Expected: https://discord.com/api/webhooks/...")
        print(f"   Got: {webhook_url[:30]}...")
        return False
    
    # Try to get webhook info (doesn't post anything)
    try:
        print("Validating webhook (GET request)...")
        response = requests.get(webhook_url, timeout=10)
        
        if response.status_code == 200:
            webhook_info = response.json()
            print()
            print("✓ Webhook validation successful!")
            print(f"  Webhook ID: {webhook_info.get('id', 'unknown')}")
            print(f"  Webhook Name: {webhook_info.get('name', 'unknown')}")
            print(f"  Channel ID: {webhook_info.get('channel_id', 'unknown')}")
            print(f"  Guild ID: {webhook_info.get('guild_id', 'unknown')}")
            return True
        else:
            print(f"❌ Webhook validation failed: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Webhook validation failed: {e}")
        print()
        print("Common issues:")
        print("  1. Webhook was deleted in Discord")
        print("  2. Invalid or malformed webhook URL")
        print("  3. Network connectivity issues")
        return False

def test_discord_role_mentions():
    """Test Discord role mention configuration."""
    print()
    print("=" * 60)
    print("🎭 TEST: Discord Role Mentions Configuration")
    print("=" * 60)
    
    platforms = ['TWITCH', 'YOUTUBE', 'KICK']
    configured_roles = {}
    
    for platform in platforms:
        role_id = os.getenv(f'DISCORD_ROLE_{platform}')
        if role_id:
            configured_roles[platform] = role_id
            print(f"✓ {platform}: Role ID {role_id}")
        else:
            print(f"  {platform}: Not configured (optional)")
    
    print()
    if configured_roles:
        print(f"✓ {len(configured_roles)} role mention(s) configured")
        print()
        print("How role mentions work:")
        print(f"  - When a platform goes live, that role will be mentioned")
        print(f"  - Example: Twitch goes live → <@&{list(configured_roles.values())[0]}> message")
    else:
        print("No role mentions configured (optional)")
        print()
        print("To configure role mentions:")
        print("  1. Enable Developer Mode in Discord: Settings → Advanced → Developer Mode")
        print("  2. Right-click a role → Copy Role ID")
        print("  3. Set DISCORD_ROLE_TWITCH=<role_id> in .env")
    
    return True

def test_discord_post():
    """Test posting a message to Discord."""
    print()
    print("=" * 60)
    print("📝 TEST: Discord Test Post")
    print("=" * 60)
    
    # Ask for confirmation
    response = input("Do you want to post a test message to Discord? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Skipping test post")
        return True
    
    # Use the imported module
    get_secret = stream_daemon.get_secret
    
    # Fetch webhook URL
    webhook_url = get_secret('Discord', 'webhook_url',
                             secret_name_env='SECRETS_AWS_DISCORD_SECRET_NAME',
                             secret_path_env='SECRETS_VAULT_DISCORD_SECRET_PATH',
                             doppler_secret_env='SECRETS_DOPPLER_DISCORD_SECRET_NAME')
    
    if not webhook_url:
        print("❌ Missing webhook URL")
        return False
    
    try:
        from datetime import datetime
        test_message = f"🧪 Stream Daemon Test Post - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        print(f"Posting: {test_message}")
        
        data = {"content": test_message}
        response = requests.post(webhook_url, json=data, timeout=10)
        
        if response.status_code == 204:
            print()
            print("✓ Post successful!")
            print("  Check your Discord channel for the test message")
            return True
        else:
            print(f"❌ Post failed: HTTP {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
    except Exception as e:
        print(f"❌ Post failed: {e}")
        return False

def test_discord_role_mention_post():
    """Test posting with role mention."""
    print()
    print("=" * 60)
    print("🎭 TEST: Discord Role Mention Post")
    print("=" * 60)
    
    # Check if any role mentions are configured
    configured_roles = {}
    for platform in ['TWITCH', 'YOUTUBE', 'KICK']:
        role_id = os.getenv(f'DISCORD_ROLE_{platform}')
        if role_id:
            configured_roles[platform] = role_id
    
    if not configured_roles:
        print("No role mentions configured - skipping test")
        print("Set DISCORD_ROLE_TWITCH, DISCORD_ROLE_YOUTUBE, or DISCORD_ROLE_KICK to test")
        return True
    
    # Ask for confirmation
    response = input("Do you want to post a test message with role mention to Discord? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Skipping role mention test")
        return True
    
    # Use the imported module
    get_secret = stream_daemon.get_secret
    
    # Fetch webhook URL
    webhook_url = get_secret('Discord', 'webhook_url',
                             secret_name_env='SECRETS_AWS_DISCORD_SECRET_NAME',
                             secret_path_env='SECRETS_VAULT_DISCORD_SECRET_PATH',
                             doppler_secret_env='SECRETS_DOPPLER_DISCORD_SECRET_NAME')
    
    if not webhook_url:
        print("❌ Missing webhook URL")
        return False
    
    try:
        from datetime import datetime
        # Use the first configured role
        platform = list(configured_roles.keys())[0]
        role_id = configured_roles[platform]
        
        test_message = f"<@&{role_id}> 🧪 Stream Daemon Role Mention Test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        print(f"Posting with role mention for {platform} (Role ID: {role_id})")
        
        data = {"content": test_message}
        response = requests.post(webhook_url, json=data, timeout=10)
        
        if response.status_code == 204:
            print()
            print("✓ Role mention post successful!")
            print("  Check your Discord channel - the role should be mentioned")
            print(f"  Role mentioned: {platform} (ID: {role_id})")
            return True
        else:
            print(f"❌ Post failed: HTTP {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
    except Exception as e:
        print(f"❌ Post failed: {e}")
        return False

def main():
    """Run all Discord tests."""
    print()
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "💬 DISCORD INTEGRATION TEST SUITE" + " " * 14 + "║")
    print("╚" + "═" * 58 + "╝")
    print()
    
    results = {
        "Doppler Fetch": test_doppler_fetch(),
        "Webhook Validation": test_discord_webhook_validate(),
        "Role Mentions Config": test_discord_role_mentions(),
        "Test Post": test_discord_post(),
        "Role Mention Post": test_discord_role_mention_post(),
    }
    
    # Summary
    print()
    print("=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} - {test_name}")
    
    total = len(results)
    passed = sum(results.values())
    print()
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)
    
    return all(results.values())

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
