# 🎯 Flutter Migration - Quick Reference Card (v1.1)

**Last Updated:** November 2, 2025 (Revised)  
**Version:** 1.1 - Incorporated Critical Adjustments  
**Status:** Ready to Begin  

---

## ⚡ **What Changed in v1.1**

Three critical improvements incorporated:

1. **🎵 Early Audio Testing** (Week 1 Day 3)
   - Test audio latency BEFORE Week 2
   - Must be <500ms to proceed
   - Catch Flutter audio issues early

2. **🖥️ Desktop UX From Day 1** (Week 1 Day 2)
   - Right-click context menus
   - Full keyboard shortcuts
   - Native window decorations
   - Proper focus management

3. **🧠 Memory Profiling** (Week 2 Day 5)
   - 30-minute stress test
   - Fix `dispose()` issues early
   - Prevent memory leaks

---

## 📋 Key Decisions Made

### ✅ Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Client Framework** | Flutter (Dart) | Cross-platform (5 platforms from 1 codebase) |
| **State Management** | flutter_bloc | Predictable, testable, scales well |
| **Backend Changes** | YES - Move VAD & echo cancellation to server | Simplifies client, better performance |
| **Wake Word Strategy** | Phase 1: Server-side<br>Phase 2: TFLite (client-side) | Quick start, optimize later |
| **Audio Packages** | record + just_audio | Best performance, lowest latency |
| **System Tray** | tray_manager | Best Windows support |
| **Project Structure** | BLoC pattern with repository layer | Clean architecture, testable |

---

## 🚀 Implementation Timeline (REVISED v1.1)

### Week 1: Foundation ⚡ **UPDATED**
- **Day 1:** Setup + project structure
- **Day 2:** WebSocket connection + **Desktop UX foundation** 🖥️
- **Day 3:** Basic text chat UI + **Audio latency test** 🎵

**Deliverable:** Text chat working + audio latency validated (<500ms)

**Critical Checkpoints:**
- ✅ Desktop UX feels native (right-click, shortcuts work)
- ✅ Audio latency <500ms (blocker for Week 2)

### Week 2: Audio ⚡ **UPDATED**
- **Day 4:** Audio recording
- **Day 5:** Audio playback + **Memory profiling** 🧠
- **Day 6:** VAD integration (server-side)
- **Day 7:** Full voice pipeline testing

**Deliverable:** Voice chat working + memory stable

**Critical Checkpoints:**
- ✅ Voice chat end-to-end works
- ✅ Memory stable over 30 minutes (no leaks)

### Week 3: Tray & Wake Words
- **Day 8:** System tray
- **Day 9:** Window management
- **Day 10:** Wake word detection (server-side)

**Deliverable:** Full tray experience

### Week 4: Polish
- **Day 11:** Conversation persistence
- **Day 12:** Settings & preferences
- **Day 13:** UX polish & animations
- **Day 14:** Testing & bug fixes

**Deliverable:** Production-ready client

---

## 🎯 Critical Success Gates

### **Cannot Proceed to Week 2 Unless:**
- ✅ WebSocket connection stable
- ✅ Desktop UX foundation complete (right-click, shortcuts)
- ✅ Audio latency test passed (<500ms) ⭐ **BLOCKER**

### **Cannot Proceed to Week 3 Unless:**
- ✅ Voice chat end-to-end works
- ✅ Memory profiling passed (no leaks) ⭐ **BLOCKER**

### **Cannot Release Unless:**
- ✅ All features working
- ✅ 8+ hours stress testing passed
- ✅ Memory stable, no crashes

---

## 📚 Essential Packages

