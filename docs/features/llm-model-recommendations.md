# LLM Model Recommendations by Hardware

🎯 **Choose the right model for your GPU** - Maximize quality within your VRAM limits.

## Overview

*Or: A Guide to Buying More GPU Than You Need to Generate Tweets*

Look, here's the thing about AI models and VRAM - it's like buying a car. You *could* get a sensible Honda Civic, but some asshole at NVIDIA convinced you that you need a Ferrari to drive to the grocery store. And now you've got a $2,000 graphics card generating "Going live on Twitch! 🎮" 

The good news? Stream Daemon actually uses that expensive silicon. The bad news? You're still using a supercomputer to write social media posts. Welcome to 2026.

**Key Insight:** Bigger models = better instruction following. It's that simple. The goal is to cram the fattest model possible into your GPU without it crying for help.

Think of VRAM like a hot dog eating contest. You want to shove as many parameters in there as physically possible before everything comes back up. Except instead of vomiting, you get "CUDA out of memory" errors. Same energy, different consequences.

---

## Quick Reference Table

*For those of you with the attention span of a goldfish (so, everyone in 2026):*

| VRAM | Primary Model | Backup Model | Quality | Speed |
|------|---------------|--------------|---------|-------|
| **4GB** | `gemma3:2b` | `phi3:mini` | ⭐⭐⭐ | ⚡⚡⚡ |
| **6GB** | `gemma3:4b` | `qwen2.5:3b` | ⭐⭐⭐⭐ | ⚡⚡⚡ |
| **8GB** | `gemma3:4b` | `qwen2.5:7b` | ⭐⭐⭐⭐⭐ | **⚡⚡⚡ ~1s** |
| **12GB** | `gemma3:4b` | `llama3.1:8b` | ⭐⭐⭐⭐⭐ | ⚡⚡⚡ |
| **16GB** | `gemma3:12b` | `qwen2.5:14b` | ⭐⭐⭐⭐⭐+ | **⚡⚡⚡ ~1.3s** |
| **24GB+** | `gemma3:27b` | `qwen2.5:32b` | ⭐⭐⭐⭐⭐+ | ⚡⚡ |

> **🏆 January 2026 Benchmark Winner:** Gemma3 models are **6-10x faster** than Qwen2.5 for stream announcements (~1s vs ~11s). For social media posts, speed wins.

---

## Detailed Recommendations by VRAM Tier

*Because apparently we need to categorize everything. Here's your GPU caste system:*

### 4GB VRAM (GTX 1650, RTX 3050 Mobile)

**The "I'm Just Happy to Be Here" Tier**

You've got 4GB of VRAM. That's adorable. That's what flagship phones had in 2020. 
You're basically asking a calculator to write poetry, but you know what? It'll fucking work.

Just expect some CPU offloading - which is tech speak for "your GPU gave up and your CPU is picking up the slack like a coworker covering for someone who's perpetually on vacation."

| Model | Size | Quality | Speed | Instruction Following |
|-------|------|---------|-------|----------------------|
| `gemma3:2b` | ~1.6GB | ⭐⭐⭐ | ⚡⚡⚡ | Good |
| `phi3:mini` | ~2.3GB | ⭐⭐⭐ | ⚡⚡⚡ | Good |
| `qwen2.5:1.5b` | ~1.2GB | ⭐⭐⭐ | ⚡⚡⚡ | Excellent |

**Recommended Configuration:**
```bash
# .env settings for 4GB VRAM
LLM_MODEL=gemma3:2b
LLM_TEMPERATURE=0.2          # Lower for better instruction following
LLM_TOP_P=0.85               # Slightly tighter sampling
LLM_MAX_TOKENS=120           # Shorter to ensure completion
LLM_ENABLE_QUALITY_SCORING=True
LLM_MIN_QUALITY_SCORE=6
```

**Installation:**
```bash
ollama pull gemma3:2b
ollama pull phi3:mini        # Backup option
```

