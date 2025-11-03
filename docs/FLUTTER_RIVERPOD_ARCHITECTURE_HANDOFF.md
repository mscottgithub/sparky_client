# Flutter + Riverpod Architecture Handoff Document
**Project:** Sparky Voice-AI System  
**Migration:** PyQt6 â†’ Flutter + Riverpod  
**Date:** 2025-11-02  
**Purpose:** Clear architectural blueprint for implementing Riverpod services in Flutter client

---

## Executive Summary

This document provides a complete architectural analysis of the existing PyQt6 Sparky client and orchestrator, mapping their patterns to Flutter + Riverpod equivalents. It identifies critical design patterns, independent service architecture, and unresolved decisions that must be made before implementation.

**Key Finding:** The system uses **TWO independent WebSocket connections** (audio and text) that share a single `session_id` for conversation continuity. This is NOT a single WebSocket with message routingâ€”it's truly dual-connection architecture.

---

## Current Architecture (PyQt6 + Python Backend)

### System Components

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                   SPARKY TRAY CLIENT                        â”‚
â”‚                   (PyQt6 v5.0.2)                           â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚                                                             â”‚
â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”              â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”           â”‚
â”‚  â”‚ Voice Mode   â”‚              â”‚  Text Mode   â”‚           â”‚
â”‚  â”‚ (Assistant)  â”‚              â”‚ (ChatWindow) â”‚           â”‚
â”‚  â”‚              â”‚              â”‚              â”‚           â”‚
â”‚  â”‚ WebSocket A  â”‚              â”‚ WebSocket B  â”‚           â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”˜              â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”˜           â”‚
â”‚         â”‚                              â”‚                   â”‚
â”‚         â”‚  Shared session_id          â”‚                   â”‚
â”‚         â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜                   â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                         â”‚
                         â–¼
         â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
         â”‚  Orchestrator WebSocket       â”‚
         â”‚  /ws/conversation             â”‚
         â”‚  (Port 8006)                  â”‚
         â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
         â”‚  - Session Management         â”‚
         â”‚  - Conversation History       â”‚
         â”‚  - Message Routing            â”‚
         â”‚  - Audio/Text Processing      â”‚
         â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                         â”‚
         â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
         â”‚                               â”‚
         â–¼                               â–¼
    â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”                     â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”
    â”‚ Whisper â”‚                     â”‚   TTS   â”‚
    â”‚ (8005)  â”‚                     â”‚ (8004)  â”‚
    â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜                     â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
              â”‚                     â”‚
              â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                         â–¼
                    â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                    â”‚   LLM   â”‚
                    â”‚  vLLM   â”‚
                    â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

### WebSocket Architecture Details

#### Voice Mode (VoiceAssistant)
- **Location:** Lines 144-393 (`WebSocketWorker` class)
- **Connection:** Dedicated WebSocket to `/ws/conversation`
- **Thread:** Runs in separate QThread with asyncio event loop
- **Sends:** Audio chunks (base64-encoded), user text
- **Receives:** Transcriptions, streaming text, binary audio chunks, meta events
- **State Machine:** idle â†’ calibrating â†’ listening_wake â†’ recording â†’ processing â†’ speaking

#### Text Mode (ChatWindow)
- **Location:** Lines 396-1200 (`ChatWindow` class)
- **Connection:** **Separate** WebSocket to `/ws/conversation`
- **Thread:** Also runs in separate thread with asyncio loop
- **Sends:** Text messages only
- **Receives:** Streaming text responses, meta events
- **UI:** PyQt6 QTextEdit with rich text formatting, markdown support

#### Critical Pattern: Session ID Sharing
```python
# Voice WebSocket connects FIRST (line 196-212)
start_msg = {
    "type": "start",
    "voice": DEFAULT_VOICE,
    "session_id": self.assistant.session_id  # May be None initially
}
await ws.send(json.dumps(start_msg))

# Server responds with session_id
response = await ws.recv()
data = json.loads(response)
if data.get("type") == "meta" and data.get("event") == "session_id":
    session_id = data.get("value")
    if not self.assistant.session_id:
        self.assistant.session_id = session_id  # STORE IT

# Text WebSocket connects SECOND (line 1049-1067)
start_msg = {
    "type": "start",
    "voice": DEFAULT_VOICE,
    "session_id": self.assistant.session_id  # REUSE same session_id
}
await self._ws.send(json.dumps(start_msg))
```

