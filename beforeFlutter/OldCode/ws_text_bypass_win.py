import asyncio, json, os, sys
import numpy as np
import sounddevice as sd
import websockets

ORCH_HOST = "10.6.1.15"
ORCH_PORT = int(os.getenv("ORCH_PORT", "8006"))
VOICE     = (os.getenv("VOICE_AI_DEFAULT_VOICE", "ara") or "ara").lower()
URI       = f"ws://{ORCH_HOST}:{ORCH_PORT}/ws/text"

TEXT = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Hello from Windows. Streaming test."

async def main():
    print(f"Connecting to {URI} …")
    print(f"Mode: LOW-LATENCY AUDIO PLAYBACK")
    
    try:
        async with websockets.connect(URI, max_size=None) as ws:
            await ws.send(json.dumps({"type": "start", "voice": VOICE}))
            print(f"Sending: '{TEXT}'")
            await ws.send(json.dumps({"type": "text", "data": TEXT}))
            await ws.send(json.dumps({"type": "final"}))

            # 🚀 CRITICAL: Low-latency audio settings
            # - Small blocksize (faster response)
            # - Request low latency from driver
            # - prime=True helps some systems start faster
            
            out = sd.OutputStream(
                samplerate=24000,
                channels=1,
                dtype="int16",
                blocksize=480,      # 20ms blocks (was 2048 = 85ms)
                latency='low',      # Request low-latency mode
                prime_output_buffers_using_stream_callback=False
            )
            
            out.start()
            print("🔊 Audio output ready")
            
            first_audio = False
            provider = None  # Track provider
            
            try:
                while True:
                    msg = await ws.recv()
                    
                    if isinstance(msg, (bytes, bytearray)):
                        if not first_audio:
                            print("⚡ PLAYING FIRST AUDIO NOW!")
                            first_audio = True
                        
                        # Write immediately - no buffering
                        audio = np.frombuffer(msg, dtype=np.int16)
                        out.write(audio)
                        
                    else:
                        try:
                            obj = json.loads(msg)
                        except Exception:
                            continue
                        
                        # 🎤 NEW: Display provider
                        if obj.get("event") == "provider":
                            provider = obj.get("value", "unknown")
                            print(f"🎤 TTS Provider: {provider.upper()}")
                        elif obj.get("event") == "ttfa_ms":
                            print(f"⚡ Server TTFA: {obj.get('value')} ms")
                        elif obj.get("type") == "done":
                            print("✓ Audio complete")
                            if provider:
                                print(f"   (Powered by {provider.upper()})")
                            break
            finally:
                out.stop()
                out.close()
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
