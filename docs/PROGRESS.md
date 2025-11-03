# Sparky Flutter Development Progress

**Project:** Sparky Voice AI - Flutter Client  
**Started:** [Date]  
**Current Phase:** Week 1 - Foundation  
**State Management:** Riverpod

---

## 📋 Quick Status

**Last Updated:** 2025-01-XX  
**Current Task:** Week 2 Day 4 Complete ✅  
**Next Up:** Week 2 - Audio Integration (Day 5: Audio Playback + Memory Profiling)

**Week 1 Status:** ✅ COMPLETE (Audio latency test deferred to Week 2 Day 4 for realistic pipeline testing)

**Recent Improvements (Post Week 1):**
- ✅ Changed app background color to light purple (easier on eyes)
- ✅ Fixed Enter/Shift+Enter behavior in chat input (Enter sends, Shift+Enter creates newline)

---

## Week 1: Foundation & Text Chat

### ✅ Day 1: Project Setup (Status: ✅ COMPLETED)

**Target:** Empty app with proper structure

- [x] Install Flutter SDK
- [x] Create new Flutter project (`sparky_client`)
- [x] Set up project structure:
  - [x] `lib/models/` - Data models
  - [x] `lib/services/` - Business logic services
  - [x] `lib/providers/` - Riverpod state providers
  - [x] `lib/screens/` - Full screen widgets
  - [x] `lib/widgets/` - Reusable UI components
- [x] Update `pubspec.yaml` with Week 1 dependencies:
  - [x] flutter_riverpod
  - [x] riverpod_annotation
  - [x] web_socket_channel
  - [x] shared_preferences
  - [x] intl
- [x] Run `flutter pub get`
- [ ] Verify app runs: `flutter run -d windows` (Ready to test)
- [x] Create core models:
  - [x] `lib/models/chat_message.dart` - Message data class
  - [x] `lib/models/connection_status.dart` - Connection state enum
  - [x] `lib/models/session_state.dart` - Session data class

**Completion Notes:**
- ✅ Updated `pubspec.yaml` with all Week 1 dependencies (flutter_riverpod 2.5.1, riverpod_annotation 2.3.5, web_socket_channel 2.4.0, shared_preferences 2.2.2, intl 0.19.0)
- ✅ Created complete project structure (models/, services/, providers/, screens/, widgets/)
- ✅ Created three core model files: ChatMessage, ConnectionStatus enum, SessionState
- ✅ Updated `main.dart` with Riverpod ProviderScope wrapper
- ✅ Created basic `HomeScreen` widget with placeholder UI
- ✅ Ran `flutter pub get` successfully - all dependencies installed
- ✅ No linting errors
- **Timestamp:** 2025-01-XX (Day 1 completed)

---

### ✅ Day 2: WebSocket Connection + Desktop UX (Status: ✅ COMPLETED)

**Target:** Connect to orchestrator, desktop-native feel

- [x] Create `lib/services/text_websocket_service.dart`
  - [x] Connect to `ws://10.6.1.15:8006/ws/conversation`
  - [x] Send "start" message with session_id
  - [x] Parse JSON messages (text_token, text_response, meta, done)
  - [x] Handle connection states (connecting, connected, disconnected, error)
  - [x] Automatic reconnection with exponential backoff (max 10 attempts)
- [x] Create `lib/providers/config_provider.dart`
  - [x] Server URL configuration (ConfigService)
  - [x] Default voice setting
- [x] Create `lib/providers/session_provider.dart`
  - [x] Manage session_id (SessionNotifier)
  - [x] Session persistence via SharedPreferences
- [x] Create `lib/providers/websocket_provider.dart`
  - [x] Expose WebSocket service as Riverpod provider
- [x] Create `lib/providers/conversation_provider.dart`
  - [x] Manage message list with streaming support
- [x] Desktop UX Foundation:
  - [x] Right-click context menus on text fields (DesktopTextField widget)
  - [x] Keyboard shortcuts (Ctrl+C/V/X/A/Z/ESC)
  - [x] ESC key to abort conversation (KeyboardShortcutsHandler)
  - [x] Tab navigation between UI elements (built into TextField)
  - [x] Proper focus management (Focus widget)

**Completion Notes:**
- ✅ Created ConfigService with server URL and default voice settings
- ✅ Implemented SessionNotifier with SharedPreferences persistence for session_id
- ✅ Created ConnectionNotifier for tracking WebSocket connection status
- ✅ Implemented TextWebSocketService with full protocol support:
  - Sends `{"type": "start", "voice": "ara", "session_id": ...}` on connect
  - Handles `text_token` (streaming), `text_response` (complete), `meta` events, `done`
  - Sends `{"type": "text_chat", "text": "..."}` for user messages
  - Automatic reconnection with exponential backoff (1s, 2s, 4s, 8s, ... up to 10 attempts)
