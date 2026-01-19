#!/usr/bin/env python3
"""
Quick connection test for Stream Daemon
Tests streaming platform authentication, social media posting, and LLM generation
"""

import sys
import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import from modularized package
from stream_daemon.config import get_config
from stream_daemon.platforms.social import MastodonPlatform, BlueskyPlatform, DiscordPlatform, MatrixPlatform
from stream_daemon.platforms.streaming import TwitchPlatform, YouTubePlatform, KickPlatform
from stream_daemon.ai import AIMessageGenerator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def test_streaming_platforms():
    """Test authentication and data fetching from streaming platforms."""
    logger.info("\n" + "="*60)
    logger.info("🎮 TESTING STREAMING PLATFORMS")
    logger.info("="*60)
    
    streaming_platforms = [
        TwitchPlatform(),
        YouTubePlatform(),
        KickPlatform()
    ]
    
    enabled_streaming = []
    results = {}
    live_streams = {}  # Store live stream data for AI generation
    
    for platform in streaming_platforms:
        logger.info(f"\n📡 Testing {platform.name}...")
        
        # Test authentication
        if not platform.authenticate():
            logger.warning(f"  ✗ {platform.name} not configured or authentication failed")
            results[platform.name] = "Not configured"
            continue
        
        logger.info(f"  ✓ {platform.name} authentication successful")
        enabled_streaming.append(platform)
        
        # Test fetching stream status
        try:
            # Get username from config
            from stream_daemon.config import get_config
            username = get_config(platform.name, 'username')
            
            is_live, stream_data = platform.is_live(username)
            if is_live:
                logger.info(f"  ✓ {platform.name} IS LIVE!")
                logger.info(f"    Stream Title: {stream_data.get('title', 'N/A')}")
                logger.info(f"    Viewers: {stream_data.get('viewer_count', 'N/A')}")
                logger.info(f"    Game: {stream_data.get('game_name', 'N/A')}")
                results[platform.name] = f"LIVE - {stream_data.get('viewer_count', 0)} viewers"
                
                # Store live stream data for AI generation testing
                # Build proper URL based on platform
                if platform.name == 'Twitch':
                    stream_url = f"https://twitch.tv/{username}"
                elif platform.name == 'YouTube':
                    stream_url = f"https://youtube.com/@{username}/live"
                elif platform.name == 'Kick':
                    stream_url = f"https://kick.com/{username}"
                else:
                    stream_url = ""
                
                live_streams[platform.name] = {
                    'username': username,
                    'title': stream_data.get('title', 'Untitled Stream'),
                    'viewer_count': stream_data.get('viewer_count', 0),
                    'game_name': stream_data.get('game_name', ''),
                    'url': stream_url
                }
            else:
                logger.info(f"  • {platform.name} is offline")
                results[platform.name] = "Offline"
        except Exception as e:
            logger.error(f"  ✗ Error checking {platform.name}: {e}")
            results[platform.name] = f"Error: {e}"
    
    return enabled_streaming, results, live_streams

def test_social_platforms(enabled_streaming):
    """Test authentication and posting to social platforms."""
    logger.info("\n" + "="*60)
    logger.info("📱 TESTING SOCIAL PLATFORMS")
    logger.info("="*60)
    
    social_platforms = [
        MastodonPlatform(),
        BlueskyPlatform(),
        DiscordPlatform(),
        MatrixPlatform()
    ]
    
    enabled_social = []
    results = {}
    
    for platform in social_platforms:
        logger.info(f"\n🔗 Testing {platform.name}...")
        
        # Test authentication
        if not platform.authenticate():
            logger.warning(f"  ✗ {platform.name} not configured or authentication failed")
            results[platform.name] = "Not configured"
            continue
        
        logger.info(f"  ✓ {platform.name} authentication successful")
        enabled_social.append(platform)
        results[platform.name] = "Authenticated"
    
    # Prompt for test post
    if enabled_social:
        logger.info("\n" + "="*60)
        logger.info("📝 TEST POST OPTION")
        logger.info("="*60)
        logger.info("Would you like to send a test post to verify posting works?")
        logger.info("Enabled social platforms:")
        for platform in enabled_social:
            logger.info(f"  • {platform.name}")
        
        print("\n")
        response = input("Send test post? (yes/no): ").strip().lower()
        
        if response in ['yes', 'y']:
            test_message = f"🧪 Stream Daemon Test Post - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\nThis is an automated test to verify posting functionality."
            
            logger.info("\n📤 Sending test posts...")
            for platform in enabled_social:
                try:
                    logger.info(f"  Posting to {platform.name}...")
                    post_id = platform.post(test_message)
                    logger.info(f"  ✓ Successfully posted to {platform.name}! Post ID: {post_id}")
                    results[platform.name] = f"Posted (ID: {post_id})"
                except Exception as e:
                    logger.error(f"  ✗ Failed to post to {platform.name}: {e}")
                    results[platform.name] = f"Post failed: {e}"
    
    return enabled_social, results

