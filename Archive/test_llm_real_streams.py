#!/usr/bin/env python3
"""
Test LLM with Real Live Stream Data
Fetches actual stream titles from Twitch, YouTube, and Kick and generates AI messages
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import stream-daemon module (handle hyphenated filename)
import importlib.util
spec = importlib.util.spec_from_file_location("stream_daemon", "stream-daemon.py")
stream_daemon = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stream_daemon)

# Import helper functions from daemon
from typing import Optional

def test_twitch():
    """Test Twitch with real stream data"""
    print("\n" + "="*60)
    print("Testing Twitch")
    print("="*60)
    
    username = os.getenv('TWITCH_USERNAME')
    if not username:
        print("⏭️  Twitch not configured (TWITCH_USERNAME not set)")
        return None
    
    try:
        from twitchAPI.twitch import Twitch
        import asyncio
        
        client_id = stream_daemon.get_secret('Twitch', 'client_id',
                                             secret_name_env='SECRETS_AWS_TWITCH_SECRET_NAME',
                                             secret_path_env='SECRETS_VAULT_TWITCH_SECRET_PATH',
                                             doppler_secret_env='SECRETS_DOPPLER_TWITCH_SECRET_NAME')
        client_secret = stream_daemon.get_secret('Twitch', 'client_secret',
                                                 secret_name_env='SECRETS_AWS_TWITCH_SECRET_NAME',
                                                 secret_path_env='SECRETS_VAULT_TWITCH_SECRET_PATH',
                                                 doppler_secret_env='SECRETS_DOPPLER_TWITCH_SECRET_NAME')
        
        if not all([client_id, client_secret]):
            print("✗ Twitch credentials not configured")
            return None
        
        print(f"✓ Username: {username}")
        print("✓ Credentials configured")
        
        # Fetch stream data
        async def get_stream():
            twitch = await Twitch(client_id, client_secret)
            users = []
            async for user in twitch.get_users(logins=[username]):
                users.append(user)
            
            if not users:
                print(f"✗ User '{username}' not found")
                await twitch.close()
                return None
            
            user_id = users[0].id
            streams = []
            async for stream in twitch.get_streams(user_id=[user_id]):
                streams.append(stream)
            
            await twitch.close()
            
            if streams:
                return streams[0]
            return None
        
        stream = asyncio.run(get_stream())
        
        if not stream:
            print(f"⚠ {username} is currently OFFLINE")
            print("   Using example title for testing...")
            title = "Just Chatting - Community Hangout and Chill Vibes!"
            url = f"https://twitch.tv/{username.lower()}"
            is_live = False
        else:
            print(f"✅ {username} is LIVE!")
            title = stream.title
            url = f"https://twitch.tv/{username.lower()}"
            is_live = True
            print(f"   Title: {title}")
            print(f"   Game: {stream.game_name}")
            print(f"   Viewers: {stream.viewer_count:,}")
        
        return {
            'platform': 'Twitch',
            'username': username,
            'title': title,
            'url': url,
            'is_live': is_live
        }
        
    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_youtube():
    """Test YouTube with real stream data"""
    print("\n" + "="*60)
    print("Testing YouTube")
    print("="*60)
    
    username = os.getenv('YOUTUBE_USERNAME')
    channel_id = os.getenv('YOUTUBE_CHANNEL_ID')
    
    if not (username or channel_id):
        print("⏭️  YouTube not configured (YOUTUBE_USERNAME or YOUTUBE_CHANNEL_ID not set)")
        return None
    
    try:
        from googleapiclient.discovery import build
        
        api_key = stream_daemon.get_secret('YouTube', 'api_key',
                                          secret_name_env='SECRETS_AWS_YOUTUBE_SECRET_NAME',
                                          secret_path_env='SECRETS_VAULT_YOUTUBE_SECRET_PATH',
                                          doppler_secret_env='SECRETS_DOPPLER_YOUTUBE_SECRET_NAME')
        if not api_key:
            print("✗ YOUTUBE_API_KEY not configured")
            return None
        
        display_name = username or channel_id
        print(f"✓ Channel: {display_name}")
        print("✓ API key configured")
        
        # Build YouTube API client
        youtube = build('youtube', 'v3', developerKey=api_key)
        
        # Get channel ID from username if needed
        if username and not channel_id:
            # Handle @username format
            handle = username.lstrip('@')
            channels = youtube.channels().list(part='id', forHandle=handle).execute()
            
            if not channels.get('items'):
                print(f"✗ Channel '@{handle}' not found")
                return None
            
            channel_id = channels['items'][0]['id']
            print(f"✓ Resolved channel ID: {channel_id}")
        
        # Search for live streams
        search = youtube.search().list(
            part='snippet',
            channelId=channel_id,
            eventType='live',
            type='video',
            maxResults=1
        ).execute()
        
        if search.get('items'):
            stream = search['items'][0]
            title = stream['snippet']['title']
            video_id = stream['id']['videoId']
            url = f"https://youtube.com/watch?v={video_id}"
            is_live = True
            
            print(f"✅ Channel is LIVE!")
            print(f"   Title: {title}")
            print(f"   URL: {url}")
        else:
            print(f"⚠ Channel is currently OFFLINE")
            print("   Using example title for testing...")
            title = "Live Coding Session - Building Cool Projects!"
            url = f"https://youtube.com/@{username.lstrip('@')}/live" if username else f"https://youtube.com/channel/{channel_id}/live"
            is_live = False
        
        return {
            'platform': 'YouTube',
            'username': display_name,
            'title': title,
            'url': url,
            'is_live': is_live
        }
        
    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_kick():
    """Test Kick with real stream data using daemon's KickPlatform"""
    print("\n" + "="*60)
    print("Testing Kick")
    print("="*60)
    
    username = os.getenv('KICK_USERNAME')
    if not username:
        print("⏭️  Kick not configured (KICK_USERNAME not set)")
        return None
    
    try:
        print(f"✓ Username: {username}")
        
        # Use the daemon's KickPlatform which has CloudFlare bypass
        kick = stream_daemon.KickPlatform()
        kick.authenticate()
        
        # Use the same method as other successful tests
        is_live, stream_data = kick.is_live(username)
        
        if is_live and stream_data:
            title = stream_data.get('title', 'Live Stream')
            viewer_count = stream_data.get('viewer_count')
            game_name = stream_data.get('game_name')
            
            print(f"✅ {username} is LIVE!")
            print(f"   Title: {title}")
            if viewer_count:
                print(f"   Viewers: {viewer_count:,}")
            if game_name:
                print(f"   Game: {game_name}")
            
            url = f"https://kick.com/{username.lower()}"
            
            return {
                'platform': 'Kick',
                'username': username,
                'title': title,
                'url': url,
                'is_live': True
            }
        else:
            print(f"⚠ {username} is currently OFFLINE")
            print("   Using example title for testing...")
            title = "Gaming and Vibes - Join the Fun!"
            url = f"https://kick.com/{username.lower()}"
            
            return {
                'platform': 'Kick',
                'username': username,
                'title': title,
                'url': url,
                'is_live': False
            }
        
    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def generate_ai_messages(stream_data):
    """Generate AI messages for stream data using daemon's AIMessageGenerator"""
    print("\n" + "="*60)
    print(f"Generating AI Messages - {stream_data['platform']}")
    print("="*60)
    print(f"Platform: {stream_data['platform']}")
    print(f"Username: {stream_data['username']}")
    print(f"Title: {stream_data['title']}")
    print(f"URL: {stream_data['url']}")
    print(f"Status: {'🔴 LIVE' if stream_data['is_live'] else '⚫ OFFLINE (using example)'}")
    
    try:
        # Use the daemon's AIMessageGenerator class
        ai_generator = stream_daemon.AIMessageGenerator()
        
        if not ai_generator.authenticate():
            print("\n✗ AI generator authentication failed")
            return False
        
        # Generate Bluesky message (300 chars)
        print("\n📱 Bluesky (300 chars):")
        print("-"*60)
        
        bluesky_msg = ai_generator.generate_stream_start_message(
            platform_name=stream_data['platform'],
            username=stream_data['username'],
            title=stream_data['title'],
            url=stream_data['url'],
            social_platform='bluesky'
        )
        
        if bluesky_msg:
            print(bluesky_msg)
            print(f"[{len(bluesky_msg)}/300 chars]")
        else:
            print("✗ Failed to generate message")
            return False
        
        # Generate Mastodon message (500 chars)
        print("\n🐘 Mastodon (500 chars):")
        print("-"*60)
        
        mastodon_msg = ai_generator.generate_stream_start_message(
            platform_name=stream_data['platform'],
            username=stream_data['username'],
            title=stream_data['title'],
            url=stream_data['url'],
            social_platform='mastodon'
        )
        
        if mastodon_msg:
            print(mastodon_msg)
            print(f"[{len(mastodon_msg)}/500 chars]")
        else:
            print("✗ Failed to generate message")
            return False
        
        print("\n✅ Messages generated successfully!")
        return True
        
    except Exception as e:
        print(f"\n✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test flow"""
    print("="*60)
    print("🎬 Real Live Stream LLM Test")
    print("="*60)
    print("\nFetching actual stream data from APIs...")
    print("="*60)
    
    # Fetch stream data from all platforms
    streams = []
    
    twitch_data = test_twitch()
    if twitch_data:
        streams.append(twitch_data)
    
    youtube_data = test_youtube()
    if youtube_data:
        streams.append(youtube_data)
    
    kick_data = test_kick()
    if kick_data:
        streams.append(kick_data)
    
    if not streams:
        print("\n❌ No platforms configured!")
        return 1
    
    # Generate AI messages for each stream
    results = {}
    for stream_data in streams:
        success = generate_ai_messages(stream_data)
        results[stream_data['platform']] = success
    
    # Summary
    print("\n" + "="*60)
    print("📊 Test Summary")
    print("="*60)
    
    for platform, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{status}: {platform}")
    
    # Show live status
    live_platforms = [s['platform'] for s in streams if s['is_live']]
    if live_platforms:
        print(f"\n🔴 Currently LIVE: {', '.join(live_platforms)}")
    
    print("="*60)
    
    if all(results.values()):
        print("\n🎉 All tests passed!")
        print("\nThe AI successfully generated messages using real stream data!")
        return 0
    else:
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test cancelled by user")
        sys.exit(1)
