"""
Streaming Platform Tests

Tests for Twitch, YouTube, and Kick streaming platform integration.
Tests authentication, live stream detection, and data retrieval.

NOTE: These tests are currently disabled because the streaming platforms
      are not yet refactored from stream-daemon.py into separate modules.
      Enable these tests after completing the refactoring to:
      stream_daemon/platforms/streaming/{twitch,youtube,kick}.py
"""

import pytest

pytestmark = pytest.mark.skip(reason="Streaming platforms not yet refactored into separate modules")


def test_placeholder():
    """Placeholder test to prevent pytest collection errors."""
    pytest.skip("Streaming platform tests disabled until refactoring is complete")
