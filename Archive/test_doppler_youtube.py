#!/usr/bin/env python3
"""
Test YouTube authentication and stream detection using Doppler secrets.
Tests that credentials are loaded correctly and can authenticate with YouTube API.
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
from googleapiclient.discovery import build

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
    """Test fetching YouTube secrets from Doppler."""
    print("=" * 60)
    print("🔐 TEST: Doppler Secret Fetch (YouTube)")
    print("=" * 60)
    
    # Use the imported module
    load_secrets_from_doppler = stream_daemon.load_secrets_from_doppler
    
    # Check if Doppler is configured
    secret_manager = os.getenv('SECRETS_SECRET_MANAGER', 'none').lower()
    doppler_token = os.getenv('DOPPLER_TOKEN')
    secret_name_env = os.getenv('SECRETS_DOPPLER_YOUTUBE_SECRET_NAME')
    
    print(f"Secret Manager: {secret_manager}")
    print(f"Doppler Token: {mask_secret(doppler_token)}")
    print(f"YouTube Secret Name: {secret_name_env or 'NOT_SET'}")
    print()
    
    if secret_manager != 'doppler':
        print("❌ SECRETS_SECRET_MANAGER is not set to 'doppler'")
        return False
    
    if not doppler_token:
        print("❌ DOPPLER_TOKEN is not set")
        return False
    
    if not secret_name_env:
        print("❌ SECRETS_DOPPLER_YOUTUBE_SECRET_NAME is not set")
        return False
    
    # Fetch secrets
    print(f"Fetching secrets with prefix: {secret_name_env}")
    secrets = load_secrets_from_doppler(secret_name_env)
    
    if not secrets:
        print("❌ No YouTube secrets found in Doppler")
        print("  Expected secrets with prefix 'YOUTUBE_*' (e.g. YOUTUBE_API_KEY)")
        print("  Add these secrets to your Doppler project to enable YouTube integration")
        return False
    
    print(f"✓ Received {len(secrets)} secret(s) from Doppler")
    print(f"  Keys found: {', '.join(secrets.keys())}")
    print()
    
    # Check required keys
    required = ['api_key']
    missing = [k for k in required if k not in secrets]
    
    if missing:
        print(f"❌ Missing required secrets: {', '.join(missing)}")
        print(f"   Expected Doppler secret: {secret_name_env}_API_KEY")
        return False
    
    # Mask and display
    for key in required:
        print(f"  {key}: {mask_secret(secrets[key])}")
    
    print("✓ All required YouTube secrets found")
    return True

def test_youtube_auth():
    """Test YouTube authentication."""
    print("\n" + "=" * 60)
    print("🔑 TEST: YouTube Authentication")
    print("=" * 60)
    
    # Use the imported module
    get_secret = stream_daemon.get_secret
    
    # Get credentials using the same method as main app
    api_key = get_secret('YouTube', 'api_key',
                        doppler_secret_env='SECRETS_DOPPLER_YOUTUBE_SECRET_NAME')
    
    print(f"API Key: {mask_secret(api_key)}")
    print()
    
    if not api_key:
        print("❌ Missing API key")
        return False
    
    try:
        print("Creating YouTube API client...")
        youtube = build('youtube', 'v3', developerKey=api_key)
        print("✓ YouTube API client created successfully!")
        return True
    except Exception as e:
        print(f"❌ YouTube client creation failed: {e}")
        return False

def test_stream_check():
    """Test checking if a YouTube stream is live."""
    print("\n" + "=" * 60)
    print("📺 TEST: Stream Status Check")
    print("=" * 60)
    
    # Use the imported module
    get_secret = stream_daemon.get_secret
    get_config = stream_daemon.get_config
    
    # Get test username/handle (required now)
    username = get_config('YouTube', 'username')
    
    if not username:
        print("⚠ YOUTUBE_USERNAME not set, skipping stream check")
        print("  Set YOUTUBE_USERNAME in .env to test stream detection")
        return True  # Don't fail, just skip
    
    print(f"Test username: {username}")
    
    # Optional: Channel ID can skip the lookup step
    channel_id = get_config('YouTube', 'channel_id')
    if channel_id:
        print(f"Channel ID provided: {channel_id}")
    else:
        print(f"No channel ID - will resolve from username")
    print()
    
    # Authenticate
    api_key = get_secret('YouTube', 'api_key',
                        doppler_secret_env='SECRETS_DOPPLER_YOUTUBE_SECRET_NAME')
    
    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        
        # If no channel_id, look it up from username
        if not channel_id:
            print(f"Resolving channel ID from username...")
            if username.startswith('@'):
                request = youtube.channels().list(
                    part="id,snippet",
                    forHandle=username
                )
            else:
                request = youtube.channels().list(
                    part="id,snippet",
                    forUsername=username
                )
            
            response = request.execute()
            if not response.get('items'):
                print(f"❌ Could not find channel for username: {username}")
                return False
            
            channel_id = response['items'][0]['id']
            print(f"✓ Resolved channel ID: {channel_id}")
        
        # Get channel info
        print(f"Looking up channel: {channel_id}")
        channel_request = youtube.channels().list(
            part="snippet,statistics",
            id=channel_id
        )
        channel_response = channel_request.execute()
        
        if not channel_response.get('items'):
            print(f"⚠ Channel '{channel_id}' not found")
            return False
        
        channel = channel_response['items'][0]
        title = channel['snippet']['title']
        subs = channel['statistics'].get('subscriberCount', 'hidden')
        
        print(f"✓ Found channel: {title}")
        print(f"  Subscribers: {subs}")
        print()
        
        # Check for live streams
        print("Checking for live streams...")
        search_request = youtube.search().list(
            part="snippet",
            channelId=channel_id,
            eventType="live",
            type="video",
            maxResults=1
        )
        search_response = search_request.execute()
        
        if search_response.get('items'):
            stream = search_response['items'][0]
            stream_title = stream['snippet']['title']
            print(f"✓ Stream is LIVE!")
            print(f"  Title: {stream_title}")
        else:
            print(f"✓ Stream check works (currently offline)")
        
        return True
        
    except Exception as e:
        print(f"❌ Stream check failed: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def main():
    """Run all YouTube tests."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 14 + "YOUTUBE PLATFORM TEST" + " " * 23 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    results = []
    
    # Test 1: Doppler fetch
    results.append(("Doppler Secret Fetch", test_doppler_fetch()))
    
    # Test 2: Authentication
    if results[0][1]:  # Only if Doppler fetch succeeded
        results.append(("YouTube Authentication", test_youtube_auth()))
    
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
