import 'dart:async';
import 'dart:typed_data';
import 'dart:io';
import 'package:just_audio/just_audio.dart';
import 'package:audioplayers/audioplayers.dart' as ap;
import 'package:path_provider/path_provider.dart';

/// Audio playback service for TTS audio output
/// Handles streaming audio chunks from orchestrator
/// Uses just_audio for non-Windows platforms, audioplayers for Windows
class AudioPlaybackService {
  AudioPlayer? _justAudioPlayer; // For non-Windows platforms
  ap.AudioPlayer? _audioPlayers; // For Windows
  bool _isPlaying = false;
  bool _isProcessingQueue = false;
  bool _isWindows = Platform.isWindows;
  
  // Buffer for accumulating audio chunks
  final List<Uint8List> _audioBuffer = [];
  static const int _initialBufferSize = 4096; // ~0.085 seconds at 24kHz mono 16-bit (reduced for faster start)
  static const int _batchSize = 8192; // ~0.17 seconds per WAV file (smaller files = less choppy)
  
  // Queue for WAV files to play
  final List<File> _fileQueue = [];
  final List<StreamSubscription> _subscriptions = [];
  Timer? _streamingTimer;
  
  // Track current playing file for cleanup
  File? _currentPlayingFile;

  AudioPlaybackService() {
    if (_isWindows) {
      // Use audioplayers for Windows
      _audioPlayers = ap.AudioPlayer();
      print('Windows detected - using audioplayers for audio playback');
      
      // Set up single completion listener
      _audioPlayers!.onPlayerComplete.listen((_) {
        _onPlaybackComplete();
      });
    } else {
      // Use just_audio for other platforms
      _justAudioPlayer = AudioPlayer();
      _justAudioPlayer!.setLoopMode(LoopMode.off);
      _justAudioPlayer!.playerStateStream.listen((state) {
        if (state.processingState == ProcessingState.completed) {
          _onPlaybackComplete();
        }
      });
    }
  }

  /// Start playing audio chunks as they arrive
  Future<void> startPlayback() async {
    if (_isProcessingQueue || _isPlaying) {
      return;
    }

    if ((_isWindows && _audioPlayers == null) || (!_isWindows && _justAudioPlayer == null)) {
      print('AudioPlayer not initialized');
      return;
    }

    // Wait for initial buffer
    while (_audioBuffer.isEmpty || _getTotalBufferSize() < _initialBufferSize) {
      await Future.delayed(const Duration(milliseconds: 10));
    }

    // Start processing queue
    _isProcessingQueue = true;
    
    // Process first batch
    await _processAudioQueue();
    
    // Start streaming timer to check for new chunks
    _startStreamingTimer();
  }

  /// Process audio queue - creates WAV files and plays them sequentially
  Future<void> _processAudioQueue() async {
    if (_isPlaying || _audioBuffer.isEmpty) {
      return;
    }

    try {
      // Process chunks in batches for smoother streaming
      // Create smaller files more frequently to reduce gaps
      int totalSize = _getTotalBufferSize();
      int bytesToProcess = totalSize > _batchSize ? _batchSize : totalSize;
      
      // Collect chunks up to batch size
      final List<Uint8List> chunksToProcess = [];
      int bytesCollected = 0;
      
      while (_audioBuffer.isNotEmpty && bytesCollected < bytesToProcess) {
        final chunk = _audioBuffer.removeAt(0);
        chunksToProcess.add(chunk);
        bytesCollected += chunk.length;
      }
      
      // Combine chunks
      final combined = Uint8List(bytesCollected);
      int offset = 0;
      for (final chunk in chunksToProcess) {
        combined.setRange(offset, offset + chunk.length, chunk);
        offset += chunk.length;
      }

      // Create WAV file in memory
      final wavData = _createWavFile(combined, 24000, 1, 16);

      // Create temporary file
      final tempDir = await getTemporaryDirectory();
      final tempFile = File('${tempDir.path}/temp_audio_${DateTime.now().millisecondsSinceEpoch}.wav');
      await tempFile.writeAsBytes(wavData);
      
      // Add to queue
      _fileQueue.add(tempFile);
      
      // Start playing if not already playing
      if (!_isPlaying) {
        await _playNextInQueue();
      }
    } catch (e) {
      print('Error processing audio queue: $e');
      _isProcessingQueue = false;
      _isPlaying = false;
    }
  }

