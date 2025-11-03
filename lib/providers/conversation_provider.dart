import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sparky_client/models/chat_message.dart';

/// Conversation notifier
/// Manages the list of chat messages with streaming support
class ConversationNotifier extends StateNotifier<List<ChatMessage>> {
  ConversationNotifier() : super([]);

  /// Add a new message
  void addMessage(ChatMessage message) {
    state = [...state, message];
  }

  /// Append content to existing message (for streaming)
  void appendToMessage(String messageId, String additionalContent) {
    state = [
      for (final msg in state)
        if (msg.messageId == messageId)
          ChatMessage(
            role: msg.role,
            content: msg.content + additionalContent,
            timestamp: msg.timestamp,
            messageId: messageId,
          )
        else
          msg
    ];
  }

  /// Update entire message content (replace)
  void updateMessage(String messageId, String newContent) {
    state = [
      for (final msg in state)
        if (msg.messageId == messageId)
          ChatMessage(
            role: msg.role,
            content: newContent,
            timestamp: msg.timestamp,
            messageId: messageId,
          )
        else
          msg
    ];
  }

  /// Clear all messages
  void clearHistory() {
    state = [];
  }
}

/// Conversation provider
final conversationProvider =
    StateNotifierProvider<ConversationNotifier, List<ChatMessage>>((ref) {
  return ConversationNotifier();
});

