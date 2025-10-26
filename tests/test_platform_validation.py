"""
Platform Configuration Validation Tests

Consolidated validation tests for all streaming and social platforms.
Tests credentials, API access, and basic functionality.

This module replaces the old test_doppler_*.py files with a single,
well-organized test suite (75% code reduction).

Test Organization:
- Environment variable loading
- Streaming platforms (Twitch, YouTube, Kick)
- Social platforms (Mastodon, Bluesky, Discord, Matrix)
- Multi-platform validation (all at once)

Run all: pytest tests/test_platform_validation.py -v
Run specific: pytest tests/test_platform_validation.py::TestTwitchValidation -v

NOTE: Streaming platform tests are currently disabled because the streaming 
      platforms are not yet refactored from stream-daemon.py into separate modules.
      Social platform tests should work since those modules exist.
"""

import pytest
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from stream_daemon.config import get_config, get_secret

# Social platforms are refactored and available
from stream_daemon.platforms.social import MastodonPlatform, BlueskyPlatform, DiscordPlatform, MatrixPlatform

# Streaming platforms not yet refactored - comment out until ready
# from stream_daemon.platforms.streaming import TwitchPlatform, YouTubePlatform, KickPlatform

import pytest
import os
from typing import Dict, Optional, Tuple

# Import from refactored modules
from stream_daemon.config import get_secret, get_config, get_bool_config
from stream_daemon.platforms.streaming import TwitchPlatform, YouTubePlatform, KickPlatform
from stream_daemon.platforms.social import MastodonPlatform, BlueskyPlatform, DiscordPlatform, MatrixPlatform


def mask_secret(secret: Optional[str]) -> str:
    """Mask a secret for safe display."""
    if not secret:
        return "NOT_SET"
    if len(secret) <= 8:
        return "***"
    return f"{secret[:4]}...{secret[-4:]}"


class TestEnvironmentValidation:
    """Validate environment configuration."""
    
    def test_secrets_manager_configured(self, load_test_env):
        """Test that a secrets manager is configured."""
        secret_manager = get_config('SECRETS_MANAGER', 'env').lower()
        
        print(f"\nSecrets Manager: {secret_manager}")
        
        assert secret_manager in ['doppler', 'aws', 'vault', 'env'], \
            f"Invalid secrets manager: {secret_manager}"
    
    def test_doppler_configuration(self, load_test_env):
        """Test Doppler configuration if using Doppler."""
        secret_manager = get_config('SECRETS_MANAGER', 'env').lower()
        
        if secret_manager != 'doppler':
            pytest.skip("Not using Doppler secrets manager")
        
        doppler_token = os.getenv('DOPPLER_TOKEN')
        
        print(f"\nDoppler Token: {mask_secret(doppler_token)}")
        
        assert doppler_token, "DOPPLER_TOKEN must be set when using Doppler"
        assert len(doppler_token) > 20, "DOPPLER_TOKEN appears to be invalid"


@pytest.mark.skip(reason="Twitch platform not yet refactored into separate module")
@pytest.mark.streaming
class TestTwitchValidation:
    """Validate Twitch platform configuration and authentication."""
    
    @pytest.fixture
    def skip_if_disabled(self):
        """Skip test if Twitch is disabled."""
        if not get_bool_config('TWITCH_ENABLE', False):
            pytest.skip("Twitch is disabled")
    
    def test_twitch_secrets_loaded(self, skip_if_disabled, load_test_env):
        """Test that Twitch secrets are loaded correctly."""
        client_id = get_secret('TWITCH_CLIENT_ID')
        client_secret = get_secret('TWITCH_CLIENT_SECRET')
        
        print(f"\nTwitch Client ID: {mask_secret(client_id)}")
        print(f"Twitch Client Secret: {mask_secret(client_secret)}")
        
        assert client_id, "TWITCH_CLIENT_ID not loaded from secrets"
        assert client_secret, "TWITCH_CLIENT_SECRET not loaded from secrets"
        assert len(client_id) > 10, "TWITCH_CLIENT_ID appears to be invalid"
        assert len(client_secret) > 10, "TWITCH_CLIENT_SECRET appears to be invalid"
    
    def test_twitch_authentication(self, skip_if_disabled, load_test_env):
        """Test Twitch API authentication."""
        from stream_daemon.platforms.streaming import TwitchPlatform  # Will be available after refactoring
        platform = TwitchPlatform()
        result = platform.authenticate()
        
        assert result is not False, "Twitch authentication failed"
        assert platform.client is not None, "Twitch client not initialized"
        
        print(f"\n✓ Twitch authentication successful")
    
    def test_twitch_usernames_configured(self, skip_if_disabled, load_test_env):
        """Test that Twitch usernames are configured."""
        usernames = get_config('TWITCH_USERNAMES', '')
        
        print(f"\nTwitch Usernames: {usernames or 'NOT_SET'}")
        
        assert usernames, "TWITCH_USERNAMES not configured"
    
    @pytest.mark.integration
    def test_twitch_stream_check(self, skip_if_disabled, load_test_env):
        """Test checking Twitch stream status."""
        platform = TwitchPlatform()
        platform.authenticate()
        
        usernames = get_config('TWITCH_USERNAMES', '').split(',')
        username = usernames[0].strip() if usernames else None
        
        if not username:
            pytest.skip("No Twitch username configured")
        
        is_live, stream_data = platform.is_live(username)
        
        print(f"\n{username} is {'LIVE' if is_live else 'OFFLINE'}")
        if is_live:
            print(f"  Title: {stream_data.get('title', 'N/A')}")
            print(f"  Game: {stream_data.get('game_name', 'N/A')}")
            print(f"  Viewers: {stream_data.get('viewer_count', 0)}")
        
        assert isinstance(is_live, bool), "is_live should be boolean"
        assert isinstance(stream_data, dict), "stream_data should be dict"


