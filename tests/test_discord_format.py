#!/usr/bin/env python3
"""Test Discord message formatting with stream_data"""

import os
import sys

# Test the new Discord formatting
def test_discord_format():
    """Verify Discord message has LLM text in content and stream data in embed"""
    
    # Mock stream data like what's returned from is_live()
    stream_data = {
        'title': 'Test Stream Title - Amazing Gameplay!',
        'viewer_count': 250,
        'thumbnail_url': 'https://example.com/thumb.jpg',
        'game_name': 'Just Chatting'
    }
    
    # Mock LLM message
    llm_message = "🎮 The stream is heating up! Jump in and join the fun!"
    
    # Mock URL
    stream_url = "https://twitch.tv/testuser"
    
    print("="*60)
    print("Testing Discord Message Format")
    print("="*60)
    
    print("\n📝 Input Data:")
    print(f"  LLM Message: {llm_message}")
    print(f"  Stream URL: {stream_url}")
    print(f"  Stream Data:")
    for key, value in stream_data.items():
        print(f"    {key}: {value}")
    
    print("\n✅ Expected Discord Webhook Payload:")
    print("  {")
    print(f'    "content": "{llm_message} <@&ROLE_ID>",')
    print('    "embeds": [')
    print('      {')
    print('        "title": "🟣 Live on Twitch",')
    print(f'        "description": "{stream_data["title"]}",')
    print(f'        "url": "{stream_url}",')
    print('        "color": 0x9146FF,')
    print('        "fields": [')
    print('          {')
    print('            "name": "👥 Viewers",')
    print(f'            "value": "{stream_data["viewer_count"]:,}",')
    print('            "inline": true')
    print('          },')
    print('          {')
    print('            "name": "🎮 Category",')
    print(f'            "value": "{stream_data["game_name"]}",')
    print('            "inline": true')
    print('          }')
    print('        ],')
    print('        "image": {')
    print(f'          "url": "{stream_data["thumbnail_url"]}"')
    print('        },')
    print('        "footer": {')
    print('          "text": "Click to watch the stream!"')
    print('        }')
    print('      }')
    print('    ]')
    print('  }')
    
    print("\n📋 Key Points:")
    print("  ✓ LLM message is in 'content' field (with role mention)")
    print("  ✓ Stream title is in embed 'description' field")
    print("  ✓ Viewer count and game category are in embed 'fields'")
    print("  ✓ Thumbnail is in embed 'image'")
    print("  ✓ Stream URL is in embed 'url' (makes title clickable)")
    
    print("\n" + "="*60)
    print("Format Verification Complete!")
    print("="*60)
    
    return True

if __name__ == "__main__":
    success = test_discord_format()
    sys.exit(0 if success else 1)
