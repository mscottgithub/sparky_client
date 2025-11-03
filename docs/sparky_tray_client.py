#!/usr/bin/env python3
"""
Sparky Voice-AI System Tray Client v5.0.2 - PyQt6 Edition
Always-listening voice assistant with wake word detection
No cloud dependencies - fully local operation
TRUE STREAMING: Plays audio as it arrives for sub-second latency
AUTO-CALIBRATION: Automatically adjusts to any microphone's noise floor
DUAL-STREAM ARCHITECTURE: Dedicated exit word detection for instant response
ECHO CANCELLATION: Subtracts AI voice from microphone to enable mid-speech interruption
V5.0.0 PYQT6: Professional chat window with native UI features
  - Native right-click menus (automatic copy/select all)
  - Perfect text selection (built-in)
  - Modern Windows 11 styling
  - Smooth font rendering
  - Theme support (light/dark)
V5.0.1 FIX: Eliminated text streaming stutter by buffering first tokens
V5.0.2 FIX: Fixed cursor position calculation causing text duplication during streaming
  - _streaming_cursor_pos now correctly points to start of content
  - _update_streaming_message no longer adds extra leading space
"""
import sys
import os
import configparser
import tempfile
import threading
import queue
from pathlib import Path
import time
from collections import deque
import asyncio
import json
import base64
from datetime import datetime
import re

import requests
import sounddevice as sd
import soundfile as sf
import numpy as np
from PIL import Image, ImageDraw
from pystray import Icon, Menu, MenuItem
import openwakeword
from openwakeword.model import Model
from pynput import keyboard

# PyQt6 imports for professional GUI
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QLabel, QMessageBox, QFileDialog, QToolBar
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QObject
from PyQt6.QtGui import QTextCursor, QTextCharFormat, QColor, QFont, QAction

# WebSocket for orchestrator
try:
    import websockets
except ImportError:
    print("⚠️ Missing 'websockets' - install with: pip install websockets")
    print("   Falling back to direct API calls")
    websockets = None

# Version info
VERSION = "5.0.2"  # Added: Auto-focus on text input when chat opens
REQUIRED_ORCHESTRATOR_VERSION = "2.5.0"

# Load configuration with inline comment support
config = configparser.ConfigParser(inline_comment_prefixes=('#', ';'))
config_path = Path(__file__).parent / 'config.ini'
config.read(config_path)

# Voice-AI Service Configuration
SERVER_HOST = config.get('VoiceAI', 'server_host', fallback='10.6.1.15')
TTS_PORT = config.getint('VoiceAI', 'tts_port', fallback=8004)
WHISPER_PORT = config.getint('VoiceAI', 'whisper_port', fallback=8005)
ORCH_PORT = config.getint('VoiceAI', 'orch_port', fallback=8006)
DEFAULT_VOICE = config.get('VoiceAI', 'default_voice', fallback='ara').lower()

# Audio Configuration
SAMPLE_RATE = config.getint('Audio', 'sample_rate', fallback=16000)
CHANNELS = config.getint('Audio', 'channels', fallback=1)
BASE_SILENCE_THRESHOLD = config.getfloat('Audio', 'silence_threshold', fallback=0.015)
SILENCE_DURATION = config.getfloat('Audio', 'silence_duration', fallback=1.5)
DEBUG_AUDIO = config.getboolean('Audio', 'debug_audio', fallback=False)
DEBUG_WAKEWORD = config.getboolean('Audio', 'debug_wakeword', fallback=False)
AUTO_CALIBRATE = config.getboolean('Audio', 'auto_calibrate', fallback=True)
CALIBRATION_DURATION = config.getfloat('Audio', 'calibration_duration', fallback=2.0)

# Emergency Abort Configuration
AUDIO_BUFFER_DURATION = 4.0
ABORT_HOTKEY = keyboard.Key.esc

# Echo Cancellation Configuration
ECHO_BUFFER_SIZE = 100
ECHO_CANCEL_ENABLED = True

# Conversation Configuration
GREETING_MESSAGE = config.get('Conversation', 'greeting', fallback='Yes? How can I help you?')
GOODBYE_MESSAGE = config.get('Conversation', 'goodbye', fallback='Goodbye!')

# TTS Audio Configuration
TTS_SAMPLE_RATE = 24000
TTS_CHANNELS = 1

# Wake Word Configuration
WAKE_MODELS_DIR = Path(__file__).parent / 'wake_models'
WAKE_MODELS_DIR.mkdir(exist_ok=True)

# Chat Window Configuration
ALLOW_DELETE = config.getboolean('ChatWindow', 'allow_delete', fallback=True)
ALLOW_EDIT = config.getboolean('ChatWindow', 'allow_edit', fallback=True)

# Build URLs
TTS_URL = f"http://{SERVER_HOST}:{TTS_PORT}"
WHISPER_URL = f"http://{SERVER_HOST}:{WHISPER_PORT}"
ORCH_WS_URL = f"ws://{SERVER_HOST}:{ORCH_PORT}/ws/conversation"


class VoiceState:
    """Tracks the current state of the voice assistant"""
    IDLE = "idle"
    CALIBRATING = "calibrating"
    LISTENING_FOR_WAKE = "listening_wake"
    ACTIVE_CONVERSATION = "active"
    RECORDING_COMMAND = "recording"
    PROCESSING = "processing"
    SPEAKING = "speaking"


class InputMode:
    """Input mode types"""
    VAD = "vad"
    MANUAL = "manual"


class ChatMessage:
    """Represents a single chat message"""
    def __init__(self, role: str, content: str, timestamp: datetime = None):
        self.role = role  # "user" or "assistant"
        self.content = content
        self.timestamp = timestamp or datetime.now()
        self.id = id(self)


class WebSocketWorker(QObject):
    """Worker object for WebSocket operations - runs in separate thread"""
    
    # Signals for thread-safe communication with GUI
    message_received = pyqtSignal(str, str, bool)  # msg_type, content, streaming_started
    connection_status = pyqtSignal(bool, str)  # connected, status_message
    session_id_received = pyqtSignal(str)  # session_id
    
    def __init__(self, assistant, send_queue):
        super().__init__()
        self.assistant = assistant
        self.send_queue = send_queue
        self.ws = None
        self.ws_connected = False
        self._closing = False
        self.loop = None
    
    def run(self):
        """Run WebSocket connection loop"""
        try:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(self._websocket_handler())
        except Exception as e:
            print(f"❌ WebSocket loop error: {e}")
            self.connection_status.emit(False, f"Connection error: {e}")
        finally:
            self.ws_connected = False
            if self.loop:
                self.loop.close()
    
    def stop(self):
        """Stop WebSocket connection"""
        self._closing = True
        if self.ws and self.loop:
            try:
                future = asyncio.run_coroutine_threadsafe(self.ws.close(), self.loop)
                future.result(timeout=1.0)
            except Exception as e:
                print(f"WebSocket close error: {e}")
    
    async def _websocket_handler(self):
        """Main WebSocket connection handler"""
        if not websockets:
            raise Exception("WebSockets library not available")
        
        try:
            async with websockets.connect(ORCH_WS_URL, ping_interval=20, ping_timeout=10) as ws:
                self.ws = ws
                self.ws_connected = True
                self.connection_status.emit(True, "Connected")
                
                # Send initial START message
                start_msg = {
                    "type": "start",
                    "voice": DEFAULT_VOICE,
                    "session_id": self.assistant.session_id
                }
                await ws.send(json.dumps(start_msg))
                
                # Receive session_id
                response = await ws.recv()
                data = json.loads(response)
                if data.get("type") == "meta" and data.get("event") == "session_id":
                    session_id = data.get("value")
                    if not self.assistant.session_id:
                        self.assistant.session_id = session_id
                        self.assistant.conversation_active = True
                        self.session_id_received.emit(session_id)
                
                # Create tasks for sending and receiving
                send_task = asyncio.create_task(self._send_handler(ws))
                recv_task = asyncio.create_task(self._receive_handler(ws))
                
                # Wait for both tasks
                await asyncio.gather(send_task, recv_task, return_exceptions=True)
        
        except Exception as e:
            print(f"❌ WebSocket error: {e}")
            self.ws_connected = False
            self.connection_status.emit(False, f"Connection lost: {e}")
    
    async def _send_handler(self, ws):
        """Handle outgoing messages"""
        while not self._closing and self.ws_connected:
            try:
                try:
                    msg_type, msg_data = self.send_queue.get_nowait()
                except queue.Empty:
                    await asyncio.sleep(0.1)
                    continue
                
                await ws.send(json.dumps({
                    "type": msg_type,
                    "text": msg_data
                }))
            
            except Exception as e:
                print(f"❌ Send error: {e}")
                break
    
    async def _receive_handler(self, ws):
        """Handle incoming messages"""
        current_response = ""
        streaming_started = False
        
        while not self._closing and self.ws_connected:
            try:
                msg = await ws.recv()
                
                if isinstance(msg, str):
                    data = json.loads(msg)
                    msg_type = data.get("type")
                    
                    if msg_type == "text_token":
                        token = data.get("token", "")
                        current_response += token
                        self.message_received.emit("token", current_response, streaming_started)
                        streaming_started = True
                    
                    elif msg_type == "text_response":
                        final_text = data.get("text", "")
                        if final_text:
                            self.message_received.emit("final", final_text, streaming_started)
                        current_response = ""
                        streaming_started = False
                    
                    elif msg_type == "error":
                        error_msg = data.get("detail", "Unknown error")
                        self.message_received.emit("error", error_msg, False)
                        print(f"❌ Server error: {error_msg}")
                    
                    elif msg_type == "done":
                        current_response = ""
                        streaming_started = False
            
            except websockets.exceptions.ConnectionClosed:
                print("🔌 WebSocket connection closed")
                break
            except Exception as e:
                print(f"❌ Receive error: {e}")
                break


