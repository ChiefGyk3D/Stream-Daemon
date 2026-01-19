#!/usr/bin/env python3
"""Test script for Ollama integration with Stream Daemon"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables from main .env file
load_dotenv()  # Loads from .env file

# Import Stream Daemon modules
from stream_daemon.ai.generator import AIMessageGenerator

# Check if Ollama is configured
def is_ollama_configured():
    """Check if Ollama is properly configured"""
    return (
        os.getenv('LLM_ENABLE', '').lower() == 'true' and
        os.getenv('LLM_PROVIDER', '').lower() == 'ollama' and
        os.getenv('LLM_OLLAMA_HOST') and
        os.getenv('LLM_MODEL')
    )

# Skip all tests if Ollama is not configured
pytestmark = pytest.mark.skipif(
    not is_ollama_configured(),
    reason="Ollama not configured (LLM_ENABLE=True, LLM_PROVIDER=ollama required)"
)

@pytest.fixture(scope="module")
def ai_generator():
    """Create AI generator instance for tests"""
    gen = AIMessageGenerator()
    return gen

def test_ollama_authentication(ai_generator):
    """Test 1: Initialize and authenticate Ollama connection"""
    print("\n" + "="*60)
    print("Test 1: Initialize Ollama Connection")
    print("="*60)
    
    assert ai_generator.authenticate(), "Failed to authenticate with Ollama server"
    
    print("✅ SUCCESS: Ollama connection initialized!")
    print(f"  Provider: {ai_generator.provider}")
    print(f"  Model: {ai_generator.model}")
    if hasattr(ai_generator, 'ollama_host'):
        print(f"  Host: {ai_generator.ollama_host}")

def test_generate_bluesky_message(ai_generator):
    """Test 2: Generate Stream Start Message (Bluesky)"""
    print("\n" + "="*60)
    print("Test 2: Generate Stream Start Message (Bluesky)")
    print("="*60)

    message = ai_generator.generate_stream_start_message(
        platform_name='Twitch',
        username='testuser',
        title='Testing Ollama Integration - Building Cool Stuff',
        url='https://twitch.tv/testuser',
        social_platform='bluesky'
    )
    
    assert message is not None, "Message generation returned None"
    assert len(message) > 0, "Message is empty"
    assert len(message) <= 300, f"Message too long for Bluesky ({len(message)} > 300)"
    
    print("✅ SUCCESS: Generated stream start message!")
    print(f"\n📝 Generated Message ({len(message)} chars):")
    print("-" * 60)
    print(message)
    print("-" * 60)

def test_generate_mastodon_message(ai_generator):
    """Test 3: Generate Stream Start Message (Mastodon)"""
    print("\n" + "="*60)
    print("Test 3: Generate Stream Start Message (Mastodon)")
    print("="*60)

    message = ai_generator.generate_stream_start_message(
        platform_name='YouTube',
        username='testuser',
        title='Live: Building an AI-Powered Stream Bot with Python',
        url='https://youtube.com/watch?v=testid',
        social_platform='mastodon'
    )
    
    assert message is not None, "Message generation returned None"
    assert len(message) > 0, "Message is empty"
    assert len(message) <= 500, f"Message too long for Mastodon ({len(message)} > 500)"
    
    print("✅ SUCCESS: Generated Mastodon message!")
    print(f"\n📝 Generated Message ({len(message)} chars):")
    print("-" * 60)
    print(message)
    print("-" * 60)

def test_generate_end_message(ai_generator):
    """Test 4: Generate Stream End Message"""
    print("\n" + "="*60)
    print("Test 4: Generate Stream End Message")
    print("="*60)

    message = ai_generator.generate_stream_end_message(
        platform_name='Twitch',
        username='testuser',
        title='Testing Ollama Integration - Building Cool Stuff',
        social_platform='bluesky'
    )
    
    assert message is not None, "Message generation returned None"
    assert len(message) > 0, "Message is empty"
    assert len(message) <= 300, f"Message too long for Bluesky ({len(message)} > 300)"
    
    print("✅ SUCCESS: Generated stream end message!")
    print(f"\n📝 Generated Message ({len(message)} chars):")
    print("-" * 60)
    print(message)
    print("-" * 60)

# Allow running as standalone script
if __name__ == '__main__':
    print("="*60)
    print("🧪 Stream Daemon Ollama Integration Test")
    print("="*60)
    
    if not is_ollama_configured():
        print("\n❌ Ollama is not configured!")
        print("  Set LLM_ENABLE=True, LLM_PROVIDER=ollama in your .env file")
        sys.exit(1)
    
    print("\n📋 Configuration:")
    print(f"  LLM_ENABLE: {os.getenv('LLM_ENABLE')}")
    print(f"  LLM_PROVIDER: {os.getenv('LLM_PROVIDER')}")
    print(f"  LLM_OLLAMA_HOST: {os.getenv('LLM_OLLAMA_HOST')}")
    print(f"  LLM_OLLAMA_PORT: {os.getenv('LLM_OLLAMA_PORT')}")
    print(f"  LLM_MODEL: {os.getenv('LLM_MODEL')}")
    
    # Run tests
    pytest.main([__file__, '-v', '-s'])
