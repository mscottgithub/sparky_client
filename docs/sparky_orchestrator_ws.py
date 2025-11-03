#!/usr/bin/env python3
"""
Sparky Orchestrator v3.0 - Proper Multi-Turn Prevention Architecture
Philosophy: Let AI speak naturally (max_tokens=1000), but enforce single-turn discipline

Changes from v2.9:
- max_tokens: 150 → 1000 (allows complete, detailed responses)
- Enhanced token cleaning: Catches backslashes, partial tokens, all artifacts
- Response validator: Post-processes to detect and truncate multi-turn patterns
- Aggressive stop sequences: Double-newlines, conversation patterns
- Nuclear system prompt from .env: User controls AI behavior completely
"""
import os, json, asyncio, logging, socket, re
from typing import AsyncIterator, Optional, Dict, List
from datetime import datetime
from uuid import uuid4
import base64
import io

import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel

# ── .env (canonical path) ──────────────────────────────────────────────────────
ENV_PATH = "/home/mintdude/Github/sparky/.env"
load_dotenv(ENV_PATH)

# ── Template Tag Cleaning ──────────────────────────────────────────────────────
def clean_llm_response(text: str, strip: bool = False) -> str:
    """
    Remove ALL template tags, special tokens, and artifacts from LLM output.
    
    Prevents tags from appearing in chat or being read aloud by TTS.
    
    CRITICAL: Replaces tags with spaces to preserve word boundaries.
    CRITICAL: Does NOT strip whitespace by default - preserves token spacing!
    
    Catches:
    - ChatML: <|im_start|>, <|im_end|>
    - Special: <|endoftext|>, <s>, </s>
    - Pipe format: |</s>|, |<s>|
    - Role prefixes: "user:", "assistant:"
    - Numbered tokens: <|reserved_special_token_92|>
    - XML tags: <speaker ...>, <|assistant|>
    - Partial tokens: </assistant|>, <|assistant (incomplete)
    - Backslash artifacts: \ \ or \n\n
    
    Args:
        text: Raw LLM output potentially containing template tags
        strip: If True, strip leading/trailing whitespace (only for final responses)
        
    Returns:
        Cleaned text with all template tags removed and proper spacing
    """
    # 0. Clean backslash artifacts (common LLM artifact)
    text = re.sub(r'\\\s*\\', ' ', text)  # \ \ or \  \
    text = re.sub(r'\\n\\n', '\n\n', text)  # Escaped newlines
    text = re.sub(r'\\+', '', text)  # Remaining standalone backslashes
    
    # 1. ChatML tags with angle brackets: <|im_start|>user, <|im_end|>, etc.
    text = re.sub(r'<\|im_start\|>\w*', ' ', text)
    text = re.sub(r'<\|im_end\|>', ' ', text)
    text = re.sub(r'<\|endoftext\|>', ' ', text)
    
    # 2. Numbered special tokens: <|reserved_special_token_N|>
    text = re.sub(r'<\|reserved_special_token_\d+\|>', ' ', text)
    
    # 3. Role markers: <|assistant|>, <|user|>, <|system|>
    text = re.sub(r'<\|(?:assistant|user|system)\|>', ' ', text)
    
    # 4. Partial/broken role markers: </assistant|>, <|assistant (no closing)
    text = re.sub(r'</(?:assistant|user|system)\|>', ' ', text)
    text = re.sub(r'<\|(?:assistant|user|system)(?!\|>)', ' ', text)
    
    # 5. Generic <|token|> format (catch-all)
    text = re.sub(r'<\|[^|>]+\|>', ' ', text)
    
    # 6. XML-style tags: <speaker ...>, etc.
    text = re.sub(r'<speaker[^>]*>', ' ', text)
    text = re.sub(r'</speaker>', ' ', text)
    
    # 7. Standard BOS/EOS tokens: <s>, </s>
    text = re.sub(r'</?s>', ' ', text)
    
    # 8. Pipe-wrapped tokens: |</s>|, |<s>|, etc.
    text = re.sub(r'\|</s>\|', ' ', text)
    text = re.sub(r'\|<s>\|', ' ', text)
    text = re.sub(r'\|<[^>]+>\|', ' ', text)  # Any |<token>| format
    
    # 9. Role prefixes that might appear
    text = re.sub(r'^\s*(user|assistant|system):\s*', '', text, flags=re.MULTILINE)
    
    # 10. Clean up excessive whitespace (but preserve single spaces between words)
    text = re.sub(r' {2,}', ' ', text)               # Multiple spaces → single space
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)   # Max 2 consecutive newlines
    
    # Only strip if explicitly requested (for final responses)
    return text.strip() if strip else text