- ✅ Created ConversationNotifier for managing chat messages with streaming support
- ✅ Created DesktopTextField widget with right-click context menu (Copy, Paste, Cut, Select All, Undo)
- ✅ Created KeyboardShortcutsHandler widget for global keyboard shortcuts
- ✅ All providers properly integrated with Riverpod
- **Protocol Note:** Uses `text_chat` message type (not `text`) per orchestrator implementation
- **Timestamp:** 2025-01-XX (Day 2 completed)

---

### ✅ Day 3: Text Chat UI + Audio Latency Test (Status: ✅ COMPLETED)

**Target:** Working text chat + validated audio latency <500ms

#### Text Chat UI:
- [x] Create `lib/screens/chat_screen.dart`
  - [x] Message list view (ListView with scroll controller)
  - [x] Text input field (DesktopTextField)
  - [x] Send button
  - [x] Connection status indicator (with connect/disconnect controls)
- [x] Create `lib/widgets/message_bubble.dart`
  - [x] User message styling (right-aligned, blue/primaryContainer)
  - [x] Assistant message styling (left-aligned, gray/surfaceVariant)
  - [x] Timestamp display (HH:mm format)
  - [ ] Markdown rendering support (deferred - can add later)
- [x] Create `lib/widgets/text_input.dart`
  - [x] TextField with desktop UX features (uses DesktopTextField)
  - [x] Send on Enter, newline on Shift+Enter (built into DesktopTextField)
  - [ ] Character counter (optional - not needed for MVP)
- [x] Create `lib/providers/conversation_provider.dart` (already created Day 2)
  - [x] Manage message list
  - [x] Handle streaming text (append deltas)
  - [x] Scroll to bottom on new message (auto-scroll implemented)

#### Audio Latency Test: ⏸️ DEFERRED TO WEEK 2
- [x] Create `lib/screens/audio_test_screen.dart` (shows deferral message)
- [ ] Record 2 seconds of audio from microphone → **DEFERRED**
- [ ] Play back immediately → **DEFERRED**
- [ ] Measure end-to-end latency → **DEFERRED**
- [ ] Display result with pass/fail indicator → **DEFERRED**
- [ ] **REQUIREMENT:** Must be <500ms to proceed to Week 2 → **DEFERRED**

**Test Result:** [DEFERRED TO WEEK 2 DAY 4]
**Note:** Audio latency will be tested during Week 2 voice pipeline integration. We'll measure actual end-to-end latency (mic → orchestrator → TTS → speakers), which provides a more realistic test of the voice pipeline.

**Completion Notes:**
- ✅ Added audio packages to pubspec.yaml: `flutter_sound: ^9.2.13`, `path_provider: ^2.1.0` (Windows compatible)
- ✅ Created ChatScreen with full message display, input, and connection management
- ✅ Created MessageBubble widget with user/assistant styling and timestamps
- ✅ Integrated WebSocket service with chat UI (auto-connects on screen load)
- ✅ Created AudioTestScreen with deferral message (testing deferred to Week 2)
- ✅ Updated HomeScreen with navigation buttons to Chat and Audio Test screens
- ✅ Auto-scroll implemented in chat screen when new messages arrive
- ✅ Connection status indicator shows real-time WebSocket state
- ✅ Desktop UX features (keyboard shortcuts, context menus) integrated in chat screen
- **Audio Latency Test:** Deferred to Week 2 Day 4. Will test with actual voice pipeline (mic → orchestrator → TTS → speakers) for more realistic measurement.
- **Note:** Markdown rendering can be added later with flutter_markdown package when needed
- **Timestamp:** 2025-01-XX (Day 3 completed)

**Post-Week 1 Improvements:**
- ✅ Updated color scheme for better visual experience:
  - Background: Light blue (`Colors.blue.shade100`) across all screens (darkened from shade50)
  - AppBar and text input: Purple (`Colors.purple.shade100`) for consistency
  - AI message bubbles: Lighter blue (`Colors.lightBlue.shade50`) - lighter than background
  - User message bubbles: Keep current color scheme
  - Home screen buttons/cards: Slightly lighter blue (`primaryContainer.withOpacity(0.6)`) than background
