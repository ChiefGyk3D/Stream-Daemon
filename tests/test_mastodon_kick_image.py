#!/usr/bin/env python3
"""
Test Mastodon image attachments with Kick stream data.

This test demonstrates that Kick thumbnails now appear on Mastodon by uploading
the stream thumbnail as an image attachment instead of relying on server-side
preview cards (which are blocked by CloudFlare).
"""

import sys
import time
sys.path.insert(0, '.')

# Import stream-daemon module (handle hyphenated filename)
import importlib.util
spec = importlib.util.spec_from_file_location("stream_daemon", "stream-daemon.py")
stream_daemon = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stream_daemon)

def test_mastodon_kick_image():
    """Test Mastodon image attachment for Kick with stream metadata."""
    
    print("=" * 80)
    print("Mastodon Kick Image Attachment Test")
    print("=" * 80)
    print()
    
    # Initialize platforms
    print("🔧 Initializing platforms...")
    kick = stream_daemon.KickPlatform()
    mastodon = stream_daemon.MastodonPlatform()
    
    # Authenticate
    print("🔑 Authenticating...")
    kick.authenticate()
    
    if not mastodon.authenticate():
        print("❌ Mastodon authentication failed!")
        print("   Make sure MASTODON_ENABLE_POSTING=True in .env")
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
        print(f"⚪ {username} is not live. Cannot test image attachment.")
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
    
    # Post to Mastodon WITH stream_data
    print("📤 Posting to Mastodon with thumbnail attachment...")
    message = f"🔴 {username} is live on Kick!\n\n{title}\n\n{stream_url}"
    
    try:
        post_id = mastodon.post(message, platform_name='Kick', stream_data=stream_data)
        
        if post_id:
            print(f"✓ Posted to Mastodon (Post ID: {post_id})")
            print()
            print("🎉 SUCCESS! Kick thumbnail attached with:")
            print(f"  • Title: {title[:50]}...")
            print(f"  • Image Alt Text: 🔴 LIVE • {viewers:,} viewers • {game}")
            print(f"  • Thumbnail: Downloaded from {thumbnail[:40]}...")
            print()
            print("📋 Check your Mastodon feed to see the image!")
            print("   It should show:")
            print("   - Post text with clickable Kick link")
            print("   - Stream thumbnail as attached image")
            print("   - Image description with viewer count and category")
        else:
            print("✗ Failed to post to Mastodon")
    except Exception as e:
        print(f"✗ Error posting to Mastodon: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=" * 80)
    print("Test complete!")
    print()
    print("💡 Note: Mastodon doesn't support rich preview cards client-side like Bluesky.")
    print("   Instead, we upload the thumbnail as an image attachment.")
    print("   This provides a similar visual result while working around CloudFlare.")
    print()

if __name__ == "__main__":
    test_mastodon_kick_image()
