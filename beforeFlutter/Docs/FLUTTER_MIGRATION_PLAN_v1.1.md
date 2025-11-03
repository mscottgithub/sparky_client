# 🚀 Sparky Flutter Client - Complete Migration Plan (v1.1)

**Version:** 1.1 (Updated with Adjustments)  
**Date:** November 2, 2025  
**Changes:** Added early audio testing, desktop UX from Day 1, memory profiling  
**Target:** Complete rewrite of PyQt6 client in Flutter/Dart  
**Goal:** Feature parity + cross-platform capability (Windows, macOS, Linux, iOS, Android)

---

## 📋 **Version 1.1 Changes**

This version incorporates three critical improvements:

1. ⚡ **Early Audio Latency Testing** (Week 1 Day 3)
   - Test audio I/O before committing to Week 2
   - Catch Flutter audio issues early
   - Tune settings if latency >500ms

2. 🖥️ **Desktop UX From Day 1** (Week 1 Day 2)
   - Right-click context menus
   - Full keyboard shortcuts
   - Native window decorations
   - Proper focus management

3. 🧠 **Memory Profiling** (Week 2 Day 5)
   - 30-minute stress test
   - Fix disposal issues early
   - Prevent memory leaks

---

## 📚 Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Decisions: Client vs Server](#architecture-decisions)
3. [Technology Stack](#technology-stack)
4. [Wake Word Strategy](#wake-word-strategy)
5. [Phase-by-Phase Implementation (UPDATED)](#implementation-phases)
6. [Feature Mapping: PyQt6 → Flutter](#feature-mapping)
7. [Mitigation Strategies for Flutter Cons](#mitigation-strategies)
8. [Project Structure](#project-structure)
9. [Development Workflow](#development-workflow)
10. [Testing Strategy](#testing-strategy)
11. [Deployment Plan](#deployment-plan)

---

## 📊 Executive Summary

### Why This Migration Makes Sense Now

- ✅ **Timing:** Only 3 days of PyQt6 code (minimal sunk cost)
- ✅ **No users:** Zero disruption, clean slate
- ✅ **Multi-platform goal:** Mobile inevitably needed
- ✅ **Solo development:** Fast decisions, no coordination overhead
- ✅ **Backend unchanged:** All Python services stay as-is

### Expected Timeline

- **Week 1-2:** Core functionality (chat, WebSocket, audio + latency validation)
- **Week 3:** System tray, wake words, advanced features
- **Week 4:** Polish, testing, documentation
- **Week 5+:** Feature expansion from enhancement brainstorm

### Key Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Audio latency issues | ⚡ Test in Week 1 Day 3 (NEW) |
| Desktop feel | 🖥️ Scaffold from Day 1 (NEW) |
| Memory leaks | 🧠 Profile in Week 2 Day 5 (NEW) |
| Wake word detection | Server-side microservice + FFI backup |
| App size bloat | Code splitting, lazy loading, compression |

---

## 🗗️ Architecture Decisions: Client vs Server

### Critical Analysis: What Belongs Where?

#### 🖥️ **MOVE TO SERVER** (Better Performance, Simpler Client)

These features are currently client-side but should be server-side:

1. **Voice Activity Detection (VAD)** ⭐ **PRIORITY**
   - **Current:** Client-side silence detection
   - **New:** Server-side VAD in orchestrator
   - **Why:** 
     - Reduces client complexity
     - Consistent behavior across all clients
     - Server has better CPU for processing
     - Easier to tune one place vs. every client
   - **Implementation:** Orchestrator uses `webrtcvad` or `silero-vad`

2. **Echo Cancellation** ⭐ **PRIORITY**
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

#### 📱 **KEEP ON CLIENT** (Essential for UX)

1. **Wake Word Detection** ⭐ **CRITICAL**
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

## 🛠️ Technology Stack

### Flutter Packages (Confirmed Compatible)

#### **Core Framework**
```yaml
dependencies:
  flutter:
    sdk: flutter
  
  # State Management
  flutter_bloc: ^8.1.3        # Recommended - predictable, testable
  equatable: ^2.0.5           # For BLoC states
```

#### **WebSocket & Network**
```yaml
  web_socket_channel: ^2.4.0   # Official WebSocket
  http: ^1.2.0                  # REST API calls (health checks)
```

#### **Audio I/O** ⭐ **CRITICAL - Low Latency Required**
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

## 🎙️ Wake Word Strategy

### The Challenge

- **openWakeWord** is Python-only
- Must run continuously (low power)
- Must be instant (<100ms response)
- Must work offline (no server dependency)

### Solution: Multi-Stage Approach

#### **Phase 1: Server-Side Wake Word (Immediate, Simple)** ⭐ **START HERE**

**Architecture:**
```
Flutter Client → Stream audio continuously → Python Wake Word Service
                                                    ↓
                                    "Wake word detected!" (WebSocket event)
                                                    ↓
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
- ✅ Works immediately (reuse existing Python code)
- ✅ Easy to maintain (Python is familiar)
- ✅ Can update models without client rebuild
- ✅ Works on all platforms (client just streams audio)

**Cons:**
- ⚠️ Network dependency (local network only)
- ⚠️ Slightly higher latency (~50ms network overhead)
- ⚠️ Continuous audio streaming (bandwidth)

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

## 📅 Phase-by-Phase Implementation (UPDATED v1.1)

### **Phase 1: Foundation (Days 1-3)** ⭐ **REVISED**

**Goal:** Basic Flutter app with text chat + audio latency validation.

#### Day 1: Project Setup & Structure
- ✅ Install Flutter SDK (see separate guide)
- ✅ Create new Flutter project
- ✅ Set up project structure (BLoC folders)
- ✅ Configure dependencies
- ✅ Create initial UI skeleton

**Deliverable:** Empty app with proper structure

#### Day 2: WebSocket Connection + Desktop UX Foundation ⚡ **NEW**
- ✅ Implement WebSocket client (BLoC pattern)
- ✅ Connect to orchestrator (`ws://10.6.1.15:8006/ws/conversation`)
- ✅ Send/receive JSON messages
- ✅ Handle connection states (connecting, connected, disconnected, error)
- ✅ Automatic reconnection with exponential backoff
- ✨ **NEW: Desktop UX Foundation**
  - ✅ Right-click context menus (copy/paste/select all)
  - ✅ Keyboard shortcuts:
    - Ctrl+C (copy)
    - Ctrl+V (paste)
    - Ctrl+X (cut)
    - Ctrl+A (select all)
    - Ctrl+Z (undo)
  - ✅ Native window decorations (custom title bar with min/max/close)
  - ✅ Tab navigation between input elements
  - ✅ Focus management (cursor in text field on window show)

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

#### Day 3: Basic Chat UI + Audio Latency Test ⚡ **CRITICAL NEW**
- ✅ Chat message display (ListView with bubbles)
- ✅ Text input field (with desktop context menu)
- ✅ Send button
- ✅ Message timestamps
- ✅ User vs. Assistant styling
- ✅ Scrolling behavior (auto-scroll to bottom)
- ✨ **NEW: Audio Latency Test** ⭐ **BLOCKER FOR WEEK 2**
  - ✅ Simple audio test screen
  - ✅ Record 2 seconds from microphone
  - ✅ Play back immediately
  - ✅ Measure end-to-end latency
  - ✅ Display latency in UI
  - ✅ **REQUIREMENT:** Must be <500ms to proceed to Week 2
  - ✅ If >500ms: Tune `record` package settings:
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
                  ? '✅ PASS - Ready for Week 2'
                  : '❌ FAIL - Needs tuning',
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

### **Phase 2: Audio Integration (Days 4-7)** ⚡ **UPDATED**

**Goal:** Voice recording and playback working + memory stable.

#### Day 4: Audio Recording
- ✅ Implement microphone recording (`record` package)
- ✅ Stream audio chunks to orchestrator
- ✅ Handle permissions (Windows, mobile)
- ✅ Visual feedback (microphone level indicator)

#### Day 5: Audio Playback + Memory Profiling ⚡ **NEW**
- ✅ Implement audio playback (`just_audio` package)
- ✅ Receive audio from orchestrator
- ✅ Stream playback (play as data arrives)
- ✅ Visual feedback (TTS progress indicator)
- ✨ **NEW: Memory Profiling Session** ⭐ **CRITICAL**
  - ✅ Open Flutter DevTools (press 'd' in terminal)
  - ✅ Navigate to Memory tab
  - ✅ Baseline: Record memory usage at startup
  - ✅ Stress test: Send 100 messages over 30 minutes
  - ✅ Monitor: Watch memory graph for leaks (upward trend)
  - ✅ Snapshot: Take heap snapshot after test
  - ✅ Fix: Find and fix any `dispose()` issues
  - ✅ **REQUIREMENT:** Memory must be stable (no upward trend)

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
7. If trend detected: Click "Snapshot" → Find retained objects
8. Fix: Ensure all controllers/streams call `dispose()`

#### Day 6: Voice Activity Detection
- ✅ Option A: Use server-side VAD (recommended)
- ✅ Option B: Implement simple client-side VAD (silence detection)
- ✅ Start/stop recording automatically
- ✅ Manual mode (push-to-talk) as fallback

#### Day 7: Integration & Testing
- ✅ Full voice pipeline: Record → Transcribe → LLM → TTS → Playback
- ✅ Test on actual hardware
- ✅ Optimize buffer sizes for latency
- ✅ Handle edge cases (no mic, no audio device)
- ✅ Verify memory remains stable during long conversations

**Deliverable:** Voice chat working + memory stable (no leaks)

---

### **Phase 3: System Tray & Wake Words (Days 8-10)**

**Goal:** App runs in system tray with wake word detection.

#### Day 8: System Tray
- ✅ Implement system tray icon (`tray_manager`)
- ✅ Tray menu (Show, Hide, Settings, Quit)
- ✅ Hide to tray on close
- ✅ Show from tray on wake word
- ✅ Tray icon states (idle, listening, speaking)

#### Day 9: Window Management
- ✅ Hide/show window programmatically
- ✅ Always-on-top mode (during conversation)
- ✅ Focus management
- ✅ Minimize to tray behavior

#### Day 10: Wake Word Integration
- ✅ Implement Phase 1 wake word strategy (server-side)
- ✅ Continuous audio streaming to wake service
- ✅ Show window on wake detection
- ✅ Exit word detection ("Hey Mycroft")
- ✅ Visual feedback (tray icon animation)

**Deliverable:** Full tray app experience with wake words

---

### **Phase 4: Advanced Features (Days 11-14)**

**Goal:** Feature parity + polish.

#### Day 11: Conversation Management
- ✅ Conversation history persistence (SQLite)
- ✅ Multiple conversations (tabs/sessions)
- ✅ Search conversations
- ✅ Export conversation (Markdown, PDF)

#### Day 12: Settings & Preferences
- ✅ Settings dialog
- ✅ Voice selection (Ara, Alex, etc.)
- ✅ Theme selection (light/dark)
- ✅ Server configuration
- ✅ Audio device selection
- ✅ Hotkey configuration

#### Day 13: Polish & UX
- ✅ Loading states
- ✅ Error handling
- ✅ Animations (smooth transitions)
- ✅ Keyboard shortcuts (comprehensive)
- ✅ Accessibility (screen reader support)

#### Day 14: Testing & Bug Fixes
- ✅ End-to-end testing
- ✅ Performance optimization
- ✅ Memory leak checks (rerun profiler)
- ✅ Stress testing (long conversations)

**Deliverable:** Production-ready Flutter client

---

## ✅ Critical Success Checkpoints (UPDATED)

### **Week 1 Cannot Proceed Without:**
- ✅ WebSocket connection working
- ✅ Desktop UX foundation in place (right-click, keyboard shortcuts)
- ✅ Audio latency test passed (<500ms)

### **Week 2 Cannot Proceed Without:**
- ✅ Voice recording working
- ✅ Audio playback working
- ✅ Memory profiling shows stable usage (no leaks)

### **Week 3 Cannot Proceed Without:**
- ✅ System tray functional
- ✅ Wake word detection working

### **Week 4 Cannot Proceed Without:**
- ✅ All core features working
- ✅ No blocking bugs
- ✅ Performance acceptable

---

## 🎯 Updated Success Criteria

**Week 1 Complete When:**
- ✅ Text chat works
- ✅ Feels desktop-native (right-click, shortcuts work)
- ✅ Audio latency <500ms (validated with test)

**Week 2 Complete When:**
- ✅ Voice chat works end-to-end
- ✅ Memory stable over 30+ minutes
- ✅ No `dispose()` issues

**Week 3 Complete When:**
- ✅ System tray works
- ✅ Wake word detection works
- ✅ Can hide/show window

**Week 4 Complete When:**
- ✅ Feature parity with PyQt6
- ✅ 8+ hours stress testing passed
- ✅ Production-ready

---

## 📝 Updated Development Notes

### **New Rule: Test Early, Test Often**

1. **Audio latency:** Test on Day 3, not Day 7
2. **Memory usage:** Test on Day 5, not end of project
3. **Desktop UX:** Build from Day 2, not retrofit in Week 4

### **Why These Changes Matter:**

- **Audio latency test on Day 3** catches issues before Week 2 work
- **Desktop UX on Day 2** prevents "mobile on desktop" feel
- **Memory profiling on Day 5** finds leaks before they compound

---

## 🎉 You're Ready to Start (v1.1)

The plan is now optimized for success with:
- ⚡ Early audio validation
- 🖥️ Desktop-first approach
- 🧠 Proactive memory management

**Next step:** Follow FLUTTER_SETUP_WINDOWS11.md to install Flutter, then return here for Week 1, Day 1.

---

**Version:** 1.1  
**Status:** Ready to Execute  
**Estimated Timeline:** 4 weeks to production-ready client

Let's build this! 🚀
