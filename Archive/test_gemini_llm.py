#!/usr/bin/env python3
"""
Test Google Gemini LLM Integration
Quick test to verify AI message generation works
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_import():
    """Test that google-genai can be imported"""
    print("Testing import...")
    try:
        import google.genai
        print("✓ google.genai imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Failed to import google.genai: {e}")
        print("\nRun: pip install google-genai")
        return False

def test_api_key():
    """Test that API key is configured"""
    print("\nTesting API key configuration...")
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("✗ GEMINI_API_KEY not found in environment")
        print("\nSet it with:")
        print("  export GEMINI_API_KEY='your_key_here'")
        print("  or add to .env file")
        return False
    
    if api_key == "your_gemini_api_key_here":
        print("⚠ GEMINI_API_KEY is still the placeholder value")
        print("\nGet your API key from:")
        print("  https://aistudio.google.com/app/apikey")
        return False
    
    print(f"✓ GEMINI_API_KEY found: {api_key[:10]}...{api_key[-4:]}")
    return True

def test_connection():
    """Test connection to Gemini API"""
    print("\nTesting Gemini API connection...")
    
    try:
        import google.genai
        
        api_key = os.getenv('GEMINI_API_KEY')
        client = google.genai.Client(api_key=api_key)
        
        print("✓ Gemini client initialized")
        
        # Simple test generation
        print("\nTesting message generation...")
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents="Say 'Hello from Gemini!' and nothing else"
        )
        print(f"✓ API Response: {response.text}")
        
        return True
        
    except Exception as e:
        print(f"✗ Failed to connect to Gemini API: {e}")
        return False

def test_message_generation():
    """Test realistic stream message generation"""
    print("\n" + "="*60)
    print("Testing Stream Message Generation")
    print("="*60)
    
    try:
        import google.genai
        
        api_key = os.getenv('GEMINI_API_KEY')
        client = google.genai.Client(api_key=api_key)
        
        # Test stream start message
        print("\n📢 Generating STREAM START message (Bluesky - 300 chars)...")
        prompt = """Generate an exciting social media post announcing a livestream has just started.

Stream Details:
- Platform: Twitch
- Streamer: ChiefGYK3D
- Title: Elden Ring Boss Rush Challenge
- URL: https://twitch.tv/chiefgyk3d

Requirements:
- Maximum 270 characters (excluding the URL which will be appended)
- Include 2-4 relevant hashtags based on the stream title
- Enthusiastic and inviting tone
- Make people want to join the stream NOW
- DO NOT include the URL in your response (it will be added automatically)
- Keep it concise and punchy

Generate ONLY the message text with hashtags, nothing else."""

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        message = response.text.strip()
        full_message = f"{message}\n\nhttps://twitch.tv/chiefgyk3d"
        
        print(f"\nGenerated Message ({len(full_message)}/300 chars):")
        print("-" * 60)
        print(full_message)
        print("-" * 60)
        
        if len(full_message) > 300:
            print(f"⚠ Message too long ({len(full_message)} chars), would be truncated")
        else:
            print(f"✓ Message fits within Bluesky limit")
        
        # Test stream end message
        print("\n📢 Generating STREAM END message (Mastodon - 500 chars)...")
        prompt = """Generate a warm social media post announcing a livestream has ended.

Stream Details:
- Platform: Twitch
- Streamer: ChiefGYK3D
- Title: Elden Ring Boss Rush Challenge

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
            contents=prompt
        )
        message = response.text.strip()
        
        print(f"\nGenerated Message ({len(message)}/500 chars):")
        print("-" * 60)
        print(message)
        print("-" * 60)
        
        if len(message) > 500:
            print(f"⚠ Message too long ({len(message)} chars), would be truncated")
        else:
            print(f"✓ Message fits within Mastodon limit")
        
        return True
        
    except Exception as e:
        print(f"✗ Failed to generate messages: {e}")
        return False

def main():
    """Run all tests"""
    print("="*60)
    print("Google Gemini LLM Integration Test")
    print("="*60)
    
    # Load .env if available
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✓ Loaded .env file")
    except ImportError:
        print("⚠ python-dotenv not installed, using environment variables only")
    
    print()
    
    # Run tests
    tests = [
        ("Import Test", test_import),
        ("API Key Test", test_api_key),
        ("Connection Test", test_connection),
        ("Message Generation Test", test_message_generation)
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n✗ {test_name} crashed: {e}")
            results[test_name] = False
        
        # Stop if critical test fails
        if not results[test_name] and test_name in ["Import Test", "API Key Test"]:
            print(f"\n⚠ Stopping tests - {test_name} failed (required for remaining tests)")
            break
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 All tests passed! Gemini integration is working!")
        print("\nYou can now:")
        print("  1. Set LLM_ENABLE=True in .env or Doppler")
        print("  2. Start the stream daemon")
        print("  3. Enjoy AI-generated stream announcements! ✨")
    else:
        print("⚠ Some tests failed. Fix the issues above before enabling LLM.")
        print("\nQuick fixes:")
        print("  • Missing import: pip install google-generativeai")
        print("  • Missing API key: Get from https://aistudio.google.com/app/apikey")
        print("  • Invalid API key: Create a new one at the URL above")
    print("="*60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
