# Running Tests

## 🚀 Quick Start

### With Doppler (Recommended for Production)
```bash
# Run all tests
doppler run -- pytest tests/

# Run with verbose output
doppler run -- pytest tests/ -v

# Run specific test file
doppler run -- pytest tests/test_platform_validation.py -v

# Run tests with coverage
doppler run -- pytest tests/ --cov=stream_daemon
```

### Without Doppler (Using .env file)
```bash
# Ensure .env file has all required variables
pytest tests/

# Run with verbose output
pytest tests/ -v
```

## 📊 Test Results

The test suite contains **74 tests** organized across 6 core files:

### Expected Results (when platforms are configured)
- ✅ **~27 tests PASSED** - Core functionality tests
- ⏭️ **~47 tests SKIPPED** - Platforms not enabled or credentials not configured
- ❌ **0 tests FAILED** - All enabled platforms should pass

### Common Skip Reasons
Tests will be skipped when:
- Platform is disabled (`PLATFORM_ENABLE=false`)
- Credentials not configured in secrets manager
- Usernames not configured (`PLATFORM_USERNAMES` empty)
- Secrets manager not configured

## 🎯 Running Specific Tests

### By Test Marker
```bash
# Run only streaming platform tests
doppler run -- pytest tests/ -m streaming -v

# Run only social platform tests  
doppler run -- pytest tests/ -m social -v

# Run only integration tests
doppler run -- pytest tests/ -m integration -v

# Run only LLM tests
doppler run -- pytest tests/ -m llm -v
```

### By Test File
```bash
# Configuration tests
doppler run -- pytest tests/test_config.py -v

# Platform validation tests
doppler run -- pytest tests/test_platform_validation.py -v

# Social platform tests
doppler run -- pytest tests/test_social_platforms.py -v

# Debouncing logic tests
doppler run -- pytest tests/test_debouncing.py -v

# Integration tests
doppler run -- pytest tests/test_integration.py -v

# LLM/AI tests
doppler run -- pytest tests/test_llm.py -v
```

### By Test Class
```bash
# Test specific platform
doppler run -- pytest tests/test_platform_validation.py::TestTwitchValidation -v
doppler run -- pytest tests/test_platform_validation.py::TestYouTubeValidation -v
doppler run -- pytest tests/test_platform_validation.py::TestKickValidation -v
doppler run -- pytest tests/test_platform_validation.py::TestMastodonValidation -v
doppler run -- pytest tests/test_platform_validation.py::TestBlueskyValidation -v
doppler run -- pytest tests/test_platform_validation.py::TestDiscordValidation -v
doppler run -- pytest tests/test_platform_validation.py::TestMatrixValidation -v
```

### By Individual Test
```bash
# Run single test
doppler run -- pytest tests/test_platform_validation.py::TestTwitchValidation::test_twitch_authentication -v
```

## 🐛 Debugging Test Failures

### Show Full Output
```bash
# Show stdout/stderr during tests
doppler run -- pytest tests/ -v -s

# Show full traceback
doppler run -- pytest tests/ -v --tb=long

# Stop on first failure
doppler run -- pytest tests/ -x
```

### Check Environment
```bash
# Verify Doppler is loading variables
doppler run -- env | grep -E "(TWITCH|YOUTUBE|KICK|MASTODON|BLUESKY|DISCORD|MATRIX)" | sort

# Check which platforms are enabled
doppler run -- env | grep "_ENABLE"
```

## 📝 Test Coverage

To generate coverage reports:

```bash
# HTML coverage report
doppler run -- pytest tests/ --cov=stream_daemon --cov-report=html

# Open coverage report
xdg-open htmlcov/index.html  # Linux
open htmlcov/index.html      # macOS
```

## ⚠️ Important Notes

1. **Doppler is Required** - If using Doppler for secrets, you MUST run tests with `doppler run --` prefix
2. **API Rate Limits** - Some tests make real API calls and may hit rate limits if run repeatedly
3. **Credentials Required** - Platform authentication tests require valid credentials
4. **Skip is Normal** - Most tests will skip if platforms aren't configured - this is expected behavior

## 🔍 Understanding Test Results

### Test Status Meanings

- **PASSED** ✅ - Test executed successfully
- **FAILED** ❌ - Test found an issue (needs investigation)
- **SKIPPED** ⏭️ - Test was skipped (platform disabled or not configured)

### When Tests Should Pass vs Skip

| Test Type | Passes When | Skips When |
|-----------|-------------|------------|
| Secrets Loading | Secrets manager configured | No secrets manager |
| Authentication | Valid credentials exist | Platform disabled or no credentials |
| Username Config | Usernames configured | No usernames set |
| Stream Check | Can connect to API | No username or platform disabled |
| Social Posting | Platform enabled + configured | Platform disabled |

## 📚 Additional Resources

- See `TEST_ANALYSIS.md` for detailed test coverage analysis
- See `TEST_CONSOLIDATION.md` for test suite cleanup history
- See `README.md` for full test suite documentation