  /// Play next file in queue
  Future<void> _playNextInQueue() async {
    if (_isPlaying || _fileQueue.isEmpty) {
      return;
    }

    try {
      final fileToPlay = _fileQueue.removeAt(0);
      _currentPlayingFile = fileToPlay;
      _isPlaying = true;

      // Play the file based on platform
      if (_isWindows && _audioPlayers != null) {
        // Windows: use audioplayers
        await _audioPlayers!.play(ap.DeviceFileSource(fileToPlay.path));
        print('Audio playback started (Windows - audioplayers): ${fileToPlay.path}');
      } else if (!_isWindows && _justAudioPlayer != null) {
        // Non-Windows: use just_audio
        await _justAudioPlayer!.setFilePath(fileToPlay.path);
        await _justAudioPlayer!.play();
        print('Audio playback started (just_audio): ${fileToPlay.path}');
      }
    } catch (e) {
      print('Error playing audio file: $e');
      _isPlaying = false;
      _currentPlayingFile = null;
      
      // Try to delete the failed file
      if (_currentPlayingFile != null) {
        try {
          await _currentPlayingFile!.delete();
        } catch (_) {}
      }
      
      // Continue with next file in queue
      if (_fileQueue.isNotEmpty) {
        await Future.delayed(const Duration(milliseconds: 100));
        await _playNextInQueue();
      } else {
        _isProcessingQueue = false;
      }
    }
  }

  /// Called when playback completes
  void _onPlaybackComplete() {
    _isPlaying = false;
    
    // Clean up the file that just finished playing (fire and forget)
    final fileToDelete = _currentPlayingFile;
    _currentPlayingFile = null;
    
    if (fileToDelete != null) {
      // Wait a bit before deleting to ensure player released the file
      Future.delayed(const Duration(milliseconds: 200), () async {
        try {
          if (await fileToDelete.exists()) {
            await fileToDelete.delete();
          }
        } catch (e) {
          print('Error deleting temp file: $e');
          // Try again later
          Future.delayed(const Duration(seconds: 2), () async {
            try {
              if (await fileToDelete.exists()) {
                await fileToDelete.delete();
              }
            } catch (_) {}
          });
        }
      });
    }
    
    // Immediately continue with queue processing (don't wait for cleanup)
    if (_fileQueue.isNotEmpty) {
      _playNextInQueue();
    } else if (_audioBuffer.isNotEmpty) {
      // Process more buffered chunks - be aggressive (process even small amounts)
      if (_getTotalBufferSize() >= _initialBufferSize || _audioBuffer.length >= 2) {
        _processAudioQueue();
      } else {
        _isProcessingQueue = false; // Wait for more chunks
      }
    } else {
      // Nothing more to play
      _isProcessingQueue = false;
    }
  }

  /// Start streaming timer - checks for new chunks periodically
  void _startStreamingTimer() {
    _streamingTimer?.cancel();
    _streamingTimer = Timer.periodic(const Duration(milliseconds: 50), (timer) {
      // More frequent checks for smoother streaming
      if (!_isProcessingQueue && _audioBuffer.isNotEmpty) {
        // Process as soon as we have chunks (more aggressive)
        if (_getTotalBufferSize() >= _initialBufferSize || _audioBuffer.length >= 2) {
          _isProcessingQueue = true;
          _processAudioQueue();
        }
      } else if (_isProcessingQueue && _audioBuffer.isNotEmpty && _getTotalBufferSize() >= _batchSize) {
        // Buffer has enough for another batch, process it
        _processAudioQueue();
      }
      
      // Stop timer if nothing to process
      if (!_isPlaying && !_isProcessingQueue && _audioBuffer.isEmpty && _fileQueue.isEmpty) {
        timer.cancel();
        _streamingTimer = null;
      }
    });
  }

  /// Add audio chunk to buffer/queue
  void addAudioChunk(Uint8List chunk) {
    // Always add to buffer
    _audioBuffer.add(chunk);
    
    // Limit buffer size to prevent memory issues
    if (_audioBuffer.length > 100) {
      print('Audio buffer limit reached (100 chunks) - dropping oldest');
      _audioBuffer.removeAt(0);
    }
    
    // If not already processing and buffer is ready, start processing
    // More aggressive: start processing sooner with less buffering
    if (!_isProcessingQueue && !_isPlaying) {
      if (_getTotalBufferSize() >= _initialBufferSize || _audioBuffer.length >= 2) {
        _isProcessingQueue = true;
        _processAudioQueue();
        _startStreamingTimer();
      }
    }
  }

