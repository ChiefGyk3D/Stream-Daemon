# Stream Daemon Test Suite

Comprehensive test suite for validating Doppler secrets and platform connectivity.

## 🎯 Purpose

These tests ensure:
- ✅ Doppler secrets are properly configured
- ✅ Platform authentication works correctly
- ✅ Stream detection methods function as expected
- ✅ No credentials are leaked in output

## 📋 Prerequisites

1. **Doppler Account** - Sign up at https://doppler.com
2. **Doppler CLI** - Install and run `doppler setup` in project directory
3. **Platform Credentials** - Configure secrets in Doppler (see `DOPPLER_SECRETS.md`)
4. **Environment Variables** - Configure `.env` file

## 🔐 Doppler Secret Setup

See **[DOPPLER_SECRETS.md](DOPPLER_SECRETS.md)** for detailed naming conventions.

### Quick Reference

```bash
# Twitch
TWITCH_CLIENT_ID=your_client_id
TWITCH_CLIENT_SECRET=your_client_secret

# YouTube
YOUTUBE_API_KEY=your_api_key

# Kick (no secrets needed, public API)
# Just enable it: KICK_ENABLE=True
```

## 🚀 Running Tests

### Test All Platforms

```bash
python tests/test_doppler_all.py
```

This runs a comprehensive suite testing all platforms.

### Test Individual Platforms

```bash
# Test Twitch
python tests/test_doppler_twitch.py

# Test YouTube
python tests/test_doppler_youtube.py

# Test Kick
python tests/test_doppler_kick.py
```

### Make Scripts Executable (Optional)

```bash
chmod +x tests/*.py

# Then run directly
./tests/test_doppler_all.py
```

## 📊 Test Coverage

### Twitch Tests
1. **Doppler Secret Fetch** - Validates `TWITCH_CLIENT_ID` and `TWITCH_CLIENT_SECRET` are retrieved
2. **Authentication** - Tests OAuth app authentication with Twitch API
3. **Stream Check** - Verifies stream status detection works

### YouTube Tests
1. **Doppler Secret Fetch** - Validates `YOUTUBE_API_KEY` is retrieved
2. **Authentication** - Tests YouTube Data API v3 client creation
3. **Stream Check** - Verifies live stream detection works

### Kick Tests
1. **API Connectivity** - Tests public API is accessible
2. **Stream Check** - Verifies stream status detection works
3. **Detection Method** - Validates detection logic matches main app

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
- Set correct username: `TWITCH_USERNAME=your_username`
- Ensure username exists on the platform
- Check for typos

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