class ChatWindow(QMainWindow):
    """Professional PyQt6 text chat window
    
    Architecture:
    - Opens ONE WebSocket connection when window is shown
    - Connection stays alive for entire chat session
    - Reused for ALL messages (no reconnection per message)
    - Closed only when window closes
    - Native right-click menus (automatic)
    - Perfect text selection (automatic)
    - Modern Windows 11 styling
    """
    
    def __init__(self, parent_app, assistant):
        super().__init__()
        
        self.parent_app = parent_app
        self.assistant = assistant
        self.messages = []
        self.is_visible = False
        
        # WebSocket worker and thread
        self.ws_worker = None
        self.ws_thread = None
        self.send_queue = queue.Queue()
        
        # Streaming state
        self._streaming_started = False
        self._streaming_displayed = False  # Track if first token has been displayed
        self._current_message_index = -1
        
        # Theme configuration (matches Tkinter colors exactly)
        self.themes = {
            "light": {
                "bg": "#C4C4D8",
                "user_msg_bg": "#4A90E2",
                "user_msg_fg": "#FFFFFF",
                "ai_msg_bg": "#D4D4E8",
                "ai_msg_fg": "#1a1a1a",
                "input_bg": "#E0E0F0",
                "input_fg": "#1a1a1a",
                "window_bg": "#B8B8CC",
                "timestamp_fg": "#808080"
            },
            "dark": {
                "bg": "#2B2B2B",
                "user_msg_bg": "#3A7BC8",
                "user_msg_fg": "#FFFFFF",
                "ai_msg_bg": "#3C3C3C",
                "ai_msg_fg": "#E0E0E0",
                "input_bg": "#333333",
                "input_fg": "#E0E0E0",
                "window_bg": "#1E1E1E",
                "timestamp_fg": "#888888"
            }
        }
        
        # Load theme preference
        self.current_theme = config.get('UI', 'theme', fallback='light')
        if self.current_theme not in self.themes:
            self.current_theme = 'light'
        
        self._setup_ui()
        self._apply_theme()
        
        # Hide initially
        self.hide()
    
    def _setup_ui(self):
        """Setup the UI components"""
        self.setWindowTitle(f"Sparky Text Chat v{VERSION}")
        self.resize(800, 600)
        
        # Central widget and layout
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Toolbar at top
        toolbar = QHBoxLayout()
        toolbar.setSpacing(5)
        
        # Toolbar buttons
        self.clear_btn = QPushButton("🗑️ Clear")
        self.clear_btn.clicked.connect(self.clear_conversation)
        self.clear_btn.setFixedWidth(100)
        toolbar.addWidget(self.clear_btn)
        
        self.export_btn = QPushButton("💾 Export")
        self.export_btn.clicked.connect(self.export_chat)
        self.export_btn.setFixedWidth(100)
        toolbar.addWidget(self.export_btn)
        
        self.new_chat_btn = QPushButton("🔄 New Chat")
        self.new_chat_btn.clicked.connect(self.start_new_chat)
        self.new_chat_btn.setFixedWidth(120)
        toolbar.addWidget(self.new_chat_btn)
        
        # Theme toggle button
        theme_icon = "🌙" if self.current_theme == "light" else "☀️"
        self.theme_btn = QPushButton(theme_icon)
        self.theme_btn.clicked.connect(self.toggle_theme)
        self.theme_btn.setFixedWidth(40)
        toolbar.addWidget(self.theme_btn)
        
        toolbar.addStretch()
        
        # Mode indicator
        self.mode_label = QLabel("")
        self.mode_label.setStyleSheet("font-weight: bold; font-size: 10pt;")
        toolbar.addWidget(self.mode_label)
        
        layout.addLayout(toolbar)
        
        # Chat display area - THIS IS WHERE THE MAGIC HAPPENS
        # QTextEdit provides:
        # - Native right-click menu (copy, select all) - AUTOMATIC ✅
        # - Perfect text selection - AUTOMATIC ✅
        # - Smooth scrolling - AUTOMATIC ✅
        # - Modern font rendering - AUTOMATIC ✅
        self.chat_text = QTextEdit()
        self.chat_text.setReadOnly(True)  # Prevents typing, allows selection
        self.chat_text.setFont(QFont("Segoe UI", 10))
        layout.addWidget(self.chat_text)
        
        # Typing indicator (hidden by default)
        self.typing_label = QLabel("")
        self.typing_label.setStyleSheet("font-style: italic; color: gray; font-size: 9pt;")
        self.typing_label.hide()
        layout.addWidget(self.typing_label)
        
        # Input area at bottom
        input_layout = QHBoxLayout()
        input_layout.setSpacing(5)
        
        # Input text box
        self.input_text = QTextEdit()
        self.input_text.setMaximumHeight(80)
        self.input_text.setFont(QFont("Segoe UI", 10))
        self.input_text.setPlaceholderText("Type your message...")
        
        # Handle Enter key to send
        self.input_text.installEventFilter(self)
        
        input_layout.addWidget(self.input_text)
        
        # Send button
        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self.send_message)
        self.send_btn.setFixedWidth(100)
        input_layout.addWidget(self.send_btn)
        
        layout.addLayout(input_layout)
        
        self._update_mode_indicator()
    
    def eventFilter(self, obj, event):
        """Handle Enter key press in input box"""
        if obj == self.input_text and event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
                if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                    # Shift+Enter = newline (allow default behavior)
                    return False
                else:
                    # Enter alone = send message
                    self.send_message()
                    return True
        return super().eventFilter(obj, event)
    
    def _apply_theme(self):
        """Apply current theme to all UI elements"""
        theme = self.themes[self.current_theme]
        
        # Update theme button icon
        theme_icon = "🌙" if self.current_theme == "light" else "☀️"
        self.theme_btn.setText(theme_icon)
        
        # Chat text area styling
        self.chat_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {theme['bg']};
                color: {theme['ai_msg_fg']};
                border: 1px solid {theme['window_bg']};
                border-radius: 5px;
                padding: 5px;
            }}
        """)
        
        # Input text area styling
        self.input_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {theme['input_bg']};
                color: {theme['input_fg']};
                border: 1px solid {theme['window_bg']};
                border-radius: 5px;
                padding: 5px;
            }}
        """)
        
        # Window background
        self.centralWidget().setStyleSheet(f"""
            QWidget {{
                background-color: {theme['window_bg']};
            }}
        """)
        
        # Buttons styling
        button_style = f"""
            QPushButton {{
                background-color: {theme['input_bg']};
                color: {theme['input_fg']};
                border: 1px solid {theme['window_bg']};
                border-radius: 3px;
                padding: 5px;
            }}
            QPushButton:hover {{
                background-color: {theme['user_msg_bg']};
                color: white;
            }}
        """
        self.clear_btn.setStyleSheet(button_style)
        self.export_btn.setStyleSheet(button_style)
        self.new_chat_btn.setStyleSheet(button_style)
        self.theme_btn.setStyleSheet(button_style)
        self.send_btn.setStyleSheet(button_style)
        
        print(f"🎨 Switched to {self.current_theme} theme")
    
    def toggle_theme(self):
        """Toggle between light and dark themes"""
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        
        # Save to config
        if not config.has_section('UI'):
            config.add_section('UI')
        config.set('UI', 'theme', self.current_theme)
        try:
            with open(config_path, 'w') as f:
                config.write(f)
        except Exception as e:
            print(f"⚠️ Failed to save theme preference: {e}")
        
        self._apply_theme()
        
        # Redraw all messages with new theme
        self._redraw_messages()
    
    def _redraw_messages(self):
        """Redraw all messages with current theme"""
        # Save cursor position
        cursor = self.chat_text.textCursor()
        
        # Clear and redraw
        self.chat_text.clear()
        for msg in self.messages:
            self._display_message(msg.role, msg.content, msg.timestamp, append=True)
        
        # Restore scroll position
        self.chat_text.setTextCursor(cursor)
    
    def _update_mode_indicator(self):
        """Update the conversation mode indicator"""
        if self.assistant.conversation_active or self.assistant.session_id:
            self.mode_label.setText("📝 Continuing conversation")
            self.mode_label.setStyleSheet("font-weight: bold; font-size: 10pt; color: green;")
        else:
            self.mode_label.setText("🆕 New conversation")
            self.mode_label.setStyleSheet("font-weight: bold; font-size: 10pt; color: blue;")
    
    def _display_message(self, role: str, content: str, timestamp: datetime = None, append: bool = True):
        """Display a message in the chat window
        
        PyQt6 Excellence:
        - Uses QTextCursor for precise text manipulation
        - QTextCharFormat for rich styling
        - No manual tag management needed
        - Perfect text rendering
        """
        timestamp = timestamp or datetime.now()
        time_str = timestamp.strftime("%H:%M")
        theme = self.themes[self.current_theme]
        
        cursor = self.chat_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        # Timestamp and icon
        icon = "👤" if role == "user" else "🤖"
        timestamp_fmt = QTextCharFormat()
        timestamp_fmt.setForeground(QColor(theme["timestamp_fg"]))
        timestamp_fmt.setFont(QFont("Segoe UI", 8))
        
        cursor.insertText(f"{icon} {time_str}\n", timestamp_fmt)
        
        # Message content with styling
        msg_fmt = QTextCharFormat()
        if role == "user":
            msg_fmt.setBackground(QColor(theme["user_msg_bg"]))
            msg_fmt.setForeground(QColor(theme["user_msg_fg"]))
        else:
            msg_fmt.setBackground(QColor(theme["ai_msg_bg"]))
            msg_fmt.setForeground(QColor(theme["ai_msg_fg"]))
        
        msg_fmt.setFont(QFont("Segoe UI", 10))
        
        # Insert message with padding
        cursor.insertText(f" {content} ", msg_fmt)
        cursor.insertText("\n\n")
        
        # Track streaming position for AI messages
        if role == "assistant" and append:
            # Point to start of content (after leading space) so updates replace correctly
            # Format is " {content} \n\n", so we need to go back: len(content) + space + \n\n = len + 3
            self._streaming_cursor_pos = cursor.position() - len(content) - 3
        
        self.chat_text.setTextCursor(cursor)
        self.chat_text.ensureCursorVisible()
    
    def _update_streaming_message(self, content: str):
        """Update the last AI message with streaming tokens
        
        V5.0.2 FIX: Correctly replaces only the content portion, not duplicating text.
        - Assumes leading space already exists from _display_message
        - Only replaces "content \n\n" portion
        - No extra leading space added
        """
        if not hasattr(self, '_streaming_cursor_pos'):
            return
        
        theme = self.themes[self.current_theme]
        
        # Move cursor to streaming position
        cursor = self.chat_text.textCursor()
        cursor.setPosition(self._streaming_cursor_pos)
        
        # Select from streaming position to end
        cursor.movePosition(QTextCursor.MoveOperation.End, QTextCursor.MoveMode.KeepAnchor)
        
        # Replace with updated content (no leading space - original display has it)
        msg_fmt = QTextCharFormat()
        msg_fmt.setBackground(QColor(theme["ai_msg_bg"]))
        msg_fmt.setForeground(QColor(theme["ai_msg_fg"]))
        msg_fmt.setFont(QFont("Segoe UI", 10))
        
        cursor.insertText(f"{content} \n\n", msg_fmt)  # No leading space!
        
        self.chat_text.ensureCursorVisible()
    
    def send_message(self):
        """Send text message through persistent WebSocket connection"""
        text = self.input_text.toPlainText().strip()
        if not text:
            return
        
        # Clear input
        self.input_text.clear()
        
        # Add user message to display
        user_msg = ChatMessage("user", text)
        self.messages.append(user_msg)
        self._display_message("user", text)
        
        # Check connection
        if not self.ws_worker or not self.ws_worker.ws_connected:
            QMessageBox.warning(self, "Not Connected", "Not connected to server. Reconnecting...")
            self._connect_websocket()
            return
        
        # Show typing indicator
        self.typing_label.setText("Sparky is typing...")
        self.typing_label.show()
        
        # Reset streaming state
        self._streaming_started = False
        self._streaming_displayed = False
        
        # Queue message for sending
        self.send_queue.put(("text_chat", text))
    
    def _on_message_received(self, msg_type: str, content: str, streaming_started: bool):
        """Handle message received from WebSocket (runs in GUI thread)
        
        V5.0.1 FIX: Buffers first few tokens to eliminate stutter.
        Previously showed partial first token ("W ") then replaced with full text.
        Now waits until we have >3 characters before displaying anything.
        """
        if msg_type == "token":
            # Streaming token
            if not streaming_started or not self._streaming_started:
                # First token - create message structure but only display if substantial
                ai_msg = ChatMessage("assistant", content)
                self.messages.append(ai_msg)
                self._streaming_started = True
                
                # Only display if we have enough content (>3 chars) to avoid stutter
                if len(content.strip()) > 3:
                    self._display_message("assistant", content)
                    self._streaming_displayed = True
                # Otherwise wait for more tokens before displaying
            else:
                # Subsequent tokens - update message content
                if self.messages:
                    self.messages[-1].content = content
                
                # Display now if we haven't yet and have enough content
                if not self._streaming_displayed and len(content.strip()) > 3:
                    self._display_message("assistant", content)
                    self._streaming_displayed = True
                elif self._streaming_displayed:
                    # Already displaying, just update
                    self._update_streaming_message(content)
        
        elif msg_type == "final":
            # Final complete response
            if self.messages:
                self.messages[-1].content = content
                # Ensure it's displayed even if we never hit the threshold
                if not self._streaming_displayed:
                    self._display_message("assistant", content)
                else:
                    self._update_streaming_message(content)
            else:
                # Fallback if no streaming
                ai_msg = ChatMessage("assistant", content)
                self.messages.append(ai_msg)
                self._display_message("assistant", content)
            
            # Hide typing indicator and reset state
            self.typing_label.hide()
            self._streaming_started = False
            self._streaming_displayed = False
        
        elif msg_type == "error":
            QMessageBox.critical(self, "Error", f"Server error:\n{content}")
            self.typing_label.hide()
    
    def _on_connection_status(self, connected: bool, message: str):
        """Handle connection status changes"""
        if not connected:
            QMessageBox.warning(self, "Connection Lost", message)
    
    def _on_session_id_received(self, session_id: str):
        """Handle session ID received"""
        self._update_mode_indicator()
    
    def _connect_websocket(self):
        """Open persistent WebSocket connection"""
        if self.ws_worker and self.ws_worker.ws_connected:
            return
        
        print("🔗 Opening persistent text chat WebSocket...")
        
        # Create worker and thread
        self.ws_worker = WebSocketWorker(self.assistant, self.send_queue)
        self.ws_thread = QThread()
        
        # Move worker to thread
        self.ws_worker.moveToThread(self.ws_thread)
        
        # Connect signals
        self.ws_thread.started.connect(self.ws_worker.run)
        self.ws_worker.message_received.connect(self._on_message_received)
        self.ws_worker.connection_status.connect(self._on_connection_status)
        self.ws_worker.session_id_received.connect(self._on_session_id_received)
        
        # Start thread
        self.ws_thread.start()
    
    def _disconnect_websocket(self):
        """Close persistent WebSocket connection"""
        if not self.ws_worker:
            return
        
        print("🔌 Closing text chat WebSocket...")
        
        self.ws_worker.stop()
        
        if self.ws_thread:
            self.ws_thread.quit()
            self.ws_thread.wait(2000)
    
    def toggle_visibility(self):
        """Toggle window visibility"""
        if self.isVisible():
            self.hide()
            self.is_visible = False
            self._disconnect_websocket()
        else:
            self.show()
            self.is_visible = True
            self.raise_()
            self.activateWindow()
            # Set focus to input field so user can type immediately
            self.input_text.setFocus()
            self._connect_websocket()
    
    def start_new_chat(self):
        """Start a new conversation"""
        if self.messages:
            reply = QMessageBox.question(
                self, "New Chat",
                "Start a new conversation?\nThis will clear the current chat history.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.messages.clear()
                self.chat_text.clear()
                
                # Clear orchestrator session
                self.assistant.session_id = None
                self.assistant.conversation_active = False
                self._update_mode_indicator()
                print("🆕 New chat started")
        else:
            # No messages yet
            self.assistant.session_id = None
            self.assistant.conversation_active = False
            self._update_mode_indicator()
    
    def clear_conversation(self):
        """Clear all messages"""
        if not self.messages:
            QMessageBox.information(self, "Nothing to Clear", "Chat is already empty.")
            return
        
        reply = QMessageBox.question(
            self, "Clear Chat",
            "Clear all messages?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.messages.clear()
            self.chat_text.clear()
            
            # Clear orchestrator history
            self.assistant.session_id = None
            self.assistant.conversation_active = False
            self._update_mode_indicator()
            print("🗑️ Chat cleared")
    
    def export_chat(self):
        """Export chat to file"""
        if not self.messages:
            QMessageBox.information(self, "Nothing to Export", "No messages to export.")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Chat",
            "",
            "Text files (*.txt);;Markdown files (*.md);;All files (*.*)"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"Sparky Chat Export - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 60 + "\n\n")
                    
                    for msg in self.messages:
                        role_name = "You" if msg.role == "user" else "Sparky"
                        f.write(f"[{msg.timestamp.strftime('%H:%M:%S')}] {role_name}:\n")
                        f.write(f"{msg.content}\n\n")
                
                QMessageBox.information(self, "Export Successful", f"Chat exported to:\n{filename}")
                print(f"💾 Chat exported to: {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", f"Failed to export chat:\n{e}")
    
    def closeEvent(self, event):
        """Handle window close event"""
        self.is_visible = False
        self._disconnect_websocket()
        event.ignore()  # Don't destroy window, just hide it
        self.hide()


class SparkyVoiceAssistant:
    """Main voice assistant engine with DUAL-STREAM architecture
    
    NO CHANGES FROM ORIGINAL - All audio/voice functionality identical
    """
    
    def __init__(self):
        self.state = VoiceState.IDLE
        self.input_mode = InputMode.VAD
        self.audio_queue = queue.Queue()
        self.running = False
        self.stream = None
        self.conversation_active = False
        
        # Command recording
        self.command_audio_buffer = []
        self.silence_chunks = 0
        self.recording_command = False
        self.is_speaking = False
        
        # Calibration
        self.silence_threshold = BASE_SILENCE_THRESHOLD
        self.calibrated = False
        self.calibration_samples = []
        
        # Emergency abort system
        self.abort_tts = False
        self.abort_reason = None
        self.abort_lock = threading.Lock()
        
        # Echo cancellation buffers
        self.tts_playback_buffer = deque(maxlen=ECHO_BUFFER_SIZE)
        self.echo_cancel_lock = threading.Lock()
        
        # DUAL-STREAM ARCHITECTURE
        self.exit_audio_queue = queue.Queue()
        self.exit_stream = None
        self.exit_stream_running = False
        self.exit_detection_thread = None
        
        # Initialize wake word models
        self.wake_model = None
        self.exit_model = None
        self.load_wake_models()
        
        # Server-side session management
        self.session_id = None
        self.output_stream = None
        
        # Start keyboard listener
        self.keyboard_listener = keyboard.Listener(on_press=self._on_key_press, daemon=True)
        self.keyboard_listener.start()
    
    def _on_key_press(self, key):
        """Handle keyboard events"""
        try:
            if key == ABORT_HOTKEY and self.conversation_active:
                print(f"\n⌨️ Hotkey abort triggered ({ABORT_HOTKEY.name.upper()})")
                self._emergency_abort()
        except AttributeError:
            pass
    
    def load_wake_models(self):
        """Load wake word models"""
        try:
            custom_wake = WAKE_MODELS_DIR / "hey_sparky.tflite"
            custom_exit = WAKE_MODELS_DIR / "bye_sparky.tflite"
            
            if custom_wake.exists() and custom_exit.exists():
                print("Loading custom Sparky wake words...")
                self.wake_model = Model(wakeword_models=[str(custom_wake)])
                self.exit_model = Model(wakeword_models=[str(custom_exit)])
                self.wake_word_name = "Hey Sparky"
                self.exit_word_name = "Bye Sparky"
            else:
                print("Loading built-in wake words (Hey Jarvis / Hey Mycroft)...")
                openwakeword.utils.download_models()
                
                self.wake_model = Model(wakeword_models=["hey_jarvis"])
                self.exit_model = Model(wakeword_models=["hey_mycroft"])
                self.wake_word_name = "Hey Jarvis"
                self.exit_word_name = "Hey Mycroft"
            
            print(f"✓ Wake word: '{self.wake_word_name}'")
            print(f"✓ Exit word: '{self.exit_word_name}'")
        
        except Exception as e:
            print(f"⚠️ Error loading wake models: {e}")
            print("   Wake words will not be available")
            self.wake_model = None
            self.exit_model = None
            self.wake_word_name = "N/A"
            self.exit_word_name = "N/A"
    
    def audio_callback(self, indata, frames, time, status):
        """Callback for PRIMARY audio stream"""
        if status:
            print(f"Audio status: {status}")
        if self.running:
            self.audio_queue.put(indata.copy())
    
    def exit_audio_callback(self, indata, frames, time, status):
        """Callback for SECONDARY audio stream"""
        if status and DEBUG_WAKEWORD:
            print(f"Exit stream audio status: {status}")
        if self.exit_stream_running:
            self.exit_audio_queue.put(indata.copy())
    
    def calibrate_microphone(self):
        """Calibrate microphone to detect ambient noise level"""
        if not AUTO_CALIBRATE:
            print("📊 Auto-calibration disabled, using configured threshold")
            self.silence_threshold = BASE_SILENCE_THRESHOLD
            self.calibrated = True
            return
        
        print("🎤 Calibrating microphone...")
        print(f"   Please remain quiet for {CALIBRATION_DURATION:.1f} seconds...")
        
        self.state = VoiceState.CALIBRATING
        self.calibration_samples = []
        calibration_start = time.time()
        
        while time.time() - calibration_start < CALIBRATION_DURATION:
            try:
                audio_chunk = self.audio_queue.get(timeout=0.1)
                audio_data = audio_chunk.flatten()
                amplitude = np.max(np.abs(audio_data))
                self.calibration_samples.append(amplitude)
            except queue.Empty:
                continue
        
        if self.calibration_samples:
            ambient_noise = np.percentile(self.calibration_samples, 95)
            self.silence_threshold = ambient_noise * 3.5
            self.silence_threshold = max(self.silence_threshold, 0.015)
            self.silence_threshold = min(self.silence_threshold, 0.15)
            self.calibrated = True
            
            print(f"   Ambient noise level: {ambient_noise:.4f}")
            print(f"   Silence threshold set to: {self.silence_threshold:.4f}")
            print("✓ Calibration complete")
        else:
            print("⚠️ Calibration failed, using default threshold")
            self.silence_threshold = BASE_SILENCE_THRESHOLD
            self.calibrated = True
    
    def _clear_audio_queue(self):
        """Clear the audio queue"""
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break
    
    def start_listening(self):
        """Start listening for wake word"""
        if self.running:
            print("Already listening")
            return
        
        print("🎤 Starting audio stream...")
        
        self.stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype='float32',
            callback=self.audio_callback,
            blocksize=int(SAMPLE_RATE * 0.08)
        )
        self.stream.start()
        self.running = True
        
        self.calibrate_microphone()
        
        if self.input_mode == InputMode.VAD:
            self.state = VoiceState.LISTENING_FOR_WAKE
            print(f"👂 Listening for '{self.wake_word_name}'...")
        else:
            self.state = VoiceState.IDLE
            print("💤 Manual mode - use menu to start conversation")
        
        threading.Thread(target=self._detection_loop, daemon=True).start()
    
    def stop_listening(self):
        """Stop listening"""
        if not self.running:
            return
        
        print("🛑 Stopping audio stream...")
        self.running = False
        
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        
        self.stop_exit_stream()
        self.state = VoiceState.IDLE
    
    def start_exit_stream(self):
        """Start exit word detection stream"""
        if self.exit_stream_running:
            return
        
        print("🎤 Starting exit word detection stream...")
        
        self.exit_stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype='float32',
            callback=self.exit_audio_callback,
            blocksize=int(SAMPLE_RATE * 0.08)
        )
        self.exit_stream.start()
        self.exit_stream_running = True
        
        self.exit_detection_thread = threading.Thread(
            target=self._exit_detection_loop,
            daemon=True
        )
        self.exit_detection_thread.start()
    
    def stop_exit_stream(self):
        """Stop exit word detection stream"""
        if not self.exit_stream_running:
            return
        
        print("🛑 Stopping exit word detection...")
        self.exit_stream_running = False
        
        if self.exit_stream:
            self.exit_stream.stop()
            self.exit_stream.close()
            self.exit_stream = None
        
        while not self.exit_audio_queue.empty():
            try:
                self.exit_audio_queue.get_nowait()
            except queue.Empty:
                break
    
    def _exit_detection_loop(self):
        """Exit word detection loop"""
        print("👂 Exit detection active...")
        
        while self.exit_stream_running and self.conversation_active:
            try:
                audio_chunk = self.exit_audio_queue.get(timeout=0.1)
                
                if self.exit_model and not self.is_speaking:
                    audio_int16 = (audio_chunk.flatten() * 32767).astype(np.int16)
                    prediction = self.exit_model.predict(audio_int16)
                    
                    for mdl_name, score in prediction.items():
                        if DEBUG_WAKEWORD and score > 0.1:
                            print(f"🚪 {mdl_name}: {score:.3f}")
                        
                        if score > 0.5:
                            print(f"\n🚪 Exit word detected! ({score:.2f})")
                            self._emergency_abort()
                            return
            
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error in exit detection: {e}")
    
    def _detection_loop(self):
        """Main detection loop"""
        wake_check_counter = 0
        
        while self.running:
            try:
                audio_chunk = self.audio_queue.get(timeout=0.1)
                
                if audio_chunk is not None:
                    cleaned_audio = audio_chunk.flatten()
                    
                    # Echo cancellation
                    if ECHO_CANCEL_ENABLED and self.is_speaking:
                        with self.echo_cancel_lock:
                            if self.tts_playback_buffer:
                                avg_echo = np.mean([buf[:len(cleaned_audio)] for buf in self.tts_playback_buffer if len(buf) >= len(cleaned_audio)], axis=0)
                                cleaned_audio = cleaned_audio - avg_echo
                    
                    # Wake word detection
                    if self.state == VoiceState.LISTENING_FOR_WAKE and self.wake_model and not self.is_speaking:
                        audio_int16 = (cleaned_audio * 32767).astype(np.int16)
                        prediction = self.wake_model.predict(audio_int16)
                        
                        wake_check_counter += 1
                        if DEBUG_WAKEWORD and wake_check_counter % 10 == 0:
                            print(f"🎯 Wake check: {prediction}")
                        
                        for mdl_name, score in prediction.items():
                            if score > 0.5:
                                print(f"\n🎯 Wake word detected! ({score:.2f})")
                                self._activate_conversation()
                                break
                    
                    # Recording logic
                    if self.conversation_active and self.state in [VoiceState.ACTIVE_CONVERSATION, VoiceState.RECORDING_COMMAND]:
                        if not self.is_speaking:
                            self._handle_recording(cleaned_audio)
            
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error in detection loop: {e}")
                import traceback
                traceback.print_exc()
    
    def _handle_recording(self, audio_data):
        """Handle command recording with silence detection"""
        amplitude = np.max(np.abs(audio_data))
        
        if DEBUG_AUDIO:
            print(f"Amplitude: {amplitude:.4f} | Threshold: {self.silence_threshold:.4f}")
        
        if amplitude > self.silence_threshold:
            if not self.recording_command:
                self.recording_command = True
                self.state = VoiceState.RECORDING_COMMAND
                self.command_audio_buffer = []
                self.silence_chunks = 0
                print("🔴 Recording...")
            
            self.command_audio_buffer.append(audio_data)
            self.silence_chunks = 0
        else:
            if self.recording_command:
                self.silence_chunks += 1
                self.command_audio_buffer.append(audio_data)
                
                silence_duration = (self.silence_chunks * 0.08)
                
                if silence_duration >= SILENCE_DURATION:
                    self.recording_command = False
                    print("⏸️ Silence detected, processing...")
                    
                    command_audio = self.command_audio_buffer.copy()
                    self.command_audio_buffer = []
                    self.silence_chunks = 0
                    
                    threading.Thread(
                        target=self._process_command,
                        args=(command_audio,),
                        daemon=True
                    ).start()
    
    def _process_command(self, audio_chunks):
        """Process recorded command using orchestrator WebSocket"""
        threading.Thread(
            target=self._run_async_orchestrator,
            args=(audio_chunks,),
            daemon=True
        ).start()
    
    def _run_async_orchestrator(self, audio_chunks):
        """Run async orchestrator call from sync thread"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._process_command_orchestrator(audio_chunks))
        finally:
            loop.close()
    
    async def _process_command_orchestrator(self, audio_chunks):
        """Process command using orchestrator WebSocket"""
        try:
            self.state = VoiceState.PROCESSING
            
            # Validate recording length
            full_audio = np.concatenate(audio_chunks)
            if len(full_audio) < SAMPLE_RATE * 0.5:
                print("⚠️ Recording too short, ignored")
                self.state = VoiceState.ACTIVE_CONVERSATION
                return
            
            print("🔗 Connecting to orchestrator...")
            
            async with websockets.connect(ORCH_WS_URL, max_size=None) as ws:
                # Send START
                start_msg = {
                    "type": "start",
                    "voice": DEFAULT_VOICE
                }
                if self.session_id:
                    start_msg["session_id"] = self.session_id
                
                await ws.send(json.dumps(start_msg))
                
                # Send audio
                print("📤 Sending audio...")
                audio_bytes = (full_audio * 32767).astype(np.int16).tobytes()
                
                chunk_size = 4096
                for i in range(0, len(audio_bytes), chunk_size):
                    chunk = audio_bytes[i:i+chunk_size]
                    encoded = base64.b64encode(chunk).decode('utf-8')
                    await ws.send(json.dumps({
                        "type": "audio",
                        "data": encoded
                    }))
                
                # Send FINAL
                await ws.send(json.dumps({"type": "final"}))
                
                # Prepare audio output
                if not self.output_stream or not self.output_stream.active:
                    self.output_stream = sd.OutputStream(
                        samplerate=TTS_SAMPLE_RATE,
                        channels=TTS_CHANNELS,
                        dtype='int16'
                    )
                    self.output_stream.start()
                
                self.is_speaking = False
                first_audio = True
                
                # Receive responses
                while True:
                    if self.abort_tts:
                        print("🛑 Conversation aborted")
                        break
                    
                    msg = await ws.recv()
                    
                    if isinstance(msg, (bytes, bytearray)):
                        # Binary audio data
                        if first_audio:
                            print("🔊 Streaming audio...")
                            self.is_speaking = True
                            self.state = VoiceState.SPEAKING
                            first_audio = False
                        
                        audio_data = np.frombuffer(msg, dtype=np.int16)
                        
                        # Echo cancellation buffer
                        if ECHO_CANCEL_ENABLED:
                            if TTS_SAMPLE_RATE != SAMPLE_RATE:
                                ratio = TTS_SAMPLE_RATE / SAMPLE_RATE
                                indices = np.arange(0, len(audio_data), ratio).astype(int)
                                resampled = audio_data[indices]
                            else:
                                resampled = audio_data
                            
                            normalized = resampled.astype(np.float32) / 32767.0
                            
                            with self.echo_cancel_lock:
                                self.tts_playback_buffer.append(normalized)
                        
                        if not self.abort_tts:
                            self.output_stream.write(audio_data)
                    
                    else:
                        # JSON metadata
                        try:
                            obj = json.loads(msg)
                            event = obj.get("event")
                            msg_type = obj.get("type")
                            
                            if event == "session_id":
                                self.session_id = obj.get("value")
                            
                            elif event == "transcription":
                                print(f"📝 You said: {obj.get('text')}")
                            
                            elif event == "thinking":
                                print("🤔 Thinking...")
                            
                            elif event == "llm_response":
                                print(f"💭 Ara responds...")
                            
                            elif event == "provider":
                                provider = obj.get("value", "unknown").upper()
                                print(f"🎤 TTS Provider: {provider}")
                            
                            elif msg_type == "done":
                                break
                            
                            elif msg_type == "error":
                                print(f"❌ Orchestrator error: {obj.get('detail')}")
                                break
                        
                        except json.JSONDecodeError:
                            pass
                
                # Clean up
                self.is_speaking = False
                with self.echo_cancel_lock:
                    self.tts_playback_buffer.clear()
                
                self.state = VoiceState.ACTIVE_CONVERSATION
        
        except Exception as e:
            print(f"❌ Error in orchestrator conversation: {e}")
            import traceback
            traceback.print_exc()
            self.state = VoiceState.ACTIVE_CONVERSATION
            self.is_speaking = False
    
    def _play_greeting_or_goodbye_via_orchestrator(self, message_type):
        """Play greeting or goodbye through orchestrator"""
        threading.Thread(
            target=self._run_async_greeting_goodbye,
            args=(message_type,),
            daemon=True
        ).start()
    
    def _run_async_greeting_goodbye(self, message_type):
        """Run async greeting/goodbye call"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._play_simple_tts(message_type))
        finally:
            loop.close()
    
    async def _play_simple_tts(self, message_type):
        """Send greeting or goodbye to orchestrator and play audio"""
        try:
            print(f"🔗 Playing {message_type} via orchestrator...")
            
            async with websockets.connect(ORCH_WS_URL, max_size=None) as ws:
                # Send START
                await ws.send(json.dumps({
                    "type": "start",
                    "voice": DEFAULT_VOICE,
                    "session_id": self.session_id
                }))
                
                # Send greeting or goodbye
                await ws.send(json.dumps({"type": message_type}))
                
                # Prepare audio output
                if not self.output_stream or not self.output_stream.active:
                    self.output_stream = sd.OutputStream(
                        samplerate=TTS_SAMPLE_RATE,
                        channels=TTS_CHANNELS,
                        dtype='int16'
                    )
                    self.output_stream.start()
                
                self.is_speaking = True
                first_audio = True
                
                # Receive and play audio
                while True:
                    if self.abort_tts:
                        break
                    
                    msg = await ws.recv()
                    
                    if isinstance(msg, (bytes, bytearray)):
                        if first_audio:
                            print(f"🔊 Playing {message_type}...")
                            first_audio = False
                        
                        audio_data = np.frombuffer(msg, dtype=np.int16)
                        
                        # Echo cancellation buffer
                        if ECHO_CANCEL_ENABLED:
                            if TTS_SAMPLE_RATE != SAMPLE_RATE:
                                ratio = TTS_SAMPLE_RATE / SAMPLE_RATE
                                indices = np.arange(0, len(audio_data), ratio).astype(int)
                                resampled = audio_data[indices]
                            else:
                                resampled = audio_data
                            
                            normalized = resampled.astype(np.float32) / 32767.0
                            
                            with self.echo_cancel_lock:
                                self.tts_playback_buffer.append(normalized)
                        
                        if not self.abort_tts:
                            self.output_stream.write(audio_data)
                    
                    else:
                        try:
                            obj = json.loads(msg)
                            if obj.get("event") == "session_id":
                                self.session_id = obj.get("value")
                            elif obj.get("type") == "done":
                                break
                        except json.JSONDecodeError:
                            pass
                
                self.is_speaking = False
                print(f"✓ {message_type.capitalize()} complete")
        
        except Exception as e:
            print(f"❌ Error playing {message_type}: {e}")
            import traceback
            traceback.print_exc()
            self.is_speaking = False
    
    def _activate_conversation(self):
        """Activate conversation mode"""
        self.state = VoiceState.ACTIVE_CONVERSATION
        self.conversation_active = True
        self.command_audio_buffer = []
        self.silence_chunks = 0
        self.recording_command = False
        
        self._clear_audio_queue()
        
        mode = "VAD - just speak" if self.input_mode == InputMode.VAD else "Manual"
        print(f"💬 Conversation active! ({mode})")
        
        if self.input_mode == InputMode.VAD:
            print(f"   Say '{self.exit_word_name}' or press {ABORT_HOTKEY.name.upper()} to exit")
        
        # Play greeting
        self._play_greeting_or_goodbye_via_orchestrator("greeting")
        
        # Start exit detection
        if self.input_mode == InputMode.VAD:
            print("⏳ Waiting for greeting to start...")
            time.sleep(0.5)
            self._clear_audio_queue()
            print("🎯 Starting exit detection now...")
            self.start_exit_stream()
    
    def _emergency_abort(self):
        """Emergency abort with instant goodbye"""
        with self.abort_lock:
            if not self.conversation_active:
                return
            
            # Mark aborting
            self.conversation_active = False
            self.abort_tts = True
            
            # Stop exit detection immediately
            self.stop_exit_stream()
            
            # Stop current audio
            if self.output_stream and self.output_stream.active:
                try:
                    self.output_stream.stop()
                    self.output_stream = None
                except Exception as e:
                    print(f"⚠️ Error stopping output: {e}")
            
            # Clear echo buffer
            with self.echo_cancel_lock:
                self.tts_playback_buffer.clear()
            
            print("\n👋 Playing goodbye...")
            
            # Play goodbye BEFORE cleanup
            self._play_greeting_or_goodbye_via_orchestrator("goodbye")
            
            # Wait for goodbye + audio buffer
            print(f"⏳ Waiting {AUDIO_BUFFER_DURATION + 1:.1f}s for audio to clear...")
            time.sleep(AUDIO_BUFFER_DURATION + 1.0)
            
            # Now cleanup
            self.abort_tts = False
            self._clear_audio_queue()
            
            self.command_audio_buffer = []
            self.silence_chunks = 0
            self.recording_command = False
            self.is_speaking = False
            
            # Return to appropriate state
            if self.input_mode == InputMode.VAD:
                self.state = VoiceState.LISTENING_FOR_WAKE
                print(f"👂 Listening for '{self.wake_word_name}'...")
            else:
                self.state = VoiceState.IDLE
                print("💤 Idle")
            
            print("✓ Abort complete")
    
    def toggle_input_mode(self):
        """Toggle between VAD and Manual mode"""
        if self.input_mode == InputMode.VAD:
            self.input_mode = InputMode.MANUAL
            if not self.conversation_active:
                self.state = VoiceState.IDLE
            print("✓ Switched to Manual mode")
        else:
            self.input_mode = InputMode.VAD
            if not self.conversation_active:
                self.state = VoiceState.LISTENING_FOR_WAKE
                print(f"✓ Switched to VAD mode - listening for '{self.wake_word_name}'")
            else:
                print("✓ Switched to VAD mode")
        
        return "VAD" if self.input_mode == InputMode.VAD else "Manual"
    
    def manual_start_conversation(self):
        """Start conversation (Manual mode)"""
        if self.input_mode != InputMode.MANUAL:
            print("⚠️ Not in Manual mode")
            return False
        
        if self.conversation_active:
            print("⚠️ Conversation already active")
            return False
        
        self._activate_conversation()
        return True
    
    def manual_stop_conversation(self):
        """Stop conversation (Manual mode)"""
        if self.input_mode != InputMode.MANUAL:
            print("⚠️ Not in Manual mode")
            return False
        
        if not self.conversation_active:
            print("⚠️ No active conversation")
            return False
        
        self._emergency_abort()
        return True
    
    def recalibrate(self):
        """Manually trigger recalibration"""
        if self.running:
            print("\n🔄 Recalibrating microphone...")
            self.calibrate_microphone()
            
            if self.input_mode == InputMode.VAD:
                if self.conversation_active:
                    self.state = VoiceState.ACTIVE_CONVERSATION
                else:
                    self.state = VoiceState.LISTENING_FOR_WAKE
            else:
                if self.conversation_active:
                    self.state = VoiceState.ACTIVE_CONVERSATION
                else:
                    self.state = VoiceState.IDLE
    
    def get_state_description(self):
        """Get human-readable state description"""
        if self.state == VoiceState.IDLE:
            return "Idle"
        elif self.state == VoiceState.CALIBRATING:
            return "Calibrating..."
        elif self.state == VoiceState.LISTENING_FOR_WAKE:
            return f"Listening for '{self.wake_word_name}'"
        elif self.state == VoiceState.ACTIVE_CONVERSATION:
            return "In conversation"
        elif self.state == VoiceState.RECORDING_COMMAND:
            return "Recording..."
        elif self.state == VoiceState.PROCESSING:
            return "Processing..."
        elif self.state == VoiceState.SPEAKING:
            return "Speaking..."
        return "Unknown"
    
    def cleanup(self):
        """Cleanup resources"""
        if self.exit_stream_running:
            self.stop_exit_stream()
        
        if self.keyboard_listener:
            self.keyboard_listener.stop()


