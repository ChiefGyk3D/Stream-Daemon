# Qwen3 Thinking Mode Support

> **Status**: Experimental (a.k.a. "we built it but we're not sure why")  
> **Added**: v3.0.0  
> **Author**: ChiefGyk3D

## Overview

So here's the thing about Qwen3 models - they decided to add a "thinking mode" where the AI shows its work like a nervous kid at a math competition. The model outputs all its reasoning in a separate `thinking` field before giving you the actual answer. 

This is great if you're solving differential equations or writing a PhD thesis. For generating a fucking tweet about your Twitch stream? It's like using a Formula 1 car to go get milk.

But hey, we built support for it anyway because that's what we do. We solve problems that shouldn't exist in the first place.

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

Notice what happened here:
- `content` is **empty** - the thing we actually wanted
- All the reasoning is in `thinking` - a verbose inner monologue nobody asked for
- The model ran out of tokens (`done_reason: "length"`) while still *thinking about thinking*

It's like asking someone for directions and they spend 10 minutes explaining HOW they're going to give you directions, then forget to actually tell you where to go.

## The Solution

Stream Daemon now supports Qwen3's thinking mode with two new configuration options. Because apparently we need to configure our AI to stop overthinking. We've come full circle - humans teaching machines to be less neurotic.

### Configuration

```env
# Enable thinking mode extraction for Qwen3 models
# Translation: "Please dig through the AI's diary to find the actual answer"
LLM_ENABLE_THINKING_MODE=True

# Multiply token limit to allow for thinking + response
# 150 tokens * 4 = 600 total tokens
# Because the AI needs 450 tokens to THINK about writing a 150 character post
LLM_THINKING_TOKEN_MULTIPLIER=4.0
```

### How It Works

1. **Token Multiplier**: When thinking mode is enabled, `max_tokens` is multiplied by `thinking_token_multiplier`. This gives the model enough tokens to finish its existential crisis AND generate the response.

2. **Content Extraction**: If the `content` field is empty but `thinking` has content, Stream Daemon attempts to extract the final answer using pattern matching:
   - Looks for quoted text (lines starting with `>`)
   - Searches for markers like "Final post:", "Here's the post:", etc.
   - Finds lines containing hashtags that match post length criteria

3. **Graceful Fallback**: If extraction fails (because parsing AI stream-of-consciousness is about as reliable as a weather forecast), Stream Daemon falls back to standard messages.

## Recommended Settings for Qwen3

If you insist on using Qwen3 (and I respect that kind of stubborn dedication to making things harder than they need to be):

```env
# Enable Qwen3 support
LLM_MODEL=qwen3:4b
LLM_ENABLE_THINKING_MODE=True
LLM_THINKING_TOKEN_MULTIPLIER=5.0

# Base tokens - will be multiplied (150 * 5 = 750)
LLM_MAX_TOKENS=150

# Lower temperature for more predictable thinking
# Higher values = more creative thinking = longer thinking = empty responses
LLM_TEMPERATURE=0.25
```

---

## Available Models on ChiefGyk3D's Ollama Servers

Here's the actual model inventory. Yes, we have two GPUs running Ollama because apparently one wasn't enough to satisfy our need to make robots write tweets.

### RTX 5060 Ti (Port 11434) - The Big Gun

The 16GB beast. This is where the premium models live.

| Model | Size | Use Case | Notes |
|-------|------|----------|-------|
| **gemma3:12b** | 7.58 GB | ✅ **RECOMMENDED** | Blazing fast (~1.3s), excellent quality. No thinking mode bullshit. |
| **qwen3:14b** | 8.63 GB | ⚠️ Experimental | Has thinking mode. Great benchmarks, annoying implementation. |
| **qwen2.5:14b** | 8.37 GB | ✅ Good | Reliable, no thinking mode, slower than Gemma3 |
| **nous-hermes2:10.7b** | 5.65 GB | Good for creative | Fine-tuned for creative tasks, might get too creative |
| **solar:10.7b** | 5.65 GB | Good general | Korean model, solid performance |
| **llama3.1:8b** | 4.58 GB | Good general | Meta's workhorse, dependable |
| **mistral:7b** | 4.07 GB | Fast | French engineering, oui oui |
| **openhermes:latest** | 3.82 GB | Versatile | Fine-tuned Mistral, good instruction following |
| **deepseek-coder:6.7b** | 3.56 GB | Code only | For when you want the AI to write code, not tweets |

### RTX 3050 (Port 11435) - The Scrappy Underdog

The 8GB card. Smaller models, faster responses, less pretentious.

| Model | Size | Use Case | Notes |
|-------|------|----------|-------|
| **gemma3:4b** | 3.10 GB | ✅ **FAST & GOOD** | ~1 second responses. Perfect for stream announcements. |
| **qwen3:4b** | 2.32 GB | ⚠️ Experimental | Thinking mode. Rivals 72B benchmarks somehow. Still annoying. |
| **qwen2.5:7b** | 4.36 GB | ✅ Good | Sweet spot for quality/speed, ~11s response |
| **neural-chat:7b** | 3.82 GB | Conversational | Intel's model, good for chat-style prompts |
| **zephyr:7b** | 3.82 GB | Good | HuggingFace's direct preference optimization |
| **phi3:mini** | 2.02 GB | Fast | Microsoft's tiny but mighty model |
| **llama3.2:3b** | 1.88 GB | Very fast | Meta's small model, quick responses |

---

## Model Comparison for Stream Daemon

Here's the truth nobody wants to hear: **for writing "Going live on Twitch!" posts, you don't need a 14 billion parameter model**. It's like buying a commercial kitchen to make toast.

