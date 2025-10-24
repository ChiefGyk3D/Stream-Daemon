#!/bin/bash
# Test runner script for Stream Daemon
# Safely runs tests without revealing credentials

set -e

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║           Stream Daemon - Platform Test Runner              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to run a test
run_test() {
    local test_name=$1
    local test_file=$2
    
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}Testing: $test_name${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    if python3 "tests/$test_file"; then
        echo -e "${GREEN}✓ $test_name PASSED${NC}"
        return 0
    else
        echo -e "${RED}✗ $test_name FAILED${NC}"
        return 1
    fi
}

# Check if running from project root
if [ ! -d "tests" ]; then
    echo -e "${RED}Error: Must run from project root directory${NC}"
    echo "Usage: ./run_tests.sh [platform]"
    exit 1
fi

# Parse arguments
PLATFORM=${1:-all}

case $PLATFORM in
    all)
        echo "Running comprehensive test suite..."
        echo ""
        run_test "All Platforms" "test_doppler_all.py"
        ;;
    twitch)
        run_test "Twitch" "test_doppler_twitch.py"
        ;;
    youtube)
        run_test "YouTube" "test_doppler_youtube.py"
        ;;
    kick)
        run_test "Kick" "test_doppler_kick.py"
        ;;
    *)
        echo -e "${RED}Unknown platform: $PLATFORM${NC}"
        echo ""
        echo "Usage: ./run_tests.sh [platform]"
        echo ""
        echo "Platforms:"
        echo "  all      - Run all platform tests (default)"
        echo "  twitch   - Test Twitch only"
        echo "  youtube  - Test YouTube only"
        echo "  kick     - Test Kick only"
        exit 1
        ;;
esac

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo ""
