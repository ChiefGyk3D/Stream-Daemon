# LLM Generation Parameters

Quick reference for configuring AI message generation parameters in Stream-Daemon.

## Configuration File (.env)

```ini
# Enable AI-generated messages
LLM_ENABLE=true

# Choose provider
LLM_PROVIDER=ollama  # or 'gemini'

# Model selection
LLM_MODEL=gemma3:4b  # Ollama: gemma3:4b, qwen2.5:3b, phi3:mini
                     # Gemini: gemini-2.0-flash-lite, gemini-1.5-flash

# Ollama connection (if provider=ollama)
LLM_OLLAMA_HOST=http://localhost
LLM_OLLAMA_PORT=11434

# Generation Parameters (NEW)
LLM_TEMPERATURE=0.3      # 0.0-1.0, lower = more focused
LLM_TOP_P=0.9           # 0.0-1.0, nucleus sampling
LLM_MAX_TOKENS=150      # 50-200, output length limit

# Retry logic
LLM_MAX_RETRIES=3
LLM_RETRY_DELAY_BASE=2
```

## Parameter Reference

### LLM_TEMPERATURE
**Range:** 0.0 to 1.0  
**Default:** 0.3  
**Purpose:** Controls output randomness

| Value | Behavior | Best For |
|-------|----------|----------|
| 0.0-0.2 | Very focused, deterministic | Critical rule-following |
| **0.3** | **Balanced, reliable** | **Stream messages (recommended)** |
| 0.4-0.6 | More creative | Creative content |
| 0.7-1.0 | Highly creative | Brainstorming |

**For small LLMs (4B params), use 0.3 or lower** to ensure strict adherence to:
- Exact hashtag counts (3 for start, 2 for end)
- Character limits
- No username-derived hashtags

### LLM_TOP_P
**Range:** 0.0 to 1.0  
**Default:** 0.9  
**Purpose:** Nucleus sampling - limits token selection to top probability mass

| Value | Behavior |
|-------|----------|
| 0.9 | Recommended - good diversity |
| 0.95 | Slightly more varied |
| 1.0 | All tokens considered |

**Keep at 0.9** for most use cases. This provides good variety while maintaining quality.

### LLM_MAX_TOKENS
**Range:** 50 to 200  
**Default:** 150  
**Purpose:** Maximum output length (approximate)

| Platform | Recommended | Why |
|----------|-------------|-----|
| **Bluesky** | 120-150 | 300 char limit |
| **Mastodon** | 150-180 | 500 char limit |
| **Discord** | 150-200 | More room |

**Note:** This is a soft limit. The code also enforces hard character limits per platform.

## How These Parameters Work

### During Generation

1. **Prompt is sent** to the LLM with context (platform, username, title)
2. **Generation parameters control** how the LLM produces tokens:
   - `temperature`: How much to randomize token selection
   - `top_p`: Which tokens to consider (by probability)
   - `max_tokens`: When to stop generating
3. **Post-processing applies** additional guardrails:
   - Character limit enforcement
   - Username hashtag removal
   - Safe trimming at word boundaries

### Parameter Flow

```
User config (.env)
    ↓
AIMessageGenerator.__init__()
    ↓
Stored as instance variables
    ↓
_generate_with_retry()
    ↓
API call with config/options
    ↓
LLM generates text
    ↓
Post-processing (guardrails)
    ↓
Final message
```

## Provider-Specific Details

### Ollama
Parameters map to Ollama's generation options:
```python
options = {
    'temperature': LLM_TEMPERATURE,
    'top_p': LLM_TOP_P,
    'num_predict': LLM_MAX_TOKENS,
}
```

### Google Gemini
Parameters map to GenerationConfig:
```python
config = {
    'temperature': LLM_TEMPERATURE,
    'top_p': LLM_TOP_P,
    'max_output_tokens': LLM_MAX_TOKENS,
}
```

## Testing Your Configuration

### 1. Quick Test
```bash
# Run with debug logging to see parameters
export LOG_LEVEL=DEBUG
python stream-daemon.py
```

Look for log lines showing:
- `✓ Ollama LLM initialized (host: ..., model: ...)`
- Generated message character counts
- Any trimming or hashtag removal warnings

### 2. Unit Tests
```bash
python tests/test_prompt_improvements.py
```

Validates:
- Hashtag counts (3 for start, 2 for end)
- No username-derived hashtags
- Character limits

### 3. Manual Testing
Set `LLM_ENABLE=true` and watch a stream go live. Check:
- Messages post correctly
- Hashtags are relevant and correct count
- No username parts in hashtags
- Character limits respected

## Troubleshooting

### Model doesn't follow hashtag count rules

**Try:**
```ini
LLM_TEMPERATURE=0.2  # Lower temperature
LLM_TOP_P=0.85       # Slightly more focused
```

Or switch to a better instruction-following model:
```ini
LLM_MODEL=qwen2.5:3b  # Excellent at following rules
```

### Messages too short or cut off

**Try:**
```ini
LLM_MAX_TOKENS=180  # Allow longer output
```

### Messages too generic/boring

**Try:**
```ini
LLM_TEMPERATURE=0.5  # More creativity
```

**Note:** Higher creativity may reduce rule-following accuracy.

### Too many API errors

**Try:**
```ini
LLM_MAX_RETRIES=5
LLM_RETRY_DELAY_BASE=3
```

## Best Practices

1. **Start with defaults** - They're tuned for small LLMs
2. **Change one parameter at a time** - Easy to identify impact
3. **Test thoroughly** - Wait for a real stream to go live
4. **Monitor logs** - Watch for warnings about trimming or hashtag removal
5. **Use debug mode** - See full prompts and responses during testing

## Performance Impact

| Parameter | Impact on Speed | Impact on Quality |
|-----------|----------------|-------------------|
| Temperature | None | High |
| Top P | Minimal | Medium |
| Max Tokens | High | Medium |

**Lower `max_tokens` = faster generation** with negligible quality impact for short messages.

## See Also

- [LLM Optimization Guide](../features/llm-optimization.md) - Comprehensive tuning guide
- [AI Messages Feature](../features/ai-messages.md) - Feature overview
- [Secrets Configuration](./secrets.md) - API key setup