def validate_single_turn_response(text: str) -> str:
    """
    Post-process LLM response to detect and truncate multi-turn patterns.
    
    Detects patterns where AI generates multiple conversation turns:
    - Question followed by answer in same response
    - Multiple distinct "paragraphs" that look like different speakers
    - Dialogue-style exchanges within the response
    
    Returns: Truncated response containing only the FIRST turn
    """
    lines = text.split('\n')
    cleaned_lines = []
    seen_question = False
    
    for line in lines:
        line_stripped = line.strip()
        
        # Skip empty lines
        if not line_stripped:
            cleaned_lines.append(line)
            continue
        
        # Detect question patterns
        if line_stripped.endswith('?'):
            if seen_question:
                # Second question = likely multi-turn, stop here
                log.warning(f"🛑 Multi-turn detected: Second question found. Truncating response.")
                break
            seen_question = True
        
        # Detect patterns that suggest user response (AI answering its own question)
        suspicious_starts = [
            "yeah,", "yes,", "no,", "well,", "actually,", "i think", "i feel",
            "that's", "it's", "i'm", "i've", "i was", "i had"
        ]
        if any(line_stripped.lower().startswith(start) for start in suspicious_starts):
            if seen_question:
                # AI asked question, now answering = multi-turn
                log.warning(f"🛑 Multi-turn detected: AI answering own question. Truncating response.")
                break
        
        cleaned_lines.append(line)
    
    result = '\n'.join(cleaned_lines).strip()
    
    # Additional check: If response has excessive length after first paragraph, truncate
    paragraphs = result.split('\n\n')
    if len(paragraphs) > 2:
        # Keep only first 2 paragraphs max
        log.warning(f"🛑 Multi-turn suspected: {len(paragraphs)} paragraphs detected. Keeping first 2.")
        result = '\n\n'.join(paragraphs[:2])
    
    return result


# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger("sparky-orchestrator-ws")

# ── Helpers for "advertised" host values in /health ────────────────────────────
def _best_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"

def _adv_host(bound_host: str, advertise_env: str) -> str:
    explicit = os.getenv(advertise_env)
    if explicit:
        return explicit
    if bound_host in ("0.0.0.0", "::", None, ""):
        return _best_ip()
    return bound_host

# ── Env → settings (all from .env) ─────────────────────────────────────────────
ORCH_HOST = os.getenv("ORCH_HOST", "0.0.0.0")
ORCH_PORT = int(os.getenv("ORCH_PORT", "8006"))

# Whisper
WHISPER_HOST = os.getenv("WHISPER_HOST", "127.0.0.1")
WHISPER_PORT = int(os.getenv("WHISPER_PORT", "8005"))
WHISPER_URL  = f"http://{WHISPER_HOST}:{WHISPER_PORT}/transcribe"

# TTS
TTS_HOST = os.getenv("VOICE_AI_HOST", "127.0.0.1")
TTS_PORT = int(os.getenv("VOICE_AI_PORT", "8004"))
TTS_WS   = f"ws://{TTS_HOST}:{TTS_PORT}/speak_stream"

# LLM
LLM_BASE  = os.getenv("LLM_PATH", "http://127.0.0.1:8000/v1").rstrip("/")
LLM_URL   = f"{LLM_BASE}/chat/completions"
LLM_MODEL = os.getenv("MODEL_NAME") or os.getenv("LLM_MODEL_NAME") or "Llama-3.1-8B-Lexi-Uncensored"
LLM_MODEL_SOURCE = "LLM_MODEL_NAME" if os.getenv("LLM_MODEL_NAME") else ("MODEL_NAME" if os.getenv("MODEL_NAME") else "default_fallback")
LLM_KEY   = os.getenv("OPENAI_API_KEY", "")

# Defaults
DEFAULT_VOICE = (os.getenv("VOICE_AI_DEFAULT_VOICE", "ara") or "ara").lower()
SAMPLE_RATE   = 24000
CHANNELS      = 1
SAMPLE_WIDTH  = 2

# 🆕 Conversation settings
CONVERSATION_SYSTEM_PROMPT = os.getenv(
    "CONVERSATION_SYSTEM_PROMPT",
    "You are Ara, a warm and friendly AI assistant. Be conversational and helpful. "
    "CRITICAL: Give ONE direct response, then STOP. Never continue with follow-up questions. "
    "Never pretend the user responded. Never generate multi-turn conversations. "
    "Keep responses brief (2-3 sentences). Answer the question, then wait for the user."
)
CONVERSATION_MAX_HISTORY = int(os.getenv("CONVERSATION_MAX_HISTORY", "20"))
CONVERSATION_MAX_TOKENS = int(os.getenv("CONVERSATION_MAX_TOKENS", "7000"))
AVG_TOKENS_PER_MESSAGE = int(os.getenv("AVG_TOKENS_PER_MESSAGE", "75"))

# Greeting/Goodbye messages (used for instant TTS responses)
GREETING_MESSAGE = os.getenv("GREETING_MESSAGE", "Yes? How can I help you?")
GOODBYE_MESSAGE = os.getenv("GOODBYE_MESSAGE", "Goodbye!")

# CORS
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",")] if os.getenv("CORS_ORIGINS") else ["*"]

log.info("Orchestrator v2 configured from .env")
log.info(f"  Whisper: {WHISPER_URL}")
log.info(f"  TTS WS : {TTS_WS}")
log.info(f"  LLM    : {LLM_URL} (model={LLM_MODEL})")
log.info(f"  Conversation: max_history={CONVERSATION_MAX_HISTORY}, max_tokens={CONVERSATION_MAX_TOKENS}")

