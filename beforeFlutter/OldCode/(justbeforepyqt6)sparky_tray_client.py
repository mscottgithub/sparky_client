#!/usr/bin/env python3
"""
Sparky Voice-AI System Tray Client v4.3.6
Always-listening voice assistant with wake word detection
No cloud dependencies - fully local operation
TRUE STREAMING: Plays audio as it arrives for sub-second latency
AUTO-CALIBRATION: Automatically adjusts to any microphone's noise floor
DUAL-STREAM ARCHITECTURE: Dedicated exit word detection for instant response
ECHO CANCELLATION: Subtracts AI voice from microphone to enable mid-speech interruption
V3.4 INSTANT GOODBYE: Exit word triggers immediate goodbye, cleanup happens after
V3.5 MODEL RELOAD: Re-adds wake word model shutdown/reload for clean slate
V3.6.1 PROVIDER DISPLAY: Shows TTS provider (XTTS/Higgs) in streaming output
V4.0.0 ORCHESTRATOR: Uses server-side conversation orchestration via WebSocket
V4.0.1 CLEANUP: Removed orphaned TTS function, fixed About dialog crash
V4.1.0 TEXT CHAT: Added full-featured text chat window with shared conversation history
V4.1.1 BUGFIX: Fixed text chat window not opening (event loop conflict - tray runs in thread, Tk in main)
V4.2.0 TOKEN STREAMING: Real-time token-by-token streaming for instant text responses
V4.3.0 PERSISTENT CONNECTION: Text chat uses persistent WebSocket (mirrors orchestrator architecture)
V4.3.1 BUGFIX: Fixed response handler initialization and task management
V4.3.2 RACE CONDITION FIX: Response handler now uses separate lifecycle flag to prevent premature exit
V4.3.6 UI IMPROVEMENTS: 
  - Light/Dark theme toggle with darker purple scheme (NO WHITE BACKGROUNDS)
  - Main bg: #C4C4D8 (darker purple), AI bubbles: #D4D4E8 (lighter purple)
  - Input box: #E0E0F0 (light purple - NO WHITE)
  - Bolder font for better readability (added "bold" to all fonts)
  - Text selection & copy FULLY FUNCTIONAL (xterm cursor, explicit selection config)
  - Navigation keys allowed (arrows, shift+arrows, home, end)
  - Theme preference saved to config.ini
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
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
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

# WebSocket for orchestrator (v4.0)
try:
    import websockets
except ImportError:
    print("⚠️ Missing 'websockets' - install with: pip install websockets")
    print("   Falling back to direct API calls")
    websockets = None

# Version info
VERSION = "4.3.8"
REQUIRED_ORCHESTRATOR_VERSION = "2.3.0"

# Load configuration with inline comment support
config = configparser.ConfigParser(inline_comment_prefixes=('#', ';'))
config_path = Path(__file__).parent / 'config.ini'
config.read(config_path)

# Voice-AI Service Configuration
SERVER_HOST = config.get('VoiceAI', 'server_host', fallback='10.6.1.15')
TTS_PORT = config.getint('VoiceAI', 'tts_port', fallback=8004)  # TTS Service (Higgs + XTTS)
WHISPER_PORT = config.getint('VoiceAI', 'whisper_port', fallback=8005)  # Whisper Transcription Service
ORCH_PORT = config.getint('VoiceAI', 'orch_port', fallback=8006)  # V4.0: Orchestrator WebSocket
DEFAULT_VOICE = config.get('VoiceAI', 'default_voice', fallback='ara').lower()  # Force lowercase for consistency

# LLM Configuration - REMOVED in v4.0 (orchestrator handles this)

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
AUDIO_BUFFER_DURATION = 4.0  # Seconds to wait after goodbye for audio to clear (increased for echo)
ABORT_HOTKEY = keyboard.Key.esc  # Escape key for instant abort

# Echo Cancellation Configuration
ECHO_BUFFER_SIZE = 100  # Number of audio chunks to buffer for echo cancellation
ECHO_CANCEL_ENABLED = True  # Toggle echo cancellation on/off

# Conversation Configuration
GREETING_MESSAGE = config.get('Conversation', 'greeting', fallback='Yes? How can I help you?')
GOODBYE_MESSAGE = config.get('Conversation', 'goodbye', fallback='Goodbye!')

# Conversation Memory Configuration - REMOVED in v4.0 (orchestrator maintains history server-side)

# TTS Audio Configuration (from server)
TTS_SAMPLE_RATE = 24000
TTS_CHANNELS = 1

# Wake Word Configuration
WAKE_MODELS_DIR = Path(__file__).parent / 'wake_models'
WAKE_MODELS_DIR.mkdir(exist_ok=True)

# Chat Window Configuration (v4.1.0)
ALLOW_DELETE = config.getboolean('ChatWindow', 'allow_delete', fallback=True)
ALLOW_EDIT = config.getboolean('ChatWindow', 'allow_edit', fallback=True)

# Build URLs
TTS_URL = f"http://{SERVER_HOST}:{TTS_PORT}"  # TTS Service (Higgs + XTTS)
WHISPER_URL = f"http://{SERVER_HOST}:{WHISPER_PORT}"  # Whisper Transcription Service
# LLM_URL removed in v4.0 - orchestrator handles LLM communication
ORCH_WS_URL = f"ws://{SERVER_HOST}:{ORCH_PORT}/ws/conversation"  # V4.0: Orchestrator WebSocket


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
    """Represents a single chat message (v4.1.0)"""
    def __init__(self, role: str, content: str, timestamp: datetime = None):
        self.role = role  # "user" or "assistant"
        self.content = content
        self.timestamp = timestamp or datetime.now()
        self.id = id(self)  # Unique identifier


class ChatWindow:
    """Professional text chat window (v4.3.0 - PERSISTENT WebSocket connection)
    
    Architecture:
    - Opens ONE WebSocket connection when window is shown
    - Connection stays alive for entire chat session
    - Reused for ALL messages (no reconnection per message)
    - Closed only when window closes
    - Mirrors orchestrator's infinite message loop architecture
    """
    
    def __init__(self, parent_app, assistant):
        self.parent_app = parent_app
        self.assistant = assistant
        self.messages = []  # List of ChatMessage objects
        self.is_visible = False
        
        # Persistent WebSocket connection (separate from audio WebSocket)
        self.ws = None
        self.ws_thread = None
        self.ws_connected = False
        self.ws_loop = None
        self.send_queue = queue.Queue()  # Messages to send
        self.response_queue = queue.Queue()  # Responses received
        self._closing = False
        self._response_handler_active = False  # Controls response handler lifecycle
        
        # Theme configuration (v4.3.6 - UI improvements)
        self.themes = {
            "light": {
                "bg": "#C4C4D8",  # Darker purple background (darker than #D4D4E8)
                "user_msg_bg": "#4A90E2",  # Blue
                "user_msg_fg": "white",
                "ai_msg_bg": "#D4D4E8",  # Lighter purple (was the old main bg)
                "ai_msg_fg": "#1a1a1a",  # Dark gray text (not black)
                "input_bg": "#E0E0F0",  # Light purple (NO WHITE)
                "input_fg": "#1a1a1a",  # Dark gray
                "window_bg": "#B8B8CC"  # Even darker purple for frames
            },
            "dark": {
                "bg": "#2B2B2B",  # Dark gray
                "user_msg_bg": "#3A7BC8",  # Darker blue
                "user_msg_fg": "white",
                "ai_msg_bg": "#3C3C3C",  # Medium gray
                "ai_msg_fg": "#E0E0E0",  # Light text
                "input_bg": "#333333",
                "input_fg": "#E0E0E0",
                "window_bg": "#1E1E1E"
            }
        }
        
        # Load theme preference from config (default to light)
        self.current_theme = config.get('UI', 'theme', fallback='light')
        if self.current_theme not in self.themes:
            self.current_theme = 'light'
        
        # Create window
        self.window = tk.Toplevel()
        self.window.title(f"Sparky Text Chat v{VERSION}")
        self.window.geometry("800x600")
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Hide initially
        self.window.withdraw()
        
        self._setup_ui()
        self._setup_styles()
        
    def _setup_ui(self):
        """Setup the UI components"""
        theme = self.themes[self.current_theme]
        
        # Top toolbar
        toolbar = tk.Frame(self.window, relief=tk.RAISED, borderwidth=1, bg=theme["window_bg"])
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=2, pady=2)
        
        tk.Button(toolbar, text="🗑️ Clear", command=self.clear_conversation, width=10).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="💾 Export", command=self.export_chat, width=10).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="🔄 New Chat", command=self.start_new_chat, width=12).pack(side=tk.LEFT, padx=2)
        
        # Theme toggle button (NEW in v4.3.6)
        theme_icon = "🌙" if self.current_theme == "light" else "☀️"
        self.theme_button = tk.Button(toolbar, text=theme_icon, command=self.toggle_theme, width=3)
        self.theme_button.pack(side=tk.LEFT, padx=10)
        
        # Conversation mode indicator
        self.mode_label = tk.Label(toolbar, text="", font=("Segoe UI", 9, "bold"), fg="blue", bg=theme["window_bg"])
        self.mode_label.pack(side=tk.RIGHT, padx=5)
        self._update_mode_indicator()
        
        # Main chat area
        self.chat_frame = tk.Frame(self.window, bg=theme["window_bg"])
        self.chat_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # CRITICAL FIX (v4.3.6): Changed state to NORMAL and added event bindings for read-only behavior
        # This allows text selection and copy while preventing editing
        select_bg = "#A0C0FF" if self.current_theme == "light" else "#4A6FA0"
        select_fg = "black" if self.current_theme == "light" else "white"
        self.chat_text = scrolledtext.ScrolledText(
            self.chat_frame,
            wrap=tk.WORD,
            font=("Segoe UI", 10, "bold"),  # CHANGED: Added "bold" for better readability
            bg=theme["bg"],
            fg=theme["ai_msg_fg"],
            state=tk.NORMAL,  # CHANGED: Was DISABLED - now allows selection
            cursor="xterm",  # Changed from "arrow" to standard text cursor for selection
            selectbackground=select_bg,  # Make text selection visible
            selectforeground=select_fg,  # Selected text color
            exportselection=True,  # Allow selected text to be copied
            takefocus=True  # Allow widget to receive keyboard focus
        )
        self.chat_text.pack(fill=tk.BOTH, expand=True)
        
        # *** TEXT SELECTION FIX ***
        # NO KEY BINDINGS - Tkinter handles selection perfectly by default
        # Removing the bind() call allows native Windows text selection to work
        
        # *** RIGHT-CLICK CONTEXT MENU ***
        # Create context menu for right-click
        self._setup_context_menu()
        
        # Input area
        input_frame = tk.Frame(self.window, bg=theme["window_bg"])
        input_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
        
        # Input text box
        self.input_text = tk.Text(
            input_frame, 
            height=3, 
            font=("Segoe UI", 10, "bold"),  # CHANGED: Added "bold"
            wrap=tk.WORD,
            bg=theme["input_bg"],
            fg=theme["input_fg"],
            insertbackground=theme["input_fg"]  # Cursor color
        )
        self.input_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Bind Enter to send, Shift+Enter for newline
        self.input_text.bind("<Return>", self._on_enter)
        self.input_text.bind("<Shift-Return>", lambda e: None)
        
        # Send button
        self.send_button = tk.Button(input_frame, text="Send", command=self.send_message, width=10)
        self.send_button.pack(side=tk.RIGHT)
        
        # Typing indicator (hidden by default)
        self.typing_label = tk.Label(self.window, text="", font=("Segoe UI", 9, "italic"), fg="gray", bg=theme["window_bg"])
        
    def _setup_styles(self):
        """Setup text tags for styling"""
        theme = self.themes[self.current_theme]
        
        # User message style (right-aligned, blue)
        self.chat_text.tag_config("user_msg", 
                                   background=theme["user_msg_bg"], 
                                   foreground=theme["user_msg_fg"], 
                                   lmargin1=200, lmargin2=200, rmargin=10, 
                                   spacing1=5, spacing3=5, wrap=tk.WORD)
        
        # AI message style (left-aligned, gray)
        self.chat_text.tag_config("ai_msg", 
                                   background=theme["ai_msg_bg"], 
                                   foreground=theme["ai_msg_fg"],
                                   lmargin1=10, lmargin2=10, rmargin=200,
                                   spacing1=5, spacing3=5, wrap=tk.WORD)
        
        # Timestamp style
        timestamp_fg = "gray" if self.current_theme == "light" else "#888888"
        self.chat_text.tag_config("timestamp", font=("Segoe UI", 8, "bold"), foreground=timestamp_fg)
    
    def _setup_context_menu(self):
        """Setup right-click context menu for chat text"""
        # Create context menu
        self.context_menu = tk.Menu(self.window, tearoff=0)
        self.context_menu.add_command(label="Copy", command=self._context_copy, accelerator="Ctrl+C")
        self.context_menu.add_command(label="Select All", command=self._context_select_all, accelerator="Ctrl+A")
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Clear Selection", command=self._context_clear_selection)
        
        # Bind right-click to show menu
        self.chat_text.bind("<Button-3>", self._show_context_menu)
    
    def _show_context_menu(self, event):
        """Show context menu on right-click"""
        try:
            # Show menu at mouse position
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            # Release the grab
            self.context_menu.grab_release()
    
    def _context_copy(self):
        """Copy selected text to clipboard"""
        try:
            # Get selected text
            selected = self.chat_text.get(tk.SEL_FIRST, tk.SEL_LAST)
            # Copy to clipboard
            self.window.clipboard_clear()
            self.window.clipboard_append(selected)
            print(f"✓ Copied {len(selected)} characters to clipboard")
        except tk.TclError:
            # No text selected
            print("⚠️ No text selected to copy")
    
    def _context_select_all(self):
        """Select all text in chat"""
        self.chat_text.tag_add(tk.SEL, "1.0", tk.END)
        self.chat_text.mark_set(tk.INSERT, "1.0")
        self.chat_text.see(tk.INSERT)
        print("✓ Selected all text")
    
    def _context_clear_selection(self):
        """Clear text selection"""
        self.chat_text.tag_remove(tk.SEL, "1.0", tk.END)
        print("✓ Cleared selection")
    
    def toggle_theme(self):
        """Toggle between light and dark themes (NEW in v4.3.6)"""
        # Switch theme
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
        
        # Apply new theme
        self._apply_theme()
    
    def _apply_theme(self):
        """Apply the current theme to all UI elements"""
        theme = self.themes[self.current_theme]
        
        # Update theme toggle button icon
        theme_icon = "🌙" if self.current_theme == "light" else "☀️"
        self.theme_button.config(text=theme_icon)
        
        # Update chat text area (including selection colors)
        select_bg = "#A0C0FF" if self.current_theme == "light" else "#4A6FA0"
        select_fg = "black" if self.current_theme == "light" else "white"
        self.chat_text.config(
            bg=theme["bg"], 
            fg=theme["ai_msg_fg"],
            selectbackground=select_bg,
            selectforeground=select_fg
        )
        
        # Update input area
        self.input_text.config(bg=theme["input_bg"], fg=theme["input_fg"], insertbackground=theme["input_fg"])
        
        # Update frames
        self.chat_frame.config(bg=theme["window_bg"])
        self.typing_label.config(bg=theme["window_bg"])
        self.mode_label.config(bg=theme["window_bg"])
        
        # Update text tags with new colors
        self._setup_styles()
        
        print(f"🎨 Switched to {self.current_theme} theme")
        
    def _update_mode_indicator(self):
        """Update the conversation mode indicator"""
        if self.assistant.conversation_active or self.assistant.session_id:
            self.mode_label.config(text="📝 Continuing conversation", fg="green")
        else:
            self.mode_label.config(text="🆕 New conversation", fg="blue")
    
    def _on_enter(self, event):
        """Handle Enter key press"""
        # Shift+Enter = newline, Enter alone = send
        if not (event.state & 0x1):  # No Shift key
            self.send_message()
            return "break"
        return None
    
    def _display_message(self, role: str, content: str, timestamp: datetime = None):
        """Display a message in the chat window"""
        # Note: chat_text is always in NORMAL state now (v4.3.6) 
        # to allow text selection - editing is blocked via event bindings
        
        timestamp = timestamp or datetime.now()
        time_str = timestamp.strftime("%H:%M")
        
        # Add timestamp and icon
        icon = "👤" if role == "user" else "🤖"
        self.chat_text.insert(tk.END, f"{icon} {time_str}\n", "timestamp")
        
        # Add message with appropriate styling
        tag = "user_msg" if role == "user" else "ai_msg"
        self.chat_text.insert(tk.END, f"{content}\n\n", tag)
        
        # For AI messages, track where we are for efficient streaming updates
        if role == "assistant":
            self._last_ai_content_length = len(content)
            self.chat_text.mark_set("streaming_pos", "end-3c")  # Before the \n\n
        
        self.chat_text.see(tk.END)
    
    def _update_last_message(self, content: str):
        """
        Update the last AI message with new content (for streaming tokens).
        
        v4.3.5: CRITICAL FIX - Only append the NEW characters instead of
        rewriting the entire message. This is O(1) per token instead of O(n).
        v4.3.6: Updated to work with NORMAL state (no state toggling needed)
        """
        try:
            if not hasattr(self, '_last_ai_content_length'):
                self._last_ai_content_length = 0
            
            # Calculate what's new
            old_len = self._last_ai_content_length
            new_chars = content[old_len:]
            
            if new_chars:
                # Note: chat_text is always NORMAL now, no state change needed
                
                # Insert new characters at the streaming position
                self.chat_text.insert("streaming_pos", new_chars, "ai_msg")
                
                # Update position marker
                self.chat_text.mark_set("streaming_pos", "end-3c")  # Before \n\n
                
                self._last_ai_content_length = len(content)
                
                self.chat_text.see(tk.END)
                
        except Exception as e:
            print(f"⚠️ Failed to update last message: {e}")
            import traceback
            traceback.print_exc()
    
    def send_message(self):
        """Send text message through persistent WebSocket connection"""
        text = self.input_text.get("1.0", tk.END).strip()
        if not text:
            return
        
        # Reset streaming state for next AI response
        self._last_ai_content_length = 0
        
        # Clear input
        self.input_text.delete("1.0", tk.END)
        
        # Add user message to display
        user_msg = ChatMessage("user", text)
        self.messages.append(user_msg)
        self._display_message("user", text)
        
        # Check connection
        if not self.ws_connected:
            self._show_error("Not connected to server. Reconnecting...")
            self._connect_websocket()
            return
        
        # Show typing indicator
        self.typing_label.config(text="Sparky is typing...")
        self.typing_label.pack(side=tk.BOTTOM, before=self.chat_text.master)
        
        # Queue message for sending via persistent connection
        self.send_queue.put(("text_chat", text))
    
    def _connect_websocket(self):
        """Open persistent WebSocket connection (separate from audio)"""
        if self.ws_connected:
            return
        
        print("🔗 Opening persistent text chat WebSocket...")
        self._closing = False
        self._response_handler_active = True  # Enable response handler
        
        # Start response handler thread IMMEDIATELY (before WebSocket connects)
        self._response_handler_running = True
        threading.Thread(target=self._handle_responses, daemon=True).start()
        
        # Start WebSocket thread
        self.ws_thread = threading.Thread(target=self._websocket_loop, daemon=True)
        self.ws_thread.start()
    
    def _disconnect_websocket(self):
        """Close persistent WebSocket connection"""
        if not self.ws_connected:
            return
        
        print("🔌 Closing text chat WebSocket...")
        self._closing = True
        self._response_handler_active = False  # Stop response handler
        
        # Close the actual WebSocket connection to unblock recv()
        if self.ws and self.ws_loop:
            try:
                # Schedule close in the asyncio loop
                future = asyncio.run_coroutine_threadsafe(self.ws.close(), self.ws_loop)
                future.result(timeout=1.0)
                print("   WebSocket closed")
            except Exception as e:
                print(f"   WebSocket close error (non-fatal): {e}")
        
        self.ws_connected = False
        
        # Give thread time to close cleanly
        if self.ws_thread:
            self.ws_thread.join(timeout=2.0)
            if self.ws_thread.is_alive():
                print("   ⚠️ WebSocket thread still running (will terminate)")
            else:
                print("   ✓ WebSocket thread closed cleanly")
    
    def _websocket_loop(self):
        """Persistent WebSocket connection loop (runs in separate thread)"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self.ws_loop = loop
            loop.run_until_complete(self._websocket_handler())
        except Exception as e:
            print(f"❌ WebSocket loop error: {e}")
        finally:
            self.ws_connected = False
            loop.close()
    
    async def _websocket_handler(self):
        """Main WebSocket connection handler - stays open for entire session"""
        if not websockets:
            raise Exception("WebSockets library not available")
        
        try:
            async with websockets.connect(ORCH_WS_URL, ping_interval=20, ping_timeout=10) as ws:
                self.ws = ws
                self.ws_connected = True
                
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
                        self.window.after(0, self._update_mode_indicator)
                
                # Create tasks for sending and receiving
                send_task = asyncio.create_task(self._send_handler(ws))
                recv_task = asyncio.create_task(self._receive_handler(ws))
                
                # Wait for BOTH tasks (they should run until connection closes)
                await asyncio.gather(send_task, recv_task, return_exceptions=True)
                    
        except Exception as e:
            print(f"❌ WebSocket error: {e}")
            self.ws_connected = False
            self.window.after(0, lambda: self._show_error(f"Connection lost: {e}"))
    
    async def _send_handler(self, ws):
        """Handle outgoing messages from queue"""
        while not self._closing and self.ws_connected:
            try:
                # Use get_nowait() instead of blocking get() to avoid blocking event loop
                try:
                    msg_type, msg_data = self.send_queue.get_nowait()
                except queue.Empty:
                    # No message available - yield control to event loop
                    await asyncio.sleep(0.1)
                    continue
                
                # Send text chat message
                await ws.send(json.dumps({
                    "type": msg_type,
                    "text": msg_data
                }))
                
            except Exception as e:
                print(f"❌ Send error: {e}")
                break
    
    async def _receive_handler(self, ws):
        """Handle incoming responses"""
        current_response = ""
        streaming_started = False
        
        while not self._closing and self.ws_connected:
            try:
                msg = await ws.recv()
                
                if isinstance(msg, str):
                    data = json.loads(msg)
                    msg_type = data.get("type")
                    
                    if msg_type == "text_token":
                        # Real-time token streaming
                        token = data.get("token", "")
                        current_response += token
                        
                        # Queue for UI update
                        self.response_queue.put(("token", current_response, streaming_started))
                        streaming_started = True
                    
                    elif msg_type == "text_response":
                        # Final complete response
                        final_text = data.get("text", "")
                        if final_text:
                            self.response_queue.put(("final", final_text, streaming_started))
                        
                        # Reset for next message
                        current_response = ""
                        streaming_started = False
                    
                    elif msg_type == "error":
                        error_msg = data.get("detail", "Unknown error")
                        self.response_queue.put(("error", error_msg, False))
                        print(f"❌ Server error: {error_msg}")
                    
                    elif msg_type == "done":
                        # Message complete
                        current_response = ""
                        streaming_started = False
                        
            except websockets.exceptions.ConnectionClosed:
                print("🔌 WebSocket connection closed")
                break
            except Exception as e:
                print(f"❌ Receive error: {e}")
                break
    
    def _handle_responses(self):
        """Handle responses from WebSocket (runs in separate thread for UI updates)"""
        # Wait for connection to be established (with timeout)
        timeout = 10.0
        start_time = time.time()
        while not self.ws_connected and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        
        if not self.ws_connected:
            print("⚠️ Response handler timeout waiting for connection")
            return
        
        while self._response_handler_active and not self._closing:
            try:
                # Check queue with timeout
                try:
                    msg_type, content, streaming_started = self.response_queue.get(timeout=0.5)
                except queue.Empty:
                    continue
                
                if msg_type == "token":
                    # Update UI with streaming token
                    if not streaming_started:
                        # First token - create new message
                        ai_msg = ChatMessage("assistant", content)
                        self.messages.append(ai_msg)
                        self.window.after(0, lambda t=content: self._display_message("assistant", t))
                    else:
                        # Subsequent tokens - update last message
                        if self.messages:
                            self.messages[-1].content = content
                        self.window.after(0, lambda t=content: self._update_last_message(t))
                
                elif msg_type == "final":
                    # Final complete response
                    if self.messages:
                        self.messages[-1].content = content
                        self.window.after(0, lambda t=content: self._update_last_message(t))
                    else:
                        # Fallback if no streaming occurred
                        ai_msg = ChatMessage("assistant", content)
                        self.messages.append(ai_msg)
                        self.window.after(0, lambda t=content: self._display_message("assistant", t))
                    
                    # Hide typing indicator
                    self.window.after(0, lambda: self.typing_label.pack_forget())
                
                elif msg_type == "error":
                    self.window.after(0, lambda e=content: self._show_error(e))
                    self.window.after(0, lambda: self.typing_label.pack_forget())
                    
            except Exception as e:
                print(f"❌ Response handler error: {e}")
    
    def _send_text_async(self, text: str):
        """DEPRECATED - kept for compatibility but not used"""
        pass
    
    async def _send_text_websocket(self, text: str):
        """DEPRECATED - kept for compatibility but not used"""
        pass
    
    def _show_error(self, error: str):
        """Show error message"""
        messagebox.showerror("Error", f"Failed to send message:\n{error}")
    
    def start_new_chat(self):
        """Start a new conversation (clear history)"""
        if self.messages:
            if messagebox.askyesno("New Chat", "Start a new conversation?\nThis will clear the current chat history."):
                self.messages.clear()
                # Note: chat_text is always NORMAL now (v4.3.6), no state change needed
                self.chat_text.delete("1.0", tk.END)
                
                # Clear orchestrator session
                self.assistant.session_id = None
                self.assistant.conversation_active = False
                self._update_mode_indicator()
                print("🆕 New chat started")
        else:
            # No messages yet, just clear session
            self.assistant.session_id = None
            self.assistant.conversation_active = False
            self._update_mode_indicator()
    
    def clear_conversation(self):
        """Clear all messages"""
        if not self.messages:
            messagebox.showinfo("Nothing to Clear", "Chat is already empty.")
            return
        
        if messagebox.askyesno("Clear Chat", "Clear all messages?"):
            self.messages.clear()
            # Note: chat_text is always NORMAL now (v4.3.6), no state change needed
            self.chat_text.delete("1.0", tk.END)
            
            # Clear orchestrator history
            self.assistant.session_id = None
            self.assistant.conversation_active = False
            self._update_mode_indicator()
            print("🗑️ Chat cleared")
    
    def export_chat(self):
        """Export chat to file"""
        if not self.messages:
            messagebox.showinfo("Nothing to Export", "No messages to export.")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("Markdown files", "*.md"), ("All files", "*.*")]
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
                
                messagebox.showinfo("Export Successful", f"Chat exported to:\n{filename}")
                print(f"💾 Chat exported to: {filename}")
            except Exception as e:
                messagebox.showerror("Export Failed", f"Failed to export chat:\n{e}")
    
    def show(self):
        """Show the chat window and open persistent WebSocket"""
        if not self.is_visible:
            self.window.deiconify()
            self.is_visible = True
            self._update_mode_indicator()
            
            # Open persistent WebSocket connection for text chat
            if not self.ws_connected:
                self._connect_websocket()
    
    def hide(self):
        """Hide the chat window and close persistent WebSocket"""
        if self.is_visible:
            self.window.withdraw()
            self.is_visible = False
            
            # Close persistent WebSocket connection
            if self.ws_connected:
                self._disconnect_websocket()
    
    def on_close(self):
        """Handle window close button"""
        # Close WebSocket before hiding
        if self.ws_connected:
            self._disconnect_websocket()
        self.hide()
    
    def toggle_visibility(self):
        """Toggle window visibility"""
        if self.is_visible:
            self.hide()
        else:
            self.show()


