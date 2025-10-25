#!/usr/bin/env python3
"""
Test Multi-Platform Live Stream Posting

Tests posting live stream announcements to Bluesky and Mastodon
with different threading modes.

Test Streamers:
- Kick: asmongold
- Twitch: SweeetTails  
- YouTube: @grndpagaming
"""

import os
import sys
import random

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
MastodonPlatform = stream_daemon.MastodonPlatform
BlueskyPlatform = stream_daemon.BlueskyPlatform

# Load environment variables
load_dotenv()

def get_config(section: str, key: str, default: str = None) -> str:
    """Get config from environment variables."""
    env_key = f"{section.upper()}_{key.upper()}"
    return os.getenv(env_key, default)

def get_stream_url(platform: str, username: str) -> str:
    """Generate stream URL for a platform."""
    platform = platform.lower()
    
    if platform == 'twitch':
        return f"https://twitch.tv/{username}"
    elif platform == 'youtube':
        # Remove @ if present
        handle = username.lstrip('@')
        return f"https://youtube.com/@{handle}/live"
    elif platform == 'kick':
        return f"https://kick.com/{username}"
    else:
        return ""

def test_live_stream_posting():
    """Test detecting live streams and posting to social platforms."""
    
    print("="*70)
    print("Multi-Platform Live Stream Posting Test")
    print("="*70)
    print()
    
    # Test streamers
    test_streamers = [
        {'platform': 'Kick', 'username': 'daletanhardt', 'platform_obj': KickPlatform()},
        {'platform': 'Twitch', 'username': 'lilypita', 'platform_obj': TwitchPlatform()},
        {'platform': 'YouTube', 'username': '@hyphonix', 'platform_obj': YouTubePlatform()}
    ]
    
    print("🎯 Test Configuration:")
    for streamer in test_streamers:
        print(f"   {streamer['platform']}: {streamer['username']}")
    print()
    print("📋 Testing Modes: SEPARATE and THREAD")
    print()
    
    # ============================================
    # STEP 1: Detect Live Streams
    # ============================================
    print("="*70)
    print("STEP 1: Detecting Live Streams")
    print("="*70)
    print()
    
    live_streams = []
    
    for streamer in test_streamers:
        platform_obj = streamer['platform_obj']
        platform_name = streamer['platform']
        username = streamer['username']
        
        print(f"🔍 Checking {platform_name}/{username}...")
        
        # Authenticate
        if platform_name == 'Kick':
            # Need to enable Kick temporarily
            os.environ['KICK_ENABLE'] = 'True'
        
        if platform_obj.authenticate():
            print(f"   ✓ Authenticated")
            
            # Check if live
            is_live, stream_title = platform_obj.is_live(username)
            
            if is_live:
                print(f"   ✅ LIVE")
                print(f"   📺 Title: {stream_title}")
                stream_url = get_stream_url(platform_name, username)
                print(f"   🔗 URL: {stream_url}")
                live_streams.append({
                    'platform': platform_name,
                    'username': username,
                    'title': stream_title,
                    'url': stream_url
                })
            else:
                print(f"   ⚪ OFFLINE")
        else:
            print(f"   ✗ Authentication failed")
        print()
    
    if not live_streams:
        print("❌ No live streams detected - cannot test posting")
        return False
    
    print(f"✅ Detected {len(live_streams)} live stream(s)")
    print()
    
    # ============================================
    # STEP 2: Initialize Social Platforms
    # ============================================
    print("="*70)
    print("STEP 2: Initializing Social Platforms")
    print("="*70)
    print()
    
    social_platforms = []
    
    # Mastodon
    print("🐘 Mastodon...")
    mastodon = MastodonPlatform()
    if mastodon.authenticate():
        print("   ✓ Authenticated")
        social_platforms.append(mastodon)
    else:
        print("   ✗ Not configured")
    
    # Bluesky
    print("🦋 Bluesky...")
    bluesky = BlueskyPlatform()
    if bluesky.authenticate():
        print("   ✓ Authenticated")
        social_platforms.append(bluesky)
    else:
        print("   ✗ Not configured")
    
    print()
    
    if not social_platforms:
        print("❌ No social platforms configured - cannot test posting")
        return False
    
    print(f"✅ {len(social_platforms)} social platform(s) ready")
    print()
    
    # ============================================
    # STEP 3: Post Announcements (SEPARATE MODE)
    # ============================================
    print("="*70)
    print("STEP 3: Posting in SEPARATE Mode")
    print("="*70)
    print()
    
    separate_post_ids = []
    
    try:
        for idx, stream in enumerate(live_streams):
            platform_name = stream['platform']
            title = stream['title']
            username = stream['username']
            url = stream['url']
            
            # Create message with URL
            message = f"🔴 LIVE on {platform_name}!\n\n{title}\n\n{url}\n\n#{platform_name}Live"
            
            print(f"📢 Posting announcement {idx+1}/{len(live_streams)}: {platform_name}")
            print(f"   Title: {title[:60]}...")
            print(f"   URL: {url}")
            print()
            
            for social in social_platforms:
                print(f"   Posting to {social.name}...")
                
                post_id = social.post(message, reply_to_id=None, platform_name=platform_name)
                if post_id:
                    print(f"      ✅ Posted (ID: {post_id})")
                    separate_post_ids.append({
                        'social': social.name,
                        'post_id': post_id,
                        'platform': platform_name
                    })
                else:
                    print(f"      ❌ Failed")
            print()
        
        print(f"✅ SEPARATE mode: Created {len(separate_post_ids)} posts")
        print()
        
    except Exception as e:
        print(f"❌ Error in SEPARATE mode: {e}")
        import traceback
        traceback.print_exc()
    
    # ============================================
    # STEP 4: Post Announcements (THREAD MODE)
    # ============================================
    print("="*70)
    print("STEP 4: Posting in THREAD Mode")
    print("="*70)
    print()
    print("⏳ Waiting 3 seconds before threading posts...")
    import time
    time.sleep(3)
    print()
    
    thread_post_ids = []
    thread_heads = {}  # Track the first post per social platform for threading
    
    try:
        for idx, stream in enumerate(live_streams):
            platform_name = stream['platform']
            title = stream['title']
            username = stream['username']
            url = stream['url']
            
            # Create message with URL
            if idx == 0:
                message = f"🔴 LIVE on {platform_name}!\n\n{title}\n\n{url}\n\n#{platform_name}Live"
            else:
                message = f"🔴 Also LIVE on {platform_name}!\n\n{title}\n\n{url}\n\n#{platform_name}Live"
            
            print(f"📢 Posting announcement {idx+1}/{len(live_streams)}: {platform_name}")
            print(f"   Title: {title[:60]}...")
            print(f"   URL: {url}")
            if idx > 0:
                print(f"   Threading: Will reply to previous post")
            print()
            
            for social in social_platforms:
                # Determine if this should be threaded
                reply_to_id = None
                if idx > 0:
                    reply_to_id = thread_heads.get(social.name)
                
                thread_text = f" (threaded)" if reply_to_id else " (new thread)"
                print(f"   Posting to {social.name}{thread_text}...")
                
                post_id = social.post(message, reply_to_id=reply_to_id, platform_name=platform_name)
                if post_id:
                    print(f"      ✅ Posted (ID: {post_id})")
                    thread_post_ids.append({
                        'social': social.name,
                        'post_id': post_id,
                        'platform': platform_name,
                        'threaded': reply_to_id is not None
                    })
                    # Update thread head for next iteration
                    thread_heads[social.name] = post_id
                else:
                    print(f"      ❌ Failed")
            print()
        
        print(f"✅ THREAD mode: Created {len(thread_post_ids)} posts")
        print()
        
    except Exception as e:
        print(f"❌ Error in THREAD mode: {e}")
        import traceback
        traceback.print_exc()
    
    # ============================================
    # STEP 5: Summary
    # ============================================
    print("="*70)
    print("📊 POSTING SUMMARY")
    print("="*70)
    print()
    print(f"Streams detected: {len(live_streams)}")
    print()
    
    print("SEPARATE MODE:")
    print(f"  Total posts: {len(separate_post_ids)}")
    for post in separate_post_ids:
        print(f"    • {post['social']}: {post['platform']} - {post['post_id']}")
    print()
    
    print("THREAD MODE:")
    print(f"  Total posts: {len(thread_post_ids)}")
    for post in thread_post_ids:
        thread_marker = "└─" if post['threaded'] else "──"
        print(f"    {thread_marker} {post['social']}: {post['platform']} - {post['post_id']}")
    print()
    
    total_posts = len(separate_post_ids) + len(thread_post_ids)
    print(f"GRAND TOTAL: {total_posts} posts created")
    print()
    print("="*70)
    print("✅ Test completed successfully!")
    print("="*70)
    print()
    print("⚠️  NOTE: Posts were created on your social media accounts!")
    print("    Check Mastodon and Bluesky to see:")
    print("    - SEPARATE mode: 3 independent posts per platform")
    print("    - THREAD mode: 3 threaded posts (first post + 2 replies)")
    print()
    
    return True

if __name__ == "__main__":
    try:
        # Ask for confirmation
        print()
        print("⚠️  WARNING: This test will POST to your Mastodon and Bluesky accounts!")
        print()
        response = input("Continue? (yes/no): ").strip().lower()
        
        if response not in ['yes', 'y']:
            print("Test cancelled.")
            sys.exit(0)
        
        print()
        success = test_live_stream_posting()
        
        if success:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