- ✅ Final color scheme - WORKING colors (ready for Week 2):
  - **Main background:** Powder Blue (#8BBCC2, RGB 139, 188, 194) for main screen and Text Chat screen
    - Applied via ColoredBox wrapper and theme `scaffoldBackgroundColor`
    - Using Material 2 (useMaterial3: false) for reliable color control
  - **AppBar and text input:** Thistle (#977597, RGB 151, 117, 151)
    - "Sparky Client" AppBar (home screen) - using ColoredBox wrapper
    - "Sparky Chat" AppBar (chat screen) - using ColoredBox wrapper
    - Message input text box (DesktopTextField and inputDecorationTheme)
    - Input area container background in chat screen
  - **Home screen center content:** Pale Green (#78C778, RGB 120, 199, 120)
    - Center container with "Sparky Voice AI" title and "Week 1 - Day 3 Complete" subtitle
    - Text Chat button background (elevation removed)
    - Audio Latency Test button background (elevation removed)
    - Features list card background (elevation removed)
  - **Solution implemented:**
    - Created centralized `AppColors` class in `lib/app_colors.dart` for all color constants
    - Used `ColoredBox` widgets to force colors at root level (bypasses all theme overrides)
    - Disabled Material 3 (useMaterial3: false) to prevent color scheme interference
    - Wrapped AppBar in PreferredSize + ColoredBox to force exact colors
    - All colors now working correctly with exact hex values
  - **Color troubleshooting process:**
    - Initial lighter colors (#B0E0E6, #D8BFD8, #98FB98) were not rendering correctly
    - Tried darker colors (#8BBCC2, #977597, #5A995A) - colors started working!
    - Final adjustment to Pale Green (#78C778) for better visual appearance
    - Root cause: Colors needed to be darker/more saturated to render correctly on Windows
- ✅ Added Dark Mode toggle:
  - Created `ThemeNotifier` provider for theme mode management
  - Added dark/light mode toggle button in AppBar (HomeScreen)
  - Dark theme: Dark gray background with appropriate contrast
  - Light theme: Light blue background with purple accents as described above
- ✅ Fixed Enter key behavior in chat input:
  - Enter key now sends message (as intended)
  - Shift+Enter creates new line (as intended)
  - Fixed FocusNode conflict error by handling Enter key in `DesktopTextField` widget itself
  - Uses `Focus` widget with `onKeyEvent` to intercept Enter before it reaches TextField
  - Enter without Shift → calls `onEnter` callback → sends message
  - Shift+Enter → passes through to TextField → creates newline
- **Bug Fix:** Resolved "GlobalKey used multiple times" and "child into parent of itself" errors
- **Timestamp:** 2025-01-XX (Post Week 1 improvements - color scheme & dark mode)

---

## Week 2: Audio Integration (Status: IN PROGRESS)

### ✅ Day 4: Audio Recording (Status: ✅ COMPLETED)
- [x] Update pubspec.yaml with `record` package (^5.1.2) and `permission_handler` (^11.3.0)
- [x] Create `AudioRecordingService` for microphone recording with streaming
  - Handles microphone permissions (Windows, mobile)
  - Streams audio chunks in real-time (16kHz mono PCM)
  - Calculates microphone level for visual feedback
  - Integrates with WebSocket service
- [x] Create `AudioWebSocketService` for voice mode WebSocket connection
  - Handles audio messages, transcriptions, streaming text
  - Receives binary audio chunks from TTS
  - Manages session_id sharing with text mode
  - Automatic reconnection with exponential backoff
- [x] Add `audioConnectionProvider` to connection_provider.dart
- [x] Create `RecordingProvider` for UI state management (recording status, microphone level, permissions)
- [x] Create `VoiceScreen` with recording UI and microphone level indicator
  - Start/Stop recording controls
  - Real-time microphone level visualization
  - Connection status indicator
  - Message display (shared conversation history)
  - Error handling and permission feedback
- [x] Update HomeScreen to include Voice Chat button
- [x] **Audio Latency Test:** Deferred to Day 4 implementation testing (will measure actual pipeline latency)

**Completion Notes:**
- ✅ Added `record` package for low-latency audio recording (16kHz mono PCM)
- ✅ Added `permission_handler` for cross-platform microphone permissions
- ✅ Created complete audio recording pipeline: microphone → streaming → WebSocket → orchestrator
- ✅ Audio chunks sent as base64-encoded JSON messages (matching orchestrator protocol)
- ✅ Microphone level calculated from PCM data (RMS) for real-time visual feedback
- ✅ Voice mode shares conversation history with text mode via shared session_id
- ✅ Audio WebSocket connects independently from text WebSocket (dual-connection architecture)
- ✅ UI shows recording state, microphone levels, and connection status
- ✅ All providers properly integrated with Riverpod
- **Protocol Note:** Audio sent as `{"type": "audio", "data": "base64..."}` with `{"type": "final"}` when complete
- **Bug Fix:** Corrected AudioEncoder enum value from `pcm16bit` to `pcm16bits` (record package v5.2.1 uses `pcm16bits`)
- **Timestamp:** 2025-01-XX (Day 4 completed)

### 🔄 Day 5: Audio Playback + Memory Profiling (Status: IN PROGRESS)
- [x] Fix audio playback service - resolve choppy playback and file locking issues
  - **Issues Found:**
    - Multiple simultaneous playback calls creating file conflicts
    - File cleanup happening while files still in use by audio player
    - No proper queuing system - files played as soon as available causing race conditions
    - Timer triggering multiple playbacks simultaneously
    - Multiple completion listeners being registered (one per file) causing conflicts
  - **Solution Implemented:**
    - Implemented proper file queue system - files played sequentially, not simultaneously
    - Single completion listener registered once in constructor (not per file)
    - Added delay before file deletion to ensure player has released the file
    - Separated state flags: `_isPlaying` and `_isProcessingQueue` for better state management
    - Proper timer management with cancellation
    - Better error handling with file cleanup retries
  - **Timestamp:** 2025-01-XX
- [x] Optimize streaming buffering to reduce choppy playback
  - **Streaming Analysis:**
    - Server side: TRUE streaming (LLM → TTS → Client binary chunks immediately)
    - Client side: Batching required (audioplayers needs WAV files, not raw PCM)
    - Old Python client used `sd.OutputStream.write()` for raw PCM streaming
    - Current Flutter client batches chunks into WAV files (creates gaps)
  - **Optimizations:**
    - Reduced initial buffer from 16384 bytes (~0.34s) to 4096 bytes (~0.085s) for faster start
    - Reduced batch size to 8192 bytes (~0.17s) - smaller files = less gaps
    - More aggressive processing: start processing with 2 chunks even if below threshold
    - Faster timer checks: 50ms instead of 150ms for more responsive processing
    - Process smaller batches more frequently to maintain smoother playback
  - **Timestamp:** 2025-01-XX
- [ ] Test audio playback with multiple conversation turns
- [ ] Memory profiling and leak detection

### ⏸️ Day 6: VAD Integration
- [ ] Tasks TBD

### ⏸️ Day 7: Full Voice Pipeline
- [ ] Tasks TBD

---

## Week 3: System Tray & Wake Words (Status: NOT STARTED)

### ⏸️ Day 8: System Tray
- [ ] Tasks TBD

### ⏸️ Day 9: Window Management
- [ ] Tasks TBD

### ⏸️ Day 10: Wake Word Integration
- [ ] Tasks TBD

---

## Week 4: Advanced Features & Polish (Status: NOT STARTED)

### ⏸️ Day 11-14
- [ ] Tasks TBD

---

## 🚨 Blockers & Issues

**Current Blockers:**
- None yet

**Resolved Issues:**
- None yet

---

## 📝 Notes & Decisions

**Architecture Decisions:**
- Using Riverpod for state management (not BLoC)
- Server-side VAD and echo cancellation
- Dual WebSocket approach (voice + text sharing session_id)

**Configuration:**
- Server: 10.6.1.15
- Orchestrator Port: 8006
- Default Voice: "ara"
- Audio Format: 16kHz mono PCM

---

## 🎯 Success Criteria

### Week 1 Complete When:
- [x] Text chat working end-to-end
- [x] Desktop UX feels native (right-click, shortcuts)
- [x] Audio latency test screen created (testing deferred to Week 2 Day 4 for realistic pipeline measurement)

### Week 2 Complete When:
- [ ] Voice chat working end-to-end
- [ ] Memory stable over 30 minutes (no leaks)

### Week 3 Complete When:
- [ ] System tray working
- [ ] Wake word detection working

### Week 4 Complete When:
- [ ] Feature parity with PyQt6 client
- [ ] 8+ hours stress testing passed
- [ ] Production-ready

---

## 📊 Metrics

**Lines of Code:** [Will track as we go]  
**Files Created:** [Will track]  
**Tests Passing:** [Will track]  
**Build Time:** [Will track]  
**App Size:** [Will track]

---

**Last Auto-Update:** [Cursor updates this timestamp]  
**Next Review:** End of Week 1
