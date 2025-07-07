# Defense Detection System v2

A comprehensive AI-powered defense detection system integrating ComfyUI, voice modification, computer vision, and hardware control capabilities.

## System Requirements

### macOS Requirements
- **macOS Version**: 10.15 (Catalina) or later
- **Architecture**: Intel x64 or Apple Silicon (M1/M2/M3)
- **RAM**: Minimum 8GB, Recommended 16GB+
- **Storage**: Minimum 10GB free space
- **Camera**: Built-in or USB camera (system will request permissions)

### Python Requirements
- **Python Version**: 3.8.0 or later (recommended: 3.10.x)
- **Package Manager**: pip 21.0+ 
- **Virtual Environment**: venv or conda

### Hardware Requirements (Optional)
- **Arduino Board**: Arduino Mega for hardware control
- **Serial Connection**: USB cable for Arduino communication
- **GPIO Devices**: Relays, LEDs, or other control devices (pins 2-13)

## Installation Guide

### Step 1: Verify System Prerequisites

```bash
# Check Python version
python3 --version

# Check pip version  
pip3 --version

# Install Xcode Command Line Tools (if not already installed)
xcode-select --install
```

### Step 2: Clone Repository in Cursor

1. Open Cursor IDE
2. Use `Cmd+Shift+P` and select "Git: Clone"
3. Enter repository URL or open local folder
4. Navigate to project directory

### Step 3: Create Virtual Environment

```bash
# Navigate to project directory
cd /path/to/defense_system_v1/project_v2

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

### Step 4: Install Python Dependencies

#### Main Project Dependencies
```bash
# Install core requirements
pip install -r requirements.txt
```

#### ComfyUI Dependencies
```bash
# Navigate to ComfyUI directory
cd ComfyUI

# Install ComfyUI requirements
pip install -r requirements.txt

# Return to project root
cd ..
```

#### Critical Package Versions

The following packages require specific versions for compatibility:

```text
# Core Framework
PyQt6>=6.5.0

# AI/ML Stack
torch>=2.0.0
torchvision
torchaudio
numpy>=1.24.0
transformers>=4.37.2

# Computer Vision
opencv-python>=4.8.0
mediapipe>=0.10.0

# Audio Processing
kokoro>=0.9.4
soundfile>=0.12.1
librosa>=0.10.0
pygame>=2.5.0

# System Integration
psutil>=5.9.0
pyserial>=3.5.0
requests>=2.31.0
```

### Step 5: Directory Structure Setup

The system will automatically create required directories, but you can verify:

```bash
# Verify directory structure
ls -la

# Required directories should include:
# - config/          (configuration files)
# - fonts/           (font resources)  
# - webcam-shots/    (camera captures)
# - weapons_img/     (image assets)
# - ComfyUI/         (AI generation engine)
# - core/            (system core modules)
# - services/        (platform services)
# - ui/              (user interface)
```

### Step 6: Font Installation

Download and install the required Chinese font:

```bash
# Create fonts directory if it doesn't exist
mkdir -p fonts

# Download Noto Sans CJK TC (example URL - verify current source)
# Place NotoSansCJKtc-Regular.otf in fonts/ directory
```

Alternative: System will fallback to "PingFang TC" on macOS if custom font unavailable.

### Step 7: Camera Permissions

macOS requires explicit camera permissions:

1. System will automatically request permissions on first run
2. If denied, manually enable in System Preferences:
   - **System Preferences** → **Security & Privacy** → **Camera**
   - Check box next to **Terminal** and **Python**

### Step 8: Configuration Files

Verify configuration files in `config/` directory:

```bash
ls config/
# Should contain:
# - anim_config.csv
# - otherssr_config.csv  
# - period_config.csv
# - prompt_config.txt
# - tts_config.txt
# - voice_mod_config.txt
# - weapon_config.csv
```

## Running the System

### Method 1: Using Python Directly

```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Run main application
python3 main.py
```

### Method 2: Using Cursor Terminal

1. Open integrated terminal in Cursor (`Cmd+` ` `)
2. Ensure you're in project directory
3. Activate virtual environment: `source venv/bin/activate`
4. Run: `python3 main.py`

### Method 3: Create Launch Script (Recommended)

Create `start_mac.sh`:

```bash
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python3 main.py
```

Make executable and run:
```bash
chmod +x start_mac.sh
./start_mac.sh
```

## Configuration

### System Configuration

Key configuration parameters in `main.py`:

```python
# Display Settings
DEBUG_TEXT_SIZE = 22        # Debug text size (12-24)
CAPTION_TEXT_SIZE = 20      # Caption text size (20-40)  
LOADING_TEXT_SIZE = 24      # Loading text size (18-32)