# ── Session Management ─────────────────────────────────────────────────────────
class ConversationSession:
    """Represents a single conversation session with history."""
    def __init__(self, session_id: str, voice: str = DEFAULT_VOICE):
        self.session_id = session_id
        self.voice = voice
        self.history: List[dict] = []  # OpenAI format: [{"role": "user", "content": "..."}, ...]
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.metadata = {}
    
    def add_message(self, role: str, content: str):
        """Add a message to history and prune if needed."""
        self.history.append({"role": role, "content": content})
        self.last_activity = datetime.now()
        
        # Prune if exceeds max
        if len(self.history) > CONVERSATION_MAX_HISTORY:
            self.history = self.history[-CONVERSATION_MAX_HISTORY:]
            log.info(f"[{self.session_id}] Pruned history to {CONVERSATION_MAX_HISTORY} messages")
    
    def get_messages_for_llm(self) -> List[dict]:
        """Get messages formatted for LLM with system prompt."""
        messages = [{"role": "system", "content": CONVERSATION_SYSTEM_PROMPT}]
        messages.extend(self.history)
        return messages
    
    def clear_history(self):
        """Clear conversation history."""
        self.history = []
        log.info(f"[{self.session_id}] History cleared")

# Global session storage (in-memory for now)
sessions: Dict[str, ConversationSession] = {}

def get_or_create_session(session_id: Optional[str], voice: str) -> ConversationSession:
    """Get existing session or create new one."""
    if session_id and session_id in sessions:
        session = sessions[session_id]
        session.last_activity = datetime.now()
        log.info(f"[{session_id}] Resumed existing session")
        return session
    
    # Create new session
    new_id = str(uuid4())
    session = ConversationSession(new_id, voice)
    sessions[new_id] = session
    log.info(f"[{new_id}] Created new session")
    return session

# ── FastAPI app ────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Sparky Orchestrator v3.0", 
    version="3.0.0",
    description="Natural AI responses with disciplined single-turn enforcement (max_tokens=1000 + validator)"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Single httpx client
_client = httpx.AsyncClient(timeout=httpx.Timeout(60.0, read=60.0, connect=10.0))

# ── Helpers ────────────────────────────────────────────────────────────────────
def pcm_to_wav(pcm_bytes: bytes, sample_rate: int = 16000, channels: int = 1, sample_width: int = 2) -> bytes:
    """
    Convert raw PCM bytes to WAV format by adding proper WAV header.
    
    Args:
        pcm_bytes: Raw PCM audio data (int16)
        sample_rate: Sample rate in Hz (default: 16000)
        channels: Number of channels (default: 1 = mono)
        sample_width: Bytes per sample (default: 2 = 16-bit)
    
    Returns:
        Complete WAV file as bytes
    """
    import struct
    
    # Calculate sizes
    data_size = len(pcm_bytes)
    file_size = data_size + 36  # 44 byte header - 8 bytes
    
    # Build WAV header
    wav_header = struct.pack(
        '<4sI4s4sIHHIIHH4sI',
        b'RIFF',           # ChunkID
        file_size,         # ChunkSize
        b'WAVE',           # Format
        b'fmt ',           # Subchunk1ID
        16,                # Subchunk1Size (16 for PCM)
        1,                 # AudioFormat (1 = PCM)
        channels,          # NumChannels
        sample_rate,       # SampleRate
        sample_rate * channels * sample_width,  # ByteRate
        channels * sample_width,  # BlockAlign
        sample_width * 8,  # BitsPerSample
        b'data',           # Subchunk2ID
        data_size          # Subchunk2Size
    )
    
    return wav_header + pcm_bytes

@app.on_event("shutdown")
async def _shutdown():
    try:
        await _client.aclose()
    except Exception:
        pass

# ── Helpers ────────────────────────────────────────────────────────────────────
async def whisper_transcribe(wav_bytes: bytes) -> str:
    """
    POST to Whisper /transcribe.
    Converts raw PCM to WAV format if needed.
    """
    # Convert raw PCM to proper WAV format
    # Client sends: int16 PCM at 16kHz mono
    wav_data = pcm_to_wav(wav_bytes, sample_rate=16000, channels=1, sample_width=2)
    
    files = {"audio": ("audio.wav", wav_data, "audio/wav")}
    r = await _client.post(WHISPER_URL, files=files)
    if r.status_code == 404:
        files = {"file": ("audio.wav", wav_data, "audio/wav")}
        r = await _client.post(WHISPER_URL, files=files)
    if r.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Whisper failed: {r.text[:200]}")
    text = (r.json().get("text") or "").strip()
    if not text:
        raise HTTPException(status_code=502, detail="Whisper returned empty text")
    return text

async def llm_chat(messages: List[dict]) -> str:
    """Call LLM with full conversation history, return complete response."""
    headers = {"Content-Type": "application/json"}
    if LLM_KEY:
        headers["Authorization"] = f"Bearer {LLM_KEY}"
    
    payload = {
        "model": LLM_MODEL,
        "messages": messages,
        "temperature": 0.8,
        "max_tokens": 1000,  # Generous limit - let AI complete thoughts naturally
        "frequency_penalty": 0.3,
        # Aggressive stop sequences to prevent multi-turn
        "stop": [
            # Template tags
            "<|im_start|>user", "<|im_start|>", "<|im_end|>",
            "\nuser:", "\n\nuser:", "user:",
            # Aggressive paragraph break (ANY double newline forces stop)
            "\n\n\n",  # Triple newline
            # Conversational turn-taking patterns
            "\n\nHow about you", "\n\nWhat about you", "\n\nHave you",
            "\n\nDo you", "\n\nAre you", "\n\nWell,", "\n\nYeah,", 
            "\n\nActually,", "\n\nI was thinking", "\n\nI've been",
            "\n\nThat's", "\n\nI think", "\n\nI feel"
        ]
    }
    
    r = await _client.post(LLM_URL, headers=headers, json=payload)
    if r.status_code != 200:
        raise HTTPException(status_code=502, detail=f"LLM error: {r.text[:200]}")
    
    response = r.json()
    text = response['choices'][0]['message']['content']
    
    # Clean template tags
    text = clean_llm_response(text)
    
    # Validate and truncate multi-turn patterns
    text = validate_single_turn_response(text)
    
    return text