**Result:** Both WebSockets write to the same conversation history on the server. User can seamlessly switch between voice and text modes while maintaining context.

---

## Orchestrator Protocol (v3.0)

### WebSocket Endpoint: `/ws/conversation`

**Infinite Message Handler** - Handles unlimited messages per WebSocket connection until disconnect.

### Message Types (Client â†’ Server)

#### 1. Start Message (Required First)
```json
{
  "type": "start",
  "voice": "ara",
  "session_id": "uuid-or-null"
}
```
- If `session_id` is null/missing, server creates new session
- Server responds with `session_id` in meta event
- Initializes conversation history for this session

#### 2. Audio Message
```json
{
  "type": "audio",
  "data": "base64-encoded-audio-bytes"
}
```
- Server sends to Whisper (port 8005)
- Transcription returned as `transcription` event
- Then processed through LLM â†’ TTS â†’ audio chunks

#### 3. Text Message
```json
{
  "type": "text",
  "content": "User's message text"
}
```
- Bypasses Whisper, goes directly to LLM
- Response streamed as `streaming_text` events
- No audio generation (text-only mode)

#### 4. Goodbye Message
```json
{
  "type": "goodbye"
}
```
- Closes current conversation turn
- Keeps session alive for next message

### Message Types (Server â†’ Client)

#### Meta Events (JSON)
```json
{
  "type": "meta",
  "event": "session_id",
  "value": "abc-123-def"
}
```
- Events: `session_id`, `provider` (tts provider used), `ttfa_ms` (time-to-first-audio)

#### Transcription (JSON)
```json
{
  "type": "transcription",
  "text": "What the user said",
  "language": "en"
}
```

#### Streaming Text (JSON)
```json
{
  "type": "streaming_text",
  "content": "AI response text",
  "is_delta": true
}
```
- `is_delta=true`: Append to current message (streaming)
- `is_delta=false`: New complete message

#### Audio Chunks (Binary)
- Raw binary data (not JSON)
- 16-bit PCM, 24kHz sample rate
- Client plays directly to audio output

#### Done (JSON)
```json
{
  "type": "done"
}
```
- Signals end of current conversation turn

### Session Management
- **Storage:** In-memory dictionary `sessions: Dict[str, ConversationSession]`
- **Lifetime:** 1 hour of inactivity (background cleanup task)
- **History:** Last 50 messages per session (configurable via `CONVERSATION_MAX_HISTORY`)
- **Isolation:** Text and audio messages are NOT isolatedâ€”they share the same history array

---

## Flutter + Riverpod Architecture Blueprint

### Service Provider Structure

