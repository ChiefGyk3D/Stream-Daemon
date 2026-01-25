# LLM Guardrails & Quality Checks

## Overview

Because even AI needs adult supervision.

**Or: "How I Learned to Stop Trusting the Robot and Love the Validation"**

### IMPORTANT: What George Carlin Jokes Are Doing Here

Let's be crystal fucking clear about something:

**The AI does NOT generate messages in George Carlin's voice.** 

Your stream announcements will be normal, professional posts like:
- "Playing Valorant ranked! Come join the climb 🎮 #Valorant #Competitive #FPS"
- "Thanks for watching the stream! See you next time #Valorant #GG"

They will NOT be:
- "Streaming some Valorant shit, come watch if you give a fuck #Valorant #Gaming"
- "Stream's over. Thanks for putting up with my bullshit for 3 hours."

The profanity and Carlin-esque humor is in the **CODE COMMENTS** and **DOCUMENTATION**.
Because if you're going to write software, you might as well be honest about what you're doing:
Teaching robots to fake enthusiasm about video games on the internet.

This document explains the **post-generation quality validation** system that catches when small LLMs fuck up and:
- Use the wrong number of hashtags
- Include forbidden clickbait words we explicitly told them not to use
- Accidentally include URLs in the content
- Hallucinate details that weren't in the stream title

George Carlin would have a field day: "We built robots that can write, but we still need to teach them how to count to three."

## Guardrail Types

### 1. Username Hashtag Removal (Pre-existing)
**Purpose**: Prevents AI from using parts of the username as hashtags.

**Example**:
- Username: `CoolStreamer99`
- Bad: `#Cool #Streamer #Gaming`
- Good: `#Minecraft #Creative #Building`

**Implementation**: `_validate_hashtags_against_username()` tokenizes the username and removes any hashtags that match.

### 2. Hashtag Count Validation (NEW)
**Purpose**: Ensures exactly the right number of hashtags are used.

**Rules**:
- **Start messages**: Exactly 3 hashtags
- **End messages**: Exactly 2 hashtags

**Why**: Small LLMs struggle with counting. Without this, you get anywhere from 1-6 hashtags.

Let that sink in. A computer. That can do billions of calculations per second. Can't consistently count to three. 

Your iPhone can render photorealistic 3D graphics, simulate physics, and predict the weather.
But asking it for exactly 3 hashtags? "Best I can do is somewhere between 1 and 6, chief."

Fucking magnificent.

**Example Failures Caught**:
```
❌ "Playing Valorant! #Valorant #Competitive" (only 2, needs 3)
❌ "Playing Valorant! #Val #Comp #FPS #Gaming" (4, needs 3)
✅ "Playing Valorant! #Valorant #Competitive #FPS" (exactly 3)
```

### 3. Forbidden Word Detection (NEW)
**Purpose**: Catches when AI ignores our prompt and uses clickbait/cringe words.

**Forbidden Words List**:
- insane, epic, crazy, smash, unmissable
- incredible, amazing, lit, fire, legendary
- mind-blowing, jaw-dropping, unbelievable

**Why**: We explicitly tell the AI not to use these. If it does anyway, we retry with stricter instructions.

**Example Failures Caught**:
```
❌ "This is going to be INSANE! #Valorant #Competitive #FPS"
❌ "Epic gameplay incoming! #Valorant #Ranked #FPS"
✅ "Ranked grind time! Let's climb together #Valorant #Competitive #FPS"
```

### 4. URL Contamination Check (NEW)
**Purpose**: Ensures URLs aren't accidentally included in message content.

**Why**: URLs are added separately after generation. If the AI includes them, formatting breaks.

**Example Failures Caught**:
```
❌ "Playing Valorant! https://twitch.tv/user #Valorant #Ranked #FPS"
✅ "Playing Valorant! #Valorant #Ranked #FPS"
     (URL added after: "...\n\nhttps://twitch.tv/user")
```

### 5. Hallucination Detection (NEW)
**Purpose**: Catches when AI invents details not in the stream title.

**Common Hallucinations**:
- "drops enabled"
- "giveaway"
- "tonight at 8pm" / "starting at 7"
- "VOD coming soon"
- "200 viewers"
- "raided someone"
- "special guest"
- "new video"

**Why**: Small LLMs sometimes "remember" patterns from training data and insert them even when not relevant.

**Example Failures Caught**:
```
Title: "Valorant Ranked"
❌ "Playing Valorant with drops enabled! #Valorant #Ranked #FPS"
❌ "Giveaway stream tonight! #Valorant #Ranked #FPS"
✅ "Ranked grind time! #Valorant #Ranked #FPS"
```

