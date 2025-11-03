import 'dart:async';
import 'dart:typed_data';
import 'dart:io';
import 'package:mp_audio_stream/mp_audio_stream.dart';

/// Audio streaming playback service using mp_audio_stream for TRUE PCM streaming
/// Replaces file-based approach with direct PCM sample streaming (like Python sounddevice)
/// 
/// Server sends: 24kHz, mono, 16-bit PCM as Uint8List
/// mp_audio_stream needs: Float32List (normalized -1.0 to 1.0)
class AudioStreamPlaybackService {
  AudioStream? _audioStream;
  bool _isInitialized = false;
  bool _isPlaying = false;
  bool _hasError = false;
  
  // Buffer for accumulating audio chunks before playback starts
  final List<Uint8List> _audioBuffer = [];
  
  // Configuration
  static const int _sampleRate = 24000; // Server sends 24kHz
  static const int _channels = 1; // Mono
  static const int _bufferSizeMs = 3000; // 3 seconds buffer (configurable)
  static const int _initialBufferSize = 4096; // ~0.085 seconds at 24kHz mono 16-bit
  
  // Track when playback started for latency measurement
  DateTime? _playbackStartTime;
  DateTime? _firstChunkTime;
  
  // Timer for periodic buffer status checks
  Timer? _bufferStatusTimer;

  AudioStreamPlaybackService() {
    print('[AudioStream] Service created - will initialize on Windows');
  }

  /// Initialize the audio stream
  /// Returns true if successful, false otherwise
  Future<bool> _initialize() async {
    if (_isInitialized) {
      return true;
    }

    try {
      print('[AudioStream] Attempting to initialize mp_audio_stream...');
      
      // Get audio stream instance
      _audioStream = getAudioStream();
      
      // Initialize with 24kHz sample rate and mono channel (1 channel)
      // CRITICAL: sampleRate must match server (24kHz) - default is 44.1kHz which causes chipmunk audio!
      // API: init({int bufferMilliSec = 3000, int waitingBufferMilliSec = 100, int channels = 1, int sampleRate = 44100})
      print('[AudioStream] Initializing with sampleRate: 24000 Hz, channels: 1, bufferMilliSec: 3000');
      final result = _audioStream!.init(
        sampleRate: 24000,       // EXPLICIT 24000 - must match server TTS output exactly (default is 44100!)
        channels: 1,              // EXPLICIT 1 (mono)
        bufferMilliSec: 3000,     // 3 second buffer
        waitingBufferMilliSec: 100, // Wait 100ms before starting playback
      );
      
      // init() returns 0 on success, non-zero on error
      if (result != 0) {
        throw Exception('mp_audio_stream init() returned error code: $result');
      }
      
      // CRITICAL: Call resume() to activate playback (required for web, recommended for all platforms)
      print('[AudioStream] Calling resume() to activate audio stream...');
      _audioStream!.resume();
      
      _isInitialized = true;
      _hasError = false;
      print('[AudioStream] ✅ Successfully initialized - sampleRate: 24000 Hz, channels: 1, init result: $result');
      print('[AudioStream] ✅ PLAYBACK ACTIVATED via resume()');
      return true;
    } catch (e, stackTrace) {
      print('[AudioStream] ERROR: Failed to initialize: $e');
      print('[AudioStream] Stack trace: $stackTrace');
      _hasError = true;
      return false;
    }
  }

  /// Convert Uint8List (raw PCM bytes) to Float32List (normalized -1.0 to 1.0)
  /// Server sends: 16-bit signed integers (little-endian) as bytes
  /// Conversion: Uint8List → Int16List → Float32List (normalized)
  Float32List _convertToFloat32(Uint8List bytes) {
    // Convert bytes to Int16List (16-bit signed integers)
    // Each sample is 2 bytes (little-endian)
    final int16Samples = bytes.buffer.asInt16List(0, bytes.length ~/ 2);
    
    // Convert to Float32List and normalize (-32768 to 32767 → -1.0 to 1.0)
    final floatSamples = Float32List(int16Samples.length);
    for (int i = 0; i < int16Samples.length; i++) {
      floatSamples[i] = int16Samples[i] / 32768.0;
      // Clamp to valid range (shouldn't be needed, but safety check)
      if (floatSamples[i] > 1.0) floatSamples[i] = 1.0;
      if (floatSamples[i] < -1.0) floatSamples[i] = -1.0;
    }
    
    return floatSamples;
  }

