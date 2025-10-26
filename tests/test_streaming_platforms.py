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

# Keeping imports commented until refactoring is complete
# from stream_daemon.platforms.streaming import TwitchPlatform, YouTubePlatform, KickPlatform


@pytest.mark.streaming
class TestTwitchPlatform:
    """Tests for Twitch streaming platform."""
    
    @pytest.fixture
    def platform(self, skip_if_platform_disabled):
        """Create Twitch platform instance."""
        skip_if_platform_disabled('twitch')
        return TwitchPlatform()
    
    def test_authentication(self, platform):
        """Test Twitch API authentication."""
        result = platform.authenticate()
        assert result is not False, "Twitch authentication failed"
        assert platform.client is not None, "Twitch client not initialized"
    
    def test_credentials_loaded(self, platform):
        """Test that Twitch credentials are loaded from secrets."""
        platform.authenticate()
        
        assert platform.client_id is not None, "Twitch client_id not loaded"
        assert platform.client_secret is not None, "Twitch client_secret not loaded"
        assert len(platform.client_id) > 0, "Twitch client_id is empty"
        assert len(platform.client_secret) > 0, "Twitch client_secret is empty"
    
    def test_is_live_check(self, platform, test_usernames):
        """Test live stream detection for configured username."""
        platform.authenticate()
        username = test_usernames['twitch']
        
        is_live, data = platform.is_live(username)
        
        # Should return a boolean and data dict
        assert isinstance(is_live, bool), "is_live should be boolean"
        assert isinstance(data, dict), "data should be dict"
        
        # If live, should have required fields
        if is_live:
            assert 'title' in data, "Live stream missing 'title'"
            assert 'game_name' in data, "Live stream missing 'game_name'"
            assert 'viewer_count' in data, "Live stream missing 'viewer_count'"
            assert 'url' in data, "Live stream missing 'url'"
            
            # Verify data types
            assert isinstance(data['title'], str), "title should be string"
            assert isinstance(data['viewer_count'], int), "viewer_count should be int"
    
    @pytest.mark.integration
    def test_multiple_live_checks(self, platform, test_usernames):
        """Test multiple consecutive is_live calls."""
        platform.authenticate()
        username = test_usernames['twitch']
        
        # Call multiple times to test stability
        for _ in range(3):
            is_live, data = platform.is_live(username)
            assert isinstance(is_live, bool)


@pytest.mark.streaming
class TestYouTubePlatform:
    """Tests for YouTube Live streaming platform."""
    
    @pytest.fixture
    def platform(self, skip_if_platform_disabled):
        """Create YouTube platform instance."""
        skip_if_platform_disabled('youtube')
        return YouTubePlatform()
    
    def test_authentication(self, platform):
        """Test YouTube API authentication."""
        result = platform.authenticate()
        assert result is not False, "YouTube authentication failed"
        assert platform.youtube_api is not None, "YouTube API client not initialized"
    
    def test_credentials_loaded(self, platform):
        """Test that YouTube API key is loaded from secrets."""
        platform.authenticate()
        
        assert platform.api_key is not None, "YouTube API key not loaded"
        assert len(platform.api_key) > 0, "YouTube API key is empty"
    
    def test_is_live_check(self, platform, test_usernames):
        """Test live stream detection for configured username."""
        platform.authenticate()
        username = test_usernames['youtube']
        
        is_live, data = platform.is_live(username)
        
        # Should return a boolean and data dict
        assert isinstance(is_live, bool), "is_live should be boolean"
        assert isinstance(data, dict), "data should be dict"
        
        # If live, should have required fields
        if is_live:
            assert 'title' in data, "Live stream missing 'title'"
            assert 'video_id' in data, "Live stream missing 'video_id'"
            assert 'url' in data, "Live stream missing 'url'"
            assert 'youtube.com' in data['url'], "URL should be YouTube URL"
    
    def test_username_normalization(self, platform):
        """Test that @ handles are normalized correctly."""
        platform.authenticate()
        
        # Test with @ prefix
        is_live1, data1 = platform.is_live("@test_channel")
        # Test without @ prefix  
        is_live2, data2 = platform.is_live("test_channel")
        
        # Both should work (either both fail gracefully or both succeed)
        assert isinstance(is_live1, bool)
        assert isinstance(is_live2, bool)
    
    @pytest.mark.slow
    def test_quota_awareness(self, platform):
        """Test that YouTube API respects quota limits."""
        platform.authenticate()
        
        # This test would make multiple calls and verify
        # that the platform handles quota limits gracefully
        # For now, just verify the platform doesn't crash on multiple calls
        
        for _ in range(5):
            is_live, data = platform.is_live("test_channel")
            assert isinstance(is_live, bool)


