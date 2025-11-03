# ðŸŽ™ï¸ Sparky Voice Services - Project Status Summary

**Session Date:** October 30, 2025  
**Status:** Services Split Complete âœ…  
**Next Phase:** Streaming Optimization & Higgs Protocol Rewrite

---

## ðŸ“Š WHAT WE ACCOMPLISHED

### âœ… Service Architecture Split
Successfully separated the monolithic voice service into three independent services:

1. **Whisper Service** (Port 8005)
   - Standalone speech-to-text transcription
   - Python 3.12 venv: `/home/mintdude/venvs/voice-ai-whisper`
   - CUDA support with PyTorch
   - Model cache: `/mnt/data3/VoiceModels/huggingface`
   - Uses: `faster-whisper` with `large-v3` model

2. **TTS Service** (Port 8004)
   - Text-to-speech with dual provider support
   - Python 3.11 venv: `/home/mintdude/venvs/voice-ai-py311`
   - Supports both Higgs and XTTS
   - Provider switchable via .env: `TTS_PROVIDER` (higgs_first | higgs_only | xtts_only)

3. **Higgs Audio Server** (Port 8010)
   - Advanced TTS using Higgs model
   - Standalone service
   - Location: `/home/mintdude/Github/sparky/higgs/`

### âœ… Configuration Centralization
- All services now use `.env` exclusively - no hardcoded values
- HuggingFace model cache properly configured: `/mnt/data3/VoiceModels/huggingface`
- GPU memory clearing added to all three services on startup/restart
- Windows client `config.ini` updated for dual-port support

### âœ… Windows Client Updates
- Updated to use separate ports for TTS (8004) and Whisper (8005)
- Added TTS provider display in console
- Properly handles both Higgs and XTTS providers

### âœ… GPU Memory Management
Fixed restart issues - all three services now clear GPU memory on startup:
- `torch.cuda.empty_cache()`
- `torch.cuda.synchronize()`

---

## ðŸŽ¯ CURRENT STATE

### Working Features âœ…
- [x] Whisper transcription (Port 8005)
- [x] XTTS text-to-speech (Port 8004)
- [x] Higgs text-to-speech (Port 8010)
- [x] Provider switching via .env (confirmed working)
- [x] GPU memory management on service restarts
- [x] Model caching (no re-downloads)
- [x] Windows tray client communication

### Service Status
```
sparky-whisper.service      â†’ ACTIVE (Port 8005)
sparky-voice-tts.service    â†’ ACTIVE (Port 8004)
higgs-local-server.service  â†’ ACTIVE (Port 8010)
```

### Configuration Files
**Server:** `/home/mintdude/Github/sparky/.env`
```bash
WHISPER_PORT=8005
VOICE_AI_PORT=8004
TTS_PROVIDER=xtts_only  # or higgs_first, higgs_only
WHISPER_MODEL=large-v3
VOICE_AI_MODEL_CACHE=/mnt/data3/VoiceModels/huggingface
VOICE_AI_GPU=cuda:0
```

**Client:** `D:\NCScott\VoiceAI-Client\config.ini`
```ini
[VoiceAI]
server_host = 10.6.1.15
tts_port = 8004
whisper_port = 8005
```

---

## âš ï¸ KNOWN ISSUES TO ADDRESS

### 1. **AI Rambling**
   - Model generates overly long responses
   - Sometimes talks in other languages
   - Needs better prompt engineering / system message tuning
   - May need response length limits

### 2. **XTTS Streaming Not Smooth**
   - Current streaming implementation needs optimization
   - Goal: Make XTTS streaming as smooth as possible
   - Priority: HIGH (next immediate task)

### 3. **Higgs Streaming Protocol Incomplete**
   - Higgs currently doesn't stream like XTTS does
   - Needs complete protocol rewrite for streaming support
   - Priority: HIGH (task after XTTS optimization)

---

## ðŸš€ NEXT STEPS (In Order)

### Phase 1: XTTS Streaming Optimization (IMMEDIATE)
**Goal:** Perfect the XTTS streaming implementation for smooth, real-time audio delivery

