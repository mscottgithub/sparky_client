import 'dart:async';
import 'dart:convert';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:sparky_client/models/chat_message.dart';
import 'package:sparky_client/providers/session_provider.dart';
import 'package:sparky_client/providers/conversation_provider.dart';
import 'package:sparky_client/providers/connection_provider.dart';

/// Text WebSocket service for conversation with orchestrator
/// Handles text-only chat mode with streaming responses
class TextWebSocketService {
  final String url;
  final String defaultVoice;
  final SessionNotifier sessionNotifier;
  final ConversationNotifier conversationNotifier;
  final ConnectionNotifier connectionNotifier;

  WebSocketChannel? _channel;
  StreamSubscription<dynamic>? _subscription;
  bool _isConnected = false;
  String? _currentStreamingMessageId;
  Timer? _reconnectTimer;
  int _reconnectAttempts = 0;
  String? _lastSessionId;
  static const int _maxReconnectAttempts = 10;
  static const Duration _initialReconnectDelay = Duration(seconds: 1);

  TextWebSocketService({
    required this.url,
    required this.defaultVoice,
    required this.sessionNotifier,
    required this.conversationNotifier,
    required this.connectionNotifier,
  });

  /// Connect to WebSocket with optional session_id
  Future<void> connect(String? sessionId) async {
    if (_isConnected) {
      print('WebSocket already connected');
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
      print('WebSocket connected');
    } catch (e) {
      print('WebSocket connection error: $e');
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
    connectionNotifier.disconnected();
    print('WebSocket disconnected');
  }

  /// Handle incoming messages
  void _handleMessage(dynamic data) {
    if (data is String) {
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
    }
  }

  /// Handle meta events (session_id, thinking, etc.)
  void _handleMeta(Map<String, dynamic> msg) {
    final event = msg['event'] as String?;

    switch (event) {
      case 'session_id':
        final sessionId = msg['value'] as String?;
        if (sessionId != null) {
          sessionNotifier.setSession(sessionId);
          print('Session ID received: $sessionId');
        }
        break;
      case 'thinking':
        print('AI is thinking...');
        // Could show a loading indicator here
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

  /// Handle done event (conversation turn complete)
  void _handleDone() {
    _currentStreamingMessageId = null;
    print('Conversation turn complete');
  }

  /// Handle errors
  void _handleError(error) {
    print('WebSocket error: $error');
    if (_isConnected) {
      _isConnected = false;
      connectionNotifier.error();
      _scheduleReconnect();
    }
  }

  /// Handle disconnect
  void _handleDisconnect() {
    print('WebSocket disconnected');
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
      print('Reconnecting (attempt $_reconnectAttempts)...');
      connect(_lastSessionId);
    });
  }

  /// Send text message to orchestrator
  void sendText(String text) {
    if (!_isConnected || text.trim().isEmpty) {
      if (!_isConnected) {
        print('Cannot send text: not connected');
      }
      return;
    }

    // Add user message to conversation immediately
    conversationNotifier.addMessage(ChatMessage.user(text));

    // Send text_chat message to orchestrator
    final msg = {
      'type': 'text_chat',
      'text': text.trim(),
    };
    _channel!.sink.add(json.encode(msg));
    print('Sent text message: ${text.substring(0, text.length.clamp(0, 50))}...');
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

