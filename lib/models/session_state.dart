/// Session state model
/// Represents the current conversation session with the orchestrator
class SessionState {
  final String? sessionId;
  final bool conversationActive;

  const SessionState({
    this.sessionId,
    this.conversationActive = false,
  });

  SessionState copyWith({
    String? sessionId,
    bool? conversationActive,
  }) {
    return SessionState(
      sessionId: sessionId ?? this.sessionId,
      conversationActive: conversationActive ?? this.conversationActive,
    );
  }
}

