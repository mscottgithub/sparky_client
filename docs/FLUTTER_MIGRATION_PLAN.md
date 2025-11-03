# ðŸš€ Sparky Flutter Client - Complete Migration Plan

**Version:** 1.0  
**Date:** November 2, 2025  
**Target:** Complete rewrite of PyQt6 client in Flutter/Dart  
**Goal:** Feature parity + cross-platform capability (Windows, macOS, Linux, iOS, Android)

---

## ðŸ“‹ Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Decisions: Client vs Server](#architecture-decisions)
3. [Technology Stack](#technology-stack)
4. [Wake Word Strategy](#wake-word-strategy)
5. [Phase-by-Phase Implementation](#implementation-phases)
6. [Feature Mapping: PyQt6 â†’ Flutter](#feature-mapping)
7. [Mitigation Strategies for Flutter Cons](#mitigation-strategies)
8. [Project Structure](#project-structure)
9. [Development Workflow](#development-workflow)
10. [Testing Strategy](#testing-strategy)
11. [Deployment Plan](#deployment-plan)

---

## ðŸ“Š Executive Summary

### Why This Migration Makes Sense Now

- âœ… **Timing:** Only 3 days of PyQt6 code (minimal sunk cost)
- âœ… **No users:** Zero disruption, clean slate
- âœ… **Multi-platform goal:** Mobile inevitably needed
- âœ… **Solo development:** Fast decisions, no coordination overhead
- âœ… **Backend unchanged:** All Python services stay as-is

### Expected Timeline

- **Week 1-2:** Core functionality (chat, WebSocket, audio)
- **Week 3:** System tray, wake words, advanced features
- **Week 4:** Polish, testing, documentation
- **Week 5+:** Feature expansion from enhancement PDF

### Key Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Wake word detection | Server-side microservice + FFI backup |
| App size bloat | Code splitting, lazy loading, compression |
| Audio latency | Use just_audio (best performance package) |
| Startup time | Lazy initialization, splash screen |
| Native feel | Platform-specific widgets, custom decorations |

---

## ðŸ—ï¸ Architecture Decisions: Client vs Server

### Critical Analysis: What Belongs Where?

#### ðŸ–¥ï¸ **MOVE TO SERVER** (Better Performance, Simpler Client)

These features are currently client-side but should be server-side:

1. **Voice Activity Detection (VAD)** â­ **PRIORITY**
   - **Current:** Client-side silence detection
   - **New:** Server-side VAD in orchestrator
   - **Why:** 
     - Reduces client complexity
     - Consistent behavior across all clients
     - Server has better CPU for processing
     - Easier to tune one place vs. every client
   - **Implementation:** Orchestrator uses `webrtcvad` or `silero-vad`

2. **Echo Cancellation** â­ **PRIORITY**
   - **Current:** Client subtracts AI voice from microphone
   - **New:** Server-side acoustic echo cancellation (AEC)
   - **Why:**
     - Complex signal processing better on server
     - Reference audio already on server (TTS output)
     - Client just streams raw audio
   - **Implementation:** Use `speexdsp` or `webrtc-audio-processing`

3. **Audio Preprocessing** (Optional but recommended)
   - **Current:** Basic gain/normalization on client
   - **New:** Server-side noise reduction, normalization
   - **Why:** Better quality, consistent across clients
   - **Implementation:** `noisereduce` library in Python

#### ðŸ“± **KEEP ON CLIENT** (Essential for UX)

1. **Wake Word Detection** â­ **CRITICAL**
   - **Why:** Must work offline, instant response, privacy
   - **Strategy:** See dedicated section below

2. **UI/UX State Management**
   - **Why:** Flutter's strength, immediate feedback

3. **Local Settings/Preferences**
   - **Why:** Persist across sessions, no server needed

4. **System Tray/Notifications**
   - **Why:** OS integration, client-specific

5. **Audio Playback**
   - **Why:** Direct to speakers, no network overhead

6. **Conversation Display/History**
   - **Why:** Instant rendering, offline access

#### ðŸ”„ **HYBRID** (Client + Server Collaboration)

1. **Conversation Management**
   - **Server:** Store full history, search, sync
   - **Client:** Cache recent messages, display, edit

2. **File Attachments**
   - **Client:** File picker, preview, compression
   - **Server:** Storage, processing, OCR

3. **Voice Recording**
   - **Client:** Capture from mic, basic buffering
   - **Server:** STT processing, VAD, echo cancellation

### Updated Architecture Diagram

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  FLUTTER CLIENT (Dart)                                  â”‚
â”‚                                                         â”‚
â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”            â”‚
â”‚  â”‚ Wake Word (FFI) â”‚  â”‚ UI/State Mgmt    â”‚            â”‚
â”‚  â”‚ - openWakeWord  â”‚  â”‚ - Provider/Bloc  â”‚            â”‚
â”‚  â”‚ - Local only    â”‚  â”‚ - Flutter widgetsâ”‚            â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜            â”‚
â”‚                                                         â”‚
â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”            â”‚
â”‚  â”‚ Audio I/O       â”‚  â”‚ System Tray      â”‚            â”‚
â”‚  â”‚ - Record mic    â”‚  â”‚ - Tray menu      â”‚            â”‚
â”‚  â”‚ - Play speaker  â”‚  â”‚ - Notifications  â”‚            â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜            â”‚
â”‚                                                         â”‚
â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”            â”‚
â”‚  â”‚ WebSocket Client                       â”‚            â”‚
â”‚  â”‚ - JSON messages                        â”‚            â”‚
â”‚  â”‚ - Binary audio chunks                  â”‚            â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜            â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                     â”‚
                     â”‚ ws://10.6.1.15:8006
                     â”‚
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  ORCHESTRATOR (Python) - ENHANCED                       â”‚
â”‚                                                         â”‚
â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”            â”‚
â”‚  â”‚ VAD Module      â”‚  â”‚ Echo Cancellationâ”‚            â”‚
â”‚  â”‚ - webrtcvad     â”‚  â”‚ - speexdsp       â”‚            â”‚
â”‚  â”‚ - Silence detectâ”‚  â”‚ - AEC processing â”‚            â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜            â”‚
â”‚                                                         â”‚
â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”            â”‚
â”‚  â”‚ Conversation Manager                   â”‚            â”‚
â”‚  â”‚ - History, search, state               â”‚            â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜            â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                     â”‚
        â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
        â”‚            â”‚            â”‚
        â–¼            â–¼            â–¼
   Whisper STT    LLM (Lexi)   TTS (XTTS/Higgs)
```

### Server-Side Changes Required

We need to enhance `sparky_orchestrator_ws.py` with:

1. **VAD Endpoint** (new functionality)
2. **Echo Cancellation** (new functionality)
3. **Audio preprocessing** (optional)
4. **Enhanced conversation management** (already exists, expand)

**Benefit:** Client becomes simpler, more focused on UI/UX.

---

## ðŸ› ï¸ Technology Stack

### Flutter Packages (Confirmed Compatible)

#### **Core Framework**
```yaml
dependencies:
  flutter:
    sdk: flutter
  
  # State Management (choose one)
  flutter_bloc: ^8.1.3        # Recommended - predictable, testable
  # OR
  provider: ^6.1.1            # Simpler alternative
  # OR  
  riverpod: ^2.4.9            # Most modern
```

**Recommendation:** Use `flutter_bloc` - best for complex state, excellent debugging, scales well.

#### **WebSocket & Network**
```yaml
  web_socket_channel: ^2.4.0   # Official WebSocket
  http: ^1.2.0                  # REST API calls (health checks)
```

#### **Audio I/O** â­ **CRITICAL - Low Latency Required**
```yaml
  # Recording
  record: ^5.0.4                # Best recording package (low latency)
  
  # Playback
  just_audio: ^0.9.36           # Best playback (streaming support)
  audioplayers: ^5.2.1          # Backup option
  
  # Processing
  audio: ^4.0.0                 # WAV manipulation if needed
```

**Why just_audio:** 
- Native platform audio (lowest latency)
- Streaming support (play as data arrives)
- Cross-platform consistency

#### **System Integration**
```yaml
  # System Tray & Window Management
  tray_manager: ^0.2.1          # Tray icon + menu
  window_manager: ^0.3.8        # Window control (hide/show)
  
  # Notifications
  local_notifier: ^0.1.5        # Native notifications
  
  # Hotkeys
  hotkey_manager: ^0.1.8        # Global hotkeys (ESC abort)
```

#### **UI Components**
```yaml
  # Rich Text
  flutter_markdown: ^0.6.18     # Markdown rendering
  flutter_syntax_view: ^4.0.0   # Code highlighting
  
  # Animations
  # (built into Flutter, no package needed)
  
  # Icons
  cupertino_icons: ^1.0.6       # iOS-style icons
```

#### **Storage & Persistence**
```yaml
  shared_preferences: ^2.2.2    # Settings storage
  path_provider: ^2.1.2         # File paths
  sqflite: ^2.3.2               # Local database (conversation cache)
```

#### **Utilities**
```yaml
  intl: ^0.19.0                 # Date/time formatting
  json_annotation: ^4.8.1       # JSON serialization
  build_runner: ^2.4.8          # Code generation
  freezed: ^2.4.6               # Immutable models
```

### Wake Word Detection Strategy

See dedicated section below for detailed implementation.

---

## ðŸŽ™ï¸ Wake Word Strategy

### The Challenge

- **openWakeWord** is Python-only
- Must run continuously (low power)
- Must be instant (<100ms response)
- Must work offline (no server dependency)

### Solution: Multi-Stage Approach

#### **Phase 1: Server-Side Wake Word (Immediate, Simple)** â­ **START HERE**

**Architecture:**
```
Flutter Client â†’ Stream audio continuously â†’ Python Wake Word Service
                                                    â†“
                                    "Wake word detected!" (WebSocket event)
                                                    â†“
                                    Flutter shows listening UI
```

**Implementation:**

1. **New Python Service:** `sparky_wakeword_service.py` (port 8011)
   ```python
   from fastapi import FastAPI, WebSocket
   import openwakeword
   from openwakeword.model import Model
   
   app = FastAPI()
   wake_model = Model(wakeword_models=["hey_sparky.tflite"])
   
   @app.websocket("/wake")
   async def wake_detection(websocket: WebSocket):
       await websocket.accept()
       while True:
           audio_chunk = await websocket.receive_bytes()
           # Process audio with openwakeword
           prediction = wake_model.predict(audio_chunk)
           if prediction["hey_sparky"] > 0.5:
               await websocket.send_json({"event": "wake_detected"})
   ```

2. **Flutter Client:**
   ```dart
   // Connect to wake word service
   final wakeChannel = WebSocketChannel.connect(
     Uri.parse('ws://10.6.1.15:8011/wake'),
   );
   
   // Stream microphone audio
   recordStream.listen((audioChunk) {
     wakeChannel.sink.add(audioChunk);
   });
   
   // Listen for wake events
   wakeChannel.stream.listen((message) {
     if (message['event'] == 'wake_detected') {
       setState(() => isListening = true);
     }
   });
   ```

**Pros:**
- âœ… Works immediately (reuse existing Python code)
- âœ… Easy to maintain (Python is familiar)
- âœ… Can update models without client rebuild
- âœ… Works on all platforms (client just streams audio)

**Cons:**
- âš ï¸ Network dependency (local network only)
- âš ï¸ Slightly higher latency (~50ms network overhead)
- âš ï¸ Continuous audio streaming (bandwidth)

**Optimization:**
- Use UDP instead of WebSocket for lower latency
- Compress audio before sending (opus codec)
- Only send audio when user is at computer (presence detection)

#### **Phase 2: Client-Side via FFI (1-2 Weeks Later)** â­ **FUTURE OPTIMIZATION**

**Use TensorFlow Lite in Flutter:**

```yaml
dependencies:
  tflite_flutter: ^0.10.4
```

**Implementation:**
```dart
import 'package:tflite_flutter/tflite_flutter.dart';

class WakeWordDetector {
  late Interpreter _interpreter;
  
  Future<void> init() async {
    _interpreter = await Interpreter.fromAsset('hey_sparky.tflite');
  }
  
  bool detect(Float32List audioChunk) {
    var output = List.filled(1, 0.0).reshape([1, 1]);
    _interpreter.run(audioChunk.reshape([1, 16000]), output);
    return output[0][0] > 0.5;  // Confidence threshold
  }
}
```

**Pros:**
- âœ… No network dependency
- âœ… Lowest possible latency (<10ms)
- âœ… Works offline
- âœ… Lower power (no network)

**Cons:**
- âš ï¸ Need to convert openWakeWord models to TFLite format
- âš ï¸ More complex client
- âš ï¸ Model updates require app rebuild

**Conversion Process:**
1. Export openWakeWord model to ONNX
2. Convert ONNX to TensorFlow SavedModel
3. Convert SavedModel to TFLite
4. Optimize for mobile (quantization)

#### **Phase 3: Native FFI (Optional, Advanced)**

If TFLite doesn't work well, use FFI to call C/C++ directly:

```dart
import 'dart:ffi' as ffi;

// Load native library
final DynamicLibrary nativeLib = DynamicLibrary.open('libwakeword.so');

// Define C function signature
typedef WakeWordDetectC = ffi.Int32 Function(
  ffi.Pointer<ffi.Float> audio,
  ffi.Int32 length,
);

typedef WakeWordDetectDart = int Function(
  ffi.Pointer<ffi.Float> audio,
  int length,
);

// Bind to Dart
final wakeDetect = nativeLib
    .lookup<ffi.NativeFunction<WakeWordDetectC>>('wake_word_detect')
    .asFunction<WakeWordDetectDart>();

// Use it
bool isWake = wakeDetect(audioPointer, audioLength) == 1;
```

**Requires:**
- C/C++ implementation of wake word detection
- Compile for each platform (Windows, Linux, macOS, iOS, Android)
- Much more complex

### **Recommendation: Start with Phase 1**

Phase 1 gets you working immediately. Optimize to Phase 2 later if needed. Phase 3 only if TFLite insufficient.

---

## ðŸ“… Phase-by-Phase Implementation

### **Phase 1: Foundation (Days 1-3)** â­ **START HERE**

**Goal:** Basic Flutter app that connects to orchestrator and exchanges text messages.

#### Day 1: Project Setup & Structure
- âœ… Install Flutter SDK (see separate guide)
- âœ… Create new Flutter project
- âœ… Set up project structure (see below)
- âœ… Configure dependencies
- âœ… Create initial UI skeleton

**Deliverable:** Empty app with proper structure

#### Day 2: WebSocket Connection
- âœ… Implement WebSocket client (Bloc pattern)
- âœ… Connect to orchestrator (`ws://10.6.1.15:8006/ws/conversation`)
- âœ… Send/receive JSON messages
- âœ… Handle connection states (connecting, connected, disconnected, error)
- âœ… Automatic reconnection with exponential backoff

**Deliverable:** App connects to orchestrator, sends/receives test messages

#### Day 3: Basic Chat UI
- âœ… Chat message display (ListView with bubbles)
- âœ… Text input field
- âœ… Send button
- âœ… Message timestamps
- âœ… User vs. Assistant styling
- âœ… Scrolling behavior (auto-scroll to bottom)

**Deliverable:** Working text chat (feature parity with PyQt6 text mode)

**Code Example - WebSocket Bloc:**
```dart
// lib/blocs/websocket/websocket_bloc.dart
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

class WebSocketBloc extends Bloc<WebSocketEvent, WebSocketState> {
  WebSocketChannel? _channel;
  
  WebSocketBloc() : super(WebSocketInitial()) {
    on<ConnectWebSocket>(_onConnect);
    on<SendMessage>(_onSendMessage);
    on<ReceiveMessage>(_onReceiveMessage);
    on<DisconnectWebSocket>(_onDisconnect);
  }
  
  void _onConnect(ConnectWebSocket event, Emitter<WebSocketState> emit) async {
    emit(WebSocketConnecting());
    
    try {
      _channel = WebSocketChannel.connect(
        Uri.parse('ws://10.6.1.15:8006/ws/conversation'),
      );
      
      // Listen for messages
      _channel!.stream.listen(
        (message) => add(ReceiveMessage(message)),
        onError: (error) => emit(WebSocketError(error.toString())),
        onDone: () => add(DisconnectWebSocket()),
      );
      
      // Send START message
      _channel!.sink.add(json.encode({
        'type': 'start',
        'voice': 'ara',
        'session_id': null,
      }));
      
      emit(WebSocketConnected());
    } catch (e) {
      emit(WebSocketError(e.toString()));
    }
  }
  
  // ... rest of handlers
}
```

### **Phase 2: Audio Integration (Days 4-7)**

**Goal:** Voice recording and playback working.

#### Day 4: Audio Recording
- âœ… Implement microphone recording (`record` package)
- âœ… Stream audio chunks to orchestrator
- âœ… Handle permissions (Windows, mobile)
- âœ… Visual feedback (microphone level indicator)

#### Day 5: Audio Playback
- âœ… Implement audio playback (`just_audio` package)
- âœ… Receive audio from orchestrator
- âœ… Stream playback (play as data arrives)
- âœ… Visual feedback (TTS progress indicator)

#### Day 6: Voice Activity Detection
- âœ… Option A: Use server-side VAD (recommended)
- âœ… Option B: Implement simple client-side VAD (silence detection)
- âœ… Start/stop recording automatically
- âœ… Manual mode (push-to-talk) as fallback

#### Day 7: Integration & Testing
- âœ… Full voice pipeline: Record â†’ Transcribe â†’ LLM â†’ TTS â†’ Playback
- âœ… Test on actual hardware
- âœ… Optimize buffer sizes for latency
- âœ… Handle edge cases (no mic, no audio device)

**Deliverable:** Voice chat working (feature parity with PyQt6 voice mode)

**Code Example - Audio Recording:**
```dart
// lib/services/audio_recorder.dart
import 'package:record/record.dart';

class AudioRecorderService {
  final _recorder = Record();
  StreamSubscription? _subscription;
  
  Future<void> startRecording(Function(Uint8List) onAudioChunk) async {
    if (await _recorder.hasPermission()) {
      final stream = await _recorder.startStream(
        RecordConfig(
          encoder: AudioEncoder.pcm16bit,
          sampleRate: 16000,
          numChannels: 1,
        ),
      );
      
      _subscription = stream.listen(onAudioChunk);
    }
  }
  
  Future<void> stopRecording() async {
    await _recorder.stop();
    await _subscription?.cancel();
  }
}
```

### **Phase 3: System Tray & Wake Words (Days 8-10)**

**Goal:** App runs in system tray with wake word detection.

#### Day 8: System Tray
- âœ… Implement system tray icon (`tray_manager`)
- âœ… Tray menu (Show, Hide, Settings, Quit)
- âœ… Hide to tray on close
- âœ… Show from tray on wake word
- âœ… Tray icon states (idle, listening, speaking)

#### Day 9: Window Management
- âœ… Hide/show window programmatically
- âœ… Always-on-top mode (during conversation)
- âœ… Focus management
- âœ… Minimize to tray behavior

#### Day 10: Wake Word Integration
- âœ… Implement Phase 1 wake word strategy (server-side)
- âœ… Continuous audio streaming to wake service
- âœ… Show window on wake detection
- âœ… Exit word detection ("Hey Mycroft")
- âœ… Visual feedback (tray icon animation)

**Deliverable:** Full tray app experience with wake words

**Code Example - System Tray:**
```dart
// lib/services/tray_service.dart
import 'package:tray_manager/tray_manager.dart';

class TrayService with TrayListener {
  Future<void> init() async {
    await trayManager.setIcon('assets/icons/tray_idle.png');
    
    Menu menu = Menu(items: [
      MenuItem(
        key: 'show',
        label: 'Show Sparky',
      ),
      MenuItem.separator(),
      MenuItem(
        key: 'settings',
        label: 'Settings',
      ),
      MenuItem.separator(),
      MenuItem(
        key: 'exit',
        label: 'Exit',
      ),
    ]);
    
    await trayManager.setContextMenu(menu);
    trayManager.addListener(this);
  }
  
  @override
  void onTrayIconMouseDown() {
    // Show window
    windowManager.show();
  }
  
  @override
  void onTrayMenuItemClick(MenuItem menuItem) {
    switch (menuItem.key) {
      case 'show':
        windowManager.show();
        break;
      case 'settings':
        // Show settings dialog
        break;
      case 'exit':
        windowManager.destroy();
        break;
    }
  }
}
```

### **Phase 4: Advanced Features (Days 11-14)**

**Goal:** Feature parity + polish.

#### Day 11: Conversation Management
- âœ… Conversation history persistence (SQLite)
- âœ… Multiple conversations (tabs/sessions)
- âœ… Search conversations
- âœ… Export conversation (Markdown, PDF)

#### Day 12: Settings & Preferences
- âœ… Settings dialog
- âœ… Voice selection (Ara, Alex, etc.)
- âœ… Theme selection (light/dark)
- âœ… Server configuration
- âœ… Audio device selection
- âœ… Hotkey configuration

#### Day 13: Polish & UX
- âœ… Loading states
- âœ… Error handling
- âœ… Animations (smooth transitions)
- âœ… Keyboard shortcuts
- âœ… Accessibility (screen reader support)

#### Day 14: Testing & Bug Fixes
- âœ… End-to-end testing
- âœ… Performance optimization
- âœ… Memory leak checks
- âœ… Stress testing (long conversations)

**Deliverable:** Production-ready Flutter client

### **Phase 5: Enhancement Features (Week 3+)**

Implement features from enhancement PDF:

- âœ… Service health dashboard
- âœ… Markdown rendering
- âœ… Code syntax highlighting
- âœ… Personality presets
- âœ… Prompt library
- âœ… File attachments
- âœ… Screenshot capture + OCR
- âœ… Debug console
- âœ… Performance metrics

---

## ðŸ—ºï¸ Feature Mapping: PyQt6 â†’ Flutter

### Complete Feature Inventory

| Feature | PyQt6 Implementation | Flutter Package | Complexity | Notes |
|---------|---------------------|-----------------|------------|-------|
| **System Tray** | `pystray` | `tray_manager` | Medium | Windows-specific tweaks needed |
| **Tray Icon States** | PIL image generation | Pre-rendered PNGs | Low | Create icon set beforehand |
| **Tray Menu** | `pystray.Menu` | `tray_manager.Menu` | Low | Direct mapping |
| **Window Show/Hide** | PyQt6 `show()`/`hide()` | `window_manager` | Low | Cross-platform consistent |
| **WebSocket** | `websockets` library | `web_socket_channel` | Low | Almost identical API |
| **Text Chat UI** | `QTextEdit` | `ListView` + `TextField` | Low | Flutter easier actually |
| **Message Bubbles** | Custom QTextEdit formatting | `Container` widgets | Low | More flexible in Flutter |
| **Audio Recording** | `sounddevice` | `record` package | Medium | Different API, similar concept |
| **Audio Playback** | `sounddevice` | `just_audio` | Medium | Streaming support better |
| **Wake Word** | `openwakeword` | Server-side + FFI | High | See wake word strategy |
| **VAD** | Client-side silence detection | Server-side (better) | Medium | Architecture change |
| **Echo Cancellation** | Client-side subtraction | Server-side (better) | High | Architecture change |
| **Hotkeys (ESC)** | `pynput` | `hotkey_manager` | Medium | Cross-platform tricky |
| **Config File** | `configparser` (.ini) | `shared_preferences` | Low | JSON instead of INI |
| **Conversation History** | In-memory list | SQLite (`sqflite`) | Medium | Better persistence |
| **Markdown Rendering** | N/A (plain text) | `flutter_markdown` | Low | New feature, easy |
| **Auto-Calibration** | Custom algorithm | Server-side or keep | Medium | Simplify if server-side |
| **Multiple Input Modes** | Manual/VAD toggle | Same concept | Low | Direct port |
| **Emergency Abort** | ESC key + voice | Same | Low | Direct port |
| **Settings Dialog** | N/A | Flutter dialog | Low | New feature |
| **Theme Switching** | N/A | `ThemeData` | Low | Built-in to Flutter |
| **Notifications** | Windows toast | `local_notifier` | Low | Better in Flutter |

### Priority Order

**Week 1 (Must Have):**
1. WebSocket connection
2. Text chat UI
3. Audio recording
4. Audio playback
5. Basic tray icon

**Week 2 (Important):**
6. System tray menu
7. Window management
8. Wake word (server-side)
9. VAD (server-side)
10. Settings storage

**Week 3 (Nice to Have):**
11. Conversation persistence
12. Multiple conversations
13. Hotkeys
14. Markdown rendering
15. Themes

**Week 4+ (Enhancements):**
16. Service health dashboard
17. Export conversations
18. Personality presets
19. Prompt library
20. File attachments

---

## ðŸ›¡ï¸ Mitigation Strategies for Flutter Cons

### Con #1: Large App Size (20-150 MB)

**Problem:** Flutter apps are larger than native/PyQt6.

**Mitigations:**

1. **Code Splitting** (reduces initial download)
   ```dart
   // Lazy load features
   import 'package:flutter/widgets.dart';
   
   Widget loadFeature(String name) {
     return DeferredWidget(
       () => import('package:sparky/features/$name.dart'),
     );
   }
   ```

2. **Tree Shaking** (removes unused code)
   ```bash
   flutter build windows --release --split-debug-info=./symbols --obfuscate
   ```
   - Removes unused widgets (~30% size reduction)

3. **Asset Optimization**
   - Use vector icons (SVG) instead of PNG
   - Compress images (TinyPNG)
   - Use WebP format for photos

4. **Remove Unused Dependencies**
   ```bash
   flutter pub deps --json | grep unused
   ```

5. **Platform-Specific Builds**
   - Don't include iOS/Android frameworks in desktop build
   ```yaml
   # pubspec.yaml
   dependencies:
     some_mobile_package:
       platforms:
         - android
         - ios
   ```

**Expected Results:**
- Initial: ~150 MB
- After optimization: ~50-80 MB
- PyQt6 equivalent: ~30-50 MB

**Verdict:** 2x larger, but acceptable for desktop. Critical for mobile - will require ongoing optimization.

### Con #2: Startup Time (1-2 seconds)

**Problem:** Flutter engine initialization takes time.

**Mitigations:**

1. **Splash Screen** (mask the delay)
   ```dart
   // Show branded splash while loading
   import 'package:flutter_native_splash/flutter_native_splash.dart';
   
   void main() {
     WidgetsBinding widgetsBinding = WidgetsFlutterBinding.ensureInitialized();
     FlutterNativeSplash.preserve(widgetsBinding: widgetsBinding);
     
     runApp(MyApp());
     
     // Remove splash when ready
     FlutterNativeSplash.remove();
   }
   ```

2. **Lazy Initialization**
   ```dart
   // Don't load everything at startup
   class SparkyApp extends StatefulWidget {
     @override
     _SparkyAppState createState() => _SparkyAppState();
   }
   
   class _SparkyAppState extends State<SparkyApp> {
     late Future<void> _initFuture;
     
     @override
     void initState() {
       super.initState();
       _initFuture = _initialize();
     }
     
     Future<void> _initialize() async {
       // Load settings
       await Settings.load();
       // Connect WebSocket (in background)
       websocketBloc.add(ConnectWebSocket());
       // Don't wait for wake word model
     }
     
     @override
     Widget build(BuildContext context) {
       return FutureBuilder(
         future: _initFuture,
         builder: (context, snapshot) {
           if (snapshot.connectionState == ConnectionState.done) {
             return MainApp();
           }
           return SplashScreen();
         },
       );
     }
   }
   ```

3. **Background Service** (advanced - Windows only)
   - Keep Flutter app running in background
   - Tray icon shows/hides window
   - No startup delay after first launch

4. **Preload Assets**
   ```dart
   // Precache images
   @override
   void didChangeDependencies() {
     precacheImage(AssetImage('assets/avatar.png'), context);
     super.didChangeDependencies();
   }
   ```

**Expected Results:**
- Initial: 2-3 seconds (first launch)
- Optimized: 0.5-1 second
- PyQt6: 0.2-0.5 seconds

**Verdict:** Slightly slower, but acceptable with splash screen. Won't notice after first launch if backgrounded.

### Con #3: Memory Usage (200-400 MB)

**Problem:** Flutter uses more RAM than native.

**Mitigations:**

1. **Dispose Resources Properly**
   ```dart
   @override
   void dispose() {
     _controller.dispose();
     _scrollController.dispose();
     _focusNode.dispose();
     super.dispose();
   }
   ```

2. **Limit Rendered Messages**
   ```dart
   // Only render visible messages
   ListView.builder(
     itemCount: visibleMessages.length,  // Not all messages
     itemBuilder: (context, index) {
       return MessageBubble(visibleMessages[index]);
     },
   );
   ```

3. **Image Caching Strategy**
   ```dart
   // Limit cache size
   PaintingBinding.instance.imageCache.maximumSize = 100;
   PaintingBinding.instance.imageCache.maximumSizeBytes = 50 << 20; // 50 MB
   ```

4. **Stream Subscriptions**
   ```dart
   // Cancel streams when not needed
   late StreamSubscription _subscription;
   
   _subscription = stream.listen(...);
   
   @override
   void dispose() {
     _subscription.cancel();
     super.dispose();
   }
   ```

**Expected Results:**
- Initial: 300-400 MB
- Optimized: 150-250 MB
- PyQt6: 100-200 MB

**Verdict:** Higher, but not prohibitive. Modern systems have plenty of RAM. Will need monitoring.

### Con #4: Desktop UI Feel

**Problem:** Flutter widgets can feel "mobile-y" on desktop.

**Mitigations:**

1. **Platform-Aware Widgets**
   ```dart
   import 'dart:io';
   
   Widget buildButton() {
     if (Platform.isWindows || Platform.isLinux) {
       // Desktop style button
       return ElevatedButton(...);
     } else {
       // Mobile style button
       return CupertinoButton(...);
     }
   }
   ```

2. **Custom Window Decorations**
   ```dart
   // Remove default title bar, create custom
   await windowManager.setTitleBarStyle(TitleBarStyle.hidden);
   
   // Create custom title bar widget
   Container(
     height: 32,
     color: Colors.grey[900],
     child: Row(
       children: [
         // Logo, title
         Spacer(),
         // Minimize, maximize, close buttons (Windows style)
       ],
     ),
   );
   ```

3. **Desktop-Specific Interactions**
   ```dart
   // Right-click context menus
   GestureDetector(
     onSecondaryTapDown: (details) {
       showMenu(
         context: context,
         position: RelativeRect.fromLTRB(
           details.globalPosition.dx,
           details.globalPosition.dy,
           details.globalPosition.dx,
           details.globalPosition.dy,
         ),
         items: [
           PopupMenuItem(value: 'copy', child: Text('Copy')),
           PopupMenuItem(value: 'paste', child: Text('Paste')),
         ],
       );
     },
     child: child,
   );
   ```

4. **Keyboard Navigation**
   ```dart
   // Full keyboard shortcuts
   Shortcuts(
     shortcuts: {
       LogicalKeySet(LogicalKeyboardKey.control, LogicalKeyboardKey.keyN):
         NewConversationIntent(),
       LogicalKeySet(LogicalKeyboardKey.control, LogicalKeyboardKey.keyW):
         CloseWindowIntent(),
     },
     child: Actions(
       actions: {
         NewConversationIntent: CallbackAction(
           onInvoke: (_) => createNewConversation(),
         ),
       },
       child: child,
     ),
   );
   ```

5. **Fluent UI Package** (Windows-specific)
   ```yaml
   dependencies:
     fluent_ui: ^4.7.6  # Microsoft Fluent Design
   ```
   - Native Windows 11 look and feel
   - Acrylic backgrounds, modern controls

**Expected Result:** Near-native feel with effort. Won't fool power users, but good enough.

### Con #5: Wake Word Detection

**Problem:** openWakeWord is Python-only.

**Mitigation:** See dedicated wake word strategy section above.

**Summary:** Server-side initially, then TFLite optimization. Solved.

### Con #6: Python Library Ecosystem

**Problem:** Can't use Python packages directly.

**Mitigations:**

1. **Server-Side Processing** â­ **PRIMARY STRATEGY**
   - Keep heavy Python logic on server
   - Client is thin UI layer
   - Example: OCR â†’ server-side, not client

2. **Dart Equivalents** (where they exist)
   - Most common operations have Dart packages
   - Example: HTTP, WebSocket, JSON, crypto, etc.

3. **Platform Channels / FFI** (last resort)
   - Call C/C++ libraries from Dart
   - Python â†’ C wrapper â†’ FFI â†’ Dart
   - Complex, but possible

**Expected Result:** 90% of features don't need Python on client. 10% use server or FFI.

### Con #7: Debugging Differences

**Problem:** Dart DevTools != Python debugger.

**Mitigations:**

1. **Learn Dart DevTools** (it's actually quite good)
   - Performance overlay (find slow widgets)
   - Widget inspector (see widget tree)
   - Network inspector (see WebSocket traffic)
   - Timeline (profiling)

2. **Extensive Logging**
   ```dart
   import 'package:logging/logging.dart';
   
   final log = Logger('WebSocketBloc');
   
   log.info('Connecting to server...');
   log.warning('Connection unstable');
   log.severe('Connection failed: $error');
   ```

3. **Crash Reporting**
   ```dart
   import 'package:flutter/foundation.dart';
   
   FlutterError.onError = (details) {
     log.severe('Flutter error', details.exception, details.stack);
     // Send to crash reporting service
   };
   ```

4. **Hot Reload** (makes debugging faster)
   - Fix bug, press 'r', see fix instantly
   - Much faster than Python restart cycle

**Expected Result:** Different, but not worse. Hot reload compensates for learning curve.

---

## ðŸ“‚ Project Structure

### Recommended Flutter Architecture

```
sparky_flutter_client/
â”œâ”€â”€ lib/
â”‚   â”œâ”€â”€ main.dart                    # App entry point
â”‚   â”‚
â”‚   â”œâ”€â”€ app.dart                     # App widget, theme, routing
â”‚   â”‚
â”‚   â”œâ”€â”€ blocs/                       # Business logic (BLoC pattern)
â”‚   â”‚   â”œâ”€â”€ websocket/
â”‚   â”‚   â”‚   â”œâ”€â”€ websocket_bloc.dart
â”‚   â”‚   â”‚   â”œâ”€â”€ websocket_event.dart
â”‚   â”‚   â”‚   â””â”€â”€ websocket_state.dart
â”‚   â”‚   â”‚
â”‚   â”‚   â”œâ”€â”€ conversation/
â”‚   â”‚   â”‚   â”œâ”€â”€ conversation_bloc.dart
â”‚   â”‚   â”‚   â”œâ”€â”€ conversation_event.dart
â”‚   â”‚   â”‚   â””â”€â”€ conversation_state.dart
â”‚   â”‚   â”‚
â”‚   â”‚   â”œâ”€â”€ audio/
â”‚   â”‚   â”‚   â”œâ”€â”€ audio_bloc.dart
â”‚   â”‚   â”‚   â”œâ”€â”€ audio_event.dart
â”‚   â”‚   â”‚   â””â”€â”€ audio_state.dart
â”‚   â”‚   â”‚
â”‚   â”‚   â””â”€â”€ settings/
â”‚   â”‚       â”œâ”€â”€ settings_bloc.dart
â”‚   â”‚       â”œâ”€â”€ settings_event.dart
â”‚   â”‚       â””â”€â”€ settings_state.dart
â”‚   â”‚
â”‚   â”œâ”€â”€ models/                      # Data models
â”‚   â”‚   â”œâ”€â”€ message.dart
â”‚   â”‚   â”œâ”€â”€ conversation.dart
â”‚   â”‚   â”œâ”€â”€ settings.dart
â”‚   â”‚   â””â”€â”€ audio_chunk.dart
â”‚   â”‚
â”‚   â”œâ”€â”€ repositories/                # Data layer
â”‚   â”‚   â”œâ”€â”€ websocket_repository.dart
â”‚   â”‚   â”œâ”€â”€ conversation_repository.dart
â”‚   â”‚   â””â”€â”€ settings_repository.dart
â”‚   â”‚
â”‚   â”œâ”€â”€ services/                    # Platform services
â”‚   â”‚   â”œâ”€â”€ audio_recorder.dart
â”‚   â”‚   â”œâ”€â”€ audio_player.dart
â”‚   â”‚   â”œâ”€â”€ tray_service.dart
â”‚   â”‚   â”œâ”€â”€ wake_word_service.dart
â”‚   â”‚   â””â”€â”€ notification_service.dart
â”‚   â”‚
â”‚   â”œâ”€â”€ widgets/                     # Reusable widgets
â”‚   â”‚   â”œâ”€â”€ message_bubble.dart
â”‚   â”‚   â”œâ”€â”€ chat_input.dart
â”‚   â”‚   â”œâ”€â”€ voice_indicator.dart
â”‚   â”‚   â””â”€â”€ loading_indicator.dart
â”‚   â”‚
â”‚   â”œâ”€â”€ screens/                     # Full screen views
â”‚   â”‚   â”œâ”€â”€ chat_screen.dart
â”‚   â”‚   â”œâ”€â”€ settings_screen.dart
â”‚   â”‚   â””â”€â”€ splash_screen.dart
â”‚   â”‚
â”‚   â”œâ”€â”€ utils/                       # Utilities
â”‚   â”‚   â”œâ”€â”€ constants.dart
â”‚   â”‚   â”œâ”€â”€ extensions.dart
â”‚   â”‚   â””â”€â”€ validators.dart
â”‚   â”‚
â”‚   â””â”€â”€ config/                      # Configuration
â”‚       â”œâ”€â”€ theme.dart
â”‚       â”œâ”€â”€ routes.dart
â”‚       â””â”€â”€ environment.dart
â”‚
â”œâ”€â”€ assets/                          # Static assets
â”‚   â”œâ”€â”€ icons/
â”‚   â”‚   â”œâ”€â”€ tray_idle.png
â”‚   â”‚   â”œâ”€â”€ tray_listening.png
â”‚   â”‚   â””â”€â”€ tray_speaking.png
â”‚   â”œâ”€â”€ images/
â”‚   â””â”€â”€ wake_models/
â”‚       â””â”€â”€ hey_sparky.tflite
â”‚
â”œâ”€â”€ test/                            # Unit tests
â”‚   â”œâ”€â”€ blocs/
â”‚   â”œâ”€â”€ services/
â”‚   â””â”€â”€ widgets/
â”‚
â”œâ”€â”€ integration_test/                # Integration tests
â”‚   â””â”€â”€ app_test.dart
â”‚
â”œâ”€â”€ windows/                         # Windows-specific code
â”œâ”€â”€ linux/                           # Linux-specific code
â”œâ”€â”€ macos/                           # macOS-specific code
â”œâ”€â”€ ios/                            # iOS-specific code (future)
â”œâ”€â”€ android/                        # Android-specific code (future)
â”‚
â”œâ”€â”€ pubspec.yaml                     # Dependencies
â””â”€â”€ README.md
```

### Key Architectural Decisions

**1. BLoC Pattern** (Business Logic Component)
- Separates UI from business logic
- Testable, predictable
- Scales well

**2. Repository Pattern**
- Abstracts data sources
- Easy to swap implementations
- Mockable for testing

**3. Service Layer**
- Platform-specific code isolated
- FFI / native code here

**4. Feature-First Organization** (alternative)
Could organize by feature instead:
```
lib/
â”œâ”€â”€ features/
â”‚   â”œâ”€â”€ chat/
â”‚   â”‚   â”œâ”€â”€ bloc/
â”‚   â”‚   â”œâ”€â”€ widgets/
â”‚   â”‚   â””â”€â”€ screens/
â”‚   â”œâ”€â”€ audio/
â”‚   â””â”€â”€ settings/
â””â”€â”€ core/
    â”œâ”€â”€ services/
    â”œâ”€â”€ utils/
    â””â”€â”€ models/
```

**Recommendation:** Start with structure above, refactor to feature-first if codebase grows large (>10k lines).

---

## ðŸ”„ Development Workflow

### Daily Development Process

1. **Start Services** (Orchestrator, Whisper, TTS, LLM)
   ```bash
   # On Linux server
   sudo systemctl start sparky-orchestrator
   sudo systemctl start sparky-whisper
   sudo systemctl start sparky-voice-tts
   sudo systemctl start higgs-local-server
   ```

2. **Run Flutter in Debug Mode**
   ```bash
   # On Windows
   cd sparky_flutter_client
   flutter run -d windows
   ```
   - Hot reload: Press `r`
   - Hot restart: Press `R`
   - Quit: Press `q`

3. **Make Changes**
   - Edit code in VS Code / Android Studio
   - Press `r` to see changes instantly

4. **Test on Target Platform**
   ```bash
   # Build release version
   flutter build windows --release
   
   # Run release build
   ./build/windows/runner/Release/sparky_flutter_client.exe
   ```

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/chat-ui

# Make commits
git add .
git commit -m "feat: implement chat message bubbles"

# Push to remote
git push origin feature/chat-ui

# Merge to main when ready
git checkout main
git merge feature/chat-ui
```

### Version Numbering

Use semantic versioning:
- `1.0.0` - Initial Flutter release (feature parity with PyQt6)
- `1.1.0` - Minor feature additions
- `1.0.1` - Bug fixes
- `2.0.0` - Major changes (mobile support)

---

## ðŸ§ª Testing Strategy

### Unit Tests

Test individual components:

```dart
// test/blocs/websocket_bloc_test.dart
import 'package:flutter_test/flutter_test.dart';
import 'package:bloc_test/bloc_test.dart';

void main() {
  group('WebSocketBloc', () {
    late WebSocketBloc bloc;
    
    setUp(() {
      bloc = WebSocketBloc();
    });
    
    tearDown(() {
      bloc.close();
    });
    
    test('initial state is WebSocketInitial', () {
      expect(bloc.state, isA<WebSocketInitial>());
    });
    
    blocTest<WebSocketBloc, WebSocketState>(
      'emits [WebSocketConnecting, WebSocketConnected] when ConnectWebSocket is added',
      build: () => bloc,
      act: (bloc) => bloc.add(ConnectWebSocket()),
      expect: () => [
        isA<WebSocketConnecting>(),
        isA<WebSocketConnected>(),
      ],
    );
  });
}
```

**Run tests:**
```bash
flutter test
```

### Widget Tests

Test UI components:

```dart
// test/widgets/message_bubble_test.dart
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('MessageBubble displays text', (WidgetTester tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: MessageBubble(
            message: Message(
              role: 'user',
              content: 'Hello, Sparky!',
            ),
          ),
        ),
      ),
    );
    
    expect(find.text('Hello, Sparky!'), findsOneWidget);
  });
}
```

### Integration Tests

Test full workflows:

```dart
// integration_test/app_test.dart
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();
  
  testWidgets('full chat flow', (WidgetTester tester) async {
    // Launch app
    await tester.pumpWidget(MyApp());
    await tester.pumpAndSettle();
    
    // Find text input
    final textField = find.byType(TextField);
    
    // Type message
    await tester.enterText(textField, 'Hello Sparky');
    await tester.pumpAndSettle();
    
    // Tap send button
    final sendButton = find.byIcon(Icons.send);
    await tester.tap(sendButton);
    await tester.pumpAndSettle();
    
    // Verify message appears
    expect(find.text('Hello Sparky'), findsOneWidget);
    
    // Wait for AI response (with timeout)
    await tester.pumpAndSettle(Duration(seconds: 5));
    
    // Verify AI responded
    expect(find.textContaining('Hello'), findsAtLeastNWidgets(2));
  });
}
```

**Run integration tests:**
```bash
flutter test integration_test/
```

### Manual Testing Checklist

Before each release:

- [ ] Text chat works (send message, receive response)
- [ ] Voice chat works (record, transcribe, respond, play audio)
- [ ] Wake word detection works (server-side or TFLite)
- [ ] Exit word detection works
- [ ] System tray shows/hides correctly
- [ ] Tray menu items work
- [ ] Settings persist across restarts
- [ ] Multiple conversations work
- [ ] Reconnection works after network loss
- [ ] Emergency abort (ESC) works
- [ ] Markdown renders correctly
- [ ] No memory leaks (run for 1 hour)
- [ ] Performance acceptable on low-end hardware

---

## ðŸš€ Deployment Plan

### Windows Distribution

**Option 1: Portable EXE (Recommended for Now)**

```bash
# Build release
flutter build windows --release

# Result at:
build/windows/runner/Release/

# Contents:
sparky_flutter_client.exe        # Main executable
flutter_windows.dll               # Flutter runtime
data/                            # Assets, fonts, etc.
```

**Distribution:**
- Zip the entire Release folder
- Users extract and run .exe
- No installer needed

**Pros:**
- âœ… Simple, fast
- âœ… No admin rights required
- âœ… Easy updates (replace folder)

**Cons:**
- âš ï¸ Larger download (includes all dependencies)
- âš ï¸ No Start menu integration
- âš ï¸ No auto-update

**Option 2: MSIX Installer (Future)**

```bash
# Install MSIX builder
flutter pub global activate msix

# Build MSIX package
flutter pub run msix:create

# Result:
build/windows/runner/Release/sparky_flutter_client.msix
```

**Distribution:**
- Upload to Microsoft Store (optional)
- Or distribute MSIX directly

**Pros:**
- âœ… Professional installer
- âœ… Start menu integration
- âœ… Automatic updates via Store

**Cons:**
- âš ï¸ Requires code signing certificate ($100-500/year)
- âš ï¸ More complex setup

**Recommendation:** Start with Option 1 (portable), move to Option 2 when ready for wider distribution.

### Auto-Update Strategy

**Phase 1: Manual Updates**
- GitHub Releases with zipped builds
- Users download and replace manually

**Phase 2: In-App Update Notification**
```dart
// Check GitHub API for latest release
Future<void> checkForUpdates() async {
  final response = await http.get(
    Uri.parse('https://api.github.com/repos/you/sparky/releases/latest'),
  );
  final latestVersion = json.decode(response.body)['tag_name'];
  
  if (latestVersion != currentVersion) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Update Available'),
        content: Text('Version $latestVersion is available!'),
        actions: [
          TextButton(
            onPressed: () => launchUrl('https://github.com/.../releases/latest'),
            child: Text('Download'),
          ),
        ],
      ),
    );
  }
}
```

**Phase 3: Auto-Update (Advanced)**
- Use `flutter_updater` package
- Download, verify, and install automatically
- Requires code signing

### Linux Distribution

**AppImage (Recommended)**
```bash
flutter build linux --release

# Package as AppImage
# (requires additional tooling - appimagetool)
```

**Or Snap Package:**
```bash
snapcraft
```

### Mobile Distribution (Future)

**iOS:**
1. Build: `flutter build ios --release`
2. Open in Xcode
3. Upload to App Store Connect
4. Submit for review

**Android:**
1. Build: `flutter build apk --release`
2. Sign with keystore
3. Upload to Google Play Console
4. Submit for review

---

## ðŸ“š Additional Documentation Needed

### For Developers

1. **CONTRIBUTING.md** - How to contribute code
2. **ARCHITECTURE.md** - Deep dive into architecture
3. **API.md** - Orchestrator API documentation
4. **DEBUGGING.md** - Common issues and solutions

### For Users

1. **README.md** - Quick start guide
2. **USER_GUIDE.md** - Full user manual
3. **FAQ.md** - Frequently asked questions
4. **TROUBLESHOOTING.md** - Common problems

---

## ðŸŽ¯ Success Criteria

### Phase 1 Complete When:
- âœ… Text chat works (send/receive messages)
- âœ… Can connect to orchestrator
- âœ… Basic UI looks good

### Phase 2 Complete When:
- âœ… Voice recording works
- âœ… Audio playback works
- âœ… Full voice conversation flow functional

### Phase 3 Complete When:
- âœ… System tray works
- âœ… Wake word detection works
- âœ… Can hide/show window

### Phase 4 Complete When:
- âœ… Settings persist
- âœ… Conversation history saves
- âœ… No major bugs
- âœ… Performance acceptable

### Ready for Release When:
- âœ… All Phase 1-4 complete
- âœ… 8+ hours of stress testing
- âœ… Documentation written
- âœ… Installer/distribution ready

---

## ðŸš¨ Risk Management

### High Risk Items

1. **Wake Word Performance**
   - **Risk:** TFLite model doesn't work well
   - **Mitigation:** Server-side fallback always available
   - **Probability:** Medium
   - **Impact:** High

2. **Audio Latency**
   - **Risk:** Flutter audio too slow for real-time
   - **Mitigation:** Use just_audio (native), optimize buffer sizes
   - **Probability:** Low
   - **Impact:** High

3. **Platform-Specific Bugs**
   - **Risk:** Works on Windows, broken on Linux
   - **Mitigation:** Test on all platforms regularly
   - **Probability:** Medium
   - **Impact:** Medium

### Medium Risk Items

4. **Learning Curve**
   - **Risk:** Dart/Flutter takes longer to learn than expected
   - **Mitigation:** Start simple, iterate
   - **Probability:** High
   - **Impact:** Low (just takes time)

5. **Memory Leaks**
   - **Risk:** App uses too much RAM over time
   - **Mitigation:** Proper disposal, profiling
   - **Probability:** Medium
   - **Impact:** Medium

### Low Risk Items

6. **UI Not "Native" Enough**
   - **Risk:** Desktop users complain about mobile feel
   - **Mitigation:** Custom widgets, platform detection
   - **Probability:** Low
   - **Impact:** Low

---

## ðŸ“ž Next Steps

1. **Read Windows setup guide** (separate document)
2. **Install Flutter SDK**
3. **Create new Flutter project**
4. **Start Phase 1 implementation**
5. **Check in after Week 1** (review progress, adjust plan)

---

## ðŸ“ Appendix: Server-Side Changes

### Orchestrator Enhancements Needed

These features should be added to `sparky_orchestrator_ws.py`:

#### 1. Voice Activity Detection (VAD)

```python
# Add to orchestrator
import webrtcvad

vad = webrtcvad.Vad(3)  # Aggressiveness 0-3

@app.websocket("/ws/conversation")
async def conversation(ws: WebSocket):
    # ... existing code ...
    
    # When receiving audio
    audio_chunk = await ws.receive_bytes()
    
    # VAD check
    is_speech = vad.is_speech(audio_chunk, sample_rate=16000)
    
    if is_speech:
        # Forward to Whisper
        pass
    else:
        # Silence detected, maybe end of utterance
        pass
```

#### 2. Echo Cancellation (AEC)

```python
# Add to orchestrator
from speexdsp import EchoCanceller

aec = EchoCanceller(frame_size=160, filter_length=1024, sample_rate=16000)

@app.websocket("/ws/conversation")
async def conversation(ws: WebSocket):
    # ... existing code ...
    
    # When receiving audio from mic
    mic_audio = await ws.receive_bytes()
    
    # When sending TTS audio to client
    tts_audio = await tts_service.synthesize(text)
    
    # Cancel echo
    clean_audio = aec.process(rec=mic_audio, play=tts_audio)
    
    # Forward clean audio to Whisper
```

#### 3. Wake Word Service (New Service)

Create `sparky_wakeword_service.py`:

```python
from fastapi import FastAPI, WebSocket
from openwakeword.model import Model
import numpy as np

app = FastAPI()

# Load wake word models
wake_model = Model(wakeword_models=[
    "hey_jarvis.tflite",
    "hey_mycroft.tflite"
])

@app.websocket("/wake")
async def wake_detection(ws: WebSocket):
    await ws.accept()
    
    while True:
        # Receive audio chunk (16kHz, 16-bit PCM)
        audio_bytes = await ws.receive_bytes()
        audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
        
        # Run prediction
        prediction = wake_model.predict(audio_array)
        
        # Check thresholds
        if prediction["hey_jarvis"] > 0.5:
            await ws.send_json({"event": "wake_detected", "word": "jarvis"})
        
        if prediction["hey_mycroft"] > 0.5:
            await ws.send_json({"event": "exit_detected", "word": "mycroft"})
```

Run on port 8011:
```bash
uvicorn sparky_wakeword_service:app --host 0.0.0.0 --port 8011
```

---

## ðŸŽ‰ Conclusion

This migration plan provides a complete roadmap from PyQt6 to Flutter. Key points:

1. **Start with server-side simplifications** (VAD, echo cancellation)
2. **Build client in phases** (text â†’ audio â†’ tray â†’ polish)
3. **Use proven packages** (just_audio, record, tray_manager)
4. **Mitigate cons proactively** (size, startup, memory)
5. **Keep backend unchanged** (all Python services stay as-is)

**Estimated timeline:** 3-4 weeks to full feature parity, then ongoing enhancements.

**Risk level:** Low (given no users, server-side fallbacks, incremental approach)

**Reward:** Cross-platform client (5 platforms from one codebase), modern UI, future-proof.

Let's build this! ðŸš€