---

### 6GB VRAM (RTX 2060, RTX 3060 Mobile, GTX 1660)

**The "Goldilocks Zone for Poor People" Tier**

6GB. Now we're talking. Not great, not terrible - like a Yelp review for a Denny's.

This is where you can actually run decent models without your computer sounding like a jet engine or your electricity bill looking like you're running a Bitcoin mining operation.

| Model | Size | Quality | Speed | Instruction Following |
|-------|------|---------|-------|----------------------|
| `gemma3:4b` | ~2.9GB | ⭐⭐⭐⭐ | ⚡⚡ | Very Good |
| `qwen2.5:3b` | ~2.3GB | ⭐⭐⭐⭐ | ⚡⚡⚡ | Excellent |
| `llama3.2:3b` | ~2.0GB | ⭐⭐⭐⭐ | ⚡⚡ | Good |

**Recommended Configuration:**
```bash
# .env settings for 6GB VRAM
LLM_MODEL=gemma3:4b
LLM_TEMPERATURE=0.3
LLM_TOP_P=0.9
LLM_MAX_TOKENS=150
LLM_ENABLE_QUALITY_SCORING=True
LLM_MIN_QUALITY_SCORE=6
```

**Installation:**
```bash
ollama pull gemma3:4b
ollama pull qwen2.5:3b       # Backup option
```

---

### 8GB VRAM (RTX 3050, RTX 3060, RTX 4060, RX 6600)

**The "Sweet Spot" - Also Known As "What Most People Actually Have"**

8GB is where the magic happens. And thanks to Google's Gemma 3, you can generate 
social media posts in about ONE SECOND. ONE. SECOND.

Meanwhile, some models take 11 seconds to write "Hey, I'm live on Twitch." 
That's enough time to make a sandwich. Choose wisely.

| Model | Size | Quality | Speed | Response Time |
|-------|------|---------|-------|---------------|
| **`gemma3:4b`** | ~3.0GB | ⭐⭐⭐⭐⭐ | ⚡⚡⚡ | **~1.0s** 🏆 |
| `qwen2.5:7b` | ~4.7GB | ⭐⭐⭐⭐⭐ | ⚡ | ~11s |
| `llama3.1:8b` | ~4.9GB | ⭐⭐⭐⭐⭐ | ⚡⚡ | ~8s |
| `mistral:7b` | ~4.1GB | ⭐⭐⭐⭐ | ⚡⚡ | ~7s |

**Why Gemma3:4b?** 

Benchmark testing in January 2026 showed Gemma3:4b completing stream announcements 
in ~1 second while Qwen2.5:7b took ~11 seconds. That's a 10x speed difference.

For generating social media posts, you want the announcement out BEFORE you've 
already been streaming for 30 seconds. Gemma3 gets it done while you're still 
adjusting your webcam.

**Qwen2.5:7b** is still excellent for instruction following - it won't fuck up 
your hashtag counts. But if speed matters (and it does for going live), Gemma3 wins.

**Recommended Configuration:**
```bash
# .env settings for 8GB VRAM (RECOMMENDED)
LLM_MODEL=gemma3:4b
LLM_TEMPERATURE=0.3
LLM_TOP_P=0.9
LLM_MAX_TOKENS=150
LLM_ENABLE_QUALITY_SCORING=True
LLM_MIN_QUALITY_SCORE=7
```

**Installation:**
```bash
ollama pull gemma3:4b        # Primary - blazing fast, great quality
ollama pull qwen2.5:7b       # Backup - excellent instruction following
```

---

### 12GB VRAM (RTX 3060 12GB, RTX 4070, RX 6700 XT)

**The "I Have Money But I'm Not Showing Off" Tier**

12GB gives you comfortable headroom. It's like having a spare bedroom - you don't 
strictly NEED it, but it's nice knowing it's there when your in-laws visit.

