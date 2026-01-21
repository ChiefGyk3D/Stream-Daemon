#!/usr/bin/env python3
"""Test improved AI prompts with real LLM calls."""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from stream_daemon.ai.generator import AIMessageGenerator

def test_prompt_outputs():
    """Test the new prompts with sample stream data."""
    
    print("=" * 80)
    print("Testing Improved AI Prompts for Stream Messages")
    print("=" * 80)
    print()
    
    # Initialize AI generator
    generator = AIMessageGenerator()
    
    print("🔧 Authenticating with LLM...")
    if not generator.authenticate():
        print("❌ Failed to authenticate. Check your LLM configuration:")
        print("   - LLM_ENABLE=True")
        print("   - LLM_PROVIDER=ollama or gemini")
        if generator.provider == 'ollama':
            print("   - Ollama running at configured host")
        else:
            print("   - GEMINI_API_KEY set")
        # Don't return - pytest functions should not return values
        return
    
    print(f"✅ Authenticated with {generator.provider} (model: {generator.model})")
    print()
    
    # Get real usernames from environment
    twitch_user = os.getenv('TWITCH_USERNAME', 'TestStreamer')
    youtube_user = os.getenv('YOUTUBE_USERNAME', '@DevStreamer')
    kick_user = os.getenv('KICK_USERNAME', 'CoolStreamer')
    
    # Test data - various stream scenarios with REAL usernames
    test_cases = [
        {
            "name": "Casual Gaming Stream",
            "platform": "Twitch",
            "username": twitch_user,
            "title": "Chill Minecraft Build Session",
            "url": f"https://twitch.tv/{twitch_user}",
            "social_platform": "bluesky"
        },
        {
            "name": "Competitive Gaming",
            "platform": "Twitch", 
            "username": twitch_user,
            "title": "Valorant Ranked Grind - Diamond Push",
            "url": f"https://twitch.tv/{twitch_user}",
            "social_platform": "mastodon"
        },
        {
            "name": "Tech/Dev Stream",
            "platform": "YouTube",
            "username": youtube_user,
            "title": "Building a Discord Bot with Python",
            "url": f"https://youtube.com/live/abc123",
            "social_platform": "bluesky"
        },
        {
            "name": "Just Chatting",
            "platform": "Kick",
            "username": kick_user,
            "title": "Morning Coffee and Vibes",
            "url": f"https://kick.com/{kick_user}",
            "social_platform": "discord"
        }
    ]
    
    # Test stream start messages
    print("🚀 STREAM START MESSAGES")
    print("-" * 80)
    print()
    
    for i, test in enumerate(test_cases, 1):
        print(f"Test {i}: {test['name']}")
        print(f"Platform: {test['platform']} | Target: {test['social_platform']}")
        print(f"Title: {test['title']}")
        print()
        
        start_msg = generator.generate_stream_start_message(
            platform_name=test['platform'],
            username=test['username'],
            title=test['title'],
            url=test['url'],
            social_platform=test['social_platform']
        )
        
        if start_msg:
            print(f"✨ Generated Message ({len(start_msg)} chars):")
            print(f"┌{'─' * 78}┐")
            for line in start_msg.split('\n'):
                print(f"│ {line:<76} │")
            print(f"└{'─' * 78}┘")
        else:
            print("❌ Failed to generate message")
        
        print()
    
    # Test stream end messages
    print()
    print("🏁 STREAM END MESSAGES")
    print("-" * 80)
    print()
    
    for i, test in enumerate(test_cases[:2], 1):  # Test just 2 to save API calls
        print(f"Test {i}: {test['name']}")
        print(f"Platform: {test['platform']} | Target: {test['social_platform']}")
        print(f"Title: {test['title']}")
        print()
        
        end_msg = generator.generate_stream_end_message(
            platform_name=test['platform'],
            username=test['username'],
            title=test['title'],
            social_platform=test['social_platform']
        )
        
        if end_msg:
            print(f"✨ Generated Message ({len(end_msg)} chars):")
            print(f"┌{'─' * 78}┐")
            for line in end_msg.split('\n'):
                print(f"│ {line:<76} │")
            print(f"└{'─' * 78}┘")
        else:
            print("❌ Failed to generate message")
        
        print()
    
    print("=" * 80)
    print("✅ Testing Complete!")
    print("=" * 80)
    
    # Test functions should not return values - just complete successfully

if __name__ == '__main__':
    try:
        success = test_prompt_outputs()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
