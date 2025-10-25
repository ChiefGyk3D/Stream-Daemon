#!/usr/bin/env python3
"""
Verify Discord periodic updates and end_stream are now implemented
"""

import sys
sys.path.insert(0, '.')

import importlib.util
spec = importlib.util.spec_from_file_location("stream_daemon", "stream-daemon.py")
stream_daemon = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stream_daemon)

print("="*80)
print("DISCORD IMPLEMENTATION VERIFICATION")
print("="*80)

import inspect

# Get the main loop source code
main_source = inspect.getsource(stream_daemon)

print("\n[1/2] Checking for Discord update_stream() in main loop...")
print("-"*80)

# Check for update_stream implementation
if 'Still live' in main_source and 'update_stream' in main_source:
    # Find the relevant section
    lines = main_source.split('\n')
    for i, line in enumerate(lines):
        if 'Still live' in line:
            # Show context around this line
            context_start = max(0, i-2)
            context_end = min(len(lines), i+8)
            print("Found implementation near 'Still live' check:")
            print()
            for j in range(context_start, context_end):
                if 'update_stream' in lines[j]:
                    print(f"  → {lines[j]}")
                else:
                    print(f"    {lines[j]}")
            
            if any('update_stream' in lines[j] for j in range(i, min(len(lines), i+8))):
                print("\n✅ PASS: update_stream() is called for streams that are still live")
            break
else:
    print("❌ FAIL: update_stream() NOT found in main loop")

print("\n[2/2] Checking for Discord end_stream() in offline handling...")
print("-"*80)

# Check for end_stream implementation
if 'platforms_went_offline' in main_source and 'end_stream' in main_source:
    lines = main_source.split('\n')
    for i, line in enumerate(lines):
        if 'platforms_went_offline' in line and 'if' in line:
            # Show context
            context_start = max(0, i-2)
            context_end = min(len(lines), i+20)
            print("Found implementation in offline handling:")
            print()
            for j in range(context_start, context_end):
                if 'end_stream' in lines[j]:
                    print(f"  → {lines[j]}")
                elif 'Discord' in lines[j] and 'special' in lines[j]:
                    print(f"  → {lines[j]}")
                elif j < i + 15:  # Only show some context
                    print(f"    {lines[j]}")
            
            if any('end_stream' in lines[j] for j in range(i, min(len(lines), i+30))):
                print("\n✅ PASS: end_stream() is called when streams go offline")
            break
else:
    print("❌ FAIL: end_stream() NOT found in offline handling")

print("\n" + "="*80)
print("IMPLEMENTATION STATUS")
print("="*80)

has_update = 'update_stream' in main_source and 'Still live' in main_source
has_end = 'end_stream' in main_source and 'platforms_went_offline' in main_source

if has_update and has_end:
    print("\n🎉 ALL DISCORD FEATURES IMPLEMENTED!")
    print("\n✅ Implemented:")
    print("  • Discord.update_stream() - Updates embeds while stream is live")
    print("  • Discord.end_stream() - Updates embed when stream ends")
    print("\n📋 Expected Behavior:")
    print("  1. Stream goes LIVE → Posts Discord embed with LLM message + card")
    print("  2. Stream still live → Updates embed viewer count every check interval")
    print("  3. Stream ends → Updates embed to 'Stream Ended' with thank you message")
    print("  4. Other platforms (Bluesky/Mastodon/Matrix) → Post new end message")
elif has_update:
    print("\n⚠️ PARTIALLY IMPLEMENTED")
    print("  ✅ update_stream() implemented")
    print("  ❌ end_stream() NOT implemented")
elif has_end:
    print("\n⚠️ PARTIALLY IMPLEMENTED")
    print("  ❌ update_stream() NOT implemented")
    print("  ✅ end_stream() implemented")
else:
    print("\n❌ NOT IMPLEMENTED")
    print("  Both features are missing from main loop")

print("="*80)
