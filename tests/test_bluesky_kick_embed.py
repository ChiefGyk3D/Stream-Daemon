#!/usr/bin/env python3
"""
Test Bluesky embed cards with Kick stream data.

This test demonstrates that Kick embeds now work on Bluesky by using
the stream metadata (title, thumbnail, viewer count) instead of trying
to scrape the Kick page (which is blocked by CloudFlare).
"""

import sys
import time
sys.path.insert(0, '.')

# Import stream-daemon module (handle hyphenated filename)
import importlib.util
spec = importlib.util.spec_from_file_location("stream_daemon", "stream-daemon.py")
stream_daemon = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stream_daemon)

def test_bluesky_kick_embed():
    """Test Bluesky embed for Kick with stream metadata."""
    
    print("=" * 80)
    print("Bluesky Kick Embed Test")
    print("=" * 80)
    print()
    
    # Initialize platforms
    print("🔧 Initializing platforms...")
    kick = stream_daemon.KickPlatform()
    bluesky = stream_daemon.BlueskyPlatform()
    
    # Authenticate
    print("🔑 Authenticating...")
    kick.authenticate()
    
    if not bluesky.authenticate():
        print("❌ Bluesky authentication failed!")
        print("   Make sure BLUESKY_ENABLE_POSTING=True in .env")
        return
    
    print("✓ All platforms authenticated")
    print()
    
    # Get configured Kick username from .env
    import os
    username = os.getenv('KICK_USERNAME', 'asmongold')
    stream_url = f'https://kick.com/{username}'
    
    print(f"📡 Checking Kick stream: {username}...")
    is_live, stream_data = kick.is_live(username)
    
    if not is_live or not stream_data:
        print(f"⚪ {username} is not live. Cannot test embed.")
        print("   Try again when the stream is live, or update KICK_USERNAME in .env")
        return
    
    title = stream_data.get('title', 'Untitled')
    viewers = stream_data.get('viewer_count', 0)
    game = stream_data.get('game_name', 'Unknown')
    thumbnail = stream_data.get('thumbnail_url', 'N/A')
    
    print(f"✓ LIVE: {title}")
    print(f"  👥 {viewers:,} viewers")
    print(f"  🎮 {game}")
    print(f"  📸 Thumbnail: {thumbnail[:60]}...")
    print()
    
    # Post to Bluesky WITH stream_data
    print("📤 Posting to Bluesky with stream metadata...")
    message = f"🔴 {username} is live on Kick!\n\n{title}\n\n{stream_url}"
    
    try:
        post_id = bluesky.post(message, platform_name='Kick', stream_data=stream_data)
        
        if post_id:
            print(f"✓ Posted to Bluesky (Post ID: {post_id})")
            print()
            print("🎉 SUCCESS! Kick embed created with:")
            print(f"  • Title: {title[:50]}...")
            print(f"  • Description: 🔴 LIVE • {viewers:,} viewers • {game}")
            print(f"  • Thumbnail: Uploaded from {thumbnail[:40]}...")
            print()
            print("📋 Check your Bluesky feed to see the rich embed card!")
            print("   It should show:")
            print("   - Stream title")
            print("   - Viewer count and category")
            print("   - Live stream thumbnail")
            print("   - Clickable link to Kick")
        else:
            print("✗ Failed to post to Bluesky")
    except Exception as e:
        print(f"✗ Error posting to Bluesky: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=" * 80)
    print("Test complete!")
    print()

if __name__ == "__main__":
    test_bluesky_kick_embed()
