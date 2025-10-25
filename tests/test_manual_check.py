#!/usr/bin/env python3
"""
Manual stream check - single iteration to see what's detected
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import importlib.util

# Load the stream daemon module
spec = importlib.util.spec_from_file_location('stream_daemon', 'stream-daemon.py')
stream_daemon = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stream_daemon)

print("="*60)
print("MANUAL STREAM CHECK")
print("="*60)

# Check Twitch
print("\n--- Twitch ---")
twitch = stream_daemon.TwitchPlatform()
if twitch.authenticate():
    username = os.getenv('TWITCH_USERNAME', 'lilypita')
    is_live, data = twitch.is_live(username)
    print(f"Username: {username}")
    print(f"Is Live: {is_live}")
    if data:
        print(f"Data: {data}")

# Check YouTube  
print("\n--- YouTube ---")
youtube = stream_daemon.YouTubePlatform()
if youtube.authenticate():
    username = os.getenv('YOUTUBE_USERNAME', 'Hyphonix')
    is_live, data = youtube.is_live(username)
    print(f"Username: {username}")
    print(f"Is Live: {is_live}")
    if data:
        print(f"Data: {data}")

# Check Kick
print("\n--- Kick ---")
kick = stream_daemon.KickPlatform()
if kick.authenticate():
    username = os.getenv('KICK_USERNAME', 'daletanhardt')
    is_live, data = kick.is_live(username)
    print(f"Username: {username}")
    print(f"Is Live: {is_live}")
    if data:
        print(f"Data: {data}")

print("\n" + "="*60)