# ── Helper: Stream LLM with sentence-buffered TTS ────────────────────────────
async def stream_llm_with_tts(ws: WebSocket, messages: List[dict], session: ConversationSession) -> bool:
    """
    Stream LLM tokens, buffer into complete sentences, and send each sentence to TTS immediately.
    
    This achieves true end-to-end streaming:
    - LLM generates tokens in real-time
    - Tokens buffered until sentence boundary (. ! ? \n)
    - Complete sentences immediately sent to TTS
    - Audio starts playing while LLM still generating
    
    Returns True on success, False on error.
    """
    import re
    try:
        import websockets
    except Exception:
        await ws.send_text(json.dumps({"type": "error", "detail": "Missing websockets library"}))
        return False
    
    # Sentence boundary pattern
    sentence_end_pattern = re.compile(r'[.!?\n]')
    
    token_buffer = ""
    full_response = ""
    sentence_count = 0
    first_audio = True
    
    try:
        # Connect to TTS once at start
        async with websockets.connect(TTS_WS, max_size=None) as tts:
            # Initialize TTS stream
            await tts.send(json.dumps({
                "type": "start",
                "voice": session.voice,
                "rate": SAMPLE_RATE
            }))
            log.info(f"[{session.session_id}] TTS connection established")
            
            # Task to relay TTS audio to client
            async def relay_tts_audio():
                nonlocal first_audio
                try:
                    while True:
                        reply = await tts.recv()
                        
                        if isinstance(reply, (bytes, bytearray)):
                            # Binary audio chunk
                            await ws.send_bytes(reply)
                            if first_audio:
                                log.info(f"[{session.session_id}] 🎵 First audio chunk sent!")
                                first_audio = False
                        else:
                            # Metadata
                            try:
                                meta = json.loads(reply)
                                await ws.send_text(json.dumps(meta))
                                
                                if meta.get("event") == "eos":
                                    log.info(f"[{session.session_id}] TTS complete")
                                    break
                            except Exception:
                                pass
                except Exception as e:
                    log.error(f"[{session.session_id}] Error in TTS relay: {e}")
            
            # Start audio relay task
            relay_task = asyncio.create_task(relay_tts_audio())
            
            # Stream LLM tokens
            log.info(f"[{session.session_id}] Starting LLM stream...")
            async for token in llm_stream_generator(messages):
                # Clean template tags from token
                clean_token = clean_llm_response(token)
                
                # Skip empty tokens after cleaning
                if not clean_token:
                    continue
                
                token_buffer += clean_token
                full_response += clean_token
                
                # Check if we hit a sentence boundary
                if sentence_end_pattern.search(token_buffer):
                    # Extract complete sentences
                    sentences = re.split(r'([.!?\n]+)', token_buffer)
                    
                    # Process complete sentences (everything except last fragment)
                    complete_text = ""
                    for i in range(0, len(sentences) - 1, 2):
                        if i + 1 < len(sentences):
                            complete_text += sentences[i] + sentences[i + 1]
                    
                    # Keep incomplete fragment in buffer
                    token_buffer = sentences[-1] if len(sentences) % 2 == 1 else ""
                    
                    if complete_text.strip():
                        sentence_count += 1
                        log.info(f"[{session.session_id}] 📤 Sentence #{sentence_count}: '{complete_text[:50]}...'")
                        
                        # Send to TTS immediately
                        await tts.send(json.dumps({
                            "type": "text",
                            "data": complete_text.strip()
                        }))
            
            # Send any remaining text in buffer
            if token_buffer.strip():
                sentence_count += 1
                log.info(f"[{session.session_id}] 📤 Final fragment: '{token_buffer[:50]}...'")
                await tts.send(json.dumps({
                    "type": "text",
                    "data": token_buffer.strip()
                }))
            
            # Finalize TTS
            await tts.send(json.dumps({"type": "final"}))
            log.info(f"[{session.session_id}] ✓ LLM complete. Sent {sentence_count} sentence(s)")
            
            # Wait for audio relay to complete
            await relay_task
        
        # Clean the complete response before saving (strip final whitespace)
        full_response = clean_llm_response(full_response, strip=True)
        
        # Validate and truncate multi-turn patterns
        full_response = validate_single_turn_response(full_response)
        
        # Send complete response text to client
        await ws.send_text(json.dumps({
            "type": "meta",
            "event": "llm_response",
            "text": full_response
        }))
        
        # Add to conversation history
        session.add_message("assistant", full_response)
        log.info(f"[{session.session_id}] Full response: '{full_response[:100]}...'")
        
        return True
        
    except Exception as e:
        log.error(f"[{session.session_id}] Error in streaming: {e}", exc_info=True)
        await ws.send_text(json.dumps({
            "type": "error",
            "detail": f"Streaming error: {str(e)[:100]}"
        }))
        return False