```dart
// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
// STABLE SERVICES (Created once, methods called on them)
// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

// Configuration (from config.ini equivalent)
final configServiceProvider = Provider<ConfigService>((ref) {
  return ConfigService(
    serverHost: '10.6.1.15',
    orchPort: 8006,
    whisperPort: 8005,
    ttsPort: 8004,
    defaultVoice: 'ara',
    sampleRate: 16000,
  );
});

// Audio I/O (microphone, speakers)
final audioServiceProvider = Provider<AudioService>((ref) {
  return AudioService();
});

// Wake word detection (openWakeWord)
final wakeWordServiceProvider = Provider<WakeWordService>((ref) {
  final audio = ref.watch(audioServiceProvider);
  return WakeWordService(audioService: audio);
});

// Audio WebSocket (Voice mode)
final audioWebSocketProvider = Provider<AudioWebSocketService>((ref) {
  final config = ref.watch(configServiceProvider);
  final session = ref.read(sessionProvider.notifier);
  final conversation = ref.read(conversationProvider.notifier);
  final audioConnection = ref.read(audioConnectionProvider.notifier);
  
  final service = AudioWebSocketService(
    url: 'ws://${config.serverHost}:${config.orchPort}/ws/conversation',
    defaultVoice: config.defaultVoice,
    sessionNotifier: session,
    conversationNotifier: conversation,
    connectionNotifier: audioConnection,
  );
  
  ref.onDispose(() {
    service.disconnect();
  });
  
  return service;
});

// Text WebSocket (Text mode)
final textWebSocketProvider = Provider<TextWebSocketService>((ref) {
  final config = ref.watch(configServiceProvider);
  final session = ref.watch(sessionProvider.notifier);  // WATCH to use session_id
  final conversation = ref.read(conversationProvider.notifier);
  final textConnection = ref.read(textConnectionProvider.notifier);
  
  final service = TextWebSocketService(
    url: 'ws://${config.serverHost}:${config.orchPort}/ws/conversation',
    defaultVoice: config.defaultVoice,
    sessionNotifier: session,
    conversationNotifier: conversation,
    connectionNotifier: textConnection,
  );
  
  ref.onDispose(() {
    service.disconnect();
  });
  
  return service;
});

// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
// STATE (Changes frequently, triggers UI rebuilds)
// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

// Session state (shared session_id)
final sessionProvider = StateNotifierProvider<SessionNotifier, SessionState>((ref) {
  return SessionNotifier();
});

class SessionState {
  final String? sessionId;
  final bool conversationActive;
  
  SessionState({this.sessionId, this.conversationActive = false});
}

// Connection status for audio WebSocket
final audioConnectionProvider = StateNotifierProvider<ConnectionNotifier, ConnectionStatus>((ref) {
  return ConnectionNotifier();
});

// Connection status for text WebSocket (INDEPENDENT!)
final textConnectionProvider = StateNotifierProvider<ConnectionNotifier, ConnectionStatus>((ref) {
  return ConnectionNotifier();
});

enum ConnectionStatus { disconnected, connecting, connected, error }

// Voice pipeline state machine
final voiceStateProvider = StateNotifierProvider<VoiceStateNotifier, VoiceState>((ref) {
  return VoiceStateNotifier();
});

enum VoiceState {
  idle,
  calibrating,
  listeningWake,
  activeConversation,
  recordingCommand,
  processing,
  speaking
}

// Recording status
final recordingProvider = StateNotifierProvider<RecordingNotifier, bool>((ref) {
  return RecordingNotifier();
});

// Playing status
final playingProvider = StateNotifierProvider<PlayingNotifier, bool>((ref) {
  return PlayingNotifier();
});

// SHARED conversation history (both voice and text write here)
final conversationProvider = StateNotifierProvider<ConversationNotifier, List<ChatMessage>>((ref) {
  return ConversationNotifier();
});

class ChatMessage {
  final String role;  // 'user' or 'assistant'
  final String content;
  final DateTime timestamp;
  final String? messageId;  // For streaming updates
  
  ChatMessage({
    required this.role,
    required this.content,
    DateTime? timestamp,
    this.messageId,
  }) : timestamp = timestamp ?? DateTime.now();
}
```

### WebSocket Service Implementation Pattern

Based on the PyQt6 `WebSocketWorker` class (lines 144-393):

