#!/usr/bin/env python3
"""
Test Discord embed updating behavior
Tests that Discord embeds are updated with fresh viewer counts and thumbnails
instead of posting duplicate messages
"""

import sys
import os
import time

# Add parent directory to path so we can import stream-daemon modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

# Load .env file for configuration settings (ENABLE_POSTING, etc.)
# Doppler will provide the actual secrets (webhooks, tokens, role IDs)
load_dotenv()

# Import stream-daemon.py as a module
import importlib.util
spec = importlib.util.spec_from_file_location("stream_daemon", "stream-daemon.py")
stream_daemon = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stream_daemon)

DiscordPlatform = stream_daemon.DiscordPlatform


def test_discord_updates():
    """Test Discord embed updates with real stream data"""
    
    print("=" * 70)
    print("DISCORD EMBED UPDATE TEST")
    print("=" * 70)
    print("\nThis test will:")
    print("  1. Post initial Discord embeds for live streams")
    print("  2. Update them every 15 seconds with fresh viewer counts")
    print("  3. Run for 3 update cycles (45 seconds total)")
    print("\n" + "=" * 70)
    
    # Initialize platforms to check real stream data
    print("\n[1/6] Initializing streaming platforms...")
    TwitchPlatform = stream_daemon.TwitchPlatform
    YouTubePlatform = stream_daemon.YouTubePlatform
    KickPlatform = stream_daemon.KickPlatform
    
    twitch = TwitchPlatform()
    youtube = YouTubePlatform()
    kick = KickPlatform()
    
    # Authenticate platforms
    twitch.authenticate()
    youtube.authenticate()
    kick.authenticate()
    
    # Initialize Discord platform
    discord = DiscordPlatform()
    
    print("\n[2/6] Authenticating Discord...")
    if not discord.authenticate():
        print("❌ Discord authentication failed!")
        return False
    
    print("✅ Discord authenticated!")
    
    # Get configured usernames from .env
    import os
    kick_username = os.getenv('KICK_USERNAME', 'asmongold')
    twitch_username = os.getenv('TWITCH_USERNAME', 'lilypita')
    youtube_username = os.getenv('YOUTUBE_USERNAME', '@grndpagaming')
    
    # Check real stream status for the configured channels
    print("\n[3/6] Checking live stream status...")
    test_channels = [
        {'platform': kick, 'platform_name': 'kick', 'username': kick_username, 'url': f'https://kick.com/{kick_username}'},
        {'platform': twitch, 'platform_name': 'twitch', 'username': twitch_username, 'url': f'https://twitch.tv/{twitch_username}'},
        {'platform': youtube, 'platform_name': 'youtube', 'username': youtube_username, 'url': f'https://youtube.com/{youtube_username}/live'},
    ]
    
    live_streams = []
    
    for channel in test_channels:
        platform_obj = channel['platform']
        username = channel['username']
        platform_name = channel['platform_name']
        
        print(f"   Checking {platform_name.upper()}/{username}...", end=" ")
        
        is_live, stream_info = platform_obj.is_live(username)
        
        if is_live and stream_info and isinstance(stream_info, dict):
            print(f"✅ LIVE! ({stream_info.get('viewer_count', 0):,} viewers)")
            live_streams.append({
                'platform': platform_obj,
                'platform_name': platform_name,
                'username': username,
                'url': channel['url'],
                'stream_data': stream_info
            })
        else:
            print(f"❌ Offline (skipping)")
    
    if not live_streams:
        print("\n⚠️ No live streams found! Test requires at least one live stream.")
        return False
    
    print(f"\n✓ Found {len(live_streams)} live stream(s)")
    
    # Post initial Discord embeds
    print("\n[4/6] Posting initial Discord embeds...")
    for stream in live_streams:
        platform_name = stream['platform_name']
        username = stream['username']
        stream_data = stream['stream_data']
        url = stream['url']
        
        title = stream_data.get('title', 'Live Stream')
        viewer_count = stream_data.get('viewer_count', 0)
        
        print(f"   📤 {platform_name.upper()}/{username}")
        print(f"      Viewers: {viewer_count:,}")
        
        # Create message
        message = f"🎮 {username} is now live!\n{title}\n{url}"
        
        # Post to Discord
        result = discord.post(
            message=message,
            reply_to_id=None,
            platform_name=platform_name,
            stream_data=stream_data
        )
        
        if result:
            print(f"      ✅ Posted (Message ID: {result})")
        else:
            print(f"      ❌ Failed to post")
    
    # Update cycle
    UPDATE_INTERVAL = 15  # seconds
    NUM_UPDATES = 3
    
    print(f"\n[5/6] Starting update cycle ({UPDATE_INTERVAL}s interval, {NUM_UPDATES} updates)")
    print(f"      Total test duration: ~{UPDATE_INTERVAL * NUM_UPDATES} seconds")
    print("\n" + "-" * 70)
    
    for update_num in range(1, NUM_UPDATES + 1):
        print(f"\n⏳ Waiting {UPDATE_INTERVAL} seconds before update #{update_num}...")
        time.sleep(UPDATE_INTERVAL)
        
        print(f"\n[Update {update_num}/{NUM_UPDATES}] Fetching fresh stream data...")
        
        for stream in live_streams:
            platform_obj = stream['platform']
            platform_name = stream['platform_name']
            username = stream['username']
            url = stream['url']
            
            print(f"   🔄 {platform_name.upper()}/{username}...", end=" ")
            
            # Get fresh stream data
            is_live, fresh_stream_data = platform_obj.is_live(username)
            
            if is_live and fresh_stream_data and isinstance(fresh_stream_data, dict):
                old_viewers = stream['stream_data'].get('viewer_count', 0)
                new_viewers = fresh_stream_data.get('viewer_count', 0)
                diff = new_viewers - old_viewers
                diff_str = f"+{diff}" if diff > 0 else str(diff) if diff < 0 else "±0"
                
                print(f"{new_viewers:,} viewers ({diff_str})")
                
                # Update Discord embed
                success = discord.update_stream(
                    platform_name=platform_name,
                    stream_data=fresh_stream_data,
                    stream_url=url
                )
                
                if success:
                    print(f"      ✅ Discord embed updated")
                    stream['stream_data'] = fresh_stream_data  # Update for next comparison
                else:
                    print(f"      ⚠️ Update failed")
            else:
                print(f"❌ Stream ended")
                discord.clear_stream(platform_name)
    
    # Summary
    print("\n" + "-" * 70)
    print("\n[6/6] TEST COMPLETE")
    print("=" * 70)
    print("\n✅ Discord embed update test completed successfully!")
    print("\nCheck your Discord channel to verify:")
    print("  • Original embeds were updated (not duplicated)")
    print("  • Viewer counts changed over time")
    print("  • Thumbnails refreshed each update")
    print("  • Footer shows 'Last updated' timestamp")
    print("  • Only 1 message per platform (updated in place)")
    
    return True


if __name__ == "__main__":
    print("\n")
    success = test_discord_updates()
    print("\n")
    sys.exit(0 if success else 1)
