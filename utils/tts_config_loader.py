# Location: project_v2/utils/tts_config_loader.py
# Usage: TTS 配置文件加載器，支援增強的語音參數

import os
import configparser
from typing import Dict, Any, Union


class TTSConfigLoader:
    """TTS 配置文件加載器"""
    
    def __init__(self, config_file='tts_config.txt'):
        self.config_file = config_file
        self.config = {}
        self.load_config()
    
    def load_config(self):
        """加載TTS配置文件"""
        if not os.path.exists(self.config_file):
            print(f"TTS配置文件不存在: {self.config_file}，使用默認設定")
            self.use_defaults()
            return
        
        try:
            # 讀取配置文件
            config_dict = {}
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    
                    # 跳過空行和註釋
                    if not line or line.startswith('#') or line.startswith('='):
                        continue
                    
                    # 解析 key=value 格式
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # 處理不同類型的值
                        config_dict[key] = self._parse_value(value)
            
            self.config = config_dict
            print(f"TTS配置已加載，共 {len(self.config)} 個設定")
            
            # 顯示關鍵配置
            if self.get_bool('verbose_logging', True):
                self._print_key_settings()
                
        except Exception as e:
            print(f"加載TTS配置文件失敗: {e}，使用默認設定")
            self.use_defaults()
    
    def _parse_value(self, value: str) -> Union[str, int, float, bool]:
        """解析配置值的類型"""
        # 布爾值
        if value.lower() in ['true', 'yes', '1', 'on']:
            return True
        elif value.lower() in ['false', 'no', '0', 'off']:
            return False
        
        # 數字
        try:
            # 先嘗試整數
            if '.' not in value:
                return int(value)
            else:
                return float(value)
        except ValueError:
            pass
        
        # 字符串
        return value
    
    def _print_key_settings(self):
        """打印關鍵設定"""
        key_settings = [
            'enabled', 'realtime_mode', 'kokoro_lang_code', 'kokoro_voice', 
            'kokoro_speed', 'min_english_chars', 'auto_clean_text',
            'max_chunk_length', 'min_chunk_length', 'verbose_logging'
        ]
        
        print("TTS 關鍵設定:")
        for key in key_settings:
            if key in self.config:
                value = self.config[key]
                print(f"  {key}: {value}")
    
    def use_defaults(self):
        """使用默認配置"""
        self.config = {
            # 基本設定
            'enabled': True,
            'realtime_mode': True,
            
            # Kokoro TTS 語音設定
            'kokoro_lang_code': 'a',
            'kokoro_voice': 'am_adam',
            'kokoro_speed': 1.1,
            
            # 文字處理設定
            'min_english_chars': 3,
            'auto_clean_text': True,
            'max_chunk_length': 80,
            'min_chunk_length': 8,
            
            # 調試設定
            'verbose_logging': True,
            'test_mode': False,
            'test_text': 'Hello! This is a test of Kokoro TTS system. The voice quality should be excellent.'
        }
        print("使用 Kokoro TTS 默認配置")
    
    def get(self, key: str, default: Any = None) -> Any:
        """獲取配置值"""
        return self.config.get(key, default)
    
    def get_str(self, key: str, default: str = '') -> str:
        """獲取字符串配置值"""
        value = self.config.get(key, default)
        return str(value)
    
    def get_int(self, key: str, default: int = 0) -> int:
        """獲取整數配置值"""
        value = self.config.get(key, default)
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
    
    def get_float(self, key: str, default: float = 0.0) -> float:
        """獲取浮點數配置值"""
        value = self.config.get(key, default)
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    
    def get_bool(self, key: str, default: bool = False) -> bool:
        """獲取布爾配置值"""
        value = self.config.get(key, default)
        if isinstance(value, bool):
            return value
        elif isinstance(value, str):
            return value.lower() in ['true', 'yes', '1', 'on']
        else:
            return bool(value)
    
    def reload_config(self):
        """重新加載配置文件"""
        print("重新加載TTS配置...")
        self.load_config()
    
    def validate_config(self) -> Dict[str, str]:
        """驗證 Kokoro TTS 配置的有效性"""
        errors = {}
        
        # 檢查語言代碼
        lang_code = self.get_str('kokoro_lang_code', 'a')
        if lang_code not in ['a', 'b']:
            errors['kokoro_lang_code'] = f"語言代碼必須是 'a' 或 'b'，當前值: {lang_code}"
        
        # 檢查語音速度
        speed = self.get_float('kokoro_speed', 1.1)
        if not (0.5 <= speed <= 2.0):
            errors['kokoro_speed'] = f"語音速度必須在 0.5-2.0 之間，當前值: {speed}"
        
        # 檢查最小英文字符數
        min_chars = self.get_int('min_english_chars', 3)
        if min_chars < 1:
            errors['min_english_chars'] = f"最小英文字母數必須大於 0，當前值: {min_chars}"
        
        # 檢查片段長度設定
        max_chunk = self.get_int('max_chunk_length', 80)
        min_chunk = self.get_int('min_chunk_length', 8)
        
        if max_chunk < 10:
            errors['max_chunk_length'] = f"最大片段長度必須大於 10，當前值: {max_chunk}"
        
        if min_chunk < 1:
            errors['min_chunk_length'] = f"最小片段長度必須大於 0，當前值: {min_chunk}"
        
        if min_chunk >= max_chunk:
            errors['chunk_length'] = f"最小片段長度 ({min_chunk}) 必須小於最大片段長度 ({max_chunk})"
        
        # 檢查語音ID的有效性
        voices = self.get_all_available_voices()
        lang_code = self.get_str('kokoro_lang_code', 'a')
        voice_id = self.get_str('kokoro_voice', 'am_adam')
        
        if lang_code in voices and voice_id not in voices[lang_code]:
            available_voices = list(voices[lang_code].keys())
            errors['kokoro_voice'] = f"語音 '{voice_id}' 不適用於語言 '{lang_code}'，可用語音: {available_voices}"
        
        return errors
    
    def get_all_available_voices(self):
        """獲取 Kokoro TTS 可用的語音列表"""
        kokoro_voices = {
            # 美式英語語音
            'a': {
                'am_adam': '中性男聲 Adam（推薦用於防禦系統）',
                'am_michael': '深沉男聲 Michael',
                'af_sarah': '清晰女聲 Sarah',
                'af_nicole': '溫和女聲 Nicole',
                'af_sky': '活潑女聲 Sky',
                'af_bella': '專業女聲 Bella'
            },
            # 英式英語語音
            'b': {
                'bf_emma': '英式女聲 Emma',
                'bf_isabella': '英式女聲 Isabella',
                'bm_george': '英式男聲 George',
                'bm_lewis': '英式男聲 Lewis'
            }
        }
        
        return kokoro_voices
    
    def print_available_voices(self):
        """打印所有可用的 Kokoro TTS 語音"""
        voices = self.get_all_available_voices()
        
        print(f"\n=== Kokoro TTS 可用語音列表 ===")
        
        for lang_code, lang_voices in voices.items():
            lang_name = "美式英語" if lang_code == 'a' else "英式英語"
            print(f"\n【{lang_name} (kokoro_lang_code={lang_code})】")
            
            for voice_id, description in lang_voices.items():
                print(f"  • {voice_id}: {description}")
        
        print("\n" + "="*50)
        print("如要使用特定語音，請在 tts_config.txt 中設定：")
        print("kokoro_lang_code=a  # 語言代碼")
        print("kokoro_voice=am_adam  # 語音ID") 
        print("="*50)
    
    def get_voice_character_settings(self) -> Dict[str, Any]:
        """獲取 Kokoro TTS 語音設定"""
        return {
            'kokoro_lang_code': self.get_str('kokoro_lang_code', 'a'),
            'kokoro_voice': self.get_str('kokoro_voice', 'am_adam'),
            'kokoro_speed': self.get_float('kokoro_speed', 1.1)
        }
    
    def get_text_processing_settings(self) -> Dict[str, Any]:
        """獲取文字處理設定"""
        return {
            'min_english_chars': self.get_int('min_english_chars', 3),
            'auto_clean_text': self.get_bool('auto_clean_text', True),
            'max_chunk_length': self.get_int('max_chunk_length', 80),
            'min_chunk_length': self.get_int('min_chunk_length', 8)
        }
    
    def get_general_settings(self) -> Dict[str, Any]:
        """獲取一般設定"""
        return {
            'enabled': self.get_bool('enabled', True),
            'realtime_mode': self.get_bool('realtime_mode', True),
            'verbose_logging': self.get_bool('verbose_logging', True),
            'test_mode': self.get_bool('test_mode', False),
            'test_text': self.get_str('test_text', 'Hello! This is a test of Kokoro TTS system.')
        }