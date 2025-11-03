import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sparky_client/services/audio_recording_service.dart';
import 'package:sparky_client/providers/config_provider.dart';

/// Audio recording service provider
final audioRecordingServiceProvider =
    Provider<AudioRecordingService>((ref) {
  final config = ref.watch(configProvider);
  return AudioRecordingService(configService: config);
});

