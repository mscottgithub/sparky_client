# test_audio_format.py
import sounddevice as sd
import numpy as np

print("Recording 2 seconds of audio...")
audio = sd.rec(int(2 * 16000), samplerate=16000, channels=1, dtype='float32')
sd.wait()

print(f"Audio shape: {audio.shape}")
print(f"Audio dtype: {audio.dtype}")
print(f"Audio min: {audio.min():.4f}")
print(f"Audio max: {audio.max():.4f}")
print(f"Audio mean: {audio.mean():.4f}")
print(f"Non-zero values: {np.count_nonzero(audio)}")

# Check if it's actually mono
if len(audio.shape) == 2:
    print(f"Channels: {audio.shape[1]}")
    audio_flat = audio.flatten()
else:
    audio_flat = audio

print(f"\nFlattened shape: {audio_flat.shape}")

# Now test with openWakeWord
print("\nTesting with openWakeWord model...")
from openwakeword.model import Model

model = Model(wakeword_models=["hey_jarvis"])

# Try prediction
prediction = model.predict(audio_flat)
print(f"Prediction result: {prediction}")