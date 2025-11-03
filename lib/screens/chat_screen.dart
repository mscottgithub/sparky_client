import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sparky_client/providers/conversation_provider.dart';
import 'package:sparky_client/providers/connection_provider.dart';
import 'package:sparky_client/providers/websocket_provider.dart';
import 'package:sparky_client/providers/session_provider.dart';
import 'package:sparky_client/widgets/message_bubble.dart';
import 'package:sparky_client/widgets/desktop_text_field.dart';
import 'package:sparky_client/models/connection_status.dart';
import 'package:sparky_client/widgets/keyboard_shortcuts_handler.dart';
import 'package:sparky_client/app_colors.dart';

/// Chat screen for text conversations with Sparky
class ChatScreen extends ConsumerStatefulWidget {
  const ChatScreen({super.key});

  @override
  ConsumerState<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends ConsumerState<ChatScreen> {
  final ScrollController _scrollController = ScrollController();
  final TextEditingController _textController = TextEditingController();
  final FocusNode _textFieldFocusNode = FocusNode();

  @override
  void dispose() {
    _scrollController.dispose();
    _textController.dispose();
    _textFieldFocusNode.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
    if (_scrollController.hasClients) {
      _scrollController.animateTo(
        _scrollController.position.maxScrollExtent,
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeOut,
      );
    }
  }

  void _handleSend() {
    final text = _textController.text.trim();
    if (text.isEmpty) return;

    final webSocketService = ref.read(textWebSocketProvider);
    webSocketService.sendText(text);
    _textController.clear();

    // Scroll to bottom after a short delay to allow message to be added
    Future.delayed(const Duration(milliseconds: 100), () {
      _scrollToBottom();
    });
  }

  void _handleConnect() {
    final webSocketService = ref.read(textWebSocketProvider);
    final sessionId = ref.read(sessionProvider).sessionId;
    webSocketService.connect(sessionId);
  }

  void _handleDisconnect() {
    final webSocketService = ref.read(textWebSocketProvider);
    webSocketService.disconnect();
  }

  void _handleAbort() {
    // Abort current conversation if needed
    // For now, just disconnect
    _handleDisconnect();
  }

  @override
  void initState() {
    super.initState();
    // Auto-connect on screen load
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final sessionId = ref.read(sessionProvider).sessionId;
      final webSocketService = ref.read(textWebSocketProvider);
      webSocketService.connect(sessionId);
    });
  }

  @override
  Widget build(BuildContext context) {
    final messages = ref.watch(conversationProvider);
    final connectionStatus = ref.watch(textConnectionProvider);
    final isConnected = connectionStatus == ConnectionStatus.connected;

    // Auto-scroll when new messages arrive
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _scrollToBottom();
    });

    return KeyboardShortcutsHandler(
      onAbort: _handleAbort,
      child: ColoredBox(
        color: AppColors.powderBlue, // Powder Blue #8BBCC2
        child: Scaffold(
          backgroundColor: Colors.transparent, // Let ColoredBox color show through
          extendBodyBehindAppBar: false,
          appBar: PreferredSize(
            preferredSize: const Size.fromHeight(kToolbarHeight),
            child: ColoredBox(
              color: AppColors.thistle, // Thistle #977597
              child: AppBar(
                title: const Text('Sparky Chat'),
                backgroundColor: Colors.transparent, // Transparent so ColoredBox shows
                foregroundColor: Colors.purple.shade900,
                elevation: 0, // Remove shadow
          actions: [
            // Connection status indicator
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Row(
                children: [
                  Icon(
                    isConnected ? Icons.circle : Icons.circle_outlined,
                    color: isConnected ? Colors.green : Colors.red,
                    size: 12,
                  ),
                  const SizedBox(width: 8),
                  Text(
                    isConnected ? 'Connected' : 'Disconnected',
                    style: TextStyle(
                      fontSize: 12,
                      color: isConnected ? Colors.green : Colors.red,
                    ),
                  ),
                ],
              ),
            ),
            // Connect/Disconnect button
            IconButton(
              icon: Icon(isConnected ? Icons.stop : Icons.play_arrow),
              onPressed: isConnected ? _handleDisconnect : _handleConnect,
              tooltip: isConnected ? 'Disconnect' : 'Connect',
            ),
          ],
              ),
            ), // Close AppBar ColoredBox
          ), // Close PreferredSize
        body: Column(
          children: [
            // Message list
            Expanded(
              child: messages.isEmpty
                  ? const Center(
                      child: Text(
                        'Start a conversation...',
                        style: TextStyle(
                          fontSize: 16,
                          color: Colors.grey,
                        ),
                      ),
                    )
                  : ListView.builder(
                      controller: _scrollController,
                      padding: const EdgeInsets.symmetric(vertical: 8),
                      itemCount: messages.length,
                      itemBuilder: (context, index) {
                        return MessageBubble(message: messages[index]);
                      },
                    ),
            ),
            // Input area
            ColoredBox(
              color: AppColors.thistle, // Thistle #977597
              child: Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withOpacity(0.1),
                      blurRadius: 4,
                      offset: const Offset(0, -2),
                    ),
                  ],
                ),
              child: Row(
                children: [
                  Expanded(
                    child: DesktopTextField(
                      controller: _textController,
                      focusNode: _textFieldFocusNode,
                      hintText: 'Type your message... (Enter to send, Shift+Enter for new line)',
                      enabled: isConnected,
                      maxLines: 3,
                      onEnter: () {
                        // Enter pressed (without Shift) = Send message
                        final text = _textController.text.trim();
                        if (text.isNotEmpty) {
                          _handleSend();
                        }
                      },
                      onSubmitted: null, // Not used when onEnter is provided
                    ),
                  ),
                  const SizedBox(width: 8),
                  IconButton(
                    icon: const Icon(Icons.send),
                    onPressed: isConnected ? _handleSend : null,
                    tooltip: 'Send message',
                  ),
                ],
              ),
              ), // Close Container
            ), // Close ColoredBox (input area)
          ],
        ), // Close body Column
      ), // Close Scaffold
    ), // Close ColoredBox (main background)
    ); // Close KeyboardShortcutsHandler
  }
}

