# Test Suite Analysis & Recommendations

## Current State Analysis

### Architecture Issues

**CRITICAL**: The test suite has major inconsistencies:

1. **Dual Code Paths**: Tests import from `stream-daemon.py` (1263 lines monolith) instead of the modular `stream_daemon/` package
2. **Redundant Tests**: Multiple test files test the same functionality
3. **Inconsistent Approach**: Some tests use actual platform classes, others duplicate logic
4. **No Proper Test Framework**: Tests are scripts, not using pytest or unittest

### Test File Inventory

#### ✅ GOOD - Using Module Imports
- `test_doppler_all.py` - Orchestrator that runs other tests
- Tests that should be using `from stream_daemon.config import get_secret`

#### ⚠️ PROBLEMATIC - Importing Monolith
Tests importing via `importlib` from `stream-daemon.py`:
- `test_platforms.py` - Platform authentication tests
- `test_social.py` - Social media tests  
- `test_doppler_bluesky.py` - Bluesky + Doppler
- `test_doppler_discord.py` - Discord + Doppler
- `test_doppler_twitch.py` - Twitch + Doppler
- `test_doppler_youtube.py` - YouTube + Doppler
- `test_doppler_mastodon.py` - Mastodon + Doppler
- `test_doppler_matrix.py` - Matrix + Doppler
- `test_doppler_kick.py` - Kick + Doppler

#### ❌ REDUNDANT - Wrapper Tests
These just call other tests:
- `test_bluesky.py` - Wrapper for `test_doppler_bluesky.py`
- `test_discord.py` - Should wrap `test_doppler_discord.py`
- `test_mastodon.py` - Should wrap `test_doppler_mastodon.py`
- `test_matrix.py` - Should wrap `test_doppler_matrix.py`

#### 🤔 UNCLEAR PURPOSE
- `test_bluesky_kick_embed.py` - Specific edge case test
- `test_discord_format.py` - Format verification
- `test_discord_stream_ended.py` - End message test
- `test_discord_updates.py` - Update behavior test
- `test_announcement_behavior.py` - Behavior verification
- `test_async_posting.py` - Concurrency test
- `test_debouncing.py` - Debounce logic test
- `test_debouncing_stream_data.py` - Stream data debounce
- `test_stream_lifecycle.py` - Full lifecycle test
- `test_manual_check.py` - Manual testing script
- `test_llm.py` - AI message generation
- `test_mastodon_kick_image.py` - Image handling
- `KICK_EMBED_FIX.py` - One-off fix script
- `diagnostic_stream_data.py` - Debug utility
- `verify_discord_format.py` - Verification utility
- `verify_discord_implementation.py` - Implementation check

### Problems Identified

1. **Tests Don't Use Actual Code**: Tests import from old monolith, not refactored modules
2. **No Unified Framework**: Mix of subprocess calls, direct imports, wrappers
3. **Redundancy**: ~15 test files could be consolidated to ~5
4. **No Structure**: Not using pytest fixtures, parametrization, or test classes
5. **Hard to Maintain**: Adding new platform = creating 3+ test files

## Recommended Refactoring

### New Structure

```
tests/
├── conftest.py                    # Pytest fixtures (shared setup)
├── test_config.py                 # Config loading (env, Doppler, AWS, Vault)
├── test_streaming_platforms.py   # All streaming platforms (Twitch, YouTube, Kick)
├── test_social_platforms.py      # All social platforms (Mastodon, Bluesky, Discord, Matrix)
├── test_ai_messages.py            # LLM integration tests
├── test_integration.py            # End-to-end workflow tests
├── utils/
│   ├── __init__.py
│   └── fixtures.py                # Test data and mocks
└── README.md                      # How to run tests
```

### Implementation Plan

#### Phase 1: Setup Test Framework (Priority 1)

**File**: `tests/conftest.py`
```python
import pytest
import os
from dotenv import load_dotenv

@pytest.fixture(scope="session", autouse=True)
def load_env():
    """Load environment variables once for all tests."""
    load_dotenv()

@pytest.fixture
def mock_stream_data():
    """Provide mock stream data for testing."""
    return {
        'title': 'Test Stream',
        'game_name': 'Test Game',
        'viewer_count': 123,
        'thumbnail_url': 'https://example.com/thumb.jpg'
    }

@pytest.fixture(params=['doppler', 'aws', 'vault', 'env'])
def secret_manager(request):
    """Test with different secret managers."""
    original = os.getenv('SECRETS_SECRET_MANAGER')
    os.environ['SECRETS_SECRET_MANAGER'] = request.param
    yield request.param
    if original:
        os.environ['SECRETS_SECRET_MANAGER'] = original
```

#### Phase 2: Consolidate Platform Tests (Priority 1)

**File**: `tests/test_streaming_platforms.py`
```python
import pytest
from stream_daemon.platforms.streaming import TwitchPlatform, YouTubePlatform, KickPlatform

class TestTwitchPlatform:
    def test_authentication(self):
        """Test Twitch authentication using actual config."""
        platform = TwitchPlatform()
        assert platform.authenticate() is not None
    
    def test_is_live_check(self):
        """Test live stream detection."""
        platform = TwitchPlatform()
        platform.authenticate()
        # Use configured username from env
        username = os.getenv('TWITCH_USERNAME', 'test_user')
        is_live, data = platform.is_live(username)
        assert isinstance(is_live, bool)
        if is_live:
            assert 'title' in data

class TestYouTubePlatform:
    # Similar structure...

class TestKickPlatform:
    # Similar structure...
```

