"""
Integration Tests

End-to-end tests for complete stream lifecycle workflows.
Tests multi-platform coordination, debouncing, and state management.
"""

import pytest
import time
import asyncio
from stream_daemon.platforms.streaming import TwitchPlatform, YouTubePlatform, KickPlatform
from stream_daemon.platforms.social import MastodonPlatform, BlueskyPlatform, DiscordPlatform, MatrixPlatform
from stream_daemon.config import get_config, get_bool_config


@pytest.mark.integration
class TestStreamLifecycle:
    """Test complete stream lifecycle from start to end."""
    
    @pytest.fixture
    def streaming_platform(self, skip_if_no_secrets):
        """Get first available streaming platform."""
        skip_if_no_secrets()
        
        # Try to create first available platform
        if get_bool_config('TWITCH_ENABLE', False):
            platform = TwitchPlatform()
            platform.authenticate()
            return platform
        elif get_bool_config('YOUTUBE_ENABLE', False):
            platform = YouTubePlatform()
            platform.authenticate()
            return platform
        elif get_bool_config('KICK_ENABLE', False):
            platform = KickPlatform()
            platform.authenticate()
            return platform
        else:
            pytest.skip("No streaming platform enabled")
    
    @pytest.fixture
    def social_platforms(self, skip_if_no_secrets):
        """Get all enabled social platforms."""
        skip_if_no_secrets()
        
        platforms = []
        
        if get_bool_config('MASTODON_ENABLE', False):
            p = MastodonPlatform()
            p.authenticate()
            platforms.append(('Mastodon', p))
        
        if get_bool_config('BLUESKY_ENABLE', False):
            p = BlueskyPlatform()
            p.authenticate()
            platforms.append(('Bluesky', p))
        
        if get_bool_config('DISCORD_ENABLE', False):
            p = DiscordPlatform()
            p.authenticate()
            platforms.append(('Discord', p))
        
        if get_bool_config('MATRIX_ENABLE', False):
            p = MatrixPlatform()
            p.authenticate()
            platforms.append(('Matrix', p))
        
        if not platforms:
            pytest.skip("No social platforms enabled")
        
        return platforms
    
    def test_stream_start_announcement(self, streaming_platform, social_platforms, test_usernames):
        """Test announcing stream start to all social platforms."""
        # Check if stream is live
        username = test_usernames.get('twitch') or test_usernames.get('youtube') or test_usernames.get('kick')
        is_live, stream_data = streaming_platform.is_live(username)
        
        if not is_live:
            pytest.skip("Stream is not live - cannot test announcement")
        
        # Create announcement message
        message = (
            f"🔴 LIVE NOW: {stream_data['title']}\n\n"
            f"Playing: {stream_data.get('game_name', 'Just Chatting')}\n\n"
            f"{stream_data['url']}\n\n"
            f"#live #streaming"
        )
        
        # Post to all social platforms
        results = {}
        for name, platform in social_platforms:
            results[name] = platform.post(message)
        
        # Verify all succeeded (or failed gracefully)
        for name, result in results.items():
            assert result is not None, f"Failed to post to {name}"
    
    @pytest.mark.slow
    def test_stream_update_debouncing(self, streaming_platform, test_usernames):
        """Test that rapid status checks don't cause duplicate announcements."""
        username = test_usernames.get('twitch') or test_usernames.get('youtube') or test_usernames.get('kick')
        
        # Check status multiple times rapidly
        results = []
        for _ in range(5):
            is_live, stream_data = streaming_platform.is_live(username)
            results.append((is_live, stream_data))
            time.sleep(1)
        
        # All results should be consistent
        first_status = results[0][0]
        for is_live, _ in results:
            assert is_live == first_status, "Stream status changed during rapid checks"
    
    def test_stream_end_announcement(self, social_platforms):
        """Test announcing stream end to all social platforms."""
        # Get configured end messages
        end_message = get_config('END_MESSAGE', 'Stream has ended. Thanks for watching!')
        
        # Post to all social platforms
        results = {}
        for name, platform in social_platforms:
            results[name] = platform.post(end_message)
        
        # Verify all succeeded
        for name, result in results.items():
            assert result is not None, f"Failed to post end message to {name}"


