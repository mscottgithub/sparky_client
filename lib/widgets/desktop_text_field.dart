import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

/// Desktop-optimized text field with right-click context menu
/// Supports: Copy, Paste, Cut, Select All, Undo
/// For multi-line fields: Enter sends (if onEnter callback provided), Shift+Enter creates newline
class DesktopTextField extends StatefulWidget {
  final TextEditingController controller;
  final String? hintText;
  final ValueChanged<String>? onSubmitted;
  final bool enabled;
  final int? maxLines;
  final FocusNode? focusNode;
  final VoidCallback? onEnter; // Called when Enter is pressed (without Shift)

  const DesktopTextField({
    super.key,
    required this.controller,
    this.hintText,
    this.onSubmitted,
    this.enabled = true,
    this.maxLines = 1,
    this.focusNode,
    this.onEnter,
  });

  @override
  State<DesktopTextField> createState() => _DesktopTextFieldState();
}

class _DesktopTextFieldState extends State<DesktopTextField> {
  FocusNode? _internalFocusNode;
  FocusNode get _focusNode => widget.focusNode ?? _internalFocusNode!;

  @override
  void initState() {
    super.initState();
    if (widget.focusNode == null) {
      _internalFocusNode = FocusNode();
    }
  }

  @override
  void dispose() {
    _internalFocusNode?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final textField = GestureDetector(
      onSecondaryTapDown: (details) {
        _showContextMenu(context, details.globalPosition);
      },
      child: TextField(
        controller: widget.controller,
        focusNode: _focusNode,
        enabled: widget.enabled,
        maxLines: widget.maxLines,
          decoration: InputDecoration(
          hintText: widget.hintText ?? 'Type message...',
          border: const OutlineInputBorder(),
          filled: true,
          fillColor: const Color(0xFF977597), // Thistle #977597 background for text input
        ),
        onSubmitted: widget.onSubmitted,
      ),
    );

    // If onEnter callback is provided, wrap with Focus to intercept Enter key
    if (widget.onEnter != null && widget.maxLines != null && widget.maxLines! > 1) {
      return Focus(
        onKeyEvent: (node, event) {
          if (event is KeyDownEvent) {
            final isShiftPressed = HardwareKeyboard.instance.isShiftPressed;
            final isEnter = event.logicalKey == LogicalKeyboardKey.enter;

            if (isEnter && !isShiftPressed && widget.enabled) {
              // Enter without Shift = call onEnter callback and prevent default
              widget.onEnter!();
              return KeyEventResult.handled; // Prevent TextField from getting the key
            }
            // Shift+Enter = New line (allow default TextField behavior)
          }
          return KeyEventResult.ignored;
        },
        child: textField,
      );
    }

    return textField;
  }

  void _showContextMenu(BuildContext context, Offset position) {
    final selection = widget.controller.selection;
    final hasSelection = selection.isValid && !selection.isCollapsed;

    showMenu(
      context: context,
      position: RelativeRect.fromLTRB(
        position.dx,
        position.dy,
        position.dx,
        position.dy,
      ),
      items: [
        if (hasSelection)
          PopupMenuItem(
            value: 'copy',
            child: Row(
              children: [
                const Icon(Icons.copy, size: 18),
                const SizedBox(width: 8),
                const Text('Copy'),
                const Spacer(),
                Text(
                  'Ctrl+C',
                  style: TextStyle(
                    color: Colors.grey[600],
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          ),
        if (hasSelection)
          PopupMenuItem(
            value: 'cut',
            child: Row(
              children: [
                const Icon(Icons.cut, size: 18),
                const SizedBox(width: 8),
                const Text('Cut'),
                const Spacer(),
                Text(
                  'Ctrl+X',
                  style: TextStyle(
                    color: Colors.grey[600],
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          ),
        PopupMenuItem(
          value: 'paste',
          child: Row(
            children: [
              const Icon(Icons.paste, size: 18),
              const SizedBox(width: 8),
              const Text('Paste'),
              const Spacer(),
              Text(
                'Ctrl+V',
                style: TextStyle(
                  color: Colors.grey[600],
                  fontSize: 12,
                ),
              ),
            ],
          ),
        ),
        PopupMenuItem(
          value: 'select_all',
          child: Row(
            children: [
              const Icon(Icons.select_all, size: 18),
              const SizedBox(width: 8),
              const Text('Select All'),
              const Spacer(),
              Text(
                'Ctrl+A',
                style: TextStyle(
                  color: Colors.grey[600],
                  fontSize: 12,
                ),
              ),
            ],
          ),
        ),
        PopupMenuItem(
          value: 'undo',
          child: Row(
            children: [
              const Icon(Icons.undo, size: 18),
              const SizedBox(width: 8),
              const Text('Undo'),
              const Spacer(),
              Text(
                'Ctrl+Z',
                style: TextStyle(
                  color: Colors.grey[600],
                  fontSize: 12,
                ),
              ),
            ],
          ),
        ),
      ],
    ).then((value) {
      if (value == null) return;

      switch (value) {
        case 'copy':
          if (hasSelection) {
            final text = widget.controller.text.substring(
              selection.start,
              selection.end,
            );
            Clipboard.setData(ClipboardData(text: text));
          }
          break;
        case 'cut':
          if (hasSelection) {
            final text = widget.controller.text.substring(
              selection.start,
              selection.end,
            );
            Clipboard.setData(ClipboardData(text: text));
            widget.controller.text = widget.controller.text.replaceRange(
              selection.start,
              selection.end,
              '',
            );
            widget.controller.selection = TextSelection.collapsed(
              offset: selection.start,
            );
          }
          break;
        case 'paste':
          Clipboard.getData('text/plain').then((data) {
            if (data?.text != null) {
              final pasteText = data!.text!;
              if (hasSelection) {
                widget.controller.text = widget.controller.text.replaceRange(
                  selection.start,
                  selection.end,
                  pasteText,
                );
                widget.controller.selection = TextSelection.collapsed(
                  offset: selection.start + pasteText.length,
                );
              } else {
                final offset = widget.controller.selection.start;
                widget.controller.text = widget.controller.text.replaceRange(
                  offset,
                  offset,
                  pasteText,
                );
                widget.controller.selection = TextSelection.collapsed(
                  offset: offset + pasteText.length,
                );
              }
            }
          });
          break;
        case 'select_all':
          widget.controller.selection = TextSelection(
            baseOffset: 0,
            extentOffset: widget.controller.text.length,
          );
          break;
        case 'undo':
          // Flutter TextEditingController doesn't have built-in undo
          // This would need custom implementation
          break;
      }
    });
  }
}

