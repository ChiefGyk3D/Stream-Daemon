#!/usr/bin/env python3
"""
Test debouncing with 2 consecutive checks to verify stream_data storage
"""

import sys
sys.path.insert(0, '.')

import importlib.util
spec = importlib.util.spec_from_file_location("stream_daemon", "stream-daemon.py")
stream_daemon = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stream_daemon)

print("="*80)
print("DEBOUNCING TEST WITH stream_data")
print("="*80)

# Initialize
kick = stream_daemon.KickPlatform()
kick.authenticate()

import os
username = os.getenv('KICK_USERNAME', 'daletanhardt')

# Create status
StreamStatus = stream_daemon.StreamStatus
status = StreamStatus(platform_name='Kick', username=username)

print(f"\n📊 Initial state:")
print(f"  state: {status.state}")
print(f"  consecutive_live_checks: {status.consecutive_live_checks}")
print(f"  stream_data: {status.stream_data}")

# First check
print(f"\n[CHECK 1] Calling is_live()...")
is_live_1, stream_data_1 = kick.is_live(username)
print(f"  is_live: {is_live_1}")
print(f"  stream_data: {stream_data_1 is not None}")

if is_live_1:
    print(f"\n[CHECK 1] Calling status.update()...")
    state_changed_1 = status.update(is_live_1, stream_data_1)
    print(f"  state_changed: {state_changed_1}")
    print(f"  state: {status.state}")
    print(f"  consecutive_live_checks: {status.consecutive_live_checks}")
    print(f"  stream_data: {status.stream_data is not None} - {status.stream_data}")

# Second check (simulating next daemon cycle)
print(f"\n[CHECK 2] Calling is_live() again...")
is_live_2, stream_data_2 = kick.is_live(username)
print(f"  is_live: {is_live_2}")
print(f"  stream_data: {stream_data_2 is not None}")

if is_live_2:
    print(f"\n[CHECK 2] Calling status.update()...")
    state_changed_2 = status.update(is_live_2, stream_data_2)
    print(f"  state_changed: {state_changed_2}")
    print(f"  state: {status.state}")
    print(f"  consecutive_live_checks: {status.consecutive_live_checks}")
    print(f"  stream_data: {status.stream_data is not None} - Should be True")
    
    if status.stream_data:
        print(f"\n✅ SUCCESS! stream_data stored after 2nd check:")
        print(f"  title: {status.stream_data.get('title', 'N/A')[:50]}")
        print(f"  viewers: {status.stream_data.get('viewer_count', 0)}")
        print(f"  thumbnail: {status.stream_data.get('thumbnail_url', 'N/A')[:60]}")
    else:
        print(f"\n❌ FAILURE! stream_data is still None after 2nd check")

print("\n" + "="*80)
