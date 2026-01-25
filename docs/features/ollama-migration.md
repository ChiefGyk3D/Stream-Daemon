# Ollama LLM Support - Migration Guide

## What's New?

Stream Daemon now supports **Ollama** for local LLM inference, giving you complete privacy and offline capabilities for AI-generated messages!

### Key Benefits

✅ **Privacy-First** - Your stream data never leaves your network  
✅ **Offline-Capable** - No internet required for AI message generation  
✅ **Cost-Free** - No API charges, run unlimited messages  
✅ **Customizable** - Choose from dozens of open-source models  
✅ **Full Control** - Host on your own hardware (GPU, CPU, or Raspberry Pi)

### Provider Comparison

| Feature | Google Gemini | Ollama |
|---------|---------------|---------|
| **Setup** | Get API key | Install server + pull model |
| **Cost** | Free tier: 30 req/min | Free unlimited |
| **Privacy** | Data sent to Google | 100% local |
| **Offline** | ❌ Requires internet | ✅ Works offline |
| **Quality** | Excellent | Very good (model-dependent) |
| **Speed** | ~1-2 seconds | Varies by hardware |
| **Hardware** | None | GPU recommended, CPU works |

---

## For Existing Users (Using Gemini)

**Good news:** Your existing setup continues to work with **zero changes required**!

The default provider is still `gemini`, so you don't need to change anything.

### Your Current Configuration (Still Works)

```bash
# .env file
LLM_ENABLE=True
GEMINI_API_KEY=AIzaSyA_your_key_here
LLM_MODEL=gemini-2.0-flash-lite
```

This continues to work exactly as before. No migration needed!

---

## For New Users (Choosing Ollama)

If you want to use Ollama instead of Gemini, here's how:

### Step 1: Install Ollama

On your LLM server (can be same machine or dedicated server):

```bash
# Linux
curl -fsSL https://ollama.com/install.sh | sh

# macOS
brew install ollama

# Windows - download from https://ollama.com/download
```