### Core Dependencies
```yaml
dependencies:
  flutter:
    sdk: flutter
  
  # State Management
  flutter_bloc: ^8.1.3
  equatable: ^2.0.5
  
  # Network
  web_socket_channel: ^2.4.0
  http: ^1.2.0
  
  # Audio (CRITICAL for latency)
  record: ^5.0.4                 # Recording
  just_audio: ^0.9.36            # Playback
  
  # System Integration
  tray_manager: ^0.2.1           # System tray
  window_manager: ^0.3.8         # Window control
  local_notifier: ^0.1.5         # Notifications
  hotkey_manager: ^0.1.8         # Global hotkeys
  
  # UI
  flutter_markdown: ^0.6.18      # Markdown rendering
  
  # Storage
  shared_preferences: ^2.2.2     # Settings
  sqflite: ^2.3.2                # Local DB
  path_provider: ^2.1.2          # File paths
  
  # Utils
  intl: ^0.19.0                  # Date/time
  json_annotation: ^4.8.1        # JSON
  freezed_annotation: ^2.4.1     # Immutable models

dev_dependencies:
  flutter_test:
    sdk: flutter
  build_runner: ^2.4.8
  json_serializable: ^6.7.1
  freezed: ^2.4.6
  flutter_lints: ^3.0.1
  bloc_test: ^9.1.5              # Testing BLoCs
```

---

## 🗗️ Project Structure Template

```
sparky_flutter_client/
├── lib/
│   ├── main.dart                          # Entry point
│   ├── app.dart                           # App configuration
│   │
│   ├── blocs/                             # Business logic
│   │   ├── websocket/
│   │   │   ├── websocket_bloc.dart
│   │   │   ├── websocket_event.dart
│   │   │   └── websocket_state.dart
│   │   ├── conversation/
│   │   ├── audio/
│   │   └── settings/
│   │
│   ├── models/                            # Data models
│   │   ├── message.dart
│   │   ├── conversation.dart
│   │   └── settings.dart
│   │
│   ├── repositories/                      # Data layer
│   │   ├── websocket_repository.dart
│   │   ├── conversation_repository.dart
│   │   └── settings_repository.dart
│   │
│   ├── services/                          # Platform services
│   │   ├── audio_recorder.dart
│   │   ├── audio_player.dart
│   │   ├── tray_service.dart
│   │   └── wake_word_service.dart
│   │
│   ├── widgets/                           # Reusable widgets
│   │   ├── message_bubble.dart
│   │   ├── chat_input.dart
│   │   └── desktop_text_field.dart       # NEW: Desktop UX
│   │
│   └── screens/                           # Full screens
│       ├── chat_screen.dart
│       ├── settings_screen.dart
│       └── audio_test_screen.dart         # NEW: Latency test
│
├── assets/
│   └── icons/
│       ├── tray_idle.png
│       ├── tray_listening.png
│       └── tray_speaking.png
│
└── test/
```

---

## 🔧 Quick Start Commands

### Initial Setup
```powershell
# Create project
flutter create sparky_flutter_client
cd sparky_flutter_client

# Add dependencies (edit pubspec.yaml first)
flutter pub get

# Run on Windows
flutter run -d windows

# Build release
flutter build windows --release
```

### Development Workflow
```powershell
# Start app with hot reload
flutter run -d windows

# In terminal while running:
r    # Hot reload (use this constantly!)
R    # Hot restart
d    # Open DevTools (for memory profiling)
q    # Quit

# Run tests
flutter test

# Analyze code
flutter analyze

# Format code
flutter format lib/
```

### Memory Profiling (Week 2 Day 5)
```powershell
# Run in debug mode
flutter run -d windows

# Press 'd' to open DevTools
# Go to Memory tab → Monitor for leaks
```

---

## ⚡ New Critical Tasks

### **Week 1 Day 2: Desktop UX Foundation**

**Must implement:**
- Right-click context menu on text fields
- Keyboard shortcuts:
  - Ctrl+C (copy)
  - Ctrl+V (paste)
  - Ctrl+X (cut)
  - Ctrl+A (select all)
  - Ctrl+Z (undo)
  - ESC (abort conversation)
- Custom title bar (native look)
- Tab navigation between elements
- Focus management (cursor in text field on show)

**Code Template - Right-Click Menu:**
```dart
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
  child: TextField(...),
)
```

---

### **Week 1 Day 3: Audio Latency Test**

**Must pass before Week 2:**
- Record 2 seconds from microphone
- Play back immediately
- Measure end-to-end latency
- **Requirement:** <500ms
- If fails: Tune `record` package settings

