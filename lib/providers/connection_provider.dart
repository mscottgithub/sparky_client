import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sparky_client/models/connection_status.dart';

/// Connection status notifier
/// Manages WebSocket connection state
class ConnectionNotifier extends StateNotifier<ConnectionStatus> {
  ConnectionNotifier() : super(ConnectionStatus.disconnected);

  void setStatus(ConnectionStatus status) {
    state = status;
  }

  void connecting() => setStatus(ConnectionStatus.connecting);
  void connected() => setStatus(ConnectionStatus.connected);
  void disconnected() => setStatus(ConnectionStatus.disconnected);
  void error() => setStatus(ConnectionStatus.error);
}

/// Connection status provider for text WebSocket
final textConnectionProvider =
    StateNotifierProvider<ConnectionNotifier, ConnectionStatus>((ref) {
  return ConnectionNotifier();
});

