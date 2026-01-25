# Qwen3 Thinking Mode Support

> **Status**: Experimental  
> **Added**: v2.x.x  
> **Author**: ChiefGyk3D

## Overview

Qwen3 models (qwen3:4b, qwen3:8b, qwen3:14b, etc.) introduce a "thinking mode" where the model outputs its reasoning process in a separate `thinking` field before generating the final response. This is great for complex reasoning tasks but creates challenges for simple tasks like generating social media posts.

## The Problem

When you ask Qwen3 to generate a stream announcement, you get a response like this:

```json
{
  "message": {
    "content": "",
    "thinking": "We are generating a Twitch live stream announcement for the user \"chiefgyk3d\"\n Stream title: \"My AI tools have been upgraded! Lets build a firewall | Cybersecurity Rants & Linux Gaming|1-21-26\"\n We must be under 280 characters, include 1-2 relevant hashtags...\n\n Steps:\n 1. Avoid repeating the title verbatim...\n 2. The stream is on Twitch...\n 3. The date is 1-21-26..."
  },
  "done": true,
  "done_reason": "length"
}
```

Notice:
- `content` is **empty**
- All the reasoning is in `thinking`
- The model ran out of tokens (`done_reason: "length"`) while still thinking

## The Solution

Stream Daemon now supports Qwen3's thinking mode with two new configuration options:

### Configuration

```env
# Enable thinking mode extraction for Qwen3 models
LLM_ENABLE_THINKING_MODE=True

# Multiply token limit to allow for thinking + response
# 150 tokens * 4 = 600 total tokens
LLM_THINKING_TOKEN_MULTIPLIER=4.0
```

### How It Works

1. **Token Multiplier**: When thinking mode is enabled, `max_tokens` is multiplied by `thinking_token_multiplier`. This gives the model enough tokens to complete its reasoning AND generate the response.

2. **Content Extraction**: If the `content` field is empty but `thinking` has content, Stream Daemon attempts to extract the final answer using pattern matching:
   - Looks for quoted text (lines starting with `>`)
   - Searches for markers like "Final post:", "Here's the post:", etc.
   - Finds lines containing hashtags that match post length criteria

3. **Graceful Fallback**: If extraction fails, Stream Daemon falls back to standard messages.

## Recommended Settings for Qwen3

```env
# Enable Qwen3 support
LLM_MODEL=qwen3:4b
LLM_ENABLE_THINKING_MODE=True
LLM_THINKING_TOKEN_MULTIPLIER=5.0

# Base tokens - will be multiplied (150 * 5 = 750)
LLM_MAX_TOKENS=150

# Lower temperature for more predictable thinking
LLM_TEMPERATURE=0.25
```

## Model Comparison

| Model | Thinking Mode | Speed | Quality | Recommendation |
|-------|---------------|-------|---------|----------------|
| gemma3:4b | No | ~1.0s ⚡ | Good | ✅ **Recommended** |
| gemma3:12b | No | ~1.3s ⚡ | Excellent | ✅ **Best Overall** |
| qwen2.5:7b | No | ~11s | Very Good | ✅ Good alternative |
| qwen3:4b | Yes | ~6s+ | Potentially Excellent | ⚠️ Requires config |
| qwen3:14b | Yes | ~10s+ | Premium | ⚠️ Requires config |

## Why We Recommend Gemma3 Over Qwen3

For Stream Daemon's use case (generating short social media posts), **Gemma3 models are superior**:

1. **Speed**: Gemma3:4b responds in ~1 second vs 6+ seconds for Qwen3
2. **Simplicity**: No thinking mode overhead - direct response
3. **Clean Output**: Single post, no multiple options
4. **Token Efficiency**: Uses fewer tokens for the same output

### When to Use Qwen3

Qwen3 may be worth using if:
- You want maximum reasoning capability for complex stream titles
- You have ample GPU VRAM and don't mind slower responses
- You're experimenting with the thinking mode feature
- Future updates improve thinking mode handling

## Benchmark Results (January 2026)

Test prompt: Stream title "My AI tools have been upgraded! Let's build a firewall | Cybersecurity Rants & Linux Gaming"

| Model | GPU | Time | Output Quality |
|-------|-----|------|----------------|
| gemma3:4b | RTX 3050 | 1.0s | Good, clean single post |
| gemma3:12b | RTX 5060 Ti | 1.3s | Excellent, polished |
| qwen2.5:7b | RTX 3050 | 11.5s | Good |
| qwen2.5:14b | RTX 5060 Ti | 11.0s | Very good |
| qwen3:4b | RTX 3050 | N/A | Thinking mode consumed all tokens |
| qwen3:14b | RTX 5060 Ti | N/A | Thinking mode consumed all tokens |

*Note: Qwen3 tests with default settings failed due to thinking mode. With `LLM_ENABLE_THINKING_MODE=True` and increased tokens, results may vary.*

## Troubleshooting

### Problem: Empty responses from Qwen3

**Solution**: Enable thinking mode and increase token multiplier:

```env
LLM_ENABLE_THINKING_MODE=True
LLM_THINKING_TOKEN_MULTIPLIER=6.0
```

### Problem: Qwen3 still running out of tokens

**Solution**: Increase base tokens:

```env
LLM_MAX_TOKENS=200
LLM_THINKING_TOKEN_MULTIPLIER=5.0
# Total: 200 * 5 = 1000 tokens
```

### Problem: Qwen3 output is slow

**Solution**: Consider switching to Gemma3 for stream announcements. Gemma3:4b is 6x faster with comparable quality for this use case.

## Technical Details

### Extraction Patterns

The `_extract_from_thinking()` method looks for:

1. **Quoted text**: Lines starting with `>`
2. **Explicit markers**: "final post:", "here's the post:", "announcement:", etc.
3. **Hashtag detection**: Lines with `#` that are post-length (30-300 chars)

### Response Structure Handling

```python
# Standard Ollama response
{"message": {"content": "The actual post"}}

# Qwen3 thinking response
{"message": {"content": "", "thinking": "Reasoning... Final post: ..."}}
```

Stream Daemon handles both structures automatically when thinking mode is enabled.

## Future Improvements

- [ ] Better heuristics for extracting posts from thinking
- [ ] Option to disable thinking mode in Ollama API (if supported)
- [ ] Cached prompts for faster Qwen3 responses
- [ ] Automatic model detection for thinking mode
