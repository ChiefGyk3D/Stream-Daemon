#!/usr/bin/env python3
"""
Test LLM + Social Media Integration
Tests AI message generation and posts samples to Bluesky and Mastodon
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_llm_generation():
    """Test LLM message generation"""
    print("="*60)
    print("Testing Google Gemini 2.5-Flash LLM")
    print("="*60)
    
    try:
        import google.genai
        
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key or api_key == 'your_gemini_api_key_here':
            print("✗ GEMINI_API_KEY not configured")
            print("\nSet it in .env file:")
            print("  GEMINI_API_KEY=AIzaSyA...")
            return None, None
        
        print(f"✓ API Key: {api_key[:10]}...{api_key[-4:]}")
        
        # Initialize client
        client = google.genai.Client(api_key=api_key)
        print("✓ Gemini client initialized")
        
        # Generate Bluesky message (300 char limit)
        print("\n" + "-"*60)
        print("📱 Generating Bluesky message (300 char limit)...")
        print("-"*60)
        
        bluesky_prompt = """Generate an exciting social media post announcing a livestream has just started.

Stream Details:
- Platform: Twitch
- Streamer: ChiefGYK3D
- Title: Testing Stream Daemon with AI Messages!
- URL: https://twitch.tv/chiefgyk3d

Requirements:
- Maximum 250 characters (excluding the URL which will be appended)
- Include 2-4 relevant hashtags
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
        
        # Truncate if needed
        if len(bluesky_msg) > 250:
            bluesky_msg = bluesky_msg[:247] + "..."
        
        bluesky_full = f"{bluesky_msg}\n\nhttps://twitch.tv/chiefgyk3d"
        
        print(f"Generated content ({len(bluesky_msg)} chars):")
        print(bluesky_msg)
        print(f"\nFull message with URL ({len(bluesky_full)}/300 chars):")
        print(bluesky_full)
        
                # Generate Mastodon message (500 char limit)
        print("\n" + "-"*60)
        print("🐘 Generating Mastodon message (500 char limit)...")
        print("-"*60)
        
        mastodon_prompt = """Generate an exciting social media post announcing a livestream has just started.

Stream Details:
- Platform: Twitch
- Streamer: ChiefGYK3D
- Title: Testing Stream Daemon with AI Messages!
- URL: https://twitch.tv/chiefgyk3d

Requirements:
- Maximum 450 characters (excluding the URL which will be appended)
- Include 2-4 relevant hashtags
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
        
        # Truncate if needed
        if len(mastodon_msg) > 450:
            mastodon_msg = mastodon_msg[:447] + "..."
        
        mastodon_full = f"{mastodon_msg}\n\nhttps://twitch.tv/chiefgyk3d"
        
        print(f"Generated content ({len(mastodon_msg)} chars):")
        print(mastodon_msg)
        print(f"\nFull message with URL ({len(mastodon_full)}/500 chars):")
        print(mastodon_full)
        
        print("\n✨ LLM generation successful!")
        return bluesky_full, mastodon_full
        
    except Exception as e:
        print(f"✗ LLM generation failed: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def test_bluesky_post(message):
    """Test posting to Bluesky"""
    print("\n" + "="*60)
    print("Testing Bluesky Post")
    print("="*60)
    
    try:
        from atproto import Client
        
        handle = os.getenv('BLUESKY_HANDLE')
        password = os.getenv('BLUESKY_APP_PASSWORD')
        
        if not handle or not password:
            print("✗ Bluesky credentials not configured")
            print("\nSet in .env file:")
            print("  BLUESKY_HANDLE=your_handle.bsky.social")
            print("  BLUESKY_APP_PASSWORD=your-app-password")
            return False
        
        print(f"✓ Handle: {handle}")
        print("✓ App password configured")
        
        # Login
        client = Client()
        client.login(handle, password)
        print("✓ Logged in to Bluesky")
        
        # Post message with clickable links using TextBuilder
        print(f"\n📤 Posting message ({len(message)} chars)...")
        print("-"*60)
        print(message)
        print("-"*60)
        
        # Use TextBuilder to make URLs clickable
        from atproto import client_utils, models
        import re
        
        text_builder = client_utils.TextBuilder()
        url_pattern = r'https?://[^\s]+'
        last_pos = 0
        first_url = None
        
        for match in re.finditer(url_pattern, message):
            # Add text before URL
            if match.start() > last_pos:
                text_builder.text(message[last_pos:match.start()])
            
            # Add URL as clickable link
            url = match.group()
            text_builder.link(url, url)
            
            # Capture first URL for embed card
            if first_url is None:
                first_url = url
            
            last_pos = match.end()
        
        # Add any remaining text after last URL
        if last_pos < len(message):
            text_builder.text(message[last_pos:])
        
        # Create embed card for the first URL if it's a Twitch link
        embed = None
        if first_url and 'twitch.tv/' in first_url:
            try:
                # Create simple embed card for Twitch
                embed = models.AppBskyEmbedExternal.Main(
                    external=models.AppBskyEmbedExternal.External(
                        uri=first_url,
                        title="🔴 Live on Twitch - ChiefGYK3D",
                        description="Testing Stream Daemon with AI Messages!",
                    )
                )
                print("✓ Created Twitch embed card")
            except Exception as e:
                print(f"⚠ Could not create embed: {e}")
        
        response = client.send_post(text_builder, embed=embed)
        print(f"✅ Posted to Bluesky!")
        print(f"   URI: {response.uri}")
        
        return True
        
    except Exception as e:
        print(f"✗ Bluesky post failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_mastodon_post(message):
    """Test posting to Mastodon"""
    print("\n" + "="*60)
    print("Testing Mastodon Post")
    print("="*60)
    
    try:
        from mastodon import Mastodon
        
        api_base_url = os.getenv('MASTODON_API_BASE_URL')
        access_token = os.getenv('MASTODON_ACCESS_TOKEN')
        
        if not api_base_url or not access_token:
            print("✗ Mastodon credentials not configured")
            print("\nSet in .env file:")
            print("  MASTODON_API_BASE_URL=https://your-instance.social")
            print("  MASTODON_ACCESS_TOKEN=your_access_token")
            return False
        
        print(f"✓ Instance: {api_base_url}")
        print("✓ Access token configured")
        
        # Initialize client
        mastodon = Mastodon(
            access_token=access_token,
            api_base_url=api_base_url
        )
        
        # Verify credentials
        account = mastodon.account_verify_credentials()
        print(f"✓ Logged in as: @{account['username']}")
        
        # Post message
        print(f"\n📤 Posting message ({len(message)} chars)...")
        print("-"*60)
        print(message)
        print("-"*60)
        
        status = mastodon.status_post(message, visibility='public')
        print(f"✅ Posted to Mastodon!")
        print(f"   URL: {status['url']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Mastodon post failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test flow"""
    print("\n" + "="*60)
    print("🤖 Stream Daemon - LLM + Social Media Test")
    print("="*60)
    print("\nThis will:")
    print("  1. Generate AI messages using Gemini 2.5-Flash")
    print("  2. Post test message to Bluesky")
    print("  3. Post test message to Mastodon")
    print("\n" + "="*60)
    
    input("\nPress Enter to continue or Ctrl+C to cancel...")
    
    # Test LLM
    bluesky_msg, mastodon_msg = test_llm_generation()
    
    if not bluesky_msg or not mastodon_msg:
        print("\n❌ LLM generation failed - cannot proceed with social media tests")
        return 1
    
    # Test Bluesky
    if os.getenv('BLUESKY_HANDLE'):
        bluesky_success = test_bluesky_post(bluesky_msg)
    else:
        print("\n⏭️  Skipping Bluesky (not configured)")
        bluesky_success = None
    
    # Test Mastodon
    if os.getenv('MASTODON_API_BASE_URL'):
        mastodon_success = test_mastodon_post(mastodon_msg)
    else:
        print("\n⏭️  Skipping Mastodon (not configured)")
        mastodon_success = None
    
    # Summary
    print("\n" + "="*60)
    print("📊 Test Summary")
    print("="*60)
    print(f"✅ LLM Generation: SUCCESS")
    
    if bluesky_success is not None:
        status = "✅ SUCCESS" if bluesky_success else "❌ FAILED"
        print(f"{status} Bluesky Post")
    else:
        print("⏭️  Bluesky: SKIPPED")
    
    if mastodon_success is not None:
        status = "✅ SUCCESS" if mastodon_success else "❌ FAILED"
        print(f"{status} Mastodon Post")
    else:
        print("⏭️  Mastodon: SKIPPED")
    
    print("="*60)
    
    # Return code
    if bluesky_success == False or mastodon_success == False:
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test cancelled by user")
        sys.exit(1)
