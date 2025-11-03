import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:sparky_client/models/session_state.dart';

/// Session state notifier
/// Manages session_id and conversation state with persistence
class SessionNotifier extends StateNotifier<SessionState> {
  static const String _sessionIdKey = 'sparky_session_id';

  SessionNotifier() : super(const SessionState()) {
    _loadSessionId();
  }

  /// Load session_id from SharedPreferences
  Future<void> _loadSessionId() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final sessionId = prefs.getString(_sessionIdKey);
      if (sessionId != null && sessionId.isNotEmpty) {
        state = state.copyWith(sessionId: sessionId);
      }
    } catch (e) {
      print('Error loading session_id: $e');
    }
  }

  /// Set session_id and persist it
  Future<void> setSession(String sessionId) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_sessionIdKey, sessionId);
      state = state.copyWith(
        sessionId: sessionId,
        conversationActive: true,
      );
    } catch (e) {
      print('Error saving session_id: $e');
    }
  }

  /// Clear session_id
  Future<void> clearSession() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove(_sessionIdKey);
      state = const SessionState();
    } catch (e) {
      print('Error clearing session_id: $e');
    }
  }

  /// Update conversation active state
  void setConversationActive(bool active) {
    state = state.copyWith(conversationActive: active);
  }
}

/// Session provider
final sessionProvider =
    StateNotifierProvider<SessionNotifier, SessionState>((ref) {
  return SessionNotifier();
});

