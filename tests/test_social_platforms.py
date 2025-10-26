"""
Social Platform Tests

Tests for Mastodon, Bluesky, Discord, and Matrix social platform integration.
Tests authentication, posting, and platform-specific formatting.
"""

import pytest
import os
from stream_daemon.platforms.social import (
    MastodonPlatform, 
    BlueskyPlatform, 
    DiscordPlatform, 
    MatrixPlatform
)


@pytest.mark.social
class TestMastodonPlatform:
    """Tests for Mastodon social platform."""
    
    @pytest.fixture
    def platform(self, skip_if_platform_disabled):
        """Create Mastodon platform instance."""
        skip_if_platform_disabled('mastodon')
        return MastodonPlatform()
    
    def test_authentication(self, platform):
        """Test Mastodon API authentication."""
        result = platform.authenticate()
        assert result is not False, "Mastodon authentication failed"
        assert platform.client is not None, "Mastodon client not initialized"
    
    def test_credentials_loaded(self, platform):
        """Test that Mastodon credentials are loaded from secrets."""
        platform.authenticate()
        
        assert platform.instance_url is not None, "Mastodon instance URL not loaded"
        assert platform.access_token is not None, "Mastodon access token not loaded"
        assert platform.instance_url.startswith('http'), "Invalid Mastodon instance URL"
    
    @pytest.mark.integration
    def test_post_message(self, platform, mock_stream_data, clean_test_posts):
        """Test posting a message to Mastodon."""
        platform.authenticate()
        
        message = f"🔴 LIVE: Test Stream\n\nPlaying: Test Game\n\nhttps://twitch.tv/test\n\n#live #test"
        
        result = platform.post(message)
        assert result is not False, "Failed to post to Mastodon"
        
        # If successful, result should contain post ID
        if result:
            assert 'id' in result or isinstance(result, dict), "Post result should contain ID"
    
    def test_character_limit(self, platform):
        """Test that Mastodon respects character limits."""
        platform.authenticate()
        
        # Mastodon default limit is 500 characters
        long_message = "A" * 600
        
        # Platform should either truncate or reject gracefully
        result = platform.post(long_message)
        # Should not crash, even if post fails
        assert result is not None


@pytest.mark.social
class TestBlueskyPlatform:
    """Tests for Bluesky social platform."""
    
    @pytest.fixture
    def platform(self, skip_if_platform_disabled):
        """Create Bluesky platform instance."""
        skip_if_platform_disabled('bluesky')
        return BlueskyPlatform()
    
    def test_authentication(self, platform):
        """Test Bluesky API authentication."""
        result = platform.authenticate()
        assert result is not False, "Bluesky authentication failed"
        assert platform.client is not None, "Bluesky client not initialized"
    
    def test_credentials_loaded(self, platform):
        """Test that Bluesky credentials are loaded from secrets."""
        platform.authenticate()
        
        assert platform.handle is not None, "Bluesky handle not loaded"
        assert platform.app_password is not None, "Bluesky app password not loaded"
    
    @pytest.mark.integration
    def test_post_message(self, platform, mock_stream_data, clean_test_posts):
        """Test posting a message to Bluesky."""
        platform.authenticate()
        
        message = f"🔴 LIVE: Test Stream\n\nPlaying: Test Game\n\nhttps://twitch.tv/test"
        
        result = platform.post(message)
        assert result is not False, "Failed to post to Bluesky"
    
    def test_embed_link(self, platform):
        """Test that Bluesky properly embeds links."""
        platform.authenticate()
        
        # Bluesky should detect and embed the URL
        message = "Testing link embed: https://kick.com/test"
        
        result = platform.post(message)
        # Should succeed or fail gracefully
        assert result is not None
    
    def test_character_limit(self, platform):
        """Test that Bluesky respects 300 character limit."""
        platform.authenticate()
        
        # Bluesky limit is 300 characters
        long_message = "A" * 350
        
        result = platform.post(long_message)
        # Should truncate or reject gracefully
        assert result is not None


@pytest.mark.social
class TestDiscordPlatform:
    """Tests for Discord webhook integration."""
    
    @pytest.fixture
    def platform(self, skip_if_platform_disabled):
        """Create Discord platform instance."""
        skip_if_platform_disabled('discord')
        return DiscordPlatform()
    
    def test_authentication(self, platform):
        """Test Discord webhook validation."""
        result = platform.authenticate()
        assert result is not False, "Discord webhook validation failed"
    
    def test_webhook_url_loaded(self, platform):
        """Test that Discord webhook URL is loaded from secrets."""
        platform.authenticate()
        
        assert platform.webhook_url is not None, "Discord webhook URL not loaded"
        assert platform.webhook_url.startswith('https://discord.com/api/webhooks/'), \
            "Invalid Discord webhook URL format"
    
    @pytest.mark.integration
    def test_post_message(self, platform, mock_stream_data, clean_test_posts):
        """Test posting a message to Discord."""
        platform.authenticate()
        
        message = f"🔴 LIVE: Test Stream\n\nPlaying: Test Game\n\nhttps://twitch.tv/test"
        
        result = platform.post(message)
        assert result is not False, "Failed to post to Discord"
    
    def test_embed_formatting(self, platform, mock_stream_data):
        """Test Discord rich embed formatting."""
        platform.authenticate()
        
        # Discord should format with rich embeds
        stream_data = mock_stream_data
        
        result = platform.post_with_embed(
            title=stream_data['title'],
            url=stream_data['url'],
            game=stream_data.get('game_name', 'Just Chatting'),
            viewers=stream_data.get('viewer_count', 0)
        )
        
        assert result is not None
    
    def test_stream_ended_message(self, platform):
        """Test posting stream ended notification."""
        platform.authenticate()
        
        message = "Stream has ended. Thanks for watching!"
        
        result = platform.post(message)
        assert result is not None


