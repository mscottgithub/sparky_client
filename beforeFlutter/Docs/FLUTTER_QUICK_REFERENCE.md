# 🎯 Flutter Migration - Quick Reference Card

**Last Updated:** November 2, 2025  
**Status:** Ready to Begin  
**Documents:** Migration Plan + Windows Setup Guide

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

### 📦 Server-Side Changes Required

**Move to Orchestrator:**
1. ✅ Voice Activity Detection (VAD) - use `webrtcvad`
2. ✅ Echo Cancellation (AEC) - use `speexdsp`
3. ✅ Audio preprocessing (optional) - use `noisereduce`

**New Service:**
4. ✅ Wake Word Service (port 8011) - `sparky_wakeword_service.py`

**Benefits:**
- Simpler client (UI focused)
- Consistent behavior across all client platforms
- Better CPU utilization (server has more resources)
- Easier to tune/debug one place vs. every client

---

## 🚀 Implementation Timeline

### Week 1: Foundation
- **Day 1:** Setup + project structure
- **Day 2:** WebSocket connection
- **Day 3:** Basic text chat UI

**Deliverable:** Text chat working

### Week 2: Audio
- **Day 4:** Audio recording
- **Day 5:** Audio playback
- **Day 6:** VAD integration (server-side)
- **Day 7:** Full voice pipeline testing

**Deliverable:** Voice chat working

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

## 📚 Essential Packages

### Core Dependencies
```yaml
dependencies:
  flutter:
    sdk: flutter
  
  # State Management
  flutter_bloc: ^8.1.3
  equatable: ^2.0.5              # For BLoC states
  
  # Network
  web_socket_channel: ^2.4.0
  http: ^1.2.0
  
  # Audio
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

## 🏗️ Project Structure Template

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
│   │   └── chat_input.dart
│   │
│   └── screens/                           # Full screens
│       ├── chat_screen.dart
│       └── settings_screen.dart
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
r    # Hot reload
R    # Hot restart
q    # Quit

# Run tests
flutter test

# Analyze code
flutter analyze

# Format code
flutter format lib/
```

### Debugging
```powershell
# Verbose logging
flutter run -v -d windows

# Clear build cache
flutter clean
flutter pub get

# Check environment
flutter doctor -v
```

---

## 🎨 Code Templates

### BLoC Template
```dart
// event
abstract class MyEvent extends Equatable {
  const MyEvent();
  @override
  List<Object> get props => [];
}

class MyEventHappened extends MyEvent {
  final String data;
  const MyEventHappened(this.data);
  @override
  List<Object> get props => [data];
}

// state
abstract class MyState extends Equatable {
  const MyState();
  @override
  List<Object> get props => [];
}

class MyInitial extends MyState {}
class MyLoading extends MyState {}
class MySuccess extends MyState {
  final String data;
  const MySuccess(this.data);
  @override
  List<Object> get props => [data];
}

// bloc
class MyBloc extends Bloc<MyEvent, MyState> {
  MyBloc() : super(MyInitial()) {
    on<MyEventHappened>(_onEventHappened);
  }
  
  void _onEventHappened(
    MyEventHappened event,
    Emitter<MyState> emit,
  ) async {
    emit(MyLoading());
    try {
      // Do something
      emit(MySuccess(event.data));
    } catch (e) {
      emit(MyError(e.toString()));
    }
  }
}
```

### WebSocket Connection Template
```dart
class WebSocketRepository {
  WebSocketChannel? _channel;
  
  void connect(String url) {
    _channel = WebSocketChannel.connect(Uri.parse(url));
    
    _channel!.stream.listen(
      (message) {
        // Handle message
        final data = json.decode(message);
        // Process data
      },
      onError: (error) {
        // Handle error
      },
      onDone: () {
        // Handle disconnect
      },
    );
  }
  
  void send(Map<String, dynamic> message) {
    _channel?.sink.add(json.encode(message));
  }
  
  void disconnect() {
    _channel?.sink.close();
  }
}
```

