import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sparky_client/services/audio_websocket_service.dart';
import 'package:sparky_client/providers/config_provider.dart';
import 'package:sparky_client/providers/session_provider.dart';
import 'package:sparky_client/providers/conversation_provider.dart';
import 'package:sparky_client/providers/connection_provider.dart';
import 'package:sparky_client/providers/audio_playback_provider.dart';

/// Audio WebSocket service provider
final audioWebSocketProvider =
    Provider<AudioWebSocketService>((ref) {
  final config = ref.watch(configProvider);
  final sessionNotifier = ref.read(sessionProvider.notifier);
  final conversationNotifier = ref.read(conversationProvider.notifier);
  final connectionNotifier = ref.read(audioConnectionProvider.notifier);
  final audioPlayback = ref.read(audioPlaybackServiceProvider);

  final service = AudioWebSocketService(
    url: config.orchestratorWebSocketUrl,
    defaultVoice: config.defaultVoice,
    sessionNotifier: sessionNotifier,
    conversationNotifier: conversationNotifier,
    connectionNotifier: connectionNotifier,
    audioPlayback: audioPlayback,
  );

  // Cleanup on dispose
  ref.onDispose(() {
    service.disconnect();
  });

  return service;
});

