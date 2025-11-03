import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:sparky_client/models/chat_message.dart';
import 'package:sparky_client/providers/session_provider.dart';
import 'package:sparky_client/providers/conversation_provider.dart';
import 'package:sparky_client/providers/connection_provider.dart';
import 'package:sparky_client/services/audio_playback_service.dart';

/// Audio WebSocket service for voice mode conversation
/// Handles audio messages, transcriptions, streaming text, and binary audio chunks
class AudioWebSocketService {
  final String url;
  final String defaultVoice;
  final SessionNotifier sessionNotifier;
  final ConversationNotifier conversationNotifier;
  final ConnectionNotifier connectionNotifier;
  AudioPlaybackService? _audioPlayback;

  WebSocketChannel? _channel;
  StreamSubscription<dynamic>? _subscription;
  bool _isConnected = false;
  String? _currentStreamingMessageId;
  Timer? _reconnectTimer;
  int _reconnectAttempts = 0;
  String? _lastSessionId;
  static const int _maxReconnectAttempts = 10;
  static const Duration _initialReconnectDelay = Duration(seconds: 1);

  // Audio buffer for collecting chunks before sending "final"
  List<Uint8List>? _currentAudioChunks;

  AudioWebSocketService({
    required this.url,
    required this.defaultVoice,
    required this.sessionNotifier,
    required this.conversationNotifier,
    required this.connectionNotifier,
    AudioPlaybackService? audioPlayback,
  }) : _audioPlayback = audioPlayback;
  
  /// Set audio playback service
  void setAudioPlayback(AudioPlaybackService playback) {
    _audioPlayback = playback;
  }

  /// Connect to WebSocket with optional session_id
  Future<void> connect(String? sessionId) async {
    if (_isConnected) {
      print('Audio WebSocket already connected');
      return;
    }

    try {
      connectionNotifier.connecting();

      // Store session ID for reconnection
      _lastSessionId = sessionId;

      _channel = WebSocketChannel.connect(Uri.parse(url));

      // Send START message (required first message)
      final startMsg = {
        'type': 'start',
        'voice': defaultVoice,
        'session_id': sessionId,
      };
      _channel!.sink.add(json.encode(startMsg));

      // Listen to incoming messages
      _subscription = _channel!.stream.listen(
        _handleMessage,
        onError: _handleError,
        onDone: _handleDisconnect,
      );

      _isConnected = true;
      _reconnectAttempts = 0;
      connectionNotifier.connected();
      print('Audio WebSocket connected');
    } catch (e) {
      print('Audio WebSocket connection error: $e');
      _isConnected = false;
      connectionNotifier.error();
      _scheduleReconnect();
    }
  }

  /// Disconnect from WebSocket
  void disconnect() {
    _reconnectTimer?.cancel();
    _subscription?.cancel();
    _channel?.sink.close();
    _isConnected = false;
    _currentStreamingMessageId = null;
    _currentAudioChunks = null;
    connectionNotifier.disconnected();
    print('Audio WebSocket disconnected');
  }

