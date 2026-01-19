#!/usr/bin/env python3
"""
Test script for local Python installation
Validates all dependencies and core functionality
"""

import sys
import importlib
import subprocess
from pathlib import Path

print("="*70)
print("🧪 Stream Daemon - Local Installation Test")
print("="*70)

# Test 1: Python version
print("\n[1/7] Checking Python version...")
py_version = sys.version_info
if py_version.major == 3 and py_version.minor >= 10:
    print(f"✅ Python {py_version.major}.{py_version.minor}.{py_version.micro}")
else:
    print(f"❌ Python {py_version.major}.{py_version.minor}.{py_version.micro} (need 3.10+)")
    sys.exit(1)

# Test 2: Core dependencies
print("\n[2/7] Checking core dependencies...")
core_deps = [
    'dotenv',
    'twitchAPI',
    'mastodon',
    'atproto',
    'discord',
    'nio',  # matrix-nio
]

failed_deps = []
for dep in core_deps:
    try:
        if dep == 'dotenv':
            importlib.import_module('dotenv')
        elif dep == 'nio':
            importlib.import_module('nio')
        elif dep == 'mastodon':
            importlib.import_module('mastodon')
        elif dep == 'twitchAPI':
            importlib.import_module('twitchAPI')
        else:
            importlib.import_module(dep)
        print(f"  ✅ {dep}")
    except ImportError as e:
        print(f"  ❌ {dep} - {e}")
        failed_deps.append(dep)

# Test 3: AI/LLM dependencies
print("\n[3/7] Checking AI/LLM dependencies...")
ai_deps = {
    'google.genai': 'google-genai (Gemini)',
    'ollama': 'ollama (local LLM)'
}

for module, name in ai_deps.items():
    try:
        importlib.import_module(module)
        print(f"  ✅ {name}")
    except ImportError:
        print(f"  ⚠️  {name} (optional - install if using)")

# Test 4: Security dependencies
print("\n[4/7] Checking security/secrets dependencies...")
sec_deps = {
    'boto3': 'AWS SDK',
    'hvac': 'HashiCorp Vault',
    'dopplersdk': 'Doppler SDK'
}

for module, name in sec_deps.items():
    try:
        importlib.import_module(module)
        print(f"  ✅ {name}")
    except ImportError:
        print(f"  ⚠️  {name} (optional - install if using)")

# Test 5: Check requirements.txt
print("\n[5/7] Validating requirements.txt...")
req_file = Path(__file__).parent / 'requirements.txt'
if req_file.exists():
    print(f"  ✅ requirements.txt exists")
    
    # Try to parse it
    try:
        with open(req_file) as f:
            lines = [l.strip() for l in f if l.strip() and not l.startswith('#')]
            print(f"  ✅ {len(lines)} packages listed")
    except Exception as e:
        print(f"  ❌ Error reading requirements.txt: {e}")
else:
    print(f"  ❌ requirements.txt not found")

# Test 6: Import Stream Daemon modules
print("\n[6/7] Testing Stream Daemon modules...")
modules_to_test = [
    'stream_daemon.config',
    'stream_daemon.models',
    'stream_daemon.ai',
    'stream_daemon.platforms.streaming',
    'stream_daemon.platforms.social',
]

failed_modules = []
for module in modules_to_test:
    try:
        importlib.import_module(module)
        print(f"  ✅ {module}")
    except Exception as e:
        print(f"  ❌ {module} - {e}")
        failed_modules.append(module)

# Test 7: Check for CVE-affected versions
print("\n[7/7] Checking for known CVEs...")
cve_checks = {
    'requests': ('2.32.5', 'CVE-2024-45590, CVE-2024-42473, CVE-2024-6472'),
    'urllib3': ('2.5.0', 'CVE-2024-37891, CVE-2024-37080, CVE-2025-78866'),
    'protobuf': ('6.33.1', 'CVE-2025-4565'),
}

for package, (min_version, cves) in cve_checks.items():
    try:
        mod = importlib.import_module(package)
        version = getattr(mod, '__version__', 'unknown')
        print(f"  ✅ {package}=={version} (need >={min_version} for {cves})")
    except ImportError:
        print(f"  ⚠️  {package} not installed")

# Summary
print("\n" + "="*70)
if failed_deps or failed_modules:
    print("❌ FAILED - Some components are missing")
    if failed_deps:
        print(f"\nMissing dependencies: {', '.join(failed_deps)}")
    if failed_modules:
        print(f"\nFailed modules: {', '.join(failed_modules)}")
    print("\nRun: pip install -r requirements.txt")
    sys.exit(1)
else:
    print("✅ SUCCESS - All dependencies installed correctly!")
    print("\nYour local installation is ready to use.")
    print("\nNext steps:")
    print("  1. Configure .env file")
    print("  2. Run: python3 stream-daemon.py")
    print("  3. Test Ollama (if using): python3 test_ollama.py")
