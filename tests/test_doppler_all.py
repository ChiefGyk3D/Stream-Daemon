#!/usr/bin/env python3
"""
Comprehensive test suite for all streaming platforms.
Tests Doppler secret fetching and platform connectivity.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# Load environment
load_dotenv()

def run_test_file(test_file: str) -> bool:
    """Run a test file and return success status."""
    import subprocess
    
    test_path = Path(__file__).parent / test_file
    
    try:
        result = subprocess.run(
            [sys.executable, str(test_path)],
            capture_output=False,
            text=True
        )
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Failed to run {test_file}: {e}")
        return False

def check_environment():
    """Check if environment is properly configured."""
    print("=" * 60)
    print("🔧 ENVIRONMENT CHECK")
    print("=" * 60)
    
    checks = []
    
    # Check secret manager
    secret_manager = os.getenv('SECRETS_SECRET_MANAGER', 'none').lower()
    checks.append(("Secret Manager", secret_manager == 'doppler'))
    print(f"Secret Manager: {secret_manager} {'✓' if secret_manager == 'doppler' else '✗'}")
    
    # Check Doppler token
    doppler_token = os.getenv('DOPPLER_TOKEN')
    has_token = bool(doppler_token)
    checks.append(("Doppler Token", has_token))
    print(f"Doppler Token: {'SET ✓' if has_token else 'NOT SET ✗'}")
    
    # Check platform configurations
    platforms = {
        'Twitch': os.getenv('SECRETS_DOPPLER_TWITCH_SECRET_NAME'),
        'YouTube': os.getenv('SECRETS_DOPPLER_YOUTUBE_SECRET_NAME'),
        'Kick': os.getenv('KICK_ENABLE')
    }
    
    print()
    for platform, config in platforms.items():
        is_configured = bool(config)
        checks.append((f"{platform} Config", is_configured))
        print(f"{platform}: {'CONFIGURED ✓' if is_configured else 'NOT CONFIGURED ⚠'}")
    
    print()
    all_passed = all(result for _, result in checks)
    
    if all_passed:
        print("✓ Environment is properly configured")
    else:
        print("⚠ Some environment variables are not set")
        print("  See .env.example for configuration details")
    
    return all_passed

def main():
    """Run all platform tests."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "STREAM DAEMON - COMPREHENSIVE TEST SUITE" + " " * 8 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    # Environment check
    env_ok = check_environment()
    
    if not env_ok:
        print("\n⚠ Environment check failed. Please configure .env file.")
        print("  See tests/DOPPLER_SECRETS.md for setup instructions")
        return False
    
    print("\n")
    
    # Run individual platform tests
    test_results = {}
    
    print("🧪 Running platform tests...\n")
    
    # Twitch
    print("\n" + "─" * 60)
    test_results['Twitch'] = run_test_file('test_doppler_twitch.py')
    
    # YouTube
    print("\n" + "─" * 60)
    test_results['YouTube'] = run_test_file('test_doppler_youtube.py')
    
    # Kick
    print("\n" + "─" * 60)
    test_results['Kick'] = run_test_file('test_doppler_kick.py')
    
    # Final summary
    print("\n" + "=" * 60)
    print("🎯 FINAL RESULTS")
    print("=" * 60)
    
    for platform, result in test_results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {platform}")
    
    passed = sum(1 for result in test_results.values() if result)
    total = len(test_results)
    
    print(f"\nOverall: {passed}/{total} platforms passed")
    print("=" * 60)
    
    if passed == total:
        print("\n🎉 All tests passed! Stream Daemon is ready to run.")
    else:
        print("\n⚠ Some tests failed. Check configuration and credentials.")
        print("  See tests/DOPPLER_SECRETS.md for troubleshooting")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
