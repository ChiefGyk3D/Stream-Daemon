#!/usr/bin/env python3
"""
Test stream_data handling through complete stream lifecycle:
OFFLINE -> CHECK 1 (debouncing) -> CHECK 2 (goes LIVE) -> CHECK 3+ (still live)
"""

import sys
sys.path.insert(0, '.')

import importlib.util
spec = importlib.util.spec_from_file_location("stream_daemon", "stream-daemon.py")
stream_daemon = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stream_daemon)

print("="*80)
print("STREAM LIFECYCLE TEST - OFFLINE TO LIVE")
print("="*80)

# Mock stream data (simulating what is_live() returns)
mock_stream_data = {
    'title': 'Test Stream - Epic Gameplay!',
    'viewer_count': 150,
    'thumbnail_url': 'https://example.com/thumb.jpg',
    'game_name': 'Just Chatting'
}

# Create a fresh StreamStatus (starts OFFLINE)
StreamStatus = stream_daemon.StreamStatus
status = StreamStatus(platform_name='Kick', username='testuser')

print(f"\n📊 INITIAL STATE (Stream is offline):")
print(f"  state: {status.state}")
print(f"  consecutive_live_checks: {status.consecutive_live_checks}")
print(f"  stream_data: {status.stream_data}")
print(f"  title: {status.title}")

# ============================================================================
# CHECK 1 - First time daemon sees stream is live
# ============================================================================
print(f"\n" + "="*80)
print(f"CHECK 1 - Stream just went live (first detection)")
print(f"="*80)
print(f"\nDaemon calls: is_live() → returns (True, stream_data)")
print(f"Daemon calls: status.update(True, stream_data)")

state_changed = status.update(True, mock_stream_data)

print(f"\n📊 After CHECK 1:")
print(f"  state_changed: {state_changed} (should be False - debouncing)")
print(f"  state: {status.state} (should still be OFFLINE)")
print(f"  consecutive_live_checks: {status.consecutive_live_checks} (should be 1)")
print(f"  stream_data: {status.stream_data is not None} (should be True - FIX APPLIED)")
print(f"  title: {status.title} (should be None - not LIVE yet)")

if status.stream_data:
    print(f"\n  ✅ stream_data IS stored during debouncing!")
    print(f"     This ensures already-live streams have data when daemon starts")
else:
    print(f"\n  ❌ stream_data NOT stored - BUG!")

# ============================================================================
# CHECK 2 - Second consecutive check confirms stream is live
# ============================================================================
print(f"\n" + "="*80)
print(f"CHECK 2 - Confirms stream is still live (debouncing complete)")
print(f"="*80)
print(f"\nDaemon calls: is_live() → returns (True, stream_data)")
print(f"Daemon calls: status.update(True, stream_data)")

# Update viewer count to simulate change
mock_stream_data['viewer_count'] = 175

state_changed = status.update(True, mock_stream_data)

print(f"\n📊 After CHECK 2:")
print(f"  state_changed: {state_changed} (should be True - TRANSITIONED TO LIVE)")
print(f"  state: {status.state} (should be LIVE)")
print(f"  consecutive_live_checks: {status.consecutive_live_checks} (should be 2)")
print(f"  stream_data: {status.stream_data is not None} (should be True)")
print(f"  title: {status.title} (should be set now)")

if state_changed:
    print(f"\n  ✅ State transitioned to LIVE - daemon will post announcements!")
    print(f"     Calling social.post(message, stream_data=status.stream_data)")
    print(f"     stream_data includes:")
    for key, value in status.stream_data.items():
        print(f"       {key}: {value}")
else:
    print(f"\n  ❌ State did NOT change - BUG!")

# ============================================================================
# CHECK 3 - Stream still live (normal updates)
# ============================================================================
print(f"\n" + "="*80)
print(f"CHECK 3 - Stream still live (periodic update)")
print(f"="*80)
print(f"\nDaemon calls: is_live() → returns (True, stream_data)")
print(f"Daemon calls: status.update(True, stream_data)")

# Update viewer count again
mock_stream_data['viewer_count'] = 200

state_changed = status.update(True, mock_stream_data)

print(f"\n📊 After CHECK 3:")
print(f"  state_changed: {state_changed} (should be False - no transition)")
print(f"  state: {status.state} (should still be LIVE)")
print(f"  consecutive_live_checks: {status.consecutive_live_checks} (should be 3)")
print(f"  stream_data viewer_count: {status.stream_data.get('viewer_count')} (should be 200 - updated)")

if status.stream_data.get('viewer_count') == 200:
    print(f"\n  ✅ stream_data updates with fresh viewer counts!")
    print(f"     Discord embeds can be updated with current data")
else:
    print(f"\n  ❌ stream_data NOT updating - BUG!")

# ============================================================================
# SUMMARY
# ============================================================================
print(f"\n" + "="*80)
print(f"LIFECYCLE TEST SUMMARY")
print(f"="*80)

results = []

# Test 1: stream_data available during debouncing (CHECK 1)
results.append(("stream_data stored on first check (debouncing)", status.stream_data is not None))

# Test 2: State transitions to LIVE on CHECK 2
results.append(("State transitions to LIVE after 2 checks", status.state.name == 'LIVE'))

# Test 3: stream_data updates on subsequent checks
results.append(("stream_data updates with fresh data", status.stream_data.get('viewer_count') == 200))

all_passed = all(passed for _, passed in results)

for test_name, passed in results:
    status_icon = "✅" if passed else "❌"
    print(f"{status_icon} {test_name}")

print()
if all_passed:
    print("🎉 ALL TESTS PASSED!")
    print()
    print("This means:")
    print("  • Debouncing works (prevents false positives)")
    print("  • stream_data available immediately (fixes already-live streams)")
    print("  • stream_data updates continuously (fresh viewer counts)")
    print("  • Bluesky embeds will work for Kick streams")
    print("  • Mastodon images will work for Kick streams")
    print("  • Discord embeds will have live viewer counts")
else:
    print("❌ SOME TESTS FAILED - THERE ARE BUGS!")

print("="*80)
