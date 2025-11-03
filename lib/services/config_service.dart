/// Configuration service for Sparky client
/// Manages server settings and default configurations
class ConfigService {
  final String serverHost;
  final int orchestratorPort;
  final int whisperPort;
  final int ttsPort;
  final String defaultVoice;
  final int sampleRate;

  const ConfigService({
    this.serverHost = '10.6.1.15',
    this.orchestratorPort = 8006,
    this.whisperPort = 8005,
    this.ttsPort = 8004,
    this.defaultVoice = 'ara',
    this.sampleRate = 16000,
  });

  /// WebSocket URL for orchestrator conversation endpoint
  String get orchestratorWebSocketUrl =>
      'ws://$serverHost:$orchestratorPort/ws/conversation';

  /// HTTP URL for orchestrator health check
  String get orchestratorHealthUrl =>
      'http://$serverHost:$orchestratorPort/health';
}

