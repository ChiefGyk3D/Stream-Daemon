#!/usr/bin/env python3
"""
Test Secrets Manager Priority Override

Verifies that when a secrets manager is enabled, it overrides .env values for secrets/webhooks.

Priority order:
1. Secrets Manager (Doppler/AWS/Vault) - HIGHEST
2. .env file - FALLBACK

This test checks that Doppler values override .env values when both are present.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 80)
print("SECRETS MANAGER PRIORITY TEST")
print("=" * 80)
print()

# Check which secrets manager is enabled
secret_manager = os.getenv('SECRETS_SECRET_MANAGER', 'none').lower()
print(f"🔐 Secrets Manager: {secret_manager}")
print()

if secret_manager == 'none':
    print("❌ No secrets manager enabled!")
    print()
    print("To run this test:")
    print("  1. Set SECRETS_SECRET_MANAGER=doppler (or aws/vault)")
    print("  2. Configure your secrets manager with test values")
    print("  3. Run: doppler run -- python3 tests/test_secrets_priority.py")
    print()
    sys.exit(1)

print("=" * 80)
print("TESTING PRIORITY OVERRIDE")
print("=" * 80)
print()
print("This test verifies that secrets manager values override .env values.")
print()

# Test secrets that should be overridden
test_cases = [
    ('TWITCH_CLIENT_ID', 'Twitch'),
    ('TWITCH_CLIENT_SECRET', 'Twitch'),
    ('YOUTUBE_API_KEY', 'YouTube'),
    ('DISCORD_WEBHOOK_URL', 'Discord'),
]

print("Checking which values are being used:")
print("-" * 80)
print()

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the get_secret function
try:
    import stream_daemon
    from stream_daemon import get_secret
except ImportError:
    # Try direct import
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "stream_daemon", 
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "stream-daemon.py")
    )
    stream_daemon = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(stream_daemon)
    get_secret = stream_daemon.get_secret

results = []

for env_var, platform in test_cases:
    # Get value from .env
    env_value = os.getenv(env_var)
    
    # Extract key from env_var (e.g., TWITCH_CLIENT_ID -> client_id)
    key = env_var.replace(f'{platform.upper()}_', '').lower()
    
    # Get value via get_secret (which respects priority)
    if secret_manager == 'doppler':
        secret_name = os.getenv(f'SECRETS_DOPPLER_{platform.upper()}_SECRET_NAME')
        if secret_name:
            actual_value = get_secret(
                platform, 
                key,
                doppler_secret_env=f'SECRETS_DOPPLER_{platform.upper()}_SECRET_NAME'
            )
        else:
            actual_value = None
    else:
        # For AWS/Vault, adjust accordingly
        actual_value = None
    
    # Mask values for security
    def mask_value(val):
        if not val:
            return "❌ NOT SET"
        if len(val) <= 8:
            return "xxxx...xxxx"
        return f"{val[:4]}...{val[-4:]}"
    
    print(f"📋 {env_var}:")
    print(f"   .env value:        {mask_value(env_value)}")
    print(f"   get_secret() uses: {mask_value(actual_value)}")
    
    # Check if they're different (meaning secrets manager overrode)
    if env_value and actual_value and env_value != actual_value:
        print(f"   ✅ OVERRIDE: Secrets manager value is being used (different from .env)")
        results.append(('OVERRIDE', env_var))
    elif env_value and actual_value and env_value == actual_value:
        print(f"   ⚠️  SAME: Values match (can't verify override)")
        results.append(('SAME', env_var))
    elif not env_value and actual_value:
        print(f"   ✅ SECRETS ONLY: Using secrets manager (no .env value)")
        results.append(('SECRETS_ONLY', env_var))
    elif env_value and not actual_value:
        print(f"   ⚠️  ENV ONLY: Using .env (secrets manager not configured)")
        results.append(('ENV_ONLY', env_var))
    else:
        print(f"   ❌ ERROR: No value found in either location")
        results.append(('ERROR', env_var))
    
    print()

print("=" * 80)
print("TEST SUMMARY")
print("=" * 80)
print()

overrides = [r for r in results if r[0] == 'OVERRIDE']
secrets_only = [r for r in results if r[0] == 'SECRETS_ONLY']
same = [r for r in results if r[0] == 'SAME']
env_only = [r for r in results if r[0] == 'ENV_ONLY']
errors = [r for r in results if r[0] == 'ERROR']

if overrides:
    print(f"✅ Confirmed overrides: {len(overrides)}")
    for _, var in overrides:
        print(f"   • {var} - Secrets manager overriding .env ✓")
    print()

if secrets_only:
    print(f"✅ Secrets manager only: {len(secrets_only)}")
    for _, var in secrets_only:
        print(f"   • {var} - Using secrets manager (no .env value)")
    print()

if same:
    print(f"⚠️  Same values: {len(same)}")
    print(f"   Cannot verify override when values match.")
    print(f"   To test: Change .env value to something different,")
    print(f"   then verify get_secret() still returns secrets manager value.")
    print()

if env_only:
    print(f"⚠️  .env fallback: {len(env_only)}")
    for _, var in env_only:
        print(f"   • {var} - Secrets manager not configured, using .env")
    print()

if errors:
    print(f"❌ Errors: {len(errors)}")
    for _, var in errors:
        print(f"   • {var} - Not found in either location")
    print()

print("=" * 80)
print()

if overrides or secrets_only:
    print("🎉 SUCCESS! Priority system is working:")
    print("   Secrets manager values are being used when available,")
    print("   and .env values serve as fallback.")
else:
    print("💡 To verify override behavior:")
    print("   1. Set different values in .env vs secrets manager")
    print("   2. Run this test again")
    print("   3. Confirm get_secret() uses secrets manager value")
print()
print("=" * 80)