async def llm_stream_generator(messages: List[dict]) -> AsyncIterator[str]:
    """
    Generator that yields LLM tokens one at a time.
    Wrapper around llm_stream() for cleaner API.
    """
    async for token in llm_stream_from_messages(messages):
        yield token


async def llm_stream_from_messages(messages: List[dict]) -> AsyncIterator[str]:
    """Stream tokens from OpenAI-compatible /chat/completions (SSE)."""
    headers = {"Content-Type": "application/json"}
    if LLM_KEY:
        headers["Authorization"] = f"Bearer {LLM_KEY}"

    payload = {
        "model": LLM_MODEL,
        "stream": True,
        "temperature": 0.8,
        "max_tokens": 1000,  # Generous limit - let AI complete thoughts naturally
        "frequency_penalty": 0.3,
        "messages": messages,
        # Aggressive stop sequences to prevent multi-turn
        "stop": [
            # Template tags
            "<|im_start|>user", "<|im_start|>", "<|im_end|>",
            "\nuser:", "\n\nuser:", "user:",
            # Aggressive paragraph break
            "\n\n\n",  # Triple newline
            # Conversational turn-taking patterns
            "\n\nHow about you", "\n\nWhat about you", "\n\nHave you",
            "\n\nDo you", "\n\nAre you", "\n\nWell,", "\n\nYeah,",
            "\n\nActually,", "\n\nI was thinking", "\n\nI've been",
            "\n\nThat's", "\n\nI think", "\n\nI feel"
        ]
    }

    finish_reason = None  # Track why generation stopped

    async with _client.stream("POST", LLM_URL, headers=headers, json=payload) as r:
        if r.status_code != 200:
            body = await r.aread()
            raise HTTPException(status_code=502, detail=f"LLM error {r.status_code}: {body[:300]!r}")
        async for line in r.aiter_lines():
            if not line or not line.startswith("data:"):
                continue
            chunk = line[5:].strip()
            if chunk == "[DONE]":
                break
            try:
                data = json.loads(chunk)
                delta = (data.get("choices") or [{}])[0].get("delta", {})
                text = delta.get("content")
                if text:
                    yield text
                
                # Capture finish_reason for debugging
                choice = (data.get("choices") or [{}])[0]
                if "finish_reason" in choice and choice["finish_reason"]:
                    finish_reason = choice["finish_reason"]
            except Exception:
                continue
    
    # Log finish_reason to diagnose why generation stopped
    if finish_reason:
        log.info(f"🛑 LLM generation finished: reason={finish_reason}")
    else:
        log.warning("🛑 LLM generation finished without finish_reason")


# ── Helper: Stream TTS audio ──────────────────────────────────────────────────
async def stream_tts_to_client(ws: WebSocket, text: str, voice: str, session_id: str):
    """
    Helper function to stream TTS audio to client.
    Used for both conversation responses AND greeting/goodbye.
    """
    log.info(f"[{session_id}] Streaming TTS for text: '{text[:50]}...'")
    
    try:
        import websockets
    except Exception:
        await ws.send_text(json.dumps({"type": "error", "detail": "Missing websockets library"}))
        return False
    
    try:
        async with websockets.connect(TTS_WS, max_size=None) as tts:
            # Start TTS
            await tts.send(json.dumps({"type": "start", "voice": voice, "rate": SAMPLE_RATE}))
            await tts.send(json.dumps({"type": "text", "data": text}))
            await tts.send(json.dumps({"type": "final"}))
            
            # Relay TTS audio to client
            while True:
                reply = await tts.recv()
                
                if isinstance(reply, (bytes, bytearray)):
                    # Binary audio chunk
                    await ws.send_bytes(reply)
                else:
                    # Metadata (provider, ttfa, etc.)
                    try:
                        meta = json.loads(reply)
                        # Forward all metadata
                        await ws.send_text(json.dumps(meta))
                        
                        if meta.get("event") == "eos":
                            log.info(f"[{session_id}] TTS complete")
                            break
                    except Exception:
                        pass
        return True
    except Exception as e:
        log.error(f"[{session_id}] TTS streaming error: {e}")
        await ws.send_text(json.dumps({"type": "error", "detail": f"TTS error: {str(e)[:100]}"}))
        return False