**Test Screen Template:**
```dart
class AudioTestScreen extends StatefulWidget {
  @override
  _AudioTestScreenState createState() => _AudioTestScreenState();
}

class _AudioTestScreenState extends State<AudioTestScreen> {
  final _recorder = Record();
  final _player = AudioPlayer();
  int? _latencyMs;
  
  Future<void> _runTest() async {
    final startTime = DateTime.now();
    
    // Record 2 seconds
    final stream = await _recorder.startStream(
      RecordConfig(
        encoder: AudioEncoder.pcm16bit,
        sampleRate: 16000,
        numChannels: 1,
      ),
    );
    
    List<int> bytes = [];
    await for (final chunk in stream.take(32)) {
      bytes.addAll(chunk);
    }
    await _recorder.stop();
    
    // Play back
    await _player.setAudioSource(BytesSource(Uint8List.fromList(bytes)));
    await _player.play();
    
    final latency = DateTime.now().difference(startTime).inMilliseconds;
    setState(() => _latencyMs = latency);
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            if (_latencyMs != null)
              Text(
                '$_latencyMs ms',
                style: TextStyle(
                  fontSize: 48,
                  color: _latencyMs! < 500 ? Colors.green : Colors.red,
                ),
              ),
            SizedBox(height: 20),
            ElevatedButton(
              onPressed: _runTest,
              child: Text('Run Latency Test'),
            ),
          ],
        ),
      ),
    );
  }
}
```

---

### **Week 2 Day 5: Memory Profiling**

**Must pass before Week 3:**
- Run app for 30 minutes
- Send 100+ messages
- Monitor memory in DevTools
- No upward trend allowed
- Fix any `dispose()` issues

**DevTools Steps:**
1. Run: `flutter run -d windows`
2. Press `d` to open DevTools
3. Go to Memory tab
4. Click "Reset" to baseline
5. Use app heavily (100 messages)
6. Watch memory graph
7. If trend up: Click "Snapshot" → Find leaks
8. Fix: Add `dispose()` calls

**Disposal Checklist:**
```dart
@override
void dispose() {
  _controller.dispose();        // Text controllers
  _scrollController.dispose();  // Scroll controllers
  _focusNode.dispose();         // Focus nodes
  _subscription.cancel();       // Stream subscriptions
  _channel?.sink.close();       // WebSocket channels
  super.dispose();
}
```

---

## 🛡️ Mitigation Strategy Summary