class SparkyTrayApp(QObject):
    """System tray application - HYBRID: pystray + PyQt6 chat window"""
    
    # Signals for thread-safe operations
    toggle_chat_signal = pyqtSignal()
    quit_signal = pyqtSignal()  # Thread-safe quit
    
    def __init__(self):
        super().__init__()  # Initialize QObject
        self.assistant = SparkyVoiceAssistant()
        self.icon = None
        self.auto_start_enabled = self._check_auto_start()
        
        # Create QApplication (required for PyQt6)
        self.qt_app = QApplication(sys.argv)
        
        # Create PyQt6 chat window
        self.chat_window = ChatWindow(self, self.assistant)
        
        # Connect signals (run in Qt main thread)
        self.toggle_chat_signal.connect(self.chat_window.toggle_visibility)
        self.quit_signal.connect(self._do_quit)
    
    def _check_auto_start(self):
        """Check if auto-start is enabled"""
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_READ
            )
            try:
                winreg.QueryValueEx(key, "SparkyVoiceAI")
                winreg.CloseKey(key)
                return True
            except FileNotFoundError:
                winreg.CloseKey(key)
                return False
        except Exception:
            return False
    
    def _toggle_auto_start(self):
        """Toggle Windows auto-start"""
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE | winreg.KEY_READ
            )
            
            if self.auto_start_enabled:
                try:
                    winreg.DeleteValue(key, "SparkyVoiceAI")
                    self.auto_start_enabled = False
                    print("✓ Auto-start disabled")
                except FileNotFoundError:
                    pass
            else:
                script_path = str(Path(__file__).absolute())
                python_path = sys.executable
                command = f'"{python_path}" "{script_path}"'
                winreg.SetValueEx(key, "SparkyVoiceAI", 0, winreg.REG_SZ, command)
                self.auto_start_enabled = True
                print("✓ Auto-start enabled")
            
            winreg.CloseKey(key)
        
        except Exception as e:
            print(f"Error toggling auto-start: {e}")
    
    def create_icon_image(self, color="green"):
        """Create icon image"""
        image = Image.new('RGB', (64, 64), color='white')
        draw = ImageDraw.Draw(image)
        
        colors = {
            "green": "#4CAF50",
            "red": "#E53935",
            "blue": "#2196F3",
            "orange": "#FF9800",
            "gray": "#9E9E9E"
        }
        
        circle_color = colors.get(color, colors["green"])
        draw.ellipse([4, 4, 60, 60], fill=circle_color)
        
        # Microphone icon
        draw.rectangle([26, 20, 38, 35], fill='white')
        draw.ellipse([28, 35, 36, 43], outline='white', width=2)
        draw.line([32, 43, 32, 48], fill='white', width=2)
        draw.line([26, 48, 38, 48], fill='white', width=2)
        
        return image
    
    def get_menu(self):
        """Create system tray menu"""
        state_text = self.assistant.get_state_description()
        input_mode = "VAD" if self.assistant.input_mode == InputMode.VAD else "Manual"
        is_manual = self.assistant.input_mode == InputMode.MANUAL
        in_conversation = self.assistant.conversation_active
        
        return Menu(
            MenuItem(f"Status: {state_text}", lambda: None, enabled=False),
            MenuItem(f"Mode: {input_mode}", lambda: None, enabled=False),
            Menu.SEPARATOR,
            MenuItem(
                "Enable Microphone" if not self.assistant.running else "Disable Microphone",
                self.toggle_listening
            ),
            MenuItem("Recalibrate Microphone", self.recalibrate_mic, enabled=self.assistant.running),
            MenuItem("Toggle Input Mode", self.toggle_input_mode),
            Menu.SEPARATOR,
            MenuItem(
                "▶ Start Conversation",
                self.start_conversation,
                enabled=(is_manual and not in_conversation)
            ),
            MenuItem(
                "■ Stop Conversation",
                self.stop_conversation,
                enabled=(is_manual and in_conversation)
            ),
            Menu.SEPARATOR,
            MenuItem(
                f"{'✓' if self.chat_window.is_visible else '  '} 💬 Open Text Chat",
                self.toggle_chat_window
            ),
            Menu.SEPARATOR,
            MenuItem(
                f"Wake: {self.assistant.wake_word_name}",
                lambda: None,
                enabled=False
            ),
            MenuItem(
                f"Exit: {self.assistant.exit_word_name} / ESC key",
                lambda: None,
                enabled=False
            ),
            Menu.SEPARATOR,
            MenuItem("Train Custom Wake Words...", self.open_training),
            MenuItem("Reload Wake Words", self.reload_wake_words),
            Menu.SEPARATOR,
            MenuItem(
                f"{'✓' if self.auto_start_enabled else '  '} Start with Windows",
                self.toggle_auto_start
            ),
            Menu.SEPARATOR,
            MenuItem("About Sparky", self.show_about),
            MenuItem("Quit", self.quit_app)
        )
    
    def toggle_listening(self, icon=None, item=None):
        """Toggle listening"""
        if self.assistant.running:
            self.assistant.stop_listening()
            self.update_icon("gray")
        else:
            self.assistant.start_listening()
            self.update_icon("green")
        
        if self.icon:
            self.icon.menu = self.get_menu()
    
    def recalibrate_mic(self, icon=None, item=None):
        """Recalibrate microphone"""
        self.assistant.recalibrate()
    
    def toggle_input_mode(self, icon=None, item=None):
        """Toggle input mode"""
        mode = self.assistant.toggle_input_mode()
        if self.icon:
            self.icon.menu = self.get_menu()
        print(f"✓ Switched to {mode}")
    
    def start_conversation(self, icon=None, item=None):
        """Start conversation (Manual mode)"""
        if self.assistant.manual_start_conversation():
            self.update_icon("red")
            if self.icon:
                self.icon.menu = self.get_menu()
    
    def stop_conversation(self, icon=None, item=None):
        """Stop conversation (Manual mode)"""
        if self.assistant.manual_stop_conversation():
            self.update_icon("green")
            if self.icon:
                self.icon.menu = self.get_menu()
    
    def toggle_chat_window(self, icon=None, item=None):
        """Toggle text chat window - thread-safe via signal"""
        # Emit signal (Qt queues it to main thread automatically)
        self.toggle_chat_signal.emit()
        
        # Update menu after brief delay to let Qt process the signal
        if self.icon:
            def update_menu():
                if self.icon:
                    self.icon.menu = self.get_menu()
            QTimer.singleShot(100, update_menu)
    
    def toggle_auto_start(self, icon=None, item=None):
        """Toggle auto-start"""
        self._toggle_auto_start()
        if self.icon:
            self.icon.menu = self.get_menu()
    
    def reload_wake_words(self, icon=None, item=None):
        """Reload wake word models"""
        print("Reloading wake word models...")
        was_running = self.assistant.running
        
        if was_running:
            self.assistant.stop_listening()
        
        self.assistant.load_wake_models()
        
        if was_running:
            self.assistant.start_listening()
        
        if self.icon:
            self.icon.menu = self.get_menu()
        
        print("✓ Wake words reloaded")
    
    def open_training(self, icon=None, item=None):
        """Open wake word training info"""
        print("\n" + "="*60)
        print("WAKE WORD TRAINING")
        print("="*60)
        print("\nUse the Google Colab notebook:")
        print("https://colab.research.google.com/drive/1q1oe2zOyZp7UsB3jJiQ1IFn8z5YfjwEb")
        print("\nTrain two models:")
        print("  - 'hey sparky' → hey_sparky.tflite")
        print("  - 'bye sparky' → bye_sparky.tflite")
        print(f"\nPlace in: {WAKE_MODELS_DIR}")
        print("Then: Reload Wake Words from menu")
        print("="*60 + "\n")
    
    def show_about(self, icon=None, item=None):
        """Show about info"""
        print("\n" + "="*60)
        print(f"SPARKY VOICE AI - PyQt6 Edition v{VERSION}")
        print("="*60)
        print("\nLocal-only voice assistant with TRUE STREAMING")
        print("No cloud • No accounts • No expiration")
        print("\nComponents:")
        print("  • openWakeWord - Wake word detection")
        print("  • faster-whisper - Speech-to-text")
        print("  • Coqui XTTS - Text-to-speech (STREAMING)")
        print("  • vLLM - LLM inference")
        print(f"\nOrchestrator: {ORCH_WS_URL}")
        print(f"  Required version: {REQUIRED_ORCHESTRATOR_VERSION}+")
        print(f"TTS Server: {TTS_URL}")
        print(f"Whisper Server: {WHISPER_URL}")
        print(f"Voice: {DEFAULT_VOICE}")
        print(f"\nAuto-Calibration: {'Enabled' if AUTO_CALIBRATE else 'Disabled'}")
        if self.assistant.calibrated:
            print(f"Silence Threshold: {self.assistant.silence_threshold:.4f}")
        print(f"Echo Cancellation: {'Enabled' if ECHO_CANCEL_ENABLED else 'Disabled'}")
        print(f"Emergency Abort: Voice + {ABORT_HOTKEY.name.upper()} key")
        print("\nv5.0 PYQT6 CHAT WINDOW:")
        print("  ✓ Native right-click menus (copy, select all)")
        print("  ✓ Perfect text selection")
        print("  ✓ Modern Windows 11 styling")
        print("  ✓ Smooth font rendering")
        print("  ✓ Professional UI")
        print("="*60 + "\n")
    
    def update_icon(self, color):
        """Update icon color"""
        if self.icon:
            self.icon.icon = self.create_icon_image(color)
    
    def quit_app(self, icon=None, item=None):
        """Quit application - thread-safe via signal"""
        print("\n👋 Quit requested...")
        # Emit signal (Qt queues it to main thread automatically)
        self.quit_signal.emit()
    
    def _do_quit(self):
        """Actually quit the application (runs in Qt main thread)"""
        print("   Executing shutdown...")
        
        # Close chat window
        if hasattr(self, 'chat_window') and self.chat_window:
            print("   Closing text chat WebSocket...")
            self.chat_window._disconnect_websocket()
        
        # Stop audio streams
        self.assistant.cleanup()
        self.assistant.stop_listening()
        
        # Stop icon
        if self.icon:
            print("   Stopping tray icon...")
            self.icon.stop()
        
        # Quit PyQt6
        if hasattr(self, 'qt_app'):
            print("   Stopping Qt application...")
            self.qt_app.quit()
        
        print("✅ Shutdown complete")
        sys.exit(0)
    
    def run(self):
        """Run the system tray app"""
        print(f"🚀 Starting Sparky Voice AI v{VERSION} (PyQt6 Edition)...")
        print(f"📂 Models: {WAKE_MODELS_DIR}")
        print(f"🛑 Exit: Voice word OR {ABORT_HOTKEY.name.upper()} key")
        print(f"🔇 Echo cancellation: {'Enabled' if ECHO_CANCEL_ENABLED else 'Disabled'}")
        print(f"⏳ Audio buffer: {AUDIO_BUFFER_DURATION}s + 1s wait")
        
        print(f"\n🔗 v5.0 PYQT6 TEXT CHAT + ORCHESTRATOR:")
        print(f"   ✓ Professional PyQt6 chat window")
        print(f"   ✓ Native right-click menus")
        print(f"   ✓ Perfect text selection")
        print(f"   ✓ Server-side conversation management")
        print(f"   ✓ Connected to: {ORCH_WS_URL}")
        
        self.assistant.start_listening()
        
        self.icon = Icon(
            "SparkyVoiceAI",
            self.create_icon_image("green"),
            "Sparky Voice AI",
            self.get_menu()
        )
        
        # Run tray icon in daemon thread
        icon_thread = threading.Thread(target=self.icon.run, daemon=True)
        icon_thread.start()
        
        # Run Qt event loop in main thread
        try:
            sys.exit(self.qt_app.exec())
        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")
            self.quit_app()


def main():
    """Main entry point"""
    print(f"""
╔══════════════════════════════════════════════════════════╗
║     SPARKY VOICE AI - PYQT6 EDITION v{VERSION}            ║
║                                                          ║
║        PROFESSIONAL CHAT WINDOW - NATIVE UI  🎨💬       ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    app = SparkyTrayApp()
    app.run()


if __name__ == "__main__":
    main()

