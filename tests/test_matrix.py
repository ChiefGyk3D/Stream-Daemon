#!/usr/bin/env python3
"""
Matrix Platform Test

Tests Matrix authentication and message posting functionality.
Verifies:
- Matrix credentials are configured
- Connection to homeserver works
- Room access is valid
- Message posting succeeds
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Matrix platform
import importlib.util
spec = importlib.util.spec_from_file_location(
    "stream_daemon",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "stream-daemon.py")
)
stream_daemon = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stream_daemon)

MatrixPlatform = stream_daemon.MatrixPlatform

print("=" * 80)
print("MATRIX PLATFORM TEST")
print("=" * 80)
print()

# Check if Matrix is enabled
matrix_enabled = os.getenv('MATRIX_ENABLE_POSTING', 'False').lower() in ['true', '1', 't', 'y', 'yes']

if not matrix_enabled:
    print("❌ Matrix posting is DISABLED")
    print()
    print("To enable Matrix:")
    print("  1. Set MATRIX_ENABLE_POSTING=True in .env")
    print("  2. Configure Matrix credentials (see docs/MATRIX_SETUP.md)")
    print()
    sys.exit(1)

print("✓ Matrix posting is enabled")
print()

# Initialize Matrix platform
print("[1/3] Initializing Matrix platform...")
matrix = MatrixPlatform()

# Authenticate
print("[2/3] Authenticating with Matrix...")
print()

success = matrix.authenticate()

if not success:
    print("❌ Matrix authentication FAILED")
    print()
    print("Missing credentials. Check your .env or secrets manager:")
    print()
    
    # Check what's missing
    homeserver = os.getenv('MATRIX_HOMESERVER')
    access_token = os.getenv('MATRIX_ACCESS_TOKEN')
    room_id = os.getenv('MATRIX_ROOM_ID')
    
    def mask(val):
        if not val:
            return "❌ NOT SET"
        if len(val) <= 8:
            return "****"
        return f"{val[:4]}...{val[-4:]}"
    
    print(f"  MATRIX_HOMESERVER:    {homeserver or '❌ NOT SET'}")
    print(f"  MATRIX_ACCESS_TOKEN:  {mask(access_token)}")
    print(f"  MATRIX_ROOM_ID:       {room_id or '❌ NOT SET'}")
    print()
    print("📖 See docs/MATRIX_SETUP.md for setup instructions")
    print()
    sys.exit(1)

print("✅ Matrix authenticated successfully!")
print()
print(f"   Homeserver: {matrix.homeserver}")
print(f"   Room ID:    {matrix.room_id}")
print(f"   Token:      {matrix.access_token[:10]}...{matrix.access_token[-10:]}")
print()

# Test message posting
print("[3/3] Testing message posting...")
print()

test_messages = [
    {
        "platform": "Twitch",
        "message": "🟣 chiefgyk3d is live on Twitch!\nTest Stream Title\nhttps://twitch.tv/chiefgyk3d"
    },
    {
        "platform": "YouTube",
        "message": "🔴 grndpagaming is live on YouTube!\nGaming Stream Test\nhttps://youtube.com/grndpagaming/live"
    },
    {
        "platform": "Kick",
        "message": "🟢 asmongold is live on Kick!\nKick Stream Test\nhttps://kick.com/asmongold"
    }
]

print("Posting test messages to Matrix room...")
print("-" * 80)
print()

posted_events = []

for i, test in enumerate(test_messages, 1):
    print(f"[{i}/3] Posting {test['platform']} notification...")
    
    event_id = matrix.post(test['message'], platform_name=test['platform'])
    
    if event_id:
        print(f"  ✅ Posted successfully!")
        print(f"     Event ID: {event_id}")
        posted_events.append(event_id)
    else:
        print(f"  ❌ Failed to post")
    
    print()
    
    # Small delay between posts
    if i < len(test_messages):
        import time
        time.sleep(1)

print("=" * 80)
print("TEST SUMMARY")
print("=" * 80)
print()

if posted_events:
    print(f"✅ Successfully posted {len(posted_events)}/{len(test_messages)} messages")
    print()
    print("📱 Check your Matrix room to see the notifications!")
    print()
    print("Expected to see:")
    print("  • Platform-specific emojis (🟣/🔴/🟢)")
    print("  • Bold platform headers")
    print("  • Clickable stream URLs")
    print("  • HTML formatted messages")
    print()
else:
    print("❌ No messages were posted successfully")
    print()
    print("Troubleshooting:")
    print("  1. Verify room ID is correct")
    print("  2. Check if bot/user is member of room")
    print("  3. Verify access token is valid")
    print("  4. Check homeserver URL is correct")
    print("  5. See docs/MATRIX_SETUP.md for detailed setup")
    print()

print("=" * 80)
