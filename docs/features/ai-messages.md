# AI-Powered Stream Messages

🤖 **Optional Feature**: Use Google's Gemini AI to generate personalized, engaging stream announcements instead of static messages.

## Overview

Stream Daemon can use Google's Gemini LLM to automatically generate unique, engaging messages for every stream announcement. Instead of repeating the same messages, each post is dynamically crafted with relevant hashtags, inviting language, and platform-appropriate formatting.

**Traditional Approach:**
```
🎮 chiefgyk3d is now live on Twitch! Playing Elden Ring
```

**AI-Generated:**
```
🚀 The gaming adventure begins NOW! Join chiefgyk3d as they tackle 
Elden Ring's toughest bosses live on Twitch! Will the boss fall or 
will rage ensue? 😤🎮 #EldenRing #LiveNow #TwitchStreaming

https://twitch.tv/chiefgyk3d
```

---

## Features

### ✨ Dynamic Content Generation

- **Unique every time** - No repeated messages
- **Context-aware** - Understands your stream title and platform
- **Engaging tone** - Inviting language that encourages viewers to join
- **Smart hashtags** - Auto-generates relevant hashtags from stream content

### 📏 Platform-Aware Character Limits

AI automatically respects character limits for each social platform:

| Platform | Limit | AI Behavior |
|----------|-------|-------------|
| **Bluesky** | 300 chars | Concise, punchy messages |
| **Mastodon** | 500 chars | More detailed announcements |
| **Discord** | 500 chars | Rich descriptions |
| **Matrix** | 500 chars | Formatted HTML messages |

### 🔗 Smart URL Handling

**Stream Start Messages:**
- AI generates the message content
- Stream URL is **automatically appended**
- Character limit accounts for URL length
- Format: `"<AI message>\n\n<stream_url>"`

**Stream End Messages:**
- No URL needed (stream already ended)
- Full character limit available for thank-you message
- Warm, grateful tone

### 🎯 Intelligent Fallback

If AI generation fails (network issue, API error, quota exceeded):
- Automatically falls back to your static messages from `messages.txt`
- Seamless failover - stream announcements always work
- Error logged for debugging

---

## Quick Start

### Step 1: Get Gemini API Key

