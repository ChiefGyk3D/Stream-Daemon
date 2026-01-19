# Add Ollama LLM Support for Privacy-First AI Messages

## 🎯 Overview

This PR adds **Ollama support** to Stream Daemon, enabling users to run AI-generated messages completely locally with full privacy and zero API costs. Users can now choose between **Google Gemini** (cloud) or **Ollama** (local) for AI message generation.

## ✨ What's New

### 🤖 Ollama Provider Support

**New Features:**
- **Local LLM Execution** - Run AI models on your own hardware
- **100% Privacy** - Stream data never leaves your network
- **Zero API Costs** - Unlimited message generation
- **Offline Capable** - Works without internet connection
- **Multiple Models** - Support for gemma2, llama3.2, qwen2.5, mistral, phi3, and more
- **Provider Selection** - Easy switching between Ollama and Gemini via `LLM_PROVIDER` config

### 📝 Documentation Updates

- **Consolidated .env.example** - Merged Ollama configuration into main example file
- **Updated README** - Added Ollama as recommended AI provider option
- **AI Messages Guide** - Enhanced with detailed Ollama setup instructions
- **Migration Guide** - Help existing Gemini users understand Ollama option

### 🧪 Enhanced Testing

- **Moved all tests to tests/ folder** - Better organization
- **test_connection.py** - Comprehensive integration test using real .env data
  - Tests streaming platform authentication (Twitch, YouTube, Kick)
  - Tests social platform authentication (Mastodon, Bluesky, Discord, Matrix)
  - Tests LLM generation with actual live stream data
  - Tests AI message posting to all social platforms
  - Production readiness validation
- **test_ollama.py** - Dedicated Ollama integration testing
- **test_local_install.py** - Dependency validation

All tests can now run from the tests/ folder with proper import paths.

## 🔧 Technical Implementation

### New Configuration Options

```python
# Choose your AI provider
LLM_PROVIDER=ollama  # or 'gemini'

# Ollama-specific settings
LLM_OLLAMA_HOST=http://192.168.1.100
LLM_OLLAMA_PORT=11434
LLM_MODEL=gemma2:2b  # or gemma3:4b, llama3.2:3b, etc.
```

### Code Changes

**New Files:**
- `tests/test_connection.py` - Production-ready integration testing
- `tests/test_ollama.py` - Ollama-specific testing (moved from root)
- `tests/test_local_install.py` - Dependency validation (moved from root)

**Modified Files:**
- `stream_daemon/ai/generator.py` - Added Ollama provider support
- `.env.example` - Consolidated Ollama and Gemini configuration
- `README.md` - Updated to highlight Ollama as recommended option
- `docs/features/ai-messages.md` - Enhanced with Ollama setup guide

**Removed Files:**
- `.env.ollama.example` - Consolidated into main .env.example

### Architecture

```python
class AIMessageGenerator:
    def __init__(self):
        self.provider = os.getenv('LLM_PROVIDER', 'gemini').lower()
        
        if self.provider == 'ollama':
            self.client = ollama.Client(
                host=f"{ollama_host}:{ollama_port}"
            )
        elif self.provider == 'gemini':
            self.client = genai.Client(api_key=api_key)
    
    def authenticate(self) -> bool:
        """Verify connection to selected provider"""
        if self.provider == 'ollama':
            return self._authenticate_ollama()
        elif self.provider == 'gemini':
            return self._authenticate_gemini()
```

## 🧪 Testing

### Manual Testing Performed

1. **Ollama Provider Tests:**
   ```bash
   # Test Ollama connection and message generation
   python3 tests/test_ollama.py
   
   # Output:
   # ✅ SUCCESS: Ollama connection initialized!
   # ✅ SUCCESS: Generated stream start message!
   # ✅ SUCCESS: Generated Mastodon message!
   # ✅ SUCCESS: Generated stream end message!
   ```

2. **Production Integration Test:**
   ```bash
   # Test with real .env data and live streams
   python3 tests/test_connection.py
   
   # Results:
   # ✅ Twitch - LIVE - 110 viewers
   # ✅ YouTube - LIVE - 245 viewers  
   # ✅ Kick - LIVE - 11,002 viewers
   # ✅ AI generated message posted to all 4 social platforms
   # ✅ Stream Daemon is PRODUCTION READY!
   ```

