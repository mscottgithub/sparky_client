import asyncio, json, os
import numpy as np
import sounddevice as sd
import websockets

TTS_HOST = "10.6.1.15"
TTS_PORT = int(os.getenv("VOICE_AI_PORT", "8004"))
VOICE    = (os.getenv("VOICE_AI_DEFAULT_VOICE", "ara") or "ara").lower()
URI      = f"ws://{TTS_HOST}:{TTS_PORT}/speak_stream"

async def main():
    print(f"Connecting to {URI} …")
    async with websockets.connect(URI, max_size=None) as ws:
        await ws.send(json.dumps({"type": "start", "voice": VOICE, "rate": 24000}))
        await ws.send(json.dumps({"type": "text", "data": "Direct TTS streaming test from Windows."}))
        await ws.send(json.dumps({"type": "final"}))

        out = sd.OutputStream(samplerate=24000, channels=1, dtype="int16", blocksize=2048)
        out.start()
        try:
            while True:
                msg = await ws.recv()
                if isinstance(msg, (bytes, bytearray)):
                    out.write(np.frombuffer(msg, dtype=np.int16))
                else:
                    try:
                        obj = json.loads(msg)
                    except Exception:
                        print("TEXT:", msg); continue
                    if obj.get("type") == "error":
                        print("TTS ERROR:", obj.get("detail"))
                    if obj.get("event") == "eos":
                        print("EOS from TTS.")
                        break
        finally:
            out.stop(); out.close()

if __name__ == "__main__":
    asyncio.run(main())
