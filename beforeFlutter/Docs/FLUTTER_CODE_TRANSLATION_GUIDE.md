# 🔄 PyQt6 to Flutter Translation Guide

**Version:** 1.0  
**Purpose:** Side-by-side code examples showing PyQt6 → Flutter equivalents  
**Audience:** Developers migrating from PyQt6 to Flutter

---

## 📋 Table of Contents

1. [Conceptual Differences](#conceptual-differences)
2. [Basic UI Elements](#basic-ui-elements)
3. [WebSocket Communication](#websocket-communication)
4. [Audio Recording & Playback](#audio-recording--playback)
5. [System Tray](#system-tray)
6. [Settings & Persistence](#settings--persistence)
7. [Threading & Async](#threading--async)
8. [Complete Feature Examples](#complete-feature-examples)

---

## 🧠 Conceptual Differences

### Python (PyQt6) vs Dart (Flutter)

| Concept | Python/PyQt6 | Dart/Flutter |
|---------|--------------|--------------|
| **Language** | Python (dynamic, interpreted) | Dart (static, compiled) |
| **UI Paradigm** | Widget-based, imperative | Widget tree, declarative |
| **Threading** | `threading.Thread` | `async/await` (isolates for CPU-bound) |
| **State Management** | Manual (instance variables) | BLoC/Provider/Riverpod |
| **Layout** | Layout managers (QVBoxLayout, etc.) | Nested widgets (Column, Row, etc.) |
| **Signals/Slots** | Qt signals/slots | Callbacks, Streams, BLoC events |
| **Type System** | Optional (type hints) | Required (strong typing) |
| **Null Safety** | No (None checks manual) | Yes (null-safe by default) |

### Key Mental Shift

**PyQt6:** Modify widgets in place, update when needed
```python
self.label.setText("New text")  # Mutate existing widget
```

**Flutter:** Build new widget tree from scratch each time
```dart
Text("New text")  // Build new widget (Flutter optimizes internally)
```

---

## 🎨 Basic UI Elements

### Text Display

**PyQt6:**
```python
from PyQt6.QtWidgets import QLabel

label = QLabel("Hello World")
label.setFont(QFont("Arial", 14))
label.setStyleSheet("color: blue;")
```

**Flutter:**
```dart
Text(
  "Hello World",
  style: TextStyle(
    fontSize: 14,
    fontFamily: 'Arial',
    color: Colors.blue,
  ),
)
```

### Button

**PyQt6:**
```python
from PyQt6.QtWidgets import QPushButton

button = QPushButton("Click Me")
button.clicked.connect(self.on_click)

def on_click(self):
    print("Button clicked")
```

**Flutter:**
```dart
ElevatedButton(
  onPressed: () {
    print("Button clicked");
  },
  child: Text("Click Me"),
)
```

### Text Input

**PyQt6:**
```python
from PyQt6.QtWidgets import QLineEdit

input_field = QLineEdit()
input_field.setPlaceholderText("Type here...")
input_field.textChanged.connect(self.on_text_changed)

def on_text_changed(self, text):
    print(f"Text: {text}")
```

**Flutter:**
```dart
TextField(
  decoration: InputDecoration(
    hintText: "Type here...",
  ),
  onChanged: (text) {
    print("Text: $text");
  },
)
```

### Layout (Vertical)

**PyQt6:**
```python
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton

widget = QWidget()
layout = QVBoxLayout()
layout.addWidget(QLabel("Title"))
layout.addWidget(QPushButton("Button"))
widget.setLayout(layout)
```

**Flutter:**
```dart
Column(
  children: [
    Text("Title"),
    ElevatedButton(
      onPressed: () {},
      child: Text("Button"),
    ),
  ],
)
```

### Scrollable List

**PyQt6:**
```python
from PyQt6.QtWidgets import QListWidget

list_widget = QListWidget()
for i in range(100):
    list_widget.addItem(f"Item {i}")
```

**Flutter:**
```dart
ListView.builder(
  itemCount: 100,
  itemBuilder: (context, index) {
    return ListTile(
      title: Text("Item $index"),
    );
  },
)
```

---

## 🌐 WebSocket Communication

### Connecting to WebSocket

**PyQt6:**
```python
import asyncio
import websockets
import json

class WebSocketWorker(QObject):
    message_received = pyqtSignal(str, str)  # type, content
    
    async def connect(self):
        async with websockets.connect("ws://10.6.1.15:8006/ws/conversation") as ws:
            # Send start message
            await ws.send(json.dumps({
                "type": "start",
                "voice": "ara"
            }))
            
            # Receive messages
            async for message in ws:
                data = json.loads(message)
                self.message_received.emit(data["type"], data.get("content", ""))
```

**Flutter:**
```dart
import 'package:web_socket_channel/web_socket_channel.dart';
import 'dart:convert';

class WebSocketService {
  late WebSocketChannel channel;
  
  void connect() {
    channel = WebSocketChannel.connect(
      Uri.parse('ws://10.6.1.15:8006/ws/conversation'),
    );
    
    // Send start message
    channel.sink.add(json.encode({
      'type': 'start',
      'voice': 'ara',
    }));
    
    // Listen for messages
    channel.stream.listen((message) {
      final data = json.decode(message);
      // Handle message
      onMessageReceived(data['type'], data['content'] ?? '');
    });
  }
  
  void onMessageReceived(String type, String content) {
    // Process message
  }
}
```

### Sending Messages

**PyQt6:**
```python
# In async context
await ws.send(json.dumps({
    "type": "text",
    "data": "Hello Sparky"
}))
```

**Flutter:**
```dart
channel.sink.add(json.encode({
  'type': 'text',
  'data': 'Hello Sparky',
}));
```

---

## 🎙️ Audio Recording & Playback

### Recording Audio

**PyQt6:**
```python
import sounddevice as sd
import numpy as np

class AudioRecorder:
    def __init__(self):
        self.stream = None
        
    def start_recording(self, callback):
        def audio_callback(indata, frames, time, status):
            # indata is numpy array
            callback(indata.tobytes())
        
        self.stream = sd.InputStream(
            samplerate=16000,
            channels=1,
            dtype='int16',
            callback=audio_callback
        )
        self.stream.start()
    
    def stop_recording(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()
```

**Flutter:**
```dart
import 'package:record/record.dart';

class AudioRecorder {
  final _recorder = Record();
  StreamSubscription? _subscription;
  
  Future<void> startRecording(Function(Uint8List) callback) async {
    final stream = await _recorder.startStream(
      RecordConfig(
        encoder: AudioEncoder.pcm16bit,
        sampleRate: 16000,
        numChannels: 1,
      ),
    );
    
    _subscription = stream.listen(callback);
  }
  
  Future<void> stopRecording() async {
    await _recorder.stop();
    await _subscription?.cancel();
  }
}
```

### Playing Audio

**PyQt6:**
```python
import sounddevice as sd
import numpy as np

class AudioPlayer:
    def play(self, audio_data, sample_rate=24000):
        # audio_data is bytes
        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        sd.play(audio_array, sample_rate)
        sd.wait()  # Wait until playback finishes
```

**Flutter:**
```dart
import 'package:just_audio/just_audio.dart';

class AudioPlayer {
  final _player = AudioPlayer();
  
  Future<void> play(Uint8List audioData) async {
    // Create audio source from bytes
    final source = BytesSource(audioData);
    
    await _player.setAudioSource(source);
    await _player.play();
  }
  
  Future<void> stop() async {
    await _player.stop();
  }
}
```

---

## 🗂️ System Tray

### Creating System Tray

**PyQt6:**
```python
from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw

class TrayApp:
    def create_icon_image(self, color):
        # Create 64x64 image
        image = Image.new('RGB', (64, 64), color)
        draw = ImageDraw.Draw(image)
        draw.ellipse((16, 16, 48, 48), fill='white')
        return image
    
    def get_menu(self):
        return Menu(
            MenuItem("Show", self.show_window),
            MenuItem("Settings", self.show_settings),
            Menu.SEPARATOR,
            MenuItem("Quit", self.quit_app)
        )
    
    def run(self):
        self.icon = Icon(
            "Sparky",
            self.create_icon_image("green"),
            "Sparky Voice AI",
            self.get_menu()
        )
        self.icon.run()
```

**Flutter:**
```dart
import 'package:tray_manager/tray_manager.dart';

class TrayService with TrayListener {
  Future<void> init() async {
    // Set icon
    await trayManager.setIcon('assets/icons/tray_green.png');
    
    // Create menu
    Menu menu = Menu(items: [
      MenuItem(
        key: 'show',
        label: 'Show',
      ),
      MenuItem(
        key: 'settings',
        label: 'Settings',
      ),
      MenuItem.separator(),
      MenuItem(
        key: 'quit',
        label: 'Quit',
      ),
    ]);
    
    await trayManager.setContextMenu(menu);
    trayManager.addListener(this);
  }
  
  @override
  void onTrayMenuItemClick(MenuItem menuItem) {
    switch (menuItem.key) {
      case 'show':
        windowManager.show();
        break;
      case 'settings':
        // Show settings
        break;
      case 'quit':
        windowManager.destroy();
        break;
    }
  }
  
  Future<void> updateIcon(String iconName) async {
    await trayManager.setIcon('assets/icons/tray_$iconName.png');
  }
}
```

---

## 💾 Settings & Persistence

### Saving Settings

**PyQt6:**
```python
import configparser
from pathlib import Path

class Settings:
    def __init__(self):
        self.config_path = Path(__file__).parent / 'config.ini'
        self.config = configparser.ConfigParser()
        
    def load(self):
        self.config.read(self.config_path)
        
    def get(self, section, key, fallback=None):
        return self.config.get(section, key, fallback=fallback)
    
    def set(self, section, key, value):
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, value)
        
    def save(self):
        with open(self.config_path, 'w') as f:
            self.config.write(f)

# Usage
settings = Settings()
settings.load()
voice = settings.get('VoiceAI', 'default_voice', fallback='ara')
settings.set('VoiceAI', 'default_voice', 'alex')
settings.save()
```

**Flutter:**
```dart
import 'package:shared_preferences/shared_preferences.dart';

class Settings {
  static SharedPreferences? _prefs;
  
  static Future<void> init() async {
    _prefs = await SharedPreferences.getInstance();
  }
  
  static String get defaultVoice {
    return _prefs?.getString('default_voice') ?? 'ara';
  }
  
  static set defaultVoice(String value) {
    _prefs?.setString('default_voice', value);
  }
  
  static String get serverHost {
    return _prefs?.getString('server_host') ?? '10.6.1.15';
  }
  
  static set serverHost(String value) {
    _prefs?.setString('server_host', value);
  }
}

// Usage
await Settings.init();
String voice = Settings.defaultVoice;
Settings.defaultVoice = 'alex';
// Automatically saved
```

---

## 🔄 Threading & Async

### Background Task

**PyQt6:**
```python
import threading

class BackgroundWorker:
    def __init__(self):
        self.thread = None
        
    def start_work(self):
        self.thread = threading.Thread(target=self.do_work)
        self.thread.daemon = True
        self.thread.start()
    
    def do_work(self):
        # Long-running task
        import time
        for i in range(10):
            print(f"Working... {i}")
            time.sleep(1)
```

**Flutter:**
```dart
class BackgroundWorker {
  void startWork() async {
    // Async task (doesn't block UI)
    await doWork();
  }
  
  Future<void> doWork() async {
    for (int i = 0; i < 10; i++) {
      print("Working... $i");
      await Future.delayed(Duration(seconds: 1));
    }
  }
}
```

### CPU-Intensive Task (Isolate)

**PyQt6:**
```python
import threading

def heavy_computation(data):
    # Intensive work
    return processed_data

thread = threading.Thread(target=heavy_computation, args=(data,))
thread.start()
```

**Flutter:**
```dart
import 'dart:isolate';

Future<void> heavyComputation(SendPort sendPort) async {
  // Intensive work
  final result = processData();
  sendPort.send(result);
}

Future<void> runHeavyTask() async {
  final receivePort = ReceivePort();
  await Isolate.spawn(heavyComputation, receivePort.sendPort);
  
  receivePort.listen((result) {
    print("Result: $result");
  });
}
```

---

## 🎯 Complete Feature Examples

### Example 1: Chat Message Display

**PyQt6:**
```python
from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtGui import QTextCursor, QTextCharFormat, QColor

class ChatWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        
    def add_message(self, role, content):
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        # Format for user
        if role == "user":
            format = QTextCharFormat()
            format.setForeground(QColor("blue"))
            cursor.setCharFormat(format)
            cursor.insertText(f"You: {content}\n")
        
        # Format for assistant
        else:
            format = QTextCharFormat()
            format.setForeground(QColor("green"))
            cursor.setCharFormat(format)
            cursor.insertText(f"Sparky: {content}\n")
        
        self.chat_display.setTextCursor(cursor)
        self.chat_display.ensureCursorVisible()
```

**Flutter:**
```dart
class ChatScreen extends StatelessWidget {
  final List<Message> messages;
  
  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      itemCount: messages.length,
      itemBuilder: (context, index) {
        final message = messages[index];
        return MessageBubble(message: message);
      },
    );
  }
}

class MessageBubble extends StatelessWidget {
  final Message message;
  
  const MessageBubble({required this.message});
  
  @override
  Widget build(BuildContext context) {
    final isUser = message.role == 'user';
    
    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: EdgeInsets.symmetric(vertical: 4, horizontal: 8),
        padding: EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: isUser ? Colors.blue[100] : Colors.green[100],
          borderRadius: BorderRadius.circular(12),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              isUser ? 'You' : 'Sparky',
              style: TextStyle(
                fontWeight: FontWeight.bold,
                color: isUser ? Colors.blue[900] : Colors.green[900],
              ),
            ),
            SizedBox(height: 4),
            Text(message.content),
          ],
        ),
      ),
    );
  }
}
```

### Example 2: State Management Pattern

**PyQt6:**
```python
from PyQt6.QtCore import QObject, pyqtSignal

class ConversationState(QObject):
    # Signals for state changes
    message_added = pyqtSignal(str, str)  # role, content
    state_changed = pyqtSignal(str)  # new state
    
    def __init__(self):
        super().__init__()
        self.messages = []
        self.current_state = "idle"
    
    def add_message(self, role, content):
        self.messages.append({"role": role, "content": content})
        self.message_added.emit(role, content)
    
    def set_state(self, state):
        self.current_state = state
        self.state_changed.emit(state)

# Usage
state = ConversationState()
state.message_added.connect(lambda r, c: print(f"{r}: {c}"))
state.add_message("user", "Hello")
```

**Flutter (with BLoC):**
```dart
// Events
abstract class ConversationEvent {}

class AddMessage extends ConversationEvent {
  final String role;
  final String content;
  
  AddMessage(this.role, this.content);
}

class ChangeState extends ConversationEvent {
  final String state;
  
  ChangeState(this.state);
}

// States
class ConversationState {
  final List<Message> messages;
  final String currentState;
  
  const ConversationState({
    required this.messages,
    required this.currentState,
  });
  
  ConversationState copyWith({
    List<Message>? messages,
    String? currentState,
  }) {
    return ConversationState(
      messages: messages ?? this.messages,
      currentState: currentState ?? this.currentState,
    );
  }
}

// BLoC
class ConversationBloc extends Bloc<ConversationEvent, ConversationState> {
  ConversationBloc() : super(ConversationState(messages: [], currentState: 'idle')) {
    on<AddMessage>((event, emit) {
      final newMessages = List<Message>.from(state.messages)
        ..add(Message(role: event.role, content: event.content));
      
      emit(state.copyWith(messages: newMessages));
    });
    
    on<ChangeState>((event, emit) {
      emit(state.copyWith(currentState: event.state));
    });
  }
}

// Usage in UI
BlocBuilder<ConversationBloc, ConversationState>(
  builder: (context, state) {
    return ListView.builder(
      itemCount: state.messages.length,
      itemBuilder: (context, index) {
        return MessageBubble(message: state.messages[index]);
      },
    );
  },
)

// Add message
context.read<ConversationBloc>().add(AddMessage('user', 'Hello'));
```

### Example 3: Settings Dialog

**PyQt6:**
```python
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QComboBox, QPushButton

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        
        layout = QVBoxLayout()
        
        # Voice selection
        self.voice_combo = QComboBox()
        self.voice_combo.addItems(["ara", "alex", "emma"])
        layout.addWidget(self.voice_combo)
        
        # Save button
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_btn)
        
        self.setLayout(layout)
    
    def save_settings(self):
        voice = self.voice_combo.currentText()
        # Save to config
        self.accept()
```

**Flutter:**
```dart
class SettingsDialog extends StatefulWidget {
  @override
  _SettingsDialogState createState() => _SettingsDialogState();
}

class _SettingsDialogState extends State<SettingsDialog> {
  String selectedVoice = 'ara';
  
  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text('Settings'),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          DropdownButton<String>(
            value: selectedVoice,
            items: ['ara', 'alex', 'emma'].map((voice) {
              return DropdownMenuItem(
                value: voice,
                child: Text(voice),
              );
            }).toList(),
            onChanged: (value) {
              setState(() {
                selectedVoice = value!;
              });
            },
          ),
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: Text('Cancel'),
        ),
        ElevatedButton(
          onPressed: () {
            // Save settings
            Settings.defaultVoice = selectedVoice;
            Navigator.pop(context);
          },
          child: Text('Save'),
        ),
      ],
    );
  }
}

// Show dialog
showDialog(
  context: context,
  builder: (context) => SettingsDialog(),
);
```

---

## 🔑 Key Takeaways

### What's Similar
- Both use widgets/components for UI
- Both have event-driven architecture
- Both support async programming
- Both have rich plugin ecosystems

### What's Different

| Aspect | PyQt6 | Flutter |
|--------|-------|---------|
| **State** | Mutable, in-place updates | Immutable, rebuild widget tree |
| **Type Safety** | Optional | Required (strong typing) |
| **Hot Reload** | No | Yes (instant feedback) |
| **Cross-platform** | Desktop only | All platforms |
| **Learning Curve** | Medium (if you know Python) | Medium (learn Dart) |
| **Development Speed** | Medium | Fast (hot reload) |

### Mental Model Shift

**From:** "Create widgets once, update them when needed"
```python
self.label = QLabel("Hello")
# Later...
self.label.setText("World")  # Mutate
```

**To:** "Describe UI based on current state, Flutter handles updates"
```dart
Text(isGreeting ? "Hello" : "World")  // Rebuild with new state
```

---

## 📚 Additional Resources

### Learning Dart
- Dart Language Tour: https://dart.dev/guides/language/language-tour
- Dart for Python Developers: https://dart.dev/guides/language/coming-from/python

### Learning Flutter
- Flutter for Qt Developers: https://docs.flutter.dev/get-started/flutter-for/qt-devs
- Flutter Widget Catalog: https://docs.flutter.dev/ui/widgets
- Flutter Codelabs: https://docs.flutter.dev/codelabs

### State Management
- BLoC Library: https://bloclibrary.dev
- Provider: https://pub.dev/packages/provider
- Riverpod: https://riverpod.dev

---

## 🎯 Quick Reference

### Common Patterns

**Create UI:**
```dart
// PyQt6: Imperative
widget = QWidget()
layout = QVBoxLayout()
layout.addWidget(child1)
layout.addWidget(child2)
widget.setLayout(layout)

// Flutter: Declarative
Column(
  children: [child1, child2],
)
```

**Update UI:**
```dart
// PyQt6: Mutate
self.label.setText("New text")

// Flutter: Rebuild
setState(() {
  text = "New text";
})
// Then in build():
Text(text)
```

**Handle Events:**
```dart
// PyQt6: Signals/Slots
button.clicked.connect(self.on_click)

// Flutter: Callbacks
onPressed: () {
  handleClick();
}
```

**Async Operations:**
```dart
// PyQt6: Threading
thread = threading.Thread(target=work)
thread.start()

// Flutter: async/await
Future<void> doWork() async {
  await something();
}
```

---

## ✅ Translation Checklist

When converting PyQt6 code to Flutter:

- [ ] Replace QWidget with Flutter widget (Container, Column, Row, etc.)
- [ ] Replace layouts with Flutter layout widgets
- [ ] Replace signals/slots with callbacks or BLoC events
- [ ] Replace threading with async/await
- [ ] Replace mutable state with setState() or BLoC
- [ ] Replace config files with SharedPreferences
- [ ] Replace QThread with Future/Stream
- [ ] Replace manual repaints with rebuild triggers

**You're now ready to translate PyQt6 code to Flutter! 🚀**