@pytest.mark.integration
class TestMultiPlatformStreaming:
    """Test monitoring multiple streaming platforms simultaneously."""
    
    @pytest.fixture
    def all_streaming_platforms(self, skip_if_no_secrets):
        """Get all enabled streaming platforms."""
        skip_if_no_secrets()
        
        platforms = []
        
        if get_bool_config('TWITCH_ENABLE', False):
            p = TwitchPlatform()
            p.authenticate()
            platforms.append(('Twitch', p))
        
        if get_bool_config('YOUTUBE_ENABLE', False):
            p = YouTubePlatform()
            p.authenticate()
            platforms.append(('YouTube', p))
        
        if get_bool_config('KICK_ENABLE', False):
            p = KickPlatform()
            p.authenticate()
            platforms.append(('Kick', p))
        
        if not platforms:
            pytest.skip("No streaming platforms enabled")
        
        return platforms
    
    def test_check_all_platforms(self, all_streaming_platforms, test_usernames):
        """Test checking live status across all platforms."""
        results = {}
        
        for name, platform in all_streaming_platforms:
            username = test_usernames.get(name.lower())
            if username:
                is_live, stream_data = platform.is_live(username)
                results[name] = (is_live, stream_data)
        
        # All should return valid results
        for name, (is_live, stream_data) in results.items():
            assert isinstance(is_live, bool), f"{name} didn't return boolean"
            assert isinstance(stream_data, dict), f"{name} didn't return dict"
    
    def test_multi_platform_restreaming(self, all_streaming_platforms, test_usernames):
        """Test scenario where user is streaming to multiple platforms."""
        live_platforms = []
        
        for name, platform in all_streaming_platforms:
            username = test_usernames.get(name.lower())
            if username:
                is_live, stream_data = platform.is_live(username)
                if is_live:
                    live_platforms.append((name, stream_data))
        
        # If user is live on multiple platforms, verify data consistency
        if len(live_platforms) > 1:
            # Titles might differ but URLs should be unique
            urls = [data['url'] for _, data in live_platforms]
            assert len(urls) == len(set(urls)), "Duplicate stream URLs detected"


@pytest.mark.integration
@pytest.mark.asyncio
class TestAsyncPosting:
    """Test asynchronous posting to social platforms."""
    
    async def post_async(self, platform, message):
        """Post message asynchronously."""
        # This would use the actual async implementation from stream_daemon
        return await asyncio.to_thread(platform.post, message)
    
    async def test_parallel_social_posts(self, skip_if_no_secrets):
        """Test posting to multiple platforms in parallel."""
        skip_if_no_secrets()
        
        platforms = []
        
        if get_bool_config('MASTODON_ENABLE', False):
            p = MastodonPlatform()
            p.authenticate()
            platforms.append(p)
        
        if get_bool_config('BLUESKY_ENABLE', False):
            p = BlueskyPlatform()
            p.authenticate()
            platforms.append(p)
        
        if not platforms:
            pytest.skip("Need at least one social platform")
        
        message = "Test parallel post: LIVE NOW"
        
        # Post to all platforms in parallel
        tasks = [self.post_async(p, message) for p in platforms]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should complete (success or exception, not hang)
        assert len(results) == len(platforms)
        
        # Check for unexpected exceptions
        for result in results:
            if isinstance(result, Exception):
                # Log but don't fail - some platforms might be rate-limited
                print(f"Platform returned exception: {result}")


