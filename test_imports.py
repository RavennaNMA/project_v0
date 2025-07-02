print("測試套件導入...")
try:
    import cv2
    print("✓ OpenCV")
except ImportError as e:
    print(f"✗ OpenCV: {e}")

try:
    import mediapipe
    print("✓ MediaPipe")
except ImportError as e:
    print(f"✗ MediaPipe: {e}")

try:
    from PyQt6.QtWidgets import QApplication
    print("✓ PyQt6")
except ImportError as e:
    print(f"✗ PyQt6: {e}")

try:
    import serial
    print("✓ PySerial")
except ImportError as e:
    print(f"✗ PySerial: {e}")

try:
    import ollama
    print("✓ Ollama")
except ImportError as e:
    print(f"✗ Ollama: {e}")

try:
    import numpy
    print("✓ NumPy")
except ImportError as e:
    print(f"✗ NumPy: {e}")

try:
    from PIL import Image
    print("✓ Pillow")
except ImportError as e:
    print(f"✗ Pillow: {e}")

try:
    import psutil
    print("✓ psutil")
except ImportError as e:
    print(f"✗ psutil: {e}")

print("\n測試完成！") 