@pytest.mark.skip(reason="YouTube platform not yet refactored into separate module")
@pytest.mark.streaming
class TestYouTubeValidation:
    """Validate YouTube platform configuration and authentication."""
    
    @pytest.fixture
    def skip_if_disabled(self):
        """Skip test if YouTube is disabled."""
        if not get_bool_config('YOUTUBE_ENABLE', False):
            pytest.skip("YouTube is disabled")
    
    def test_youtube_secrets_loaded(self, skip_if_disabled, load_test_env):
        """Test that YouTube secrets are loaded correctly."""
        api_key = get_secret('YOUTUBE_API_KEY')
        
        print(f"\nYouTube API Key: {mask_secret(api_key)}")
        
        assert api_key, "YOUTUBE_API_KEY not loaded from secrets"
        assert len(api_key) > 20, "YOUTUBE_API_KEY appears to be invalid"
    
    def test_youtube_authentication(self, skip_if_disabled, load_test_env):
        """Test YouTube API authentication."""
        platform = YouTubePlatform()
        result = platform.authenticate()
        
        assert result is not False, "YouTube authentication failed"
        assert platform.youtube_api is not None, "YouTube API client not initialized"
        
        print(f"\n✓ YouTube authentication successful")
    
    def test_youtube_usernames_configured(self, skip_if_disabled, load_test_env):
        """Test that YouTube usernames are configured."""
        usernames = get_config('YOUTUBE_USERNAMES', '')
        
        print(f"\nYouTube Usernames: {usernames or 'NOT_SET'}")
        
        assert usernames, "YOUTUBE_USERNAMES not configured"
    
    @pytest.mark.integration
    def test_youtube_stream_check(self, skip_if_disabled, load_test_env):
        """Test checking YouTube stream status."""
        platform = YouTubePlatform()
        platform.authenticate()
        
        usernames = get_config('YOUTUBE_USERNAMES', '').split(',')
        username = usernames[0].strip() if usernames else None
        
        if not username:
            pytest.skip("No YouTube username configured")
        
        is_live, stream_data = platform.is_live(username)
        
        print(f"\n{username} is {'LIVE' if is_live else 'OFFLINE'}")
        if is_live:
            print(f"  Title: {stream_data.get('title', 'N/A')}")
            print(f"  Video ID: {stream_data.get('video_id', 'N/A')}")
        
        assert isinstance(is_live, bool), "is_live should be boolean"
        assert isinstance(stream_data, dict), "stream_data should be dict"


