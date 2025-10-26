# Test Suite Documentation# Stream Daemon Test Suite



This directory contains the comprehensive test suite for the Stream Daemon project. Tests are organized using pytest and follow best practices for Python testing.Comprehensive test suite for validating Doppler secrets and platform connectivity.



## Table of Contents## 🎯 Purpose



- [Test Structure](#test-structure)These tests ensure:

- [Running Tests](#running-tests)- ✅ Doppler secrets are properly configured

- [Test Organization](#test-organization)- ✅ Platform authentication works correctly

- [Configuration](#configuration)- ✅ Stream detection methods function as expected

- [Writing Tests](#writing-tests)- ✅ No credentials are leaked in output

- [CI/CD Integration](#cicd-integration)

## 📋 Prerequisites

## Test Structure

1. **Doppler Account** - Sign up at https://doppler.com

### Test Files2. **Doppler CLI** - Install and run `doppler setup` in project directory

3. **Platform Credentials** - Configure secrets in Doppler (see `DOPPLER_SECRETS.md`)

- **conftest.py** - Pytest configuration and shared fixtures4. **Environment Variables** - Configure `.env` file with test usernames

- **test_config.py** - Configuration and secrets management tests

- **test_streaming_platforms.py** - Twitch, YouTube, and Kick platform tests> **📌 Important:** Doppler tokens are environment-specific. A `dev` token only accesses `dev` secrets, `stg` only accesses `stg`, etc. Choose your environment (`dev`/`stg`/`prd`) in both your token generation and `DOPPLER_CONFIG` setting. See [DOPPLER_GUIDE.md](../DOPPLER_GUIDE.md) for details.

- **test_social_platforms.py** - Mastodon, Bluesky, Discord, and Matrix tests

- **test_integration.py** - End-to-end workflow and lifecycle tests## ⚙️ Test Configuration



### Legacy Tests (Being Updated)Tests are configured via **environment variables** in your `.env` file, **not hardcoded values**. This makes tests portable and easy to customize for different environments.



The following files are being updated to use the new pytest framework:### Required Username Configuration



- `test_doppler_*.py` - Platform-specific tests (9 files)Add these to your `.env` file to control which channels are tested:

- `test_llm.py` - LLM integration tests

- `test_announcement_behavior.py` - Announcement logic tests```bash

- `test_async_posting.py` - Asynchronous posting tests# Usernames for test scripts (used by all test files)

- `test_debouncing.py` - Debounce mechanism testsKICK_USERNAME=asmongold        # Kick channel to check for live streams

- `test_stream_lifecycle.py` - Stream state management testsTWITCH_USERNAME=lilypita       # Twitch channel to check for live streams

YOUTUBE_USERNAME=grndpagaming  # YouTube channel (@ optional - auto-added if missing)

## Running Tests```



### Install Dependencies**Why environment variables?**

- ✅ Easy to change test targets without editing code

First, install pytest and related packages:- ✅ Different configurations for dev/staging/production

- ✅ Keeps test files clean and maintainable

```bash- ✅ Follows same pattern as main application

pip install pytest pytest-asyncio pytest-cov

```**All test scripts automatically pull usernames from `.env`:**

- `test_discord_doppler.py` - Tests Discord with all three platforms

Or install from requirements.txt:- `test_discord_updates.py` - Tests Discord live updating

- `test_discord_stream_ended.py` - Tests stream ended messages

```bash- `test_bluesky_kick_embed.py` - Tests Bluesky Kick preview cards

pip install -r requirements.txt- `test_mastodon_kick_image.py` - Tests Mastodon Kick image attachments

```

## 🔐 Doppler Secret Setup

### Run All Tests

See **[DOPPLER_SECRETS.md](DOPPLER_SECRETS.md)** for detailed naming conventions.

```bash

pytest tests/ -v### Quick Reference

```

```bash

### Run Specific Test File# Twitch

TWITCH_CLIENT_ID=your_client_id

```bashTWITCH_CLIENT_SECRET=your_client_secret

pytest tests/test_config.py -v

```# YouTube

YOUTUBE_API_KEY=your_api_key

### Run Tests by Category

# Kick (no secrets needed, public API)

Tests are marked with custom markers for filtering:# Just enable it: KICK_ENABLE=True

```

```bash

# Run only streaming platform tests## 🚀 Running Tests

pytest tests/ -v -m streaming

### Test All Platforms

# Run only social platform tests

pytest tests/ -v -m social```bash

python tests/test_doppler_all.py

# Run integration tests```

pytest tests/ -v -m integration

This runs a comprehensive suite testing all streaming and social platforms.

# Skip slow tests

pytest tests/ -v -m "not slow"### Test Individual Streaming Platforms



# Run LLM tests only```bash

pytest tests/ -v -m llm# Test Twitch

```python tests/test_doppler_twitch.py



### Run Tests with Coverage# Test YouTube

python tests/test_doppler_youtube.py

```bash

# Generate coverage report# Test Kick

pytest tests/ --cov=stream_daemon --cov-report=htmlpython tests/test_doppler_kick.py

```

# View coverage report

open htmlcov/index.html### Test Individual Social Platforms

```

```bash

## Test Organization# Test Mastodon

python tests/test_doppler_mastodon.py

### Test Markers

# Test Bluesky

Tests use pytest markers for categorization:python tests/test_doppler_bluesky.py



- `@pytest.mark.streaming` - Tests for Twitch, YouTube, Kick# Test Discord

- `@pytest.mark.social` - Tests for Mastodon, Bluesky, Discord, Matrixpython tests/test_doppler_discord.py

- `@pytest.mark.integration` - End-to-end workflow tests

- `@pytest.mark.slow` - Tests that take longer to run# Test Matrix (placeholder - not yet implemented)

- `@pytest.mark.llm` - LLM/AI integration testspython tests/test_doppler_matrix.py

```

### Test Classes

### Make Scripts Executable (Optional)

Tests are organized into classes by functionality:

```bash

**test_config.py:**chmod +x tests/*.py

- `TestConfigLoading` - Environment variable parsing

- `TestSecretLoading` - Doppler/AWS/Vault integration# Then run directly

- `TestSecretMasking` - Security validation./tests/test_doppler_all.py

- `TestSecretsManagerIntegration` - Connectivity tests./tests/test_doppler_mastodon.py

```

**test_streaming_platforms.py:**

- `TestTwitchPlatform` - Twitch API integration## 📊 Test Coverage

- `TestYouTubePlatform` - YouTube Live API

- `TestKickPlatform` - Kick platform integration### Streaming Platform Tests

- `TestPlatformComparison` - Cross-platform consistency

#### Twitch Tests

**test_social_platforms.py:**1. **Doppler Secret Fetch** - Validates `TWITCH_CLIENT_ID` and `TWITCH_CLIENT_SECRET` are retrieved

- `TestMastodonPlatform` - Mastodon API2. **Authentication** - Tests OAuth app authentication with Twitch API

- `TestBlueskyPlatform` - Bluesky AT Protocol3. **Stream Check** - Verifies stream status detection works

- `TestDiscordPlatform` - Discord webhooks

- `TestMatrixPlatform` - Matrix protocol#### YouTube Tests

- `TestSocialPlatformBroadcast` - Multi-platform posting1. **Doppler Secret Fetch** - Validates `YOUTUBE_API_KEY` is retrieved

2. **Authentication** - Tests YouTube Data API v3 client creation

**test_integration.py:**3. **Stream Check** - Verifies live stream detection works

- `TestStreamLifecycle` - Start/end workflows

- `TestMultiPlatformStreaming` - Multi-platform monitoring#### Kick Tests

- `TestAsyncPosting` - Asynchronous operations1. **API Connectivity** - Tests public API is accessible

- `TestErrorRecovery` - Error handling2. **Stream Check** - Verifies stream status detection works

- `TestStatePersistence` - State management3. **Detection Method** - Validates detection logic matches main app

- `TestMessageFormatting` - Platform-specific formatting

### Social Platform Tests

## Configuration

#### Mastodon Tests

### Environment Variables1. **Doppler Secret Fetch** - Validates all 3 Mastodon credentials are retrieved

   - `MASTODON_CLIENT_ID`

Tests use environment variables from `.env` file or secrets manager. Required variables:   - `MASTODON_CLIENT_SECRET`

   - `MASTODON_ACCESS_TOKEN`

```bash2. **Authentication** - Tests Mastodon API authentication

# Streaming Platforms3. **Account Verification** - Retrieves and displays account information

TWITCH_ENABLE=true4. **Test Post** - Posts a test status (optional, with deletion)

TWITCH_USERNAMES=username1,username25. **Threading Test** - Tests reply/thread functionality (optional, with deletion)

# TWITCH_CLIENT_ID and TWITCH_CLIENT_SECRET from secrets manager

#### Bluesky Tests

YOUTUBE_ENABLE=true1. **Doppler Secret Fetch** - Validates `BLUESKY_APP_PASSWORD` is retrieved

YOUTUBE_USERNAMES=@channel1,@channel22. **Authentication** - Tests Bluesky (AT Protocol) login

# YOUTUBE_API_KEY from secrets manager3. **Profile Info** - Retrieves and displays profile information

4. **Character Limit** - Validates 300-character limit handling

KICK_ENABLE=true5. **Test Post** - Posts a test message (optional, with deletion)

KICK_USERNAMES=username1,username26. **Threading Test** - Tests reply/thread functionality (optional, with deletion)



# Social Platforms#### Discord Tests

MASTODON_ENABLE=true1. **Doppler Secret Fetch** - Validates `DISCORD_WEBHOOK_URL` is retrieved

# MASTODON_INSTANCE_URL and MASTODON_ACCESS_TOKEN from secrets manager2. **Webhook Validation** - Tests webhook exists and is accessible

3. **Role Mentions Config** - Checks platform-specific role mention setup

BLUESKY_ENABLE=true4. **Test Post** - Posts a test message via webhook (optional)

# BLUESKY_HANDLE and BLUESKY_APP_PASSWORD from secrets manager5. **Role Mention Post** - Tests role mention functionality (optional)



DISCORD_ENABLE=true#### Matrix Tests

# DISCORD_WEBHOOK_URL from secrets manager1. **Placeholder** - Matrix support not yet implemented

2. **Config Check** - Verifies if Matrix config exists (for future use)

MATRIX_ENABLE=true

# MATRIX_HOMESERVER, MATRIX_ACCESS_TOKEN, MATRIX_ROOM_ID from secrets manager## 🔒 Security Features



# Secrets Manager (choose one)- ✅ **Credentials Masked** - All secrets displayed as `xxxx...yyyy`

SECRETS_MANAGER=doppler  # or aws, vault, env- ✅ **No Plain Text Output** - Secrets never printed in full

```- ✅ **Safe for Streaming** - Can run tests on live stream without exposing credentials

- ✅ **Environment Isolation** - Uses `.env` file, not hardcoded values

### Test Data

## 📝 Example Output

The `conftest.py` file provides fixtures for test data:

```

- `load_test_env` - Loads `.env` file for session╔==========================================================╗

- `mock_stream_data` - Sample stream data║               TWITCH PLATFORM TEST                       ║

- `test_usernames` - Configured usernames per platform╚==========================================================╝

- `clean_test_posts` - Cleanup after posting tests

============================================================

### Skipping Tests🔐 TEST: Doppler Secret Fetch (Twitch)

============================================================

Tests automatically skip when dependencies aren't available:Secret Manager: doppler

Doppler Token: dp.s...xyz

```pythonTwitch Secret Name: TWITCH

@pytest.mark.skip_if_no_secrets

def test_requires_secrets():Fetching secrets with prefix: TWITCH

    """This test needs secrets configured."""✓ Received 2 secret(s) from Doppler

    pass  Keys found: client_id, client_secret



@pytest.fixture  client_id: abc1...xyz9

def platform(self, skip_if_platform_disabled):  client_secret: sec1...ret9

    """Skip if platform is disabled."""✓ All required Twitch secrets found

    skip_if_platform_disabled('twitch')

    return TwitchPlatform()============================================================

```🔑 TEST: Twitch Authentication

============================================================

## Writing TestsClient ID: abc1...xyz9

Client Secret: sec1...ret9

### Basic Test Structure

Authenticating with Twitch API...

```python✓ Authentication successful!

import pytest

from stream_daemon.platforms.streaming import TwitchPlatform============================================================

📺 TEST: Stream Status Check

@pytest.mark.streaming============================================================

class TestTwitchFeature:Test username: your_username

    """Test a specific Twitch feature."""

    Looking up user: your_username

    @pytest.fixture✓ Found user: YourDisplayName (ID: 123456789)

    def platform(self, skip_if_platform_disabled):Checking stream status...

        """Create authenticated platform instance."""✓ Stream check works (currently offline)

        skip_if_platform_disabled('twitch')

        platform = TwitchPlatform()============================================================

        platform.authenticate()📊 TEST SUMMARY

        return platform============================================================

    ✓ PASS: Doppler Secret Fetch

    def test_feature(self, platform):✓ PASS: Twitch Authentication

        """Test the feature."""✓ PASS: Stream Status Check

        result = platform.some_method()

        assert result is not NoneResults: 3/3 tests passed

```============================================================

```

### Integration Test Example

## 🐛 Troubleshooting

```python

@pytest.mark.integration### "DOPPLER_TOKEN is not set"

@pytest.mark.slow```bash

def test_full_workflow(streaming_platform, social_platforms):# Set in .env file

    """Test complete announcement workflow."""DOPPLER_TOKEN=dp.st.xxxxxxxxxxxx

    # Check if live

    is_live, stream_data = streaming_platform.is_live("username")# Or use Doppler CLI

    doppler run -- python tests/test_doppler_all.py

    if is_live:```

        # Announce to all platforms

        for name, platform in social_platforms:### "No secrets returned from Doppler"

            result = platform.post(f"LIVE: {stream_data['title']}")- Check secret names match exactly (case-sensitive)

            assert result is not None- Verify secret prefix: `TWITCH_CLIENT_ID` requires `SECRETS_DOPPLER_TWITCH_SECRET_NAME=TWITCH`

```- Run `doppler secrets` to list all secrets



### Async Test Example### "Authentication failed"

- Verify credentials are correct in Doppler dashboard

```python- Check API key/client ID hasn't expired

@pytest.mark.asyncio- For Twitch: Ensure app is registered at https://dev.twitch.tv/console/apps

async def test_async_posting():

    """Test asynchronous operations."""### "User not found"

    platform = MastodonPlatform()- Verify username is set correctly in `.env` file:

    platform.authenticate()  - `TWITCH_USERNAME=your_twitch_username`

      - `YOUTUBE_USERNAME=your_youtube_handle` (@ optional)

    result = await asyncio.to_thread(platform.post, "Test message")  - `KICK_USERNAME=your_kick_username`

    assert result is not None- Ensure username exists on the platform

```- Check for typos in `.env` file

- For YouTube: Works with or without @ prefix (e.g., both `grndpagaming` and `@grndpagaming` work)

## CI/CD Integration

### "Stream not found" / "Currently offline"

### GitHub Actions Example- This is **normal** if the configured channel is not live during testing

- Tests verify the **detection mechanism works**, not whether a stream is actually live

Create `.github/workflows/test.yml`:- To test with a live stream:

  1. Find a channel that's currently live on the platform

```yaml  2. Update the username in `.env` (e.g., `KICK_USERNAME=asmongold`)

name: Tests  3. Re-run the test

- Tests will show "✓ Stream check works (currently offline)" or "✓ LIVE" depending on stream status

on: [push, pull_request]

## 📚 Configuration Files

jobs:

  test:- **`.env`** - Environment variables (git-ignored)

    runs-on: ubuntu-latest- **`.env.example`** - Template with all variables

    - **`DOPPLER_SECRETS.md`** - Detailed Doppler setup guide

    steps:

    - uses: actions/checkout@v3## 🧪 Test Files

    

    - name: Set up Python- `test_doppler_all.py` - Comprehensive suite (runs all tests)

      uses: actions/setup-python@v4- `test_doppler_twitch.py` - Twitch-specific tests

      with:- `test_doppler_youtube.py` - YouTube-specific tests

        python-version: '3.11'- `test_doppler_kick.py` - Kick-specific tests

    

    - name: Install dependencies## 💡 Tips

      run: |

        pip install -r requirements.txt1. **Run before deploying** - Validate credentials before going live

        pip install pytest pytest-asyncio pytest-cov2. **Test after Doppler changes** - Verify secrets after updating

    3. **Use in CI/CD** - Add to automated testing pipeline

    - name: Run tests4. **Safe for demos** - Can run on stream without revealing secrets

      env:

        DOPPLER_TOKEN: ${{ secrets.DOPPLER_TOKEN }}## 🔗 Related Documentation

      run: |

        pytest tests/ -v --cov=stream_daemon --cov-report=xml- [Doppler Setup Guide](../DOPPLER_GUIDE.md)

    - [Platform Guide](../PLATFORM_GUIDE.md)

    - name: Upload coverage- [Migration Guide](../MIGRATION.md)

      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

### Pre-commit Hooks

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: pytest-check
        name: pytest
        entry: pytest
        args: [tests/, -v, -m, "not slow"]
        language: system
        pass_filenames: false
        always_run: true
```

## Best Practices

1. **Isolation** - Each test should be independent
2. **Fixtures** - Use fixtures for shared setup/teardown
3. **Markers** - Tag tests by category for filtering
4. **Assertions** - Use descriptive assertion messages
5. **Cleanup** - Always clean up test data (use `clean_test_posts` fixture)
6. **Secrets** - Never commit secrets; use environment variables
7. **Mocking** - Mock external services when possible
8. **Coverage** - Aim for 80%+ code coverage

## Troubleshooting

### Tests Fail with "Import could not be resolved"

Install pytest:
```bash
pip install pytest pytest-asyncio
```

### Tests Skip with "No secrets configured"

Set up your secrets manager:
```bash
# Use the wizard
./scripts/create-secrets.sh

# Or set environment variables
export SECRETS_MANAGER=env
export TWITCH_CLIENT_ID=your_id
export TWITCH_CLIENT_SECRET=your_secret
```

### Platform Tests Fail with Authentication Error

1. Check your secrets are correctly configured
2. Verify API credentials are valid
3. Check platform is enabled: `PLATFORM_ENABLE=true`
4. Verify network connectivity

### Integration Tests Timeout

Integration tests can be slow. Run without slow tests:
```bash
pytest tests/ -v -m "not slow"
```

## Migration Notes

This test suite replaces the legacy monolith-based tests. Key changes:

1. **Import Changes**: 
   - Old: `importlib.util.spec_from_file_location('stream_daemon', 'stream-daemon.py')`
   - New: `from stream_daemon.platforms.streaming import TwitchPlatform`

2. **Framework**: Now uses pytest instead of standalone scripts

3. **Organization**: Consolidated from 35+ files to 5 core test files

4. **Fixtures**: Shared setup via `conftest.py` instead of duplicated code

For details on the migration, see `TEST_ANALYSIS.md`.

---

**Questions?** See the main project README or open an issue on GitHub.