3. **Dependency Validation:**
   ```bash
   python3 tests/test_local_install.py
   
   # ✅ SUCCESS - All dependencies installed correctly!
   ```

### Test Coverage

- ✅ Ollama server connectivity
- ✅ Model availability verification
- ✅ Message generation for all social platforms (Bluesky, Mastodon, Discord, Matrix)
- ✅ Character limit enforcement (300 for Bluesky, 500 for Mastodon)
- ✅ Stream start and end message generation
- ✅ Error handling and retry logic
- ✅ Fallback to static messages when AI unavailable
- ✅ Real production environment testing with live streams

## 🔄 Migration Path

### For Existing Users (Using Gemini)

**No changes required!** Your current setup continues to work:

```bash
# Current setup - still works perfectly
LLM_ENABLE=True
GEMINI_API_KEY=AIzaSyA_your_key_here
LLM_MODEL=gemini-2.0-flash-lite
```

Default provider is `gemini`, so existing deployments are unaffected.

### For New Users or Migration to Ollama

```bash
# 1. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 2. Pull a model
ollama pull gemma2:2b

# 3. Start server
ollama serve

# 4. Update .env
LLM_ENABLE=True
LLM_PROVIDER=ollama  # ← New setting
LLM_OLLAMA_HOST=http://localhost
LLM_OLLAMA_PORT=11434
LLM_MODEL=gemma2:2b
```

See [docs/features/ollama-migration.md](docs/features/ollama-migration.md) for complete guide.

## 📊 Performance & Resource Usage

### Ollama (Local)
- **Latency**: 0.5-2 seconds (hardware dependent)
- **Cost**: $0 per message
- **Rate Limit**: None (unlimited)
- **Privacy**: 100% local
- **Hardware**: 
  - Minimum: 4GB RAM, CPU-only (slower)
  - Recommended: 8GB+ RAM, NVIDIA/AMD/Apple GPU
  - Optimal: 16GB+ RAM, dedicated GPU

### Gemini (Cloud) 
- **Latency**: 1-2 seconds
- **Cost**: ~$0.0001 per message (Gemini 2.0 Flash Lite)
- **Rate Limit**: 10-30 requests/minute (model dependent)
- **Privacy**: Data sent to Google Cloud
- **Hardware**: None required

## 🔗 Related Documentation

