# LLM Optimization Guide

*Or: How to Make a Computer Count to Three Without Fucking It Up*

## Optimizing for Small LLMs (Gemma2, Phi, Llama 3B-4B)

Here's the thing about small language models - they're like interns. Eager, capable of 
doing the job, but you need to be VERY specific about what you want or you'll end up 
with 47 hashtags and a message that somehow includes the entire lyrics to "Bohemian Rhapsody."

This guide helps you configure Stream Daemon's AI message generation so your tiny robot 
brain actually follows instructions instead of going on creative tangents.

## Configuration Parameters

Add these settings to your configuration file. Yes, there are a lot of knobs to turn.
Welcome to AI in 2026 - we've automated everything except making it simple.

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

*The Knobs and Dials That Control Your Robot's Personality*

### Temperature (0.0 - 1.0)

Think of temperature as how drunk your AI is:
- **0.0-0.3** (Sober): Focused, consistent, follows instructions like a good employee
- **0.4-0.6** (Tipsy): Gets creative, might improvise a little
- **0.7-1.0** (Hammered): "Hashtags? What hashtags? Let me tell you about my dreams..."

**For stream messages, use 0.3.** We want the AI following rules, not going on creative journeys.

### Top P (0.0 - 1.0)

Nucleus sampling - sounds fancy, basically means "how many words should the AI consider 
before picking one?"

- **0.9** (Recommended): Only considers the best options. Like hiring - ignore the bottom 10%.
- **0.95**: A bit more adventurous with word choices
- **1.0**: Considers EVERYTHING including terrible options. Democracy in action.

### Max Tokens (50 - 200)

How many words (roughly) the AI can vomit out before we cut it off:
- **150** (Recommended): Enough for a post with hashtags without writing a novel
- **100**: For platforms with strict limits (looking at you, Bluesky)
- **200**: When you want the AI to really express itself (dangerous)

Too low = truncated mid-sentence like a bad cell pho—
Too high = the AI won't shut up and you're paying for every token.

## Prompt Engineering Enhancements

*The Art of Talking to Computers Like They're Particularly Dense Children*

The enhanced prompts now use several techniques to make small models actually listen:

### 1. Step-by-Step Instructions

Small LLMs perform better when you spell everything out. It's like giving directions to 
someone who's never been anywhere - "Turn left at the Starbucks. No, the OTHER Starbucks."
```
STEP 1 - CONTENT RULES
STEP 2 - HASHTAG RULES
```

### 2. Few-Shot Examples

We show the AI what good and bad outputs look like. Because apparently 
"EXACTLY 3 hashtags" isn't clear enough - we need to show examples like a preschool teacher.

The prompts include 3 good examples and 3 bad examples showing:
- ✓ Correct hashtag counts (3 for start, 2 for end)
- ✓ Hashtags from title only
- ✗ Common mistakes to avoid

### 3. Visual Markers

Using checkmarks and X marks helps smaller models understand what we want.
It's like training a dog with treats, except the dog is made of math.

