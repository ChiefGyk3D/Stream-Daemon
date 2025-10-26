#!/usr/bin/env python3
"""
Simulate 2 check cycles to test debouncing and posting

NOTE: This test is currently disabled because the streaming platforms
      are not yet refactored from stream-daemon.py into separate modules.
      Enable this test after completing the refactoring.
"""

import pytest

pytestmark = pytest.mark.skip(reason="Test uses old monolithic stream-daemon.py structure")

# Test code kept for reference after refactoring is complete
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import importlib.util
from dataclasses import dataclass, field
from typing import Optional, Dict
from datetime import datetime
from enum import Enum

# Load the stream daemon module
spec = importlib.util.spec_from_file_location('stream_daemon', 'stream-daemon.py')
stream_daemon = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stream_daemon)

print("="*60)
print("SIMULATING 2 CHECK CYCLES (DEBOUNCING TEST)")
print("="*60)

# Create stream status trackers
statuses = {}

platforms = {
    'Twitch': ('lilypita', stream_daemon.TwitchPlatform()),
    'YouTube': ('Hyphonix', stream_daemon.YouTubePlatform()),
    'Kick': ('daletanhardt', stream_daemon.KickPlatform())
}

# Authenticate all platforms
for name, (username, platform) in platforms.items():
    if platform.authenticate():
        statuses[name] = stream_daemon.StreamStatus(
            platform_name=name,
            username=username
        )
        print(f"✓ {name} authenticated")

print("\n" + "="*60)
print("CHECK CYCLE 1 (Initial)")
print("="*60)

for name, (username, platform) in platforms.items():
    status = statuses[name]
    is_live, data = platform.is_live(username)
    
    print(f"\n{name}/{username}:")
    print(f"  API says: {'LIVE' if is_live else 'OFFLINE'}")
    if data:
        print(f"  Title: {data.get('title', 'N/A')}")
    
    state_changed = status.update(is_live, data.get('title') if data else None)
    print(f"  State: {status.state.value}")
    print(f"  Consecutive live checks: {status.consecutive_live_checks}")
    print(f"  State changed: {state_changed}")

"""
print("\n" + "="*60)
print("CHECK CYCLE 2 (Debouncing confirmation)")
print("="*60)

for name, (username, platform) in platforms.items():
    status = statuses[name]
    is_live, data = platform.is_live(username)
    
    print(f"\n{name}/{username}:")
    print(f"  API says: {'LIVE' if is_live else 'OFFLINE'}")
    
    state_changed = status.update(is_live, data.get('title') if data else None)
    print(f"  State: {status.state.value}")
    print(f"  Consecutive live checks: {status.consecutive_live_checks}")
    print(f"  State changed: {state_changed}")
    
    if state_changed:
        print(f"  🔴 WOULD TRIGGER POSTING NOW!")

print("\n" + "="*60)
print("SUMMARY")
print("="*60)

live_count = sum(1 for s in statuses.values() if s.state == stream_daemon.StreamState.LIVE)
print(f"Streams in LIVE state: {live_count}/{len(statuses)}")

for name, status in statuses.items():
    print(f"  {name}: {status.state.value}")
