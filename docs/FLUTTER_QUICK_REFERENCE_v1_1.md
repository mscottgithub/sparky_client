# ðŸŽ¯ Flutter Migration - Quick Reference Card (v1.1)

**Last Updated:** November 2, 2025 (Revised)  
**Version:** 1.1 - Incorporated Critical Adjustments  
**Status:** Ready to Begin  

---

## âš¡ **What Changed in v1.1**

Three critical improvements incorporated:

1. **ðŸŽµ Early Audio Testing** (Week 1 Day 3)
   - Test audio latency BEFORE Week 2
   - Must be <500ms to proceed
   - Catch Flutter audio issues early

2. **ðŸ–¥ï¸ Desktop UX From Day 1** (Week 1 Day 2)
   - Right-click context menus
   - Full keyboard shortcuts
   - Native window decorations
   - Proper focus management

3. **ðŸ§  Memory Profiling** (Week 2 Day 5)
   - 30-minute stress test
   - Fix `dispose()` issues early
   - Prevent memory leaks

---

## ðŸ“‹ Key Decisions Made

### âœ… Architecture Decisions

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

## ðŸš€ Implementation Timeline (REVISED v1.1)

### Week 1: Foundation âš¡ **UPDATED**
- **Day 1:** Setup + project structure
- **Day 2:** WebSocket connection + **Desktop UX foundation** ðŸ–¥ï¸
- **Day 3:** Basic text chat UI + **Audio latency test** ðŸŽµ

**Deliverable:** Text chat working + audio latency validated (<500ms)

**Critical Checkpoints:**
- âœ… Desktop UX feels native (right-click, shortcuts work)
- âœ… Audio latency <500ms (blocker for Week 2)

### Week 2: Audio âš¡ **UPDATED**
- **Day 4:** Audio recording
- **Day 5:** Audio playback + **Memory profiling** ðŸ§ 
- **Day 6:** VAD integration (server-side)
- **Day 7:** Full voice pipeline testing

**Deliverable:** Voice chat working + memory stable

**Critical Checkpoints:**
- âœ… Voice chat end-to-end works
- âœ… Memory stable over 30 minutes (no leaks)

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

## ðŸŽ¯ Critical Success Gates

### **Cannot Proceed to Week 2 Unless:**
- âœ… WebSocket connection stable
- âœ… Desktop UX foundation complete (right-click, shortcuts)
- âœ… Audio latency test passed (<500ms) â­ **BLOCKER**

### **Cannot Proceed to Week 3 Unless:**
- âœ… Voice chat end-to-end works
- âœ… Memory profiling passed (no leaks) â­ **BLOCKER**

### **Cannot Release Unless:**
- âœ… All features working
- âœ… 8+ hours stress testing passed
- âœ… Memory stable, no crashes

---

## ðŸ“š Essential Packages

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

## ðŸ——ï¸ Project Structure Template

```
sparky_flutter_client/
â”œâ”€â”€ lib/
â”‚   â”œâ”€â”€ main.dart                          # Entry point
â”‚   â”œâ”€â”€ app.dart                           # App configuration
â”‚   â”‚
â”‚   â”œâ”€â”€ blocs/                             # Business logic
â”‚   â”‚   â”œâ”€â”€ websocket/
â”‚   â”‚   â”‚   â”œâ”€â”€ websocket_bloc.dart
â”‚   â”‚   â”‚   â”œâ”€â”€ websocket_event.dart
â”‚   â”‚   â”‚   â””â”€â”€ websocket_state.dart
â”‚   â”‚   â”œâ”€â”€ conversation/
â”‚   â”‚   â”œâ”€â”€ audio/
â”‚   â”‚   â””â”€â”€ settings/
â”‚   â”‚
â”‚   â”œâ”€â”€ models/                            # Data models
â”‚   â”‚   â”œâ”€â”€ message.dart
â”‚   â”‚   â”œâ”€â”€ conversation.dart
â”‚   â”‚   â””â”€â”€ settings.dart
â”‚   â”‚
â”‚   â”œâ”€â”€ repositories/                      # Data layer
â”‚   â”‚   â”œâ”€â”€ websocket_repository.dart
â”‚   â”‚   â”œâ”€â”€ conversation_repository.dart
â”‚   â”‚   â””â”€â”€ settings_repository.dart
â”‚   â”‚
â”‚   â”œâ”€â”€ services/                          # Platform services
â”‚   â”‚   â”œâ”€â”€ audio_recorder.dart
â”‚   â”‚   â”œâ”€â”€ audio_player.dart
â”‚   â”‚   â”œâ”€â”€ tray_service.dart
â”‚   â”‚   â””â”€â”€ wake_word_service.dart
â”‚   â”‚
â”‚   â”œâ”€â”€ widgets/                           # Reusable widgets
â”‚   â”‚   â”œâ”€â”€ message_bubble.dart
â”‚   â”‚   â”œâ”€â”€ chat_input.dart
â”‚   â”‚   â””â”€â”€ desktop_text_field.dart       # NEW: Desktop UX
â”‚   â”‚
â”‚   â””â”€â”€ screens/                           # Full screens
â”‚       â”œâ”€â”€ chat_screen.dart
â”‚       â”œâ”€â”€ settings_screen.dart
â”‚       â””â”€â”€ audio_test_screen.dart         # NEW: Latency test
â”‚
â”œâ”€â”€ assets/
â”‚   â””â”€â”€ icons/
â”‚       â”œâ”€â”€ tray_idle.png
â”‚       â”œâ”€â”€ tray_listening.png
â”‚       â””â”€â”€ tray_speaking.png
â”‚
â””â”€â”€ test/
```

