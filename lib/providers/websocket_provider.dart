import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sparky_client/services/text_websocket_service.dart';
import 'package:sparky_client/providers/config_provider.dart';
import 'package:sparky_client/providers/session_provider.dart';
import 'package:sparky_client/providers/conversation_provider.dart';
import 'package:sparky_client/providers/connection_provider.dart';

/// Text WebSocket service provider
/// Provides the text WebSocket service instance
final textWebSocketProvider = Provider<TextWebSocketService>((ref) {
  final config = ref.watch(configProvider);
  final sessionNotifier = ref.read(sessionProvider.notifier);
  final conversationNotifier = ref.read(conversationProvider.notifier);
  final connectionNotifier = ref.read(textConnectionProvider.notifier);

  final service = TextWebSocketService(
    url: config.orchestratorWebSocketUrl,
    defaultVoice: config.defaultVoice,
    sessionNotifier: sessionNotifier,
    conversationNotifier: conversationNotifier,
    connectionNotifier: connectionNotifier,
  );

  // Cleanup on dispose
  ref.onDispose(() {
    service.disconnect();
  });

  return service;
});

