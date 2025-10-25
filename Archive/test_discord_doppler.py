#!/usr/bin/env python3
"""
Test Discord integration with Doppler secrets
Tests both single role and per-platform role configurations
"""

import sys
import os

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

def test_discord_posting():
    """Test Discord webhook posting with real stream data"""
    
    print("=" * 70)
    print("DISCORD DOPPLER INTEGRATION TEST")
    print("=" * 70)
    
    # Initialize platforms to check real stream data
    print("\n[0/4] Initializing streaming platforms...")
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
    
    print("\n[1/4] Authenticating Discord...")
    if not discord.authenticate():
        print("❌ Discord authentication failed!")
        print("   Make sure you have set up Doppler secrets:")
        print("   - discord_webhook_url (required)")
        print("   - discord_role (optional - for single role)")
        print("   - discord_role_twitch, discord_role_youtube, discord_role_kick (optional - for per-platform roles)")
        return False
    
    print("✅ Discord authenticated successfully!")
    print(f"   Default webhook: {'✓' if discord.webhook_url else '✗'}")
    print(f"   Platform webhooks: {len(discord.webhook_urls)} configured")
    print(f"   Default role: {'✓' if discord.role_id else '✗'}")
    print(f"   Platform roles: {len(discord.role_mentions)} configured")
    
    # Get configured usernames from .env
    import os
    kick_username = os.getenv('KICK_USERNAME', 'asmongold')
    twitch_username = os.getenv('TWITCH_USERNAME', 'lilypita')
    youtube_username = os.getenv('YOUTUBE_USERNAME', '@grndpagaming')
    
    # Check real stream status for the configured channels
    print("\n[2/4] Checking live stream status...")
    test_channels = [
        {'platform': kick, 'platform_name': 'kick', 'username': kick_username, 'url_template': f'https://kick.com/{kick_username}'},
        {'platform': twitch, 'platform_name': 'twitch', 'username': twitch_username, 'url_template': f'https://twitch.tv/{twitch_username}'},
        {'platform': youtube, 'platform_name': 'youtube', 'username': youtube_username, 'url_template': f'https://youtube.com/{youtube_username}/live'},
    ]
    
    test_streams = []
    
    for channel in test_channels:
        platform_obj = channel['platform']
        username = channel['username']
        platform_name = channel['platform_name']
        
        print(f"   Checking {platform_name.upper()}/{username}...", end=" ")
        
        is_live, stream_info = platform_obj.is_live(username)
        
        if is_live and stream_info:
            print(f"✅ LIVE!")
            if isinstance(stream_info, dict):
                print(f"      Title: {stream_info.get('title', 'Unknown')}")
                if stream_info.get('viewer_count'):
                    print(f"      Viewers: {stream_info['viewer_count']:,}")
                if stream_info.get('game_name'):
                    print(f"      Category: {stream_info['game_name']}")
                
                test_streams.append({
                    'platform': platform_name,
                    'channel': username,
                    'title': stream_info.get('title', 'Live Stream'),
                    'url': channel['url_template'].format(username.lstrip('@')),
                    'stream_data': stream_info
                })
            else:
                # Old format (just title string) - create basic stream_data
                print(f"      Title: {stream_info}")
                test_streams.append({
                    'platform': platform_name,
                    'channel': username,
                    'title': stream_info,
                    'url': channel['url_template'].format(username.lstrip('@')),
                    'stream_data': {
                        'title': stream_info,
                        'viewer_count': None,
                        'thumbnail_url': None,
                        'game_name': None
                    }
                })
        else:
            print(f"❌ Offline")
            # Use test data if not live
            print(f"      Using test data instead")
            test_data = {
                'kick': {
                    'title': 'ELDEN RING DLC - First Playthrough',
                    'viewer_count': 12543,
                    'thumbnail_url': 'https://images.kick.com/video_thumbnails/example.jpg',
                    'game_name': 'Elden Ring'
                },
                'twitch': {
                    'title': 'Cozy Art Stream 🎨 Drawing Cute Characters',
                    'viewer_count': 847,
                    'thumbnail_url': 'https://static-cdn.jtvnw.net/previews-ttv/live_user_lilypita-1280x720.jpg',
                    'game_name': 'Art'
                },
                'youtube': {
                    'title': 'Red Dead Redemption 2 - Story Mode Part 15',
                    'viewer_count': 1234,
                    'thumbnail_url': 'https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg',
                    'game_name': None
                }
            }
            
            stream_data = test_data[platform_name]
            test_streams.append({
                'platform': platform_name,
                'channel': username,
                'title': stream_data['title'],
                'url': channel['url_template'].format(username.lstrip('@')),
                'stream_data': stream_data
            })
    
    print("\n" + "=" * 70)
    print("TESTING DISCORD POSTS")
    print("=" * 70)
    
    successful_posts = 0
    
    for i, stream in enumerate(test_streams, 1):
        print(f"\n[{i}/3] Testing {stream['platform'].upper()} - {stream['channel']}")
        print(f"      Title: {stream['title']}")
        print(f"      URL: {stream['url']}")
        
        # Create message
        message = f"🎮 {stream['channel']} is now live!\n{stream['title']}\n{stream['url']}"
        
        # Post to Discord with stream metadata
        result = discord.post(
            message=message,
            reply_to_id=None,
            platform_name=stream['platform'],
            stream_data=stream['stream_data']
        )
        
        if result:
            print(f"      ✅ Posted successfully!")
            successful_posts += 1
            
            # Show which webhook and role were used
            webhook_used = "platform-specific" if stream['platform'] in discord.webhook_urls else "default"
            role_used = "none"
            if stream['platform'] in discord.role_mentions:
                role_used = f"platform-specific ({discord.role_mentions[stream['platform']]})"
            elif discord.role_id:
                role_used = f"default ({discord.role_id})"
            
            print(f"      📡 Webhook: {webhook_used}")
            print(f"      👥 Role: {role_used}")
        else:
            print(f"      ❌ Failed to post")
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"✓ Successful posts: {successful_posts}/3")
    print(f"✗ Failed posts: {3 - successful_posts}/3")
    
    if successful_posts == 3:
        print("\n🎉 All Discord posts succeeded!")
        print("\nCheck your Discord channel to verify:")
        print("  • Each platform has correct color (Purple/Red/Green)")
        print("  • Correct role mentions (if configured)")
        print("  • Clickable stream URLs")
        print("  • Rich embed cards with titles")
        print("  • Viewer counts displayed (if stream is live)")
        print("  • Stream thumbnails (if available)")
        print("  • Game/Category info (if available)")
        return True
    else:
        print("\n⚠️ Some posts failed. Check the errors above.")
        return False


if __name__ == "__main__":
    print("\n")
    success = test_discord_posting()
    print("\n")
    sys.exit(0 if success else 1)