```dart
import 'dart:convert';
import 'dart:typed_data';
import 'package:web_socket_channel/web_socket_channel.dart';

class AudioWebSocketService {
  final String url;
  final String defaultVoice;
  final SessionNotifier sessionNotifier;
  final ConversationNotifier conversationNotifier;
  final ConnectionNotifier connectionNotifier;
  
  WebSocketChannel? _channel;
  StreamSubscription? _subscription;
  bool _isConnected = false;
  String? _currentStreamingMessageId;  // For delta updates
  
  AudioWebSocketService({
    required this.url,
    required this.defaultVoice,
    required this.sessionNotifier,
    required this.conversationNotifier,
    required this.connectionNotifier,
  });
  
  // â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  // Connection Management
  // â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  
  Future<void> connect(String? sessionId) async {
    try {
      connectionNotifier.setStatus(ConnectionStatus.connecting);
      
      _channel = WebSocketChannel.connect(Uri.parse(url));
      
      // Send START message (matches PyQt6 pattern, line 197-202)
      final startMsg = {
        'type': 'start',
        'voice': defaultVoice,
        'session_id': sessionId,  // null = new session, string = resume
      };
      _channel!.sink.add(json.encode(startMsg));
      
      // Listen to incoming messages
      _subscription = _channel!.stream.listen(
        _handleMessage,
        onError: _handleError,
        onDone: _handleDisconnect,
      );
      
      _isConnected = true;
      connectionNotifier.setStatus(ConnectionStatus.connected);
      
    } catch (e) {
      print('WebSocket connection error: $e');
      _isConnected = false;
      connectionNotifier.setStatus(ConnectionStatus.error);
    }
  }
  
  void disconnect() {
    _subscription?.cancel();
    _channel?.sink.close();
    _isConnected = false;
    connectionNotifier.setStatus(ConnectionStatus.disconnected);
  }
  
  // â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  // Message Handling (matches orchestrator protocol)
  // â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  
  void _handleMessage(dynamic data) {
    if (data is String) {
      // JSON message
      try {
        final msg = json.decode(data) as Map<String, dynamic>;
        final type = msg['type'] as String?;
        
        switch (type) {
          case 'meta':
            _handleMeta(msg);
            break;
          case 'streaming_text':
            _handleStreamingText(msg);
            break;
          case 'transcription':
            _handleTranscription(msg);
            break;
          case 'done':
            _handleDone(msg);
            break;
          default:
            print('Unknown message type: $type');
        }
      } catch (e) {
        print('Error parsing JSON message: $e');
      }
    } else if (data is Uint8List || data is List<int>) {
      // Binary audio chunk
      _handleAudioChunk(data as List<int>);
    }
  }
  
  void _handleMeta(Map<String, dynamic> msg) {
    final event = msg['event'] as String?;
    final value = msg['value'];
    
    if (event == 'session_id') {
      // Server assigned/confirmed session_id
      sessionNotifier.setSession(value as String);
      print('Session ID: $value');
    } else if (event == 'provider') {
      // TTS provider info (xtts, higgs, etc.)
      print('TTS provider: $value');
    } else if (event == 'ttfa_ms') {
      // Time-to-first-audio metric
      print('TTFA: ${value}ms');
    }
  }
  
  void _handleStreamingText(Map<String, dynamic> msg) {
    final content = msg['content'] as String;
    final isDelta = msg['is_delta'] as bool? ?? false;
    
    if (isDelta) {
      // Append to existing message (streaming)
      if (_currentStreamingMessageId != null) {
        // Find and update the existing message
        conversationNotifier.appendToMessage(
          _currentStreamingMessageId!,
          content,
        );
      }
    } else {
      // New message
      _currentStreamingMessageId = DateTime.now().millisecondsSinceEpoch.toString();
      conversationNotifier.addMessage(
        ChatMessage(
          role: 'assistant',
          content: content,
          messageId: _currentStreamingMessageId,
        ),
      );
    }
  }
  
  void _handleTranscription(Map<String, dynamic> msg) {
    final text = msg['text'] as String;
    final language = msg['language'] as String?;
    
    // Add user message to conversation
    conversationNotifier.addMessage(
      ChatMessage(
        role: 'user',
        content: text,
      ),
    );
    
    print('Transcription [$language]: $text');
  }
  
  void _handleAudioChunk(List<int> data) {
    // Send to audio playback service
    // This would integrate with your AudioService to play the chunk
    // audioService.playChunk(data);
    print('Received audio chunk: ${data.length} bytes');
  }
  
  void _handleDone(Map<String, dynamic> msg) {
    // Conversation turn complete
    _currentStreamingMessageId = null;
    print('Conversation turn complete');
  }
  
  void _handleError(error) {
    print('WebSocket error: $error');
    _isConnected = false;
    connectionNotifier.setStatus(ConnectionStatus.error);
  }
  
  void _handleDisconnect() {
    print('WebSocket disconnected');
    _isConnected = false;
    connectionNotifier.setStatus(ConnectionStatus.disconnected);
  }
  
  // â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  // Sending Messages
  // â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  
  void sendAudio(List<int> audioData) {
    if (!_isConnected) {
      print('Cannot send audio: not connected');
      return;
    }
    
    final msg = {
      'type': 'audio',
      'data': base64Encode(audioData),
    };
    _channel!.sink.add(json.encode(msg));
  }
  
  void sendText(String text) {
    if (!_isConnected) {
      print('Cannot send text: not connected');
      return;
    }
    
    final msg = {
      'type': 'text',
      'content': text,
    };
    _channel!.sink.add(json.encode(msg));
  }
  
  void sendGoodbye() {
    if (!_isConnected) return;
    
    final msg = {'type': 'goodbye'};
    _channel!.sink.add(json.encode(msg));
  }
}

// TextWebSocketService would be nearly identical
// Main difference: No audio handling, text-only focus
class TextWebSocketService {
  // Same structure, simplified for text-only
  // Remove: _handleAudioChunk, sendAudio
  // Keep: All text handling, streaming, session management
}
```

