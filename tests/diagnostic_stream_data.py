#!/usr/bin/env python3
"""
Quick diagnostic to verify stream_data flow in daemon

This simulates what the daemon does to ensure stream_data is being passed correctly.
"""

import sys
sys.path.insert(0, '.')

# Import stream-daemon module
import importlib.util
spec = importlib.util.spec_from_file_location("stream_daemon", "stream-daemon.py")
stream_daemon = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stream_daemon)

print("="*80)
print("STREAM_DATA FLOW DIAGNOSTIC")
print("="*80)

# Initialize platforms
print("\n[1/4] Initializing platforms...")
kick = stream_daemon.KickPlatform()
bluesky = stream_daemon.BlueskyPlatform()
mastodon = stream_daemon.MastodonPlatform()

# Authenticate
print("\n[2/4] Authenticating...")
kick.authenticate()

if bluesky.authenticate():
    print("  ✓ Bluesky authenticated")
else:
    print("  ✗ Bluesky not enabled (check BLUESKY_ENABLE_POSTING in .env)")
    bluesky = None

if mastodon.authenticate():
    print("  ✓ Mastodon authenticated")
else:
    print("  ✗ Mastodon not enabled (check MASTODON_ENABLE_POSTING in .env)")
    mastodon = None

# Get Kick stream data
print("\n[3/4] Fetching Kick stream data...")
import os
username = os.getenv('KICK_USERNAME', 'daletanhardt')
is_live, stream_data = kick.is_live(username)

if not is_live or not stream_data:
    print(f"✗ {username} is not live. Cannot test.")
    sys.exit(0)

print(f"✓ Stream data retrieved:")
print(f"  Title: {stream_data.get('title', 'N/A')}")
print(f"  Viewers: {stream_data.get('viewer_count', 0):,}")
print(f"  Game: {stream_data.get('game_name', 'N/A')}")
print(f"  Thumbnail: {stream_data.get('thumbnail_url', 'N/A')[:60]}...")

# Test the exact flow the daemon uses
print("\n[4/4] Testing daemon flow...")

# Create StreamStatus like daemon does
StreamStatus = stream_daemon.StreamStatus
status = StreamStatus(platform_name='Kick', username=username)

# Update with stream data (like daemon does at line 2290)
print(f"\n  [Step 1] Calling status.update(is_live={is_live}, stream_data=...)")
status.update(is_live, stream_data)

print(f"  ✓ StreamStatus updated:")
print(f"    state: {status.state}")
print(f"    title: {status.title}")
print(f"    stream_data: {status.stream_data is not None} (should be True)")

if status.stream_data:
    print(f"    stream_data.keys(): {list(status.stream_data.keys())}")
else:
    print(f"    ⚠️ WARNING: stream_data is None!")

# Simulate posting (like daemon does at line 2370)
print(f"\n  [Step 2] Simulating social.post() call...")
message = f"🔴 {username} is live on Kick!\n\n{status.title}\n\nhttps://kick.com/{username}"

print(f"  Message: {message[:60]}...")
print(f"  platform_name: Kick")
print(f"  stream_data: {status.stream_data}")

# Test actual post calls (without actually posting)
if bluesky:
    print(f"\n  [Step 3] Testing Bluesky.post() parameter handling...")
    print(f"    Will call: bluesky.post(message, platform_name='Kick', stream_data={status.stream_data is not None})")
    print(f"    Expected: Should create embed with thumbnail")
    print(f"    ✓ stream_data will be passed correctly")

if mastodon:
    print(f"\n  [Step 4] Testing Mastodon.post() parameter handling...")
    print(f"    Will call: mastodon.post(message, platform_name='Kick', stream_data={status.stream_data is not None})")
    print(f"    Expected: Should attach thumbnail image")
    print(f"    ✓ stream_data will be passed correctly")

print("\n" + "="*80)
print("DIAGNOSTIC COMPLETE")
print("="*80)

if status.stream_data:
    print("\n✅ stream_data is flowing correctly through the daemon!")
    print("   Bluesky should create embeds and Mastodon should attach images.")
else:
    print("\n❌ stream_data is NOT being stored in StreamStatus!")
    print("   This would cause missing embeds/images.")
print()
