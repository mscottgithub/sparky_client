import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Recording state model
class RecordingState {
  final bool isRecording;
  final double microphoneLevel; // 0.0 to 1.0
  final bool hasPermission;
  final String? error;

  const RecordingState({
    this.isRecording = false,
    this.microphoneLevel = 0.0,
    this.hasPermission = false,
    this.error,
  });

  RecordingState copyWith({
    bool? isRecording,
    double? microphoneLevel,
    bool? hasPermission,
    String? error,
  }) {
    return RecordingState(
      isRecording: isRecording ?? this.isRecording,
      microphoneLevel: microphoneLevel ?? this.microphoneLevel,
      hasPermission: hasPermission ?? this.hasPermission,
      error: error ?? this.error,
    );
  }
}

/// Recording state notifier
class RecordingNotifier extends StateNotifier<RecordingState> {
  RecordingNotifier() : super(const RecordingState());

  void setRecording(bool recording) {
    state = state.copyWith(isRecording: recording);
  }

  void setMicrophoneLevel(double level) {
    state = state.copyWith(microphoneLevel: level.clamp(0.0, 1.0));
  }

  void setPermission(bool hasPermission) {
    state = state.copyWith(hasPermission: hasPermission);
  }

  void setError(String? error) {
    state = state.copyWith(error: error);
  }

  void reset() {
    state = const RecordingState();
  }
}

/// Recording state provider
final recordingProvider =
    StateNotifierProvider<RecordingNotifier, RecordingState>((ref) {
  return RecordingNotifier();
});

