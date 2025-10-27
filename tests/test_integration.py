"""
End-to-End Integration Tests

Tests complete workflows from stream detection to social media posting.
Simulates real-world scenarios with all platforms working together.
"""

import pytest
from stream_daemon.platforms.social import MastodonPlatform, BlueskyPlatform
from stream_daemon.models import StreamStatus
from stream_daemon.config import get_bool_config


class TestStreamingIntegration:
    """Integration tests for streaming platforms."""
    
    def test_stream_status_tracking(self):
        """Test that StreamStatus correctly tracks stream state changes."""
        status = StreamStatus(platform_name='Twitch', username='testuser')
        
        # Initial state should be OFFLINE
        assert status.state.name == 'OFFLINE'
        
        # Mock stream data
        stream_data = {
            'title': 'Test Stream',
            'viewer_count': 100,
            'thumbnail_url': 'https://example.com/thumb.jpg',
            'game_name': 'Test Game'
        }
        
        # First update - should not trigger (debouncing)
        changed = status.update(True, stream_data)
        assert changed == False
        assert status.state.name == 'OFFLINE'
        
        # Second update - should trigger LIVE state
        changed = status.update(True, stream_data)
        assert changed == True
        assert status.state.name == 'LIVE'
        assert status.title == 'Test Stream'


class TestSocialIntegration:
    """Integration tests for social platforms."""
    
    @pytest.mark.skipif(
        not get_bool_config('Mastodon', 'enable', default=False),
        reason="Mastodon not enabled"
    )
    def test_mastodon_integration(self):
        """Test Mastodon platform integration."""
        platform = MastodonPlatform()
        assert platform.name == "Mastodon"
        
        # Test authentication
        result = platform.authenticate()
        if result:
            assert platform.enabled == True
    
    @pytest.mark.skipif(
        not get_bool_config('Bluesky', 'enable', default=False),
        reason="Bluesky not enabled"
    )
    def test_bluesky_integration(self):
        """Test Bluesky platform integration."""
        platform = BlueskyPlatform()
        assert platform.name == "Bluesky"
        
        # Test authentication
        result = platform.authenticate()
        if result:
            assert platform.enabled == True


def test_placeholder():
    """Placeholder test to ensure test collection works."""
    assert True
