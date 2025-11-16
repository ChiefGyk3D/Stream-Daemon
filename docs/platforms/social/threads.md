# Threads (Meta) Platform Setup Guide

## Overview

Threads is Meta's (formerly Facebook) text-based conversation platform that launched in 2023 as a companion app to Instagram. Stream Daemon supports posting stream announcements to Threads using the official Threads API.

**Character Limit:** 500 characters (including URLs and hashtags)

## Prerequisites

1. **Instagram Account**: You need an Instagram account to use Threads
2. **Threads Profile**: Create a Threads profile linked to your Instagram account at https://www.threads.net/
3. **Meta Developer Account**: Create a developer account at https://developers.facebook.com/
4. **Meta App**: Create an app with the "Threads Use Case" enabled

## Step 1: Create a Meta App

1. Go to https://developers.facebook.com/apps
2. Click **Create App**
3. Select **"None"** for use case (you'll add Threads next)
4. Click **Next**
5. Enter your app details:
   - **App Name**: e.g., "My Stream Bot"
   - **App Contact Email**: Your email address
6. Click **Create App**
7. From the app dashboard, click **Add Product**
8. Find **Threads** and click **Set Up**

### Important: Two App IDs

When you create a Meta app, you'll see **two app IDs**:
- **Facebook App ID**: For Facebook/Instagram products
- **Threads App ID**: For Threads API (use this one!)

⚠️ **Make sure you use the Threads App ID and Threads App Secret for API calls.**

## Step 2: Configure Threads Product

1. In your app dashboard, go to **Threads** > **Settings**
2. Under **Basic Settings**, note your:
   - **Threads App ID**
   - **Threads App Secret**
3. Add a **Redirect URI** (e.g., `https://localhost/` for testing)
4. Save changes

## Step 3: Get Your Threads User ID

Your Threads User ID is the same as your Instagram User ID. You can get it using the Instagram Graph API:

### Method 1: Using Graph API Explorer

1. Go to https://developers.facebook.com/tools/explorer/
2. Select your app from the dropdown
3. In the **User or Page** dropdown, select your Instagram Business/Creator account
4. In the query field, enter: `me?fields=id,username`
5. Click **Submit**
6. Copy the `id` value - this is your **Threads User ID**

### Method 2: Using a Test Script

```bash
# Replace with your Instagram access token
curl -X GET "https://graph.instagram.com/me?fields=id,username&access_token=YOUR_ACCESS_TOKEN"
```

## Step 4: Get Permissions and Access Token

### Required Permissions

Your app needs the following permissions:
- `threads_basic` - Required for all Threads endpoints
- `threads_content_publish` - Required for posting to Threads

### Generate Access Token

#### Option A: Using Authorization Flow (Recommended)

1. Build an authorization URL:
```
https://www.threads.net/oauth/authorize
  ?client_id=YOUR_THREADS_APP_ID
  &redirect_uri=YOUR_REDIRECT_URI
  &scope=threads_basic,threads_content_publish
  &response_type=code
```

2. Visit this URL in your browser and authorize your app
3. You'll be redirected to your redirect URI with an authorization code:
```
https://your-redirect-uri/?code=AUTHORIZATION_CODE
```

4. Exchange the authorization code for a short-lived access token:
```bash
curl -X POST "https://graph.threads.net/oauth/access_token" \
  -d "client_id=YOUR_THREADS_APP_ID" \
  -d "client_secret=YOUR_THREADS_APP_SECRET" \
  -d "grant_type=authorization_code" \
  -d "redirect_uri=YOUR_REDIRECT_URI" \
  -d "code=AUTHORIZATION_CODE"
```

Response:
```json
{
  "access_token": "SHORT_LIVED_TOKEN",
  "token_type": "bearer",
  "expires_in": 3600
}
```

5. Exchange short-lived token for long-lived token (60 days):
```bash
curl -X GET "https://graph.threads.net/access_token" \
  -d "grant_type=th_exchange_token" \
  -d "client_secret=YOUR_THREADS_APP_SECRET" \
  -d "access_token=SHORT_LIVED_TOKEN"
```

Response:
```json
{
  "access_token": "LONG_LIVED_TOKEN",
  "token_type": "bearer",
  "expires_in": 5184000
}
```

#### Option B: Using Access Token Tool (Testing Only)

For development/testing, you can use the Access Token Tool:
1. Go to https://developers.facebook.com/tools/accesstoken/
2. Select your Threads app
3. Generate a User Access Token with required permissions
4. ⚠️ **This token expires in 1 hour** - exchange it for a long-lived token immediately

### Refresh Long-Lived Tokens

Long-lived tokens expire after 60 days. Refresh them before expiry:

```bash
curl -X GET "https://graph.threads.net/refresh_access_token" \
  -d "grant_type=th_refresh_token" \
  -d "access_token=LONG_LIVED_TOKEN"
```

Response:
```json
{
  "access_token": "NEW_LONG_LIVED_TOKEN",
  "token_type": "bearer",
  "expires_in": 5184000
}
```

## Step 5: Add Threads Testers (For Testing)

Before your app is approved by Meta's App Review, only Threads Testers can use it:

1. In your Meta app dashboard, go to **Roles** > **Threads Testers**
2. Click **Add Threads Testers**
3. Enter the Instagram username or User ID
4. Send the invitation

The invited user must accept:
1. Go to https://www.threads.net/settings/account
2. Look for **Website Permissions**
3. Accept the pending invitation

## Step 6: Configure Stream Daemon

Add the following to your `.env` file or secrets manager:

```bash
# Threads Configuration
THREADS_ENABLE_POSTING=true
THREADS_USER_ID=your_instagram_user_id_here
THREADS_ACCESS_TOKEN=your_long_lived_access_token_here
```

### Using Doppler

```bash
doppler secrets set THREADS_ENABLE_POSTING true
doppler secrets set THREADS_USER_ID your_instagram_user_id_here
doppler secrets set THREADS_ACCESS_TOKEN your_long_lived_access_token_here
```

### Using AWS Secrets Manager

Store your Threads access token in AWS Secrets Manager:

```json
{
  "threads_access_token": "your_long_lived_access_token_here"
}
```

Then set:
```bash
THREADS_ENABLE_POSTING=true
THREADS_USER_ID=your_instagram_user_id_here
SECRETS_AWS_THREADS_SECRET_NAME=your-secret-name
```

### Using HashiCorp Vault

Store your Threads access token in Vault:

```bash
vault kv put secret/threads access_token=your_long_lived_access_token_here
```

Then set:
```bash
THREADS_ENABLE_POSTING=true
THREADS_USER_ID=your_instagram_user_id_here
SECRETS_VAULT_THREADS_SECRET_PATH=secret/threads
```

## Step 7: Test Your Configuration

Run the stream daemon:

```bash
python stream-daemon.py
```

Look for the Threads authentication message:
```
✓ Threads authenticated (@your_username)
```

If authentication fails, check:
- Your Threads User ID is correct
- Your access token hasn't expired (60 days for long-lived tokens)
- Your app has the required permissions (`threads_basic`, `threads_content_publish`)
- You're using the **Threads App ID**, not the Facebook App ID

## Character Limits

Threads enforces a **500 character limit** for all text posts, including:
- Message text
- URLs (fully expanded, not shortened)
- Hashtags
- Emojis (counted as UTF-8 bytes)

**Stream Daemon's AI generator automatically caps Threads messages at:**
- **440 characters** for start messages (leaves room for URL + hashtags + buffer)
- **480 characters** for end messages (no URL, more room for content)

Emergency truncation at 500 chars is in place as a safety net.

## Rate Limits

Threads API has the following rate limits:

- **250 posts per 24 hours** per user
- Carousel posts count as 1 post
- Rate limits are per-user, not per-app

If you exceed the rate limit, you'll receive a 429 error. The daemon will log this error but continue running.

## Threading Support

Stream Daemon fully supports Threads threading modes:

### Threading Modes

Configure in your `.env`:

```bash
# Live announcement threading
LIVE_THREADING_MODE=separate    # Each platform gets separate post (default)
# LIVE_THREADING_MODE=thread     # Reply to previous live announcement
# LIVE_THREADING_MODE=combined   # Single post for all live streams

# End announcement threading  
END_THREADING_MODE=thread        # Reply to live announcement (default)
# END_THREADING_MODE=separate    # Separate end post
# END_THREADING_MODE=combined    # Single end post for all streams
# END_THREADING_MODE=disabled    # No end messages
# END_THREADING_MODE=single_when_all_end  # Wait until all streams end
```

**Example: Thread mode**
```
Post 1: "🔴 LIVE on Twitch! Playing Minecraft..."
  └─ Post 2: "Thanks for watching! Stream ended."
```

## API Details

### Two-Step Posting Process

Threads uses a two-step process for posting:

1. **Create Media Container**: `POST /{user-id}/threads`
   - Creates a container with your text/media
   - Returns a container ID
   - Text-only posts: instant
   - Media posts: takes time to process

2. **Publish Container**: `POST /{user-id}/threads_publish`
   - Publishes the container
   - Returns the post ID
   - Can be used for threading (reply_to_id)

Stream Daemon handles both steps automatically with a 2-second delay between them.

### Supported Features

✅ **Supported:**
- Text posts (up to 500 chars)
- URL links (automatically rendered as cards)
- Hashtags (clickable topics)
- Threading/replies
- Reply-to for creating threads

❌ **Not Yet Supported:**
- Image/video attachments
- Carousel posts (multiple images)
- Polls
- GIF attachments
- Location tagging

These features may be added in future updates.

## Troubleshooting

### Authentication Failed

**Error**: `✗ Threads authentication failed: missing user_id or access_token`

**Solutions**:
- Verify `THREADS_USER_ID` is set
- Verify `THREADS_ACCESS_TOKEN` is set
- Check your secrets manager configuration

### Invalid OAuth Access Token

**Error**: `API Error: Invalid OAuth access token`

**Solutions**:
- Your access token may have expired (60 days for long-lived tokens)
- Generate a new long-lived token
- Set up automatic token refresh before expiry

### Permission Denied

**Error**: `API Error: Permission denied`

**Solutions**:
- Verify your app has `threads_basic` and `threads_content_publish` permissions
- If testing, ensure your Instagram account is added as a Threads Tester
- If in production, ensure permissions are approved via App Review

### Message Too Long

**Error**: `CRITICAL: Message exceeds Threads' 500 char limit`

**Solutions**:
- This should never happen with AI generator enabled
- Check your `messages.txt` file - may contain overly long static messages
- Verify AI generator is enabled and working
- Report as a bug if AI generator is enabled

### Rate Limit Exceeded

**Error**: `429 Rate Limit Exceeded`

**Solutions**:
- You've posted more than 250 times in 24 hours
- Wait until your rate limit resets
- Consider reducing posting frequency
- Multiple streams going live simultaneously can trigger this

### Wrong App ID

**Error**: `API Error: Invalid client_id`

**Solutions**:
- Make sure you're using the **Threads App ID**, not Facebook App ID
- Check your app dashboard - you should see two IDs
- Verify the App ID in your configuration matches your app

## App Review (Going to Production)

For production use with non-tester accounts, you must submit your app for App Review:

1. In your app dashboard, go to **App Review** > **Permissions and Features**
2. Request review for:
   - `threads_basic`
   - `threads_content_publish`
3. Provide:
   - **Use case description**: Explain your stream bot
   - **Step-by-step instructions**: How to test your app
   - **Screencast**: Video showing your app in action
4. Submit for review
5. Meta typically reviews within 3-5 business days

Until approved, only Threads Testers can use your app.

## Security Best Practices

1. **Never commit access tokens**: Use environment variables or secrets managers
2. **Rotate tokens regularly**: Refresh long-lived tokens before 60-day expiry
3. **Use secrets managers**: Doppler, AWS Secrets Manager, or HashiCorp Vault
4. **Limit permissions**: Only request permissions you need
5. **Monitor API usage**: Watch for unusual posting patterns
6. **Set up alerts**: Notify if authentication fails

## Resources

- **Threads API Documentation**: https://developers.facebook.com/docs/threads/
- **Get Started Guide**: https://developers.facebook.com/docs/threads/get-started
- **API Reference**: https://developers.facebook.com/docs/threads/reference
- **Sample App**: https://github.com/fbsamples/threads_api
- **Developer Support**: https://developers.facebook.com/support/

## Related Documentation

- [Configuration Guide](../../configuration/secrets.md)
- [Multi-Platform Support](../../features/multi-platform.md)
- [AI Message Generation](../../features/ai-messages.md)
- [Secrets Management](../../configuration/secrets-wizard.md)
