#!/usr/bin/env python3
"""
Quick test script for Threads posting.

Usage:
    doppler run -- python3 test_threads.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stream_daemon.platforms.social.threads import ThreadsPlatform

def main():
    print("=" * 70)
    print("Threads Integration Test")
    print("=" * 70)
    print()
    
    # Initialize Threads platform
    print("1. Initializing Threads platform...")
    threads = ThreadsPlatform()
    
    # Authenticate
    print("2. Authenticating with Threads API...")
    if not threads.authenticate():
        print("\n❌ FAILED: Authentication failed!")
        print("\nPlease check:")
        print("  - THREADS_USER_ID is set in Doppler")
        print("  - THREADS_ACCESS_TOKEN is set in Doppler")
        print("  - THREADS_ENABLE_POSTING=True in Doppler")
        print("  - Access token hasn't expired (60-day limit)")
        return 1
    
    print("✅ Authentication successful!")
    print()
    
    # Test post
    test_message = "🎮 Testing Stream Daemon Threads integration! #StreamDaemon"
    
    print("3. Preparing test post:")
    print(f"   Message: {test_message}")
    print(f"   Length: {len(test_message)}/500 characters")
    print()
    
    print("4. Posting to Threads...")
    post_id = threads.post(test_message)
    
    if post_id:
        print(f"\n✅ SUCCESS! Post published")
        print(f"   Post ID: {post_id}")
        print(f"\n🔗 View your post at:")
        print(f"   https://www.threads.net/t/{post_id}")
        print()
        print("=" * 70)
        return 0
    else:
        print("\n❌ FAILED: Post failed")
        print("\nCheck the error messages above for details.")
        print()
        print("Common issues:")
        print("  - Invalid access token (expired or wrong permissions)")
        print("  - Wrong user ID")
        print("  - Rate limit exceeded (250 posts/24hrs)")
        print()
        print("=" * 70)
        return 1

if __name__ == "__main__":
    sys.exit(main())
