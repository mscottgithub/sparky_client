# check_models.py
import openwakeword
from pathlib import Path

package_path = Path(openwakeword.__file__).parent
models_path = package_path / "resources" / "models"

print(f"Models directory: {models_path}")
print(f"Exists: {models_path.exists()}")

if models_path.exists():
    print("\nAvailable models:")
    for model_file in models_path.glob("*.tflite"):
        print(f"  - {model_file.name}")
    for model_file in models_path.glob("*.onnx"):
        print(f"  - {model_file.name}")
else:
    print("Models directory not found!")