### Conversation State Notifier with Streaming Support

```dart
class ConversationNotifier extends StateNotifier<List<ChatMessage>> {
  ConversationNotifier() : super([]);
  
  // Add new message
  void addMessage(ChatMessage message) {
    state = [...state, message];
  }
  
  // Append content to existing message (for streaming)
  void appendToMessage(String messageId, String additionalContent) {
    state = [
      for (final msg in state)
        if (msg.messageId == messageId)
          ChatMessage(
            role: msg.role,
            content: msg.content + additionalContent,  // Append
            timestamp: msg.timestamp,
            messageId: messageId,
          )
        else
          msg
    ];
  }
  
  // Replace entire message content
  void updateMessage(String messageId, String newContent) {
    state = [
      for (final msg in state)
        if (msg.messageId == messageId)
          ChatMessage(
            role: msg.role,
            content: newContent,  // Replace
            timestamp: msg.timestamp,
            messageId: messageId,
          )
        else
          msg
    ];
  }
  
  // Clear all messages
  void clearHistory() {
    state = [];
  }
}
```

---

## Critical Design Patterns

### 1. Session ID Propagation Flow

```
App Start
   â”‚
   â”œâ”€â–º Voice WebSocket connects with session_id=null
   â”‚      â”‚
   â”‚      â””â”€â–º Server creates new session, returns session_id
   â”‚             â”‚
   â”‚             â””â”€â–º SessionNotifier.setSession(sessionId)
   â”‚                    â”‚
   â”‚                    â””â”€â–º session_id stored in app state
   â”‚
   â””â”€â–º User opens Text Chat
          â”‚
          â””â”€â–º Text WebSocket connects with session_id from SessionNotifier
                 â”‚
                 â””â”€â–º Server adds to existing session conversation
                        â”‚
                        â””â”€â–º Both WebSockets now share history
```

**Implementation Note:** The first WebSocket to connect creates the session. The second must read and reuse that session_id.

### 2. Independent Connection States

```dart
// UI can show connection status for BOTH modes independently
class StatusBar extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final audioConn = ref.watch(audioConnectionProvider);
    final textConn = ref.watch(textConnectionProvider);
    
    return Row(
      children: [
        ConnectionIndicator(
          label: 'Voice',
          status: audioConn,
        ),
        ConnectionIndicator(
          label: 'Text',
          status: textConn,
        ),
      ],
    );
  }
}
```

### 3. Shared Conversation Display

```dart
// Both voice and text modes can view the same conversation
class MessageList extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final messages = ref.watch(conversationProvider);  // Shared state
    
    return ListView.builder(
      itemCount: messages.length,
      itemBuilder: (context, index) {
        final message = messages[index];
        return MessageBubble(
          role: message.role,
          content: message.content,
          timestamp: message.timestamp,
        );
      },
    );
  }
}
```

### 4. Service Initialization Order

Riverpod handles dependency ordering automatically:

```dart
// Declaring dependencies with ref.watch() ensures proper order
final textWebSocketProvider = Provider<TextWebSocketService>((ref) {
  final config = ref.watch(configServiceProvider);      // â† Created FIRST
  final session = ref.watch(sessionProvider.notifier);  // â† Created SECOND
  
  return TextWebSocketService(/* uses config and session */);
});

// When UI requests textWebSocketProvider:
// 1. Riverpod sees it needs configServiceProvider
// 2. Creates ConfigService
// 3. Riverpod sees it needs sessionProvider
// 4. Creates SessionNotifier
// 5. Creates TextWebSocketService
// 6. Returns to UI
```

---

## Key Differences from Original Discussion

### What Changed After Code Analysis

**Before:** Assumed single WebSocket with message routing  
**After:** Discovered two truly independent WebSocket connections

**Before:** Thought services might share connection  
**After:** Each mode has dedicated connection, only session_id is shared

**Before:** Unclear how conversation sync worked  
**After:** Server-side session management with shared history array

**Before:** Uncertain about streaming text pattern  
**After:** Clear `is_delta` flag for append vs. new message

### Architectural Insights

1. **Dual WebSocket Architecture**
   - Reduces coupling between voice and text modes
   - Allows independent connection lifecycles
   - Simplifies error handling per mode
   - Enables true parallel operation

