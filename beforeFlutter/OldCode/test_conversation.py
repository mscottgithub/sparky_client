#!/usr/bin/env python3
"""
Test Client for /ws/conversation endpoint
Simulates tray client behavior but simplified for testing
"""
import asyncio
import json
import base64
import sys
import os
import wave

import websockets

ORCH_HOST = "10.6.1.15"
ORCH_PORT = 8006
URI = f"ws://{ORCH_HOST}:{ORCH_PORT}/ws/conversation"

async def test_conversation():
    """Test the new conversation endpoint."""
    print(f"🔌 Connecting to {URI}...")
    
    try:
        async with websockets.connect(URI, max_size=None) as ws:
            # 1. Send START
            print("📤 Sending start message...")
            await ws.send(json.dumps({
                "type": "start",
                "voice": "ara",
                # "session_id": "test-session-123"  # Optional: resume existing
            }))
            
            # 2. Simulate sending audio file
            print("📤 Sending audio file...")
            
            # For testing, we need a real WAV file
            # In real usage, this would be live audio from microphone
            test_audio_path = sys.argv[1] if len(sys.argv) > 1 else None
            
            if not test_audio_path or not os.path.exists(test_audio_path):
                print("❌ Usage: python test_conversation.py <audio.wav>")
                print("   Please provide a WAV file to test with")
                return
            
            # Read audio file and encode as base64
            with open(test_audio_path, "rb") as f:
                audio_data = f.read()
            
            # Send audio in chunks (simulating real-time recording)
            chunk_size = 4096
            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i+chunk_size]
                encoded = base64.b64encode(chunk).decode('utf-8')
                await ws.send(json.dumps({
                    "type": "audio",
                    "data": encoded
                }))
            
            print(f"✓ Sent {len(audio_data)} bytes of audio")
            
            # 3. Send FINAL
            print("📤 Sending final message...")
            await ws.send(json.dumps({"type": "final"}))
            
            # 4. Receive responses
            print("👂 Listening for responses...")
            session_id = None
            transcription = None
            llm_response = None
            provider = None
            audio_received = 0
            audio_chunks = []  # Collect audio for saving
            
            while True:
                msg = await ws.recv()
                
                if isinstance(msg, (bytes, bytearray)):
                    # Binary audio data - collect it
                    audio_chunks.append(bytes(msg))
                    audio_received += len(msg)
                    if audio_received % 10000 == 0:
                        print(f"  🔊 Received {audio_received} bytes of audio...")
                else:
                    # Text message (metadata)
                    try:
                        obj = json.loads(msg)
                        msg_type = obj.get("type")
                        event = obj.get("event")
                        
                        if event == "session_id":
                            session_id = obj.get("value")
                            print(f"✓ Session ID: {session_id}")
                        
                        elif event == "transcription":
                            transcription = obj.get("text")
                            print(f"✓ Transcription: '{transcription}'")
                        
                        elif event == "thinking":
                            print("🤔 LLM is thinking...")
                        
                        elif event == "llm_response":
                            llm_response = obj.get("text")
                            print(f"✓ LLM Response: '{llm_response}'")
                        
                        elif event == "provider":
                            provider = obj.get("value")
                            print(f"🎤 TTS Provider: {provider.upper()}")
                        
                        elif event == "ttfa_ms":
                            ttfa = obj.get("value")
                            print(f"⚡ Time to First Audio: {ttfa}ms")
                        
                        elif msg_type == "done":
                            print("✓ Conversation turn complete!")
                            break
                        
                        elif msg_type == "error":
                            print(f"❌ Error: {obj.get('detail')}")
                            break
                    
                    except json.JSONDecodeError:
                        pass
            
            print(f"\n📊 Summary:")
            print(f"  Session ID: {session_id}")
            print(f"  Transcription: {transcription}")
            print(f"  LLM Response: {llm_response}")
            print(f"  Provider: {provider}")
            print(f"  Audio received: {audio_received} bytes")
            
            # Save audio as proper WAV file
            if audio_chunks:
                output_file = "test_output.wav"
                raw_audio = b''.join(audio_chunks)
                
                # Write WAV file with proper headers
                # Audio format: 24000 Hz, mono, 16-bit PCM
                with wave.open(output_file, 'wb') as wav_file:
                    wav_file.setnchannels(1)  # Mono
                    wav_file.setsampwidth(2)  # 16-bit = 2 bytes
                    wav_file.setframerate(24000)  # Sample rate
                    wav_file.writeframes(raw_audio)
                
                print(f"  💾 Audio saved to: {output_file}")
                print(f"     Format: 24000 Hz, mono, 16-bit PCM")
                print(f"     Duration: {len(raw_audio) / (24000 * 2):.2f} seconds")
                print(f"     Play with: ffplay {output_file}")
            
            print("\n✅ Test complete!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_conversation())
