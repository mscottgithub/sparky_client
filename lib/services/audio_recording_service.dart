import 'dart:async';
import 'dart:typed_data';
import 'package:record/record.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:sparky_client/services/config_service.dart';

/// Audio recording service for microphone input
/// Handles recording, permissions, and audio streaming
class AudioRecordingService {
  final AudioRecorder _recorder = AudioRecorder();
  final ConfigService configService;
  
  StreamController<Uint8List>? _audioStreamController;
  StreamSubscription<Uint8List>? _recordingSubscription;
  bool _isRecording = false;
  
  // Microphone level tracking
  StreamController<double>? _levelStreamController;
  Timer? _levelTimer;
  
  AudioRecordingService({required this.configService});

  /// Check and request microphone permission
  Future<bool> checkPermission() async {
    try {
      // Check current status
      final status = await Permission.microphone.status;
      
      if (status.isGranted) {
        return true;
      }
      
      // Request permission if not granted
      if (status.isDenied) {
        final result = await Permission.microphone.request();
        return result.isGranted;
      }
      
      // Permission is permanently denied
      if (status.isPermanentlyDenied) {
        print('Microphone permission is permanently denied');
        return false;
      }
      
      return false;
    } catch (e) {
      print('Error checking microphone permission: $e');
      return false;
    }
  }

  /// Start recording audio stream
  /// Returns true if recording started successfully
  Future<bool> startRecording({
    required Function(Uint8List) onAudioChunk,
    Function(double)? onLevelUpdate, // Microphone level callback (0.0 - 1.0)
  }) async {
    if (_isRecording) {
      print('Recording already in progress');
      return false;
    }

    // Check permissions first
    final hasPermission = await checkPermission();
    if (!hasPermission) {
      print('Microphone permission not granted');
      return false;
    }

    try {
      // Check if recorder is available
      if (!await _recorder.hasPermission()) {
        print('Recorder does not have permission');
        return false;
      }

      // Create stream controller for audio chunks
      _audioStreamController = StreamController<Uint8List>(
        onCancel: () {
          _stopRecording();
        },
      );

      // Listen to audio stream
      _recordingSubscription = _audioStreamController!.stream.listen(
        onAudioChunk,
        onError: (error) {
          print('Error in audio stream: $error');
        },
      );

      // Start recording stream with 16kHz mono PCM (as per config)
      final stream = await _recorder.startStream(
        const RecordConfig(
          encoder: AudioEncoder.pcm16bits,
          sampleRate: 16000,
          numChannels: 1,
        ),
      );

      // Listen to stream and buffer chunks
      stream.listen(
        (data) {
          // Stream returns Uint8List chunks
          final audioChunk = data;
          
          // Forward to stream controller
          _audioStreamController?.add(audioChunk);
          
          // Calculate and report microphone level if callback provided
          if (onLevelUpdate != null) {
            _calculateAudioLevel(audioChunk, onLevelUpdate);
          }
        },
        onError: (error) {
          print('Error in recording stream: $error');
          _stopRecording();
        },
        cancelOnError: false,
      );

      _isRecording = true;
      print('Recording started');
      return true;
    } catch (e) {
      print('Error starting recording: $e');
      _stopRecording();
      return false;
    }
  }

  /// Stop recording
  Future<void> stopRecording() async {
    await _stopRecording();
  }

  /// Internal method to stop recording
  Future<void> _stopRecording() async {
    if (!_isRecording) return;

    try {
      // Stop the recorder
      await _recorder.stop();
      
      // Cancel subscriptions
      await _recordingSubscription?.cancel();
      _recordingSubscription = null;
      
      // Close stream controller
      await _audioStreamController?.close();
      _audioStreamController = null;
      
      // Stop level timer
      _levelTimer?.cancel();
      _levelTimer = null;
      
      _isRecording = false;
      print('Recording stopped');
    } catch (e) {
      print('Error stopping recording: $e');
      _isRecording = false;
    }
  }

  /// Calculate audio level (amplitude) from PCM data
  /// Returns value between 0.0 and 1.0
  void _calculateAudioLevel(Uint8List audioData, Function(double) callback) {
    try {
      if (audioData.isEmpty) {
        callback(0.0);
        return;
      }

      // Ensure we have an even number of bytes for 16-bit samples
      // If odd, truncate to even length
      final evenLength = (audioData.length ~/ 2) * 2;
      if (evenLength == 0) {
        callback(0.0);
        return;
      }

      // Create a view with aligned length (must be multiple of 2 for Int16)
      final alignedData = evenLength < audioData.length
          ? audioData.sublist(0, evenLength)
          : audioData;

      // Convert bytes to 16-bit integers
      // Use buffer view only if data is properly aligned, otherwise create new list
      Int16List samples;
      try {
        samples = Int16List.view(alignedData.buffer, alignedData.offsetInBytes, alignedData.length ~/ 2);
      } catch (e) {
        // If view fails (misaligned), convert manually
        samples = Int16List(alignedData.length ~/ 2);
        for (int i = 0; i < samples.length; i++) {
          final byteIndex = i * 2;
          samples[i] = (alignedData[byteIndex] | (alignedData[byteIndex + 1] << 8));
          // Convert unsigned to signed
          if (samples[i] > 32767) samples[i] -= 65536;
        }
      }
      
      // Calculate RMS (Root Mean Square) for amplitude
      if (samples.isEmpty) {
        callback(0.0);
        return;
      }
      
      double sum = 0.0;
      for (final sample in samples) {
        final normalized = sample / 32768.0; // Normalize to -1.0 to 1.0
        sum += normalized * normalized;
      }
      
      final rms = (sum / samples.length);
      final level = (rms * 10).clamp(0.0, 1.0); // Scale and clamp to 0-1
      
      callback(level);
    } catch (e) {
      print('Error calculating audio level: $e');
      callback(0.0);
    }
  }

  /// Check if currently recording
  bool get isRecording => _isRecording;

  /// Dispose resources
  Future<void> dispose() async {
    await _stopRecording();
    await _levelStreamController?.close();
    await _recorder.dispose();
  }
}

