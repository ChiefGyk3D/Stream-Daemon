#!/usr/bin/env python3
"""
Test Multi-Platform Live Detection

Tests the stream daemon's ability to detect live streams across multiple platforms
and retrieve stream titles correctly.

Test Streamers:
- Kick: asmongold
- Twitch: SweeetTails
- YouTube: @grndpagaming
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

# Import after path is set
import importlib.util
spec = importlib.util.spec_from_file_location("stream_daemon", "stream-daemon.py")
stream_daemon = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stream_daemon)

TwitchPlatform = stream_daemon.TwitchPlatform
YouTubePlatform = stream_daemon.YouTubePlatform
KickPlatform = stream_daemon.KickPlatform

# Load environment variables
load_dotenv()

def test_platform_detection():
    """Test detection of live streams on all platforms."""
    
    print("="*70)
    print("Multi-Platform Live Stream Detection Test")
    print("="*70)
    print()
    
    # Test credentials
    test_streamers = {
        'Kick': 'asmongold',
        'Twitch': 'SweeetTails',
        'YouTube': '@grndpagaming'
    }
    
    print("🎯 Testing Streamers:")
    for platform, username in test_streamers.items():
        print(f"   {platform}: {username}")
    print()
    
    results = {}
    
    # ============================================
    # TEST KICK
    # ============================================
    print("━"*70)
    print("🟢 KICK PLATFORM")
    print("━"*70)
    
    try:
        kick = KickPlatform()
        if kick.authenticate():
            print("✓ Kick authentication successful")
            
            username = test_streamers['Kick']
            print(f"\n🔍 Checking: {username}")
            
            is_live, stream_title = kick.is_live(username)
            
            if is_live:
                print(f"✅ LIVE - Title: {stream_title}")
                results['Kick'] = {'live': True, 'title': stream_title, 'username': username}
            else:
                print(f"⚪ OFFLINE")
                results['Kick'] = {'live': False, 'title': None, 'username': username}
        else:
            print("✗ Kick authentication failed (this is expected if no credentials configured)")
            results['Kick'] = {'live': None, 'title': None, 'username': test_streamers['Kick'], 'error': 'Auth failed'}
    except Exception as e:
        print(f"❌ Error testing Kick: {e}")
        results['Kick'] = {'live': None, 'title': None, 'username': test_streamers['Kick'], 'error': str(e)}
    
    print()
    
    # ============================================
    # TEST TWITCH
    # ============================================
    print("━"*70)
    print("🟣 TWITCH PLATFORM")
    print("━"*70)
    
    try:
        twitch = TwitchPlatform()
        if twitch.authenticate():
            print("✓ Twitch authentication successful")
            
            username = test_streamers['Twitch']
            print(f"\n🔍 Checking: {username}")
            
            is_live, stream_title = twitch.is_live(username)
            
            if is_live:
                print(f"✅ LIVE - Title: {stream_title}")
                results['Twitch'] = {'live': True, 'title': stream_title, 'username': username}
            else:
                print(f"⚪ OFFLINE")
                results['Twitch'] = {'live': False, 'title': None, 'username': username}
        else:
            print("✗ Twitch authentication failed")
            results['Twitch'] = {'live': None, 'title': None, 'username': test_streamers['Twitch'], 'error': 'Auth failed'}
    except Exception as e:
        print(f"❌ Error testing Twitch: {e}")
        results['Twitch'] = {'live': None, 'title': None, 'username': test_streamers['Twitch'], 'error': str(e)}
    
    print()
    
    # ============================================
    # TEST YOUTUBE
    # ============================================
    print("━"*70)
    print("🔴 YOUTUBE PLATFORM")
    print("━"*70)
    
    try:
        youtube = YouTubePlatform()
        if youtube.authenticate():
            print("✓ YouTube authentication successful")
            
            username = test_streamers['YouTube']
            print(f"\n🔍 Checking: {username}")
            
            is_live, stream_title = youtube.is_live(username)
            
            if is_live:
                print(f"✅ LIVE - Title: {stream_title}")
                results['YouTube'] = {'live': True, 'title': stream_title, 'username': username}
            else:
                print(f"⚪ OFFLINE")
                results['YouTube'] = {'live': False, 'title': None, 'username': username}
        else:
            print("✗ YouTube authentication failed")
            results['YouTube'] = {'live': None, 'title': None, 'username': test_streamers['YouTube'], 'error': 'Auth failed'}
    except Exception as e:
        print(f"❌ Error testing YouTube: {e}")
        results['YouTube'] = {'live': None, 'title': None, 'username': test_streamers['YouTube'], 'error': str(e)}
    
    print()
    
    # ============================================
    # SUMMARY
    # ============================================
    print("="*70)
    print("📊 SUMMARY")
    print("="*70)
    print()
    
    live_count = 0
    offline_count = 0
    error_count = 0
    
    for platform, data in results.items():
        status_icon = "❓"
        status_text = "UNKNOWN"
        
        if 'error' in data:
            status_icon = "❌"
            status_text = f"ERROR: {data['error']}"
            error_count += 1
        elif data['live'] is True:
            status_icon = "🔴"
            status_text = "LIVE"
            live_count += 1
        elif data['live'] is False:
            status_icon = "⚪"
            status_text = "OFFLINE"
            offline_count += 1
        
        print(f"{status_icon} {platform:<10} {data['username']:<20} {status_text}")
        if data['title']:
            print(f"   └─ Title: {data['title'][:60]}{'...' if len(data['title']) > 60 else ''}")
    
    print()
    print(f"Live: {live_count} | Offline: {offline_count} | Errors: {error_count}")
    print()
    
    # Test multi-platform posting scenarios
    if live_count > 1:
        print("="*70)
        print("🎮 MULTI-PLATFORM SCENARIO DETECTED")
        print("="*70)
        print()
        print(f"✓ {live_count} platforms are currently live!")
        print()
        print("This is a perfect test case for the multi-platform posting modes:")
        print()
        print("📋 Recommended Configurations:")
        print()
        print("1. SEPARATE MODE (each platform gets its own post):")
        platforms_list = [p for p, d in results.items() if d['live']]
        for platform in platforms_list:
            data = results[platform]
            print(f"   Post: '🔴 LIVE on {platform}! {data['title']}'")
        print()
        
        print("2. THREAD MODE (announcements thread together):")
        for i, platform in enumerate(platforms_list):
            data = results[platform]
            indent = "   " + ("└─ " if i > 0 else "")
            print(f"{indent}Post: '🔴 {'Also live' if i > 0 else 'LIVE'} on {platform}! {data['title']}'")
        print()
        
        print("3. COMBINED MODE (single post):")
        combined_platforms = ', '.join(platforms_list)
        titles = ' | '.join([f"{p}: {results[p]['title']}" for p in platforms_list])
        print(f"   Post: '🔴 LIVE on {combined_platforms}!'")
        print(f"         {titles[:70]}...")
        print()
    
    print("="*70)
    return results

if __name__ == "__main__":
    try:
        results = test_platform_detection()
        
        # Check if any platforms are live
        any_live = any(r.get('live') is True for r in results.values())
        any_errors = any('error' in r for r in results.values())
        
        if any_errors and not any_live:
            print("⚠️  Some errors occurred - check credentials")
            sys.exit(1)
        elif any_live:
            print("✅ Successfully detected live streams!")
            sys.exit(0)
        else:
            print("ℹ️  All streamers are currently offline")
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
