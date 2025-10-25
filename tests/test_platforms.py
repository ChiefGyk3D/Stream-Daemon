#!/usr/bin/env python3
"""
Test Platform API Authentication and Stream Detection
Tests each streaming platform's ability to authenticate and detect live streams.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import importlib.util

# Load the stream daemon module
spec = importlib.util.spec_from_file_location('stream_daemon', 'stream-daemon.py')
stream_daemon = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stream_daemon)


def test_twitch_authentication():
    """Test Twitch API authentication"""
    print("\n" + "="*60)
    print("Testing Twitch Authentication")
    print("="*60)
    
    twitch = stream_daemon.TwitchPlatform()
    if twitch.authenticate():
        print("✅ Twitch authentication successful")
        return True
    else:
        print("❌ Twitch authentication failed")
        return False


def test_twitch_live_detection():
    """Test Twitch live stream detection"""
    print("\n" + "="*60)
    print("Testing Twitch Live Stream Detection")
    print("="*60)
    
    username = os.getenv('TWITCH_USERNAME', 'lilypita')
    print(f"Checking: {username}")
    
    twitch = stream_daemon.TwitchPlatform()
    if not twitch.authenticate():
        print("❌ Cannot test - authentication failed")
        return False
    
    is_live, data = twitch.is_live(username)
    
    if is_live:
        print(f"✅ Stream is LIVE!")
        print(f"   Title: {data.get('title', 'N/A')}")
        print(f"   Game: {data.get('game_name', 'N/A')}")
        print(f"   Viewers: {data.get('viewer_count', 'N/A')}")
        return True
    else:
        print(f"⚪ Stream is offline")
        return True  # Not an error, just offline


def test_youtube_authentication():
    """Test YouTube API authentication"""
    print("\n" + "="*60)
    print("Testing YouTube Authentication")
    print("="*60)
    
    youtube = stream_daemon.YouTubePlatform()
    if youtube.authenticate():
        print("✅ YouTube authentication successful")
        return True
    else:
        print("❌ YouTube authentication failed")
        return False


def test_youtube_live_detection():
    """Test YouTube live stream detection"""
    print("\n" + "="*60)
    print("Testing YouTube Live Stream Detection")
    print("="*60)
    
    username = os.getenv('YOUTUBE_USERNAME', 'Hyphonix')
    print(f"Checking: {username}")
    
    youtube = stream_daemon.YouTubePlatform()
    if not youtube.authenticate():
        print("❌ Cannot test - authentication failed")
        return False
    
    is_live, data = youtube.is_live(username)
    
    if is_live:
        print(f"✅ Stream is LIVE!")
        print(f"   Title: {data.get('title', 'N/A')}")
        print(f"   Video ID: {data.get('video_id', 'N/A')}")
        print(f"   URL: https://youtube.com/watch?v={data.get('video_id', '')}")
        return True
    else:
        print(f"⚪ Stream is offline")
        return True  # Not an error, just offline


def test_kick_authentication():
    """Test Kick API authentication"""
    print("\n" + "="*60)
    print("Testing Kick Authentication")
    print("="*60)
    
    kick = stream_daemon.KickPlatform()
    if kick.authenticate():
        print("✅ Kick authentication successful")
        return True
    else:
        print("❌ Kick authentication failed")
        return False


def test_kick_live_detection():
    """Test Kick live stream detection"""
    print("\n" + "="*60)
    print("Testing Kick Live Stream Detection")
    print("="*60)
    
    username = os.getenv('KICK_USERNAME', 'daletanhardt')
    print(f"Checking: {username}")
    
    kick = stream_daemon.KickPlatform()
    if not kick.authenticate():
        print("❌ Cannot test - authentication failed")
        return False
    
    is_live, data = kick.is_live(username)
    
    if is_live:
        print(f"✅ Stream is LIVE!")
        print(f"   Title: {data.get('title', 'N/A')}")
        print(f"   Category: {data.get('category', 'N/A')}")
        print(f"   URL: https://kick.com/{username}")
        return True
    else:
        print(f"⚪ Stream is offline")
        return True  # Not an error, just offline


def run_all_platform_tests():
    """Run all platform tests"""
    print("\n" + "="*60)
    print("🎬 PLATFORM API TESTS")
    print("="*60)
    
    results = {}
    
    # Twitch tests
    results['twitch_auth'] = test_twitch_authentication()
    results['twitch_live'] = test_twitch_live_detection()
    
    # YouTube tests
    results['youtube_auth'] = test_youtube_authentication()
    results['youtube_live'] = test_youtube_live_detection()
    
    # Kick tests
    results['kick_auth'] = test_kick_authentication()
    results['kick_live'] = test_kick_live_detection()
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    return all(results.values())


if __name__ == "__main__":
    success = run_all_platform_tests()
    sys.exit(0 if success else 1)