2. **Server-Side Session Management**
   - Client doesn't manage conversation history locally
   - Server is source of truth
   - Enables session resumption after disconnect
   - Automatic cleanup of old sessions

3. **Threading Pattern in PyQt6**
   - WebSocket operations in separate threads
   - Qt signals for thread-safe UI updates
   - Asyncio event loops in worker threads
   
   **Flutter Equivalent:**
   - No separate threads needed (Dart isolates if necessary)
   - StreamController for async communication
   - setState() / StateNotifier for UI updates

---

## Open Questions & Design Decisions

### ðŸ”´ CRITICAL: Must Decide Before Implementation

#### 1. Auto-Connect Behavior

**Audio WebSocket:**
- [ ] **Option A:** Auto-connect on app start (like current PyQt6 client)
  - Pros: Instant wake word listening, no user action needed
  - Cons: Always-on connection, consumes resources
  
- [ ] **Option B:** Manual connect via UI button
  - Pros: User control, battery-friendly for mobile
  - Cons: Extra step before using voice

**Text WebSocket:**
- [ ] **Option A:** Auto-connect when chat window opens
  - Pros: Immediate readiness, seamless UX
  - Cons: Connection even if user doesn't send message
  
- [ ] **Option B:** Connect on first message send
  - Pros: Lazy loading, no wasted connections
  - Cons: First message has connection delay

**Current PyQt6 Behavior:** Audio auto-connects on app start, text auto-connects when window opens.

#### 2. Session Persistence

**Question:** Should session_id be saved to local storage and restored on app restart?

- [ ] **Option A:** Ephemeral sessions (current behavior)
  - New session_id on every app start
  - Conversation history lost on restart
  - Server cleans up after 1 hour
  
- [ ] **Option B:** Persistent sessions
  - Save session_id to SharedPreferences/SecureStorage
  - Restore on app restart
  - Resume conversation where user left off
  
- [ ] **Option C:** Hybrid approach
  - Persist session_id for N hours (e.g., 8 hours)
  - If older than N hours, start fresh session
  - Provide "Clear History" button in UI

**Recommendation:** Option C provides best UX while respecting server's 1-hour cleanup.

#### 3. Connection Failure Handling

**Question:** What happens if one WebSocket fails but the other is connected?

- [ ] **Voice WebSocket fails, Text WebSocket active:**
  - Continue allowing text chat?
  - Disable voice UI but keep text functional?
  - Show error banner but maintain session?
  
- [ ] **Text WebSocket fails, Voice WebSocket active:**
  - Continue voice conversations?
  - Disable text chat UI?
  - Allow voice mode independently?

**Current PyQt6 Behavior:** Modes are truly independentâ€”if one fails, the other continues.

#### 4. Mobile-Specific Considerations

**Background Audio:**
- How to handle wake word detection when app is backgrounded?
- iOS/Android background audio permissions
- Battery optimization strategies

**Network Changes:**
- Auto-reconnect on WiFi/cellular switch?
- Buffering strategy during poor connectivity?
- Offline mode capabilities?

### ðŸŸ¡ MEDIUM PRIORITY: Can Decide During Implementation

#### 5. Streaming Text Display Strategy

**Question:** How to handle partial text streaming in UI?

- [ ] **Option A:** Character-by-character append
  - Most responsive, shows all tokens immediately
  - Can feel jittery for user
  
- [ ] **Option B:** Word-level buffering
  - Smoother display
  - Slight delay (10-50ms)
  
- [ ] **Option C:** Sentence-level buffering
  - Natural reading experience
  - Longer delay before first display

**Current PyQt6 Behavior:** Character-level with cursor position management to prevent duplication.

#### 6. Audio Playback Strategy

**Question:** How to handle audio chunk streaming?

- [ ] **Queue-based:** Buffer chunks and play sequentially
- [ ] **Direct playback:** Play each chunk immediately as received
- [ ] **Hybrid:** Small buffer (100-200ms) then continuous playback

**Current PyQt6 Behavior:** Direct playback with deque for echo cancellation reference.

#### 7. State Machine Complexity

The PyQt6 client has 7 voice states. Flutter needs:

- [ ] **Option A:** Full state machine (all 7 states)
  - Matches current behavior exactly
  - More complex to implement
  