@pytest.mark.streaming
class TestKickPlatform:
    """Tests for Kick streaming platform."""
    
    @pytest.fixture
    def platform(self, skip_if_platform_disabled):
        """Create Kick platform instance."""
        skip_if_platform_disabled('kick')
        return KickPlatform()
    
    def test_authentication(self, platform):
        """Test Kick authentication (OAuth or public API)."""
        result = platform.authenticate()
        # Kick public API doesn't require auth, should still succeed
        assert result is not False, "Kick authentication/initialization failed"
    
    def test_is_live_check(self, platform, test_usernames):
        """Test live stream detection for configured username."""
        platform.authenticate()
        username = test_usernames['kick']
        
        is_live, data = platform.is_live(username)
        
        # Should return a boolean and data dict
        assert isinstance(is_live, bool), "is_live should be boolean"
        assert isinstance(data, dict), "data should be dict"
        
        # If live, should have required fields
        if is_live:
            assert 'title' in data, "Live stream missing 'title'"
            assert 'category' in data or 'game_name' in data, "Live stream missing category/game"
            assert 'viewers' in data or 'viewer_count' in data, "Live stream missing viewer count"
            assert 'url' in data, "Live stream missing 'url'"
            assert 'kick.com' in data['url'], "URL should be Kick URL"
    
    def test_public_api_fallback(self, platform):
        """Test that Kick works without OAuth credentials."""
        # Even without OAuth, should be able to check public channels
        platform.authenticate()
        
        # Test with a known high-profile streamer
        is_live, data = platform.is_live("xqc")  # Popular Kick streamer
        
        assert isinstance(is_live, bool), "Public API should return boolean"
        assert isinstance(data, dict), "Public API should return dict"


@pytest.mark.integration
class TestPlatformComparison:
    """Cross-platform comparison tests."""
    
    def test_all_platforms_return_consistent_format(self, test_usernames):
        """Test that all platforms return data in consistent format."""
        platforms = []
        
        # Create platforms that are enabled
        if os.getenv('TWITCH_ENABLE', '').lower() in ('true', '1', 'yes'):
            platforms.append(('Twitch', TwitchPlatform(), test_usernames['twitch']))
        
        if os.getenv('YOUTUBE_ENABLE', '').lower() in ('true', '1', 'yes'):
            platforms.append(('YouTube', YouTubePlatform(), test_usernames['youtube']))
        
        if os.getenv('KICK_ENABLE', '').lower() in ('true', '1', 'yes'):
            platforms.append(('Kick', KickPlatform(), test_usernames['kick']))
        
        if not platforms:
            pytest.skip("No streaming platforms enabled")
        
        for name, platform, username in platforms:
            platform.authenticate()
            is_live, data = platform.is_live(username)
            
            # All should return same types
            assert isinstance(is_live, bool), f"{name}: is_live should be boolean"
            assert isinstance(data, dict), f"{name}: data should be dict"
            
            # All should have url if live
            if is_live:
                assert 'url' in data, f"{name}: missing 'url' in live stream data"
                assert data['url'].startswith('http'), f"{name}: invalid URL format"
