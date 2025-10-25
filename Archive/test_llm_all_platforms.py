#!/usr/bin/env python3
"""
Test LLM Message Generation for All Configured Streaming Platforms
Tests Twitch, YouTube, and Kick with AI-generated messages
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_llm_for_platform(platform_name, username, title, url):
    """Test LLM generation for a specific platform"""
    print("\n" + "="*60)
    print(f"Testing {platform_name} - {username}")
    print("="*60)
    
    try:
        import google.genai
        
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            print("✗ GEMINI_API_KEY not configured")
            return False
        
        client = google.genai.Client(api_key=api_key)
        
        # Test Bluesky message (300 char limit)
        print(f"\n📱 Bluesky Message (300 chars):")
        print("-"*60)
        
        bluesky_prompt = f"""Generate an exciting social media post announcing a livestream has just started.

Stream Details:
- Platform: {platform_name}
- Streamer: {username}
- Title: {title}
- URL: {url}

Requirements:
- Maximum 250 characters (excluding the URL which will be appended)
- Include 2-4 relevant hashtags based on the stream title
- Enthusiastic and inviting tone
- Make people want to join the stream NOW
- DO NOT include the URL in your response (it will be added automatically)
- Keep it concise and punchy

Generate ONLY the message text with hashtags, nothing else."""

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=bluesky_prompt
        )
        bluesky_msg = response.text.strip()
        
        if len(bluesky_msg) > 250:
            bluesky_msg = bluesky_msg[:247] + "..."
        
        bluesky_full = f"{bluesky_msg}\n\n{url}"
        print(f"Content: {len(bluesky_msg)} chars")
        print(bluesky_msg)
        print(f"\nWith URL: {len(bluesky_full)}/300 chars")
        print(bluesky_full)
        
        # Test Mastodon message (500 char limit)
        print(f"\n🐘 Mastodon Message (500 chars):")
        print("-"*60)
        
        mastodon_prompt = f"""Generate an exciting social media post announcing a livestream has just started.

Stream Details:
- Platform: {platform_name}
- Streamer: {username}
- Title: {title}
- URL: {url}

Requirements:
- Maximum 450 characters (excluding the URL which will be appended)
- Include 2-4 relevant hashtags based on the stream title
- Enthusiastic and inviting tone
- More detailed than a short post - use the extra space!
- Make people want to join the stream NOW
- DO NOT include the URL in your response (it will be added automatically)

Generate ONLY the message text with hashtags, nothing else."""

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=mastodon_prompt
        )
        mastodon_msg = response.text.strip()
        
        if len(mastodon_msg) > 450:
            mastodon_msg = mastodon_msg[:447] + "..."
        
        mastodon_full = f"{mastodon_msg}\n\n{url}"
        print(f"Content: {len(mastodon_msg)} chars")
        print(mastodon_msg)
        print(f"\nWith URL: {len(mastodon_full)}/500 chars")
        print(mastodon_full)
        
        # Test Stream End message
        print(f"\n🔚 Stream End Message (500 chars):")
        print("-"*60)
        
        end_prompt = f"""Generate a warm, thankful social media post announcing a livestream has ended.

Stream Details:
- Platform: {platform_name}
- Streamer: {username}
- Title: {title}

Requirements:
- Maximum 500 characters
- Thank viewers for joining
- Include 1-3 relevant hashtags based on the stream title
- Grateful and friendly tone
- Encourage them to catch the next stream
- Keep it concise and heartfelt

Generate ONLY the message text with hashtags, nothing else."""

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=end_prompt
        )
        end_msg = response.text.strip()
        
        if len(end_msg) > 500:
            end_msg = end_msg[:497] + "..."
        
        print(f"Length: {len(end_msg)}/500 chars")
        print(end_msg)
        
        print("\n✅ All messages generated successfully!")
        return True
        
    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test flow"""
    print("="*60)
    print("🤖 Multi-Platform LLM Message Generation Test")
    print("="*60)
    print("\nTesting AI message generation for all configured platforms")
    print("="*60)
    
    results = {}
    
    # Test Twitch
    twitch_username = os.getenv('TWITCH_USERNAME')
    if twitch_username:
        print(f"\n✓ Twitch configured: {twitch_username}")
        url = f"https://twitch.tv/{twitch_username.lower()}"
        title = "Epic Gaming Marathon - Testing AI Stream Announcements!"
        results['Twitch'] = test_llm_for_platform('Twitch', twitch_username, title, url)
    else:
        print("\n⏭️  Twitch not configured (TWITCH_USERNAME not set)")
    
    # Test YouTube
    youtube_username = os.getenv('YOUTUBE_USERNAME')
    youtube_channel_id = os.getenv('YOUTUBE_CHANNEL_ID')
    if youtube_username or youtube_channel_id:
        display_name = youtube_username or youtube_channel_id
        print(f"\n✓ YouTube configured: {display_name}")
        
        if youtube_channel_id:
            url = f"https://youtube.com/channel/{youtube_channel_id}/live"
        else:
            url = f"https://youtube.com/@{youtube_username}/live"
        
        title = "Live Coding Session - Building with AI and Automation!"
        results['YouTube'] = test_llm_for_platform('YouTube', display_name, title, url)
    else:
        print("\n⏭️  YouTube not configured (YOUTUBE_USERNAME or YOUTUBE_CHANNEL_ID not set)")
    
    # Test Kick
    kick_username = os.getenv('KICK_USERNAME')
    if kick_username:
        print(f"\n✓ Kick configured: {kick_username}")
        url = f"https://kick.com/{kick_username.lower()}"
        title = "Just Chatting - Tech Talk and Community Hangout!"
        results['Kick'] = test_llm_for_platform('Kick', kick_username, title, url)
    else:
        print("\n⏭️  Kick not configured (KICK_USERNAME not set)")
    
    # Summary
    print("\n" + "="*60)
    print("📊 Test Summary")
    print("="*60)
    
    if not results:
        print("❌ No streaming platforms configured!")
        print("\nSet usernames in .env file:")
        print("  TWITCH_USERNAME=your_username")
        print("  YOUTUBE_USERNAME=@YourChannel")
        print("  KICK_USERNAME=your_username")
        return 1
    
    for platform, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{status}: {platform}")
    
    print("="*60)
    
    # Return code
    if all(results.values()):
        print("\n🎉 All platforms tested successfully!")
        print("\nThe LLM will generate unique, engaging messages for:")
        for platform in results.keys():
            print(f"  • {platform}")
        print("\nTo enable in production, set LLM_ENABLE=True in Doppler")
        return 0
    else:
        print("\n⚠️  Some tests failed - check errors above")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test cancelled by user")
        sys.exit(1)