1. **Go to Google AI Studio:**
   - Visit [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
   - Sign in with your Google account

2. **Create API Key:**
   - Click **"Create API Key"**
   - Select "Create API key in new project" (or use existing)
   - Copy your API key (starts with `AIza...`)
   - **Keep it secure!**

### Step 2: Configure Stream Daemon

**Option A: Using Environment Variables (.env)**

```bash
# Enable AI message generation
LLM_ENABLE=True

# Your Gemini API key
GEMINI_API_KEY=AIzaSyA_your_actual_api_key_here

# Model to use (recommended: gemini-2.0-flash-lite)
LLM_MODEL=gemini-2.0-flash-lite
```

**Option B: Using Secrets Manager (Recommended for Production)**

**In your `.env` file:**
```bash
# Enable AI messages
LLM_ENABLE=True

# Model selection (not sensitive, OK in .env)
LLM_MODEL=gemini-2.0-flash-lite

# Configure secrets manager
SECRETS_MANAGER=doppler
SECRETS_DOPPLER_LLM_SECRET_NAME=LLM
```

**In Doppler (or your secrets manager):**
```bash
# Add API key to Doppler
doppler secrets set GEMINI_API_KEY="AIzaSyA_your_key_here"

# Optional: also store enable flag and model in Doppler
doppler secrets set LLM_ENABLE="True"
doppler secrets set LLM_MODEL="gemini-2.0-flash-lite"
```

### Step 3: Test It!

Start streaming and watch the AI-generated announcements!

**To test without going live:**
```bash
# Check AI configuration
python3 -c "
from stream_daemon.ai.generator import AIMessageGenerator
import os
from dotenv import load_dotenv
load_dotenv()

gen = AIMessageGenerator()
if gen.is_initialized:
    print('✅ AI message generation is ready!')
    msg = gen.generate_start_message('Twitch', 'chiefgyk3d', 'Testing Stream', 'bluesky')
    print(f'Sample message: {msg}')
else:
    print('❌ AI not initialized - check configuration')
"
```

---

## Configuration Reference

### Required Settings

| Variable | Description | Example |
|----------|-------------|---------|
| `LLM_ENABLE` | Enable AI message generation | `True` |
| `GEMINI_API_KEY` | Google Gemini API key | `AIzaSyA...` |

### Optional Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_MODEL` | Gemini model to use | `gemini-2.0-flash-lite` |

### Model Options

**gemini-2.0-flash-lite** (Recommended - Default):
- ✅ Very fast response time (~1-2 seconds)
- ✅ Higher rate limits (30 requests/minute vs 15 for 1.5-flash)
- ✅ Cost-effective (free tier: 30 requests/minute)
- ✅ Optimized for short-form content like social media posts
- ✅ Best for most users

**gemini-1.5-flash**:
- ✅ Fast response time (~1-2 seconds)
- ✅ Cost-effective (free tier: 15 requests/minute, 1 million tokens/day)
- ✅ Great quality for social media posts
- ⚠️ Lower rate limits than 2.0-flash-lite

**gemini-1.5-pro**:
- ⚠️ Slower response time (~3-5 seconds)
- ⚠️ More expensive (free tier: 2 requests/minute, 50 requests/day)
- ✅ Slightly better quality
- ⚠️ Overkill for stream announcements

**gemini-2.0-flash-exp** (Experimental):
- ⚠️ May be unstable
- ✅ Latest features
- ⚠️ Subject to change

**Recommendation:** Stick with `gemini-2.0-flash-lite` (the default) unless you have specific needs.

---

## How It Works

### Message Generation Flow

```
┌─────────────────────────────────────────┐
│ Stream Goes Live                        │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│ Is LLM_ENABLE=True?                     │
└────┬─────────────────────────┬──────────┘
     │ YES                      │ NO
     ▼                          ▼
┌──────────────────┐   ┌─────────────────┐
│ Call Gemini API  │   │ Use static      │
│ with:            │   │ message from    │
│ - Platform       │   │ messages.txt    │
│ - Username       │   └─────────────────┘
│ - Stream Title   │
│ - Social Target  │
│ - Char Limit     │
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│ AI generates     │
│ personalized     │
│ message with     │
│ hashtags         │
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│ Append URL       │
│ (for start msgs) │
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│ Post to social   │
│ platforms        │
└──────────────────┘
```

### Context Provided to AI

**For Stream Start Messages:**

The AI receives:
```
Platform: Twitch
Username: chiefgyk3d
Stream Title: Elden Ring - Boss Rush Challenge
Target Social: bluesky (300 char limit)
Message Type: Stream started
```

AI is instructed to:
- Generate exciting, inviting announcement
- Include 2-4 relevant hashtags
- Respect character limit (minus URL space)
- Be enthusiastic and urgent
- Make people want to join NOW

**For Stream End Messages:**

The AI receives:
```
Platform: Twitch
Username: chiefgyk3d
Stream Title: Elden Ring - Boss Rush Challenge
Target Social: mastodon (500 char limit)
Message Type: Stream ended
```

AI is instructed to:
- Generate warm thank-you message
- Be grateful and friendly
- Include 1-3 relevant hashtags
- Encourage viewers to catch next stream
- No URL needed

---

## Character Limit Handling

### How Limits Work

**Bluesky (300 characters):**
```
AI generates up to: 270 characters
URL + spacing:      ~30 characters
─────────────────────────────────
Total:              300 characters
```

**Mastodon (500 characters):**
```
AI generates up to: 470 characters
URL + spacing:      ~30 characters
─────────────────────────────────
Total:              500 characters
```

### Overflow Protection

If AI generates a message that's too long:

```python
if len(full_message) > max_chars:
    # Truncate content (preserve URL)
    overflow = len(full_message) - max_chars
    message = message[:-overflow-3] + "..."
    full_message = f"{message}\n\n{url}"
```

This ensures posts **never** exceed platform limits.

---

## Example Messages

### Stream Start Examples

**Twitch → Bluesky (300 char limit):**
```
🔥 LIVE NOW! chiefgyk3d is tackling Elden Ring's toughest bosses! 
Epic fails or legendary victories? Find out! 🎮⚔️ #EldenRing 
#TwitchLive #GamingCommunity

https://twitch.tv/chiefgyk3d
```

**YouTube → Mastodon (500 char limit):**
```
📺 The stream is LIVE! Join chiefgyk3d on YouTube for an incredible 
Elden Ring boss rush marathon! Watch as they take on every major boss 
in one epic session. Will they succeed or will the bosses reign supreme? 
Tune in now for gaming greatness! 🎮✨ #EldenRing #YouTubeLive #BossRush 
#LiveGaming

https://youtube.com/@chiefgyk3d/live
```

**Kick → Discord (500 char limit):**
```
🟢 GO TIME! chiefgyk3d just went live on Kick with Elden Ring boss rush 
action! This is going to be INSANE! Join the community and watch the chaos 
unfold in real-time. Will skill triumph or will rage quit? Only one way to 
find out! 🎮🔥 #Kick #EldenRing #LiveNow

https://kick.com/chiefgyk3d
```

### Stream End Examples

**Twitch → Bluesky:**
```
That's a wrap! 🎬 Thanks for joining the Elden Ring boss rush stream! 
What an incredible session! See you next time for more gaming adventures! 
💜 #ThankYou #TwitchCommunity #EldenRing
```

**YouTube → Mastodon:**
```
Stream complete! 🎉 Thank you SO much to everyone who joined today's 
Elden Ring marathon! Your support means the world! The VOD will be 
available soon. Don't forget to like, subscribe, and hit that notification 
bell for next time! See you in the next stream! 🙏✨ #YouTubeCommunity 
#ThankYou #EldenRing
```

---

## Cost & Rate Limits

### Google Gemini Free Tier

**gemini-2.0-flash-lite (Default):**
- ✅ **30 requests per minute**
- ✅ **High rate limits optimized for social media posting**
- ✅ **Free tier available**

**gemini-1.5-flash:**
- ✅ **15 requests per minute**
- ✅ **1 million tokens per day**
- ✅ **1,500 requests per day**

**Usage per Stream:**
- Stream start: 1 request × 4 social platforms = 4 requests
- Stream end: 1 request × 4 social platforms = 4 requests
- **Total per stream: ~8 requests**

**You can handle:**
- With 2.0-flash-lite: Multiple simultaneous streams with 30 req/min
- With 1.5-flash: ~187 streams per day (well above reasonable usage)
- Multiple streams simultaneously

**Cost if exceeding free tier:**
- $0.075 per 1M input tokens
- $0.30 per 1M output tokens
- Typical stream announcement: ~500 tokens total
- **Extremely cheap even at scale**

### Rate Limit Handling

Stream Daemon automatically handles rate limits:

1. **Request fails with rate limit error**
2. **Waits and retries** (exponential backoff)
3. **After 3 retries, falls back** to static messages
4. **Logs error** for debugging

You'll never miss a stream announcement due to rate limits.

---

## Fallback Behavior

AI generation can fail for several reasons. Stream Daemon gracefully handles all scenarios:

### Automatic Fallback Scenarios

| Scenario | Behavior |
|----------|----------|
| **LLM_ENABLE=False** | Always use static messages |
| **API Key Missing** | Fall back to static messages |
| **Network Error** | Retry 3x, then use static |
| **Rate Limit Hit** | Wait and retry, then use static |
| **Invalid Response** | Use static messages |
| **Generation Empty** | Use static messages |

### What You'll See

**Successful AI generation:**
```
✓ AI generated start message for Twitch → bluesky
```

**Fallback to static:**
```
⚠ AI generation failed: Rate limit exceeded, using fallback message
```

**Complete failure (AI disabled):**
```
ℹ AI messages disabled, using static messages
```

All scenarios result in stream announcements being posted - you never miss a notification!

---

## Troubleshooting

### "AI message generation failed"

**Problem:** AI not generating messages

**Check:**
1. Is `LLM_ENABLE=True` set?
2. Is `GEMINI_API_KEY` configured?
3. Is the API key valid (starts with `AIza`)?
4. Is the model name correct? (`gemini-2.0-flash-lite` or `gemini-1.5-flash`)

**Test API key manually:**
```bash
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-lite:generateContent?key=YOUR_KEY" \
  -H 'Content-Type: application/json' \
  -d '{"contents":[{"parts":[{"text":"Say hello"}]}]}'
```

### "Invalid API Key"

**Problem:** Gemini returns authentication error

**Solutions:**
1. Verify API key is correct (copy again from Google AI Studio)
2. Check for extra spaces or characters
3. Ensure key starts with `AIza`
4. Try generating a new API key
5. Verify project has Gemini API enabled

### "Rate limit exceeded"

**Problem:** Too many requests

**Solutions:**
1. **Wait a few minutes** - rate limits reset
2. **Reduce request frequency:**
   - Free tier: 15 requests/minute
   - Streaming to 4 platforms = 4 requests per notification
   - Max ~3 stream start/end cycles per minute
3. **Upgrade to paid tier** (usually unnecessary)
4. **Use static messages temporarily:**
   ```bash
   LLM_ENABLE=False
   ```

### "Messages too long"

**Problem:** Generated messages exceed character limits

**This shouldn't happen** - AI is instructed to respect limits. But if it does:

1. **Check character limits in code:**
   - Bluesky: 300
   - Mastodon: 500
   - Discord: 500
   - Matrix: 500

2. **Overflow protection** automatically truncates

3. **Report if persistent** - may need prompt tuning

### "AI generates boring messages"

**Problem:** Generated messages aren't engaging enough

**Solutions:**
1. **Use more descriptive stream titles:**
   - ❌ "Gaming"
   - ✅ "Elden Ring - Boss Rush Challenge Mode"

2. **Model choice:**
   - Try `gemini-1.5-pro` for slightly better quality
   - (Though gemini-2.0-flash-lite is usually great)

3. **Prompts can be tuned** in code:
   - Edit `stream_daemon/ai/generator.py`
   - Modify `_generate_start_message()` and `_generate_end_message()`

---

## Advanced Configuration

### Custom Prompts

Want to customize how AI generates messages? Edit the prompts in `stream_daemon/ai/generator.py`:

**Location:** `stream_daemon/ai/generator.py`, method `_generate_start_message()`

**Current prompt template:**
```python
prompt = f"""Generate an exciting social media post announcing a livestream has just started.

Stream: {username} on {platform}
Title: {stream_title}
Max: {char_limit} characters (excluding URL which will be added automatically)

Requirements:
- Enthusiastic and inviting
- 2-4 relevant hashtags
- Make people want to join NOW
- Don't include URL (added automatically)
"""
```

**Customize it:**
```python
# Make it more casual
prompt = f"""Write a chill social media post about a stream that just started...

# Make it more professional
prompt = f"""Craft a professional announcement for a live broadcast...

# Make it more gaming-focused
prompt = f"""Generate a hype gaming announcement...
```

### Multiple API Keys

To use different API keys for different environments:

```bash
# Development
LLM_ENABLE=True
GEMINI_API_KEY=AIza_dev_key_here

# Production (in Doppler)
doppler secrets set GEMINI_API_KEY="AIza_prod_key_here" --config prd
```

---

## Security Best Practices

### DO:
- ✅ Store API key in secrets manager (Doppler/AWS/Vault)
- ✅ Use separate API keys for dev/staging/production
- ✅ Regenerate API key if compromised
- ✅ Monitor usage in Google AI Studio

### DON'T:
- ❌ Commit API key to git
- ❌ Share API key in screenshots/logs
- ❌ Use production key in development
- ❌ Post API key publicly

### API Key Rotation

**How to rotate API keys:**

1. **Generate new API key** in Google AI Studio
2. **Update secrets manager:**
   ```bash
   doppler secrets set GEMINI_API_KEY="new_key_here"
   ```
3. **Restart Stream Daemon**
4. **Delete old API key** from Google AI Studio

---

## See Also

- [Custom Messages Guide](custom-messages.md) - Configure static fallback messages
- [Multi-Platform Guide](multi-platform.md) - Multi-streaming strategies
- [Secrets Management](../configuration/secrets.md) - Doppler/AWS/Vault setup
- [Quick Start Guide](../getting-started/quickstart.md) - Initial setup

---

**Last Updated:** 2024