### 6. Message Deduplication (NEW - Configurable)
**Purpose**: Prevents identical or very similar messages across multiple announcements.

**Configuration**:
```bash
LLM_ENABLE_DEDUPLICATION=True  # Enable/disable
LLM_DEDUP_CACHE_SIZE=20        # How many messages to remember
```

**How it works**:
- Caches last N messages (default: 20)
- Normalizes messages (removes hashtags, emojis, punctuation)
- Calculates word overlap similarity
- >80% similar = considered duplicate
- Triggers retry if duplicate detected

**Why**: When streaming to multiple platforms (Twitch + YouTube + Kick), you don't want the same exact announcement posted 3 times.

**Example**:
```
First announcement: "Time for some Valorant ranked! Let's climb #Valorant #Ranked #FPS"
Duplicate (rejected): "Time for some Valorant ranked! Let's climb #Valorant #Competitive #Ranked"
Different (accepted): "Competitive Valorant grind time! Join me #Valorant #Ranked #FPS"
```

**George says**: "Because nobody wants to read the same fucking announcement 5 times. Although to be fair, humans already do this manually."

### 7. Emoji Count Limits (NEW - Configurable)
**Purpose**: Prevents emoji spam in generated messages.

**Configuration**:
```bash
LLM_MAX_EMOJI_COUNT=1  # 0-10 allowed
```

**Why**: Too many emojis = looks like a teenager's Instagram post. Too few = boring corporate speak. Sweet spot: 0-1 emoji.

**Example Failures Caught**:
```
Max emoji: 1
❌ "Playing Valorant! 🎮🔥💪🎯 #Valorant #Ranked #FPS" (4 emojis)
✅ "Playing Valorant! Let's go 🎮 #Valorant #Ranked #FPS" (1 emoji)
✅ "Playing Valorant! #Valorant #Ranked #FPS" (0 emojis, also fine)
```

**George says**: "Too many emojis = looks like you're 12. We're literally teaching robots not to spam emojis. Living the dream."

