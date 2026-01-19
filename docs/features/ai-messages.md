# AI-Powered Stream Messages

🤖 **Optional Feature**: Use AI to generate personalized, engaging stream announcements instead of static messages.

## Overview

Stream Daemon supports multiple AI providers to automatically generate unique, engaging messages for every stream announcement. Instead of repeating the same messages, each post is dynamically crafted with relevant hashtags, inviting language, and platform-appropriate formatting.

**Supported Providers:**
- **Google Gemini** - Cloud-based AI with high-quality output (requires API key)
- **Ollama** - Local LLM server for privacy and offline use (requires local installation)

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

Choose your preferred AI provider:

### Option 1: Ollama (Local LLM Server)

**Best for:** Privacy, offline use, no API costs, full control

#### Step 1: Install and Configure Ollama

1. **Install Ollama on your LLM server:**
   ```bash
   # Linux
   curl -fsSL https://ollama.com/install.sh | sh
   
   # macOS
   brew install ollama
   
   # Windows - download from https://ollama.com/download
   ```
   
   **Multi-GPU Setup:** For mixed/multiple GPU configurations (different vendors/models), see [FrankenLLM](https://github.com/ChiefGyk3D/FrankenLLM) for advanced setup guides.

2. **Browse available models:**
   ```bash
   # View all available models at https://ollama.com/library
   # Or search from command line:
   ollama list          # Show locally installed models
   ollama search llama  # Search for models (requires ollama >= 0.1.26)
   ```

3. **Pull a model (recommended: gemma2:2b for balance of quality and speed):**
   ```bash
   ollama pull gemma2:2b
   
   # Other good options:
   # ollama pull llama3.2:3b  # Faster, smaller
   # ollama pull qwen2.5:3b   # Good for technical content
   # ollama pull mistral:7b   # Higher quality, slower
   ```

4. **Start Ollama server:**
   ```bash
   ollama serve
   # By default runs on http://localhost:11434
   ```

#### Step 2: Configure Stream Daemon

**In your `.env` file:**
```bash
# Enable AI message generation
LLM_ENABLE=True

# Use Ollama provider
LLM_PROVIDER=ollama

# Ollama server configuration
LLM_OLLAMA_HOST=http://192.168.1.100  # Your LLM server IP
LLM_OLLAMA_PORT=11434                  # Default Ollama port
LLM_MODEL=gemma2:2b                    # Model to use

# Optional: Retry configuration
LLM_MAX_RETRIES=3
LLM_RETRY_DELAY_BASE=2

# NOTE: You can keep both Gemini and Ollama settings in the same .env file!
# Only the active provider (set by LLM_PROVIDER) will be used.
# Example - both configs coexist:
# GEMINI_API_KEY=AIza...           # Used when LLM_PROVIDER=gemini
# LLM_OLLAMA_HOST=http://...       # Used when LLM_PROVIDER=ollama
# Just change LLM_PROVIDER to switch between them!
```

**Remote Ollama Server:**
If Ollama is on a different machine, ensure it's accessible:
```bash
# On the Ollama server, allow remote connections:
OLLAMA_HOST=0.0.0.0 ollama serve

# Or set in systemd/environment
export OLLAMA_HOST=0.0.0.0
```

#### Step 3: Test It!

```bash
# Verify Ollama connection
curl http://192.168.1.100:11434/api/tags

# Test AI generation
python3 -c "
from stream_daemon.ai.generator import AIMessageGenerator
from dotenv import load_dotenv
load_dotenv()

gen = AIMessageGenerator()
if gen.authenticate():
    print('✅ Ollama LLM is ready!')
    msg = gen.generate_stream_start_message(
        'Twitch', 'chiefgyk3d', 
        'Testing AI Messages', 
        'https://twitch.tv/test',
        'bluesky'
    )
    print(f'Sample message:\n{msg}')
else:
    print('❌ Ollama not initialized - check configuration')
"
```

---

### Option 2: Google Gemini (Cloud API)

**Best for:** Highest quality, no local resources needed, easy setup

#### Step 1: Get Gemini API Key

1. **Go to Google AI Studio:**
   - Visit [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
   - Sign in with your Google account

2. **Create API Key:**
   - Click **"Create API Key"**
   - Select "Create API key in new project" (or use existing)
   - Copy your API key (starts with `AIza...`)
   - **Keep it secure!**

#### Step 2: Configure Stream Daemon

**Option A: Using Environment Variables (.env)**

```bash
# Enable AI message generation
LLM_ENABLE=True

# Use Gemini provider (default)
LLM_PROVIDER=gemini

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

# Use Gemini provider
LLM_PROVIDER=gemini

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

#### Step 3: Test It!

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
if gen.authenticate():
    print('✅ AI message generation is ready!')
    msg = gen.generate_stream_start_message(
        'Twitch', 'chiefgyk3d', 
        'Testing Stream', 
        'https://twitch.tv/test',
        'bluesky'
    )
    print(f'Sample message:\n{msg}')
else:
    print('❌ AI not initialized - check configuration')
"
```

---

## Rate Limiting

### Built-in API Rate Limiting

Stream Daemon includes proactive rate limiting to prevent hitting Gemini API quota limits:

**Rate Limiting Strategy:**
- **Maximum Concurrent Calls:** 4 simultaneous API requests
- **Minimum Delay:** 2 seconds between requests (stays under 30 requests/minute limit)
- **Thread-Safe:** Global semaphore coordinates across all platforms

**How It Works:**
```python
# Semaphore limits concurrent requests
with _api_semaphore:  # Max 4 concurrent
    # Enforce minimum delay
    with _api_call_lock:
        if time_since_last_call < 2.0:
            sleep(2.0 - time_since_last_call)
        # Make API call
```

**Example Scenario:**
```
Twitch goes live → 4 social platforms request AI messages
  ├─ Request 1: Bluesky  (0s)       ✓ Immediate
  ├─ Request 2: Mastodon (2s delay) ✓ Queued
  ├─ Request 3: Discord  (4s delay) ✓ Queued
  └─ Request 4: Matrix   (6s delay) ✓ Queued

YouTube goes live → waits for available slots
  ├─ Request 5: Bluesky  (8s)       ✓ After slot opens
  └─ ...continues with 2s spacing
```

**Benefits:**
- ✅ Prevents 429 rate limit errors from Gemini API
- ✅ Handles burst traffic when multiple streams go live
- ✅ No configuration needed - works automatically
- ✅ Maintains existing retry logic for transient errors
- ✅ Stays well under Gemini's 30 requests/minute limit

**Gemini API Limits:**
- Free tier: 30 requests/minute, 4M tokens/minute, 1,500 requests/day
- With rate limiting: ~24 seconds for 12 requests (3 platforms × 4 social networks)
- Typical usage: 2-8 requests per stream event (start/end × platforms)

**No Configuration Required:**
Rate limiting is automatically enabled when using AI-powered messages. The 4 concurrent / 2-second delay defaults are optimal for most use cases.

---

## Configuration Reference

### Required Settings

| Variable | Description | Example |
|----------|-------------|---------|
| `LLM_ENABLE` | Enable AI message generation | `True` |
| `LLM_PROVIDER` | AI provider (`gemini` or `ollama`) | `gemini` or `ollama` |

### Gemini-Specific Settings

| Variable | Description | Example |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google Gemini API key (required for Gemini) | `AIzaSyA...` |
| `LLM_MODEL` | Gemini model to use | `gemini-2.0-flash-lite` |

### Ollama-Specific Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_OLLAMA_HOST` | Ollama server IP/hostname | `http://localhost` |
| `LLM_OLLAMA_PORT` | Ollama server port | `11434` |
| `LLM_MODEL` | Ollama model to use | `gemma2:2b` |

### Optional Settings (Both Providers)

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_MAX_RETRIES` | Maximum retry attempts on errors | `3` |
| `LLM_RETRY_DELAY_BASE` | Base delay for exponential backoff (seconds) | `2` |

### Gemini Model Options

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

### Ollama Model Options

**gemma2:2b** (Recommended - Default for 4B variant):
- ✅ Fast inference on modest hardware
- ✅ Good quality for social media posts
- ✅ Low memory usage (~2GB VRAM)
- ✅ Based on Google's Gemma 2 architecture
- ✅ Best balance of speed and quality

**llama3.2:3b**:
- ✅ Very fast inference
- ✅ Good quality
- ✅ Low memory usage (~2GB VRAM)
- ✅ Meta's latest small model

**qwen2.5:3b**:
- ✅ Excellent for technical content
- ✅ Fast inference
- ✅ Low memory usage (~2GB VRAM)
- ✅ Strong at following instructions

**mistral:7b**:
- ✅ Higher quality output
- ⚠️ Slower inference
- ⚠️ Higher memory usage (~5GB VRAM)
- ✅ Good for detailed, creative content

**phi3:3b**:
- ✅ Very fast
- ✅ Low memory (~2GB VRAM)
- ✅ Good at concise content
- ✅ Microsoft's efficient model

**To pull a model:**
```bash
# On your Ollama server
ollama pull gemma2:2b
ollama pull llama3.2:3b
ollama pull qwen2.5:3b
ollama pull mistral:7b
```

**Model Performance Tips:**
- For GPU: Any 3B-7B model works well
- For CPU only: Use 2B-3B models (gemma2:2b, llama3.2:3b)
- For fastest: llama3.2:3b or phi3:3b
- For quality: mistral:7b or qwen2.5:3b
- For balance: gemma2:2b (default)

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
│ Which provider?  │   │ Use static      │
│ - gemini         │   │ message from    │
│ - ollama         │   │ messages.txt    │
└────┬─────────────┘   └─────────────────┘
     │
     ├─ gemini ──────────┐
     │                   ▼
     │         ┌──────────────────┐
     │         │ Call Gemini API  │
     │         │ with API key     │
     │         └────┬─────────────┘
     │              │
     └─ ollama ─────┤
                    ▼
           ┌──────────────────┐
           │ Call LLM with:   │
           │ - Platform       │
           │ - Username       │
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

AI generation can fail for several reasons. Stream Daemon gracefully handles all scenarios with **automatic retry logic**.

### Automatic Retry for Transient Errors

Stream Daemon automatically retries API calls for temporary failures:

| Error Type | Retry? | Behavior |
|------------|--------|----------|
| **503 Service Unavailable** | ✅ Yes | Retries with exponential backoff |
| **429 Rate Limit Exceeded** | ✅ Yes | Waits and retries automatically |
| **Model Overloaded** | ✅ Yes | Intelligent retry with backoff |
| **Network Timeout** | ✅ Yes | Retries up to max attempts |
| **Quota Exceeded** | ✅ Yes | Retries with delays |
| **Invalid API Key** | ❌ No | Immediate fallback to static |
| **Authentication Error** | ❌ No | Immediate fallback to static |

**Retry Configuration** (customize in `.env`):
```bash
# Maximum retry attempts (default: 3)
LLM_MAX_RETRIES=3

# Base delay for exponential backoff in seconds (default: 2)
# Actual delays: 2s, 4s, 8s for attempts 1, 2, 3
LLM_RETRY_DELAY_BASE=2
```

**Exponential Backoff Pattern:**
- Attempt 1: Wait 2 seconds
- Attempt 2: Wait 4 seconds  
- Attempt 3: Wait 8 seconds
- After 3 failed retries: Fall back to static messages

### Fallback Scenarios

| Scenario | Behavior |
|----------|----------|
| **LLM_ENABLE=False** | Always use static messages (no API calls) |
| **API Key Missing** | Fall back to static messages immediately |
| **Network Error** | Retry 3x with backoff, then use static |
| **503 Overload** | Retry 3x (2s, 4s, 8s delays), then use static |
| **Rate Limit Hit** | Retry 3x with exponential backoff, then use static |
| **Invalid Response** | Use static messages immediately |
| **Generation Empty** | Use static messages immediately |

### What You'll See in Logs

**Successful generation (no retry):**
```
✨ Generated stream start message (245 chars content + URL = 280/300 total)
```

**Retry in progress:**
```
⚠ API error (attempt 1/4): 503 UNAVAILABLE. Retrying in 2s...
⚠ API error (attempt 2/4): 503 UNAVAILABLE. Retrying in 4s...
✨ Generated stream start message (238 chars content + URL = 273/300 total)
```

**Retry exhausted, using fallback:**
```
✗ Failed after 4 attempts: 503 Service Unavailable
⚠ AI generation failed, using fallback message
```

**AI disabled:**
```
ℹ AI messages disabled, using static messages
```

**All scenarios guarantee announcements are posted** - you never miss a notification!

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
