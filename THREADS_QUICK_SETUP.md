# Quick Threads Setup Guide

## What You Need

1. **Threads User ID** (same as your Instagram User ID)
2. **Long-Lived Access Token** (valid for 60 days)

---

## Step-by-Step Setup (15 minutes)

### Step 1: Get Your Instagram/Threads User ID

**Option A: Using Instagram Graph API Explorer**

1. Go to: https://developers.facebook.com/tools/explorer/
2. Click "Get Token" → "Get User Access Token"
3. Select permissions: `instagram_basic`, `pages_show_list`
4. Generate token
5. In the query field enter: `me?fields=id,username`
6. Click Submit
7. **Copy the `id` value** - this is your User ID

**Option B: Quick API Call**

If you already have an Instagram access token:
```bash
curl "https://graph.instagram.com/me?fields=id,username&access_token=YOUR_TEMP_TOKEN"
```

Look for the `"id"` field in the response.

---

### Step 2: Create Meta App & Get Threads Access Token

#### 2A: Create App

1. Go to: https://developers.facebook.com/apps/create/
2. Select **"Other"** as app type → Next
3. Select **"Business"** type → Next
4. Fill in:
   - **App Name**: `Stream Daemon Bot` (or your preferred name)
   - **App Contact Email**: Your email
5. Click **Create App**

#### 2B: Add Threads Product

1. In left sidebar, click **"Add Product"**
2. Find **Threads** card and click **"Set up"**
3. Go to **Threads** → **Settings** in left sidebar
4. Note your:
   - **Threads App ID**: `1234567890123456`
   - **Threads App Secret**: `abc123def456...`

#### 2C: Get Access Token (Manual OAuth Flow)

**Step 1: Build Authorization URL**

Replace `YOUR_THREADS_APP_ID` and `YOUR_REDIRECT_URI`:

```
https://www.threads.net/oauth/authorize?client_id=YOUR_THREADS_APP_ID&redirect_uri=https://localhost/&scope=threads_basic,threads_content_publish&response_type=code
```

Example:
```
https://www.threads.net/oauth/authorize?client_id=1234567890&redirect_uri=https://localhost/&scope=threads_basic,threads_content_publish&response_type=code
```

**Step 2: Visit URL & Authorize**

1. Paste the URL into your browser
2. Log in with your Instagram account (if not already logged in)
3. Click **"Allow"** to authorize the app
4. You'll be redirected to `https://localhost/?code=LONG_CODE_HERE`
5. **Copy the entire code** from the URL (everything after `code=`)

**Step 3: Exchange Code for Short-Lived Token**

```bash
curl -X POST "https://graph.threads.net/oauth/access_token" \
  -d "client_id=YOUR_THREADS_APP_ID" \
  -d "client_secret=YOUR_THREADS_APP_SECRET" \
  -d "grant_type=authorization_code" \
  -d "redirect_uri=https://localhost/" \
  -d "code=AUTHORIZATION_CODE_FROM_STEP_2"
```

Response:
```json
{
  "access_token": "THxxxx...short_lived_token",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Copy the `access_token`** - you have 1 hour to use it!

**Step 4: Exchange for Long-Lived Token (60 days)**

```bash
curl -X GET "https://graph.threads.net/access_token?grant_type=th_exchange_token&client_secret=YOUR_THREADS_APP_SECRET&access_token=SHORT_LIVED_TOKEN_FROM_STEP_3"
```

Response:
```json
{
  "access_token": "THxxxx...long_lived_token",
  "token_type": "bearer",
  "expires_in": 5184000
}
```

**Copy this `access_token`** - this is your 60-day token!

---

### Step 3: Add Credentials to Doppler

**Using Doppler CLI:**

```bash
# Set Threads User ID (your Instagram User ID)
doppler secrets set THREADS_USER_ID="your_instagram_user_id"

# Set Threads Access Token (long-lived, 60-day token)
doppler secrets set THREADS_ACCESS_TOKEN="THxxxxxxxxxxxxx"

# Enable Threads posting
doppler secrets set THREADS_ENABLE_POSTING="True"
```

**Using Doppler Dashboard:**

1. Go to: https://dashboard.doppler.com/
2. Select your project and environment (e.g., `stream-daemon` → `dev`)
3. Click **"Add Secret"**
4. Add these secrets:
   - `THREADS_USER_ID` = `123456789` (your Instagram/Threads user ID)
   - `THREADS_ACCESS_TOKEN` = `THQVJxxxxxx...` (60-day token)
   - `THREADS_ENABLE_POSTING` = `True`

---

### Step 4: Test Threads Posting

**Quick Test Script:**

Create `test_threads.py`:

```python
#!/usr/bin/env python3
"""Quick test script for Threads posting"""

import sys
sys.path.insert(0, '/home/chiefgyk3d/src/twitch-and-toot')

from stream_daemon.platforms.social.threads import ThreadsPlatform

# Initialize and authenticate
threads = ThreadsPlatform()
if not threads.authenticate():
    print("❌ Authentication failed!")
    sys.exit(1)

print("✅ Authentication successful!")

# Test post
test_message = "🎮 Testing Stream Daemon Threads integration! #StreamDaemon"
print(f"\nPosting: {test_message}")
print(f"Character count: {len(test_message)}/500")

