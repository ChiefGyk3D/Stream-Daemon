# LLM Optimization Guide

## Optimizing for Small LLMs (Gemma2, Phi, Llama 3B-4B)

This guide helps you configure Stream-Daemon's AI message generation for optimal performance with smaller language models.

## Configuration Parameters

Add these settings to your configuration file to control AI generation:

```ini
[LLM]
enable = true
provider = ollama  # or gemini

# Model selection
model = gemma3:4b  # or gemma3:4b, phi3:mini, llama3.2:3b

# Ollama connection (if using local models)
ollama_host = http://localhost
ollama_port = 11434

# Generation parameters for better control
temperature = 0.3      # Lower = more focused/consistent (0.0-1.0)
top_p = 0.9           # Nucleus sampling threshold (0.0-1.0)
max_tokens = 150      # Maximum output length

# Retry configuration
max_retries = 3
retry_delay_base = 2
```

## Generation Parameters Explained

### Temperature (0.0 - 1.0)
Controls randomness in output generation:
- **0.0-0.3** (Recommended): Very focused, consistent, follows instructions closely
- **0.4-0.6**: Balanced creativity and structure
- **0.7-1.0**: More creative but may ignore constraints

**For stream messages, use 0.3** to ensure the model follows the strict formatting rules.

### Top P (0.0 - 1.0)
Nucleus sampling - considers only the most likely tokens:
- **0.9** (Recommended): Good balance of quality and variety
- **0.95**: Slightly more varied
- **1.0**: Considers all tokens (less predictable)

### Max Tokens (50 - 200)
Maximum number of tokens to generate:
- **150** (Recommended): Enough for posts with 3 hashtags and URL
- **100**: For very short platforms (Bluesky)
- **200**: For longer platforms (Mastodon)

Too low = truncated messages. Too high = slower generation, higher cost.

## Prompt Engineering Enhancements

The enhanced prompts now use:

### 1. Step-by-Step Instructions
Small LLMs perform better with explicit steps:
```
STEP 1 - CONTENT RULES
STEP 2 - HASHTAG RULES
```

### 2. Few-Shot Examples
The prompts include 3 good examples and 3 bad examples showing:
- ✓ Correct hashtag counts (3 for start, 2 for end)
- ✓ Hashtags from title only
- ✗ Common mistakes to avoid

### 3. Visual Markers
Using checkmarks and X marks helps smaller models understand:
- ✓ = Required/Good
- ✗ = Forbidden/Bad

### 4. Repetition of Critical Rules
Key constraints are repeated multiple times:
- "EXACTLY 3 hashtags" (stated 3 times)
- Character limits (reinforced in multiple places)
- Username exclusion rule (stated in bold and examples)

## Recommended Models

### Ollama (Local/Self-hosted)

| Model | Size | Speed | Quality | Best For |
|-------|------|-------|---------|----------|
| **gemma2:2b** | 1.6GB | ⚡⚡⚡ | ⭐⭐⭐ | CPU-only systems |
| **gemma2:4b** | 2.9GB | ⚡⚡ | ⭐⭐⭐⭐ | **Recommended** |
| **phi3:mini** | 2.3GB | ⚡⚡⚡ | ⭐⭐⭐ | Fast, compact |
| **llama3.2:3b** | 2.0GB | ⚡⚡ | ⭐⭐⭐⭐ | Good reasoning |
| **qwen2.5:3b** | 2.3GB | ⚡⚡ | ⭐⭐⭐⭐ | Excellent instruction following |

**Installation:**
```bash
ollama pull gemma3:4b
```

### Google Gemini (Cloud API)

| Model | Cost | Speed | Quality | Best For |
|-------|------|-------|---------|----------|
| **gemini-2.0-flash-lite** | Free tier | ⚡⚡⚡ | ⭐⭐⭐⭐ | **Recommended** - 30 req/min |
| **gemini-1.5-flash** | $0.075/1M | ⚡⚡ | ⭐⭐⭐⭐⭐ | Higher quality |

## Testing Your Configuration

### 1. Quick Test
Run the prompt improvement test to see if your model follows instructions:
```bash
python tests/test_prompt_improvements.py
```

### 2. Check Generated Messages
Enable debug logging to see full prompts and responses:
```bash
export LOG_LEVEL=DEBUG
python stream-daemon.py
```

### 3. Validate Hashtag Counts
The tests check for:
- Start messages: exactly 3 hashtags
- End messages: exactly 2 hashtags
- No username-derived hashtags
- Character limit compliance

## Troubleshooting

### Problem: Model generates wrong number of hashtags

**Solution 1:** Lower temperature
```ini
temperature = 0.2  # Even more focused
```

**Solution 2:** Try a different model
```bash
# Qwen models are excellent at following instructions
ollama pull qwen2.5:3b
```

**Solution 3:** Reduce max_tokens
```ini
max_tokens = 120  # Forces more concise output
```

### Problem: Model ignores character limits

**Solution:** The code automatically trims messages, but you can:
1. Lower `max_tokens` to force shorter output
2. Use a more instruction-following model (Qwen, Gemma2)
3. Check logs for trimming warnings

### Problem: Model adds generic hashtags (#Gaming, #Live)

**Solution:** Already handled by enhanced prompts, but ensure you're using:
- Latest code with improved prompts
- Temperature ≤ 0.3
- A recent model (Gemma2, Qwen2.5)

### Problem: Model uses username in hashtags

**Solution:** This is caught by the `_validate_hashtags_against_username` guardrail:
- Automatically removes username-derived hashtags
- Check logs for "Removed username-derived hashtag" warnings
- If persistent, the model may need fine-tuning on your use case

## Performance Tips

### For CPU-Only Systems
```ini
model = gemma3:2b
temperature = 0.2
max_tokens = 100
```

### For GPU Systems (NVIDIA/AMD)
```ini
model = gemma3:4b  # or qwen2.5:7b for even better quality
temperature = 0.3
max_tokens = 150
```

### For Cloud API (Gemini)
```ini
provider = gemini
model = gemini-2.0-flash-lite
temperature = 0.3
max_tokens = 150
```
Rate limits: 30 requests/min (free tier), perfect for multi-stream setups.

## Advanced: Prompt Customization

If you want to further customize prompts for your specific use case, edit these methods in `stream_daemon/ai/generator.py`:

- `_prompt_stream_start()`: Start message template
- `_prompt_stream_end()`: End message template

Key principles for small LLMs:
1. **Be explicit**: Don't assume the model knows implicit rules
2. **Use examples**: Show don't tell (3+ examples)
3. **Repeat critical constraints**: State important rules multiple times
4. **Use formatting**: Visual markers (✓/✗), steps, bold text
5. **Keep it focused**: One clear task per prompt

## Monitoring

Watch these log messages:
- `✓ Ollama LLM initialized` - Successful connection
- `✨ Generated stream start message` - Success with char count
- `⚠ AI generated message too long, trimming` - Model exceeded limit
- `⚠ Removed username-derived hashtag` - Guardrail activated

## See Also

- [AI Messages Feature](./ai-messages.md) - Overview of AI integration
- [Ollama Migration Guide](./ollama-migration.md) - Switching from Gemini to Ollama
- [Testing Guide](../development/testing.md) - Running AI tests
