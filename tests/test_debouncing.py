"""
Debouncing Logic Tests

Simulates 2 check cycles to test debouncing and posting behavior.
Tests that stream announcements only occur after debounce confirmation.
"""

from stream_daemon.models import StreamStatus, StreamState


class TestDebouncingBehavior:
    """Test debouncing logic for stream state transitions."""
    
    def test_debouncing_requires_two_checks(self):
        """Test that going live requires two consecutive positive checks."""
        status = StreamStatus(platform_name='Twitch', username='testuser')
        
        stream_data = {
            'title': 'Test Stream',
            'viewer_count': 100,
            'thumbnail_url': 'https://example.com/thumb.jpg',
            'game_name': 'Test Game'
        }
        
        # First check - should not trigger (debouncing)
        changed = status.update(True, stream_data)
        assert changed == False
        assert status.state == StreamState.OFFLINE
        assert status.consecutive_live_checks == 1
        
        # Second check - should trigger LIVE state
        changed = status.update(True, stream_data)
        assert changed == True
        assert status.state == StreamState.LIVE
        assert status.consecutive_live_checks == 2
    
    def test_debouncing_resets_on_offline(self):
        """Test that debouncing resets if stream goes offline before confirmation."""
        status = StreamStatus(platform_name='Twitch', username='testuser')
        
        stream_data = {
            'title': 'Test Stream',
            'viewer_count': 100,
            'thumbnail_url': 'https://example.com/thumb.jpg',
            'game_name': 'Test Game'
        }
        
        # First check - stream detected
        changed = status.update(True, stream_data)
        assert changed == False
        assert status.consecutive_live_checks == 1
        
        # Stream goes offline before second check
        changed = status.update(False, None)
        assert changed == False
        assert status.state == StreamState.OFFLINE
        assert status.consecutive_live_checks == 0
    
    def test_stream_data_preserved_during_debouncing(self):
        """Test that stream_data is available during debouncing period."""
        status = StreamStatus(platform_name='Twitch', username='testuser')
        
        stream_data = {
            'title': 'Test Stream',
            'viewer_count': 100,
            'thumbnail_url': 'https://example.com/thumb.jpg',
            'game_name': 'Test Game'
        }
        
        # First check - stream_data should be stored even though not LIVE yet
        changed = status.update(True, stream_data)
        assert changed == False
        assert status.stream_data is not None
        assert status.stream_data['title'] == 'Test Stream'
        assert status.stream_data['viewer_count'] == 100
    
    def test_no_duplicate_announcements(self):
        """Test that multiple updates while live don't trigger state changes."""
        status = StreamStatus(platform_name='Twitch', username='testuser')
        
        stream_data = {
            'title': 'Test Stream',
            'viewer_count': 100,
            'thumbnail_url': 'https://example.com/thumb.jpg',
            'game_name': 'Test Game'
        }
        
        # Go through debouncing
        status.update(True, stream_data)
        changed = status.update(True, stream_data)
        assert changed == True  # Should transition to LIVE
        
        # Subsequent updates should not trigger changes
        stream_data['viewer_count'] = 150
        changed = status.update(True, stream_data)
        assert changed == False  # Already LIVE, no state change
        
        stream_data['viewer_count'] = 200
        changed = status.update(True, stream_data)
        assert changed == False  # Still LIVE, no state change
