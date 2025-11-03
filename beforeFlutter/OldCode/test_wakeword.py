# test_wakeword.py
import sounddevice as sd
import numpy as np
import openwakeword
from openwakeword.model import Model
import queue
import time

print("Loading wake word model...")
model = Model(wakeword_models=["hey_jarvis"])

print("Loaded models:", list(model.models.keys()))
print("\nListening for 'Hey Jarvis'...")
print("Scores will be shown continuously (threshold is 0.5)")
print("Say 'Hey Jarvis' multiple times!\n")

audio_queue = queue.Queue()

def audio_callback(indata, frames, time_info, status):
    audio_queue.put(indata.copy())

stream = sd.InputStream(
    channels=1,
    samplerate=16000,
    callback=audio_callback,
    blocksize=int(16000 * 0.08)
)

stream.start()

try:
    audio_buffer = []
    while True:
        chunk = audio_queue.get()
        audio_buffer.append(chunk)
        
        if len(audio_buffer) >= 1:
            audio_data = np.concatenate(audio_buffer, axis=0).flatten()
            audio_buffer = []
            
            prediction = model.predict(audio_data)
            
            for model_name, score in prediction.items():
                if score > 0.1:  # Show any significant score
                    print(f"{model_name}: {score:.3f}", end="")
                    if score > 0.5:
                        print(" ← DETECTED!")
                    else:
                        print()
                        
except KeyboardInterrupt:
    print("\nStopped")
    stream.stop()
    stream.close()