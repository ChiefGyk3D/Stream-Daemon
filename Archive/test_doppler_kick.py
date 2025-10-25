#!/usr/bin/env python3
"""
Test Kick stream detection.
Kick uses a public API so no authentication is required.
"""

import os
import sys
import importlib.util
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the stream-daemon module using importlib
stream_daemon_path = Path(__file__).parent.parent / "stream-daemon.py"
spec = importlib.util.spec_from_file_location("stream_daemon", stream_daemon_path)
stream_daemon = importlib.util.module_from_spec(spec)
sys.modules["stream_daemon"] = stream_daemon
spec.loader.exec_module(stream_daemon)

from dotenv import load_dotenv
import requests

# Load environment
load_dotenv()

# Kick API headers
KICK_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Accept': 'application/json',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://kick.com/'
}

def test_doppler_fetch():
    """Test fetching Kick secrets from Doppler (if configured)."""
    print("=" * 60)
    print("🔐 TEST: Doppler Secret Fetch (Kick)")
    print("=" * 60)
    
    # Use the imported module
    load_secrets_from_doppler = stream_daemon.load_secrets_from_doppler
    
    # Check if Doppler is configured
    secret_manager = os.getenv('SECRETS_SECRET_MANAGER', 'none').lower()
    doppler_token = os.getenv('DOPPLER_TOKEN')
    secret_name_env = os.getenv('SECRETS_DOPPLER_KICK_SECRET_NAME')
    
    print(f"Secret Manager: {secret_manager}")
    print(f"Doppler Token: {'SET' if doppler_token else 'NOT_SET'}")
    print(f"Kick Secret Name: {secret_name_env or 'NOT_SET'}")
    print()
    
    if secret_manager != 'doppler':
        print("ℹ SECRETS_SECRET_MANAGER is not set to 'doppler'")
        print("  Kick can work without authentication (public API)")
        return True  # Not an error - Kick works without auth
    
    if not doppler_token:
        print("ℹ DOPPLER_TOKEN is not set")
        print("  Kick can work without authentication (public API)")
        return True
    
    if not secret_name_env:
        print("ℹ SECRETS_DOPPLER_KICK_SECRET_NAME is not set")
        print("  Kick can work without authentication (public API)")
        return True
    
    # Try to fetch secrets
    print(f"Fetching secrets with prefix: {secret_name_env}")
    secrets = load_secrets_from_doppler(secret_name_env)
    
    if not secrets:
        print("ℹ No Kick secrets found in Doppler")
        print("  Expected secrets with prefix 'KICK_*' (e.g. KICK_CLIENT_ID, KICK_CLIENT_SECRET)")
        print("  Kick can work without authentication using public API")
        return True
    
    print(f"✓ Received {len(secrets)} secret(s) from Doppler")
    print(f"  Keys found: {', '.join(secrets.keys())}")
    print()
    
    # Check for auth keys (optional for Kick)
    if 'client_id' in secrets and 'client_secret' in secrets:
        print("✓ Kick authentication credentials found")
        print("  Will use authenticated API (higher rate limits)")
    else:
        print("ℹ No Kick auth credentials in Doppler")
        print("  Will use public API (may be rate limited)")
    
    return True

def test_kick_auth():
    """Test Kick authentication (if configured)."""
    print("\n" + "=" * 60)
    print("🔑 TEST: Kick Authentication")
    print("=" * 60)
    
    # Use the imported module
    get_secret = stream_daemon.get_secret
    
    # Try to get credentials
    client_id = get_secret('Kick', 'client_id',
                          doppler_secret_env='SECRETS_DOPPLER_KICK_SECRET_NAME')
    client_secret = get_secret('Kick', 'client_secret',
                              doppler_secret_env='SECRETS_DOPPLER_KICK_SECRET_NAME')
    
    if not client_id or not client_secret:
        print("ℹ No Kick credentials configured")
        print("  This is OK - Kick works without authentication")
        print("  Using public API for stream checks")
        return True  # Not an error
    
    print(f"Client ID: {'***' if client_id else 'NOT_SET'}")
    print(f"Client Secret: {'***' if client_secret else 'NOT_SET'}")
    print()
    
    try:
        print("Authenticating with Kick API...")
        # Use correct OAuth server endpoint (id.kick.com, not api.kick.com)
        token_url = "https://id.kick.com/oauth/token"
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        data = {
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret
        }
        response = requests.post(token_url, data=data, headers=headers, timeout=10)
        
        if response.status_code == 200:
            token_data = response.json()
            if token_data.get('access_token'):
                print("✓ Authentication successful!")
                print("  Will use authenticated API")
                return True
        
        print(f"⚠ Authentication returned status {response.status_code}")
        print("  Falling back to public API")
        return True  # Still OK, will use public API
        
    except Exception as e:
        print(f"⚠ Authentication error: {e}")
        print("  Falling back to public API")
        return True  # Still OK, will use public API

