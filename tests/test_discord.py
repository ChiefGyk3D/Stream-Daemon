#!/usr/bin/env python3
"""
Test Discord webhook posting.
This is a wrapper that calls test_doppler_discord.py for compatibility.
"""

import sys
import subprocess
from pathlib import Path

def main():
    """Run the Discord Doppler test."""
    test_file = Path(__file__).parent / "test_doppler_discord.py"
    
    if not test_file.exists():
        print("❌ Error: test_doppler_discord.py not found")
        print(f"   Expected at: {test_file}")
        return 1
    
    # Run the actual test
    result = subprocess.run([sys.executable, str(test_file)])
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())