You can run the same models as 8GB but with room to breathe. Larger context windows, 
faster inference, and that smug satisfaction of knowing your GPU isn't constantly 
on the verge of a panic attack.

| Model | Size | Quality | Speed | Instruction Following |
|-------|------|---------|-------|----------------------|
| **`qwen2.5:7b`** | ~4.7GB | ⭐⭐⭐⭐⭐ | ⚡⚡⚡ | **Excellent** |
| `llama3.1:8b` | ~4.9GB | ⭐⭐⭐⭐⭐ | ⚡⚡ | Good |
| `gemma3:9b` | ~5.8GB | ⭐⭐⭐⭐⭐ | ⚡⚡ | Very Good |
| `mistral:7b` | ~4.1GB | ⭐⭐⭐⭐ | ⚡⚡⚡ | Good |

**Recommended Configuration:**
```bash
# .env settings for 12GB VRAM
LLM_MODEL=qwen2.5:7b
LLM_TEMPERATURE=0.3
LLM_TOP_P=0.9
LLM_MAX_TOKENS=150
LLM_ENABLE_QUALITY_SCORING=True
LLM_MIN_QUALITY_SCORE=7
```

**Installation:**
```bash
ollama pull qwen2.5:7b       # Primary
ollama pull llama3.1:8b      # Alternative with different "voice"
```

---

### 16GB VRAM (RTX 4080, RTX 5060 Ti, RX 7800 XT, Tesla T4)

**The "I Made Some Good Life Choices" Tier** *(Or bad ones, depending on your credit card statement)*

16GB. Now you're playing with the big boys. And with Gemma3:12b, you get premium 
quality at near-instant speeds (~1.3 seconds). That's faster than some people can 
read the tweet, let alone write it.

You're essentially running a digital entity that can write better social media posts 
than most humans, in less time than it takes to blink twice. Peak humanity.

| Model | Size | Quality | Speed | Response Time |
|-------|------|---------|-------|---------------|
| **`gemma3:12b`** | ~7.5GB | ⭐⭐⭐⭐⭐+ | ⚡⚡⚡ | **~1.3s** 🏆 |
| `qwen2.5:14b` | ~9.0GB | ⭐⭐⭐⭐⭐+ | ⚡ | ~11s |
| `llama3.1:8b` | ~4.9GB | ⭐⭐⭐⭐⭐ | ⚡⚡ | ~8s |
| `codestral:22b-v0.1-q4` | ~13GB | ⭐⭐⭐⭐⭐ | ⚡ | ~15s |

**Why Gemma3:12b?** 

Benchmark winner. Premium quality with near-instant response. It's like having 
a professional copywriter who works for free and never takes breaks.

**Qwen2.5:14b** is still exceptional for instruction following, but takes ~11 seconds. 
If you're batch processing or don't mind the wait, it's great. For real-time 
stream announcements? Gemma3:12b is the clear winner.

**Recommended Configuration:**
```bash
# .env settings for 16GB VRAM (PREMIUM)
LLM_MODEL=gemma3:12b
LLM_TEMPERATURE=0.3
LLM_TOP_P=0.9
LLM_MAX_TOKENS=150
LLM_ENABLE_QUALITY_SCORING=True
LLM_MIN_QUALITY_SCORE=7
```

**Installation:**
```bash
ollama pull gemma3:12b       # Primary - premium quality, fast
ollama pull qwen2.5:14b      # Alternative - exceptional instruction following
ollama pull llama3.1:8b      # Fast backup
```

---

### 24GB+ VRAM (RTX 3090, RTX 4090, A100, A6000)

**The "I Either Mine Crypto, Do ML Research, or Have a Problem" Tier**

24 gigabytes of video memory. You magnificent bastard.

You can run models so large they probably have existential crises. 32 billion parameters? 
Sure. 70 billion with some compression? Why not. You're basically running a small 
civilization in silicon.