# ── 🆕 NEW: /ws/conversation - Full conversation management ───────────────────
@app.websocket("/ws/conversation")
async def conversation(ws: WebSocket):
    """
    🧠 CONVERSATION ENDPOINT - Infinite message handler with isolated text/audio modes
    
    Client → Server:
      {"type": "start", "voice": "ara", "session_id": "uuid-optional"}
      {"type": "greeting"}  # Optional: play greeting message
      {"type": "audio", "data": "<base64-wav>"}  # Start audio message
      {"type": "final"}  # End audio message
      {"type": "text_chat", "text": "user message"}  # 🆕 Text chat mode (isolated)
      {"type": "goodbye"}  # Optional: play goodbye message
      {"type": "clear_history"}  # Optional: clear conversation
    
    Server → Client:
      {"type": "meta", "event": "session_id", "value": "uuid"}
      {"type": "meta", "event": "greeting"}
      {"type": "meta", "event": "goodbye"}
      {"type": "meta", "event": "transcription", "text": "..."}
      {"type": "meta", "event": "thinking"}
      {"type": "text_token", "token": "..."}  # 🆕 Token streaming for text chat
      {"type": "text_response", "text": "..."}  # 🆕 Complete text response
      {"type": "meta", "event": "provider", "value": "xtts"}
      {"type": "meta", "event": "ttfa_ms", "value": 123}
      <binary PCM16 audio chunks>
      {"type": "done"}
    """
    await ws.accept()
    log.info("[/ws/conversation] Client connected")
    
    session: Optional[ConversationSession] = None
    voice = DEFAULT_VOICE
    
    try:
        # ═══════════════════════════════════════════════════════════════════════
        # PHASE 1: Initial Setup - Receive START message
        # ═══════════════════════════════════════════════════════════════════════
        log.info("[/ws/conversation] Waiting for start message...")
        start_msg = await ws.receive_text()
        start = json.loads(start_msg)
        
        if start.get("type") != "start":
            await ws.send_text(json.dumps({"type": "error", "detail": "Expected 'start'"}))
            await ws.close()
            return
        
        voice = (start.get("voice") or DEFAULT_VOICE).lower()
        session_id = start.get("session_id")
        
        # Get or create session
        session = get_or_create_session(session_id, voice)
        
        # Send session ID back
        await ws.send_text(json.dumps({
            "type": "meta",
            "event": "session_id",
            "value": session.session_id
        }))
        log.info(f"[{session.session_id}] Session active, voice={voice}")
        
        # ═══════════════════════════════════════════════════════════════════════
        # PHASE 2: INFINITE MESSAGE LOOP - Handle all message types independently
        # ═══════════════════════════════════════════════════════════════════════
        while True:
            msg = await ws.receive()
            
            # ─────────────────────────────────────────────────────────────────
            # Check for disconnect message (prevents RuntimeError)
            # ─────────────────────────────────────────────────────────────────
            if msg.get("type") == "websocket.disconnect":
                log.info(f"[{session.session_id}] Client disconnected (disconnect message received)")
                break
            
            # ─────────────────────────────────────────────────────────────────
            # Handle text-based messages
            # ─────────────────────────────────────────────────────────────────
            if "text" in msg:
                obj = json.loads(msg["text"])
                msg_type = obj.get("type")
                
                # ═════════════════════════════════════════════════════════════
                # TEXT CHAT MODE - Completely isolated, no audio code
                # ═════════════════════════════════════════════════════════════
                if msg_type == "text_chat":
                    text = obj.get("text", "").strip()
                    if not text:
                        await ws.send_text(json.dumps({"type": "error", "detail": "Empty text"}))
                        continue
                    
                    log.info(f"[{session.session_id}] 💬 Text chat: '{text[:50]}...'")
                    
                    # Add user message to history
                    session.add_message("user", text)
                    
                    # Stream LLM response token-by-token
                    log.info(f"[{session.session_id}] Streaming text response...")
                    await ws.send_text(json.dumps({"type": "meta", "event": "thinking"}))
                    
                    messages = session.get_messages_for_llm()
                    full_response = ""
                    
                    try:
                        async for token in llm_stream_generator(messages):
                            # Clean template tags from token before sending
                            clean_token = clean_llm_response(token)
                            
                            # Only send non-empty tokens
                            if clean_token:
                                await ws.send_text(json.dumps({
                                    "type": "text_token",
                                    "token": clean_token
                                }))
                                full_response += clean_token
                        
                        # Clean the complete response before saving to history (strip final whitespace)
                        full_response = clean_llm_response(full_response, strip=True)
                        
                        # Add assistant response to history
                        session.add_message("assistant", full_response)
                        
                        # Send final complete response
                        await ws.send_text(json.dumps({
                            "type": "text_response",
                            "text": full_response
                        }))
                        
                        log.info(f"[{session.session_id}] ✅ Text response complete: '{full_response[:50]}...'")
                        
                    except Exception as e:
                        log.error(f"[{session.session_id}] ❌ Text chat error: {e}", exc_info=True)
                        await ws.send_text(json.dumps({"type": "error", "detail": str(e)[:200]}))
                    
                    # Send done
                    await ws.send_text(json.dumps({"type": "done"}))
                    continue  # Back to message loop
                
                # ═════════════════════════════════════════════════════════════
                # AUDIO MODE - Completely isolated, handles full audio pipeline
                # ═════════════════════════════════════════════════════════════
                elif msg_type == "audio":
                    log.info(f"[{session.session_id}] 🎤 Audio message started")
                    
                    # Collect initial audio chunk
                    audio_buffer = io.BytesIO()
                    audio_data = base64.b64decode(obj.get("data", ""))
                    audio_buffer.write(audio_data)
                    
                    # Collect remaining audio chunks until "final"
                    while True:
                        chunk_msg = await ws.receive()
                        
                        if "text" in chunk_msg:
                            chunk_obj = json.loads(chunk_msg["text"])
                            chunk_type = chunk_obj.get("type")
                            
                            if chunk_type == "audio":
                                # Additional audio chunk
                                audio_data = base64.b64decode(chunk_obj.get("data", ""))
                                audio_buffer.write(audio_data)
                            
                            elif chunk_type == "final":
                                # Audio complete
                                log.info(f"[{session.session_id}] Audio finalized")
                                break
                        
                        elif "bytes" in chunk_msg:
                            # Binary audio chunk
                            audio_buffer.write(chunk_msg["bytes"])
                    
                    # Transcribe audio
                    log.info(f"[{session.session_id}] Transcribing...")
                    audio_bytes = audio_buffer.getvalue()
                    
                    if len(audio_bytes) < 1000:
                        await ws.send_text(json.dumps({"type": "error", "detail": "Audio too short"}))
                        continue
                    
                    transcribed_text = await whisper_transcribe(audio_bytes)
                    log.info(f"[{session.session_id}] 📝 Transcribed: '{transcribed_text[:50]}...'")
                    
                    # Send transcription
                    await ws.send_text(json.dumps({
                        "type": "meta",
                        "event": "transcription",
                        "text": transcribed_text
                    }))
                    
                    # Add to history
                    session.add_message("user", transcribed_text)
                    
                    # Stream LLM response with TTS
                    log.info(f"[{session.session_id}] Streaming LLM → TTS response...")
                    await ws.send_text(json.dumps({"type": "meta", "event": "thinking"}))
                    
                    messages = session.get_messages_for_llm()
                    success = await stream_llm_with_tts(ws, messages, session)
                    
                    if not success:
                        log.error(f"[{session.session_id}] ❌ Audio response failed")
                        continue
                    
                    # Send done
                    await ws.send_text(json.dumps({"type": "done"}))
                    log.info(f"[{session.session_id}] ✅ Audio conversation turn complete")
                    continue  # Back to message loop
                
                # ═════════════════════════════════════════════════════════════
                # GREETING - Play greeting message
                # ═════════════════════════════════════════════════════════════
                elif msg_type == "greeting":
                    log.info(f"[{session.session_id}] 👋 Playing greeting")
                    await ws.send_text(json.dumps({"type": "meta", "event": "greeting"}))
                    
                    greeting_text = os.getenv("GREETING_MESSAGE", "Yes? How can I help you?")
                    await stream_tts_to_client(ws, greeting_text, voice, session.session_id)
                    await ws.send_text(json.dumps({"type": "done"}))
                    continue
                
                # ═════════════════════════════════════════════════════════════
                # GOODBYE - Play goodbye and end session
                # ═════════════════════════════════════════════════════════════
                elif msg_type == "goodbye":
                    log.info(f"[{session.session_id}] 👋 Playing goodbye")
                    await ws.send_text(json.dumps({"type": "meta", "event": "goodbye"}))
                    
                    goodbye_text = os.getenv("GOODBYE_MESSAGE", "Goodbye!")
                    await stream_tts_to_client(ws, goodbye_text, voice, session.session_id)
                    await ws.send_text(json.dumps({"type": "done"}))
                    
                    # Close connection after goodbye
                    await ws.close()
                    return
                
                # ═════════════════════════════════════════════════════════════
                # CLEAR HISTORY - Clear conversation history
                # ═════════════════════════════════════════════════════════════
                elif msg_type == "clear_history":
                    log.info(f"[{session.session_id}] 🗑️ Clearing history")
                    session.clear_history()
                    await ws.send_text(json.dumps({
                        "type": "meta",
                        "event": "history_cleared"
                    }))
                    continue
                
                # ═════════════════════════════════════════════════════════════
                # UNKNOWN MESSAGE TYPE
                # ═════════════════════════════════════════════════════════════
                else:
                    log.warning(f"[{session.session_id}] ⚠️ Unknown message type: {msg_type}")
                    continue
            
            # ─────────────────────────────────────────────────────────────────
            # Handle binary messages (shouldn't happen outside audio collection)
            # ─────────────────────────────────────────────────────────────────
            elif "bytes" in msg:
                log.warning(f"[{session.session_id}] ⚠️ Unexpected binary message outside audio mode")
                continue
        
    except WebSocketDisconnect:
        log.info(f"[{session.session_id if session else 'unknown'}] Client disconnected")
    except RuntimeError as e:
        # This happens when receive() is called after disconnect
        if "disconnect message has been received" in str(e):
            log.info(f"[{session.session_id if session else 'unknown'}] Client disconnected (late detection)")
        else:
            log.error(f"[{session.session_id if session else 'unknown'}] ❌ RuntimeError: {e}", exc_info=True)
    except Exception as e:
        log.error(f"[{session.session_id if session else 'unknown'}] ❌ Error: {e}", exc_info=True)
        try:
            await ws.send_text(json.dumps({"type": "error", "detail": str(e)[:200]}))
        except Exception:
            pass
    finally:
        try:
            await ws.close()
        except Exception:
            pass