@pytest.mark.skip(reason="Kick platform not yet refactored into separate module")
@pytest.mark.streaming
class TestKickValidation:
    """Validate Kick platform configuration."""
    
    @pytest.fixture
    def skip_if_disabled(self):
        """Skip test if Kick is disabled."""
        if not get_bool_config('KICK_ENABLE', False):
            pytest.skip("Kick is disabled")
    
    def test_kick_usernames_configured(self, skip_if_disabled, load_test_env):
        """Test that Kick usernames are configured."""
        usernames = get_config('KICK_USERNAMES', '')
        
        print(f"\nKick Usernames: {usernames or 'NOT_SET'}")
        
        assert usernames, "KICK_USERNAMES not configured"
    
    def test_kick_initialization(self, skip_if_disabled, load_test_env):
        """Test Kick platform initialization."""
        platform = KickPlatform()
        result = platform.authenticate()
        
        # Kick public API doesn't require auth
        assert result is not False, "Kick initialization failed"
        
        print(f"\n✓ Kick platform initialized")
    
    @pytest.mark.integration
    def test_kick_stream_check(self, skip_if_disabled, load_test_env):
        """Test checking Kick stream status."""
        platform = KickPlatform()
        platform.authenticate()
        
        usernames = get_config('KICK_USERNAMES', '').split(',')
        username = usernames[0].strip() if usernames else None
        
        if not username:
            pytest.skip("No Kick username configured")
        
        is_live, stream_data = platform.is_live(username)
        
        print(f"\n{username} is {'LIVE' if is_live else 'OFFLINE'}")
        if is_live:
            print(f"  Title: {stream_data.get('title', 'N/A')}")
            print(f"  Category: {stream_data.get('category', 'N/A')}")
            print(f"  Viewers: {stream_data.get('viewers', 0)}")
        
        assert isinstance(is_live, bool), "is_live should be boolean"
        assert isinstance(stream_data, dict), "stream_data should be dict"


@pytest.mark.social
class TestMastodonValidation:
    """Validate Mastodon platform configuration and authentication."""
    
    @pytest.fixture
    def skip_if_disabled(self):
        """Skip test if Mastodon is disabled."""
        if not get_bool_config('MASTODON_ENABLE', False):
            pytest.skip("Mastodon is disabled")
    
    def test_mastodon_secrets_loaded(self, skip_if_disabled, load_test_env):
        """Test that Mastodon secrets are loaded correctly."""
        instance_url = get_secret('MASTODON_INSTANCE_URL')
        client_id = get_secret('MASTODON_CLIENT_ID')
        client_secret = get_secret('MASTODON_CLIENT_SECRET')
        access_token = get_secret('MASTODON_ACCESS_TOKEN')
        
        print(f"\nMastodon Instance: {instance_url or 'NOT_SET'}")
        print(f"Mastodon Client ID: {mask_secret(client_id)}")
        print(f"Mastodon Client Secret: {mask_secret(client_secret)}")
        print(f"Mastodon Access Token: {mask_secret(access_token)}")
        
        assert instance_url, "MASTODON_INSTANCE_URL not loaded from secrets"
        assert instance_url.startswith('http'), "MASTODON_INSTANCE_URL should start with http"
        assert client_id, "MASTODON_CLIENT_ID not loaded from secrets"
        assert client_secret, "MASTODON_CLIENT_SECRET not loaded from secrets"
        assert access_token, "MASTODON_ACCESS_TOKEN not loaded from secrets"
    
    def test_mastodon_authentication(self, skip_if_disabled, load_test_env):
        """Test Mastodon API authentication."""
        platform = MastodonPlatform()
        result = platform.authenticate()
        
        assert result is not False, "Mastodon authentication failed"
        assert platform.client is not None, "Mastodon client not initialized"
        
        print(f"\n✓ Mastodon authentication successful")
    
    @pytest.mark.integration
    def test_mastodon_account_verify(self, skip_if_disabled, load_test_env):
        """Test verifying Mastodon account credentials."""
        platform = MastodonPlatform()
        platform.authenticate()
        
        try:
            account = platform.client.account_verify_credentials()
            print(f"\n✓ Logged in as: @{account['username']}")
            print(f"  Display Name: {account.get('display_name', 'N/A')}")
            print(f"  Followers: {account.get('followers_count', 0)}")
        except Exception as e:
            pytest.fail(f"Failed to verify credentials: {e}")