- [ ] **Option B:** Simplified states (3-4 states)
  - Easier to maintain
  - May lose some status granularity
  
- [ ] **Option C:** State per feature
  - Separate recording state, speaking state, wake state
  - More flexible, easier to test

**States from PyQt6:**
1. idle
2. calibrating (mic noise floor)
3. listening_wake (waiting for wake word)
4. active_conversation
5. recording_command
6. processing (waiting for AI response)
7. speaking (playing audio)

### ðŸŸ¢ LOW PRIORITY: Can Be Decided Later

#### 8. Wake Word Implementation

**Question:** Use same openWakeWord library or Flutter alternative?

- [ ] **Option A:** openWakeWord via Flutter FFI
  - Proven to work (current system)
  - Requires native bridge
  
- [ ] **Option B:** Flutter wake word package
  - Pure Dart, easier integration
  - May have different accuracy
  
- [ ] **Option C:** Server-side wake word detection
  - Move complexity to server
  - Requires always-streaming audio

#### 9. UI Framework Choice

**Question:** Material Design, Cupertino, or custom?

- [ ] Material Design 3 (Android-style)
- [ ] Cupertino (iOS-style)
- [ ] Adaptive (Material on Android, Cupertino on iOS)
- [ ] Custom design system

**Current PyQt6:** Windows 11 native styling

#### 10. Configuration Management

**Question:** How to load config.ini equivalent in Flutter?

- [ ] YAML config file (pubspec.yaml style)
- [ ] JSON config file
- [ ] Environment variables
- [ ] Hardcoded defaults with runtime overrides

**Current PyQt6:** `config.ini` with ConfigParser

---

## Implementation Roadmap Suggestion

### Phase 1: Foundation (Week 1)
1. âœ… **Project setup:** Flutter 3.x, Riverpod 2.x
2. âœ… **Basic providers:** ConfigService, SessionNotifier
3. âœ… **WebSocket services:** AudioWebSocketService, TextWebSocketService (no audio I/O yet)
4. âœ… **Conversation state:** ConversationNotifier with streaming support
5. âœ… **Simple UI:** Display messages, connection status

**Goal:** Can send/receive text messages, see shared conversation.

### Phase 2: Text Mode (Week 2)
1. Text input field
2. Message list with user/assistant bubbles
3. Streaming text display (character-by-character)
4. Connection status indicators
5. Session management (new/resume)

**Goal:** Full-featured text chat with orchestrator.

### Phase 3: Audio I/O (Week 3)
1. AudioService implementation (microphone, speakers)
2. Record audio â†’ base64 â†’ send via WebSocket
3. Receive audio chunks â†’ playback
4. Recording state management
5. Playing state management

**Goal:** Can speak to AI and hear responses.

### Phase 4: Voice Pipeline (Week 4)
1. Wake word detection (openWakeWord integration)
2. Voice state machine (idle â†’ listening â†’ recording â†’ processing â†’ speaking)
3. VAD (Voice Activity Detection)
4. Microphone calibration
5. Echo cancellation (subtract AI voice from mic input)

**Goal:** Full voice assistant functionality matching PyQt6 client.

### Phase 5: Polish & Mobile (Week 5-6)
1. Mobile-specific UI (system tray â†’ mobile app UI)
2. Background audio handling
3. Network change handling (reconnection)
4. Settings screen (config management)
5. Persistent sessions (SharedPreferences)
6. Error handling & user feedback

**Goal:** Production-ready mobile app.

---

## Testing Strategy

### Unit Tests
- [ ] ConfigService loads correctly
- [ ] SessionNotifier state transitions
- [ ] ConversationNotifier message operations
- [ ] WebSocket message parsing

### Integration Tests
- [ ] WebSocket connection flow
- [ ] Session ID propagation
- [ ] Message streaming (text and audio)
- [ ] Error recovery

### Widget Tests
- [ ] Message list renders correctly
- [ ] Input field submits messages
- [ ] Connection indicators update
- [ ] State changes trigger rebuilds

### E2E Tests
- [ ] Complete voice conversation
- [ ] Complete text conversation
- [ ] Switch between voice and text
- [ ] Session resumption after disconnect

---

## Dependencies