- [AI Messages Guide](docs/features/ai-messages.md) - Complete setup for both providers
- [Ollama Migration Guide](docs/features/ollama-migration.md) - Switching from Gemini
- [Ollama Library](https://ollama.com/library) - Browse available models
- [FrankenLLM](https://github.com/ChiefGyk3D/FrankenLLM) - Multi-GPU Ollama setup

## ✅ Checklist

- [x] Code changes tested locally
- [x] Documentation updated
- [x] Tests pass (`test_ollama.py`, `test_connection.py`)
- [x] Backward compatibility maintained
- [x] Example configuration provided
- [x] Migration guide created
- [x] Tests organized in tests/ folder
- [x] .env.example consolidated

## 🎉 Impact

This PR enables privacy-conscious users to run AI-generated messages completely locally while maintaining full compatibility with existing Gemini users. No breaking changes, zero configuration changes required for existing deployments.
- ✅ Minimum 2-second delay between requests (stays under 30 RPM limit)
- ✅ Thread-safe coordination across all platforms
- ✅ Maintains existing retry logic with exponential backoff
- ✅ Prevents quota exhaustion from simultaneous streams

**Request Pattern Example:**
```
Twitch goes live → 4 social platforms
  ├─ Request 1: Bluesky  (0s)
  ├─ Request 2: Mastodon (2s delay)
  ├─ Request 3: Discord  (4s delay)
  └─ Request 4: Matrix   (6s delay)

YouTube goes live → waits for semaphore slots
  ├─ Request 5: Bluesky  (8s)
  └─ ...continues with 2s spacing
```

## 📊 Changes Summary

### Files Modified

**`stream_daemon/platforms/streaming/youtube.py`** (22 insertions, 4 deletions)
- Added `error_cooldown_time` tracking
- Implemented 10-minute cooldown check in `is_live()`
- Enhanced error logging with X/5 counter
- Automatic reset after cooldown expires

**`stream_daemon/ai/generator.py`** (35 insertions, 6 deletions)
- Added `threading` import for `Semaphore`
- Implemented global semaphore (max 4 concurrent)
- Added minimum delay enforcement (2 seconds)
- Thread-safe coordination with locks
- Updated docstrings to reflect actual implementation

### Backward Compatibility

✅ **Fully backward compatible** - no configuration changes required:
- YouTube monitoring works exactly as before, just with automatic recovery
- AI message generation works exactly as before, just with rate limiting
- No breaking changes to APIs or configuration
- Existing behavior preserved, only adds resilience

## 🧪 Testing

### YouTube Error Recovery

**Test Scenario:** Simulate consecutive YouTube API errors
```python
# After 5 errors, enters 10-minute cooldown
# Logs: "YouTube: Maximum consecutive errors (5) reached. Entering 10-minute cooldown."
# During cooldown: "YouTube: In error cooldown. X minutes remaining."
# After cooldown: "YouTube: Error cooldown period ended. Resetting consecutive errors."
```

**Manual Testing:**
- Tested with invalid API key (triggers errors)
- Verified cooldown countdown in logs
- Confirmed automatic recovery after 10 minutes
- Verified error counter resets correctly

### Gemini Rate Limiting

**Test Scenario:** Multiple streams go live simultaneously
```python
# 3 streaming platforms × 4 social networks = 12 potential requests
# Semaphore limits to 4 concurrent
# 2-second delay between each request
# Total time: ~24 seconds for 12 requests (stays well under 30 RPM)
```

**Expected Behavior:**
- Requests queue automatically when 4 concurrent limit reached
- Debug logs show: "Rate limiting: waiting Xs before API call"
- No 429 errors from Gemini API
- All announcements eventually post successfully

## 🚀 Deployment

### Recommended Deployment Steps

1. **Merge this PR to main**
2. **Deploy to production server** (192.168.213.210):
   ```bash
   ssh user@192.168.213.210
   cd /path/to/stream-daemon
   git pull origin main
   docker build -f Docker/Dockerfile -t stream-daemon:local .
   docker stop stream-daemon && docker rm stream-daemon
   docker-compose up -d  # or your container restart method
   ```
3. **Monitor logs** for recovery messages:
   ```bash
   docker logs -f stream-daemon | grep -E "cooldown|rate limit"
   ```
4. **Verify YouTube resumes** after errors
5. **Watch for Gemini rate limiting** working correctly

### Rollback Plan

If issues occur, rollback is simple:
```bash
git checkout <previous-commit>
docker build -f Docker/Dockerfile -t stream-daemon:local .
docker-compose restart
```

## 📝 Documentation Updates

Documentation has been updated to reflect new error recovery behavior:

- **README.md**: Updated YouTube feature description to mention automatic error recovery
- **docs/platforms/streaming/youtube.md**: Added "Error Recovery" section documenting cooldown behavior
- **docs/features/ai-messages.md**: Added "Rate Limiting" section documenting semaphore and delay

## 🔍 Review Checklist

- [x] Code follows project style guidelines
- [x] Backward compatible (no breaking changes)
- [x] Error handling is comprehensive
- [x] Logging is clear and helpful
- [x] Thread-safe implementation (rate limiting)
- [x] Documentation updated
- [x] Manual testing completed
- [x] Production-ready

## 🎉 Expected Outcomes

After merging:

1. **YouTube monitoring is resilient**: Automatic recovery from temporary API issues without manual intervention
2. **Gemini API stays under limits**: Proactive rate limiting prevents 429 errors even with simultaneous streams
3. **Better user experience**: No lost announcements due to platform errors or rate limits
4. **Reduced manual intervention**: Daemon self-heals from common error conditions
5. **Production stability**: Both issues observed in production logs are resolved

## 📚 Related Issues

- Fixes production issue: YouTube "5 consecutive errors" permanent disable
- Addresses missing implementation: Gemini rate limiting mentioned in comments but not coded
- Improves resilience: Both YouTube and AI generation become self-healing

---

**Branch:** `hotfix/youtube-error-recovery`  
**Commits:** 
- `e483316` - fix: Add automatic recovery for YouTube consecutive errors
- `0e17562` - feat: Add Gemini API rate limiting

**Ready for:** Immediate merge to `main` and production deployment