**Tasks:**
- [ ] Analyze current XTTS streaming code in `sparky_voice_tts.py`
- [ ] Identify bottlenecks and buffering issues
- [ ] Optimize chunk sizes and timing
- [ ] Test with various text lengths
- [ ] Measure latency and smoothness
- [ ] Document optimal parameters

**Expected Outcome:** Buttery-smooth XTTS streaming with minimal latency

---

### Phase 2: Higgs Streaming Protocol Rewrite (NEXT)
**Goal:** Implement full streaming support for Higgs to match XTTS quality

**Current Higgs Flow:**
```
Client â†’ TTS Service â†’ Higgs Server â†’ Generate complete audio â†’ Return URL â†’ Stream from file
```

**Target Higgs Flow:**
```
Client â†’ TTS Service â†’ Higgs Server â†’ Stream audio chunks in real-time â†’ Client plays immediately
```

**Tasks:**
- [ ] Design new streaming protocol for Higgs
- [ ] Modify `higgs_local_server.py` to support chunk-based generation
- [ ] Update `sparky_voice_tts.py` Higgs integration for streaming
- [ ] Match XTTS streaming API interface
- [ ] Test streaming quality and latency
- [ ] Benchmark against XTTS performance

**Technical Considerations:**
- Higgs model generates audio differently than XTTS
- May need to implement progressive audio token generation
- Need to maintain audio quality during streaming
- Must handle interruptions gracefully

---

### Phase 3: AI Response Quality (AFTER STREAMING)
**Goal:** Fix rambling and language switching issues

**Tasks:**
- [ ] Review LLM system prompts
- [ ] Add response length constraints
- [ ] Implement language detection/forcing
- [ ] Test conversation quality
- [ ] Fine-tune personality parameters

---

## ðŸ“ KEY FILE LOCATIONS

### Server Files (Linux)
```
/home/mintdude/Github/sparky/
â”œâ”€â”€ .env                                          # Master configuration
â”œâ”€â”€ voice-ai-service/
â”‚   â”œâ”€â”€ sparky_whisper_service.py                # Port 8005
â”‚   â””â”€â”€ sparky_voice_tts.py                      # Port 8004
â””â”€â”€ higgs/
    â””â”€â”€ higgs_local_server.py                    # Port 8010

/home/mintdude/venvs/
â”œâ”€â”€ voice-ai-whisper/    # Python 3.12 + PyTorch CUDA
â””â”€â”€ voice-ai-py311/      # Python 3.11 + XTTS

/mnt/data3/VoiceModels/
â”œâ”€â”€ huggingface/         # HF model cache
â”œâ”€â”€ voice-library/       # Voice embeddings
â””â”€â”€ Higgs/              # Higgs models

/etc/systemd/system/
â”œâ”€â”€ sparky-whisper.service
â”œâ”€â”€ sparky-voice-tts.service
â””â”€â”€ higgs-local-server.service
```

### Client Files (Windows)
```
D:\NCScott\VoiceAI-Client\
â”œâ”€â”€ sparky_tray_client.py
â””â”€â”€ config.ini
```

---

## ðŸ”§ IMPORTANT TECHNICAL DETAILS

### Model Locations (ALWAYS USE THESE)
```
/mnt/data3/VoiceModels/huggingface/hub/
â”œâ”€â”€ models--Systran--faster-whisper-large-v3
â”œâ”€â”€ models--bosonai--hubert_base
â””â”€â”€ ... (all downloaded, never re-download)
```

### Environment Variables in .env
```bash
# Voice Services
WHISPER_PORT=8005
WHISPER_HOST=0.0.0.0
VOICE_AI_PORT=8004
VOICE_AI_HOST=0.0.0.0

# Higgs Configuration
HIGGS_BASE_URL=http://127.0.0.1:8010
HIGGS_TEMPERATURE=1.0
HIGGS_TOP_P=0.95
HIGGS_TOP_K=50
HIGGS_RAS_WIN_LEN=7

# TTS Provider Selection
TTS_PROVIDER=xtts_only  # higgs_first | higgs_only | xtts_only

# Model Paths
VOICE_AI_MODEL_CACHE=/mnt/data3/VoiceModels/huggingface
VOICE_LIBRARY_PATH=/mnt/data3/VoiceModels/voice-library

# GPU
VOICE_AI_GPU=cuda:0

# Models
WHISPER_MODEL=large-v3
XTTS_MODEL=tts_models/multilingual/multi-dataset/xtts_v2
```