- ✓ = Required/Good (Do this, you magnificent digital entity)
- ✗ = Forbidden/Bad (For the love of God, don't do this)

### 4. Repetition of Critical Rules

We repeat important rules multiple times because, like humans, AI sometimes needs to hear 
things three times before it sinks in. "EXACTLY 3 hashtags" appears in the prompt like 
a concerned parent reminding you to wear a jacket.

Key constraints are repeated multiple times:
- "EXACTLY 3 hashtags" (stated 3 times)
- Character limits (reinforced in multiple places)
- Username exclusion rule (stated in bold and examples)

## Recommended Models

For detailed model recommendations based on your GPU VRAM, see **[LLM Model Recommendations](./llm-model-recommendations.md)** - 
it's got tables, tiers, and more hardware-shaming than a PC gaming forum.

### Quick Reference

*The "I Don't Have Time to Read Documentation" Table*

| VRAM | Primary Model | Backup | Quality |
|------|---------------|--------|---------|
| **4GB** | `gemma3:2b` | `phi3:mini` | ⭐⭐⭐ |
| **6GB** | `gemma3:4b` | `qwen2.5:3b` | ⭐⭐⭐⭐ |
| **8GB** | `qwen2.5:7b` | `gemma3:4b` | ⭐⭐⭐⭐⭐ |
| **16GB** | `qwen2.5:14b` | `gemma3:12b` | ⭐⭐⭐⭐⭐+ |
| **24GB+** | `qwen2.5:32b` | `qwen2.5:14b` | Maximum |

### Ollama (Local/Self-hosted)

| Model | Size | Speed | Quality | Best For |
|-------|------|-------|---------|----------|
| **`qwen2.5:7b`** | 4.7GB | ⚡⚡ | ⭐⭐⭐⭐⭐ | **Recommended** - Best instruction following |
| `gemma3:2b` | 1.6GB | ⚡⚡⚡ | ⭐⭐⭐ | CPU-only systems |
| `gemma3:4b` | 2.9GB | ⚡⚡ | ⭐⭐⭐⭐ | 6GB GPUs |
| `qwen2.5:14b` | 9.0GB | ⚡⚡ | ⭐⭐⭐⭐⭐+ | 16GB GPUs - Premium quality |
| `llama3.1:8b` | 4.9GB | ⚡⚡ | ⭐⭐⭐⭐ | Good reasoning |

**Why Qwen 2.5?** The Qwen 2.5 family excels at following precise instructions - exactly what Stream Daemon needs for hashtag counts, character limits, and formatting rules. It's the "actually reads the assignment" model.

### Google Gemini (Cloud API)

*When you'd rather pay Google than deal with GPU drivers.*

| Model | Cost | Speed | Quality | Best For |
|-------|------|-------|---------|----------|
| **gemini-2.0-flash-lite** | Free tier | ⚡⚡⚡ | ⭐⭐⭐⭐ | **Recommended** - 30 req/min |
| **gemini-1.5-flash** | $0.075/1M | ⚡⚡ | ⭐⭐⭐⭐⭐ | Higher quality |

## Testing Your Configuration

*Trust But Verify (Mostly Just Verify)*

### 1. Quick Test
Run the prompt improvement test to see if your model actually listens:
```bash
python tests/test_prompt_improvements.py
```

### 2. Check Generated Messages
Enable debug logging to see the full conversation with your AI. It's like reading someone's 
therapy session, but the patient is a language model:
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

*When Your Robot Doesn't Do What You Asked*

### Problem: Model generates wrong number of hashtags

You said 3. It gave you 5. Or 1. Or it decided hashtags are oppressive and refused entirely.

**Solution 1:** Lower temperature
```ini
temperature = 0.2  # Even more focused
```

**Solution 2:** Try a different model
```bash
# Qwen models are excellent at following instructions
ollama pull qwen2.5:3b
```

**Solution 3:** Reduce max_tokens - sometimes forcing brevity helps focus:
```ini
max_tokens = 120  # Forces more concise output
```

### Problem: Model ignores character limits

**Why This Happens:** The model doesn't actually know what "300 characters" means. It's 
counting tokens, not characters, and frankly it's not great at counting either.

**Solution:** The code automatically trims messages, but you can:
1. Lower `max_tokens` to force shorter output
2. Use a more instruction-following model (Qwen, Gemma2)
3. Check logs for trimming warnings

### Problem: Model adds generic hashtags (#Gaming, #Live)

We specifically said "no generic hashtags" and it added #Gaming anyway. Because of course it did.

**Solution:** Already handled by enhanced prompts and guardrails, but ensure you're using:
- Latest code with improved prompts
- Temperature ≤ 0.3
- A recent model (Gemma2, Qwen2.5)

### Problem: Model uses username in hashtags

Your username is "ChiefGyk3D" and the AI decided #ChiefGyk3D or #Gyk was a great hashtag. 
Narrator: It was not a great hashtag.

**Solution:** This is caught by the `_validate_hashtags_against_username` guardrail:
- Automatically removes username-derived hashtags
- Check logs for "Removed username-derived hashtag" warnings
- If persistent, the model may need fine-tuning on your use case

## Performance Tips

*Squeeze Every Last Drop of Performance From Your Silicon*

### For CPU-Only Systems

You're running AI on your CPU. Brave. Foolish. Respectable.
```ini
model = gemma3:2b
temperature = 0.2
max_tokens = 100
```

### For GPU Systems (NVIDIA/AMD)

You have a graphics card. The AI gods smile upon you.
```ini
model = gemma3:4b  # or qwen2.5:7b for even better quality
temperature = 0.3
max_tokens = 150
```

### For Cloud API (Gemini)

Let Google handle it. Sometimes outsourcing is the answer.
```ini
provider = gemini
model = gemini-2.0-flash-lite
temperature = 0.3
max_tokens = 150
```
Rate limits: 30 requests/min (free tier), perfect for multi-stream setups.

## Advanced: Prompt Customization

*For When You Want to Get Your Hands Dirty*

If you want to further customize prompts for your specific use case (you masochist), 
edit these methods in `stream_daemon/ai/generator.py`:

- `_prompt_stream_start()`: Start message template
- `_prompt_stream_end()`: End message template

Key principles for small LLMs (learned through pain and suffering):
1. **Be explicit**: Assume the model knows nothing. Because it often doesn't.
2. **Use examples**: Show don't tell. Like teaching a toddler, but the toddler is math.
3. **Repeat critical constraints**: Say it once, say it twice, say it three times. They still might miss it.
4. **Use formatting**: Visual markers (✓/✗), steps, bold text - anything to make it obvious.
5. **Keep it focused**: One task per prompt. Multitasking is for humans (and we're not even good at it).

## Monitoring

*Keeping an Eye on Your Digital Employee*

Watch these log messages like a hawk:
- `✓ Ollama LLM initialized` - Successful connection
- `✨ Generated stream start message` - Success with char count
- `⚠ AI generated message too long, trimming` - Model exceeded limit
- `⚠ Removed username-derived hashtag` - Guardrail activated (caught the AI being stupid)

## See Also

*More Documentation for Your Reading Pleasure*

- [LLM Model Recommendations](./llm-model-recommendations.md) - **Pick the right model for your hardware**
- [AI Messages Feature](./ai-messages.md) - The feature overview (where this madness begins)
- [LLM Guardrails](./llm-guardrails.md) - All the ways we prevent AI from embarrassing you
- [Ollama Migration Guide](./ollama-migration.md) - Escape the cloud, run AI locally
- [Testing Guide](../development/testing.md) - Make sure this shit actually works
- [FrankenLLM](https://github.com/ChiefGyk3D/FrankenLLM) - Multi-GPU setups for the truly committed
