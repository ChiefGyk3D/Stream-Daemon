"""
Streaming Platform Tests

Tests for Twitch, YouTube, and Kick streaming platform integration.
Tests authentication, live stream detection, and data retrieval.
"""

import pytest
from stream_daemon.platforms.streaming import TwitchPlatform, YouTubePlatform, KickPlatform
from stream_daemon.config import get_config, get_bool_config


class TestTwitchPlatform:
    """Tests for Twitch streaming platform."""
    
    @pytest.fixture
    def platform(self):
        """Create a Twitch platform instance."""
        return TwitchPlatform()
    
    def test_platform_initialization(self, platform):
        """Test that platform initializes correctly."""
        assert platform.name == "Twitch"
        assert platform.enabled == False
    
    def test_authentication(self, platform, load_test_env):
        """Test Twitch authentication."""
        # This test requires valid credentials
        if not get_config('Twitch', 'client_id'):
            pytest.skip("Twitch credentials not configured")
        
        result = platform.authenticate()
        assert isinstance(result, bool)
        
        if result:
            assert platform.enabled == True
            assert platform.client_id is not None
    
    def test_is_live_when_disabled(self, platform):
        """Test that is_live returns False when platform is disabled."""
        result, data = platform.is_live('test_user')
        assert result == False
        assert data is None


class TestYouTubePlatform:
    """Tests for YouTube streaming platform."""
    
    @pytest.fixture
    def platform(self):
        """Create a YouTube platform instance."""
        return YouTubePlatform()
    
    def test_platform_initialization(self, platform):
        """Test that platform initializes correctly."""
        assert platform.name == "YouTube"
        assert platform.enabled == False
    
    def test_authentication(self, platform, load_test_env):
        """Test YouTube authentication."""
        # This test requires valid credentials
        if not get_config('YouTube', 'api_key'):
            pytest.skip("YouTube credentials not configured")
        
        result = platform.authenticate()
        assert isinstance(result, bool)
        
        if result:
            assert platform.enabled == True
            assert platform.client is not None
    
    def test_is_live_when_disabled(self, platform):
        """Test that is_live returns False when platform is disabled."""
        result, data = platform.is_live('test_user')
        assert result == False
        assert data is None


class TestKickPlatform:
    """Tests for Kick streaming platform."""
    
    @pytest.fixture
    def platform(self):
        """Create a Kick platform instance."""
        return KickPlatform()
    
    def test_platform_initialization(self, platform):
        """Test that platform initializes correctly."""
        assert platform.name == "Kick"
        assert platform.enabled == False
    
    def test_authentication(self, platform, load_test_env):
        """Test Kick authentication."""
        # Kick is optional and may fall back to public API
        if not get_bool_config('Kick', 'enable', default=False):
            pytest.skip("Kick not enabled")
        
        result = platform.authenticate()
        assert isinstance(result, bool)
        
        # Kick should enable even without credentials (public API fallback)
        if result:
            assert platform.enabled == True
    
    def test_is_live_when_disabled(self, platform):
        """Test that is_live returns False when platform is disabled."""
        result, data = platform.is_live('test_user')
        assert result == False
        assert data is None