### 8. Profanity Filter (NEW - Configurable)
**Purpose**: Blocks profanity in AI-generated messages (while keeping Carlin's code commentary).

**Configuration**:
```bash
LLM_ENABLE_PROFANITY_FILTER=False  # Default: disabled
LLM_PROFANITY_SEVERITY=moderate    # mild, moderate, severe
```

**Severity Levels**:
- **mild**: Blocks hard profanity (fuck, shit, etc.)
- **moderate**: + sexual references, slurs
- **severe**: + mild profanity (damn, hell, crap)

**Why**: You might not want the AI dropping F-bombs about your Minecraft stream. Note: This only affects GENERATED content, not our beautiful Carlin commentary.

**George says**: "'You can't say fuck on television!' - George Carlin, probably rolling in his grave that we're now censoring robots too."

### 9. Quality Scoring System (NEW - Configurable)
**Purpose**: Scores messages 1-10 and retries if quality is too low.

**Configuration**:
```bash
LLM_ENABLE_QUALITY_SCORING=False  # Default: disabled (for picky users)
LLM_MIN_QUALITY_SCORE=6           # Minimum acceptable score
```

**Scoring Criteria**:
- **10**: Perfect (natural, engaging, unique)
- **7-9**: Good (clear, interesting)
- **4-6**: Mediocre (generic, boring)
- **1-3**: Bad (very generic, poor grammar, wrong info)

**Deductions**:
- Generic phrases (come hang out, let's go, etc.): -2 points each
- Too short (<5 words): -3 points
- Too long (>25 words): -2 points
- Repeated words (>30%): -2 points
- Doesn't reference title: -3 points
- Lacks personality (no !, ?, emoji): -1 point

**Example**:
```
Message: "come hang out let's go join me stream" 
Score: 3/10 (too many generic phrases, very short, no hashtags)
Action: ⚠ Retry with stricter prompt

Message: "Competitive Valorant ranked! Let's climb together 🎮 #Valorant #Ranked #FPS"
Score: 8/10 (clear, engaging, good length, references game)
Action: ✅ Accept
```

**George says**: "We're literally grading the AI's homework. 'Sorry robot, you get a C-. Try harder next time.' This is what we've become."

### 10. Platform-Specific Validation (NEW - Configurable)
**Purpose**: Validates platform-specific formatting rules.

**Configuration**:
```bash
LLM_ENABLE_PLATFORM_VALIDATION=True  # Default: enabled
```

**Platform Rules**:

**Discord**:
- Checks for malformed mentions (e.g., `@123>` without `<`)
- Validates markdown pairing (`**`, `__`, `*`)
- Ensures embed-safe formatting

**Bluesky**:
- Validates AT Protocol handle format (`@user.domain`)
- Checks for URLs in content (should be separate for facets/link cards)
- Ensures proper "facet" structure

**Mastodon**:
- Checks for HTML entities (should be plain text)
- Validates CW/visibility if configured

**Example Failures Caught**:
```
Discord: "Check @123> for updates" → ❌ Malformed mention
Discord: "**bold text* #Valorant" → ❌ Unmatched markdown

Bluesky: "Follow @username #Val" → ❌ Needs .domain (@username.bsky.social)
Bluesky: "Stream https://kick.com #Val" → ❌ URL should be added separately

Mastodon: "Stream &nbsp; time!" → ❌ HTML entity detected
```

**George says**: "Each social media platform is a special fucking snowflake with its own rules. Discord wants mentions just so. Bluesky has its fancy 'facets' nonsense. 'Just post some text' was too simple. Had to complicate it."

### 11. Character Limit Enforcement (Pre-existing)
**Purpose**: Ensures messages fit within platform limits.

**Limits**:
- Bluesky: 300 chars total (240 content + URL)
- Mastodon: 500 chars
- Discord: 2000 chars
- Matrix: 500 chars (default)

**Implementation**: Messages are trimmed at word boundaries to avoid cutting hashtags.

## Auto-Retry System

When validation fails, the system **automatically retries once** with a stricter prompt.

### Retry Flow

```
1. Generate message with normal prompt
2. Validate quality
3. If validation fails:
   - Log issues: "⚠ Generated message has quality issues: Wrong hashtag count: 2 (expected 3)"
   - Retry with strict_mode=True
   - Validate retry attempt
4. If retry succeeds:
   - Use new message
   - Log: "✅ Retry produced valid message"
5. If retry fails:
   - Use original message (better than nothing)
   - Log: "⚠ Retry still has issues, using original"
```

### Strict Mode Prompt

When `strict_mode=True`, the prompt is prefixed with:

```
⚠️ CRITICAL: Previous attempt violated rules. FOLLOW INSTRUCTIONS EXACTLY. ⚠️
```

This gives the LLM extra context that it needs to pay more attention.

## Usage Examples

### Normal Message (Passes)

```python
# Input
platform_name = "Twitch"
username = "CoolStreamer99"
title = "Valorant Competitive"
url = "https://twitch.tv/coolstreamer99"

# Generated message
"Ranked grind time! Let's climb together #Valorant #Competitive #FPS"

# Validation
✅ 3 hashtags (correct)
✅ No forbidden words
✅ No URL in content
✅ No hallucinations detected

# Final output
"Ranked grind time! Let's climb together #Valorant #Competitive #FPS\n\nhttps://twitch.tv/coolstreamer99"
```

### Failed Message (Auto-Retried)

```python
# Input (same as above)

# First attempt
"Epic Valorant stream! Come watch the INSANE plays! #Valorant #Competitive"

# Validation
❌ 2 hashtags (expected 3)
❌ Forbidden words: epic, insane

# Auto-retry with strict mode
"Competitive Valorant ranked! Join me for some games #Valorant #Competitive #Ranked"

# Validation (retry)
✅ 3 hashtags (correct)
✅ No forbidden words
✅ Passes all checks

# Final output (using retry)
"Competitive Valorant ranked! Join me for some games #Valorant #Competitive #Ranked\n\nhttps://twitch.tv/coolstreamer99"
```

## Testing

Tests are located in `tests/test_llm_quality_checks.py`.

**Run tests**:
```bash
pytest tests/test_llm_quality_checks.py -v
```

**Test coverage**:
- ✅ Hashtag extraction
- ✅ Hashtag count validation
- ✅ Forbidden word detection
- ✅ URL contamination check
- ✅ Hallucination detection
- ✅ Multiple issues reporting
- ✅ Case-insensitive matching
- ✅ Edge cases

## Configuration

No additional configuration needed. All guardrails are **enabled by default** when using AI message generation.

To disable AI generation entirely:
```bash
# .env or environment
LLM_PROVIDER=none
```

This will fall back to manual messages from `messages.txt` and `end_messages.txt`.

## Logging

Validation results are logged with clear indicators:

```
# Success
✨ Generated stream start message (234 chars content + URL = 285/300 total)

# Warning (issues found, retrying)
⚠ Generated message has quality issues: Wrong hashtag count: 2 (expected 3), Contains forbidden words: epic, insane
🔄 Retrying with stricter prompt...
✅ Retry produced valid message

# Warning (retry also failed)
⚠ Retry still has issues: Wrong hashtag count: 4 (expected 3), using original

# Error (generation failed completely)
✗ Failed to generate start message: Connection timeout
```

## Performance Impact

**Minimal**: Validation adds ~1ms per message.

**Retry overhead**: If validation fails (~5-10% of cases), one additional API call is made (typically 1-3 seconds for Ollama, 0.5-1 second for Gemini).

**Trade-off**: Slightly longer generation time (when retry needed) for significantly better quality.

## When Guardrails Activate

Based on real-world testing with small LLMs (2B-4B params):

- **Hashtag count issues**: ~8% of generations
- **Forbidden words**: ~3% of generations
- **Hallucinations**: ~1-2% of generations
- **URL contamination**: <1% of generations

**Total retry rate**: ~10-12% of messages trigger auto-retry.

**Retry success rate**: ~70% of retries produce valid messages.

## Best Practices

1. **Use generation parameters** (see [llm-parameters.md](../configuration/llm-parameters.md)):
   - `LLM_TEMPERATURE=0.3` (lower = more consistent)
   - `LLM_TOP_P=0.9` (nucleus sampling)
   - `LLM_MAX_TOKENS=150` (prevents rambling)

2. **Monitor logs** for frequent validation failures:
   ```bash
   # Check for quality issues
   grep "quality issues" /var/log/stream-daemon/stream-daemon.log
   ```

3. **Test with your specific titles**:
   - Some game names trigger more issues than others
   - Generic titles ("Just Chatting") are harder for small LLMs

4. **Consider larger models** if issues persist:
   - 7B+ params have much better instruction following
   - Gemini Flash Lite (cloud) is very reliable

## Limitations

These guardrails are **post-generation checks**, not perfect prevention:

- **Can't fix everything**: Some issues are unfixable without regenerating (which we do via retry)
- **Tone/style issues**: Can't validate if message sounds "genuine" or "engaging"
- **Context appropriateness**: Can't know if message is appropriate for the actual stream content
- **Language/grammar**: No spelling or grammar checking

For maximum quality, consider:
- Using larger models (7B+)
- Manual review of messages
- Custom messages for important streams
- Cloud LLMs (Gemini) for critical announcements

## The Bigger Picture (A Carlin Rant)

Let's step back and appreciate the absurdity of what we've built here:

We created **artificial intelligence** - machines that can understand language, generate text,
and communicate with humans. This is science fiction shit. This is Star Trek.

And what are we using it for? To announce when someone starts playing Minecraft.

Then, because the AI isn't quite good enough at pretending to be excited about Minecraft,
we built ELEVEN DIFFERENT SYSTEMS to check its work:
- Count the hashtags (can you count to three, robot?)
- Check for forbidden words (don't say EPIC!)
- Verify it didn't make shit up (no, there's no giveaway)
- Make sure it's not using too many emojis (you're not 12)
- Grade its quality (C+, try harder)
- Validate platform-specific bullshit (because nothing can be simple)

We've built an artificial intelligence babysitter. An AI nanny. A robot chaperone.

**And it's all so you don't have to manually tweet "going live" every time you stream.**

This is either the pinnacle of human achievement or proof that we've lost the fucking plot.
I honestly can't tell anymore.

But hey, at least the code comments are funny.

---

*"We created machines that can think, but we still need to teach them not to be assholes."*  
*- The Ghost of George Carlin, somewhere laughing his spectral ass off*

## Summary

The LLM guardrail system provides **automatic quality enforcement** with:

✅ **Post-generation validation** - Catches common AI mistakes  
✅ **Auto-retry with strict mode** - Second chance for better output  
✅ **Comprehensive logging** - Clear visibility into issues  
✅ **Minimal performance impact** - <1ms validation, ~10% retry rate  
✅ **No configuration needed** - Works out of the box  

Combined with enhanced prompts (see [llm-optimization.md](llm-optimization.md)) and generation parameters (see [../configuration/llm-parameters.md](../configuration/llm-parameters.md)), this creates a robust system for reliable AI-generated stream announcements.

## See Also

- [LLM Model Recommendations](llm-model-recommendations.md) - Choose the right model for your hardware
- [LLM Optimization](llm-optimization.md) - Fine-tune your generation parameters
- [AI Messages](ai-messages.md) - The main AI messaging guide
- [FrankenLLM](https://github.com/ChiefGyk3D/FrankenLLM) - Multi-GPU setup for the mad scientists among us

---

*"We created machines that can think, but we still need to teach them not to be assholes."* - The Ghost of George Carlin
