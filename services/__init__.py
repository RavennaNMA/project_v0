# Location: project_v2/services/__init__.py
# Usage: Services 模組初始化

from .ollama_service import OllamaService
from .image_service import ImageService
from .platform_service import PlatformService
from .tts_service import TTSService
from .comfyui_sync_service import ComfyUISyncService

# 語音修改服務 - 可選導入
try:
    from .voice_mod_service import VoiceModService
    VOICE_MOD_AVAILABLE = True
except ImportError as e:
    print(f"警告: 語音修改服務不可用: {e}")
    VoiceModService = None
    VOICE_MOD_AVAILABLE = False

__all__ = [
    'OllamaService',
    'ImageService',
    'PlatformService',
    'TTSService',
    'ComfyUISyncService',
    'VoiceModService',
    'VOICE_MOD_AVAILABLE'
]