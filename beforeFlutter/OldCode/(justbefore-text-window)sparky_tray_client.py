#!/usr/bin/env python3
"""
Sparky Voice-AI System Tray Client v4.0.0
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
        self.keyboard_listener = keyboard.Listener(on_press=self._on_key_press)
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
        print("SPARKY VOICE AI - System Tray Edition v4.0.0")
        print("="*60)
        print("\nLocal-only voice assistant with TRUE STREAMING")
        print("No cloud • No accounts • No expiration")
        print("\nComponents:")
        print("  • openWakeWord - Wake word detection")
        print("  • faster-whisper - Speech-to-text")
        print("  • Coqui XTTS - Text-to-speech (STREAMING)")
        print("  • vLLM - LLM inference")
        print(f"\nOrchestrator: {ORCH_WS_URL}")
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
        print("="*60 + "\n")
    
    def update_icon(self, color):
        """Update icon color"""
        if self.icon:
            self.icon.icon = self.create_icon_image(color)
    
    def quit_app(self, icon=None, item=None):
        """Quit application"""
        print("\n👋 Shutting down Sparky...")
        self.assistant.cleanup()
        self.assistant.stop_listening()
        if self.icon:
            self.icon.stop()
    
    def run(self):
        """Run the system tray app"""
        print("🚀 Starting Sparky Voice AI v4.0.0...")
        print(f"📂 Models: {WAKE_MODELS_DIR}")
        print(f"🛑 Exit: Voice word OR {ABORT_HOTKEY.name.upper()} key")
        print(f"🔇 Echo cancellation: {'Enabled' if ECHO_CANCEL_ENABLED else 'Disabled'}")
        print(f"⏳ Audio buffer: {AUDIO_BUFFER_DURATION}s + 1s wait")
        
        print(f"\n🔗 v4.0 ORCHESTRATOR MODE:")
        print(f"   ✓ Server-side conversation management")
        print(f"   ✓ Session persistence across turns")
        print(f"   ✓ Connected to: {ORCH_WS_URL}")
        
        self.assistant.start_listening()
        
        self.icon = Icon(
            "SparkyVoiceAI",
            self.create_icon_image("green"),
            "Sparky Voice AI",
            self.get_menu()
        )
        
        self.icon.run()


def main():
    """Main entry point"""
    print("""
╔══════════════════════════════════════════════════════════╗
║     SPARKY VOICE AI - SYSTEM TRAY EDITION v4.0          ║
║                                                          ║
║        SERVER-SIDE ORCHESTRATION - WEBSOCKET  🔗         ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    app = SparkyTrayApp()
    app.run()


if __name__ == "__main__":
    main()