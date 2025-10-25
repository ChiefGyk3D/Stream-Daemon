#!/usr/bin/env python3
"""
Test Mastodon authentication and posting using Doppler secrets.
Tests that credentials are loaded correctly and can authenticate with Mastodon API.
"""

import os
import sys
import importlib.util
from pathlib import Path

# Add parent directory to path to import from stream-daemon
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the stream-daemon module using importlib
stream_daemon_path = Path(__file__).parent.parent / "stream-daemon.py"
spec = importlib.util.spec_from_file_location("stream_daemon", stream_daemon_path)
stream_daemon = importlib.util.module_from_spec(spec)
sys.modules["stream_daemon"] = stream_daemon
spec.loader.exec_module(stream_daemon)

from dotenv import load_dotenv
from mastodon import Mastodon

# Load environment
load_dotenv()

def mask_secret(secret: str) -> str:
    """Mask a secret for safe display."""
    if not secret:
        return "NOT_SET"
    if len(secret) <= 8:
        return "***"
    return f"{secret[:4]}...{secret[-4:]}"

def test_doppler_fetch():
    """Test fetching Mastodon secrets from Doppler."""
    print("=" * 60)
    print("🔐 TEST: Doppler Secret Fetch (Mastodon)")
    print("=" * 60)
    
    # Use the imported module
    load_secrets_from_doppler = stream_daemon.load_secrets_from_doppler
    get_secret = stream_daemon.get_secret
    
    # Check if Doppler is configured
    secret_manager = os.getenv('SECRETS_SECRET_MANAGER', 'none').lower()
    doppler_token = os.getenv('DOPPLER_TOKEN')
    secret_name_env = os.getenv('SECRETS_DOPPLER_MASTODON_SECRET_NAME')
    
    print(f"Secret Manager: {secret_manager}")
    print(f"Doppler Token: {mask_secret(doppler_token)}")
    print(f"Mastodon Secret Name: {secret_name_env or 'NOT_SET'}")
    print()
    
    if secret_manager != 'doppler':
        print("❌ SECRETS_SECRET_MANAGER is not set to 'doppler'")
        return False
    
    if not doppler_token:
        print("❌ DOPPLER_TOKEN is not set")
        return False
    
    if not secret_name_env:
        print("❌ SECRETS_DOPPLER_MASTODON_SECRET_NAME is not set")
        return False
    
    # Fetch secrets
    print(f"Fetching secrets with prefix: {secret_name_env}")
    secrets = load_secrets_from_doppler(secret_name_env)
    
    if not secrets:
        print("❌ No Mastodon secrets found in Doppler")
        print("  Expected secrets with prefix 'MASTODON_*':")
        print("    - MASTODON_CLIENT_ID (or mastodon_client_id)")
        print("    - MASTODON_CLIENT_SECRET (or mastodon_client_secret)")
        print("    - MASTODON_ACCESS_TOKEN (or mastodon_access_token)")
        print("  Add these secrets to your Doppler project to enable Mastodon integration")
        return False
    
    print(f"✓ Received {len(secrets)} secret(s) from Doppler")
    print(f"  Keys found: {', '.join(secrets.keys())}")
    print()
    
    # Check required keys
    required = ['client_id', 'client_secret', 'access_token']
    missing = [k for k in required if k not in secrets]
    
    if missing:
        print(f"❌ Missing required secrets: {', '.join(missing)}")
        print(f"   Expected Doppler secrets:")
        for key in missing:
            print(f"     - {secret_name_env}_{key.upper()}")
        return False
    
    # Mask and display
    for key in required:
        print(f"  {key}: {mask_secret(secrets[key])}")
    
    print("✓ All required Mastodon secrets found")
    return True