  /// Add audio chunk to buffer/stream
  /// Chunks arrive as Uint8List (raw PCM 16-bit samples)
  void addAudioChunk(Uint8List chunk) {
    if (_hasError) {
      print('[AudioStream] ERROR: Service has error state, ignoring chunk');
      return;
    }

    // Track first chunk arrival time for latency measurement
    if (_firstChunkTime == null) {
      _firstChunkTime = DateTime.now();
      print('[AudioStream] First chunk received: ${chunk.length} bytes');
    }

    // If not initialized, try to initialize (Windows check)
    if (!_isInitialized && Platform.isWindows) {
      _initialize().then((success) {
        if (success) {
          // Process buffered chunks
          _processBufferedChunks();
        }
      });
    }

    // Add to buffer
    _audioBuffer.add(chunk);
    
    // Limit buffer size to prevent memory issues
    final totalBufferSize = _getTotalBufferSize();
    final maxBufferSize = _sampleRate * _channels * 2 * (_bufferSizeMs / 1000); // 2 bytes per sample
    if (totalBufferSize > maxBufferSize) {
      print('[AudioStream] WARNING: Buffer size limit reached ($totalBufferSize bytes), dropping oldest');
      while (_audioBuffer.isNotEmpty && _getTotalBufferSize() > maxBufferSize * 0.8) {
        _audioBuffer.removeAt(0);
      }
    }

    // If initialized and playing, push directly to stream
    if (_isInitialized && _isPlaying && _audioStream != null) {
      try {
        final floatSamples = _convertToFloat32(chunk);
        final pushResult = _audioStream!.push(floatSamples);
        
        // push() returns 0 on success, non-zero when buffer is full (data ignored)
        if (pushResult != 0) {
          print('[AudioStream] ⚠️ WARNING: push() returned $pushResult - buffer may be full! Chunk ignored (${chunk.length} bytes, ${floatSamples.length} samples)');
          
          // Check buffer statistics
          final stats = _audioStream!.stat();
          print('[AudioStream] Buffer stats - full: ${stats.full}, exhaust: ${stats.exhaust}');
        } else {
          print('[AudioStream] ✅ Fed ${chunk.length} bytes (${floatSamples.length} samples) to stream successfully');
        }
      } catch (e) {
        print('[AudioStream] ERROR pushing chunk: $e');
        _hasError = true;
      }
    }
  }

  /// Process all buffered chunks and push to stream
  void _processBufferedChunks() {
    if (!_isInitialized || _audioStream == null || _audioBuffer.isEmpty) {
      return;
    }

    try {
      print('[AudioStream] Processing ${_audioBuffer.length} buffered chunks...');
      
      // Combine all buffered chunks
      final totalSize = _getTotalBufferSize();
      final combined = Uint8List(totalSize);
      int offset = 0;
      for (final chunk in _audioBuffer) {
        combined.setRange(offset, offset + chunk.length, chunk);
        offset += chunk.length;
      }
      _audioBuffer.clear();

      // Convert and push
      final floatSamples = _convertToFloat32(combined);
      final pushResult = _audioStream!.push(floatSamples);
      
      // push() returns 0 on success, non-zero when buffer is full
      if (pushResult != 0) {
        print('[AudioStream] ⚠️ WARNING: push() returned $pushResult - buffer may be full! Buffered data ignored (${floatSamples.length} samples)');
        final stats = _audioStream!.stat();
        print('[AudioStream] Buffer stats - full: ${stats.full}, exhaust: ${stats.exhaust}');
      } else {
        print('[AudioStream] ✅ Pushed ${floatSamples.length} samples to stream successfully');
      }
    } catch (e) {
      print('[AudioStream] ERROR processing buffered chunks: $e');
      _hasError = true;
    }
  }

