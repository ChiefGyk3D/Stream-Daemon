#!/usr/bin/env python3
"""
Run All Tests
Comprehensive test suite for stream-daemon.
"""

import sys
import os

# Import all test modules
from test_platforms import run_all_platform_tests
from test_social import run_all_social_tests
from test_llm import run_all_llm_tests


def main():
    """Run all test suites"""
    print("\n" + "="*60)
    print("🧪 STREAM DAEMON - COMPREHENSIVE TEST SUITE")
    print("="*60)
    
    all_results = {}
    
    # Run platform tests
    print("\n\n" + "🎬 PHASE 1: STREAMING PLATFORM TESTS")
    all_results['platforms'] = run_all_platform_tests()
    
    # Run social media tests
    print("\n\n" + "📱 PHASE 2: SOCIAL MEDIA PLATFORM TESTS")
    all_results['social'] = run_all_social_tests()
    
    # Run LLM tests
    print("\n\n" + "🤖 PHASE 3: AI MESSAGE GENERATION TESTS")
    all_results['llm'] = run_all_llm_tests()
    
    # Final summary
    print("\n\n" + "="*60)
    print("🎯 FINAL TEST SUMMARY")
    print("="*60)
    
    for suite_name, result in all_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {suite_name}")
    
    total_passed = sum(1 for v in all_results.values() if v)
    total_suites = len(all_results)
    
    print(f"\n{total_passed}/{total_suites} test suites passed")
    
    if all(all_results.values()):
        print("\n🎉 ALL TESTS PASSED! System is ready.")
        return 0
    else:
        print("\n⚠️  SOME TESTS FAILED. Please review errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