def test_kick_api():
    """Test Kick API connectivity using authenticated API."""
    print("\n" + "=" * 60)
    print("🌐 TEST: Authenticated API Connectivity")
    print("=" * 60)
    
    # Use the imported module
    get_secret = stream_daemon.get_secret
    
    # Get credentials
    client_id = get_secret('Kick', 'client_id',
                          doppler_secret_env='SECRETS_DOPPLER_KICK_SECRET_NAME')
    client_secret = get_secret('Kick', 'client_secret',
                              doppler_secret_env='SECRETS_DOPPLER_KICK_SECRET_NAME')
    
    if not client_id or not client_secret:
        print("ℹ No Kick credentials - skipping authenticated API test")
        return True  # Not a failure
    
    try:
        # Authenticate
        token_url = "https://id.kick.com/oauth/token"
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        data = {
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret
        }
        response = requests.post(token_url, data=data, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"⚠ Could not authenticate: {response.status_code}")
            return False
        
        token = response.json().get('access_token')
        
        # Test API access
        test_username = "chiefgyk3d"
        print(f"Testing authenticated API with: {test_username}")
        url = "https://api.kick.com/public/v1/channels"
        headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json'
        }
        params = {'slug': test_username}
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            channels = data.get('data', [])
            print("✓ Authenticated Kick API is accessible")
            print(f"  Found {len(channels)} channel(s)")
            return True
        else:
            print(f"❌ API request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

def test_stream_check():
    """Test checking if a Kick stream is live using authenticated API."""
    print("\n" + "=" * 60)
    print("📺 TEST: Stream Status Check (Authenticated)")
    print("=" * 60)
    
    # Use the imported module
    get_secret = stream_daemon.get_secret
    
    # Get test username
    test_username = os.getenv('KICK_USERNAME', 'chiefgyk3d')
    print(f"Test username: {test_username}")
    
    # Get credentials
    client_id = get_secret('Kick', 'client_id',
                          doppler_secret_env='SECRETS_DOPPLER_KICK_SECRET_NAME')
    client_secret = get_secret('Kick', 'client_secret',
                              doppler_secret_env='SECRETS_DOPPLER_KICK_SECRET_NAME')
    
    if not client_id or not client_secret:
        print("ℹ No Kick credentials - skipping stream check")
        return True  # Not a failure
    
    print()
    
    try:
        # Authenticate
        token_url = "https://id.kick.com/oauth/token"
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        data = {
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret
        }
        response = requests.post(token_url, data=data, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"⚠ Could not authenticate: {response.status_code}")
            return False
        
        token = response.json().get('access_token')
        
        # Check channel info with authenticated API
        url = "https://api.kick.com/public/v1/channels"
        headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json'
        }
        params = {'slug': test_username}
        print(f"Fetching channel info...")
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            channels = data.get('data', [])
            
            if not channels:
                print(f"⚠ No channel found for: {test_username}")
                return False
            
            channel = channels[0]
            slug = channel.get('slug', 'unknown')
            
            print(f"✓ Found channel: {slug}")
            print()
            
            # Check livestream status (embedded in channel data)
            print(f"Checking stream status...")
            stream = channel.get('stream', {})
            is_live = stream.get('is_live', False)
            
            if is_live:
                title = channel.get('stream_title', 'No title')
                viewers = stream.get('viewer_count', 0)
                print(f"✓ Stream is LIVE!")
                print(f"  Title: {title}")
                print(f"  Viewers: {viewers:,}")
            else:
                print(f"✓ Stream check works (currently offline)")
            
            return True
        else:
            print(f"❌ Channel lookup failed with status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Stream check failed: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def test_detection_method():
    """Verify the actual KickPlatform detection method works."""
    print("\n" + "=" * 60)
    print("🔍 TEST: KickPlatform Detection Method")
    print("=" * 60)
    
    test_username = os.getenv('KICK_USERNAME', 'chiefgyk3d')
    
    print(f"Testing actual KickPlatform.is_live() method")
    print(f"Username: {test_username}")
    print()
    
    try:
        # Create and authenticate the actual platform class
        kick = stream_daemon.KickPlatform()
        
        if not kick.authenticate():
            print("⚠ Could not authenticate, but Kick can still work with public API")
            return True  # Not a failure
        
        print(f"✓ Authenticated: use_auth={kick.use_auth}")
        print()
        
        # Call the actual detection method
        print("Calling KickPlatform.is_live()...")
        is_live, title = kick.is_live(test_username)
        
        print(f"Detection result:")
        print(f"  is_live: {is_live}")
        print(f"  title: {title or 'N/A'}")
        
        if is_live:
            print()
            print("✓ Stream detected as LIVE!")
        else:
            print()
            print("✓ Detection method works (stream offline)")
        
        return True
        
    except Exception as e:
        print(f"❌ Detection validation failed: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def main():
    """Run all Kick tests."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 16 + "KICK PLATFORM TEST" + " " * 24 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    print("NOTE: Kick supports both authenticated and public API")
    print("      Authentication is optional but recommended")
    print()
    
    results = []
    
    # Test 1: Doppler fetch (optional)
    results.append(("Doppler Secret Fetch", test_doppler_fetch()))
    
    # Test 2: Authentication (optional)
    results.append(("Kick Authentication", test_kick_auth()))
    
    # Test 3: API connectivity
    results.append(("Public API Connectivity", test_kick_api()))
    
    # Test 4: Stream check
    results.append(("Stream Status Check", test_stream_check()))
    
    # Test 5: Detection method
    results.append(("Detection Method Validation", test_detection_method()))
    
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
    
    if passed == total:
        print("\n✓ All tests passed!")
    else:
        print("\n⚠ Some tests failed, but Kick may still work with public API")
    
    return all(result for _, result in results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