---

## ðŸ”§ Quick Start Commands

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
# Go to Memory tab â†’ Monitor for leaks
```

---

## âš¡ New Critical Tasks

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
7. If trend up: Click "Snapshot" â†’ Find leaks
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

## ðŸ›¡ï¸ Mitigation Strategy Summary

### Large App Size
- âœ… Use tree shaking: `flutter build --split-debug-info`
- âœ… Optimize assets: WebP images, SVG icons
- âœ… Remove unused dependencies
- ðŸŽ¯ Target: 50-80 MB (vs PyQt6's ~30 MB)

### Startup Time
- âœ… Add splash screen
- âœ… Lazy initialization (load in background)
- âœ… Don't wait for wake word model at startup
- ðŸŽ¯ Target: <1 second (vs PyQt6's ~0.3s)

### Memory Usage
- âœ… Dispose resources properly
- âœ… Limit rendered messages (pagination)
- âœ… Cancel stream subscriptions
- âœ… **Week 2 Day 5: Memory profiling** â­ NEW
- ðŸŽ¯ Target: 150-250 MB (vs PyQt6's ~150 MB)

### Desktop Feel
- âœ… Platform-specific widgets
- âœ… Custom window decorations
- âœ… **Week 1 Day 2: Right-click context menus** â­ NEW
- âœ… **Week 1 Day 2: Full keyboard shortcuts** â­ NEW

### Audio Latency
- âœ… **Week 1 Day 3: Early testing** â­ NEW
- âœ… Tune `record` package settings if needed
- ðŸŽ¯ Target: <500ms end-to-end

### Wake Words
- âœ… Phase 1: Server-side (immediate)
- âœ… Phase 2: TFLite client-side (optimize later)

---

## âœ… Pre-Flight Checklist (Updated)

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

## ðŸš¨ Critical Reminders (Updated)

### DO:
- âœ… **Test audio latency on Day 3** (blocker for Week 2) âš¡
- âœ… **Add desktop UX on Day 2** (right-click, shortcuts) âš¡
- âœ… **Profile memory on Week 2 Day 5** (catch leaks early) âš¡
- âœ… Test frequently (run app often, don't accumulate bugs)
- âœ… Use hot reload extensively (press 'r' after every change)
- âœ… Follow BLoC pattern consistently
- âœ… Move complex logic to server when possible
- âœ… Dispose resources in `dispose()` methods
- âœ… Handle WebSocket disconnections gracefully

### DON'T:
- âŒ Skip audio latency test on Day 3 (will regret in Week 2)
- âŒ Skip desktop UX on Day 2 (will feel mobile-ish)
- âŒ Skip memory profiling on Day 5 (leaks compound)
- âŒ Try to do everything at once (follow phase-by-phase plan)
- âŒ Forget to test on real hardware (not just debug mode)
- âŒ Ignore memory leaks (use DevTools profiler)
- âŒ Hardcode server URLs (use config)
- âŒ Block UI thread (use async/await properly)

---

## ðŸŽ¯ Success Metrics (Updated)

### Week 1 Success:
- âœ… App connects to orchestrator via WebSocket
- âœ… Can send text messages
- âœ… Can receive text responses
- âœ… Messages display correctly in chat UI
- âœ… **Desktop UX feels native** (right-click, shortcuts work) âš¡
- âœ… **Audio latency <500ms** (validated with test) âš¡

### Week 2 Success:
- âœ… Can record voice from microphone
- âœ… Can play TTS audio from speakers
- âœ… Full voice conversation flow works
- âœ… Audio latency acceptable (<1 second total)
- âœ… **Memory stable over 30 minutes** (no leaks) âš¡

### Week 3 Success:
- âœ… App runs in system tray
- âœ… Wake word detection shows window
- âœ… Exit word detection hides window
- âœ… Tray menu functional

### Week 4 Success:
- âœ… Conversations persist across restarts
- âœ… Settings save correctly
- âœ… No crashes in 1-hour stress test
- âœ… Performance acceptable on target hardware

### Release Ready:
- âœ… All PyQt6 features implemented
- âœ… Markdown rendering works
- âœ… Export conversations works
- âœ… Build produces working .exe
- âœ… Documentation complete
- âœ… **8+ hours stress testing passed** (with memory profiling)

---

## ðŸ“Š Server Endpoints Reference

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

## ðŸŽ‰ Ready to Begin! (v1.1)

You have:
- âœ… Complete migration plan (60+ pages) - **v1.1 with critical adjustments**
- âœ… Windows setup guide (step-by-step)
- âœ… This quick reference card - **v1.1 updated**
- âœ… Server architecture decisions made
- âœ… Clear 4-week timeline with success gates
- âœ… Code templates and examples

**Start with:**
1. Read Windows setup guide
2. Install Flutter (1-2 hours)
3. Create `sparky_flutter_client` project
4. Begin Phase 1, Day 1 (project structure)

**First milestone:** Text chat + desktop UX + audio latency test by end of Week 1

Good luck! ðŸš€

---

**Version:** 1.1  
**Changes:** Added early audio testing, desktop UX from Day 1, memory profiling  
**Status:** Optimized for Success

Let's build this! ðŸš€
