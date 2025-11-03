import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:sparky_client/models/chat_message.dart';

/// Message bubble widget for displaying chat messages
/// Shows user messages (right-aligned, blue) and assistant messages (left-aligned, gray)
class MessageBubble extends StatelessWidget {
  final ChatMessage message;

  const MessageBubble({
    super.key,
    required this.message,
  });

  @override
  Widget build(BuildContext context) {
    final isUser = message.role == 'user';
    final theme = Theme.of(context);

    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: BoxDecoration(
          color: isUser
              ? theme.colorScheme.primaryContainer // Keep user messages as-is
              : Colors.lightBlue.shade50, // Lighter blue for AI messages (lighter than background blue.shade50)
          borderRadius: BorderRadius.circular(16),
        ),
        constraints: BoxConstraints(
          maxWidth: MediaQuery.of(context).size.width * 0.7,
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              message.content,
              style: TextStyle(
                color: isUser
                    ? theme.colorScheme.onPrimaryContainer
                    : Colors.blue.shade900, // Dark blue text for AI messages on light blue background
                fontSize: 14,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              DateFormat('HH:mm').format(message.timestamp),
              style: TextStyle(
                color: isUser
                    ? theme.colorScheme.onPrimaryContainer.withOpacity(0.7)
                    : Colors.blue.shade700.withOpacity(0.7),
                fontSize: 11,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

