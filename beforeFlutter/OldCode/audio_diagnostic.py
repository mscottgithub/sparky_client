#!/usr/bin/env python3
"""
Sparky Diagnostic Script - Audio Testing
Quick script to diagnose audio input issues
"""
import sounddevice as sd
import numpy as np
import time
import openwakeword
from openwakeword.model import Model
from pathlib import Path

print("="*60)
print("🔍 SPARKY AUDIO DIAGNOSTIC")
print("="*60)

# Test 1: List audio devices
print("\n📊 Available Audio Devices:")
print(sd.query_devices())

# Test 2: Check default input device
print("\n🎤 Default Input Device:")
default_in = sd.query_devices(kind='input')
print(f"  Name: {default_in['name']}")
print(f"  Channels: {default_in['max_input_channels']}")
print(f"  Sample Rate: {default_in['default_samplerate']}")

# Test 3: Try to record 2 seconds of audio
print("\n🎙️ Testing Audio Input (2 seconds)...")
print("  Make some noise!")

try:
    SAMPLE_RATE = 16000
    duration = 2.0
    
    recording = sd.rec(
        int(duration * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype='float32'
    )
    sd.wait()
    
    # Check if we got audio
    audio_data = recording.flatten()
    max_amplitude = np.max(np.abs(audio_data))
    rms = np.sqrt(np.mean(audio_data**2))
    
    print(f"✓ Recording complete!")
    print(f"  Max amplitude: {max_amplitude:.4f}")
    print(f"  RMS level: {rms:.4f}")
    
    if max_amplitude < 0.001:
        print("  ⚠️ WARNING: Audio level very low - check microphone!")
    elif max_amplitude > 0.01:
        print("  ✓ Audio level looks good!")
    
except Exception as e:
    print(f"❌ Audio recording failed: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Test streaming callback
print("\n🔄 Testing Streaming Callback (3 seconds)...")
print("  Make some noise!")

chunk_count = 0
max_seen = 0.0

def test_callback(indata, frames, time_info, status):
    global chunk_count, max_seen
    if status:
        print(f"  Status: {status}")
    chunk_count += 1
    audio_data = indata.flatten()
    amplitude = np.max(np.abs(audio_data))
    if amplitude > max_seen:
        max_seen = amplitude
    if chunk_count % 10 == 0:
        print(f"  Chunk {chunk_count}: amplitude = {amplitude:.4f}")

try:
    stream = sd.InputStream(
        channels=1,
        samplerate=SAMPLE_RATE,
        callback=test_callback,
        blocksize=int(SAMPLE_RATE * 0.08)
    )
    stream.start()
    time.sleep(3.0)
    stream.stop()
    stream.close()
    
    print(f"✓ Streaming test complete!")
    print(f"  Total chunks: {chunk_count}")
    print(f"  Max amplitude seen: {max_seen:.4f}")
    
    if chunk_count == 0:
        print("  ❌ ERROR: No audio chunks received!")
    elif max_seen < 0.001:
        print("  ⚠️ WARNING: Audio level very low!")
    else:
        print("  ✓ Audio streaming working!")
        
except Exception as e:
    print(f"❌ Streaming test failed: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Check wake word models
print("\n🎯 Testing Wake Word Models...")
WAKE_MODELS_DIR = Path(__file__).parent / 'wake_models'

try:
    custom_wake = WAKE_MODELS_DIR / "hey_sparky.tflite"
    custom_exit = WAKE_MODELS_DIR / "bye_sparky.tflite"
    
    if custom_wake.exists() and custom_exit.exists():
        print(f"✓ Custom models found:")
        print(f"  {custom_wake}")
        print(f"  {custom_exit}")
        
        # Try to load them
        wake_model = Model(wakeword_models=[str(custom_wake)])
        print(f"✓ Wake model loaded successfully")
        
        exit_model = Model(wakeword_models=[str(custom_exit)])
        print(f"✓ Exit model loaded successfully")
        
    else:
        print("ℹ️ No custom models, using built-in...")
        openwakeword.utils.download_models()
        
        wake_model = Model(wakeword_models=["hey_jarvis"])
        print(f"✓ Wake model (hey_jarvis) loaded")
        
        exit_model = Model(wakeword_models=["hey_mycroft"])
        print(f"✓ Exit model (hey_mycroft) loaded")
        
except Exception as e:
    print(f"❌ Wake word model error: {e}")
    import traceback
    traceback.print_exc()

# Summary
print("\n" + "="*60)
print("📋 DIAGNOSTIC SUMMARY")
print("="*60)
print(f"Audio Input Available: {'✓' if default_in else '❌'}")
print(f"Audio Recording Works: {'✓' if max_amplitude > 0 else '❌'}")
print(f"Audio Streaming Works: {'✓' if chunk_count > 0 else '❌'}")
print(f"Wake Models Load: {'✓' if 'wake_model' in locals() else '❌'}")
print("="*60)

if max_amplitude < 0.001:
    print("\n⚠️ PROBLEM DETECTED: Low/no audio input!")
    print("Possible causes:")
    print("  1. Microphone is muted in system settings")
    print("  2. Wrong input device selected")
    print("  3. Microphone not plugged in")
    print("  4. Permissions issue (Windows requires mic access)")
    print("\nSuggestions:")
    print("  - Check system audio settings")
    print("  - Try speaking louder near the microphone")
    print("  - Check Windows Privacy > Microphone permissions")
elif chunk_count == 0:
    print("\n⚠️ PROBLEM DETECTED: Streaming callback not working!")
    print("This is a sounddevice library issue.")
else:
    print("\n✅ All systems appear to be working!")
    print("If wake words still don't work, check:")
    print("  1. Speaking clearly toward microphone")
    print("  2. Saying exact wake phrase ('Hey Jarvis')")
    print("  3. Background noise isn't too loud")