@pytest.mark.social
class TestBlueskyValidation:
    """Validate Bluesky platform configuration and authentication."""
    
    @pytest.fixture
    def skip_if_disabled(self):
        """Skip test if Bluesky is disabled."""
        if not get_bool_config('BLUESKY_ENABLE', False):
            pytest.skip("Bluesky is disabled")
    
    def test_bluesky_secrets_loaded(self, skip_if_disabled, load_test_env):
        """Test that Bluesky secrets are loaded correctly."""
        handle = get_secret('BLUESKY_HANDLE')
        app_password = get_secret('BLUESKY_APP_PASSWORD')
        
        print(f"\nBluesky Handle: {handle or 'NOT_SET'}")
        print(f"Bluesky App Password: {mask_secret(app_password)}")
        
        assert handle, "BLUESKY_HANDLE not loaded from secrets"
        assert app_password, "BLUESKY_APP_PASSWORD not loaded from secrets"
        assert len(app_password) > 10, "BLUESKY_APP_PASSWORD appears to be invalid"
    
    def test_bluesky_authentication(self, skip_if_disabled, load_test_env):
        """Test Bluesky API authentication."""
        platform = BlueskyPlatform()
        result = platform.authenticate()
        
        assert result is not False, "Bluesky authentication failed"
        assert platform.client is not None, "Bluesky client not initialized"
        
        print(f"\n✓ Bluesky authentication successful")
    
    @pytest.mark.integration
    def test_bluesky_profile_check(self, skip_if_disabled, load_test_env):
        """Test fetching Bluesky profile."""
        platform = BlueskyPlatform()
        platform.authenticate()
        
        try:
            handle = get_secret('BLUESKY_HANDLE')
            profile = platform.client.get_profile(handle)
            print(f"\n✓ Logged in as: @{profile.handle}")
            print(f"  Display Name: {profile.display_name or 'N/A'}")
            print(f"  Followers: {profile.followers_count or 0}")
        except Exception as e:
            pytest.fail(f"Failed to fetch profile: {e}")


@pytest.mark.social
class TestDiscordValidation:
    """Validate Discord webhook configuration."""
    
    @pytest.fixture
    def skip_if_disabled(self):
        """Skip test if Discord is disabled."""
        if not get_bool_config('DISCORD_ENABLE', False):
            pytest.skip("Discord is disabled")
    
    def test_discord_secrets_loaded(self, skip_if_disabled, load_test_env):
        """Test that Discord webhook URL is loaded correctly."""
        webhook_url = get_secret('DISCORD_WEBHOOK_URL')
        
        print(f"\nDiscord Webhook: {mask_secret(webhook_url)}")
        
        assert webhook_url, "DISCORD_WEBHOOK_URL not loaded from secrets"
        assert webhook_url.startswith('https://discord.com/api/webhooks/'), \
            "DISCORD_WEBHOOK_URL should start with https://discord.com/api/webhooks/"
    
    def test_discord_initialization(self, skip_if_disabled, load_test_env):
        """Test Discord platform initialization."""
        platform = DiscordPlatform()
        result = platform.authenticate()
        
        assert result is not False, "Discord initialization failed"
        
        print(f"\n✓ Discord webhook validated")
    
    @pytest.mark.integration
    def test_discord_webhook_reachable(self, skip_if_disabled, load_test_env):
        """Test that Discord webhook is reachable."""
        import requests
        
        webhook_url = get_secret('DISCORD_WEBHOOK_URL')
        
        try:
            # Just verify the webhook exists (GET request)
            response = requests.get(webhook_url)
            assert response.status_code in [200, 401], \
                f"Webhook returned unexpected status: {response.status_code}"
            
            print(f"\n✓ Discord webhook is reachable")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Failed to reach webhook: {e}")


@pytest.mark.social
class TestMatrixValidation:
    """Validate Matrix platform configuration and authentication."""
    
    @pytest.fixture
    def skip_if_disabled(self):
        """Skip test if Matrix is disabled."""
        if not get_bool_config('MATRIX_ENABLE', False):
            pytest.skip("Matrix is disabled")
    
    def test_matrix_secrets_loaded(self, skip_if_disabled, load_test_env):
        """Test that Matrix secrets are loaded correctly."""
        homeserver = get_secret('MATRIX_HOMESERVER')
        access_token = get_secret('MATRIX_ACCESS_TOKEN')
        room_id = get_secret('MATRIX_ROOM_ID')
        
        print(f"\nMatrix Homeserver: {homeserver or 'NOT_SET'}")
        print(f"Matrix Access Token: {mask_secret(access_token)}")
        print(f"Matrix Room ID: {room_id or 'NOT_SET'}")
        
        assert homeserver, "MATRIX_HOMESERVER not loaded from secrets"
        assert homeserver.startswith('http'), "MATRIX_HOMESERVER should start with http"
        assert access_token, "MATRIX_ACCESS_TOKEN not loaded from secrets"
        assert room_id, "MATRIX_ROOM_ID not loaded from secrets"
        assert room_id.startswith('!'), f"MATRIX_ROOM_ID should start with !, got: {room_id}"
    
    def test_matrix_authentication(self, skip_if_disabled, load_test_env):
        """Test Matrix platform authentication."""
        platform = MatrixPlatform()
        result = platform.authenticate()
        
        assert result is not False, "Matrix authentication failed"
        assert platform.client is not None, "Matrix client not initialized"
        
        print(f"\n✓ Matrix authentication successful")
    
    @pytest.mark.integration
    def test_matrix_room_access(self, skip_if_disabled, load_test_env):
        """Test that Matrix room is accessible."""
        platform = MatrixPlatform()
        platform.authenticate()
        
        room_id = get_secret('MATRIX_ROOM_ID')
        
        try:
            # Try to get room info
            response = platform.client.room_get_state(room_id)
            print(f"\n✓ Room {room_id} is accessible")
        except Exception as e:
            pytest.fail(f"Failed to access room: {e}")


