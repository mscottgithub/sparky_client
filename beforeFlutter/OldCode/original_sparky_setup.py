#!/usr/bin/env python3
"""
Sparky Voice AI - Setup Script
Prepares the environment and downloads necessary models
"""
import os
import sys
from pathlib import Path

def setup_sparky():
    """Setup Sparky Voice AI environment"""
    print("""
╔══════════════════════════════════════════════════════════╗
║         SPARKY VOICE AI - SETUP & INSTALLATION          ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    
    # Install dependencies
    print("\n📦 Installing dependencies...")
    import subprocess
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], check=True)
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("✓ Dependencies installed")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        print("   Try manually: pip install -r requirements.txt")
        sys.exit(1)
    
    # Create directories
    print("\n📁 Creating directories...")
    wake_models_dir = Path(__file__).parent / 'wake_models'
    wake_models_dir.mkdir(exist_ok=True)
    print(f"✓ Created: {wake_models_dir}")
    
    # Download openWakeWord models
    print("\n⬇️  Downloading pre-trained wake word models...")
    try:
        import openwakeword
        openwakeword.utils.download_models()
        print("✓ Downloaded built-in models")
    except Exception as e:
        print(f"⚠️  Warning: Could not download models: {e}")
        print("   Models will be downloaded on first run")
    
    # Check config
    config_file = Path(__file__).parent / 'config.ini'
    if not config_file.exists():
        print("\n⚠️  WARNING: config.ini not found!")
        print("   Please create config.ini with your server settings")
        print("   See README.md for configuration template")
    else:
        print("\n✓ Configuration file found")
    
    print("""
╔══════════════════════════════════════════════════════════╗
║                    SETUP COMPLETE!                       ║
╚══════════════════════════════════════════════════════════╝

Next steps:
1. Ensure config.ini has your server settings
2. Run: python voice_client_tray.py
3. Right-click the tray icon to access settings

To train custom wake words:
1. Visit: https://colab.research.google.com/drive/1q1oe2zOyZp7UsB3jJiQ1IFn8z5YfjwEb
2. Train "hey sparky" and "bye sparky"
3. Save .tflite files to wake_models/
4. Reload wake words from tray menu

Default wake words:
  - Activate: "Hey Jarvis"
  - Deactivate: "Hey Mycroft"

Happy chatting with Sparky! 🎤
    """)

if __name__ == "__main__":
    setup_sparky()