**Multi-GPU Setup:** Got GPUs from different eras, vendors, or possibly dimensions? See [FrankenLLM](https://github.com/ChiefGyk3D/FrankenLLM) for the dark arts of combining them into one unholy LLM server. NVIDIA RTX 3050 + RTX 5060 Ti? Sure. AMD + NVIDIA in the same box? Why not. We named it FrankenLLM because you're literally stitching GPU corpses together. "IT'S ALIVE! AND IT KNOWS EXACTLY 3 HASHTAGS!"

### Step 2: Discover Available Models

Browse and search for models:

```bash
# View all available models at https://ollama.com/library

# List locally installed models
ollama list

# Search for specific models (requires ollama >= 0.1.26)
ollama search llama
ollama search gemma
```

### Step 3: Pull a Model

Choose a model based on your hardware:

```bash
# 🏆 Recommended for most users (~1 second response time!)
ollama pull gemma3:4b

# Alternative options:
ollama pull gemma3:12b    # Premium quality (16GB GPU)
ollama pull qwen2.5:7b    # Excellent instruction following (slower ~11s)
ollama pull llama3.2:3b   # Fast backup option
```

### Step 4: Start Ollama Server

```bash
# Allow remote connections (if Stream Daemon is on different machine)
OLLAMA_HOST=0.0.0.0 ollama serve

# Or just run locally
ollama serve
```

### Step 5: Configure Stream Daemon

Add to your `.env` file:

```bash
# Enable AI messages
LLM_ENABLE=True

# Use Ollama provider
LLM_PROVIDER=ollama

# Ollama server location
LLM_OLLAMA_HOST=http://192.168.1.100  # Your server IP
LLM_OLLAMA_PORT=11434                  # Default port

# Model to use
LLM_MODEL=gemma3:4b
```

### Step 6: Test

```bash
# Test Ollama connection
curl http://192.168.1.100:11434/api/tags

# Test Stream Daemon
python3 -c "
from stream_daemon.ai.generator import AIMessageGenerator
from dotenv import load_dotenv
load_dotenv()

gen = AIMessageGenerator()
if gen.authenticate():
    print('✅ Ollama is ready!')
else:
    print('❌ Check configuration')
"
```

---

## Switching from Gemini to Ollama

Want to switch your existing setup? Easy!

### Before (Gemini)

```bash
# .env
LLM_ENABLE=True
GEMINI_API_KEY=AIzaSyA_your_key_here
LLM_MODEL=gemini-2.0-flash-lite
```

### After (Ollama)

```bash
# .env
LLM_ENABLE=True
LLM_PROVIDER=ollama                    # Add this line
LLM_OLLAMA_HOST=http://192.168.1.100  # Add this line
LLM_OLLAMA_PORT=11434                  # Add this line
LLM_MODEL=gemma3:4b                    # Change model (fast!)

# GEMINI_API_KEY is ignored when using Ollama (can leave it or remove it)
```

That's it! Restart Stream Daemon and you're using local LLMs.

**Pro Tip:** You can keep both provider configurations in the same `.env` file! Just change `LLM_PROVIDER` to switch between them without editing other settings.

---

## Switching from Ollama to Gemini

Going the other direction? Just as easy!

### Before (Ollama)

```bash
# .env
LLM_ENABLE=True
LLM_PROVIDER=ollama
LLM_OLLAMA_HOST=http://192.168.1.100
LLM_OLLAMA_PORT=11434
LLM_MODEL=gemma3:4b
```

### After (Gemini)

```bash
# .env
LLM_ENABLE=True
LLM_PROVIDER=gemini                    # Change or remove (gemini is default)
GEMINI_API_KEY=AIzaSyA_your_key_here  # Add this
LLM_MODEL=gemini-2.0-flash-lite       # Change model

# Ollama settings are ignored when using Gemini (can leave them)
```

---

## Using Both Providers (Advanced)

**Yes, you can have both Gemini and Ollama configured in the same `.env` file!**

This is useful for:
- **Quick switching** between providers without editing configs
- **Testing** different providers for quality comparison
- **Fallback** strategies (switch if one provider is down)
- **Development** vs **production** (Ollama for dev, Gemini for prod)

### Example: Both Providers in One File

```bash
# .env - Both providers configured

# Enable AI
LLM_ENABLE=True

# Choose active provider (switch by changing this line)
LLM_PROVIDER=ollama  # or 'gemini'

# Gemini configuration (used when LLM_PROVIDER=gemini)
GEMINI_API_KEY=AIzaSyA_your_key_here

# Ollama configuration (used when LLM_PROVIDER=ollama)
LLM_OLLAMA_HOST=http://192.168.1.100
LLM_OLLAMA_PORT=11434

# Model selection (provider-specific)
# For Gemini: gemini-2.0-flash-lite, gemini-1.5-flash, etc.
# For Ollama: gemma3:4b, gemma3:12b, qwen2.5:7b, etc.
LLM_MODEL=gemma3:4b

# Shared settings
LLM_MAX_RETRIES=3
LLM_RETRY_DELAY_BASE=2
```

### Switching Between Providers

Just change one line and restart:

```bash
# Use Ollama (local)
LLM_PROVIDER=ollama
LLM_MODEL=gemma3:4b

# Or use Gemini (cloud)
LLM_PROVIDER=gemini
LLM_MODEL=gemini-2.0-flash-lite
```

That's it! All other settings stay the same, and the unused provider's config is simply ignored.

---

## Recommended Models

### For Ollama

| Use Case | Model | VRAM | Speed | Quality |
|----------|-------|------|-------|--------|
| **🏆 Recommended** | `gemma3:4b` | ~3GB | **~1s** | Excellent |
| **Premium** | `gemma3:12b` | ~8GB | ~1.3s | Excellent+ |
| **Instruction following** | `qwen2.5:7b` | ~5GB | ~11s | Excellent |
| **Fastest small** | `llama3.2:3b` | ~2GB | Very fast | Good |
| **CPU-only** | `gemma3:2b` | ~2GB | Fast | Good |

### For Gemini

| Use Case | Model | Speed | Quality |
|----------|-------|-------|---------|
| **Default (Recommended)** | `gemini-2.0-flash-lite` | Very fast | Excellent |
| **Alternative** | `gemini-1.5-flash` | Fast | Excellent |
| **Highest quality** | `gemini-1.5-pro` | Slower | Best |

---

## Hardware Requirements for Ollama

### Minimum (CPU-only)
- **CPU:** 4 cores
- **RAM:** 8GB
- **Model:** `gemma3:2b` or `llama3.2:3b`
- **Speed:** 3-10 seconds per message

### Recommended (with GPU)
- **GPU:** 6GB+ VRAM (RTX 3060, RTX 4060, etc.)
- **CPU:** Any modern CPU
- **RAM:** 8GB
- **Model:** `gemma3:4b` (🏆 ~1 second response!)
- **Speed:** 1-2 seconds per message

### Optimal (High-end GPU)
- **GPU:** 8GB+ VRAM (RTX 3060, 4060, etc.)
- **CPU:** Any modern CPU
- **RAM:** 16GB
- **Model:** Any model up to 13B
- **Speed:** <1 second per message

---

## Troubleshooting

### "Failed to connect to Ollama"

**Solution:**
```bash
# 1. Check Ollama is running
curl http://192.168.1.100:11434/api/tags

# 2. Ensure firewall allows port 11434
sudo ufw allow 11434/tcp

# 3. Start Ollama with remote access
OLLAMA_HOST=0.0.0.0 ollama serve
```

### "Model not found"

**Solution:**
```bash
# Pull the model
ollama pull gemma3:4b

# Verify it's available
ollama list
```

### "Ollama Python client not installed"

**Solution:**
```bash
pip install ollama
```

---

## More Information

- **Full Documentation:** [docs/features/ai-messages.md](ai-messages.md)
- **Ollama Website:** https://ollama.com
- **Model Library:** https://ollama.com/library
- **Configuration Reference:** [docs/configuration/secrets-quick-reference.md](../configuration/secrets-quick-reference.md)

---

## Questions?

Open an issue on GitHub or check the [documentation](../README.md)!
