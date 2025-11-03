import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

/// Intent classes for keyboard shortcuts
class CopyIntent extends Intent {
  const CopyIntent();
}

class PasteIntent extends Intent {
  const PasteIntent();
}

class CutIntent extends Intent {
  const CutIntent();
}

class SelectAllIntent extends Intent {
  const SelectAllIntent();
}

class UndoIntent extends Intent {
  const UndoIntent();
}

class AbortIntent extends Intent {
  const AbortIntent();
}

/// Keyboard shortcuts handler widget
/// Wraps children with keyboard shortcut support
class KeyboardShortcutsHandler extends StatelessWidget {
  final Widget child;
  final VoidCallback? onAbort;

  const KeyboardShortcutsHandler({
    super.key,
    required this.child,
    this.onAbort,
  });

  @override
  Widget build(BuildContext context) {
    return Shortcuts(
      shortcuts: {
        LogicalKeySet(LogicalKeyboardKey.control, LogicalKeyboardKey.keyC):
            const CopyIntent(),
        LogicalKeySet(LogicalKeyboardKey.control, LogicalKeyboardKey.keyV):
            const PasteIntent(),
        LogicalKeySet(LogicalKeyboardKey.control, LogicalKeyboardKey.keyX):
            const CutIntent(),
        LogicalKeySet(LogicalKeyboardKey.control, LogicalKeyboardKey.keyA):
            const SelectAllIntent(),
        LogicalKeySet(LogicalKeyboardKey.control, LogicalKeyboardKey.keyZ):
            const UndoIntent(),
        LogicalKeySet(LogicalKeyboardKey.escape): const AbortIntent(),
      },
      child: Actions(
        actions: {
          CopyIntent: CallbackAction<CopyIntent>(
            onInvoke: (_) => _handleCopy(context),
          ),
          PasteIntent: CallbackAction<PasteIntent>(
            onInvoke: (_) => _handlePaste(context),
          ),
          CutIntent: CallbackAction<CutIntent>(
            onInvoke: (_) => _handleCut(context),
          ),
          SelectAllIntent: CallbackAction<SelectAllIntent>(
            onInvoke: (_) => _handleSelectAll(context),
          ),
          UndoIntent: CallbackAction<UndoIntent>(
            onInvoke: (_) => _handleUndo(context),
          ),
          AbortIntent: CallbackAction<AbortIntent>(
            onInvoke: (_) {
              if (onAbort != null) {
                onAbort!();
              }
              return null;
            },
          ),
        },
        child: Focus(
          autofocus: true,
          child: child,
        ),
      ),
    );
  }

  void _handleCopy(BuildContext context) {
    final textField = _findTextField(context);
    if (textField != null && textField.selection.isValid) {
      final selection = textField.selection;
      if (!selection.isCollapsed) {
        final text = textField.text.substring(
          selection.start,
          selection.end,
        );
        Clipboard.setData(ClipboardData(text: text));
      }
    }
  }

  void _handlePaste(BuildContext context) {
    final textField = _findTextField(context);
    if (textField != null) {
      Clipboard.getData('text/plain').then((data) {
        if (data?.text != null && textField.selection.isValid) {
          final selection = textField.selection;
          final pasteText = data!.text!;
          if (!selection.isCollapsed) {
            textField.text = textField.text.replaceRange(
              selection.start,
              selection.end,
              pasteText,
            );
            textField.selection = TextSelection.collapsed(
              offset: selection.start + pasteText.length,
            );
          } else {
            final offset = selection.start;
            textField.text = textField.text.replaceRange(
              offset,
              offset,
              pasteText,
            );
            textField.selection = TextSelection.collapsed(
              offset: offset + pasteText.length,
            );
          }
        }
      });
    }
  }

  void _handleCut(BuildContext context) {
    final textField = _findTextField(context);
    if (textField != null && textField.selection.isValid) {
      final selection = textField.selection;
      if (!selection.isCollapsed) {
        final text = textField.text.substring(
          selection.start,
          selection.end,
        );
        Clipboard.setData(ClipboardData(text: text));
        textField.text = textField.text.replaceRange(
          selection.start,
          selection.end,
          '',
        );
        textField.selection = TextSelection.collapsed(
          offset: selection.start,
        );
      }
    }
  }

  void _handleSelectAll(BuildContext context) {
    final textField = _findTextField(context);
    if (textField != null) {
      textField.selection = TextSelection(
        baseOffset: 0,
        extentOffset: textField.text.length,
      );
    }
  }

  void _handleUndo(BuildContext context) {
    // TextEditingController undo would need custom implementation
    // For now, this is a placeholder
  }

  TextEditingController? _findTextField(BuildContext context) {
    // Try to find a focused text field
    final focusNode = FocusScope.of(context).focusedChild;
    if (focusNode != null) {
      // This is a simplified approach - in practice, you'd track controllers
      // For now, we'll rely on the DesktopTextField handling these
      return null;
    }
    return null;
  }
}

