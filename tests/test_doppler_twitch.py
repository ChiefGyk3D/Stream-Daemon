#!/usr/bin/env python3
"""
Test Twitch authentication and stream detection using Doppler secrets.
Tests that credentials are loaded correctly and can authenticate with Twitch API.
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
from twitchAPI.twitch import Twitch

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
    """Test fetching Twitch secrets from Doppler."""
    print("=" * 60)
    print("🔐 TEST: Doppler Secret Fetch (Twitch)")
    print("=" * 60)
    
    # Use the imported module
    load_secrets_from_doppler = stream_daemon.load_secrets_from_doppler
    get_secret = stream_daemon.get_secret
    
    # Check if Doppler is configured
    secret_manager = os.getenv('SECRETS_SECRET_MANAGER', 'none').lower()
    doppler_token = os.getenv('DOPPLER_TOKEN')
    secret_name_env = os.getenv('SECRETS_DOPPLER_TWITCH_SECRET_NAME')
    
    print(f"Secret Manager: {secret_manager}")
    print(f"Doppler Token: {mask_secret(doppler_token)}")
    print(f"Twitch Secret Name: {secret_name_env or 'NOT_SET'}")
    print()
    
    if secret_manager != 'doppler':
        print("❌ SECRETS_SECRET_MANAGER is not set to 'doppler'")
        return False
    
    if not doppler_token:
        print("❌ DOPPLER_TOKEN is not set")
        return False
    
    if not secret_name_env:
        print("❌ SECRETS_DOPPLER_TWITCH_SECRET_NAME is not set")
        return False
    
    # Fetch secrets
    print(f"Fetching secrets with prefix: {secret_name_env}")
    secrets = load_secrets_from_doppler(secret_name_env)
    
    if not secrets:
        print("❌ No Twitch secrets found in Doppler")
        print("  Expected secrets with prefix 'TWITCH_*' (e.g. TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET)")
        print("  Add these secrets to your Doppler project to enable Twitch integration")
        return False
    
    print(f"✓ Received {len(secrets)} secret(s) from Doppler")
    print(f"  Keys found: {', '.join(secrets.keys())}")
    print()
    
    # Check required keys
    required = ['client_id', 'client_secret']
    missing = [k for k in required if k not in secrets]
    
    if missing:
        print(f"❌ Missing required secrets: {', '.join(missing)}")
        print(f"   Expected Doppler secrets: {secret_name_env}_CLIENT_ID, {secret_name_env}_CLIENT_SECRET")
        return False
    
    # Mask and display
    for key in required:
        print(f"  {key}: {mask_secret(secrets[key])}")
    
    print("✓ All required Twitch secrets found")
    return True

async def test_twitch_auth_async():
    """Test Twitch authentication (async)."""
    # Use the imported module
    get_secret = stream_daemon.get_secret
    
    # Get credentials using the same method as main app
    client_id = get_secret('Twitch', 'client_id',
                          doppler_secret_env='SECRETS_DOPPLER_TWITCH_SECRET_NAME')
    client_secret = get_secret('Twitch', 'client_secret',
                              doppler_secret_env='SECRETS_DOPPLER_TWITCH_SECRET_NAME')
    
    print(f"Client ID: {mask_secret(client_id)}")
    print(f"Client Secret: {mask_secret(client_secret)}")
    print()
    
    if not client_id or not client_secret:
        print("❌ Missing credentials")
        return False
    
    try:
        print("Authenticating with Twitch API...")
        twitch = await Twitch(client_id, client_secret)
        print("✓ Authentication successful!")
        await twitch.close()
        return True
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def test_twitch_auth():
    """Test Twitch authentication."""
    print("\n" + "=" * 60)
    print("🔑 TEST: Twitch Authentication")
    print("=" * 60)
    
    import asyncio
    return asyncio.run(test_twitch_auth_async())

async def test_stream_check_async():
    """Test checking if a stream is live (async)."""
    # Use the imported module
    get_secret = stream_daemon.get_secret
    
    # Get test username
    test_username = os.getenv('TWITCH_USERNAME', 'test')
    print(f"Test username: {test_username}")
    print()
    
    # Authenticate
    client_id = get_secret('Twitch', 'client_id',
                          doppler_secret_env='SECRETS_DOPPLER_TWITCH_SECRET_NAME')
    client_secret = get_secret('Twitch', 'client_secret',
                              doppler_secret_env='SECRETS_DOPPLER_TWITCH_SECRET_NAME')
    
    twitch = None
    try:
        twitch = await Twitch(client_id, client_secret)
        
        # Get user info
        print(f"Looking up user: {test_username}")
        user_generator = twitch.get_users(logins=[test_username])
        users = []
        async for user in user_generator:
            users.append(user)
        
        if not users:
            print(f"⚠ User '{test_username}' not found on Twitch")
            return False
        
        user = users[0]
        user_id = user.id
        display_name = user.display_name
        
        print(f"✓ Found user: {display_name} (ID: {user_id})")
        
        # Check stream status
        print(f"Checking stream status...")
        stream_generator = twitch.get_streams(user_id=[user_id])
        streams = []
        async for stream in stream_generator:
            streams.append(stream)
        
        live_streams = [s for s in streams if s.type == 'live']
        
        if live_streams:
            stream = live_streams[0]
            title = stream.title
            viewer_count = stream.viewer_count
            print(f"✓ Stream is LIVE!")
            print(f"  Title: {title}")
            print(f"  Viewers: {viewer_count}")
        else:
            print(f"✓ Stream check works (currently offline)")
        
        return True
        
    except Exception as e:
        print(f"❌ Stream check failed: {e}")
        import traceback
        print(traceback.format_exc())
        return False
    finally:
        if twitch:
            await twitch.close()

def test_stream_check():
    """Test checking if a stream is live."""
    print("\n" + "=" * 60)
    print("📺 TEST: Stream Status Check")
    print("=" * 60)
    
    import asyncio
    return asyncio.run(test_stream_check_async())

def main():
    """Run all Twitch tests."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "TWITCH PLATFORM TEST" + " " * 23 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    results = []
    
    # Test 1: Doppler fetch
    results.append(("Doppler Secret Fetch", test_doppler_fetch()))
    
    # Test 2: Authentication
    if results[0][1]:  # Only if Doppler fetch succeeded
        results.append(("Twitch Authentication", test_twitch_auth()))
    
    # Test 3: Stream check
    if len(results) > 1 and results[1][1]:  # Only if auth succeeded
        results.append(("Stream Status Check", test_stream_check()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\nResults: {passed}/{total} tests passed")
    print("=" * 60)
    
    return all(result for _, result in results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
