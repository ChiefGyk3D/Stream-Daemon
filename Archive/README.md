# Archive - Historical Reference Documentation

> **📚 This directory contains historical setup guides and reference documentation.**
>
> **Current documentation** is in: `/docs/`  
> **Current tests** are in: `/tests/`

## 📖 What's Here

This directory preserves **historical setup guides** that may still be useful as reference material:

- **DOPPLER_SECRETS.md** - Doppler secret naming conventions and setup
- **KICK_AUTH_GUIDE.md** - Kick OAuth authentication guide  
- **DISCORD_TEST_SETUP.md** - Discord webhook setup reference
- **QUICK_REFERENCE.md** - Quick reference for old test structure

These files contain useful setup information and are kept for reference, though current best practices are documented in `/docs/`.

---

## � What Was Removed

**Test Files (Removed October 26, 2025):**

The legacy `test_doppler_*.py` files (2,374 lines across 9 files) have been **deleted** after being replaced by modern pytest-based tests.

**Old files (now deleted):**
- test_doppler_all.py
- test_doppler_twitch.py
- test_doppler_youtube.py
- test_doppler_kick.py
- test_doppler_mastodon.py
- test_doppler_bluesky.py
- test_doppler_discord.py
- test_doppler_matrix.py

**Replaced by:**
- ✅ `/tests/test_platform_validation.py` (600 lines, 75% reduction)
- ✅ Proper imports from `stream_daemon` package
- ✅ Full pytest framework with markers and fixtures

**Why removed:**
- ❌ Used importlib to import from monolithic `stream-daemon.py`
- ❌ 2,374 lines of duplicated code
- ❌ No pytest framework support
- ❌ Not aligned with refactored codebase

**See:** [/tests/TEST_CONSOLIDATION.md](../tests/TEST_CONSOLIDATION.md) for migration details

---

## 📖 Current Documentation

For up-to-date information, see:

- **Testing**: [/tests/README.md](../tests/README.md)
- **Test Consolidation**: [/tests/TEST_CONSOLIDATION.md](../tests/TEST_CONSOLIDATION.md)
- **Configuration**: [/docs/configuration/](../docs/configuration/)
- **Secrets Management**: [/docs/configuration/secrets.md](../docs/configuration/secrets.md)
- **Platform Setup**: [/docs/platforms/](../docs/platforms/)

---

*Last Updated: October 26, 2025*  
*Archive cleaned - test files removed, documentation preserved*

## 📚 Documentation Preserved

- **DOPPLER_SECRETS.md** - Historical reference for Doppler secret naming conventions
- **KICK_AUTH_GUIDE.md** - Guide for Kick OAuth authentication  
- **DISCORD_TEST_SETUP.md** - Discord webhook setup reference
- **QUICK_REFERENCE.md** - Quick reference for old test structure

These files are kept for historical context and may contain useful setup information, but refer to the main documentation in `/docs/` for current best practices.

---

## 🔄 Migration Information

**Old Structure** (Pre-Modularization):
- Monolithic `stream-daemon.py` (1263 lines)
- Tests imported via `importlib.util.spec_from_file_location()`
- Individual test files per platform per secrets manager

**New Structure** (Current):
- Modular `stream_daemon/` package
- Tests use standard imports: `from stream_daemon.platforms...`
- Consolidated test files using pytest framework
- See `/tests/TEST_ANALYSIS.md` for details

---

## 📖 Current Documentation

For up-to-date information, see:

- **Testing**: [/tests/README.md](../tests/README.md)
- **Configuration**: [/docs/configuration/](../docs/configuration/)
- **Secrets Management**: [/docs/configuration/secrets.md](../docs/configuration/secrets.md)
- **Platform Setup**: [/docs/platforms/](../docs/platforms/)

---

*Last Updated: October 25, 2025*  
*Archive cleaned and reorganized during test suite refactoring*
python tests/test_doppler_discord.py