# ── OLD ENDPOINTS (Keep for compatibility) ────────────────────────────────────

async def llm_stream(prompt: str, system_prompt: Optional[str]) -> AsyncIterator[str]:
    """Stream tokens from OpenAI-compatible /chat/completions (SSE)."""
    headers = {"Content-Type": "application/json"}
    if LLM_KEY:
        headers["Authorization"] = f"Bearer {LLM_KEY}"

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload = {"model": LLM_MODEL, "stream": True, "temperature": 0.7, "messages": messages}

    async with _client.stream("POST", LLM_URL, headers=headers, json=payload) as r:
        if r.status_code != 200:
            body = await r.aread()
            raise HTTPException(status_code=502, detail=f"LLM error {r.status_code}: {body[:300]!r}")
        async for line in r.aiter_lines():
            if not line or not line.startswith("data:"):
                continue
            chunk = line[5:].strip()
            if chunk == "[DONE]":
                break
            try:
                data = json.loads(chunk)
                delta = (data.get("choices") or [{}])[0].get("delta", {})
                text = delta.get("content")
                if text:
                    yield text
            except Exception:
                continue

@app.websocket("/ws/chat")
async def chat(ws: WebSocket):
    """Legacy endpoint - Audio → Whisper → LLM(stream) → TTS → audio"""
    await ws.accept()
    log.info("[/ws/chat] Client connected (legacy endpoint)")
    # ... (keep existing implementation)
    await ws.close()

