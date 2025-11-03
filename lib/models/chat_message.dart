/// Chat message model
/// Represents a single message in the conversation (user or assistant)
class ChatMessage {
  final String role; // 'user' or 'assistant'
  final String content;
  final DateTime timestamp;
  final String? messageId; // For streaming updates

  ChatMessage({
    required this.role,
    required this.content,
    DateTime? timestamp,
    this.messageId,
  }) : timestamp = timestamp ?? DateTime.now();

  /// Creates a user message
  factory ChatMessage.user(String content) {
    return ChatMessage(
      role: 'user',
      content: content,
    );
  }

  /// Creates an assistant message
  factory ChatMessage.assistant(String content, {String? messageId}) {
    return ChatMessage(
      role: 'assistant',
      content: content,
      messageId: messageId,
    );
  }
}