# Test Matrix (placeholder - not yet implemented)
python tests/test_doppler_matrix.py
```

### Make Scripts Executable (Optional)

```bash
chmod +x tests/*.py

# Then run directly
./tests/test_doppler_all.py
./tests/test_doppler_mastodon.py
```

## 📊 Test Coverage

### Streaming Platform Tests

#### Twitch Tests
1. **Doppler Secret Fetch** - Validates `TWITCH_CLIENT_ID` and `TWITCH_CLIENT_SECRET` are retrieved
2. **Authentication** - Tests OAuth app authentication with Twitch API
3. **Stream Check** - Verifies stream status detection works

#### YouTube Tests
1. **Doppler Secret Fetch** - Validates `YOUTUBE_API_KEY` is retrieved
2. **Authentication** - Tests YouTube Data API v3 client creation
3. **Stream Check** - Verifies live stream detection works

#### Kick Tests
1. **API Connectivity** - Tests public API is accessible
2. **Stream Check** - Verifies stream status detection works
3. **Detection Method** - Validates detection logic matches main app

### Social Platform Tests

#### Mastodon Tests
1. **Doppler Secret Fetch** - Validates all 3 Mastodon credentials are retrieved
   - `MASTODON_CLIENT_ID`
   - `MASTODON_CLIENT_SECRET`
   - `MASTODON_ACCESS_TOKEN`
2. **Authentication** - Tests Mastodon API authentication
3. **Account Verification** - Retrieves and displays account information
4. **Test Post** - Posts a test status (optional, with deletion)
5. **Threading Test** - Tests reply/thread functionality (optional, with deletion)

#### Bluesky Tests
1. **Doppler Secret Fetch** - Validates `BLUESKY_APP_PASSWORD` is retrieved
2. **Authentication** - Tests Bluesky (AT Protocol) login
3. **Profile Info** - Retrieves and displays profile information
4. **Character Limit** - Validates 300-character limit handling
5. **Test Post** - Posts a test message (optional, with deletion)
6. **Threading Test** - Tests reply/thread functionality (optional, with deletion)

#### Discord Tests
1. **Doppler Secret Fetch** - Validates `DISCORD_WEBHOOK_URL` is retrieved
2. **Webhook Validation** - Tests webhook exists and is accessible
3. **Role Mentions Config** - Checks platform-specific role mention setup
4. **Test Post** - Posts a test message via webhook (optional)
5. **Role Mention Post** - Tests role mention functionality (optional)

#### Matrix Tests
1. **Placeholder** - Matrix support not yet implemented
2. **Config Check** - Verifies if Matrix config exists (for future use)

## 🔒 Security Features

- ✅ **Credentials Masked** - All secrets displayed as `xxxx...yyyy`
- ✅ **No Plain Text Output** - Secrets never printed in full
- ✅ **Safe for Streaming** - Can run tests on live stream without exposing credentials
- ✅ **Environment Isolation** - Uses `.env` file, not hardcoded values

## 📝 Example Output

```
╔==========================================================╗
║               TWITCH PLATFORM TEST                       ║
╚==========================================================╝

============================================================
🔐 TEST: Doppler Secret Fetch (Twitch)
============================================================
Secret Manager: doppler
Doppler Token: dp.s...xyz
Twitch Secret Name: TWITCH

Fetching secrets with prefix: TWITCH
✓ Received 2 secret(s) from Doppler
  Keys found: client_id, client_secret

  client_id: abc1...xyz9
  client_secret: sec1...ret9
✓ All required Twitch secrets found

============================================================
🔑 TEST: Twitch Authentication
============================================================
Client ID: abc1...xyz9
Client Secret: sec1...ret9

Authenticating with Twitch API...
✓ Authentication successful!

============================================================
📺 TEST: Stream Status Check
============================================================
Test username: your_username

Looking up user: your_username
✓ Found user: YourDisplayName (ID: 123456789)
Checking stream status...
✓ Stream check works (currently offline)

============================================================
📊 TEST SUMMARY
============================================================
✓ PASS: Doppler Secret Fetch
✓ PASS: Twitch Authentication
✓ PASS: Stream Status Check

Results: 3/3 tests passed
============================================================
```

## 🐛 Troubleshooting

### "DOPPLER_TOKEN is not set"
```bash
# Set in .env file
DOPPLER_TOKEN=dp.st.xxxxxxxxxxxx

# Or use Doppler CLI
doppler run -- python tests/test_doppler_all.py
```

### "No secrets returned from Doppler"
- Check secret names match exactly (case-sensitive)
- Verify secret prefix: `TWITCH_CLIENT_ID` requires `SECRETS_DOPPLER_TWITCH_SECRET_NAME=TWITCH`
- Run `doppler secrets` to list all secrets

### "Authentication failed"
- Verify credentials are correct in Doppler dashboard
- Check API key/client ID hasn't expired
- For Twitch: Ensure app is registered at https://dev.twitch.tv/console/apps

### "User not found"
- Verify username is set correctly in `.env` file:
  - `TWITCH_USERNAME=your_twitch_username`
  - `YOUTUBE_USERNAME=your_youtube_handle` (@ optional)
  - `KICK_USERNAME=your_kick_username`
- Ensure username exists on the platform
- Check for typos in `.env` file
- For YouTube: Works with or without @ prefix (e.g., both `grndpagaming` and `@grndpagaming` work)

### "Stream not found" / "Currently offline"
- This is **normal** if the configured channel is not live during testing
- Tests verify the **detection mechanism works**, not whether a stream is actually live
- To test with a live stream:
  1. Find a channel that's currently live on the platform
  2. Update the username in `.env` (e.g., `KICK_USERNAME=asmongold`)
  3. Re-run the test
- Tests will show "✓ Stream check works (currently offline)" or "✓ LIVE" depending on stream status

## 📚 Configuration Files

- **`.env`** - Environment variables (git-ignored)
- **`.env.example`** - Template with all variables
- **`DOPPLER_SECRETS.md`** - Detailed Doppler setup guide

## 🧪 Test Files

- `test_doppler_all.py` - Comprehensive suite (runs all tests)
- `test_doppler_twitch.py` - Twitch-specific tests
- `test_doppler_youtube.py` - YouTube-specific tests
- `test_doppler_kick.py` - Kick-specific tests

## 💡 Tips

1. **Run before deploying** - Validate credentials before going live
2. **Test after Doppler changes** - Verify secrets after updating
3. **Use in CI/CD** - Add to automated testing pipeline
4. **Safe for demos** - Can run on stream without revealing secrets

## 🔗 Related Documentation

- [Doppler Setup Guide](../DOPPLER_GUIDE.md)
- [Platform Guide](../PLATFORM_GUIDE.md)
- [Migration Guide](../MIGRATION.md)