@app.websocket("/ws/text")
async def text_bypass(ws: WebSocket):
    """Legacy endpoint - Text → TTS → audio"""
    await ws.accept()
    log.info("[/ws/text] Client connected (legacy endpoint)")
    
    try:
        start = json.loads(await ws.receive_text())
        if start.get("type") != "start":
            await ws.send_text(json.dumps({"type":"error","detail":"Expected 'start'"}))
            await ws.close()
            return
        voice = (start.get("voice") or DEFAULT_VOICE).lower()

        try:
            import websockets
        except Exception:
            await ws.send_text(json.dumps({"type":"error","detail":"Missing websockets"}))
            await ws.close()
            return

        async with websockets.connect(TTS_WS, max_size=None) as tts:
            await tts.send(json.dumps({"type":"start","voice":voice,"rate":SAMPLE_RATE}))

            while True:
                msg = await ws.receive_text()
                obj = json.loads(msg)
                typ = obj.get("type")
                if typ == "text":
                    await tts.send(json.dumps({"type":"text","data":obj.get("data","")}))
                elif typ == "final":
                    await tts.send(json.dumps({"type":"final"}))
                    break

            while True:
                reply = await tts.recv()
                if isinstance(reply, (bytes, bytearray)):
                    await ws.send_bytes(reply)
                else:
                    try:
                        meta = json.loads(reply)
                        if meta.get("event") == "provider":
                            await ws.send_text(json.dumps(meta))
                        elif meta.get("event") == "ttfa_ms":
                            await ws.send_text(json.dumps(meta))
                        elif meta.get("event") == "eos":
                            await ws.send_text(json.dumps({"type":"done"}))
                            break
                    except Exception:
                        pass
    except WebSocketDisconnect:
        pass
    except Exception as e:
        log.error(f"[/ws/text] Error: {e}", exc_info=True)
        try:
            await ws.send_text(json.dumps({"type":"error","detail":str(e)[:200]}))
        except Exception:
            pass
    finally:
        await ws.close()

# ── Health ─────────────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    adv_tts_host = _adv_host(TTS_HOST, "TTS_ADVERTISE_HOST")
    adv_wh_host  = _adv_host(WHISPER_HOST, "WHISPER_ADVERTISE_HOST")
    return {
        "ok": True,
        "version": "3.0.0",
        "tts_ws": f"ws://{adv_tts_host}:{TTS_PORT}/speak_stream",
        "whisper": f"http://{adv_wh_host}:{WHISPER_PORT}/transcribe",
        "llm": {"url": LLM_URL, "model": LLM_MODEL, "source": LLM_MODEL_SOURCE},
        "defaults": {"voice": DEFAULT_VOICE, "rate": SAMPLE_RATE},
        "conversation": {
            "max_history": CONVERSATION_MAX_HISTORY,
            "max_tokens": CONVERSATION_MAX_TOKENS,
            "active_sessions": len(sessions)
        },
        "endpoints": {
            "conversation": "/ws/conversation - Infinite message handler with isolated text/audio modes",
            "chat": "/ws/chat - Legacy audio chat",
            "text": "/ws/text - Legacy text-to-speech"
        }
    }

@app.get("/")
async def root():
    return {
        "service": "Sparky Orchestrator v3.0 (Natural AI with Single-Turn Discipline)",
        "version": "3.0.0",
        "features": [
            "🧠 Server-side conversation management",
            "💬 Persistent conversation history",
            "🎤 Full audio → text → LLM → audio pipeline",
            "⚡ WebSocket streaming",
            "🔄 Session resumption",
            "⚡ Real-time token streaming",
            "🎯 Isolated text/audio modes (NEW!)"
        ],
        "endpoints": {
            "/ws/conversation": "Infinite message handler - text and audio fully isolated",
            "/ws/chat": "Legacy audio chat",
            "/ws/text": "Legacy text bypass",
            "/health": "Service health"
        }
    }

# ── Session cleanup (background task) ─────────────────────────────────────────
@app.on_event("startup")
async def start_cleanup_task():
    """Background task to clean up old sessions."""
    async def cleanup():
        while True:
            await asyncio.sleep(300)  # Every 5 minutes
            now = datetime.now()
            to_remove = []
            for sid, session in sessions.items():
                # Remove sessions inactive for 1 hour
                if (now - session.last_activity).seconds > 3600:
                    to_remove.append(sid)
            
            for sid in to_remove:
                del sessions[sid]
                log.info(f"[{sid}] Session cleaned up (inactive)")
            
            if to_remove:
                log.info(f"Cleaned up {len(to_remove)} inactive sessions")
    
    asyncio.create_task(cleanup())

# ── Main ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    log.info("="*60)
    log.info("Sparky Orchestrator v3.0 - Natural AI with Single-Turn Discipline")
    log.info(f"Listening on: {ORCH_HOST}:{ORCH_PORT}")
    log.info("="*60)
    uvicorn.run(app, host=ORCH_HOST, port=ORCH_PORT, log_level="info")