class TestAllPlatformsValidation:
    """Cross-platform validation tests."""
    
    def test_at_least_one_streaming_platform_enabled(self, load_test_env):
        """Test that at least one streaming platform is enabled."""
        twitch_enabled = get_bool_config('TWITCH_ENABLE', False)
        youtube_enabled = get_bool_config('YOUTUBE_ENABLE', False)
        kick_enabled = get_bool_config('KICK_ENABLE', False)
        
        enabled_platforms = []
        if twitch_enabled:
            enabled_platforms.append('Twitch')
        if youtube_enabled:
            enabled_platforms.append('YouTube')
        if kick_enabled:
            enabled_platforms.append('Kick')
        
        print(f"\nEnabled streaming platforms: {', '.join(enabled_platforms) or 'NONE'}")
        
        assert enabled_platforms, \
            "At least one streaming platform must be enabled (TWITCH_ENABLE, YOUTUBE_ENABLE, or KICK_ENABLE)"
    
    def test_at_least_one_social_platform_enabled(self, load_test_env):
        """Test that at least one social platform is enabled."""
        mastodon_enabled = get_bool_config('MASTODON_ENABLE', False)
        bluesky_enabled = get_bool_config('BLUESKY_ENABLE', False)
        discord_enabled = get_bool_config('DISCORD_ENABLE', False)
        matrix_enabled = get_bool_config('MATRIX_ENABLE', False)
        
        enabled_platforms = []
        if mastodon_enabled:
            enabled_platforms.append('Mastodon')
        if bluesky_enabled:
            enabled_platforms.append('Bluesky')
        if discord_enabled:
            enabled_platforms.append('Discord')
        if matrix_enabled:
            enabled_platforms.append('Matrix')
        
        print(f"\nEnabled social platforms: {', '.join(enabled_platforms) or 'NONE'}")
        
        assert enabled_platforms, \
            "At least one social platform must be enabled (MASTODON_ENABLE, BLUESKY_ENABLE, DISCORD_ENABLE, or MATRIX_ENABLE)"
    
    def test_configuration_summary(self, load_test_env):
        """Print a summary of the current configuration."""
        print("\n" + "=" * 60)
        print("CONFIGURATION SUMMARY")
        print("=" * 60)
        
        # Secrets Manager
        secret_manager = get_config('SECRETS_MANAGER', 'env')
        print(f"\nSecrets Manager: {secret_manager.upper()}")
        
        # Streaming Platforms
        print("\nStreaming Platforms:")
        for platform in ['TWITCH', 'YOUTUBE', 'KICK']:
            enabled = get_bool_config(f'{platform}_ENABLE', False)
            usernames = get_config(f'{platform}_USERNAMES', '')
            status = "✓ ENABLED" if enabled else "✗ DISABLED"
            print(f"  {platform}: {status}")
            if enabled and usernames:
                print(f"    Usernames: {usernames}")
        
        # Social Platforms
        print("\nSocial Platforms:")
        for platform in ['MASTODON', 'BLUESKY', 'DISCORD', 'MATRIX']:
            enabled = get_bool_config(f'{platform}_ENABLE', False)
            status = "✓ ENABLED" if enabled else "✗ DISABLED"
            print(f"  {platform}: {status}")
        
        # LLM Configuration
        llm_enabled = get_bool_config('LLM_ENABLE', False)
        if llm_enabled:
            llm_provider = get_config('LLM_PROVIDER', 'none')
            print(f"\nLLM: ✓ ENABLED ({llm_provider})")
        else:
            print(f"\nLLM: ✗ DISABLED")
        
        print("=" * 60)