### Service Management Commands
```bash
# Check status
sudo systemctl status sparky-whisper sparky-voice-tts higgs-local-server

# Restart services
sudo systemctl restart sparky-whisper
sudo systemctl restart sparky-voice-tts
sudo systemctl restart higgs-local-server

# View logs
sudo journalctl -u sparky-whisper -f
sudo journalctl -u sparky-voice-tts -f
sudo journalctl -u higgs-local-server -f

# Test endpoints
curl http://10.6.1.15:8005/health  # Whisper
curl http://10.6.1.15:8004/health  # TTS
curl http://10.6.1.15:8010/health  # Higgs
```

---

## ðŸŽ¯ CRITICAL PRINCIPLES ESTABLISHED

1. **Never hardcode values** - Everything goes in `.env` or `config.ini`
2. **Models are always pre-downloaded** - Never re-download, always use `/mnt/data3/VoiceModels/`
3. **GPU memory management** - Always clear cache on service startup
4. **Configuration first** - Ask before generating massive code changes
5. **HuggingFace cache** - Always set `HF_HOME` and `HUGGINGFACE_HUB_CACHE` env vars

---

## ðŸ“Š PERFORMANCE METRICS (Current)

### XTTS (Working Well)
- Latency: ~1-2 seconds first audio
- Quality: High
- Streaming: Functional but needs optimization

### Higgs (Working, Not Streaming)
- Latency: ~3-5 seconds complete generation
- Quality: Excellent
- Streaming: **NOT IMPLEMENTED** (generates full audio, then streams file)

### Whisper
- Transcription speed: ~0.5-1.0x real-time with large-v3
- Accuracy: Excellent
- GPU memory: Managed

---

## ðŸŽ“ LESSONS LEARNED

1. **PyTorch CUDA installation is critical** for GPU acceleration
2. **GPU memory doesn't release automatically** on service restart - must clear explicitly
3. **Streaming protocols differ** between XTTS and Higgs - need unified approach
4. **HuggingFace model caching** requires proper env var setup to avoid re-downloads
5. **Service separation** prevents cascade failures (Whisper crash doesn't kill TTS)

---

## ðŸ”œ IMMEDIATE NEXT SESSION FOCUS

**PRIMARY GOAL:** Optimize XTTS streaming for buttery-smooth audio delivery

**What to bring to next chat:**
1. Current XTTS streaming code section from `sparky_voice_tts.py`
2. Any specific streaming issues or stuttering examples
3. Client-side audio playing code if needed
4. Performance measurements (if available)

**After XTTS is perfect:**
- Tackle Higgs streaming protocol rewrite
- Make Higgs stream chunks in real-time like XTTS
- Achieve feature parity between both providers

---

## âœ… SYSTEM STATUS: OPERATIONAL

All services are running and functional. Ready to move forward with streaming optimization!

**Current Provider:** XTTS (confirmed working)  
**Higgs Provider:** Functional (confirmed working, non-streaming)  
**Whisper:** Operational (confirmed working)

---

**Next Chat Should Start With:**
"Let's optimize XTTS streaming. Here's the current streaming code..."

---

## ðŸ“ž QUICK REFERENCE

**Switch TTS Provider:**
```bash
# Edit .env
nano /home/mintdude/Github/sparky/.env
# Change: TTS_PROVIDER=higgs_first  (or xtts_only or higgs_only)
sudo systemctl restart sparky-voice-tts
```

**Test Provider:**
```bash
# Watch logs to see which provider is used
sudo journalctl -u sparky-voice-tts -f

# Windows client shows: "ðŸŽ¤ TTS provider: higgs" or "ðŸŽ¤ TTS provider: xtts"
```

**Restart Everything:**
```bash
sudo systemctl restart sparky-whisper sparky-voice-tts higgs-local-server
```

---

**Status:** âœ… Ready for Phase 1 - XTTS Streaming Optimization  
**Priority:** HIGH - Next immediate task  
**Expected Duration:** 1-2 sessions

---

*End of Summary Document*