class SparkyVoiceAssistant:
    """Main voice assistant engine with DUAL-STREAM architecture"""
    
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
        self.abort_lock = threading.Lock()  # Prevents race conditions
        
        # Echo cancellation buffers
        self.tts_playback_buffer = deque(maxlen=ECHO_BUFFER_SIZE)  # What AI is playing
        self.echo_cancel_lock = threading.Lock()
        
        # V3.0: DUAL-STREAM ARCHITECTURE
        # Secondary stream dedicated to exit word detection only
        self.exit_audio_queue = queue.Queue()
        self.exit_stream = None
        self.exit_stream_running = False
        self.exit_detection_thread = None
        
        # Initialize wake word models
        self.wake_model = None
        self.exit_model = None
        self.load_wake_models()
        
        # V4.0: Server-side session management
        self.session_id = None  # Orchestrator maintains conversation history
        self.output_stream = None  # Keep output stream open during conversation
        
        # Start keyboard listener for Escape key
        # v4.3.4: Make keyboard listener daemon so it doesn't block exit
        self.keyboard_listener = keyboard.Listener(on_press=self._on_key_press, daemon=True)
        self.keyboard_listener.start()
        
    def _on_key_press(self, key):
        """Handle keyboard events"""
        try:
            if key == ABORT_HOTKEY and self.conversation_active:
                print(f"\n⌨️ Hotkey abort triggered ({ABORT_HOTKEY.name.upper()})")
                self._emergency_abort()
        except AttributeError:
            pass  # Special keys may not have certain attributes
    
    def load_wake_models(self):
        """Load wake word models"""
        try:
            # Check for custom models first
            custom_wake = WAKE_MODELS_DIR / "hey_sparky.tflite"
            custom_exit = WAKE_MODELS_DIR / "bye_sparky.tflite"
            
            if custom_wake.exists() and custom_exit.exists():
                print("Loading custom Sparky wake words...")
                self.wake_model = Model(wakeword_models=[str(custom_wake)])
                self.exit_model = Model(wakeword_models=[str(custom_exit)])
                self.wake_word_name = "Hey Sparky"
                self.exit_word_name = "Bye Sparky"
            else:
                # Fall back to built-in models
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
        """Callback for PRIMARY audio stream (wake word + recording)"""
        if status:
            print(f"Audio status: {status}")
        if self.running:
            self.audio_queue.put(indata.copy())
    
    def exit_audio_callback(self, indata, frames, time, status):
        """Callback for SECONDARY audio stream (exit word detection only)"""
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
        
        # Collect samples for calibration period
        while time.time() - calibration_start < CALIBRATION_DURATION:
            try:
                audio_chunk = self.audio_queue.get(timeout=0.1)
                audio_data = audio_chunk.flatten()
                amplitude = np.max(np.abs(audio_data))
                self.calibration_samples.append(amplitude)
            except queue.Empty:
                continue
        
        # Calculate noise floor with better margin
        if self.calibration_samples:
            ambient_noise = np.percentile(self.calibration_samples, 95)
            self.silence_threshold = ambient_noise * 3.5  # Higher multiplier for better separation
            self.silence_threshold = max(self.silence_threshold, 0.015)  # Even higher minimum - no more phantoms!
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
        """Clear the audio queue to prevent stale audio from triggering detections"""
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break
        if DEBUG_WAKEWORD:
            print("  🗑️ Audio queue cleared")
    
    def _apply_echo_cancellation(self, mic_audio):
        """
        Apply simple echo cancellation by subtracting known TTS playback
        
        This is a basic implementation - just subtracts the audio we're playing.
        A full implementation would need:
        - Acoustic delay compensation
        - Adaptive filtering for room acoustics
        - Speaker response modeling
        
        But this simple version should work well enough for our purposes.
        """
        if not ECHO_CANCEL_ENABLED or not self.is_speaking:
            return mic_audio  # No echo to cancel
        
        with self.echo_cancel_lock:
            if len(self.tts_playback_buffer) == 0:
                return mic_audio  # No TTS audio to subtract
            
            # Get the most recent TTS chunk (rough synchronization)
            tts_chunk = self.tts_playback_buffer[-1]
            
            # Ensure same length
            min_len = min(len(mic_audio), len(tts_chunk))
            mic_segment = mic_audio[:min_len]
            tts_segment = tts_chunk[:min_len]
            
            # Simple subtraction with attenuation factor
            # (speakers aren't as loud at mic as original signal)
            attenuation = 0.3  # Assume speaker audio is 30% as loud at mic
            cleaned_audio = mic_segment - (tts_segment * attenuation)
            
            # Pad back to original length if needed
            if len(cleaned_audio) < len(mic_audio):
                padding = np.zeros(len(mic_audio) - len(cleaned_audio))
                cleaned_audio = np.concatenate([cleaned_audio, padding])
            
            return cleaned_audio
    
    def start_listening(self):
        """Start the PRIMARY audio stream (wake word + recording)"""
        self.running = True
        
        # Start primary audio stream
        self.stream = sd.InputStream(
            channels=CHANNELS,
            samplerate=SAMPLE_RATE,
            callback=self.audio_callback,
            blocksize=int(SAMPLE_RATE * 0.08)
        )
        self.stream.start()
        
        # Start detection thread for primary stream
        self.detection_thread = threading.Thread(target=self._detection_loop, daemon=True)
        self.detection_thread.start()
        
        mode_str = "VAD" if self.input_mode == InputMode.VAD else "Manual"
        print(f"🎤 Primary stream started - Mode: {mode_str}")
        
        # Auto-calibrate on startup
        if AUTO_CALIBRATE:
            self.calibrate_microphone()
        
        # Set appropriate state after calibration
        if self.input_mode == InputMode.VAD:
            self.state = VoiceState.LISTENING_FOR_WAKE
        else:
            if self.conversation_active:
                self.state = VoiceState.ACTIVE_CONVERSATION
            else:
                self.state = VoiceState.IDLE
    
    def start_exit_stream(self):
        """V3.0: Start the SECONDARY audio stream (dedicated exit word detection)"""
        if self.exit_stream_running:
            return  # Already running
        
        self.exit_stream_running = True
        
        # Start secondary audio stream for exit word detection
        self.exit_stream = sd.InputStream(
            channels=CHANNELS,
            samplerate=SAMPLE_RATE,
            callback=self.exit_audio_callback,
            blocksize=int(SAMPLE_RATE * 0.08)
        )
        self.exit_stream.start()
        
        # Start dedicated exit word detection thread
        self.exit_detection_thread = threading.Thread(target=self._exit_detection_loop, daemon=True)
        self.exit_detection_thread.start()
        
        print("🎯 Exit detection stream started (dedicated)")
    
    def stop_exit_stream(self):
        """V3.0: Stop the SECONDARY audio stream"""
        if not self.exit_stream_running:
            return
        
        self.exit_stream_running = False
        
        if self.exit_stream:
            self.exit_stream.stop()
            self.exit_stream.close()
            self.exit_stream = None
        
        # Clear exit audio queue
        while not self.exit_audio_queue.empty():
            try:
                self.exit_audio_queue.get_nowait()
            except queue.Empty:
                break
        
        print("🛑 Exit detection stream stopped")
    
    def stop_listening(self):
        """Stop the PRIMARY audio stream"""
        self.running = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        self.calibrated = False
        print("🔇 Primary stream stopped")
    
    def _exit_detection_loop(self):
        """
        V3.0: DEDICATED exit word detection loop
        Runs on SECONDARY audio stream - 100% focused on exit word detection
        No competition with other processing - ALWAYS listening!
        """
        audio_buffer = []
        exit_check_counter = 0
        
        print("✓ Exit detection loop active (100% dedicated)")
        
        while self.exit_stream_running:
            try:
                audio_chunk = self.exit_audio_queue.get(timeout=0.1)
                audio_buffer.append(audio_chunk)
                
                if len(audio_buffer) >= 1:
                    audio_data = np.concatenate(audio_buffer, axis=0).flatten()
                    audio_buffer = []
                    
                    # Apply echo cancellation if AI is speaking
                    cleaned_audio = self._apply_echo_cancellation(audio_data)
                    
                    # EXIT WORD DETECTION - runs on EVERY chunk!
                    if self.exit_model:
                        audio_int16 = (cleaned_audio * 32767).astype(np.int16)
                        prediction = self.exit_model.predict(audio_int16)
                        
                        exit_check_counter += 1
                        
                        # Dynamic threshold: more sensitive when AI speaking
                        exit_threshold = 0.3 if self.is_speaking else 0.5
                        
                        if DEBUG_WAKEWORD and exit_check_counter % 20 == 0:
                            status = "SPEAKING+ECHO" if self.is_speaking else "LISTENING"
                            for mdl_name, score in prediction.items():
                                print(f"🎯 [EXIT STREAM {exit_check_counter}] [{status}] {mdl_name}: {score:.3f} (threshold: {exit_threshold})")
                        
                        # Check if exit word detected
                        for mdl_name, score in prediction.items():
                            if score > exit_threshold:
                                print(f"\n🛑 EXIT WORD DETECTED! ({score:.2f} > {exit_threshold})")
                                self._emergency_abort()
                                break
                        
            except queue.Empty:
                continue
            except Exception as e:
                if self.exit_stream_running:  # Only log if we should be running
                    print(f"Error in exit detection loop: {e}")
                    import traceback
                    traceback.print_exc()
    
    def _detection_loop(self):
        """PRIMARY detection loop (wake word + recording only)"""
        audio_buffer = []
        wake_check_counter = 0
        
        while self.running:
            try:
                audio_chunk = self.audio_queue.get(timeout=0.1)
                
                # Skip processing if we're calibrating
                if self.state == VoiceState.CALIBRATING:
                    continue
                
                audio_buffer.append(audio_chunk)
                
                if len(audio_buffer) >= 1:
                    audio_data = np.concatenate(audio_buffer, axis=0).flatten()
                    audio_buffer = []
                    
                    # Apply echo cancellation if AI is speaking
                    cleaned_audio = self._apply_echo_cancellation(audio_data)
                    
                    # WAKE WORD DETECTION (only when waiting for wake word)
                    if self.input_mode == InputMode.VAD:
                        if self.state == VoiceState.LISTENING_FOR_WAKE and self.wake_model and not self.is_speaking:
                            audio_int16 = (cleaned_audio * 32767).astype(np.int16)
                            prediction = self.wake_model.predict(audio_int16)
                            
                            wake_check_counter += 1
                            if DEBUG_WAKEWORD and wake_check_counter % 10 == 0:
                                audio_info = f"Audio: shape={audio_int16.shape} dtype={audio_int16.dtype} range=[{audio_int16.min()}, {audio_int16.max()}]"
                                scores_str = " | ".join([f"{name}: {score:.3f}" for name, score in prediction.items()])
                                print(f"🎯 Wake check: {scores_str} | {audio_info}")
                            
                            for mdl_name, score in prediction.items():
                                if DEBUG_WAKEWORD and score > 0.1:
                                    print(f"🔔 {mdl_name}: {score:.3f}", end="")
                                    if score > 0.5:
                                        print(" ← THRESHOLD MET!")
                                    else:
                                        print(" (below threshold)")
                                
                                if score > 0.5:
                                    print(f"\n🎯 Wake word detected! ({score:.2f})")
                                    self._activate_conversation()
                                    break
                    
                    # RECORDING LOGIC (when conversation active and not speaking)
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
            print(f"Amplitude: {amplitude:.4f} | Threshold: {self.silence_threshold:.4f} | Recording: {self.recording_command} | Silence chunks: {self.silence_chunks}")
        
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
                
                if DEBUG_AUDIO:
                    print(f"  Silence duration: {silence_duration:.2f}s / {SILENCE_DURATION}s")
                
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
        """
        Process recorded command using orchestrator WebSocket
        V4.0: Server-side orchestration - client only handles audio I/O
        """
        # Always use orchestrator - server handles Whisper → LLM → TTS
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
        """
        V4.0: Process command using orchestrator WebSocket
        Server handles: Whisper → LLM → TTS coordination
        Client handles: Audio I/O with streaming playback
        """
        try:
            self.state = VoiceState.PROCESSING
            
            # Validate recording length
            full_audio = np.concatenate(audio_chunks)
            if len(full_audio) < SAMPLE_RATE * 0.5:
                print("⚠️ Recording too short, ignored")
                self.state = VoiceState.ACTIVE_CONVERSATION
                return
            
            print("🔗 Connecting to orchestrator...")
            
            # Connect to orchestrator WebSocket
            async with websockets.connect(ORCH_WS_URL, max_size=None) as ws:
                # 1. Send START with optional session resumption
                start_msg = {
                    "type": "start",
                    "voice": DEFAULT_VOICE
                }
                if self.session_id:
                    start_msg["session_id"] = self.session_id
                
                await ws.send(json.dumps(start_msg))
                
                # 2. Send audio as base64 chunks
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
                
                # 3. Send FINAL
                await ws.send(json.dumps({"type": "final"}))
                
                # 4. Prepare audio output
                if not self.output_stream or not self.output_stream.active:
                    self.output_stream = sd.OutputStream(
                        samplerate=TTS_SAMPLE_RATE,
                        channels=TTS_CHANNELS,
                        dtype='int16'
                    )
                    self.output_stream.start()
                
                self.is_speaking = False
                first_audio = True
                
                # 5. Receive responses
                while True:
                    # Check abort flag
                    if self.abort_tts:
                        print("🛑 Conversation aborted")
                        break
                    
                    msg = await ws.recv()
                    
                    if isinstance(msg, (bytes, bytearray)):
                        # Binary audio data - play immediately (TRUE STREAMING)
                        if first_audio:
                            print("🔊 Streaming audio...")
                            self.is_speaking = True
                            self.state = VoiceState.SPEAKING
                            first_audio = False
                        
                        audio_data = np.frombuffer(msg, dtype=np.int16)
                        
                        # Echo cancellation buffer
                        if ECHO_CANCEL_ENABLED:
                            # Resample from 24kHz to 16kHz to match mic
                            if TTS_SAMPLE_RATE != SAMPLE_RATE:
                                ratio = TTS_SAMPLE_RATE / SAMPLE_RATE
                                indices = np.arange(0, len(audio_data), ratio).astype(int)
                                resampled = audio_data[indices]
                            else:
                                resampled = audio_data
                            
                            normalized = resampled.astype(np.float32) / 32767.0
                            
                            with self.echo_cancel_lock:
                                self.tts_playback_buffer.append(normalized)
                        
                        # Play audio
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
        """
        Play greeting or goodbye through orchestrator (async wrapper)
        message_type: "greeting" or "goodbye"
        """
        threading.Thread(
            target=self._run_async_greeting_goodbye,
            args=(message_type,),
            daemon=True
        ).start()
    
    def _run_async_greeting_goodbye(self, message_type):
        """Run async greeting/goodbye call from sync thread"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._play_simple_tts(message_type))
        finally:
            loop.close()
    
    async def _play_simple_tts(self, message_type):
        """
        Send greeting or goodbye to orchestrator and play audio
        message_type: "greeting" or "goodbye"
        """
        try:
            print(f"🔗 Playing {message_type} via orchestrator...")
            
            async with websockets.connect(ORCH_WS_URL, max_size=None) as ws:
                # 1. Send START
                await ws.send(json.dumps({
                    "type": "start",
                    "voice": DEFAULT_VOICE,
                    "session_id": self.session_id  # Resume session if exists
                }))
                
                # 2. Send greeting or goodbye message
                await ws.send(json.dumps({"type": message_type}))
                
                # 3. Prepare audio output
                if not self.output_stream or not self.output_stream.active:
                    self.output_stream = sd.OutputStream(
                        samplerate=TTS_SAMPLE_RATE,
                        channels=TTS_CHANNELS,
                        dtype='int16'
                    )
                    self.output_stream.start()
                
                self.is_speaking = True
                first_audio = True
                
                # 4. Receive and play audio
                while True:
                    if self.abort_tts:
                        break
                    
                    msg = await ws.recv()
                    
                    if isinstance(msg, (bytes, bytearray)):
                        # Binary audio data
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
                        # JSON metadata
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
        """
        Activate conversation mode
        V3.3: Quick delay (0.3s) before exit stream - balances responsiveness and stability
        """
        self.state = VoiceState.ACTIVE_CONVERSATION
        self.conversation_active = True
        self.command_audio_buffer = []
        self.silence_chunks = 0
        self.recording_command = False
        
        self._clear_audio_queue()
        
        # V3.2: DON'T start exit stream yet - wait until after greeting
        
        mode = "VAD - just speak" if self.input_mode == InputMode.VAD else "Manual"
        print(f"💬 Conversation active! ({mode})")
        
        if self.input_mode == InputMode.VAD:
            print(f"   Say '{self.exit_word_name}' or press {ABORT_HOTKEY.name.upper()} to exit")
        
        # Play greeting via orchestrator (non-blocking)
        self._play_greeting_or_goodbye_via_orchestrator("greeting")
        
        # V3.3: Wait briefly for greeting to start, then start exit detection
        if self.input_mode == InputMode.VAD:
            print("⏳ Waiting for greeting to start...")
            time.sleep(0.5)  # Brief wait for greeting to begin
            self._clear_audio_queue()  # Clear any stale audio
            print("🎯 Starting exit detection now...")
            self.start_exit_stream()
    
    def _emergency_abort(self):
        """
        V3.4 INSTANT GOODBYE FIX: Play goodbye IMMEDIATELY, cleanup happens after
        THREAD-SAFE: Uses lock to prevent race conditions from multiple abort sources
        """
        # CRITICAL: Lock prevents race condition if both hotkey and exit word trigger simultaneously
        with self.abort_lock:
            # Check if already aborting
            if not self.conversation_active:
                return  # Already aborted, skip
            
            print("🛑 EMERGENCY ABORT - User requested exit")
            
            # Set abort flag to stop any ongoing TTS
            self.abort_reason = "user_abort"
            self.abort_tts = True
            
            # Stop any ongoing recording immediately
            self.recording_command = False
            self.command_audio_buffer = []
            self.silence_chunks = 0
            
            # Mark conversation as ended (BEFORE goodbye so user can't trigger another exit)
            self.conversation_active = False
            
            # V3.5: Stop wake word models to ensure clean state
            if self.input_mode == InputMode.VAD:
                print("🔄 Stopping wake word models...")
                self.wake_model = None
                self.exit_model = None
            
            # Brief pause to let abort flag take effect
            time.sleep(0.1)
            
            # Reset abort flag for goodbye message
            self.abort_tts = False
            self.abort_reason = None
            
            # *** V4.0: PLAY GOODBYE VIA ORCHESTRATOR ***
            goodbye_msg = GOODBYE_MESSAGE.strip()
            if goodbye_msg:
                print("👋 Playing goodbye message via orchestrator...")
                self._play_greeting_or_goodbye_via_orchestrator("goodbye")
                # Wait for goodbye to complete
                time.sleep(2.0)  # Brief wait for goodbye to play
            else:
                print("👋 Silent goodbye (no message configured)")
            
            # *** NOW DO ALL THE CLEANUP AFTER GOODBYE ***
            print("🧹 Starting cleanup...")
            
            # Stop exit stream (can be slow)
            self.stop_exit_stream()
            
            # Clear audio queue
            self._clear_audio_queue()
            
            # Clear echo cancellation buffer
            with self.echo_cancel_lock:
                self.tts_playback_buffer.clear()
            
            # CRITICAL: Audio buffer to let all audio clear from mic/room
            print(f"⏳ Audio buffer active ({AUDIO_BUFFER_DURATION}s)...")
            time.sleep(AUDIO_BUFFER_DURATION)
            
            # CRITICAL: Clear audio queue AGAIN after buffer to remove any lingering echo
            self._clear_audio_queue()
            
            # CRITICAL: Additional 1 second wait to ensure complete silence
            time.sleep(1.0)
            
            # V3.5: Reload wake word models for completely fresh start
            if self.input_mode == InputMode.VAD:
                try:
                    print("🔄 Reloading wake word models...")
                    self.load_wake_models()
                    print("✓ Models reloaded - clean slate!")
                except Exception as e:
                    print(f"❌ Failed to reload models: {e}")
                    print("   Wake words unavailable - use 'Reload Wake Words' from menu")
                    self.state = VoiceState.IDLE
                    return
            
            # Now safe to transition back to listening
            if self.input_mode == InputMode.VAD:
                self.state = VoiceState.LISTENING_FOR_WAKE
                print(f"✓ Ready! Listening for '{self.wake_word_name}'...")
            else:
                self.state = VoiceState.IDLE
                print("✓ Conversation ended")
    
    def toggle_input_mode(self):
        """Toggle between VAD and Manual mode"""
        if self.conversation_active:
            self._emergency_abort()
        
        self.input_mode = InputMode.MANUAL if self.input_mode == InputMode.VAD else InputMode.VAD
        
        if self.input_mode == InputMode.VAD:
            self.state = VoiceState.LISTENING_FOR_WAKE
        else:
            self.state = VoiceState.IDLE
        
        mode = "VAD" if self.input_mode == InputMode.VAD else "Manual"
        print(f"🔄 Input mode: {mode}")
        return mode
    
    def manual_start_conversation(self):
        """Manually start conversation (Manual mode only)"""
        if self.input_mode == InputMode.MANUAL and not self.conversation_active:
            self._activate_conversation()
            return True
        return False
    
    def manual_stop_conversation(self):
        """Manually stop conversation (Manual mode only) - uses same emergency abort"""
        if self.input_mode == InputMode.MANUAL and self.conversation_active:
            self._emergency_abort()
            return True
        return False
    
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
        # Stop exit stream if running
        if self.exit_stream_running:
            self.stop_exit_stream()
        
        if self.keyboard_listener:
            self.keyboard_listener.stop()


class SparkyTrayApp:
    """System tray application"""
    
    def __init__(self):
        self.assistant = SparkyVoiceAssistant()
        self.icon = None
        self.auto_start_enabled = self._check_auto_start()
        
        # v4.1.0: Create hidden Tk root for text chat window
        # (Required for tk.Toplevel to work in system tray app)
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the root window
        
        # v4.1.0: Initialize text chat window
        self.chat_window = ChatWindow(self, self.assistant)
        
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
        """Toggle text chat window (v4.1.0)"""
        self.chat_window.toggle_visibility()
        if self.icon:
            self.icon.menu = self.get_menu()
    
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
        print(f"SPARKY VOICE AI - System Tray Edition v{VERSION}")
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
        print("\nv4.0 ORCHESTRATOR:")
        print("  ✓ Server-side conversation management")
        print("  ✓ Persistent session history across restarts")
        print("  ✓ True end-to-end streaming (LLM → TTS)")
        print("  ✓ Instant greeting/goodbye via server")
        print("\nv4.1 TEXT CHAT:")
        print("  ✓ Professional text chat window")
        print("  ✓ Shared conversation history (text + voice)")
        print("  ✓ Continue conversations across modes")
        print("  ✓ Export/clear functionality")
        print("="*60 + "\n")
    
    def update_icon(self, color):
        """Update icon color"""
        if self.icon:
            self.icon.icon = self.create_icon_image(color)
    
    def quit_app(self, icon=None, item=None):
        """Quit application"""
        print("\n👋 Shutting down Sparky...")
        
        # v4.3.4: Close chat window first (includes WebSocket cleanup)
        if hasattr(self, 'chat_window') and self.chat_window:
            print("   Closing text chat WebSocket...")
            self.chat_window._disconnect_websocket()
        
        # Stop audio streams
        self.assistant.cleanup()
        self.assistant.stop_listening()
        
        # Quit Tkinter event loop first (main thread)
        if hasattr(self, 'root'):
            print("   Stopping Tkinter event loop...")
            self.root.quit()
        
        # Stop icon (will exit icon thread)
        if self.icon:
            print("   Stopping tray icon...")
            self.icon.stop()
        
        # Destroy Tkinter root (cleanup)
        if hasattr(self, 'root'):
            try:
                self.root.destroy()
            except:
                pass  # May already be destroyed
        
        print("✅ Shutdown complete")
    
    def run(self):
        """Run the system tray app"""
        print(f"🚀 Starting Sparky Voice AI v{VERSION}...")
        print(f"📂 Models: {WAKE_MODELS_DIR}")
        print(f"🛑 Exit: Voice word OR {ABORT_HOTKEY.name.upper()} key")
        print(f"🔇 Echo cancellation: {'Enabled' if ECHO_CANCEL_ENABLED else 'Disabled'}")
        print(f"⏳ Audio buffer: {AUDIO_BUFFER_DURATION}s + 1s wait")
        
        print(f"\n🔗 v4.1 TEXT CHAT + ORCHESTRATOR:")
        print(f"   ✓ Server-side conversation management")
        print(f"   ✓ Session persistence across turns")
        print(f"   ✓ Text chat with shared history")
        print(f"   ✓ Connected to: {ORCH_WS_URL}")
        
        self.assistant.start_listening()
        
        self.icon = Icon(
            "SparkyVoiceAI",
            self.create_icon_image("green"),
            "Sparky Voice AI",
            self.get_menu()
        )
        
        # v4.3.4: Run tray icon in daemon thread so it doesn't block exit
        # This allows clean shutdown when quit_app() is called
        icon_thread = threading.Thread(target=self.icon.run, daemon=True)
        icon_thread.start()
        
        # Run Tkinter event loop in main thread
        # This is required for text chat window to work
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")
            self.quit_app()
        
        # v4.3.4: Explicitly exit after mainloop completes
        # This ensures the process terminates cleanly
        print("🚪 Main loop exited, terminating process...")
        import sys
        sys.exit(0)


def main():
    """Main entry point"""
    print(f"""
╔══════════════════════════════════════════════════════════╗
║     SPARKY VOICE AI - SYSTEM TRAY EDITION v{VERSION}         ║
║                                                          ║
║        TEXT CHAT + ORCHESTRATION - WEBSOCKET  🔗💬       ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    app = SparkyTrayApp()
    app.run()


if __name__ == "__main__":
    main()