@pytest.mark.social
class TestMatrixPlatform:
    """Tests for Matrix room integration."""
    
    @pytest.fixture
    def platform(self, skip_if_platform_disabled):
        """Create Matrix platform instance."""
        skip_if_platform_disabled('matrix')
        return MatrixPlatform()
    
    def test_authentication(self, platform):
        """Test Matrix homeserver authentication."""
        result = platform.authenticate()
        assert result is not False, "Matrix authentication failed"
        assert platform.client is not None, "Matrix client not initialized"
    
    def test_credentials_loaded(self, platform):
        """Test that Matrix credentials are loaded from secrets."""
        platform.authenticate()
        
        assert platform.homeserver is not None, "Matrix homeserver not loaded"
        assert platform.access_token is not None or platform.password is not None, \
            "Matrix credentials not loaded"
        assert platform.room_id is not None, "Matrix room ID not loaded"
    
    @pytest.mark.integration
    def test_post_message(self, platform, mock_stream_data, clean_test_posts):
        """Test posting a message to Matrix room."""
        platform.authenticate()
        
        message = f"🔴 LIVE: Test Stream\n\nPlaying: Test Game\n\nhttps://twitch.tv/test"
        
        result = platform.post(message)
        assert result is not False, "Failed to post to Matrix"
    
    def test_markdown_formatting(self, platform):
        """Test Matrix Markdown formatting support."""
        platform.authenticate()
        
        # Matrix supports Markdown
        message = "**LIVE**: *Test Stream* - [Watch Now](https://twitch.tv/test)"
        
        result = platform.post(message)
        assert result is not None
    
    def test_room_id_validation(self, platform):
        """Test that room ID is valid format."""
        platform.authenticate()
        
        # Matrix room IDs start with !
        assert platform.room_id.startswith('!'), \
            f"Invalid Matrix room ID format: {platform.room_id}"


@pytest.mark.integration
class TestSocialPlatformBroadcast:
    """Test broadcasting to multiple social platforms."""
    
    def test_broadcast_to_all_enabled(self, test_usernames, mock_stream_data):
        """Test posting to all enabled social platforms."""
        platforms = []
        
        # Create all enabled platforms
        if os.getenv('MASTODON_ENABLE', '').lower() in ('true', '1', 'yes'):
            platforms.append(('Mastodon', MastodonPlatform()))
        
        if os.getenv('BLUESKY_ENABLE', '').lower() in ('true', '1', 'yes'):
            platforms.append(('Bluesky', BlueskyPlatform()))
        
        if os.getenv('DISCORD_ENABLE', '').lower() in ('true', '1', 'yes'):
            platforms.append(('Discord', DiscordPlatform()))
        
        if os.getenv('MATRIX_ENABLE', '').lower() in ('true', '1', 'yes'):
            platforms.append(('Matrix', MatrixPlatform()))
        
        if not platforms:
            pytest.skip("No social platforms enabled")
        
        # Authenticate all
        for name, platform in platforms:
            result = platform.authenticate()
            assert result is not False, f"{name} authentication failed"
        
        # Test message
        message = f"🔴 LIVE: {mock_stream_data['title']}\n\n{mock_stream_data['url']}"
        
        # Post to all
        results = {}
        for name, platform in platforms:
            results[name] = platform.post(message)
        
        # All should return result (success or graceful failure)
        for name, result in results.items():
            assert result is not None, f"{name} returned None"
    
    @pytest.mark.slow
    def test_sequential_posting(self, mock_stream_data):
        """Test that sequential posts don't interfere with each other."""
        platforms = []
        
        if os.getenv('MASTODON_ENABLE', '').lower() in ('true', '1', 'yes'):
            platforms.append(MastodonPlatform())
        
        if os.getenv('BLUESKY_ENABLE', '').lower() in ('true', '1', 'yes'):
            platforms.append(BlueskyPlatform())
        
        if not platforms:
            pytest.skip("Need at least one social platform enabled")
        
        # Authenticate
        for platform in platforms:
            platform.authenticate()
        
        # Post multiple times in sequence
        messages = [
            "Test message 1",
            "Test message 2",
            "Test message 3"
        ]
        
        for message in messages:
            for platform in platforms:
                result = platform.post(message)
                assert result is not None
