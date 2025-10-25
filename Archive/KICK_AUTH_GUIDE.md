# Kick Authentication Guide

## Overview

Kick.com now supports **optional authentication** for better API access and higher rate limits. Stream Daemon can work with or without Kick credentials.

## Two Operating Modes

### 1. Authenticated Mode (Recommended)
- ✅ Higher rate limits
- ✅ More reliable API access
- ✅ Official API endpoints
- ⚠️ Requires client credentials

### 2. Public API Mode (Fallback)
- ⚠️ Lower rate limits
- ⚠️ May be blocked by security policies (403 errors)
- ⚠️ Subject to scraping restrictions
- ✅ No credentials needed

## Getting Kick Credentials

1. Visit the Kick Developer Portal (exact URL TBD - check Kick's documentation)
2. Create a new application
3. Generate Client ID and Client Secret
4. Copy credentials to your secrets manager

## Configuration

### In Doppler

Create these secrets in your Doppler project:

```bash
KICK_CLIENT_ID=your_client_id_here
KICK_CLIENT_SECRET=your_client_secret_here
```

### In .env

```bash
# Enable Kick
KICK_ENABLE=True
KICK_USERNAME=your_kick_username

# Configure Doppler secret name
SECRETS_DOPPLER_KICK_SECRET_NAME=KICK

# Or set credentials directly (not recommended for production)
KICK_CLIENT_ID=your_client_id
KICK_CLIENT_SECRET=your_client_secret
```

## How It Works

### Authentication Flow

1. Stream Daemon checks for `KICK_CLIENT_ID` and `KICK_CLIENT_SECRET`
2. If found, attempts OAuth client credentials flow:
   ```
   POST https://id.kick.com/oauth/token
   Content-Type: application/x-www-form-urlencoded
   grant_type=client_credentials
   ```
3. If successful, uses Bearer token for all API calls
4. If authentication fails, falls back to public API

### API Endpoints

**Authenticated API:**
- Base: `https://api.kick.com/public/v1/`
- Channel info: `/channels/{username}`
- Livestreams: `/livestreams?broadcaster_user_id={user_id}`
- Requires: `Authorization: Bearer {token}` header

**Public API (Fallback):**
- Base: `https://kick.com/api/v2/`
- Livestream: `/channels/{username}/livestream`
- Requires: Browser-like headers to avoid 403

## Testing

Run the Kick test suite to verify your setup:

```bash
# Test all aspects (Doppler, auth, API)
python tests/test_doppler_kick.py

# Or use the test runner
./run_tests.sh kick
```

### Expected Output (With Auth)

```
╔==========================================================╗
║                KICK PLATFORM TEST                        ║
╚==========================================================╝

NOTE: Kick supports both authenticated and public API
      Authentication is optional but recommended

============================================================
🔐 TEST: Doppler Secret Fetch (Kick)
============================================================
Secret Manager: doppler
Doppler Token: SET
Kick Secret Name: KICK

Fetching secrets with prefix: KICK
✓ Received 2 secret(s) from Doppler
  Keys found: client_id, client_secret

✓ Kick authentication credentials found
  Will use authenticated API (higher rate limits)

============================================================
🔑 TEST: Kick Authentication
============================================================
Client ID: ***
Client Secret: ***

Authenticating with Kick API...
✓ Authentication successful!
  Will use authenticated API

============================================================
📺 TEST: Stream Status Check
============================================================
Test username: chiefgyk3d

✓ Stream check works (currently offline)

...
```

### Expected Output (Without Auth)

```
============================================================
🔐 TEST: Doppler Secret Fetch (Kick)
============================================================
ℹ No secrets returned from Doppler
  Kick can work without authentication (public API)

============================================================
🔑 TEST: Kick Authentication
============================================================
ℹ No Kick credentials configured
  This is OK - Kick works without authentication
  Using public API for stream checks
...
```

## Troubleshooting

### 403 Forbidden Errors (Public API)

```
Response status: 403
Error: Request blocked by security policy
```

**Solution:** Configure Kick authentication credentials. The public API is heavily rate-limited and may block automated requests.

### Authentication Failed

```
⚠ Authentication returned status 401
```

**Causes:**
- Invalid client_id or client_secret
- Credentials expired or revoked
- Wrong OAuth endpoint

**Solution:** Verify credentials in Kick Developer Portal and regenerate if needed.

### Token Endpoint Not Found (404)

```
⚠ Authentication returned status 404
```

**Cause:** OAuth endpoint URL may be incorrect

**Solution:** Check Kick's official API documentation for the correct token endpoint. May need to update `token_url` in code.

## Migration from Public API

If you're currently using Stream Daemon without Kick credentials:

1. Generate Kick API credentials (see above)
2. Add to Doppler or .env file
3. Restart Stream Daemon
4. Monitor logs for "✓ Kick authenticated" message
5. If authentication fails, Stream Daemon automatically falls back to public API

**No downtime required** - authentication is attempted on startup and falls back gracefully.

## Rate Limits

### Authenticated API
- **Likely higher limits** (exact limits TBD)
- Suitable for production use
- Recommended for monitoring multiple channels

### Public API
- **Very restrictive**
- May return 403 after few requests
- Only suitable for development/testing

## Security Best Practices

✅ **DO:**
- Store credentials in secrets manager (Doppler/Vault/AWS)
- Use environment variables
- Rotate credentials periodically
- Monitor for 401 errors (expired tokens)

❌ **DON'T:**
- Commit credentials to git
- Share credentials in public
- Use same credentials across environments
- Hard-code credentials in source files

## API Reference

### OAuth Token Request

```http
POST /oauth2/token HTTP/1.1
Host: api.kick.com
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials&
client_id=YOUR_CLIENT_ID&
client_secret=YOUR_CLIENT_SECRET
```

### Livestreams Request (Authenticated)

```http
GET /public/v1/livestreams?broadcaster_user_id=123 HTTP/1.1
Host: api.kick.com
Authorization: Bearer YOUR_ACCESS_TOKEN
Accept: application/json
```

### Response Format

```json
{
  "data": [
    {
      "broadcaster_user_id": 123,
      "channel_id": 456,
      "stream_title": "Playing games!",
      "viewer_count": 1000,
      "started_at": "2025-10-23T12:00:00Z",
      "language": "en",
      "has_mature_content": false
    }
  ],
  "message": "Success"
}
```

## Support

For issues with:
- **Stream Daemon:** Check `/tests/README.md` and run test suite
- **Kick API:** Consult Kick's official developer documentation
- **Doppler:** See `/tests/DOPPLER_SECRETS.md`