post_id = threads.post(test_message)

if post_id:
    print(f"\n✅ SUCCESS! Post ID: {post_id}")
    print(f"View at: https://www.threads.net/@YOUR_USERNAME/post/{post_id}")
else:
    print("\n❌ Post failed - check logs above")
```

**Run test:**

```bash
cd /home/chiefgyk3d/src/twitch-and-toot
doppler run -- python3 test_threads.py
```

**Expected output:**
```
✓ Threads authenticated (@your_username)
✅ Authentication successful!

Posting: 🎮 Testing Stream Daemon Threads integration! #StreamDaemon
Character count: 59/500

✓ Threads post published: 1234567890
✅ SUCCESS! Post ID: 1234567890
```

---

## Important Notes

### Character Limits

- **Maximum:** 500 characters (includes URLs, hashtags, emojis)
- **AI Generator limits:**
  - Start messages: 440 chars (+ URL ≈ 490 total)
  - End messages: 480 chars (room for hashtags)

### Hashtag Recommendation

**Use ONE hashtag maximum** for Threads posts. The AI generator leaves room for this.

Example end message with hashtag:
```
Thanks for watching! Stream VOD available at the link 🎮 #Twitch
```

### Rate Limits

- **250 posts per 24 hours** per user
- Applies to all posts (start + end messages)
- With 5-minute check intervals: ~288 checks/day (safe margin)
- Monitoring 10 streamers: ~20 posts/day (well under limit)

### Token Expiration

Long-lived tokens expire after **60 days**. Set a calendar reminder to refresh:

```bash
# Refresh before expiry
curl -X GET "https://graph.threads.net/refresh_access_token?grant_type=th_refresh_token&access_token=CURRENT_LONG_LIVED_TOKEN"

# Update in Doppler
doppler secrets set THREADS_ACCESS_TOKEN="NEW_TOKEN"
```

---

## Troubleshooting

### Authentication Failed

**Error:** `✗ Threads authentication failed: missing user_id or access_token`

**Solution:**
```bash
# Check secrets are set
doppler secrets get THREADS_USER_ID
doppler secrets get THREADS_ACCESS_TOKEN

# Verify they're not empty
```

### Invalid Access Token

**Error:** `API Error: {'error': {'message': 'Invalid OAuth access token'}}`

**Solutions:**
1. Token expired (60 days) - generate new long-lived token
2. Wrong token type - make sure you exchanged for long-lived token
3. Token not for Threads - regenerate with `threads_basic` and `threads_content_publish` permissions

### User ID Not Found

**Error:** `API Error: {'error': {'message': 'Unsupported get request'}}`

**Solution:** Wrong User ID format. Make sure you're using:
- ✅ Instagram/Threads User ID (numeric, e.g., `123456789`)
- ❌ NOT username (e.g., `@myusername`)
- ❌ NOT Facebook User ID

Get correct ID:
```bash
curl "https://graph.instagram.com/me?fields=id&access_token=YOUR_TOKEN"
```

### Message Too Long

**Error:** `✗ CRITICAL: Message exceeds Threads' 500 char limit`

**Solution:** This shouldn't happen with AI generator, but if it does:
1. Check AI generator settings
2. Verify message templates aren't too long
3. URLs count toward limit (typically 23-30 chars)

### Can't Find Threads in Meta Developer Portal

**Solution:** Threads API might be in limited release. Check:
1. Your account is approved for Threads API
2. You're using a Business/Creator Instagram account (required)
3. Contact Meta support for API access

---

## Quick Reference

### Required Secrets

```bash
THREADS_ENABLE_POSTING=True
THREADS_USER_ID=123456789              # Your Instagram/Threads user ID
THREADS_ACCESS_TOKEN=THQVJxxxxx...     # 60-day long-lived token
```

### Optional Configuration (in .env, not secrets)

```bash
# Doppler secret names (if using custom names)
SECRETS_DOPPLER_THREADS_SECRET_NAME=THREADS
```

### API Endpoints

- **Auth Test:** `GET https://graph.threads.net/v1.0/{user-id}?fields=id,username`
- **Create Container:** `POST https://graph.threads.net/v1.0/{user-id}/threads`
- **Publish Post:** `POST https://graph.threads.net/v1.0/{user-id}/threads_publish`
- **Token Exchange:** `POST https://graph.threads.net/oauth/access_token`
- **Token Refresh:** `GET https://graph.threads.net/refresh_access_token`

---

## Next Steps

After testing works:

1. **Enable in main config:**
   ```bash
   doppler secrets set THREADS_ENABLE_POSTING=True
   ```

2. **Customize messages (optional):**
   - Edit `messages.txt` for start messages
   - Edit `end_messages.txt` for end messages with hashtags

3. **Run Stream Daemon:**
   ```bash
   doppler run -- python3 stream-daemon.py
   ```

4. **Set reminder:** Refresh access token in 50 days (10-day buffer)

---

## Additional Resources

- **Threads API Docs:** https://developers.facebook.com/docs/threads/
- **Getting Started:** https://developers.facebook.com/docs/threads/get-started
- **Rate Limits:** https://developers.facebook.com/docs/threads/troubleshooting#rate-limits
- **Full Platform Guide:** `docs/platforms/social/threads.md`