**File**: `tests/test_social_platforms.py`
```python
import pytest
from stream_daemon.platforms.social import MastodonPlatform, BlueskyPlatform, DiscordPlatform, MatrixPlatform

class TestMastodonPlatform:
    def test_authentication(self):
        platform = MastodonPlatform()
        assert platform.authenticate() is not None
    
    def test_post_message(self, mock_stream_data):
        platform = MastodonPlatform()
        platform.authenticate()
        # Test posting (may need to delete after)
        result = platform.post("Test message from automated tests")
        assert result is not None

class TestBlueskyPlatform:
    # Similar structure...
```

#### Phase 3: Config Tests (Priority 2)

**File**: `tests/test_config.py`
```python
import pytest
from stream_daemon.config import get_secret, get_config, get_bool_config

class TestSecretLoading:
    def test_doppler_secrets(self):
        """Test loading secrets from Doppler."""
        if os.getenv('SECRETS_SECRET_MANAGER') == 'doppler':
            secret = get_secret('Twitch', 'client_id')
            assert secret is not None
            assert len(secret) > 0
    
    def test_secret_priority(self):
        """Test that secret managers override env vars."""
        # Set both env var and use secret manager
        # Verify secret manager wins
        pass

class TestConfigLoading:
    def test_bool_config(self):
        """Test boolean configuration parsing."""
        assert get_bool_config('TWITCH_ENABLE', False) in [True, False]
```

#### Phase 4: Integration Tests (Priority 3)

**File**: `tests/test_integration.py`
```python
import pytest
from stream_daemon.models import StreamState

class TestStreamLifecycle:
    def test_going_live_workflow(self, mock_stream_data):
        """Test complete workflow: offline -> live -> post."""
        # This would test the actual daemon workflow
        pass
    
    def test_multi_platform_posting(self):
        """Test posting to multiple social platforms."""
        pass
```

### Migration Steps

1. **Install pytest**: Add to `requirements.txt`
   ```
   pytest>=7.4.0
   pytest-asyncio>=0.21.0
   pytest-cov>=4.1.0  # For coverage reports
   ```

2. **Create conftest.py**: Setup fixtures

3. **Migrate one platform at a time**:
   - Start with Twitch (simplest)
   - Then YouTube, Kick
   - Then social platforms
   - Finally integration tests

4. **Update documentation**: Create `tests/README.md`

5. **Remove old tests**: Archive to `tests/archive/` first

6. **Update CI/CD**: If using GitHub Actions, update to run pytest

### Benefits

- ✅ **DRY**: No redundant test files
- ✅ **Maintainable**: One test class per platform
- ✅ **Flexible**: Parametrize for different secret managers
- ✅ **Standard**: Uses pytest (industry standard)
- ✅ **Fast**: Fixtures avoid redundant setup
- ✅ **Accurate**: Tests actual code, not copy-pasted logic
- ✅ **Coverage**: Can track what's tested with pytest-cov
- ✅ **Discoverable**: `pytest -v` shows all tests

### Quick Wins (Do First)

1. **Delete obvious duplicates**:
   - Remove `test_bluesky.py`, `test_discord.py`, etc. (wrappers)
   - Keep only `test_doppler_*.py` versions

2. **Fix imports**: Update remaining tests to use:
   ```python
   from stream_daemon.platforms.streaming import TwitchPlatform
   from stream_daemon.config import get_secret
   ```
   Instead of:
   ```python
   import importlib.util
   spec = importlib.util.spec_from_file_location('stream_daemon', 'stream-daemon.py')
   ```

3. **Create basic test runner**:
   ```bash
   # tests/run_tests.sh
   #!/bin/bash
   pytest tests/ -v --tb=short
   ```

## Current Test Commands

```bash
# Old way (current)
python tests/test_doppler_all.py
python tests/test_platforms.py
python tests/run_all_tests.py

# New way (after refactor)
pytest tests/                           # Run all
pytest tests/test_streaming_platforms.py  # Run one suite
pytest tests/ -v                        # Verbose
pytest tests/ -k "twitch"              # Run only Twitch tests
pytest tests/ --cov=stream_daemon      # With coverage
```

## Questions to Answer

1. **Should tests post to real platforms?**
   - Current: Yes (can clutter timelines)
   - Recommendation: Use test accounts OR mock APIs for unit tests, real for integration

2. **Delete posted test messages?**
   - Current: No cleanup
   - Recommendation: Yes, delete in teardown

3. **Run tests in CI/CD?**
   - Current: No CI
   - Recommendation: Yes, but only with secrets in GitHub Secrets

4. **Test coverage goals?**
   - Recommendation: Aim for 80%+ on core logic (config, platforms)
   - Don't need 100% on error paths

## Estimated Effort

- **Quick cleanup** (remove wrappers, fix imports): 2 hours
- **Pytest setup + migrate 1 platform**: 3 hours  
- **Migrate all platforms**: 8 hours
- **Integration tests**: 4 hours
- **Documentation + CI/CD**: 2 hours

**Total**: ~19 hours for complete refactor

**Quick Win Path**: 5 hours gets you cleaned up tests that actually test the right code