def test_llm_generation(enabled_social=None, live_streams=None):
    """Test LLM message generation with real stream data."""
    logger.info("\n" + "="*60)
    logger.info("🤖 TESTING LLM MESSAGE GENERATION")
    logger.info("="*60)
    
    results = {}
    
    try:
        # Initialize AI generator
        ai_generator = AIMessageGenerator()
        
        if not ai_generator.authenticate():
            logger.warning("  ✗ LLM not configured or disabled")
            results['status'] = "Not configured"
            return results, None
        
        logger.info("  ✓ LLM authentication successful")
        logger.info(f"  Provider: {ai_generator.provider}")
        logger.info(f"  Model: {ai_generator.model}")
        
        # Use real stream data if available, otherwise use test data
        if live_streams:
            logger.info("\n🎮 Using REAL LIVE STREAM DATA for AI generation:")
            for platform_name, stream_data in live_streams.items():
                logger.info(f"  • {platform_name}: {stream_data['username']} - {stream_data['title'][:60]}...")
            
            # Ask which stream to generate message for
            print("\n")
            stream_choices = list(live_streams.keys())
            for i, platform_name in enumerate(stream_choices, 1):
                stream_data = live_streams[platform_name]
                print(f"  {i}. {platform_name} - {stream_data['username']} ({stream_data['viewer_count']} viewers)")
            
            choice = input(f"\nSelect stream to generate message for (1-{len(stream_choices)}, or press Enter for first): ").strip()
            
            if choice and choice.isdigit() and 1 <= int(choice) <= len(stream_choices):
                selected_platform = stream_choices[int(choice) - 1]
            else:
                selected_platform = stream_choices[0]
            
            stream_data = live_streams[selected_platform]
            platform_name = selected_platform
            username = stream_data['username']
            title = stream_data['title']
            url = stream_data['url']
            
            logger.info(f"\n✨ Generating AI message for: {platform_name} - {username}")
            logger.info(f"  Title: {title}")
            logger.info(f"  Viewers: {stream_data['viewer_count']}")
            if stream_data.get('game_name'):
                logger.info(f"  Game: {stream_data['game_name']}")
        else:
            # Use test data
            logger.info("\n⚠️  No live streams found, using TEST DATA for AI generation")
            platform_name = 'Twitch'
            username = 'test_streamer'
            title = 'Building a Python Stream Daemon with LLM Integration'
            url = 'https://twitch.tv/test_streamer'
        
        try:
            generated_message = ai_generator.generate_stream_start_message(
                platform_name=platform_name,
                username=username,
                title=title,
                url=url,
                social_platform='mastodon'
            )
            
            if generated_message:
                logger.info("\n  ✓ Successfully generated message!")
                logger.info(f"\n{'─'*60}")
                logger.info("Generated Message:")
                logger.info(f"{'─'*60}")
                logger.info(generated_message)
                logger.info(f"{'─'*60}\n")
                results['status'] = "Success"
                results['message_length'] = len(generated_message)
                results['platform'] = platform_name
                results['username'] = username
                
                # Offer to post AI-generated message to all social platforms
                if enabled_social:
                    print("\n")
                    response = input("Post this AI-generated message to all social platforms? (yes/no): ").strip().lower()
                    
                    if response in ['yes', 'y']:
                        logger.info("\n📤 Posting AI-generated message to social platforms...")
                        for platform in enabled_social:
                            try:
                                logger.info(f"  Posting to {platform.name}...")
                                post_id = platform.post(generated_message)
                                logger.info(f"  ✓ Successfully posted to {platform.name}! Post ID: {post_id}")
                                results[f'{platform.name}_post'] = f"Posted (ID: {post_id})"
                            except Exception as e:
                                logger.error(f"  ✗ Failed to post to {platform.name}: {e}")
                                results[f'{platform.name}_post'] = f"Failed: {e}"
            else:
                logger.warning("  ⚠ Generated message is empty")
                results['status'] = "Empty response"
                
        except Exception as e:
            logger.error(f"  ✗ Failed to generate message: {e}")
            results['status'] = f"Generation failed: {e}"
            
    except Exception as e:
        logger.error(f"  ✗ Error initializing LLM: {e}")
        results['status'] = f"Init failed: {e}"
    
    return results, ai_generator if 'ai_generator' in locals() else None

def print_summary(streaming_results, social_results, llm_results=None):
    """Print a summary of all test results."""
    logger.info("\n" + "="*60)
    logger.info("📊 TEST SUMMARY")
    logger.info("="*60)
    
    logger.info("\n🎮 Streaming Platforms:")
    for platform, result in streaming_results.items():
        logger.info(f"  {platform:12} - {result}")
    
    logger.info("\n📱 Social Platforms:")
    for platform, result in social_results.items():
        logger.info(f"  {platform:12} - {result}")
    
    if llm_results:
        logger.info("\n🤖 LLM Generation:")
        for key, value in llm_results.items():
            logger.info(f"  {key:15} - {value}")
    
    logger.info("\n" + "="*60)

def main():
    """Main test function."""
    try:
        # Test streaming platforms and collect live stream data
        enabled_streaming, streaming_results, live_streams = test_streaming_platforms()
        
        if not enabled_streaming:
            logger.error("\n❌ No streaming platforms are configured!")
            logger.error("Please configure at least one streaming platform in .env")
            return 1
        
        # Test social platforms
        enabled_social, social_results = test_social_platforms(enabled_streaming)
        
        if not enabled_social:
            logger.error("\n❌ No social platforms are configured!")
            logger.error("Please configure at least one social platform in .env")
            return 1
        
        # Test LLM generation with real live stream data
        llm_results, ai_generator = test_llm_generation(enabled_social, live_streams)
        
        # Print summary
        print_summary(streaming_results, social_results, llm_results)
        
        logger.info("\n✅ All tests complete!")
        
        # Production readiness check
        if live_streams:
            logger.info("\n" + "="*60)
            logger.info("🚀 PRODUCTION READINESS CHECK")
            logger.info("="*60)
            logger.info(f"✅ Streaming platforms: {len(enabled_streaming)} configured")
            logger.info(f"✅ Social platforms: {len(enabled_social)} configured")
            logger.info(f"✅ Live streams detected: {len(live_streams)}")
            if llm_results.get('status') == 'Success':
                logger.info(f"✅ AI generation: Working")
            logger.info("\n🎉 Stream Daemon is PRODUCTION READY!")
            logger.info("   Run: python3 stream-daemon.py")
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Test interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"\n❌ Unexpected error: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
