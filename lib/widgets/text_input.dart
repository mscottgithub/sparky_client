import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:sparky_client/widgets/desktop_text_field.dart';

/// Text input widget with Enter/Shift+Enter handling
/// Enter = Send message, Shift+Enter = New line
class ChatTextInput extends StatefulWidget {
  final VoidCallback onSend;
  final String? hintText;
  final bool enabled;

  const ChatTextInput({
    super.key,
    required this.onSend,
    this.hintText,
    this.enabled = true,
  });

  @override
  State<ChatTextInput> createState() => _ChatTextInputState();
}

class _ChatTextInputState extends State<ChatTextInput> {
  final TextEditingController _controller = TextEditingController();
  final FocusNode _focusNode = FocusNode();

  @override
  void dispose() {
    _controller.dispose();
    _focusNode.dispose();
    super.dispose();
  }

  void _handleSubmitted(String text) {
    if (text.trim().isNotEmpty && widget.enabled) {
      widget.onSend();
      _controller.clear();
    }
  }

  void _handleKeyEvent(KeyEvent event) {
    if (event is KeyDownEvent) {
      final isShiftPressed = event.logicalKey == LogicalKeyboardKey.shiftLeft ||
          event.logicalKey == LogicalKeyboardKey.shiftRight;
      final isEnterPressed = event.logicalKey == LogicalKeyboardKey.enter;

      if (isEnterPressed && !isShiftPressed && widget.enabled) {
        // Enter without Shift = Send
        final text = _controller.text.trim();
        if (text.isNotEmpty) {
          widget.onSend();
          _controller.clear();
        }
      }
      // Shift+Enter = New line (handled by TextField default behavior)
    }
  }

  String get text => _controller.text;

  void clear() {
    _controller.clear();
  }

  @override
  Widget build(BuildContext context) {
    return KeyboardListener(
      focusNode: _focusNode,
      onKeyEvent: _handleKeyEvent,
      child: DesktopTextField(
        controller: _controller,
        focusNode: _focusNode,
        hintText: widget.hintText ?? 'Type your message... (Enter to send, Shift+Enter for new line)',
        enabled: widget.enabled,
        maxLines: 3,
        onSubmitted: _handleSubmitted,
      ),
    );
  }
}