For stream announcements.

I'm not judging. Okay, I'm judging a little. But respect.

| Model | Size | Quality | Speed | Instruction Following |
|-------|------|---------|-------|----------------------|
| **`qwen2.5:32b`** | ~20GB | ⭐⭐⭐⭐⭐++ | ⚡ | **Near-Perfect** |
| `llama3.1:70b-q4` | ~40GB* | ⭐⭐⭐⭐⭐++ | ⚡ | Excellent |
| `mixtral:8x7b` | ~26GB | ⭐⭐⭐⭐⭐+ | ⚡ | Very Good |
| `deepseek-v2:16b` | ~10GB | ⭐⭐⭐⭐⭐ | ⚡⚡ | Excellent |

*Note: 70B models require quantization (q4) to fit in 24GB, or multi-GPU setups.

**Recommended Configuration:**
```bash
# .env settings for 24GB+ VRAM (MAXIMUM)
LLM_MODEL=qwen2.5:32b
LLM_TEMPERATURE=0.3
LLM_TOP_P=0.9
LLM_MAX_TOKENS=150
LLM_ENABLE_QUALITY_SCORING=True
LLM_MIN_QUALITY_SCORE=8      # Can be strict with large models
```

**Installation:**
```bash
ollama pull qwen2.5:32b      # Primary
ollama pull qwen2.5:14b      # Faster alternative
```

---

## Multi-GPU Setups

*Because one GPU generating tweets wasn't absurd enough.*

If you have multiple GPUs - maybe an old one and a new one, or different brands like 
some kind of graphics card collector - you can actually use them together. Or separately. 
We don't judge your GPU relationship dynamics.

### Example: RTX 3050 (8GB) + RTX 5060 Ti (16GB)

*The "Hand-Me-Down Plus Upgrade" Configuration*

**Server 1 (RTX 3050 - 8GB):**
```bash
# Ollama instance on port 11434
ollama pull qwen2.5:7b
ollama pull gemma3:4b
```

**Server 2 (RTX 5060 Ti - 16GB):**
```bash
# Ollama instance on port 11435 (or different server)
ollama pull qwen2.5:14b
ollama pull gemma3:12b
ollama pull llama3.1:8b
```

**Stream Daemon Configuration (using the bigger GPU):**
```bash
LLM_OLLAMA_HOST=http://192.168.1.100  # Server with 5060 Ti
LLM_OLLAMA_PORT=11435
LLM_MODEL=qwen2.5:14b
```