  /// Start playing audio chunks as they arrive
  /// Waits for initial buffer, then streams continuously
  Future<void> startPlayback() async {
    if (_isPlaying) {
      print('[AudioStream] Already playing');
      return;
    }

    if (_hasError) {
      print('[AudioStream] ERROR: Cannot start playback - service has error');
      return;
    }

    // Initialize if not already done (Windows only)
    if (!_isInitialized && Platform.isWindows) {
      print('[AudioStream] Initializing before starting playback...');
      final success = await _initialize();
      if (!success) {
        print('[AudioStream] ERROR: Failed to initialize, cannot start playback');
        return;
      }
    }

    if (!_isInitialized || _audioStream == null) {
      print('[AudioStream] ERROR: Not initialized, cannot start playback');
      return;
    }

    // Wait for initial buffer (to reduce stuttering)
    print('[AudioStream] Waiting for initial buffer (${_initialBufferSize} bytes)...');
    while (_audioBuffer.isEmpty || _getTotalBufferSize() < _initialBufferSize) {
      await Future.delayed(const Duration(milliseconds: 10));
      if (_audioBuffer.isEmpty && _isPlaying == false) {
        // Still waiting for first chunk
        continue;
      }
    }

    print('[AudioStream] Starting playback with ${_audioBuffer.length} chunks (${_getTotalBufferSize()} bytes)');
    
    // Verify stream is ready
    if (_audioStream == null) {
      print('[AudioStream] ERROR: AudioStream is null!');
      return;
    }
    
    // Check initial buffer statistics
    final initialStats = _audioStream!.stat();
    print('[AudioStream] Initial buffer stats - full: ${initialStats.full}, exhaust: ${initialStats.exhaust}');
    
    // Ensure resume() is called (should already be done in init, but double-check)
    _audioStream!.resume();
    
    _isPlaying = true;
    _playbackStartTime = DateTime.now();
    
    // Calculate and log latency
    if (_firstChunkTime != null && _playbackStartTime != null) {
      final latency = _playbackStartTime!.difference(_firstChunkTime!);
      print('[AudioStream] Latency from first chunk to playback start: ${latency.inMilliseconds}ms');
    }

    // Process buffered chunks
    _processBufferedChunks();
    
    // Verify playback state
    final statsAfterStart = _audioStream!.stat();
    print('[AudioStream] ✅ PLAYBACK STARTED - streaming active');
    print('[AudioStream] Buffer stats after start - full: ${statsAfterStart.full}, exhaust: ${statsAfterStart.exhaust}');
    print('[AudioStream] _isPlaying flag: $_isPlaying, _isInitialized: $_isInitialized');
    
    // Start periodic buffer status monitoring
    _startBufferMonitoring();
  }

  /// Start periodic buffer status monitoring
  void _startBufferMonitoring() {
    _bufferStatusTimer?.cancel();
    _bufferStatusTimer = Timer.periodic(const Duration(seconds: 2), (timer) {
      if (!_isPlaying || _audioStream == null) {
        timer.cancel();
        _bufferStatusTimer = null;
        return;
      }
      
      final stats = _audioStream!.stat();
      final bufferSize = _getTotalBufferSize();
      print('[AudioStream] 📊 Buffer status - full: ${stats.full}, exhaust: ${stats.exhaust}, our buffer: $bufferSize bytes, chunks: ${_audioBuffer.length}');
      
      if (stats.full > 0) {
        print('[AudioStream] ⚠️ WARNING: Buffer full events detected (${stats.full}) - audio may be dropping!');
      }
      if (stats.exhaust > 0) {
        print('[AudioStream] ⚠️ WARNING: Buffer exhaust events detected (${stats.exhaust}) - audio may be stuttering!');
      }
    });
  }

  /// Stop playback and clear buffer
  Future<void> stopPlayback() async {
    if (!_isPlaying) {
      return;
    }

    try {
      print('[AudioStream] Stopping playback...');
      
      // Stop buffer monitoring
      _bufferStatusTimer?.cancel();
      _bufferStatusTimer = null;
      
      _isPlaying = false;
      _audioBuffer.clear();
      _firstChunkTime = null;
      _playbackStartTime = null;
      
      // Get final statistics
      if (_audioStream != null) {
        final finalStats = _audioStream!.stat();
        print('[AudioStream] Final buffer stats - full: ${finalStats.full}, exhaust: ${finalStats.exhaust}');
      }
      
      // Note: mp_audio_stream doesn't have a stop() method
      // We just stop pushing new chunks and let the buffer drain
      print('[AudioStream] Playback stopped');
    } catch (e) {
      print('[AudioStream] ERROR stopping playback: $e');
    }
  }

  /// Get total size of buffered audio
  int _getTotalBufferSize() {
    return _audioBuffer.fold<int>(0, (sum, chunk) => sum + chunk.length);
  }

  /// Check if currently playing
  bool get isPlaying => _isPlaying;

  /// Check if service has error
  bool get hasError => _hasError;

  /// Check if initialized
  bool get isInitialized => _isInitialized;

  /// Dispose resources
  Future<void> dispose() async {
    try {
      print('[AudioStream] Disposing service...');
      
      // Stop buffer monitoring
      _bufferStatusTimer?.cancel();
      _bufferStatusTimer = null;
      
      await stopPlayback();
      
      if (_audioStream != null && _isInitialized) {
        _audioStream!.uninit();
        _isInitialized = false;
      }
      
      _audioStream = null;
      _audioBuffer.clear();
      print('[AudioStream] Service disposed');
    } catch (e) {
      print('[AudioStream] ERROR disposing: $e');
    }
  }
}