# TTS Settings
TTS_ENABLED = True          # Enable text-to-speech
TTS_RATE = 160             # Speech rate (50-300)
TTS_VOLUME = 0.8           # Volume level (0.0-1.0)

# Voice Modification
VOICE_MOD_ENABLED = True                    # Enable voice modification
VOICE_MOD_SYNC_FROM_COMFYUI = True         # Sync from ComfyUI settings
```

### Arduino Setup (Optional)

If using hardware control:

1. **Install Arduino IDE** from [arduino.cc](https://www.arduino.cc)
2. **Upload sketch**: Load `hardware/defense_system_arduino.ino` 
3. **Connect hardware**: USB cable, verify port (usually `/dev/cu.usbserial*` or `/dev/cu.usbmodem*`)
4. **Test connection**: System will auto-detect Arduino on serial ports

## Troubleshooting

### Common Issues

#### Python/Pip Issues
```bash
# If python3 command not found
brew install python3

# If pip installation fails
python3 -m ensurepip --default-pip
```

#### PyQt6 Issues
```bash
# If PyQt6 installation fails on Apple Silicon
pip install --upgrade pip setuptools wheel
pip install PyQt6 --no-binary PyQt6
```

#### Camera Access Denied
1. **System Preferences** → **Security & Privacy** → **Camera**
2. Enable for **Terminal** and **Python**  
3. Restart application

#### Font Rendering Issues
- Download NotoSansCJKtc-Regular.otf to `fonts/` directory
- System will fallback to PingFang TC if font missing

#### Serial Port Issues
```bash
# List available serial ports
python3 -c "import serial.tools.list_ports; print([p.device for p in serial.tools.list_ports.comports()])"

# Grant permissions (if needed)
sudo chmod 666 /dev/cu.usbserial*
```

### Performance Optimization

#### For Apple Silicon Macs
```bash
# Use optimized PyTorch for M1/M2/M3
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

#### Memory Management
- Close unnecessary applications
- Monitor system resources in Activity Monitor
- Consider increasing swap space for large AI models

## Development in Cursor

### Recommended Extensions
- Python
- Pylance  
- GitLens
- Arduino (if using hardware features)

### Cursor-Specific Features
- Use `Cmd+K` for AI code completion
- Use `Cmd+L` for AI chat assistance
- Use `Cmd+I` for inline AI editing

### Debugging
```bash
# Run with debug output
python3 main.py --debug

# Check system dependencies
python3 -c "from services.platform_service import PlatformService; print(PlatformService().check_dependencies())"
```

## System Architecture

### Core Components
- **main.py**: Application entry point and configuration
- **core/**: Face detection, camera management, state machine
- **services/**: Platform services, ComfyUI integration, TTS, voice modification  
- **ui/**: PyQt6 user interface components
- **ComfyUI/**: AI image generation subsystem

### Data Flow
1. **Camera Input** → Face Detection → State Machine
2. **AI Generation** → ComfyUI → Image Processing  
3. **Voice Pipeline** → TTS → Voice Modification → Audio Output
4. **Hardware Control** → Arduino → GPIO Devices

## Support

### System Information
```bash
# Get platform info
python3 -c "from services.platform_service import PlatformService; import pprint; pprint.pprint(PlatformService().get_platform_info())"

# Check dependencies
python3 -c "from services.platform_service import PlatformService; print(PlatformService().check_dependencies())"
```

### Logs and Debugging
- Application logs appear in terminal/Cursor console
- Camera permissions logged to system console
- Arduino communication logged to serial monitor

For additional support, ensure all requirements are met and dependencies properly installed before reporting issues.