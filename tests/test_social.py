#!/usr/bin/env python3
"""
Test Social Media Platform Authentication
Tests authentication to Mastodon, Bluesky, Discord, and Matrix.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import importlib.util

# Load the stream daemon module
spec = importlib.util.spec_from_file_location('stream_daemon', 'stream-daemon.py')
stream_daemon = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stream_daemon)


def test_mastodon_authentication():
    """Test Mastodon authentication"""
    print("\n" + "="*60)
    print("Testing Mastodon Authentication")
    print("="*60)
    
    mastodon = stream_daemon.MastodonPlatform()
    if mastodon.authenticate():
        print("✅ Mastodon authentication successful")
        return True
    else:
        print("❌ Mastodon authentication failed")
        return False


def test_bluesky_authentication():
    """Test Bluesky authentication"""
    print("\n" + "="*60)
    print("Testing Bluesky Authentication")
    print("="*60)
    
    bluesky = stream_daemon.BlueskyPlatform()
    if bluesky.authenticate():
        print("✅ Bluesky authentication successful")
        return True
    else:
        print("❌ Bluesky authentication failed")
        return False


def test_discord_authentication():
    """Test Discord webhook configuration"""
    print("\n" + "="*60)
    print("Testing Discord Webhook Configuration")
    print("="*60)
    
    discord = stream_daemon.DiscordPlatform()
    if discord.authenticate():
        print("✅ Discord webhook configured")
        return True
    else:
        print("❌ Discord webhook configuration failed")
        return False


def test_matrix_authentication():
    """Test Matrix authentication"""
    print("\n" + "="*60)
    print("Testing Matrix Authentication")
    print("="*60)
    
    matrix = stream_daemon.MatrixPlatform()
    if matrix.authenticate():
        print("✅ Matrix authentication successful")
        return True
    else:
        print("❌ Matrix authentication failed")
        return False


def run_all_social_tests():
    """Run all social media authentication tests"""
    print("\n" + "="*60)
    print("📱 SOCIAL MEDIA AUTHENTICATION TESTS")
    print("="*60)
    
    results = {}
    
    results['mastodon'] = test_mastodon_authentication()
    results['bluesky'] = test_bluesky_authentication()
    results['discord'] = test_discord_authentication()
    results['matrix'] = test_matrix_authentication()
    
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
    success = run_all_social_tests()
    sys.exit(0 if success else 1)