| Model | Thinking Mode | Speed | Quality | Recommendation |
|-------|---------------|-------|---------|----------------|
| gemma3:4b | No | ~1.0s ⚡ | Good | ✅ **Best Value** |
| gemma3:12b | No | ~1.3s ⚡ | Excellent | ✅ **Best Overall** |
| qwen2.5:7b | No | ~11s | Very Good | ✅ Solid choice |
| qwen2.5:14b | No | ~11s | Excellent | ✅ Premium quality |
| qwen3:4b | Yes | ~6s+ | Potentially Excellent | ⚠️ Requires thinking mode config |
| qwen3:14b | Yes | ~10s+ | Premium | ⚠️ Requires thinking mode config |
| llama3.1:8b | No | ~8s | Good | ✅ Reliable |
| mistral:7b | No | ~7s | Good | ✅ Solid |

## Why We Recommend Gemma3 Over Qwen3

For Stream Daemon's use case (generating short social media posts), **Gemma3 models are superior**:

1. **Speed**: Gemma3:4b responds in ~1 second vs 6+ seconds for Qwen3. That's the difference between "posted while going live" and "posted after you've already been streaming for 5 minutes."

2. **Simplicity**: No thinking mode overhead - direct response. The model doesn't need to philosophize about hashtags.

3. **Clean Output**: Single post, no multiple options. It gives you what you asked for, not a menu of possibilities like some indecisive restaurant.

4. **Token Efficiency**: Uses fewer tokens for the same output. Less mental gymnastics, more results.

### When to Use Qwen3

Qwen3 may be worth using if:
- You want maximum reasoning capability for complex stream titles (do those exist?)
- You have ample GPU VRAM and don't mind slower responses
- You're experimenting with the thinking mode feature because you enjoy suffering
- Future updates improve thinking mode handling
- You want bragging rights about using a "reasoning model" to write tweets

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

*Note: Qwen3 tests with default settings failed due to thinking mode. With `LLM_ENABLE_THINKING_MODE=True` and increased tokens, results may vary. Or they might not. We're dealing with AI here - predictability is not guaranteed.*

---

## Troubleshooting

### Problem: Empty responses from Qwen3

The AI thought so hard about what to say that it forgot to actually say anything. Classic.

**Solution**: Enable thinking mode and increase token multiplier:

```env
LLM_ENABLE_THINKING_MODE=True
LLM_THINKING_TOKEN_MULTIPLIER=6.0
```

### Problem: Qwen3 still running out of tokens

The AI's internal monologue is longer than a Dostoevsky novel.

**Solution**: Increase base tokens:

```env
LLM_MAX_TOKENS=200
LLM_THINKING_TOKEN_MULTIPLIER=5.0
# Total: 200 * 5 = 1000 tokens
# That's 1000 tokens for a 280 character tweet. Let that sink in.
```

### Problem: Qwen3 output is slow

**Solution**: Switch to Gemma3. Seriously. Gemma3:4b is 6x faster with comparable quality for this use case. Sometimes the answer to "how do I make this work?" is "use something else."

### Problem: Model not found on Ollama server

Check which port your model is on:
- **RTX 5060 Ti models**: Port 11434
- **RTX 3050 models**: Port 11435

```env
# For gemma3:12b (on the 5060 Ti)
LLM_OLLAMA_HOST=http://192.168.214.10
LLM_OLLAMA_PORT=11434

# For gemma3:4b (on the 3050)
LLM_OLLAMA_HOST=http://192.168.214.10
LLM_OLLAMA_PORT=11435
```

---

## Technical Details

For those who want to understand the sausage-making process:

### Extraction Patterns

The `_extract_from_thinking()` method looks for:

1. **Quoted text**: Lines starting with `>` - because sometimes the AI "quotes" its own answer
2. **Explicit markers**: "final post:", "here's the post:", "announcement:", etc. - teaching robots to label their work
3. **Hashtag detection**: Lines with `#` that are post-length (30-300 chars) - if it looks like a duck and has hashtags like a duck...

### Response Structure Handling

```python
# Standard Ollama response (normal models)
{"message": {"content": "The actual post"}}

# Qwen3 thinking response (thinking models)
{"message": {"content": "", "thinking": "Reasoning... Final post: ..."}}
```

Stream Daemon handles both structures automatically when thinking mode is enabled. It's like having a translator for AI that can't just give you a straight answer.

---

## Multi-GPU Setup with FrankenLLM

Running multiple Ollama instances on different GPUs? That's what [FrankenLLM](https://github.com/ChiefGyk3D/FrankenLLM) is for.

```bash
# Port 11434 = GPU 0 (RTX 5060 Ti) - Big models
# Port 11435 = GPU 1 (RTX 3050) - Fast models
```

This way you can:
- Run the fast 4B model on the 3050 for quick responses
- Keep the premium 12B model on the 5060 Ti for quality
- Pretend you're running a data center from your home office

---

## Future Improvements

- [ ] Better heuristics for extracting posts from thinking (teaching robots to find their own answers)
- [ ] Option to disable thinking mode in Ollama API (if Ollama ever supports it)
- [ ] Cached prompts for faster Qwen3 responses (if we can convince it to remember things)
- [ ] Automatic model detection for thinking mode (so you don't have to read documentation)
- [ ] A simpler world where AI just answers questions without philosophizing about it first

---

## The Bottom Line

Use **gemma3:12b** (or gemma3:4b if you want speed). They're fast, they're reliable, and they don't need therapy to write a tweet.

If you want to experiment with Qwen3, we support it. But don't say we didn't warn you about the thinking mode.

As George Carlin might say: "We've managed to create artificial intelligence that overthinks things just like humans do. Great. Now we have TWO species that can't make a simple decision without an existential crisis."