### System Tray Template
```dart
class TrayService with TrayListener {
  Future<void> init() async {
    await trayManager.setIcon('assets/icons/tray_idle.png');
    
    Menu menu = Menu(items: [
      MenuItem(key: 'show', label: 'Show Sparky'),
      MenuItem.separator(),
      MenuItem(key: 'exit', label: 'Exit'),
    ]);
    
    await trayManager.setContextMenu(menu);
    trayManager.addListener(this);
  }
  
  @override
  void onTrayMenuItemClick(MenuItem menuItem) {
    switch (menuItem.key) {
      case 'show':
        windowManager.show();
        break;
      case 'exit':
        windowManager.destroy();
        break;
    }
  }
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
- 🎯 Target: 150-250 MB (vs PyQt6's ~150 MB)

### Desktop Feel
- ✅ Platform-specific widgets
- ✅ Custom window decorations
- ✅ Right-click context menus
- ✅ Full keyboard shortcuts

### Wake Words
- ✅ Phase 1: Server-side (immediate)
- ✅ Phase 2: TFLite client-side (optimize later)

---

## ✅ Pre-Flight Checklist

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
- [ ] Flutter Migration Plan (`FLUTTER_MIGRATION_PLAN.md`)
- [ ] Windows Setup Guide (`FLUTTER_SETUP_WINDOWS11.md`)
- [ ] This Quick Reference Card

---

## 🚨 Critical Reminders

### DO:
- ✅ Start with Phase 1 (text chat) - verify architecture works
- ✅ Test frequently (run app often, don't accumulate bugs)
- ✅ Use hot reload extensively (press 'r' after every change)
- ✅ Follow BLoC pattern consistently
- ✅ Move complex logic to server when possible
- ✅ Dispose resources in `dispose()` methods
- ✅ Handle WebSocket disconnections gracefully

### DON'T:
- ❌ Try to do everything at once (follow phase-by-phase plan)
- ❌ Forget to test on real hardware (not just debug mode)
- ❌ Skip the server-side changes (VAD, echo cancellation)
- ❌ Ignore memory leaks (use DevTools profiler)
- ❌ Hardcode server URLs (use config)
- ❌ Block UI thread (use async/await properly)
- ❌ Forget to test reconnection logic

---

## 📞 When You Need Help

### Flutter-Specific Issues
1. Check Flutter docs: https://docs.flutter.dev
2. Search Flutter issues: https://github.com/flutter/flutter/issues
3. Ask in Flutter Discord: https://discord.gg/flutter

### Sparky-Specific Issues
1. Check migration plan troubleshooting section
2. Verify server services are running (`curl http://10.6.1.15:8006/health`)
3. Check orchestrator logs (`sudo journalctl -u sparky-orchestrator -f`)

### Dart Language Questions
1. Dart language tour: https://dart.dev/guides/language/language-tour
2. Effective Dart: https://dart.dev/guides/language/effective-dart

---

## 🎯 Success Metrics

### Week 1 Success:
- ✅ App connects to orchestrator via WebSocket
- ✅ Can send text messages
- ✅ Can receive text responses
- ✅ Messages display correctly in chat UI

### Week 2 Success:
- ✅ Can record voice from microphone
- ✅ Can play TTS audio from speakers
- ✅ Full voice conversation flow works
- ✅ Audio latency acceptable (<1 second total)

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

## 🔄 Version Management

### Semantic Versioning
- `1.0.0` - Initial Flutter release (PyQt6 feature parity)
- `1.1.0` - New features (from enhancement PDF)
- `1.0.1` - Bug fixes
- `2.0.0` - Mobile support added

### Git Branching Strategy
```
main            - Production-ready code
develop         - Integration branch
feature/*       - Feature branches
bugfix/*        - Bug fix branches
release/*       - Release preparation
```

---

## 🎉 Ready to Begin!

You have:
- ✅ Complete migration plan (60+ pages)
- ✅ Windows setup guide (step-by-step)
- ✅ This quick reference card
- ✅ Server architecture decisions made
- ✅ Clear 4-week timeline
- ✅ Code templates and examples

**Start with:**
1. Read Windows setup guide
2. Install Flutter (1-2 hours)
3. Create `sparky_flutter_client` project
4. Begin Phase 1, Day 1 (project structure)

**First milestone:** Text chat working by end of Week 1

Good luck! 🚀

---

## 📝 Notes Section

Use this space for your own notes during development:

```
Week 1 Progress:
- [ ] Day 1:
- [ ] Day 2:
- [ ] Day 3:

Blockers:


Decisions:


Next Session Focus:

```
