# Location: project_v2/utils/tts_config_loader.py
# Usage: TTS 配置文件加載器，支援增強的語音參數

import os
import configparser
from typing import Dict, Any, Union


class TTSConfigLoader:
    """TTS 配置文件加載器"""
    
    def __init__(self, config_file='TTS_config.txt'):
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
            'enabled', 'rate', 'volume', 'pitch_adjustment',
            'voice_selection_mode', 'preferred_voice_id', 
            'emphasis_level', 'pause_duration_multiplier',
            'auto_stop_previous', 'progress_report_interval'
        ]
        
        print("TTS 關鍵設定:")
        for key in key_settings:
            if key in self.config:
                value = self.config[key]
                if key == 'preferred_voice_id' and len(str(value)) > 50:
                    # 截短語音ID顯示
                    short_id = str(value).split('\\')[-1] if '\\' in str(value) else str(value)
                    print(f"  {key}: {short_id}")
                else:
                    print(f"  {key}: {value}")
    
    def use_defaults(self):
        """使用默認配置"""
        self.config = {
            # 基本設定
            'enabled': True,
            'rate': 140,
            'volume': 0.7,
            'voice_selection_mode': 'auto',
            'preferred_voice_id': '',
            
            # 語音特效
            'pitch_adjustment': -15,
            'enhance_punctuation_pauses': True,
            'use_ssml': False,
            
            # 語音過濾
            'min_english_chars': 3,
            'auto_clean_text': True,
            'speak_punctuation': False,
            
            # 性能設定
            'queue_timeout': 1.0,
            'text_processing_delay': 100,
            'error_retry_count': 2,
            
            # 同步設定
            'synchronous_speech': True,
            'auto_stop_previous': False,
            'progress_report_interval': 50,
            
            # 聲線調整
            'emphasis_level': 1,
            'enable_speed_variation': False,
            'pause_duration_multiplier': 1.2,
            
            # 調試設定
            'verbose_logging': True,
            'test_mode': False,
            'test_text': 'Defense system TTS configuration loaded successfully.',
            
            # 高級設定
            'engine_priority': 'sapi5',
            'buffer_size': 200,
            'preload_next_sentence': True
        }
        print("使用TTS默認配置")
    
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
        """驗證配置的有效性"""
        errors = {}
        
        # 檢查數值範圍
        rate = self.get_int('rate', 140)
        if not (50 <= rate <= 300):
            errors['rate'] = f"語音速度必須在50-300之間，當前值: {rate}"
        
        volume = self.get_float('volume', 0.7)
        if not (0.0 <= volume <= 1.0):
            errors['volume'] = f"音量必須在0.0-1.0之間，當前值: {volume}"
        
        pitch = self.get_int('pitch_adjustment', 0)
        if not (-50 <= pitch <= 50):
            errors['pitch_adjustment'] = f"音調調整必須在-50到50之間，當前值: {pitch}"
        
        min_chars = self.get_int('min_english_chars', 3)
        if min_chars < 1:
            errors['min_english_chars'] = f"最小英文字母數必須大於0，當前值: {min_chars}"
        
        emphasis = self.get_int('emphasis_level', 1)
        if not (0 <= emphasis <= 3):
            errors['emphasis_level'] = f"語氣強度必須在0-3之間，當前值: {emphasis}"
        
        pause_mult = self.get_float('pause_duration_multiplier', 1.0)
        if not (0.1 <= pause_mult <= 5.0):
            errors['pause_duration_multiplier'] = f"停頓時長倍數必須在0.1-5.0之間，當前值: {pause_mult}"
        
        progress_interval = self.get_int('progress_report_interval', 50)
        if not (10 <= progress_interval <= 1000):
            errors['progress_report_interval'] = f"進度回報間隔必須在10-1000毫秒之間，當前值: {progress_interval}"
        
        return errors
    
    def get_all_available_voices(self):
        """獲取系統所有可用的語音列表"""
        try:
            import pyttsx3
            engine = pyttsx3.init()
            voices = engine.getProperty('voices')
            
            voice_list = []
            for voice in voices:
                voice_info = {
                    'id': voice.id,
                    'name': voice.name,
                    'languages': getattr(voice, 'languages', []),
                    'gender': getattr(voice, 'gender', 'unknown'),
                    'age': getattr(voice, 'age', 'unknown')
                }
                voice_list.append(voice_info)
            
            engine.stop()
            return voice_list
            
        except Exception as e:
            print(f"獲取語音列表失敗: {e}")
            return []
    
    def print_available_voices(self):
        """打印所有可用的語音"""
        voices = self.get_all_available_voices()
        
        if not voices:
            print("無法獲取可用語音列表")
            return
        
        print(f"\n=== 系統可用語音列表 (共 {len(voices)} 個) ===")
        
        for i, voice in enumerate(voices, 1):
            print(f"\n{i}. {voice['name']}")
            print(f"   ID: {voice['id']}")
            if voice['languages']:
                print(f"   語言: {voice['languages']}")
            if voice['gender'] != 'unknown':
                print(f"   性別: {voice['gender']}")
        
        print("\n" + "="*50)
        print("如要使用特定語音，請複製ID到TTS_config.txt的preferred_voice_id設定中")
        print("="*50) 
    
    def get_voice_character_settings(self) -> Dict[str, Any]:
        """獲取語音角色設定"""
        return {
            'emphasis_level': self.get_int('emphasis_level', 1),
            'enable_speed_variation': self.get_bool('enable_speed_variation', False),
            'pause_duration_multiplier': self.get_float('pause_duration_multiplier', 1.2),
            'enhance_punctuation_pauses': self.get_bool('enhance_punctuation_pauses', True)
        }
    
    def get_sync_settings(self) -> Dict[str, Any]:
        """獲取同步設定"""
        return {
            'synchronous_speech': self.get_bool('synchronous_speech', True),
            'auto_stop_previous': self.get_bool('auto_stop_previous', False),
            'progress_report_interval': self.get_int('progress_report_interval', 50)
        }
    
    def get_performance_settings(self) -> Dict[str, Any]:
        """獲取性能設定"""
        return {
            'queue_timeout': self.get_float('queue_timeout', 1.0),
            'text_processing_delay': self.get_int('text_processing_delay', 100),
            'error_retry_count': self.get_int('error_retry_count', 2),
            'buffer_size': self.get_int('buffer_size', 200),
            'preload_next_sentence': self.get_bool('preload_next_sentence', True)
        }