# AI-Powered Stream Messages (Google Gemini LLM)

🤖 **Optional Feature**: Use Google's Gemini AI to generate personalized, engaging stream announcements instead of static messages.

## Table of Contents
- [Why Use AI Messages?](#why-use-ai-messages)
- [Quick Start](#quick-start)
- [Features](#features)
- [Configuration](#configuration)
- [How It Works](#how-it-works)
- [Character Limits](#character-limits)
- [Fallback Behavior](#fallback-behavior)
- [Cost & Rate Limits](#cost--rate-limits)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

---

## Why Use AI Messages?

Traditional approach:
```
🎮 {username} is now live on {platform}! {stream_title}
```

With AI (Gemini):
```
🚀 The gaming adventure begins NOW! Join ChiefGYK3D as they tackle 
Elden Ring's toughest bosses live on Twitch! Will the boss fall or 
will rage ensue? 😤🎮 #EldenRing #LiveNow #TwitchStreaming

https://twitch.tv/chiefgyk3d
```

**Benefits:**
- ✨ **Dynamic & Unique**: Every stream gets a fresh, personalized message
- 🎯 **Engaging**: AI crafts inviting copy that draws viewers in
- #️⃣ **Smart Hashtags**: Auto-generates relevant hashtags from your stream title
- 📏 **Platform-Aware**: Respects Bluesky (300) and Mastodon (500) character limits
- 🔗 **URL Included**: Stream URL automatically added to start messages

---

## Quick Start

### 1. Get Your Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click **"Create API Key"**
3. Copy your API key (starts with `AIza...`)

### 2. Configure in Doppler (Recommended)

```bash
# In Doppler, add to your config:
LLM_ENABLE=True
GEMINI_API_KEY=AIzaSyA... (your actual key)
LLM_MODEL=gemini-1.5-flash
```

### 3. Or Configure in .env

```bash
# In .env file:
LLM_ENABLE=True
GEMINI_API_KEY=AIzaSyA... (your actual key)
LLM_MODEL=gemini-1.5-flash
```

### 4. Test It!

Start your stream and watch the AI-generated announcements! 🎉

---

## Features

### Platform-Specific Character Limits

AI automatically adjusts message length for each social platform:

| Platform | Character Limit | What Happens |
|----------|----------------|--------------|
| **Bluesky** | 300 chars | AI generates concise, punchy messages |
| **Mastodon** | 500 chars | AI uses more space for detailed messages |
| **Discord** | 500 chars | Default limit (very generous) |
| **Matrix** | 500 chars | Default limit |

### Smart URL Handling

**Stream Start Messages:**
- AI generates the message content
- Stream URL is **automatically appended**
- Character limit accounts for URL length
- Example: `"Amazing content here!\n\nhttps://twitch.tv/user"`

**Stream End Messages:**
- No URL needed (stream already ended)
- Full character limit available for thank-you message

### Hashtag Generation

AI analyzes your stream title and generates relevant hashtags:

```
Stream Title: "Elden Ring - Boss Rush Challenge"
Generated Hashtags: #EldenRing #BossRush #LiveNow #Twitch
```

### Dynamic Tone

**Stream Start:** Exciting, urgent, inviting
```
🔥 It's GO TIME! ChiefGYK3D just went live with an epic Elden Ring 
boss marathon! Witness the chaos unfold right now! 🎮⚔️
```

**Stream End:** Grateful, warm, encouraging
```
Thanks for joining the stream! What an incredible boss rush session! 
See you next time for more gaming adventures! 🙏✨
```

---

## Configuration

### Environment Variables

Add to `.env` or your secrets manager (Doppler/AWS/Vault):

```bash
# ============================================
# AI MESSAGE GENERATION (Google Gemini LLM)
# ============================================

# Enable/disable AI messages (True/False)
LLM_ENABLE=True

# Your Google Gemini API key
GEMINI_API_KEY=AIzaSyA_your_actual_api_key_here

# Gemini model to use
# Options:
#   - gemini-1.5-flash (RECOMMENDED: fast, cost-effective, great quality)
#   - gemini-1.5-pro (more capable, but slower and more expensive)
LLM_MODEL=gemini-1.5-flash
```

### Doppler Configuration

Store your API key securely in Doppler:

```bash
# In Doppler, create "llm" config section:
doppler secrets set GEMINI_API_KEY="AIzaSyA..." --config prd

# Also set:
doppler secrets set LLM_ENABLE="True" --config prd
doppler secrets set LLM_MODEL="gemini-1.5-flash" --config prd
```

### AWS Secrets Manager

```json
{
  "gemini_api_key": "AIzaSyA...",
  "enable": "True",
  "model": "gemini-1.5-flash"
}
```

Store in secret named by `SECRETS_AWS_LLM_SECRET_NAME`.

### HashiCorp Vault

```bash
vault kv put secret/llm \
  gemini_api_key="AIzaSyA..." \
  enable="True" \
  model="gemini-1.5-flash"
```

Path configured by `SECRETS_VAULT_LLM_SECRET_PATH`.

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

### What AI Receives

The AI is given context about your stream:

**For Stream Start:**
- Streaming platform (Twitch, YouTube, Kick)
- Your username
- Stream title
- Stream URL
- Target social platform (for character limits)
- Instruction to generate exciting, inviting message

**For Stream End:**
- Streaming platform
- Your username  
- Stream title (from when it started)
- Target social platform
- Instruction to generate grateful, warm message

### AI Prompts (Simplified)

**Start Prompt:**
```
Generate an exciting social media post announcing a livestream 
has just started.

Stream: ChiefGYK3D on Twitch
Title: Elden Ring Boss Rush Challenge
Max: 270 characters (excluding URL)

Requirements:
- Enthusiastic and inviting
- 2-4 relevant hashtags
- Make people want to join NOW
- Don't include URL (added automatically)
```

**End Prompt:**
```
Generate a warm social media post announcing a livestream ended.

Stream: ChiefGYK3D on Twitch  
Title: Elden Ring Boss Rush Challenge
Max: 300 characters

Requirements:
- Thank viewers for joining
- Grateful and friendly tone
- 1-3 relevant hashtags
- Encourage them to catch next stream
```

---

## Character Limits

### How Limits Are Enforced

**Bluesky (300 chars):**
```
Generated content: 270 chars max
URL + spacing:      30 chars
─────────────────────────────
Total:             300 chars
```

**Mastodon (500 chars):**
```
Generated content: 470 chars max
URL + spacing:      30 chars
─────────────────────────────
Total:             500 chars
```

**Discord/Matrix (500 chars):**
```
Full 500 chars available for content
(URLs don't count against limit in most Discord clients)
```

### Overflow Protection

If AI generates a message that's too long:

```python
if len(full_message) > max_chars:
    # Truncate content (not URL)
    overflow = len(full_message) - max_chars
    message = message[:-overflow-3] + "..."
    full_message = f"{message}\n\n{url}"
```

---

## Fallback Behavior

AI generation can fail for several reasons. The system automatically falls back to your static messages:

### When Fallback Occurs

1. **LLM_ENABLE=False**: AI disabled, always use static messages
2. **API Key Missing**: No `GEMINI_API_KEY` configured
3. **API Error**: Network issues, rate limits, invalid key
4. **Generation Failure**: AI returns empty/invalid response
5. **Initialization Failed**: Can't connect to Gemini API

### What You'll See

```
⚠ AI generation returned None, using fallback message
```

Or:

```
✗ Failed to generate start message: <error details>, using fallback
```

Then your normal static message from `messages.txt` is used.

### This Means

🔒 **No Downtime**: Your stream announcements still go out even if AI fails
✅ **Graceful Degradation**: Always have a working backup
📝 **Keep Your Static Messages**: Still need them for fallback!

---

## Cost & Rate Limits

### Google Gemini Pricing (as of 2024)

**gemini-1.5-flash** (Recommended):
- **Free Tier**: 15 requests/minute, 1,500 requests/day
- **Paid**: $0.075 per 1M input tokens, $0.30 per 1M output tokens

**gemini-1.5-pro**:
- **Free Tier**: 2 requests/minute, 50 requests/day  
- **Paid**: $1.25 per 1M input tokens, $5.00 per 1M output tokens

### Cost Estimation

**Typical Stream Announcement:**
- Input: ~200 tokens (prompt + context)
- Output: ~100 tokens (generated message)

**With gemini-1.5-flash:**
- Cost per announcement: ~$0.00001 (basically free)
- 1,000 announcements: ~$0.01
- **Annual cost for daily streamer**: ~$4

**Free tier covers most streamers:**
- Stream once/day: ~2 API calls/day (start + end)
- Free tier: 1,500 requests/day
- **Plenty of headroom!** ✅

### Rate Limit Handling

The daemon automatically handles rate limits:

```
✗ AI message generation failed: Rate limit exceeded, using fallback
```

If you hit rate limits frequently:
1. Upgrade to paid tier (very cheap)
2. Or use static messages some of the time
3. Or reduce posting frequency

---

## Examples

### Example 1: Single Stream Start (Twitch)

**Static Message (old way):**
```
🎮 ChiefGYK3D is now live on Twitch! Elden Ring Boss Rush Challenge
https://twitch.tv/chiefgyk3d
```

**AI-Generated (with LLM):**
```
🔥 LIVE NOW! Join ChiefGYK3D for an epic Elden Ring boss rush! 
Watch the carnage unfold as we attempt to beat every boss back-to-back! 
Can we do it? 😤⚔️ #EldenRing #BossRush #TwitchLive

https://twitch.tv/chiefgyk3d
```

---

### Example 2: Stream End (YouTube)

**Static Message:**
```
Thanks for watching! ChiefGYK3D's stream on YouTube has ended.
```

**AI-Generated:**
```
Stream's wrapped! 🎬 Huge thanks to everyone who tuned in for the 
Minecraft build session! Your support means everything! 
Catch the VOD for all the highlights! 💙 #MinecraftLive #ThankYou
```

---

### Example 3: Bluesky (300 char limit)

**AI knows it's Bluesky and generates shorter:**
```
🚀 GO LIVE! ChiefGYK3D tackling Elden Ring bosses NOW! 
Come witness the chaos! 😤 #EldenRing #TwitchLive

https://twitch.tv/chiefgyk3d
```
*(Exactly 150 chars - well under limit)*

---

### Example 4: Mastodon (500 char limit)

**AI uses more space for detailed message:**
```
🎮 The stream just started! ChiefGYK3D is diving deep into 
Elden Ring with an insane boss rush challenge! Every major boss, 
back-to-back, no breaks! Will they conquer the Lands Between or 
will the bosses reign supreme? Only one way to find out! 
Join the adventure right now! 🔥⚔️ 

#EldenRing #BossRush #SoulsLike #TwitchLive #LiveNow

https://twitch.tv/chiefgyk3d
```
*(Uses full 500 chars for maximum engagement)*

---

## Troubleshooting

### AI Not Working

**Check 1: Is LLM enabled?**
```bash
# In .env or Doppler:
LLM_ENABLE=True
```

**Check 2: Valid API key?**
```bash
# Should start with "AIza..."
GEMINI_API_KEY=AIzaSyA...
```

**Check 3: Check logs:**
```
✓ Google Gemini LLM initialized (model: gemini-1.5-flash)
```

If you see:
```
✗ LLM enabled but no GEMINI_API_KEY found
```
→ API key not configured properly

**Check 4: Test API key manually:**
```python
import google.generativeai as genai

genai.configure(api_key="AIzaSyA...")
model = genai.GenerativeModel('gemini-1.5-flash')
response = model.generate_content("Say hello!")
print(response.text)  # Should print "Hello!"
```

---

### Messages Still Static

You'll see in logs:
```
✨ Generated stream start message (285/300 chars)
```

If you **don't** see this, AI isn't being used. Check:

1. `LLM_ENABLE=True` set?
2. API key valid?
3. No errors in logs?
4. Daemon restarted after config change?

---

### API Key Invalid

```
✗ Failed to initialize Gemini: API key not valid. Please pass a valid API key.
```

**Solution:**
1. Go to https://aistudio.google.com/app/apikey
2. Create a NEW API key
3. Update `GEMINI_API_KEY` with new key
4. Restart daemon

---

### Rate Limits Hit

```
✗ AI message generation failed: Rate limit exceeded, using fallback
```

**Free tier limits:**
- gemini-1.5-flash: 15 req/min, 1,500 req/day
- gemini-1.5-pro: 2 req/min, 50 req/day

**Solutions:**
1. **Upgrade to paid tier** (very cheap, ~$4/year for daily streamer)
2. **Use gemini-1.5-flash** (higher free limits)
3. **Reduce check frequency** (increase `SETTINGS_CHECK_INTERVAL`)

---

### Messages Too Short/Long

AI should respect character limits automatically.

If messages are being truncated:
```
✨ Generated stream start message (305/300 chars)  
⚠ Message truncated to fit limit
```

This is **normal** - AI sometimes goes over, system auto-truncates.

If you want **shorter** messages:
- Use Bluesky (300 char limit forces brevity)
- System already optimizes for each platform

If you want **longer** messages:
- Use Mastodon (500 char limit)
- AI will use full space available

---

### Cost Concerns

**Monitor your usage:**
1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Check usage dashboard
3. Set up billing alerts

**For most streamers:**
- Cost is negligible (~$4/year)
- Free tier is MORE than enough
- Only pay if you exceed free tier

**If costs are high:**
- Check daemon isn't running multiple times
- Verify you're using gemini-1.5-flash (not pro)
- Consider using AI only for stream starts (not ends)

---

## Disabling AI Messages

Set in `.env` or Doppler:
```bash
LLM_ENABLE=False
```

System will immediately fallback to static messages from `messages.txt` and `end_messages.txt`.

**No restart needed** - checked every time a stream goes live/offline.

---

## Advanced: Customizing AI Behavior

Want to tweak how AI generates messages? Edit the `AIMessageGenerator` class in `stream-daemon.py`:

### Change Prompt Template

Find around line 2040:
```python
prompt = f"""Generate an exciting, engaging social media post...

Stream Details:
- Platform: {platform_name}
- Streamer: {username}
- Title: {title}

Requirements:
- Maximum {content_max} characters
- Include 2-4 relevant hashtags
- Enthusiastic and inviting tone
- Make people want to join the stream NOW
...
```

### Adjust Hashtag Count

Change `Include 2-4 relevant hashtags` to your preference.

### Change Tone

Modify the tone instructions:
- "Enthusiastic and inviting" → "Professional and informative"
- "Grateful and friendly" → "Casual and fun"

### Use Different Model

In `.env`:
```bash
# More capable but slower/expensive
LLM_MODEL=gemini-1.5-pro

# Faster, cheaper, great quality (default)
LLM_MODEL=gemini-1.5-flash
```

---

## Best Practices

✅ **DO:**
- Use `gemini-1.5-flash` for best cost/performance
- Keep static messages as fallback
- Monitor API usage in Google AI Studio
- Test with a few streams before going live
- Set up billing alerts if using paid tier

❌ **DON'T:**
- Use gemini-1.5-pro unless you need it (costs 10x more)
- Remove static messages (needed for fallback)
- Share your API key publicly
- Commit API key to git

---

## Summary

🎯 **What You Get:**
- Unique, engaging messages for every stream
- Platform-optimized character limits
- Automatic hashtag generation
- Graceful fallback to static messages
- Minimal cost (~$4/year for daily streamers)

🚀 **Quick Setup:**
1. Get Gemini API key from https://aistudio.google.com/app/apikey
2. Set `LLM_ENABLE=True` and `GEMINI_API_KEY=...`
3. Start streaming - watch AI-powered announcements roll out!

📚 **Resources:**
- [Google AI Studio](https://aistudio.google.com/)
- [Gemini API Documentation](https://ai.google.dev/docs)
- [Pricing Details](https://ai.google.dev/pricing)

---

**Questions?** Check the main README or open an issue on GitHub! 🎮✨