  /// Handle incoming messages (JSON or binary)
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
          case 'text_token':
            _handleTextToken(msg);
            break;
          case 'text_response':
            _handleTextResponse(msg);
            break;
          case 'done':
            _handleDone();
            break;
          case 'error':
            _handleError(msg['detail'] ?? 'Unknown error');
            break;
          default:
            print('Unknown message type: $type');
        }
      } catch (e) {
        print('Error parsing JSON message: $e');
      }
    } else if (data is Uint8List || data is List<int>) {
      // Binary audio chunk from TTS
      _handleAudioChunk(data is Uint8List ? data : Uint8List.fromList(data));
    }
  }

  /// Handle meta events (session_id, transcription, thinking, etc.)
  void _handleMeta(Map<String, dynamic> msg) {
    final event = msg['event'] as String?;

    switch (event) {
      case 'session_id':
        final sessionId = msg['value'] as String?;
        if (sessionId != null) {
          sessionNotifier.setSession(sessionId);
          print('Audio session ID received: $sessionId');
        }
        break;
      case 'transcription':
        final text = msg['text'] as String?;
        if (text != null && text.isNotEmpty) {
          // Add transcribed user message to conversation
          conversationNotifier.addMessage(ChatMessage.user(text));
          print('Transcription: $text');
        }
        break;
      case 'thinking':
        print('AI is thinking...');
        // Could show a loading indicator here
        break;
      case 'greeting':
        print('Greeting event received');
        break;
      case 'provider':
        final provider = msg['value'] as String?;
        print('TTS provider: $provider');
        break;
      case 'ttfa_ms':
        final ttfa = msg['value'];
        print('Time-to-first-audio: ${ttfa}ms');
        break;
      default:
        print('Meta event: $event');
    }
  }

  /// Handle streaming text token
  void _handleTextToken(Map<String, dynamic> msg) {
    final token = msg['token'] as String?;
    if (token == null || token.isEmpty) return;

    // Start streaming message if not already started
    if (_currentStreamingMessageId == null) {
      _currentStreamingMessageId = DateTime.now().millisecondsSinceEpoch.toString();
      conversationNotifier.addMessage(
        ChatMessage.assistant(
          token,
          messageId: _currentStreamingMessageId,
        ),
      );
    } else {
      // Append token to existing message
      conversationNotifier.appendToMessage(_currentStreamingMessageId!, token);
    }
  }

  /// Handle complete text response
  void _handleTextResponse(Map<String, dynamic> msg) {
    final text = msg['text'] as String?;
    if (text == null) return;

    // Replace the streaming message with complete response
    if (_currentStreamingMessageId != null) {
      conversationNotifier.updateMessage(_currentStreamingMessageId!, text);
    } else {
      // Create new message if no streaming was happening
      _currentStreamingMessageId = DateTime.now().millisecondsSinceEpoch.toString();
      conversationNotifier.addMessage(
        ChatMessage.assistant(
          text,
          messageId: _currentStreamingMessageId,
        ),
      );
    }
  }

  /// Handle binary audio chunk (TTS output)
  void _handleAudioChunk(Uint8List data) {
    print('Received audio chunk: ${data.length} bytes');
    
    // Send to audio playback service
    if (_audioPlayback != null) {
      _audioPlayback!.addAudioChunk(data);
      
      // Start playback if not already started
      if (!_audioPlayback!.isPlaying) {
        _audioPlayback!.startPlayback();
      }
    } else {
      print('Warning: Audio playback service not set');
    }
  }

  /// Handle done event (conversation turn complete)
  void _handleDone() {
    _currentStreamingMessageId = null;
    print('Audio conversation turn complete');
  }

  /// Handle errors
  void _handleError(error) {
    print('Audio WebSocket error: $error');
    if (_isConnected) {
      _isConnected = false;
      connectionNotifier.error();
      _scheduleReconnect();
    }
  }

  /// Handle disconnect
  void _handleDisconnect() {
    print('Audio WebSocket disconnected');
    _isConnected = false;
    connectionNotifier.disconnected();
    _scheduleReconnect();
  }

  /// Schedule automatic reconnection with exponential backoff
  void _scheduleReconnect() {
    if (_reconnectAttempts >= _maxReconnectAttempts) {
      print('Max reconnection attempts reached');
      return;
    }

    _reconnectTimer?.cancel();
    final delay = Duration(
      milliseconds: _initialReconnectDelay.inMilliseconds *
          (1 << _reconnectAttempts.clamp(0, 10)), // Exponential backoff, max 2^10
    );

    _reconnectTimer = Timer(delay, () {
      _reconnectAttempts++;
      print('Reconnecting audio WebSocket (attempt $_reconnectAttempts)...');
      connect(_lastSessionId);
    });
  }

  /// Start sending audio (initialize buffer)
  void startAudioMessage() {
    if (!_isConnected) {
      print('Cannot start audio message: not connected');
      return;
    }
    _currentAudioChunks = [];
  }

  /// Send audio chunk to orchestrator
  /// Audio should be base64-encoded in JSON format
  void sendAudioChunk(Uint8List audioData) {
    if (!_isConnected) {
      print('Cannot send audio chunk: not connected');
      return;
    }

    // Initialize chunks if not already started
    if (_currentAudioChunks == null) {
      startAudioMessage();
    }

    // Add to buffer
    _currentAudioChunks!.add(audioData);

    // Encode as base64 and send
    final base64Data = base64Encode(audioData);
    final msg = {
      'type': 'audio',
      'data': base64Data,
    };
    _channel!.sink.add(json.encode(msg));
  }

  /// Finalize audio message (send "final" to complete audio transmission)
  void finalizeAudioMessage() {
    if (!_isConnected || _currentAudioChunks == null) {
      if (_currentAudioChunks == null) {
        print('No audio message in progress');
      }
      return;
    }

    // Send final message
    final msg = {'type': 'final'};
    _channel!.sink.add(json.encode(msg));

    print('Audio message finalized (${_currentAudioChunks!.length} chunks)');
    _currentAudioChunks = null;
  }

  /// Send greeting message
  void sendGreeting() {
    if (!_isConnected) return;

    final msg = {'type': 'greeting'};
    _channel!.sink.add(json.encode(msg));
  }

  /// Send goodbye message
  void sendGoodbye() {
    if (!_isConnected) return;

    final msg = {'type': 'goodbye'};
    _channel!.sink.add(json.encode(msg));
  }

  /// Check if connected
  bool get isConnected => _isConnected;
}

