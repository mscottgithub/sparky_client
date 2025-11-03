# ðŸš€ Sparky Flutter Client - Complete Migration Plan (v1.1)

**Version:** 1.1 (Updated with Adjustments)  
**Date:** November 2, 2025  
**Changes:** Added early audio testing, desktop UX from Day 1, memory profiling  
**Target:** Complete rewrite of PyQt6 client in Flutter/Dart  
**Goal:** Feature parity + cross-platform capability (Windows, macOS, Linux, iOS, Android)

---

## ðŸ“‹ **Version 1.1 Changes**

This version incorporates three critical improvements:

1. âš¡ **Early Audio Latency Testing** (Week 1 Day 3)
   - Test audio I/O before committing to Week 2
   - Catch Flutter audio issues early
   - Tune settings if latency >500ms

2. ðŸ–¥ï¸ **Desktop UX From Day 1** (Week 1 Day 2)
   - Right-click context menus
   - Full keyboard shortcuts
   - Native window decorations
   - Proper focus management

3. ðŸ§  **Memory Profiling** (Week 2 Day 5)
   - 30-minute stress test
   - Fix disposal issues early
   - Prevent memory leaks

---

## ðŸ“š Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Decisions: Client vs Server](#architecture-decisions)
3. [Technology Stack](#technology-stack)
4. [Wake Word Strategy](#wake-word-strategy)
5. [Phase-by-Phase Implementation (UPDATED)](#implementation-phases)
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

- **Week 1-2:** Core functionality (chat, WebSocket, audio + latency validation)
- **Week 3:** System tray, wake words, advanced features
- **Week 4:** Polish, testing, documentation
- **Week 5+:** Feature expansion from enhancement brainstorm

### Key Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Audio latency issues | âš¡ Test in Week 1 Day 3 (NEW) |
| Desktop feel | ðŸ–¥ï¸ Scaffold from Day 1 (NEW) |
| Memory leaks | ðŸ§  Profile in Week 2 Day 5 (NEW) |
| Wake word detection | Server-side microservice + FFI backup |
| App size bloat | Code splitting, lazy loading, compression |

---

## ðŸ——ï¸ Architecture Decisions: Client vs Server

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

---

## ðŸ› ï¸ Technology Stack

### Flutter Packages (Confirmed Compatible)

#### **Core Framework**
```yaml
dependencies:
  flutter:
    sdk: flutter
  
  # State Management
  flutter_riverpod: ^2.5.1    # Recommended - predictable, testable, less boilerplate
  riverpod_annotation: ^2.3.5 # Code generation for providers
```

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
   wake_model = Model(wakeword_models=["hey_jarvis.tflite", "hey_mycroft.tflite"])
   
   @app.websocket("/wake")
   async def wake_detection(ws: WebSocket):
       await ws.accept()
       
       while True:
           audio_bytes = await ws.receive_bytes()
           audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
           
           prediction = wake_model.predict(audio_array)
           
           if prediction["hey_jarvis"] > 0.5:
               await ws.send_json({"event": "wake_detected", "word": "jarvis"})
           
           if prediction["hey_mycroft"] > 0.5:
               await ws.send_json({"event": "exit_detected", "word": "mycroft"})
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

#### **Phase 2: Client-Side via TFLite (Future Optimization)**

Use TensorFlow Lite in Flutter:

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
    return output[0][0] > 0.5;
  }
}
```

---

## ðŸ“… Phase-by-Phase Implementation (UPDATED v1.1)

### **Phase 1: Foundation (Days 1-3)** â­ **REVISED**

**Goal:** Basic Flutter app with text chat + audio latency validation.

#### Day 1: Project Setup & Structure
- âœ… Install Flutter SDK (see separate guide)
- âœ… Create new Flutter project
- âœ… Set up project structure (Riverpod providers/services folders)
- âœ… Configure dependencies
- âœ… Create initial UI skeleton

**Deliverable:** Empty app with proper structure

#### Day 2: WebSocket Connection + Desktop UX Foundation âš¡ **NEW**
- âœ… Implement WebSocket client (Riverpod provider pattern)
- âœ… Connect to orchestrator (`ws://10.6.1.15:8006/ws/conversation`)
- âœ… Send/receive JSON messages
- âœ… Handle connection states (connecting, connected, disconnected, error)
- âœ… Automatic reconnection with exponential backoff
- âœ¨ **NEW: Desktop UX Foundation**
  - âœ… Right-click context menus (copy/paste/select all)
  - âœ… Keyboard shortcuts:
    - Ctrl+C (copy)
    - Ctrl+V (paste)
    - Ctrl+X (cut)
    - Ctrl+A (select all)
    - Ctrl+Z (undo)
  - âœ… Native window decorations (custom title bar with min/max/close)
  - âœ… Tab navigation between input elements
  - âœ… Focus management (cursor in text field on window show)

**Deliverable:** App connects to orchestrator, sends/receives messages, feels desktop-native

**Code Example - Right-Click Menu:**
```dart
// lib/widgets/desktop_text_field.dart
class DesktopTextField extends StatelessWidget {
  final TextEditingController controller;
  
  @override
  Widget build(BuildContext context) {
    return GestureDetector(
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
            PopupMenuItem(
              value: 'copy',
              child: Row(
                children: [
                  Icon(Icons.copy, size: 18),
                  SizedBox(width: 8),
                  Text('Copy'),
                  Spacer(),
                  Text('Ctrl+C', style: TextStyle(color: Colors.grey)),
                ],
              ),
            ),
            PopupMenuItem(
              value: 'paste',
              child: Row(
                children: [
                  Icon(Icons.paste, size: 18),
                  SizedBox(width: 8),
                  Text('Paste'),
                  Spacer(),
                  Text('Ctrl+V', style: TextStyle(color: Colors.grey)),
                ],
              ),
            ),
          ],
        ).then((value) {
          if (value == 'copy') {
            Clipboard.setData(ClipboardData(text: controller.selection.textInside(controller.text)));
          } else if (value == 'paste') {
            Clipboard.getData('text/plain').then((data) {
              if (data != null) {
                controller.text = controller.text.replaceRange(
                  controller.selection.start,
                  controller.selection.end,
                  data.text!,
                );
              }
            });
          }
        });
      },
      child: TextField(
        controller: controller,
        decoration: InputDecoration(hintText: 'Type message...'),
      ),
    );
  }
}
```

**Code Example - Keyboard Shortcuts:**
```dart
// lib/screens/chat_screen.dart
Shortcuts(
  shortcuts: {
    LogicalKeySet(LogicalKeyboardKey.control, LogicalKeyboardKey.keyC): CopyIntent(),
    LogicalKeySet(LogicalKeyboardKey.control, LogicalKeyboardKey.keyV): PasteIntent(),
    LogicalKeySet(LogicalKeyboardKey.control, LogicalKeyboardKey.keyX): CutIntent(),
    LogicalKeySet(LogicalKeyboardKey.control, LogicalKeyboardKey.keyA): SelectAllIntent(),
    LogicalKeySet(LogicalKeyboardKey.escape): AbortIntent(),
  },
  child: Actions(
    actions: {
      CopyIntent: CallbackAction<CopyIntent>(
        onInvoke: (intent) => _handleCopy(),
      ),
      PasteIntent: CallbackAction<PasteIntent>(
        onInvoke: (intent) => _handlePaste(),
      ),
      AbortIntent: CallbackAction<AbortIntent>(
        onInvoke: (intent) => _handleAbort(),
      ),
    },
    child: ChatView(),
  ),
)
```

#### Day 3: Basic Chat UI + Audio Latency Test âš¡ **CRITICAL NEW**
- âœ… Chat message display (ListView with bubbles)
- âœ… Text input field (with desktop context menu)
- âœ… Send button
- âœ… Message timestamps
- âœ… User vs. Assistant styling
- âœ… Scrolling behavior (auto-scroll to bottom)
- âœ¨ **NEW: Audio Latency Test** â­ **BLOCKER FOR WEEK 2**
  - âœ… Simple audio test screen
  - âœ… Record 2 seconds from microphone
  - âœ… Play back immediately
  - âœ… Measure end-to-end latency
  - âœ… Display latency in UI
  - âœ… **REQUIREMENT:** Must be <500ms to proceed to Week 2
  - âœ… If >500ms: Tune `record` package settings:
    - Reduce buffer size
    - Adjust sample rate
    - Test different audio encoders

**Deliverable:** Working text chat + audio latency validated (<500ms)

**Code Example - Audio Latency Test:**
```dart
// lib/screens/audio_test_screen.dart
class AudioTestScreen extends StatefulWidget {
  @override
  _AudioTestScreenState createState() => _AudioTestScreenState();
}

class _AudioTestScreenState extends State<AudioTestScreen> {
  final _recorder = Record();
  final _player = AudioPlayer();
  List<int> _recordedBytes = [];
  int? _latencyMs;
  
  Future<void> _runLatencyTest() async {
    setState(() {
      _latencyMs = null;
      _recordedBytes.clear();
    });
    
    final startTime = DateTime.now();
    
    // Record for 2 seconds
    final stream = await _recorder.startStream(
      RecordConfig(
        encoder: AudioEncoder.pcm16bit,
        sampleRate: 16000,
        numChannels: 1,
      ),
    );
    
    await for (final chunk in stream.take(32)) {  // ~2 seconds at 16kHz
      _recordedBytes.addAll(chunk);
    }
    
    await _recorder.stop();
    
    // Play back immediately
    final source = BytesSource(Uint8List.fromList(_recordedBytes));
    await _player.setAudioSource(source);
    await _player.play();
    
    final endTime = DateTime.now();
    final latency = endTime.difference(startTime).inMilliseconds;
    
    setState(() {
      _latencyMs = latency;
    });
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Audio Latency Test')),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text('Audio Latency Test', style: TextStyle(fontSize: 24)),
            SizedBox(height: 20),
            if (_latencyMs != null) ...[
              Text(
                '$_latencyMs ms',
                style: TextStyle(
                  fontSize: 48,
                  fontWeight: FontWeight.bold,
                  color: _latencyMs! < 500 ? Colors.green : Colors.red,
                ),
              ),
              SizedBox(height: 10),
              Text(
                _latencyMs! < 500 
                  ? 'âœ… PASS - Ready for Week 2'
                  : 'âŒ FAIL - Needs tuning',
                style: TextStyle(fontSize: 18),
              ),
            ],
            SizedBox(height: 40),
            ElevatedButton(
              onPressed: _runLatencyTest,
              child: Text('Run Test'),
            ),
          ],
        ),
      ),
    );
  }
}
```

---

### **Phase 2: Audio Integration (Days 4-7)** âš¡ **UPDATED**

**Goal:** Voice recording and playback working + memory stable.

#### Day 4: Audio Recording
- âœ… Implement microphone recording (`record` package)
- âœ… Stream audio chunks to orchestrator
- âœ… Handle permissions (Windows, mobile)
- âœ… Visual feedback (microphone level indicator)

#### Day 5: Audio Playback + Memory Profiling âš¡ **NEW**
- âœ… Implement audio playback (`just_audio` package)
- âœ… Receive audio from orchestrator
- âœ… Stream playback (play as data arrives)
- âœ… Visual feedback (TTS progress indicator)
- âœ¨ **NEW: Memory Profiling Session** â­ **CRITICAL**
  - âœ… Open Flutter DevTools (press 'd' in terminal)
  - âœ… Navigate to Memory tab
  - âœ… Baseline: Record memory usage at startup
  - âœ… Stress test: Send 100 messages over 30 minutes
  - âœ… Monitor: Watch memory graph for leaks (upward trend)
  - âœ… Snapshot: Take heap snapshot after test
  - âœ… Fix: Find and fix any `dispose()` issues
  - âœ… **REQUIREMENT:** Memory must be stable (no upward trend)

**Code Example - Memory Profiling:**
```dart
// Add this to your main.dart for debug mode
void main() {
  if (kDebugMode) {
    // Enable memory profiling
    debugPrint('Memory profiling enabled');
    
    // Log memory usage every minute
    Timer.periodic(Duration(minutes: 1), (_) {
      final usage = ProcessInfo.currentRss / (1024 * 1024);  // MB
      debugPrint('Memory usage: ${usage.toStringAsFixed(1)} MB');
    });
  }
  
  runApp(MyApp());
}
```

**DevTools Memory Profiling Steps:**
1. Run app in debug mode: `flutter run -d windows`
2. Press `d` in terminal to open DevTools
3. Go to Memory tab
4. Click "Reset" to baseline
5. Use app normally (send 100 messages)
6. Watch for upward trend in memory graph
7. If trend detected: Click "Snapshot" â†’ Find retained objects
8. Fix: Ensure all controllers/streams call `dispose()`

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
- âœ… Verify memory remains stable during long conversations

**Deliverable:** Voice chat working + memory stable (no leaks)

---

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

---

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
- âœ… Keyboard shortcuts (comprehensive)
- âœ… Accessibility (screen reader support)

#### Day 14: Testing & Bug Fixes
- âœ… End-to-end testing
- âœ… Performance optimization
- âœ… Memory leak checks (rerun profiler)
- âœ… Stress testing (long conversations)

**Deliverable:** Production-ready Flutter client

---

## âœ… Critical Success Checkpoints (UPDATED)

### **Week 1 Cannot Proceed Without:**
- âœ… WebSocket connection working
- âœ… Desktop UX foundation in place (right-click, keyboard shortcuts)
- âœ… Audio latency test passed (<500ms)

### **Week 2 Cannot Proceed Without:**
- âœ… Voice recording working
- âœ… Audio playback working
- âœ… Memory profiling shows stable usage (no leaks)

### **Week 3 Cannot Proceed Without:**
- âœ… System tray functional
- âœ… Wake word detection working

### **Week 4 Cannot Proceed Without:**
- âœ… All core features working
- âœ… No blocking bugs
- âœ… Performance acceptable

---

## ðŸŽ¯ Updated Success Criteria

**Week 1 Complete When:**
- âœ… Text chat works
- âœ… Feels desktop-native (right-click, shortcuts work)
- âœ… Audio latency <500ms (validated with test)

**Week 2 Complete When:**
- âœ… Voice chat works end-to-end
- âœ… Memory stable over 30+ minutes
- âœ… No `dispose()` issues

**Week 3 Complete When:**
- âœ… System tray works
- âœ… Wake word detection works
- âœ… Can hide/show window

**Week 4 Complete When:**
- âœ… Feature parity with PyQt6
- âœ… 8+ hours stress testing passed
- âœ… Production-ready

---

## ðŸ“ Updated Development Notes

### **New Rule: Test Early, Test Often**

1. **Audio latency:** Test on Day 3, not Day 7
2. **Memory usage:** Test on Day 5, not end of project
3. **Desktop UX:** Build from Day 2, not retrofit in Week 4

### **Why These Changes Matter:**

- **Audio latency test on Day 3** catches issues before Week 2 work
- **Desktop UX on Day 2** prevents "mobile on desktop" feel
- **Memory profiling on Day 5** finds leaks before they compound

---

## ðŸŽ‰ You're Ready to Start (v1.1)

The plan is now optimized for success with:
- âš¡ Early audio validation
- ðŸ–¥ï¸ Desktop-first approach
- ðŸ§  Proactive memory management

**Next step:** Follow FLUTTER_SETUP_WINDOWS11.md to install Flutter, then return here for Week 1, Day 1.

---

**Version:** 1.1  
**Status:** Ready to Execute  
**Estimated Timeline:** 4 weeks to production-ready client

Let's build this! ðŸš€
