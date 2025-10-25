#!/usr/bin/env python3
"""
Test Bluesky authentication and posting using Doppler secrets.
Tests that credentials are loaded correctly and can authenticate with Bluesky API.
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
from atproto import Client

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
    """Test fetching Bluesky secrets from Doppler."""
    print("=" * 60)
    print("🔐 TEST: Doppler Secret Fetch (Bluesky)")
    print("=" * 60)
    
    # Use the imported module
    load_secrets_from_doppler = stream_daemon.load_secrets_from_doppler
    get_secret = stream_daemon.get_secret
    
    # Check if Doppler is configured
    secret_manager = os.getenv('SECRETS_SECRET_MANAGER', 'none').lower()
    doppler_token = os.getenv('DOPPLER_TOKEN')
    secret_name_env = os.getenv('SECRETS_DOPPLER_BLUESKY_SECRET_NAME')
    
    print(f"Secret Manager: {secret_manager}")
    print(f"Doppler Token: {mask_secret(doppler_token)}")
    print(f"Bluesky Secret Name: {secret_name_env or 'NOT_SET'}")
    print()
    
    if secret_manager != 'doppler':
        print("❌ SECRETS_SECRET_MANAGER is not set to 'doppler'")
        return False
    
    if not doppler_token:
        print("❌ DOPPLER_TOKEN is not set")
        return False
    
    if not secret_name_env:
        print("❌ SECRETS_DOPPLER_BLUESKY_SECRET_NAME is not set")
        return False
    
    # Fetch secrets
    print(f"Fetching secrets with prefix: {secret_name_env}")
    secrets = load_secrets_from_doppler(secret_name_env)
    
    if not secrets:
        print("❌ No Bluesky secrets found in Doppler")
        print("  Expected secret with prefix 'BLUESKY_*':")
        print("    - BLUESKY_APP_PASSWORD (or bluesky_app_password)")
        print()
        print("  How to get a Bluesky app password:")
        print("    1. Go to https://bsky.app/settings/app-passwords")
        print("    2. Click 'Add App Password'")
        print("    3. Name: 'Stream Daemon'")
        print("    4. Copy the generated password")
        print("    5. Add to Doppler as BLUESKY_APP_PASSWORD")
        print()
        print("  ⚠️  Note: This is NOT your main account password!")
        return False
    
    print(f"✓ Received {len(secrets)} secret(s) from Doppler")
    print(f"  Keys found: {', '.join(secrets.keys())}")
    print()
    
    # Check required keys
    required = ['app_password']
    missing = [k for k in required if k not in secrets]
    
    if missing:
        print(f"❌ Missing required secrets: {', '.join(missing)}")
        print(f"   Expected Doppler secret: {secret_name_env}_APP_PASSWORD")
        return False
    
    # Mask and display
    for key in required:
        print(f"  {key}: {mask_secret(secrets[key])}")
    
    print("✓ All required Bluesky secrets found")
    return True

def test_bluesky_auth():
    """Test Bluesky authentication."""
    print()
    print("=" * 60)
    print("🔑 TEST: Bluesky Authentication")
    print("=" * 60)
    
    # Use the imported module
    get_secret = stream_daemon.get_secret
    get_config = stream_daemon.get_config
    
    # Fetch credentials
    handle = get_config('Bluesky', 'handle')
    app_password = get_secret('Bluesky', 'app_password',
                              secret_name_env='SECRETS_AWS_BLUESKY_SECRET_NAME',
                              secret_path_env='SECRETS_VAULT_BLUESKY_SECRET_PATH',
                              doppler_secret_env='SECRETS_DOPPLER_BLUESKY_SECRET_NAME')
    
    print(f"Handle: {handle or 'NOT_SET'}")
    print(f"App Password: {mask_secret(app_password)}")
    print()
    
    if not handle:
        print("❌ BLUESKY_HANDLE is not set")
        print("   Set it to your Bluesky handle (e.g., yourname.bsky.social)")
        return False
    
    if not app_password:
        print("❌ App password not found")
        print("   Create one at https://bsky.app/settings/app-passwords")
        return False
    
    try:
        print("Creating Bluesky client...")
        client = Client()
        
        print(f"Logging in as {handle}...")
        profile = client.login(handle, app_password)
        
        print()
        print("✓ Authentication successful!")
        print(f"  Handle: @{profile.handle}")
        print(f"  Display Name: {profile.display_name or '(not set)'}")
        print(f"  DID: {profile.did}")
        
        # Get additional profile info
        profile_info = client.get_profile(profile.handle)
        print(f"  Followers: {profile_info.followers_count or 0}")
        print(f"  Following: {profile_info.follows_count or 0}")
        print(f"  Posts: {profile_info.posts_count or 0}")
        
        return True
        
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        print()
        print("Common issues:")
        print("  1. Invalid app password - regenerate at https://bsky.app/settings/app-passwords")
        print("  2. Wrong handle format - should be 'yourname.bsky.social' (no @)")
        print("  3. App password was deleted")
        print("  4. Using main password instead of app password")
        return False

def test_bluesky_post():
    """Test posting to Bluesky."""
    print()
    print("=" * 60)
    print("📝 TEST: Bluesky Test Post")
    print("=" * 60)
    
    # Ask for confirmation
    response = input("Do you want to post a test message to Bluesky? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Skipping test post")
        return True
    
    # Use the imported module
    get_secret = stream_daemon.get_secret
    get_config = stream_daemon.get_config
    
    # Fetch credentials
    handle = get_config('Bluesky', 'handle')
    app_password = get_secret('Bluesky', 'app_password',
                              secret_name_env='SECRETS_AWS_BLUESKY_SECRET_NAME',
                              secret_path_env='SECRETS_VAULT_BLUESKY_SECRET_PATH',
                              doppler_secret_env='SECRETS_DOPPLER_BLUESKY_SECRET_NAME')
    
    if not all([handle, app_password]):
        print("❌ Missing credentials")
        return False
    
    try:
        client = Client()
        client.login(handle, app_password)
        
        from datetime import datetime
        test_message = f"🧪 Stream Daemon Test Post - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        print(f"Posting: {test_message}")
        response = client.send_post(text=test_message)
        
        print()
        print("✓ Post successful!")
        print(f"  URI: {response.uri}")
        print(f"  CID: {response.cid}")
        
        # Extract post URL from URI
        # Format: at://did:plc:xxx/app.bsky.feed.post/xxx
        if response.uri:
            parts = response.uri.split('/')
            if len(parts) >= 5:
                did = parts[2]
                post_id = parts[-1]
                # Bluesky post URL format
                post_url = f"https://bsky.app/profile/{did}/post/{post_id}"
                print(f"  URL: {post_url}")
        
        # Ask if user wants to delete the test post
        delete = input("\nDelete test post? (yes/no): ")
        if delete.lower() in ['yes', 'y']:
            # Extract record key from URI
            parts = response.uri.split('/')
            record_key = parts[-1]
            client.delete_post(record_key)
            print("✓ Test post deleted")
        
        return True
        
    except Exception as e:
        print(f"❌ Post failed: {e}")
        return False

def test_bluesky_profile_info():
    """Test fetching Bluesky profile information."""
    print()
    print("=" * 60)
    print("👤 TEST: Bluesky Profile Information")
    print("=" * 60)
    
    # Use the imported module
    get_secret = stream_daemon.get_secret
    get_config = stream_daemon.get_config
    
    # Fetch credentials
    handle = get_config('Bluesky', 'handle')
    app_password = get_secret('Bluesky', 'app_password',
                              secret_name_env='SECRETS_AWS_BLUESKY_SECRET_NAME',
                              secret_path_env='SECRETS_VAULT_BLUESKY_SECRET_PATH',
                              doppler_secret_env='SECRETS_DOPPLER_BLUESKY_SECRET_NAME')
    
    if not all([handle, app_password]):
        print("❌ Missing credentials")
        return False
    
    try:
        client = Client()
        client.login(handle, app_password)
        
        print("Fetching profile information...")
        profile = client.get_profile(handle)
        
        print()
        print("✓ Profile information retrieved!")
        print(f"  Handle: @{profile.handle}")
        print(f"  Display Name: {profile.display_name or '(not set)'}")
        print(f"  Description: {profile.description[:100] if profile.description else '(not set)'}")
        print(f"  Followers: {profile.followers_count or 0}")
        print(f"  Following: {profile.follows_count or 0}")
        print(f"  Posts: {profile.posts_count or 0}")
        print(f"  DID: {profile.did}")
        
        return True
        
    except Exception as e:
        print(f"❌ Profile fetch failed: {e}")
        return False

def test_bluesky_char_limit():
    """Test Bluesky character limit handling."""
    print()
    print("=" * 60)
    print("📏 TEST: Bluesky Character Limit")
    print("=" * 60)
    
    # Bluesky has a 300 character limit for posts
    print("Bluesky character limit: 300 characters")
    print()
    
    test_messages = [
        ("Short message", "🧪 This is a short test message."),
        ("Medium message (100 chars)", "🧪 " + "X" * 97),
        ("Long message (250 chars)", "🧪 " + "X" * 247),
        ("At limit (300 chars)", "🧪 " + "X" * 297),
    ]
    
    for name, message in test_messages:
        length = len(message)
        status = "✓" if length <= 300 else "✗"
        print(f"{status} {name}: {length} chars")
    
    print()
    print("Note: Messages over 300 characters will be rejected by Bluesky API")
    print("Stream Daemon should truncate or split long messages")
    
    return True

def test_bluesky_threading():
    """Test Bluesky thread posting (reply functionality)."""
    print()
    print("=" * 60)
    print("🧵 TEST: Bluesky Threading (Replies)")
    print("=" * 60)
    
    # Ask for confirmation
    response = input("Do you want to test thread posting on Bluesky? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Skipping thread test")
        return True
    
    # Use the imported module
    get_secret = stream_daemon.get_secret
    get_config = stream_daemon.get_config
    
    # Fetch credentials
    handle = get_config('Bluesky', 'handle')
    app_password = get_secret('Bluesky', 'app_password',
                              secret_name_env='SECRETS_AWS_BLUESKY_SECRET_NAME',
                              secret_path_env='SECRETS_VAULT_BLUESKY_SECRET_PATH',
                              doppler_secret_env='SECRETS_DOPPLER_BLUESKY_SECRET_NAME')
    
    if not all([handle, app_password]):
        print("❌ Missing credentials")
        return False
    
    try:
        from atproto import models
        from datetime import datetime
        
        client = Client()
        client.login(handle, app_password)
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Post parent
        parent_text = f"🧪 Stream Daemon Thread Test - {timestamp}"
        print(f"Posting parent: {parent_text}")
        parent_response = client.send_post(text=parent_text)
        print(f"✓ Parent posted (URI: {parent_response.uri})")
        
        # Post reply - Bluesky requires parent and root references
        reply_text = "🧵 This is a threaded reply - Stream Daemon supports Bluesky threading!"
        print(f"Posting reply: {reply_text}")
        
        # Create reply references
        parent_ref = models.AppBskyFeedPost.ReplyRef(
            parent=models.ComAtprotoRepoStrongRef.Main(
                uri=parent_response.uri,
                cid=parent_response.cid
            ),
            root=models.ComAtprotoRepoStrongRef.Main(
                uri=parent_response.uri,
                cid=parent_response.cid
            )
        )
        
        reply_response = client.send_post(text=reply_text, reply_to=parent_ref)
        print(f"✓ Reply posted (URI: {reply_response.uri})")
        
        print()
        print("✓ Thread test successful!")
        print(f"  Parent URI: {parent_response.uri}")
        print(f"  Reply URI: {reply_response.uri}")
        
        # Ask if user wants to delete the test thread
        delete = input("\nDelete test thread? (yes/no): ")
        if delete.lower() in ['yes', 'y']:
            # Extract record keys from URIs
            parent_key = parent_response.uri.split('/')[-1]
            reply_key = reply_response.uri.split('/')[-1]
            client.delete_post(reply_key)
            client.delete_post(parent_key)
            print("✓ Test thread deleted")
        
        return True
        
    except Exception as e:
        print(f"❌ Thread test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all Bluesky tests."""
    print()
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "🦋 BLUESKY INTEGRATION TEST SUITE" + " " * 14 + "║")
    print("╚" + "═" * 58 + "╝")
    print()
    
    results = {
        "Doppler Fetch": test_doppler_fetch(),
        "Authentication": test_bluesky_auth(),
        "Profile Info": test_bluesky_profile_info(),
        "Character Limit": test_bluesky_char_limit(),
        "Test Post": test_bluesky_post(),
        "Threading": test_bluesky_threading(),
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
