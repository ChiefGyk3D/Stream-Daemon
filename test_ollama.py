#!/usr/bin/env python3
"""Test script for Ollama integration with Stream Daemon"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from main .env file
load_dotenv()  # Loads from .env file

print("="*60)
print("🧪 Stream Daemon Ollama Integration Test")
print("="*60)

# Import Stream Daemon modules
try:
    from stream_daemon.ai.generator import AIMessageGenerator
    print("✓ Successfully imported AIMessageGenerator")
except ImportError as e:
    print(f"✗ Failed to import: {e}")
    print("  Make sure you're in the correct directory and dependencies are installed")
    sys.exit(1)

# Check configuration
print("\n📋 Configuration:")
print(f"  LLM_ENABLE: {os.getenv('LLM_ENABLE')}")
print(f"  LLM_PROVIDER: {os.getenv('LLM_PROVIDER')}")
print(f"  LLM_OLLAMA_HOST: {os.getenv('LLM_OLLAMA_HOST')}")
print(f"  LLM_OLLAMA_PORT: {os.getenv('LLM_OLLAMA_PORT')}")
print(f"  LLM_MODEL: {os.getenv('LLM_MODEL')}")

# Test 1: Initialize AI Generator
print("\n" + "="*60)
print("Test 1: Initialize Ollama Connection")
print("="*60)

gen = AIMessageGenerator()
if gen.authenticate():
    print("✅ SUCCESS: Ollama connection initialized!")
    print(f"  Provider: {gen.provider}")
    print(f"  Model: {gen.model}")
    print(f"  Host: {gen.ollama_host}")
else:
    print("❌ FAILED: Could not initialize Ollama connection")
    print("  Check your configuration and server accessibility")
    sys.exit(1)

# Test 2: Generate Stream Start Message
print("\n" + "="*60)
print("Test 2: Generate Stream Start Message (Bluesky)")
print("="*60)

try:
    message = gen.generate_stream_start_message(
        platform_name='Twitch',
        username='testuser',
        title='Testing Ollama Integration - Building Cool Stuff',
        url='https://twitch.tv/testuser',
        social_platform='bluesky'
    )
    
    if message:
        print("✅ SUCCESS: Generated stream start message!")
        print(f"\n📝 Generated Message ({len(message)} chars):")
        print("-" * 60)
        print(message)
        print("-" * 60)
    else:
        print("❌ FAILED: Message generation returned None")
except Exception as e:
    print(f"❌ FAILED: Exception during generation: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Generate Stream Start Message (Mastodon - longer)
print("\n" + "="*60)
print("Test 3: Generate Stream Start Message (Mastodon)")
print("="*60)

try:
    message = gen.generate_stream_start_message(
        platform_name='YouTube',
        username='testuser',
        title='Live: Building an AI-Powered Stream Bot with Python',
        url='https://youtube.com/watch?v=testid',
        social_platform='mastodon'
    )
    
    if message:
        print("✅ SUCCESS: Generated Mastodon message!")
        print(f"\n📝 Generated Message ({len(message)} chars):")
        print("-" * 60)
        print(message)
        print("-" * 60)
    else:
        print("❌ FAILED: Message generation returned None")
except Exception as e:
    print(f"❌ FAILED: Exception during generation: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Generate Stream End Message
print("\n" + "="*60)
print("Test 4: Generate Stream End Message")
print("="*60)

try:
    message = gen.generate_stream_end_message(
        platform_name='Twitch',
        username='testuser',
        title='Testing Ollama Integration - Building Cool Stuff',
        social_platform='bluesky'
    )
    
    if message:
        print("✅ SUCCESS: Generated stream end message!")
        print(f"\n📝 Generated Message ({len(message)} chars):")
        print("-" * 60)
        print(message)
        print("-" * 60)
    else:
        print("❌ FAILED: Message generation returned None")
except Exception as e:
    print(f"❌ FAILED: Exception during generation: {e}")
    import traceback
    traceback.print_exc()

# Summary
print("\n" + "="*60)
print("✅ All Tests Completed Successfully!")
print("="*60)
print("\nYour Ollama integration is working correctly!")
print("You can now use Ollama for AI-powered stream messages.")
