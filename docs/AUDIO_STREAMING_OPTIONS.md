# Flutter Windows Audio Streaming Options

## Current Situation

**Python Client (Working):**
- Uses `sounddevice.OutputStream.write()` 
- Writes raw PCM int16 samples directly to audio device
- TRUE streaming - no file creation, no batching
- Low latency, no gaps

**Current Flutter Client:**
- Uses `audioplayers` package
- Requires complete WAV files (not raw PCM)
- Must batch chunks into files → creates gaps
- Not true streaming

## Recommended Options for True PCM Streaming

### 1. **mp_audio_stream** ⭐ RECOMMENDED

**Why:** Explicitly designed for raw audio data streams using miniaudio library

**Features:**
- ✅ Raw PCM streaming support
- ✅ Multi-platform (including Windows)
- ✅ Simple Stream-based API
- ✅ Designed for continuous playback of buffered audio data
- ✅ Uses miniaudio (low-level audio library, similar to sounddevice)

**Pub.dev:** https://pub.dev/packages/mp_audio_stream

**Example Usage (estimated):**
```dart
import 'package:mp_audio_stream/mp_audio_stream.dart';

// Create audio stream player
final player = AudioStreamPlayer(
  sampleRate: 24000,
  channels: 1,
  format: AudioFormat.pcmInt16,
);

// Stream audio chunks directly
await player.playStream(stream);
// Or write chunks directly
player.write(audioChunk);
```

**Pros:**
- Most suitable for raw PCM streaming
- Simple API
- Active development

**Cons:**
- Less popular (may have fewer examples)
- Need to verify Windows support quality

---

### 2. **audio_io** 

**Why:** Real-time audio streaming with Stream-based API

**Features:**
- ✅ Stream-based API
- ✅ Low-latency audio I/O
- ✅ Real-time audio processing
- ✅ Windows support

**Pub.dev:** https://pub.dev/packages/audio_io

**Example Usage (estimated):**
```dart
import 'package:audio_io/audio_io.dart';

// Create audio output
final output = AudioOutput(
  sampleRate: 24000,
  channels: 1,
  format: AudioFormat.int16,
);

// Stream chunks directly
output.stream.add(audioChunk);
```

**Pros:**
- Explicitly designed for real-time streaming
- Stream-based API is familiar

**Cons:**
- Less documentation/examples
- Need to verify maturity

---

### 3. **flutter_sound** 

**Why:** Can play from Dart streams (though may not be true raw PCM)

**Features:**
- ✅ Supports playback from Dart streams
- ✅ Cross-platform
- ✅ Well-maintained
- ⚠️ May still require some buffering

**Pub.dev:** https://pub.dev/packages/flutter_sound

**Pros:**
- Popular, well-documented
- Cross-platform support
- Active maintenance

**Cons:**
- May still batch internally (need to test)
- API designed more for file/URL playback

---

### 4. **socket_audiostream** (Windows-specific)

**Why:** Windows-specific plugin using native Media Foundation API

**Features:**
- ✅ Windows-specific (low-level)
- ✅ Low-latency
- ✅ Real-time streaming
- ✅ Built-in AEC, NS, AGC

**Pub.dev:** https://pub.dev/packages/socket_audiostream

**Pros:**
- True low-level Windows API
- Designed for real-time streaming

**Cons:**
- Windows only (not cross-platform)
- Less generic (socket-focused)

---

### 5. **Custom Platform Channel** (Advanced)

**Why:** Direct access to Windows audio APIs (WASAPI)

**Implementation:**
- Use `dart:ffi` to call Windows audio APIs directly
- Or create custom plugin with Windows native code

**Pros:**
- Full control
- True streaming
- Same level as Python sounddevice

**Cons:**
- Most complex
- Requires Windows C++ development
- Maintenance burden

---

## Recommendation

**Best Option: `mp_audio_stream`**

**Reasoning:**
1. Explicitly designed for raw PCM streaming (our exact use case)
2. Uses miniaudio (proven low-level audio library)
3. Simple API similar to sounddevice's `write()` method
4. Multi-platform support (Windows included)

**Migration Strategy:**
1. Add `mp_audio_stream` to `pubspec.yaml`
2. Create new `AudioStreamPlaybackService` using `mp_audio_stream`
3. Replace current file-based approach with direct PCM streaming
4. Keep `audioplayers` as fallback for non-Windows if needed

**Fallback:** If `mp_audio_stream` doesn't work well, try `audio_io` next.

---

## Implementation Plan

### Step 1: Add Package
```yaml
dependencies:
  mp_audio_stream: ^0.2.0  # Check latest version
```

### Step 2: Create Streaming Service
```dart
class AudioStreamPlaybackService {
  AudioStreamPlayer? _player;
  
  Future<void> initialize() {
    _player = AudioStreamPlayer(
      sampleRate: 24000,
      channels: 1,
      format: AudioFormat.pcmInt16,
    );
  }
  
  void writePCMChunk(Uint8List chunk) {
    // Convert Uint8List to Int16List if needed
    final samples = chunk.buffer.asInt16List();
    _player?.write(samples);
  }
  
  void dispose() {
    _player?.dispose();
  }
}
```

### Step 3: Integrate
- Replace `AudioPlaybackService` with `AudioStreamPlaybackService`
- Remove WAV file creation
- Write chunks directly as they arrive

---

## Testing Plan

1. **Latency Test:** Measure time from chunk arrival to playback
2. **Gap Test:** Verify no gaps between chunks
3. **Multiple Turns:** Test multiple conversation turns
4. **Error Handling:** Test with varying chunk sizes/rates

---

## Notes

- Python client uses `sounddevice` which is a Python wrapper around PortAudio
- `mp_audio_stream` uses miniaudio (similar low-level approach)
- Both should provide similar performance
- The key is avoiding file creation and writing PCM directly