  /// Stop playback
  Future<void> stopPlayback() async {
    try {
      _streamingTimer?.cancel();
      _streamingTimer = null;
      
      if (_isWindows && _audioPlayers != null) {
        await _audioPlayers!.stop();
      } else if (!_isWindows && _justAudioPlayer != null) {
        await _justAudioPlayer!.stop();
      }
      
      // Clear buffers and queue
      _audioBuffer.clear();
      _fileQueue.clear();
      _isPlaying = false;
      _isProcessingQueue = false;
      
      // Clean up current file
      if (_currentPlayingFile != null) {
        final file = _currentPlayingFile;
        _currentPlayingFile = null;
        Future.delayed(const Duration(milliseconds: 500), () async {
          try {
            if (file != null && await file.exists()) {
              await file.delete();
            }
          } catch (_) {}
        });
      }
      
      // Clean up queued files
      for (final file in _fileQueue) {
        try {
          if (await file.exists()) {
            await file.delete();
          }
        } catch (_) {}
      }
      
      print('Audio playback stopped');
    } catch (e) {
      print('Error stopping audio playback: $e');
    }
  }

  /// Get total size of buffered audio
  int _getTotalBufferSize() {
    return _audioBuffer.fold<int>(0, (sum, chunk) => sum + chunk.length);
  }

  /// Create WAV file from PCM data
  Uint8List _createWavFile(Uint8List pcmData, int sampleRate, int channels, int bitsPerSample) {
    final byteRate = sampleRate * channels * (bitsPerSample ~/ 8);
    final blockAlign = channels * (bitsPerSample ~/ 8);
    final dataLength = pcmData.length;
    final fileSize = 36 + dataLength;

    final header = Uint8List(44);
    int offset = 0;

    // RIFF header
    header.setRange(offset, offset + 4, 'RIFF'.codeUnits);
    offset += 4;
    header.setRange(offset, offset + 4, _intToBytes(fileSize, 4));
    offset += 4;
    header.setRange(offset, offset + 4, 'WAVE'.codeUnits);
    offset += 4;

    // fmt chunk
    header.setRange(offset, offset + 4, 'fmt '.codeUnits);
    offset += 4;
    header.setRange(offset, offset + 4, _intToBytes(16, 4));
    offset += 4;
    header.setRange(offset, offset + 2, _intToBytes(1, 2)); // PCM format
    offset += 2;
    header.setRange(offset, offset + 2, _intToBytes(channels, 2));
    offset += 2;
    header.setRange(offset, offset + 4, _intToBytes(sampleRate, 4));
    offset += 4;
    header.setRange(offset, offset + 4, _intToBytes(byteRate, 4));
    offset += 4;
    header.setRange(offset, offset + 2, _intToBytes(blockAlign, 2));
    offset += 2;
    header.setRange(offset, offset + 2, _intToBytes(bitsPerSample, 2));
    offset += 2;

    // data chunk
    header.setRange(offset, offset + 4, 'data'.codeUnits);
    offset += 4;
    header.setRange(offset, offset + 4, _intToBytes(dataLength, 4));

    // Combine header and PCM data
    final wavFile = Uint8List(header.length + pcmData.length);
    wavFile.setRange(0, header.length, header);
    wavFile.setRange(header.length, header.length + pcmData.length, pcmData);

    return wavFile;
  }

  Uint8List _intToBytes(int value, int bytes) {
    final result = Uint8List(bytes);
    for (int i = 0; i < bytes; i++) {
      result[i] = value & 0xFF;
      value >>= 8;
    }
    return result;
  }

  /// Check if currently playing
  bool get isPlaying => _isPlaying;

  /// Dispose resources
  Future<void> dispose() async {
    await stopPlayback();
    
    // Cancel all subscriptions
    for (final sub in _subscriptions) {
      await sub.cancel();
    }
    _subscriptions.clear();
    
    if (_isWindows && _audioPlayers != null) {
      await _audioPlayers!.dispose();
      _audioPlayers = null;
    } else if (!_isWindows && _justAudioPlayer != null) {
      await _justAudioPlayer!.dispose();
      _justAudioPlayer = null;
    }
  }
}
