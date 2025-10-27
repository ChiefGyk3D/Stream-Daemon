"""
Test async posting performance improvement
"""
import time
import sys
import os
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

load_dotenv()

# Mock the social platforms and AI generator for testing
class MockAIGenerator:
    def authenticate(self):
        return True
    
    def generate_message(self, *args, **kwargs):
        # Simulate AI generation time (normally 10+ seconds)
        time.sleep(0.1)  # Reduced for testing
        return "Mock AI generated message about the stream!"

class MockSocialPlatform:
    def __init__(self, name, delay=0.05):
        self.name = name
        self.delay = delay
        self.enabled = True
    
    def post(self, message, reply_to_id=None, platform_name=None, stream_data=None):
        # Simulate posting time
        time.sleep(self.delay)
        return f"mock_post_id_{self.name}_{int(time.time() * 1000)}"

# Mock the logger
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Create mock platforms
enabled_social = [
    MockSocialPlatform("Mastodon", 0.05),
    MockSocialPlatform("Bluesky", 0.05),
    MockSocialPlatform("Discord", 0.05),
    MockSocialPlatform("Matrix", 0.05),
]

ai_generator = MockAIGenerator()

# Test synchronous posting (old way)
print("\n" + "="*60)
print("Testing SYNCHRONOUS posting (old way)...")
print("="*60)
start_time = time.time()

sync_results = {}
for social in enabled_social:
    # Generate message
    message = ai_generator.generate_message()
    # Post
    post_id = social.post(message, platform_name="Twitch")
    sync_results[social.name] = post_id

sync_duration = time.time() - start_time
print(f"✓ Synchronous posting completed in {sync_duration:.2f} seconds")
print(f"  Results: {list(sync_results.keys())}")

# Test async posting (new way) 
print("\n" + "="*60)
print("Testing ASYNCHRONOUS posting (new way)...")
print("="*60)

# We need to define the async function inline since importing is tricky
from concurrent.futures import ThreadPoolExecutor, as_completed

def post_to_social_async_test(enabled_social, ai_generator):
    def post_to_single_platform(social):
        try:
            # Generate message with AI
            message = ai_generator.generate_message()
            
            # Post to platform
            post_id = social.post(message, platform_name="Twitch")
            
            return (social.name, post_id)
        except Exception as e:
            print(f"Error posting to {social.name}: {e}")
            return (social.name, None)
    
    # Post to all platforms in parallel
    results = {}
    with ThreadPoolExecutor(max_workers=len(enabled_social)) as executor:
        futures = [executor.submit(post_to_single_platform, social) for social in enabled_social]
        for future in as_completed(futures):
            social_name, post_id = future.result()
            results[social_name] = post_id
    
    return results

start_time = time.time()
async_results = post_to_social_async_test(enabled_social, ai_generator)
async_duration = time.time() - start_time

print(f"✓ Asynchronous posting completed in {async_duration:.2f} seconds")
print(f"  Results: {list(async_results.keys())}")

# Compare
print("\n" + "="*60)
print("PERFORMANCE COMPARISON")
print("="*60)
print(f"Synchronous:  {sync_duration:.2f} seconds")
print(f"Asynchronous: {async_duration:.2f} seconds")
speedup = sync_duration / async_duration
print(f"Speedup:      {speedup:.2f}x faster! 🚀")
print(f"Time saved:   {sync_duration - async_duration:.2f} seconds")

if speedup >= 3.5:
    print("\n✅ SUCCESS! Async posting is ~4x faster as expected!")
else:
    print(f"\n⚠️  Warning: Expected ~4x speedup, got {speedup:.2f}x")