**See [FrankenLLM](https://github.com/ChiefGyk3D/FrankenLLM)** for the complete guide to building your own multi-GPU LLM monster.

Why "FrankenLLM"? Because you're literally stitching together GPU corpses from different generations, vendors, and possibly alternate timelines into one unholy abomination that generates social media posts. NVIDIA RTX 3050 from 2022 + RTX 5060 Ti from 2025? Sure. AMD RX 6700 XT + NVIDIA RTX 4090? Absolutely unhinged, but we support it.

"IT'S ALIVE! AND IT FOLLOWS INSTRUCTIONS BETTER THAN MY INTERNS!"

FrankenLLM covers:
- 🔧 Installing Ollama on multi-GPU systems
- ⚡ Configuring GPU layer distribution
- 🔌 Running Ollama as a remote service
- 🧪 Testing and benchmarking your monster
- 🛠️ Troubleshooting when the villagers come with pitchforks

---

## Model Families Explained

*A brief history of corporations teaching silicon to bullshit.*

### Qwen 2.5 (Recommended for Stream Daemon)

**Alibaba's Gift to the World** - Yes, the shopping company. Turns out they're pretty good at AI too.

The Qwen 2.5 family is like that overachieving student who actually follows the syllabus.
You say "exactly 3 hashtags" and it gives you exactly 3 hashtags. Revolutionary concept, 
apparently, because most models treat instructions like suggestions.

| Model | Parameters | VRAM Needed | Notes |
|-------|------------|-------------|-------|
| `qwen2.5:1.5b` | 1.5B | ~2GB | Minimal systems |
| `qwen2.5:3b` | 3B | ~3GB | Good for 6GB GPUs |
| `qwen2.5:7b` | 7B | ~5GB | **Best value** |
| `qwen2.5:14b` | 14B | ~9GB | **Premium quality** |
| `qwen2.5:32b` | 32B | ~20GB | Maximum quality |
| `qwen2.5:72b` | 72B | ~45GB | Requires multi-GPU |

### Gemma 3 (Google)

**Google's Entry** - Because of course Google has an AI model. They probably have seven.

Gemma 3 offers excellent quality with good instruction following. It's like the 
reliable Honda of AI models - not flashy, but it'll get you there without breaking down.

| Model | Parameters | VRAM Needed | Notes |
|-------|------------|-------------|-------|
| `gemma3:2b` | 2B | ~2GB | Fast, entry-level |
| `gemma3:4b` | 4B | ~3GB | Good balance |
| `gemma3:9b` | 9B | ~6GB | High quality |
| `gemma3:12b` | 12B | ~8GB | Excellent |
| `gemma3:27b` | 27B | ~17GB | Premium |

### LLaMA 3.1 (Meta)

**Meta's Contribution** - Zuckerberg's gift to open-source AI.

LLaMA 3.1 is versatile and capable, but can be a bit... creative with instructions.
It's like that talented employee who does great work but interprets "business casual" 
as "Hawaiian shirt and cargo shorts." You might need to be more explicit with it.

| Model | Parameters | VRAM Needed | Notes |
|-------|------------|-------------|-------|
| `llama3.2:1b` | 1B | ~1GB | Very fast, basic |
| `llama3.2:3b` | 3B | ~2GB | Good for chat |
| `llama3.1:8b` | 8B | ~5GB | Popular choice |
| `llama3.1:70b` | 70B | ~40GB | Requires quantization |

### Mistral/Mixtral

**The French Connection** - Mistral AI proving that the French can do more than wine and cheese.

Good all-around performance. Mixtral uses "Mixture of Experts" architecture, which sounds 
fancy but basically means it has multiple smaller brains working together. Like a hive mind,
but for generating social media posts. The future is weird.

| Model | Parameters | VRAM Needed | Notes |
|-------|------------|-------------|-------|
| `mistral:7b` | 7B | ~4GB | Good general purpose |
| `mixtral:8x7b` | 46.7B MoE | ~26GB | Mixture of experts |

---

## Optimized Settings Summary

*Because copy-pasting is easier than thinking.*

### For Small Models (≤4B parameters)

**"Hand-Holding Mode"** - These little guys need extra guidance.

```bash
LLM_TEMPERATURE=0.2          # Very focused
LLM_TOP_P=0.85               # Tighter sampling
LLM_MAX_TOKENS=120           # Shorter outputs
LLM_ENABLE_QUALITY_SCORING=True
LLM_MIN_QUALITY_SCORE=6      # More lenient
LLM_MAX_RETRIES=3            # More retries
```

### For Medium Models (7-8B parameters)

**"The Goldilocks Settings"** - Just right.

```bash
LLM_TEMPERATURE=0.3          # Balanced
LLM_TOP_P=0.9                # Standard sampling
LLM_MAX_TOKENS=150           # Standard length
LLM_ENABLE_QUALITY_SCORING=True
LLM_MIN_QUALITY_SCORE=7      # Moderate strictness
LLM_MAX_RETRIES=3
```

### For Large Models (≥12B parameters)

**"Trust Mode"** - These models actually know what they're doing. Mostly.

```bash
LLM_TEMPERATURE=0.3          # Can go slightly higher (0.4)
LLM_TOP_P=0.9                # Standard sampling
LLM_MAX_TOKENS=150           # Standard length
LLM_ENABLE_QUALITY_SCORING=True
LLM_MIN_QUALITY_SCORE=8      # Can be stricter
LLM_MAX_RETRIES=2            # Fewer retries needed
```

---

## Google Gemini (Cloud Alternative)

*For When You'd Rather Pay Google Than Buy a GPU*

No GPU? No problem! Just hand your data to one of the largest corporations on Earth 
and they'll generate your tweets for you. What could go wrong?

In all seriousness, Gemini is actually pretty good and the free tier is generous.
Sometimes the right answer is "let someone else deal with it."

| Model | Rate Limit | Quality | Cost | Best For |
|-------|------------|---------|------|----------|
| `gemini-2.0-flash-lite` | 30 RPM | ⭐⭐⭐⭐ | Free tier | **Recommended** |
| `gemini-2.0-flash` | 15 RPM | ⭐⭐⭐⭐⭐ | Low | Higher quality |
| `gemini-2.5-flash` | 10 RPM | ⭐⭐⭐⭐⭐ | Low | Latest features |
| `gemini-2.5-pro` | 5 RPM | ⭐⭐⭐⭐⭐+ | Medium | Maximum quality |

**Configuration:**
```bash
LLM_ENABLE=True
LLM_PROVIDER=gemini
LLM_MODEL=gemini-2.0-flash-lite
GEMINI_API_KEY=your_api_key_here
```

---

## Troubleshooting

*When Your Expensive Equipment Decides to Have a Bad Day*

### Model runs slowly / uses CPU

**Symptom:** Generation takes 10+ seconds. You could write the tweet yourself faster.

**What's Actually Happening:** Your model is too fat for your GPU. It's spilling over 
into CPU territory like a muffin top over jeans that don't fit anymore.

**Solution:** Use a smaller model that fits your VRAM. Accept your hardware's limitations.
It's called personal growth.
```bash
# Check current model size
ollama list

# Switch to smaller model
LLM_MODEL=qwen2.5:3b  # Instead of qwen2.5:7b
```

### Model ignores hashtag counts

**Symptom:** You asked for 3 hashtags. You got 7. Or 0. Or the AI just made up words.

**What's Actually Happening:** The model is treating your instructions as "suggestions"
rather than "rules." Like a cat being told to stay off the counter.

**Solution 1:** Lower temperature
```bash
LLM_TEMPERATURE=0.2
```

**Solution 2:** Enable quality scoring to catch and retry
```bash
LLM_ENABLE_QUALITY_SCORING=True
LLM_MIN_QUALITY_SCORE=7
```

**Solution 3:** Upgrade to a larger model (larger = better instruction following)

The nuclear option. Throw money at the problem. Works in tech, works in life.

### Out of memory errors

**Symptom:** Ollama crashes, your terminal fills with angry red text, existential dread sets in.

**What's Actually Happening:** Your GPU is screaming "I CAN'T HOLD ALL THESE PARAMETERS"
and giving up entirely. It's the silicon equivalent of a mental breakdown.

**Solution:** Use a quantized or smaller model. Quantization is like compression for AI -
you lose some quality but gain the ability to actually run the damn thing:
```bash
# Use quantized version (if available)
ollama pull qwen2.5:7b-q4_0

# Or use smaller model
ollama pull qwen2.5:3b
```

---

## See Also

*Further Reading for the Terminally Curious*

- [AI Messages Overview](./ai-messages.md) - The feature that started this beautiful disaster
- [LLM Optimization Guide](./llm-optimization.md) - Squeeze every last drop of performance
- [LLM Guardrails](./llm-guardrails.md) - Teaching robots to behave
- [Ollama Migration Guide](./ollama-migration.md) - Escape the cloud, embrace the local
- [FrankenLLM](https://github.com/ChiefGyk3D/FrankenLLM) - Multi-GPU mad science