### Core Flutter Packages
```yaml
dependencies:
  flutter:
    sdk: flutter
  
  # State management
  flutter_riverpod: ^2.5.1
  
  # WebSockets
  web_socket_channel: ^2.4.0
  
  # Audio I/O
  record: ^5.0.1              # Microphone recording
  audioplayers: ^5.2.1         # Audio playback
  
  # Persistence
  shared_preferences: ^2.2.2   # Session ID storage
  
  # UI helpers
  intl: ^0.18.1                # Date/time formatting
```

### Native Integration (Later Phases)
- Wake word detection (openWakeWord FFI or Dart package)
- Platform-specific audio handling (iOS/Android)
- Background service (mobile)

---

## File Structure Recommendation

```
lib/
â”œâ”€â”€ main.dart                          # App entry, ProviderScope
â”œâ”€â”€ models/
â”‚   â”œâ”€â”€ chat_message.dart              # ChatMessage class
â”‚   â”œâ”€â”€ session_state.dart             # SessionState class
â”‚   â””â”€â”€ connection_status.dart         # ConnectionStatus enum
â”œâ”€â”€ services/
â”‚   â”œâ”€â”€ config_service.dart            # Configuration management
â”‚   â”œâ”€â”€ audio_websocket_service.dart   # Voice WebSocket
â”‚   â”œâ”€â”€ text_websocket_service.dart    # Text WebSocket
â”‚   â”œâ”€â”€ audio_service.dart             # Mic + speaker I/O
â”‚   â””â”€â”€ wake_word_service.dart         # Wake word detection
â”œâ”€â”€ providers/
â”‚   â”œâ”€â”€ config_provider.dart           # configServiceProvider
â”‚   â”œâ”€â”€ session_provider.dart          # sessionProvider
â”‚   â”œâ”€â”€ conversation_provider.dart     # conversationProvider
â”‚   â”œâ”€â”€ connection_providers.dart      # audio/text connection
â”‚   â”œâ”€â”€ voice_state_provider.dart      # voiceStateProvider
â”‚   â””â”€â”€ websocket_providers.dart       # WebSocket services
â”œâ”€â”€ screens/
â”‚   â”œâ”€â”€ home_screen.dart               # Main app screen
â”‚   â”œâ”€â”€ chat_screen.dart               # Text chat UI
â”‚   â””â”€â”€ settings_screen.dart           # Configuration
â””â”€â”€ widgets/
    â”œâ”€â”€ message_list.dart              # Scrollable message list
    â”œâ”€â”€ message_bubble.dart            # Single message display
    â”œâ”€â”€ text_input.dart                # Message input field
    â”œâ”€â”€ status_bar.dart                # Connection indicators
    â””â”€â”€ voice_controls.dart            # Voice mode buttons
```

---

## Conclusion

This document provides a complete blueprint for implementing Sparky's Flutter client with Riverpod. The key architectural insightâ€”two independent WebSockets sharing a session_idâ€”simplifies the design and enables true parallel text/voice operation.

**Next Steps:**
1. Review open questions and make design decisions
2. Set up Flutter project with dependencies
3. Implement Phase 1 (Foundation)
4. Iterate based on testing feedback

**Critical Success Factors:**
- Maintain independence between audio and text WebSockets
- Implement proper session_id sharing mechanism
- Handle streaming text updates efficiently
- Build robust error handling for connection failures

---

## Appendix: Code References

### PyQt6 Client
- **Main file:** `sparky_tray_client.py` (1993 lines)
- **WebSocketWorker:** Lines 144-393
- **ChatWindow:** Lines 396-1200
- **VoiceAssistant:** Lines 1201-1776

### Orchestrator
- **Main file:** `sparky_orchestrator_ws.py` (1141 lines)
- **Conversation endpoint:** Lines 695-960 (`/ws/conversation`)
- **Session management:** Lines 598-694 (`ConversationSession` class)
- **Message protocol:** Lines 695-960 (handler logic)

### Key Configuration Values
- **Server:** 10.6.1.15
- **Ports:** Orchestrator 8006, Whisper 8005, TTS 8004
- **Audio:** 16kHz sample rate, mono channel
- **TTS:** 24kHz sample rate for playback
- **Default voice:** 'ara'
- **Session timeout:** 1 hour
- **Max conversation history:** 50 messages

---

**Document Version:** 1.0  
**Last Updated:** 2025-11-02  
**Next Review:** After Phase 1 implementation