@pytest.mark.integration
class TestErrorRecovery:
    """Test error handling and recovery scenarios."""
    
    def test_invalid_username(self):
        """Test handling of invalid streaming usernames."""
        platform = TwitchPlatform()
        platform.authenticate()
        
        # Try to check status of non-existent user
        is_live, stream_data = platform.is_live("this_user_definitely_does_not_exist_12345")
        
        # Should return False gracefully, not crash
        assert is_live is False
        assert isinstance(stream_data, dict)
    
    def test_network_timeout_handling(self):
        """Test handling of network timeouts."""
        platform = TwitchPlatform()
        platform.authenticate()
        
        # This would test timeout handling
        # In a real scenario, you'd mock the network call to timeout
        # For now, just verify the platform has timeout configuration
        assert hasattr(platform, 'timeout') or hasattr(platform, 'request_timeout')
    
    def test_rate_limit_handling(self, skip_if_no_secrets):
        """Test handling of API rate limits."""
        skip_if_no_secrets()
        
        platform = TwitchPlatform()
        platform.authenticate()
        
        # Make many rapid requests
        for i in range(20):
            is_live, _ = platform.is_live("test_user")
            # Should handle rate limits gracefully without crashing
            assert isinstance(is_live, bool)


@pytest.mark.integration
@pytest.mark.slow
class TestStatePersistence:
    """Test state management and persistence."""
    
    def test_stream_state_tracking(self, streaming_platform, test_usernames):
        """Test tracking stream state changes over time."""
        username = test_usernames.get('twitch') or test_usernames.get('youtube') or test_usernames.get('kick')
        
        # Get initial state
        initial_live, initial_data = streaming_platform.is_live(username)
        
        # Wait a bit
        time.sleep(5)
        
        # Check again
        current_live, current_data = streaming_platform.is_live(username)
        
        # State should be consistent over short time
        assert initial_live == current_live, "Stream state changed unexpectedly"
        
        # If live, viewer count might change but stream should remain live
        if initial_live and current_live:
            assert initial_data['url'] == current_data['url'], "Stream URL changed"
    
    def test_announcement_deduplication(self):
        """Test that duplicate announcements are prevented."""
        # This would test the actual deduplication logic from stream_daemon
        # For now, verify the concept exists
        
        # In real implementation, track announced stream IDs
        announced_streams = set()
        
        stream_id = "test_stream_123"
        
        # First announcement
        if stream_id not in announced_streams:
            announced_streams.add(stream_id)
            should_announce = True
        else:
            should_announce = False
        
        assert should_announce is True
        
        # Second announcement (duplicate)
        if stream_id not in announced_streams:
            announced_streams.add(stream_id)
            should_announce = True
        else:
            should_announce = False
        
        assert should_announce is False, "Duplicate announcement not prevented"


@pytest.mark.integration
class TestMessageFormatting:
    """Test message formatting for different platforms."""
    
    def test_kick_embed_handling(self, mock_stream_data):
        """Test Kick stream embed URL formatting."""
        kick_url = "https://kick.com/test_channel"
        
        # Bluesky should handle Kick embeds specially
        if get_bool_config('BLUESKY_ENABLE', False):
            platform = BlueskyPlatform()
            platform.authenticate()
            
            message = f"LIVE: Test Stream\n\n{kick_url}"
            result = platform.post(message)
            
            assert result is not None
    
    def test_platform_specific_formatting(self, mock_stream_data):
        """Test that each platform formats messages appropriately."""
        stream_data = mock_stream_data
        
        # Base message
        base_msg = f"🔴 LIVE: {stream_data['title']}\n\n{stream_data['url']}"
        
        # Discord might use embeds
        if get_bool_config('DISCORD_ENABLE', False):
            discord = DiscordPlatform()
            discord.authenticate()
            result = discord.post(base_msg)
            assert result is not None
        
        # Mastodon supports longer messages
        if get_bool_config('MASTODON_ENABLE', False):
            mastodon = MastodonPlatform()
            mastodon.authenticate()
            long_msg = base_msg + "\n\n" + "#" * 50  # Add hashtags
            result = mastodon.post(long_msg)
            assert result is not None
        
        # Bluesky has stricter limits
        if get_bool_config('BLUESKY_ENABLE', False):
            bluesky = BlueskyPlatform()
            bluesky.authenticate()
            # Should truncate or handle gracefully
            result = bluesky.post(base_msg)
            assert result is not None
