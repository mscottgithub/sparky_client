import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sparky_client/services/audio_playback_service.dart';

/// Audio playback service provider
final audioPlaybackServiceProvider =
    Provider<AudioPlaybackService>((ref) {
  final service = AudioPlaybackService();

  // Cleanup on dispose
  ref.onDispose(() {
    service.dispose();
  });

  return service;
});

