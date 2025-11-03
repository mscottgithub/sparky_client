import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sparky_client/app_colors.dart';
import 'package:sparky_client/models/connection_status.dart';
import 'package:sparky_client/providers/audio_recording_provider.dart';
import 'package:sparky_client/providers/audio_websocket_provider.dart';
import 'package:sparky_client/providers/connection_provider.dart';
import 'package:sparky_client/providers/conversation_provider.dart';
import 'package:sparky_client/providers/recording_provider.dart';
import 'package:sparky_client/providers/session_provider.dart';
import 'package:sparky_client/widgets/message_bubble.dart';

/// Voice mode screen for audio conversation
/// Allows recording and sending audio to orchestrator
class VoiceScreen extends ConsumerStatefulWidget {
  const VoiceScreen({super.key});

  @override
  ConsumerState<VoiceScreen> createState() => _VoiceScreenState();
}

class _VoiceScreenState extends ConsumerState<VoiceScreen> {
  final ScrollController _scrollController = ScrollController();

  @override
  void initState() {
    super.initState();
    // Connect audio WebSocket on screen load
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _connectWebSocket();
    });
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  /// Connect audio WebSocket with current session ID
  void _connectWebSocket() {
    final audioWebSocket = ref.read(audioWebSocketProvider);
    final sessionId = ref.read(sessionProvider).sessionId;
    audioWebSocket.connect(sessionId);
  }

  /// Auto-scroll to bottom when new messages arrive
  void _scrollToBottom() {
    if (_scrollController.hasClients) {
      _scrollController.animateTo(
        _scrollController.position.maxScrollExtent,
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeOut,
      );
    }
  }

  /// Start recording audio
  Future<void> _startRecording() async {
    final recordingService = ref.read(audioRecordingServiceProvider);
    final audioWebSocket = ref.read(audioWebSocketProvider);
    final recordingNotifier = ref.read(recordingProvider.notifier);

    // Check permission first
    final hasPermission = await recordingService.checkPermission();
    recordingNotifier.setPermission(hasPermission);

    if (!hasPermission) {
      recordingNotifier.setError('Microphone permission not granted');
      return;
    }

    // Check WebSocket connection
    if (!audioWebSocket.isConnected) {
      recordingNotifier.setError('WebSocket not connected');
      return;
    }

    // Start audio message
    audioWebSocket.startAudioMessage();

    // Start recording with callbacks
    final started = await recordingService.startRecording(
      onAudioChunk: (Uint8List chunk) {
        // Send audio chunk to WebSocket
        audioWebSocket.sendAudioChunk(chunk);
      },
      onLevelUpdate: (double level) {
        // Update microphone level for UI
        recordingNotifier.setMicrophoneLevel(level);
      },
    );

    if (started) {
      recordingNotifier.setRecording(true);
      recordingNotifier.setError(null);
    } else {
      recordingNotifier.setError('Failed to start recording');
    }
  }

  /// Stop recording and finalize audio message
  Future<void> _stopRecording() async {
    final recordingService = ref.read(audioRecordingServiceProvider);
    final audioWebSocket = ref.read(audioWebSocketProvider);
    final recordingNotifier = ref.read(recordingProvider.notifier);

    // Stop recording
    await recordingService.stopRecording();

    // Finalize audio message
    audioWebSocket.finalizeAudioMessage();

    // Update state
    recordingNotifier.setRecording(false);
    recordingNotifier.setMicrophoneLevel(0.0);
  }

  @override
  Widget build(BuildContext context) {
    final messages = ref.watch(conversationProvider);
    final connectionStatus = ref.watch(audioConnectionProvider);
    final recordingState = ref.watch(recordingProvider);

    // Auto-scroll when messages change
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _scrollToBottom();
    });

    return ColoredBox(
      color: AppColors.powderBlue,
      child: Scaffold(
        backgroundColor: Colors.transparent,
        appBar: PreferredSize(
          preferredSize: const Size.fromHeight(kToolbarHeight),
          child: ColoredBox(
            color: AppColors.thistle,
            child: AppBar(
              title: const Text('Voice Chat'),
              backgroundColor: Colors.transparent,
              foregroundColor: Colors.purple.shade900,
              elevation: 0,
              actions: [
                // Connection status indicator
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16.0),
                  child: Center(
                    child: _ConnectionIndicator(status: connectionStatus),
                  ),
                ),
              ],
            ),
          ),
        ),
        body: Column(
          children: [
            // Messages list
            Expanded(
              child: messages.isEmpty
                  ? Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(
                            Icons.mic,
                            size: 64,
                            color: Colors.grey.shade400,
                          ),
                          const SizedBox(height: 16),
                          Text(
                            'Start recording to begin conversation',
                            style: TextStyle(
                              fontSize: 16,
                              color: Colors.grey.shade600,
                            ),
                          ),
                        ],
                      ),
                    )
                  : ListView.builder(
                      controller: _scrollController,
                      padding: const EdgeInsets.all(16.0),
                      itemCount: messages.length,
                      itemBuilder: (context, index) {
                        final message = messages[index];
                        return MessageBubble(message: message);
                      },
                    ),
            ),

            // Recording status and controls
            Container(
              padding: const EdgeInsets.all(16.0),
              decoration: BoxDecoration(
                color: AppColors.thistle.withOpacity(0.7),
                borderRadius: const BorderRadius.only(
                  topLeft: Radius.circular(16),
                  topRight: Radius.circular(16),
                ),
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  // Error message
                  if (recordingState.error != null)
                    Container(
                      padding: const EdgeInsets.all(8.0),
                      margin: const EdgeInsets.only(bottom: 8.0),
                      decoration: BoxDecoration(
                        color: Colors.red.shade100,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Row(
                        children: [
                          Icon(Icons.error, color: Colors.red.shade700, size: 20),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              recordingState.error!,
                              style: TextStyle(color: Colors.red.shade700),
                            ),
                          ),
                        ],
                      ),
                    ),

                  // Microphone level indicator
                  if (recordingState.isRecording)
                    Container(
                      height: 8,
                      margin: const EdgeInsets.only(bottom: 16),
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(4),
                        color: Colors.grey.shade300,
                      ),
                      child: FractionallySizedBox(
                        alignment: Alignment.centerLeft,
                        widthFactor: recordingState.microphoneLevel,
                        child: Container(
                          decoration: BoxDecoration(
                            borderRadius: BorderRadius.circular(4),
                            color: Colors.red.shade400,
                          ),
                        ),
                      ),
                    ),

                  // Record button
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      ElevatedButton.icon(
                        onPressed: connectionStatus == ConnectionStatus.connected
                            ? (recordingState.isRecording
                                ? _stopRecording
                                : _startRecording)
                            : null,
                        icon: Icon(
                          recordingState.isRecording
                              ? Icons.stop
                              : Icons.mic,
                        ),
                        label: Text(
                          recordingState.isRecording ? 'Stop Recording' : 'Start Recording',
                        ),
                        style: ElevatedButton.styleFrom(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 24,
                            vertical: 16,
                          ),
                          backgroundColor: recordingState.isRecording
                              ? Colors.red.shade400
                              : Colors.blue.shade400,
                          foregroundColor: Colors.white,
                          disabledBackgroundColor: Colors.grey.shade400,
                        ),
                      ),
                    ],
                  ),

                  // Connection controls
                  const SizedBox(height: 8),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      TextButton.icon(
                        onPressed: connectionStatus == ConnectionStatus.connected
                            ? () {
                                ref.read(audioWebSocketProvider).disconnect();
                              }
                            : () {
                                _connectWebSocket();
                              },
                        icon: Icon(
                          connectionStatus == ConnectionStatus.connected
                              ? Icons.close
                              : Icons.refresh,
                        ),
                        label: Text(
                          connectionStatus == ConnectionStatus.connected
                              ? 'Disconnect'
                              : 'Connect',
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Connection status indicator widget
class _ConnectionIndicator extends StatelessWidget {
  final ConnectionStatus status;

  const _ConnectionIndicator({required this.status});

  @override
  Widget build(BuildContext context) {
    Color color;
    IconData icon;
    String label;

    switch (status) {
      case ConnectionStatus.connected:
        color = Colors.green;
        icon = Icons.circle;
        label = 'Connected';
        break;
      case ConnectionStatus.connecting:
        color = Colors.orange;
        icon = Icons.hourglass_empty;
        label = 'Connecting...';
        break;
      case ConnectionStatus.error:
        color = Colors.red;
        icon = Icons.error;
        label = 'Error';
        break;
      case ConnectionStatus.disconnected:
        color = Colors.grey;
        icon = Icons.circle_outlined;
        label = 'Disconnected';
        break;
    }

    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, color: color, size: 16),
        const SizedBox(width: 4),
        Text(
          label,
          style: TextStyle(
            color: color,
            fontSize: 12,
            fontWeight: FontWeight.w500,
          ),
        ),
      ],
    );
  }
}

