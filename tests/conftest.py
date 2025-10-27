"""
Pytest configuration and fixtures for Stream Daemon tests.
"""

import pytest
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
@pytest.fixture(scope="session", autouse=True)
def load_test_env():
    """Load environment variables once for all tests."""
    # Load from project root .env file
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    yield


@pytest.fixture
def mock_stream_data():
    """Provide mock stream data for testing."""
    return {
        'title': 'Test Stream Title',
        'game_name': 'Test Game',
        'viewer_count': 123,
        'thumbnail_url': 'https://example.com/thumb.jpg',
        'url': 'https://example.com/stream',
        'platform': 'test'
    }


@pytest.fixture
def test_usernames():
    """Provide test usernames from environment."""
    return {
        'twitch': os.getenv('TWITCH_USERNAME', 'test_twitch_user'),
        'youtube': os.getenv('YOUTUBE_USERNAME', 'test_youtube_user'),
        'kick': os.getenv('KICK_USERNAME', 'test_kick_user')
    }


@pytest.fixture(scope="function")
def clean_test_posts():
    """Track and cleanup test posts made during testing."""
    created_posts = []
    
    def register_post(platform, post_id):
        """Register a post for cleanup."""
        created_posts.append((platform, post_id))
    
    yield register_post
    
    # Cleanup after test
    # TODO: Implement actual cleanup once platform classes support deletion


@pytest.fixture
def skip_if_no_secrets():
    """Skip test if secret manager is not configured."""
    secret_manager = os.getenv('SECRETS_MANAGER', 'none').lower()
    if secret_manager == 'none':
        pytest.skip("No secret manager configured (set SECRETS_MANAGER)")


@pytest.fixture
def skip_if_platform_disabled():
    """Factory to skip test if specific platform is disabled."""
    def _skip(platform_name: str):
        enable_key = f"{platform_name.upper()}_ENABLE"
        if not os.getenv(enable_key, '').lower() in ('true', '1', 'yes'):
            pytest.skip(f"{platform_name} is disabled (set {enable_key}=True)")
    return _skip


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (requires real credentials)"
    )
    config.addinivalue_line(
        "markers", "streaming: mark test as streaming platform test"
    )
    config.addinivalue_line(
        "markers", "social: mark test as social platform test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "llm: mark test as requiring LLM API access"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Add integration marker to tests in specific files
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        
        # Add slow marker to lifecycle tests
        if "lifecycle" in item.nodeid or "integration" in item.nodeid:
            item.add_marker(pytest.mark.slow)
