import asyncio, json, os, sys, time
import numpy as np
import sounddevice as sd
import websockets

ORCH_HOST = "10.6.1.15"
ORCH_PORT = int(os.getenv("ORCH_PORT", "8006"))
VOICE     = (os.getenv("VOICE_AI_DEFAULT_VOICE", "ara") or "ara").lower()
URI       = f"ws://{ORCH_HOST}:{ORCH_PORT}/ws/text"

TEXT = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Hello from Windows. Streaming test."

async def main():
    print(f"\n{'='*60}")
    print("PERFORMANCE PROFILING TEST")
    print(f"{'='*60}")
    print(f"Connecting to {URI}")
    
    timings = {}
    
    try:
        t_start = time.time()
        
        async with websockets.connect(URI, max_size=None) as ws:
            t_connected = time.time()
            timings['connection'] = (t_connected - t_start) * 1000
            
            await ws.send(json.dumps({"type": "start", "voice": VOICE}))
            t_start_sent = time.time()
            
            await ws.send(json.dumps({"type": "text", "data": TEXT}))
            t_text_sent = time.time()
            timings['text_send'] = (t_text_sent - t_start_sent) * 1000
            
            await ws.send(json.dumps({"type": "final"}))
            t_final_sent = time.time()
            timings['final_send'] = (t_final_sent - t_text_sent) * 1000
            
            print(f"\n📊 SEND TIMINGS:")
            print(f"  Connection: {timings['connection']:.0f}ms")
            print(f"  Text send:  {timings['text_send']:.0f}ms")
            print(f"  Final send: {timings['final_send']:.0f}ms")
            print(f"  Total sent: {(t_final_sent - t_start) * 1000:.0f}ms")

            out = sd.OutputStream(samplerate=24000, channels=1, dtype="int16", blocksize=2048)
            out.start()
            
            first_audio = None
            first_meta = None
            ttfa_reported = None
            audio_chunks = 0
            
            try:
                while True:
                    t_recv = time.time()
                    msg = await ws.recv()
                    
                    if isinstance(msg, (bytes, bytearray)):
                        if first_audio is None:
                            first_audio = t_recv
                            actual_ttfa = (first_audio - t_start) * 1000
                            print(f"\n🎵 FIRST AUDIO RECEIVED:")
                            print(f"  Time from start: {actual_ttfa:.0f}ms")
                            if ttfa_reported:
                                print(f"  Server reported:  {ttfa_reported:.0f}ms")
                                print(f"  Network overhead: {actual_ttfa - ttfa_reported:.0f}ms")
                        
                        audio_chunks += 1
                        out.write(np.frombuffer(msg, dtype=np.int16))
                    else:
                        if first_meta is None:
                            first_meta = t_recv
                            timings['first_meta'] = (first_meta - t_start) * 1000
                        
                        try:
                            obj = json.loads(msg)
                        except Exception:
                            continue
                        
                        if obj.get("event") == "ttfa_ms":
                            ttfa_reported = obj.get('value')
                            print(f"\n⚡ SERVER TTFA: {ttfa_reported}ms")
                        elif obj.get("type") == "done":
                            t_done = time.time()
                            total_time = (t_done - t_start) * 1000
                            audio_duration = (t_done - first_audio) * 1000 if first_audio else 0
                            
                            print(f"\n✓ COMPLETE:")
                            print(f"  Total time:     {total_time:.0f}ms")
                            print(f"  Audio duration: {audio_duration:.0f}ms")
                            print(f"  Audio chunks:   {audio_chunks}")
                            
                            print(f"\n{'='*60}")
                            print("BREAKDOWN:")
                            print(f"{'='*60}")
                            print(f"  1. Connection:        {timings.get('connection', 0):.0f}ms")
                            print(f"  2. Send messages:     {timings.get('text_send', 0) + timings.get('final_send', 0):.0f}ms")
                            print(f"  3. Wait for audio:    {(first_audio - t_final_sent) * 1000 if first_audio else 0:.0f}ms  ← CRITICAL")
                            print(f"  4. Audio streaming:   {audio_duration:.0f}ms")
                            print(f"{'='*60}\n")
                            break
            finally:
                out.stop(); out.close()
                
    except websockets.ConnectionClosedOK:
        print("Connection closed")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
