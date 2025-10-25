#!/usr/bin/env python3
"""
Test AI Message Generation
Tests Google Gemini LLM integration for generating stream announcements.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import importlib.util

# Load the stream daemon module
spec = importlib.util.spec_from_file_location('stream_daemon', 'stream-daemon.py')
stream_daemon = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stream_daemon)


def test_llm_authentication():
    """Test Google Gemini API authentication"""
    print("\n" + "="*60)
    print("Testing Google Gemini LLM Authentication")
    print("="*60)
    
    ai = stream_daemon.AIMessageGenerator()
    if ai.authenticate():
        print(f"✅ Gemini API authenticated (model: {ai.model})")
        return True
    else:
        print("❌ Gemini API authentication failed")
        return False


def test_llm_message_generation():
    """Test AI message generation with sample data"""
    print("\n" + "="*60)
    print("Testing AI Message Generation")
    print("="*60)
    
    ai = stream_daemon.AIMessageGenerator()
    if not ai.authenticate():
        print("❌ Cannot test - authentication failed")
        return False
    
    # Test data
    test_streams = [
        {
            'platform': 'Twitch',
            'username': 'TestStreamer',
            'title': 'Epic Gaming Session - Come Join the Fun!',
            'url': 'https://twitch.tv/teststreamer'
        },
        {
            'platform': 'YouTube',
            'username': 'ContentCreator',
            'title': 'LIVE: Building Amazing Projects',
            'url': 'https://youtube.com/watch?v=test123'
        },
        {
            'platform': 'Kick',
            'username': 'KickStreamer',
            'title': 'Chill Vibes and Good Times',
            'url': 'https://kick.com/kickstreamer'
        }
    ]
    
    all_passed = True
    
    for stream in test_streams:
        print(f"\n--- Testing {stream['platform']} ---")
        print(f"Title: {stream['title']}")
        
        # Test Bluesky (300 char limit)
        bluesky_msg = ai.generate_stream_start_message(
            platform_name=stream['platform'],
            username=stream['username'],
            title=stream['title'],
            url=stream['url'],
            social_platform='bluesky'
        )
        
        if bluesky_msg:
            print(f"\n📱 Bluesky ({len(bluesky_msg)}/300 chars):")
            print(bluesky_msg)
            
            if len(bluesky_msg) > 300:
                print(f"❌ FAIL: Message exceeds 300 character limit!")
                all_passed = False
            else:
                print(f"✅ Within character limit")
        else:
            print("❌ FAIL: No Bluesky message generated")
            all_passed = False
        
        # Test Mastodon (500 char limit)
        mastodon_msg = ai.generate_stream_start_message(
            platform_name=stream['platform'],
            username=stream['username'],
            title=stream['title'],
            url=stream['url'],
            social_platform='mastodon'
        )
        
        if mastodon_msg:
            print(f"\n🐘 Mastodon ({len(mastodon_msg)}/500 chars):")
            print(mastodon_msg)
            
            if len(mastodon_msg) > 500:
                print(f"❌ FAIL: Message exceeds 500 character limit!")
                all_passed = False
            else:
                print(f"✅ Within character limit")
        else:
            print("❌ FAIL: No Mastodon message generated")
            all_passed = False
    
    return all_passed


def run_all_llm_tests():
    """Run all LLM tests"""
    print("\n" + "="*60)
    print("🤖 AI MESSAGE GENERATION TESTS")
    print("="*60)
    
    results = {}
    
    results['llm_auth'] = test_llm_authentication()
    results['llm_generation'] = test_llm_message_generation()
    
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
    success = run_all_llm_tests()
    sys.exit(0 if success else 1)