def test_mastodon_auth():
    """Test Mastodon authentication."""
    print()
    print("=" * 60)
    print("🔑 TEST: Mastodon Authentication")
    print("=" * 60)
    
    # Use the imported module
    get_secret = stream_daemon.get_secret
    get_config = stream_daemon.get_config
    
    # Fetch credentials
    client_id = get_secret('Mastodon', 'client_id',
                          secret_name_env='SECRETS_AWS_MASTODON_SECRET_NAME',
                          secret_path_env='SECRETS_VAULT_MASTODON_SECRET_PATH',
                          doppler_secret_env='SECRETS_DOPPLER_MASTODON_SECRET_NAME')
    client_secret = get_secret('Mastodon', 'client_secret',
                               secret_name_env='SECRETS_AWS_MASTODON_SECRET_NAME',
                               secret_path_env='SECRETS_VAULT_MASTODON_SECRET_PATH',
                               doppler_secret_env='SECRETS_DOPPLER_MASTODON_SECRET_NAME')
    access_token = get_secret('Mastodon', 'access_token',
                              secret_name_env='SECRETS_AWS_MASTODON_SECRET_NAME',
                              secret_path_env='SECRETS_VAULT_MASTODON_SECRET_PATH',
                              doppler_secret_env='SECRETS_DOPPLER_MASTODON_SECRET_NAME')
    api_base_url = get_config('Mastodon', 'api_base_url')
    
    print(f"API Base URL: {api_base_url or 'NOT_SET'}")
    print(f"Client ID: {mask_secret(client_id)}")
    print(f"Client Secret: {mask_secret(client_secret)}")
    print(f"Access Token: {mask_secret(access_token)}")
    print()
    
    if not all([client_id, client_secret, access_token, api_base_url]):
        print("❌ Missing required credentials:")
        if not client_id:
            print("  - Client ID")
        if not client_secret:
            print("  - Client Secret")
        if not access_token:
            print("  - Access Token")
        if not api_base_url:
            print("  - API Base URL (set MASTODON_API_BASE_URL)")
        return False
    
    try:
        print("Creating Mastodon client...")
        mastodon = Mastodon(
            client_id=client_id,
            client_secret=client_secret,
            access_token=access_token,
            api_base_url=api_base_url
        )
        
        print("Verifying credentials...")
        account = mastodon.account_verify_credentials()
        
        print()
        print("✓ Authentication successful!")
        print(f"  Account: @{account['username']}")
        print(f"  Display Name: {account['display_name']}")
        print(f"  Instance: {api_base_url}")
        print(f"  Followers: {account['followers_count']}")
        print(f"  Following: {account['following_count']}")
        print(f"  Posts: {account['statuses_count']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        print()
        print("Common issues:")
        print("  1. Invalid credentials - regenerate in Mastodon Settings → Development")
        print("  2. Wrong API base URL - should be https://your.instance (e.g., https://mastodon.social)")
        print("  3. Application deleted in Mastodon settings")
        print("  4. Missing 'write:statuses' permission")
        return False

def test_mastodon_post():
    """Test posting a test status to Mastodon."""
    print()
    print("=" * 60)
    print("📝 TEST: Mastodon Test Post")
    print("=" * 60)
    
    # Ask for confirmation
    response = input("Do you want to post a test status to Mastodon? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Skipping test post")
        return True
    
    # Use the imported module
    get_secret = stream_daemon.get_secret
    get_config = stream_daemon.get_config
    
    # Fetch credentials
    client_id = get_secret('Mastodon', 'client_id',
                          secret_name_env='SECRETS_AWS_MASTODON_SECRET_NAME',
                          secret_path_env='SECRETS_VAULT_MASTODON_SECRET_PATH',
                          doppler_secret_env='SECRETS_DOPPLER_MASTODON_SECRET_NAME')
    client_secret = get_secret('Mastodon', 'client_secret',
                               secret_name_env='SECRETS_AWS_MASTODON_SECRET_NAME',
                               secret_path_env='SECRETS_VAULT_MASTODON_SECRET_PATH',
                               doppler_secret_env='SECRETS_DOPPLER_MASTODON_SECRET_NAME')
    access_token = get_secret('Mastodon', 'access_token',
                              secret_name_env='SECRETS_AWS_MASTODON_SECRET_NAME',
                              secret_path_env='SECRETS_VAULT_MASTODON_SECRET_PATH',
                              doppler_secret_env='SECRETS_DOPPLER_MASTODON_SECRET_NAME')
    api_base_url = get_config('Mastodon', 'api_base_url')
    
    if not all([client_id, client_secret, access_token, api_base_url]):
        print("❌ Missing credentials")
        return False
    
    try:
        mastodon = Mastodon(
            client_id=client_id,
            client_secret=client_secret,
            access_token=access_token,
            api_base_url=api_base_url
        )
        
        from datetime import datetime
        test_message = f"🧪 Stream Daemon Test Post - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        print(f"Posting: {test_message}")
        status = mastodon.status_post(test_message)
        
        print()
        print("✓ Post successful!")
        print(f"  Status ID: {status['id']}")
        print(f"  URL: {status['url']}")
        print(f"  Created: {status['created_at']}")
        
        # Ask if user wants to delete the test post
        delete = input("\nDelete test post? (yes/no): ")
        if delete.lower() in ['yes', 'y']:
            mastodon.status_delete(status['id'])
            print("✓ Test post deleted")
        
        return True
        
    except Exception as e:
        print(f"❌ Post failed: {e}")
        return False

def test_mastodon_threading():
    """Test Mastodon thread posting (reply functionality)."""
    print()
    print("=" * 60)
    print("🧵 TEST: Mastodon Threading (Replies)")
    print("=" * 60)
    
    # Ask for confirmation
    response = input("Do you want to test thread posting on Mastodon? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Skipping thread test")
        return True
    
    # Use the imported module
    get_secret = stream_daemon.get_secret
    get_config = stream_daemon.get_config
    
    # Fetch credentials
    client_id = get_secret('Mastodon', 'client_id',
                          secret_name_env='SECRETS_AWS_MASTODON_SECRET_NAME',
                          secret_path_env='SECRETS_VAULT_MASTODON_SECRET_PATH',
                          doppler_secret_env='SECRETS_DOPPLER_MASTODON_SECRET_NAME')
    client_secret = get_secret('Mastodon', 'client_secret',
                               secret_name_env='SECRETS_AWS_MASTODON_SECRET_NAME',
                               secret_path_env='SECRETS_VAULT_MASTODON_SECRET_PATH',
                               doppler_secret_env='SECRETS_DOPPLER_MASTODON_SECRET_NAME')
    access_token = get_secret('Mastodon', 'access_token',
                              secret_name_env='SECRETS_AWS_MASTODON_SECRET_NAME',
                              secret_path_env='SECRETS_VAULT_MASTODON_SECRET_PATH',
                              doppler_secret_env='SECRETS_DOPPLER_MASTODON_SECRET_NAME')
    api_base_url = get_config('Mastodon', 'api_base_url')
    
    if not all([client_id, client_secret, access_token, api_base_url]):
        print("❌ Missing credentials")
        return False
    
    try:
        mastodon = Mastodon(
            client_id=client_id,
            client_secret=client_secret,
            access_token=access_token,
            api_base_url=api_base_url
        )
        
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Post parent status
        parent_message = f"🧪 Stream Daemon Thread Test - {timestamp}"
        print(f"Posting parent: {parent_message}")
        parent_status = mastodon.status_post(parent_message)
        print(f"✓ Parent posted (ID: {parent_status['id']})")
        
        # Post reply
        reply_message = "🧵 This is a threaded reply - Stream Daemon supports threading!"
        print(f"Posting reply: {reply_message}")
        reply_status = mastodon.status_post(reply_message, in_reply_to_id=parent_status['id'])
        print(f"✓ Reply posted (ID: {reply_status['id']})")
        
        print()
        print("✓ Thread test successful!")
        print(f"  Parent URL: {parent_status['url']}")
        print(f"  Reply URL: {reply_status['url']}")
        
        # Ask if user wants to delete the test thread
        delete = input("\nDelete test thread? (yes/no): ")
        if delete.lower() in ['yes', 'y']:
            mastodon.status_delete(reply_status['id'])
            mastodon.status_delete(parent_status['id'])
            print("✓ Test thread deleted")
        
        return True
        
    except Exception as e:
        print(f"❌ Thread test failed: {e}")
        return False

def main():
    """Run all Mastodon tests."""
    print()
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "🐘 MASTODON INTEGRATION TEST SUITE" + " " * 13 + "║")
    print("╚" + "═" * 58 + "╝")
    print()
    
    results = {
        "Doppler Fetch": test_doppler_fetch(),
        "Authentication": test_mastodon_auth(),
        "Test Post": test_mastodon_post(),
        "Threading": test_mastodon_threading(),
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
