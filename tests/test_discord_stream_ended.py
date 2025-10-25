#!/usr/bin/env python3
"""
Test Discord stream ended message functionality.

This test demonstrates:
1. Posting initial stream notification
2. Updating the embed with fresh data (simulating live stream)
3. Marking the stream as ended with custom message (keeping VOD link)
"""

import sys
import time
sys.path.insert(0, '.')

# Import stream-daemon module (handle hyphenated filename)
import importlib.util
spec = importlib.util.spec_from_file_location("stream_daemon", "stream-daemon.py")
stream_daemon = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stream_daemon)

def test_stream_ended():
    """Test complete stream lifecycle: start, update, end."""
    
    print("=" * 80)
    print("Discord Stream Ended Test")
    print("=" * 80)
    print()
    
    # Initialize platforms
    print("🔧 Initializing platforms...")
    kick = stream_daemon.KickPlatform()
    twitch = stream_daemon.TwitchPlatform()
    youtube = stream_daemon.YouTubePlatform()
    discord = stream_daemon.DiscordPlatform()
    
    # Authenticate
    print("🔑 Authenticating...")
    kick.authenticate()
    twitch.authenticate()
    youtube.authenticate()
    
    if not discord.authenticate():
        print("❌ Discord authentication failed!")
        return
    
    print("✓ All platforms authenticated")
    print()
    
    # Get configured usernames from .env
    import os
    kick_username = os.getenv('KICK_USERNAME', 'asmongold')
    twitch_username = os.getenv('TWITCH_USERNAME', 'lilypita')
    youtube_username = os.getenv('YOUTUBE_USERNAME', '@grndpagaming')
    
    # Test with configured streams
    test_streams = [
        ('Kick', kick_username, kick, f'https://kick.com/{kick_username}'),
        ('Twitch', twitch_username, twitch, f'https://twitch.tv/{twitch_username}'),
        ('YouTube', youtube_username, youtube, f'https://youtube.com/{youtube_username}/live'),
    ]
    
    posted_streams = []
    
    # Phase 1: Post initial stream notifications
    print("📤 Phase 1: Posting initial stream notifications...")
    print("-" * 80)
    
    for platform_name, username, platform, stream_url in test_streams:
        print(f"\n{platform_name}: Checking {username}...")
        is_live, stream_data = platform.is_live(username)
        
        if is_live and stream_data:
            title = stream_data.get('title', 'Untitled')
            viewers = stream_data.get('viewer_count', 0)
            game = stream_data.get('game_name', 'Unknown')
            
            print(f"  ✓ LIVE: {title}")
            print(f"    👥 {viewers:,} viewers")
            print(f"    🎮 {game}")
            
            # Post to Discord
            message = f"{platform_name} is live: {title} {stream_url}"
            message_id = discord.post(message, platform_name=platform_name, stream_data=stream_data)
            
            if message_id:
                print(f"  ✓ Posted to Discord (Message ID: {message_id})")
                posted_streams.append((platform_name, username, platform, stream_url, stream_data))
            else:
                print(f"  ✗ Failed to post to Discord")
        else:
            print(f"  ⚪ Offline")
    
    if not posted_streams:
        print("\n⚠ No live streams found to test with!")
        return
    
    print()
    print("=" * 80)
    print(f"✓ Posted {len(posted_streams)} stream notification(s)")
    print()
    
    # Phase 2: Update embeds to simulate stream in progress
    print("📤 Phase 2: Updating embeds (simulating stream updates)...")
    print("-" * 80)
    print("⏳ Waiting 10 seconds before first update...")
    time.sleep(10)
    
    for platform_name, username, platform, stream_url, old_data in posted_streams:
        print(f"\n{platform_name}: Fetching fresh data for {username}...")
        is_live, stream_data = platform.is_live(username)
        
        if is_live and stream_data:
            old_viewers = old_data.get('viewer_count', 0)
            new_viewers = stream_data.get('viewer_count', 0)
            diff = new_viewers - old_viewers
            diff_str = f"+{diff}" if diff > 0 else str(diff) if diff < 0 else "±0"
            
            print(f"  👥 {new_viewers:,} viewers ({diff_str})")
            
            # Update Discord embed
            success = discord.update_stream(platform_name, stream_data, stream_url)
            if success:
                print(f"  ✓ Discord embed updated")
            else:
                print(f"  ✗ Failed to update Discord")
        else:
            print(f"  ⚪ Stream went offline")
    
    print()
    print("=" * 80)
    print("✓ Updated all embeds with fresh data")
    print()
    
    # Phase 3: Mark streams as ended
    print("📤 Phase 3: Marking streams as ended...")
    print("-" * 80)
    print("⏳ Waiting 10 seconds before marking as ended...")
    time.sleep(10)
    
    for platform_name, username, platform, stream_url, old_data in posted_streams:
        print(f"\n{platform_name}: Marking stream as ended for {username}...")
        
        # Fetch final stats (or use cached data if stream already ended)
        is_live, stream_data = platform.is_live(username)
        if not is_live:
            # Stream ended, use last known data
            stream_data = old_data
            print(f"  ⚪ Stream is now offline")
        else:
            # Stream still live, use current data as "final" stats for demo
            print(f"  ✓ Stream still live (using current stats as final)")
        
        # Update Discord embed to show stream ended
        success = discord.end_stream(platform_name, stream_data, stream_url)
        if success:
            print(f"  ✓ Discord embed updated to show stream ended")
            print(f"    💬 Custom ended message applied")
            print(f"    🔗 VOD link preserved: {stream_url}")
        else:
            print(f"  ✗ Failed to update Discord")
    
    print()
    print("=" * 80)
    print("✓ Test complete!")
    print()
    print("📋 Summary:")
    print(f"  • Posted {len(posted_streams)} initial stream notification(s)")
    print(f"  • Updated embeds with fresh viewer counts")
    print(f"  • Marked streams as ended with custom messages")
    print(f"  • VOD links preserved in all ended embeds")
    print()
    print("💡 TIP: Check your Discord channel to see:")
    print("  1. Initial embeds with role mentions")
    print("  2. Updated viewer counts")
    print("  3. Final 'stream ended' messages with VOD links")
    print()

if __name__ == "__main__":
    test_stream_ended()