### Large App Size
- ✅ Use tree shaking: `flutter build --split-debug-info`
- ✅ Optimize assets: WebP images, SVG icons
- ✅ Remove unused dependencies
- 🎯 Target: 50-80 MB (vs PyQt6's ~30 MB)

### Startup Time
- ✅ Add splash screen
- ✅ Lazy initialization (load in background)
- ✅ Don't wait for wake word model at startup
- 🎯 Target: <1 second (vs PyQt6's ~0.3s)

### Memory Usage
- ✅ Dispose resources properly
- ✅ Limit rendered messages (pagination)
- ✅ Cancel stream subscriptions
- ✅ **Week 2 Day 5: Memory profiling** ⭐ NEW
- 🎯 Target: 150-250 MB (vs PyQt6's ~150 MB)

### Desktop Feel
- ✅ Platform-specific widgets
- ✅ Custom window decorations
- ✅ **Week 1 Day 2: Right-click context menus** ⭐ NEW
- ✅ **Week 1 Day 2: Full keyboard shortcuts** ⭐ NEW

### Audio Latency
- ✅ **Week 1 Day 3: Early testing** ⭐ NEW
- ✅ Tune `record` package settings if needed
- 🎯 Target: <500ms end-to-end

### Wake Words
- ✅ Phase 1: Server-side (immediate)
- ✅ Phase 2: TFLite client-side (optimize later)

---

## ✅ Pre-Flight Checklist (Updated)

Before starting development:

**Windows Setup:**
- [ ] Flutter SDK installed (`flutter --version` works)
- [ ] Visual Studio 2022 with C++ tools
- [ ] VS Code with Flutter extension
- [ ] Git installed
- [ ] Test project runs (`flutter create test && cd test && flutter run -d windows`)

**Server Setup:**
- [ ] Orchestrator running and accessible
- [ ] Whisper service running
- [ ] TTS service running
- [ ] LLM (Lexi V2) running
- [ ] Can curl health endpoints

**Documentation Read:**
- [ ] Flutter Migration Plan v1.1 (`FLUTTER_MIGRATION_PLAN_v1.1.md`)
- [ ] Windows Setup Guide (`FLUTTER_SETUP_WINDOWS11.md`)
- [ ] This Quick Reference Card (v1.1)

---

## 🚨 Critical Reminders (Updated)

### DO:
- ✅ **Test audio latency on Day 3** (blocker for Week 2) ⚡
- ✅ **Add desktop UX on Day 2** (right-click, shortcuts) ⚡
- ✅ **Profile memory on Week 2 Day 5** (catch leaks early) ⚡
- ✅ Test frequently (run app often, don't accumulate bugs)
- ✅ Use hot reload extensively (press 'r' after every change)
- ✅ Follow BLoC pattern consistently
- ✅ Move complex logic to server when possible
- ✅ Dispose resources in `dispose()` methods
- ✅ Handle WebSocket disconnections gracefully

### DON'T:
- ❌ Skip audio latency test on Day 3 (will regret in Week 2)
- ❌ Skip desktop UX on Day 2 (will feel mobile-ish)
- ❌ Skip memory profiling on Day 5 (leaks compound)
- ❌ Try to do everything at once (follow phase-by-phase plan)
- ❌ Forget to test on real hardware (not just debug mode)
- ❌ Ignore memory leaks (use DevTools profiler)
- ❌ Hardcode server URLs (use config)
- ❌ Block UI thread (use async/await properly)

---

## 🎯 Success Metrics (Updated)

### Week 1 Success:
- ✅ App connects to orchestrator via WebSocket
- ✅ Can send text messages
- ✅ Can receive text responses
- ✅ Messages display correctly in chat UI
- ✅ **Desktop UX feels native** (right-click, shortcuts work) ⚡
- ✅ **Audio latency <500ms** (validated with test) ⚡

### Week 2 Success:
- ✅ Can record voice from microphone
- ✅ Can play TTS audio from speakers
- ✅ Full voice conversation flow works
- ✅ Audio latency acceptable (<1 second total)
- ✅ **Memory stable over 30 minutes** (no leaks) ⚡

### Week 3 Success:
- ✅ App runs in system tray
- ✅ Wake word detection shows window
- ✅ Exit word detection hides window
- ✅ Tray menu functional

### Week 4 Success:
- ✅ Conversations persist across restarts
- ✅ Settings save correctly
- ✅ No crashes in 1-hour stress test
- ✅ Performance acceptable on target hardware

### Release Ready:
- ✅ All PyQt6 features implemented
- ✅ Markdown rendering works
- ✅ Export conversations works
- ✅ Build produces working .exe
- ✅ Documentation complete
- ✅ **8+ hours stress testing passed** (with memory profiling)

---

## 📊 Server Endpoints Reference

### Orchestrator (10.6.1.15:8006)
- `GET /health` - Service health
- `WS /ws/conversation` - Main conversation endpoint
- Supports: text, audio, streaming

### Whisper (10.6.1.15:8005)
- `GET /health` - Service health
- `POST /transcribe` - Audio transcription

### TTS (10.6.1.15:8004)
- `GET /health` - Service health
- `WS /speak_stream` - Streaming TTS

### Wake Word (10.6.1.15:8011) - NEW
- `GET /health` - Service health
- `WS /wake` - Continuous wake word detection

---

## 🎉 Ready to Begin! (v1.1)

You have:
- ✅ Complete migration plan (60+ pages) - **v1.1 with critical adjustments**
- ✅ Windows setup guide (step-by-step)
- ✅ This quick reference card - **v1.1 updated**
- ✅ Server architecture decisions made
- ✅ Clear 4-week timeline with success gates
- ✅ Code templates and examples

**Start with:**
1. Read Windows setup guide
2. Install Flutter (1-2 hours)
3. Create `sparky_flutter_client` project
4. Begin Phase 1, Day 1 (project structure)

**First milestone:** Text chat + desktop UX + audio latency test by end of Week 1

Good luck! 🚀

---

**Version:** 1.1  
**Changes:** Added early audio testing, desktop UX from Day 1, memory profiling  
**Status:** Optimized for Success

Let's build this! 🚀
