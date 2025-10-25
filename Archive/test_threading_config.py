#!/usr/bin/env python3
"""
Test Multi-Platform Threading Configuration

This script validates that the new threading mode configurations
are loaded correctly and validates the configuration values.
"""

import os
import sys
from dotenv import load_dotenv

# Load .env file
load_dotenv()

def get_config(section: str, key: str, default: str = None) -> str:
    """Get config from environment variables."""
    env_key = f"{section.upper()}_{key.upper()}"
    return os.getenv(env_key, default)

def test_threading_configs():
    """Test that threading mode configurations are valid."""
    
    print("="*60)
    print("Multi-Platform Threading Configuration Test")
    print("="*60)
    
    # Valid modes
    valid_live_modes = ['separate', 'thread', 'combined']
    valid_end_modes = ['disabled', 'separate', 'thread', 'combined', 'single_when_all_end']
    
    # Load configurations
    live_mode = get_config('Messages', 'live_threading_mode', default='separate').lower()
    end_mode = get_config('Messages', 'end_threading_mode', default='thread').lower()
    use_platform_specific = get_config('Messages', 'use_platform_specific_messages', default='True')
    
    print(f"\n📋 Current Configuration:")
    print(f"   LIVE_THREADING_MODE: {live_mode}")
    print(f"   END_THREADING_MODE: {end_mode}")
    print(f"   USE_PLATFORM_SPECIFIC_MESSAGES: {use_platform_specific}")
    
    # Validate
    errors = []
    warnings = []
    
    print(f"\n🔍 Validation:")
    
    # Validate live mode
    if live_mode in valid_live_modes:
        print(f"   ✓ LIVE_THREADING_MODE '{live_mode}' is valid")
    else:
        errors.append(f"Invalid LIVE_THREADING_MODE '{live_mode}'. Must be one of: {', '.join(valid_live_modes)}")
        print(f"   ✗ LIVE_THREADING_MODE '{live_mode}' is INVALID")
    
    # Validate end mode
    if end_mode in valid_end_modes:
        print(f"   ✓ END_THREADING_MODE '{end_mode}' is valid")
    else:
        errors.append(f"Invalid END_THREADING_MODE '{end_mode}'. Must be one of: {', '.join(valid_end_modes)}")
        print(f"   ✗ END_THREADING_MODE '{end_mode}' is INVALID")
    
    # Check for common misconfigurations
    if end_mode == 'thread' and live_mode == 'combined':
        warnings.append("Using 'thread' end mode with 'combined' live mode may not thread as expected")
        print(f"   ⚠ Warning: 'thread' end mode + 'combined' live mode combination")
    
    if end_mode == 'single_when_all_end':
        print(f"   ℹ Info: Using single_when_all_end - will wait for ALL platforms to finish")
    
    # Print results
    print(f"\n{'='*60}")
    if errors:
        print(f"❌ VALIDATION FAILED ({len(errors)} error(s))")
        for error in errors:
            print(f"   • {error}")
        return False
    elif warnings:
        print(f"⚠️  VALIDATION PASSED WITH WARNINGS ({len(warnings)} warning(s))")
        for warning in warnings:
            print(f"   • {warning}")
        return True
    else:
        print(f"✅ VALIDATION PASSED - Configuration is valid!")
        return True

def print_mode_examples():
    """Print examples of each mode."""
    print(f"\n{'='*60}")
    print("📖 Mode Examples:")
    print("="*60)
    
    print("\n🔴 LIVE_THREADING_MODE:")
    print("   separate: 'Live on Twitch!' + 'Live on YouTube!' (separate posts)")
    print("   thread:   'Live on Twitch!' → 'Also on YouTube!' (threaded)")
    print("   combined: 'Live on Twitch, YouTube!' (single post)")
    
    print("\n🔵 END_THREADING_MODE:")
    print("   disabled:            No end messages")
    print("   separate:            'Twitch ended!' + 'YouTube ended!' (separate)")
    print("   thread:              'Live!' → 'Stream ended!' (threaded to live post)")
    print("   combined:            'Twitch, YouTube ended!' (single post)")
    print("   single_when_all_end: Wait for all platforms, then 'All ended!'")
    
    print(f"\n📚 See MULTI_PLATFORM_EXAMPLES.md for detailed scenarios")

if __name__ == "__main__":
    success = test_threading_configs()
    print_mode_examples()
    
    print(f"\n{'='*60}")
    if success:
        print("✅ Test completed successfully!")
        sys.exit(0)
    else:
        print("❌ Test failed - please fix configuration errors")
        sys.exit(1)
