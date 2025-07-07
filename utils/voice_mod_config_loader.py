# Location: project_v2/utils/voice_mod_config_loader.py
# Usage: 語音修改配置載入器，管理語音效果參數設定

import os
from typing import Dict, Any, Optional
from PyQt6.QtCore import QObject


class VoiceModConfigLoader(QObject):
    """語音修改配置載入器"""
    
    def __init__(self, config_file: Optional[str] = None):
        super().__init__()
        if config_file is None:
            config_file = "voice_mod_config.txt"
        self.config_file = config_file
        self.config_data = {}
        
        # 預設的語音修改設定
        self.default_config = {
            # 語音修改總開關
            'voice_mod_enabled': False,
            
            # 語音配置文件設定
            'voice_profile': 'None',  # None, Cinematic, Monster, Singer, Robot, Child, Darth Vader, etc.
            'profile_intensity': 0.7,  # 配置文件效果強度 (0.0-1.0)
            
            # 手動模式
            'manual_mode': False,  # 是否使用手動模式而非配置文件
            
            # 全局效果設定
            'effect_blend': 1.0,     # 效果混合比例 (0.0=原音, 1.0=全效果)
            'output_volume': 0.0,    # 輸出音量調整 (dB)
            
            # 基礎語音變換
            'pitch_shift': 0.0,      # 音調偏移 (-12.0 到 12.0 半音)
            'formant_shift': 0.0,    # 音色偏移 (-5.0 到 5.0)
            
            # 空間效果
            'reverb_amount': 0.0,    # 混響量 (0.0-1.0)
            'echo_delay': 0.0,       # 回聲延遲 (0.0-1.0)
            
            # 音色效果
            'distortion': 0.0,       # 失真 (0.0-1.0)
            'compression': 0.0,      # 壓縮 (0.0-1.0)
            
            # EQ 均衡器
            'eq_bass': 0.0,          # 低頻調整 (-1.0 到 1.0)
            'eq_mid': 0.0,           # 中頻調整 (-1.0 到 1.0)
            'eq_treble': 0.0,        # 高頻調整 (-1.0 到 1.0)
            
            # 調試設定
            'verbose_logging': True,  # 詳細日誌
        }
        
        # 載入配置
        self.load_config()
    
    def load_config(self):
        """載入配置檔案"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and '=' in line:
                            key, value = line.split('=', 1)
                            self.config_data[key.strip()] = value.strip()
                print(f"載入語音修改配置: {self.config_file}")
            except Exception as e:
                print(f"載入配置失敗: {e}")
                self.config_data = {}
        else:
            print(f"配置檔案不存在，使用預設值: {self.config_file}")
            self.config_data = {}
    
    def save_config(self):
        """儲存配置檔案"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                f.write("# 語音修改配置檔案\n")
                for key, value in self.config_data.items():
                    f.write(f"{key}={value}\n")
            print(f"儲存語音修改配置: {self.config_file}")
        except Exception as e:
            print(f"儲存配置失敗: {e}")
    
    def get_value(self, key: str, default_value):
        """獲取配置值"""
        if key in self.config_data:
            try:
                value_str = self.config_data[key]
                if isinstance(default_value, bool):
                    return value_str.lower() in ('true', '1', 'yes', 'on')
                elif isinstance(default_value, int):
                    return int(value_str)
                elif isinstance(default_value, float):
                    return float(value_str)
                else:
                    return value_str
            except ValueError:
                return default_value
        return default_value
    
    def set_value(self, key: str, value):
        """設定配置值"""
        self.config_data[key] = str(value)
    
    def get_bool(self, key: str, default_value: bool = False) -> bool:
        """獲取布林值"""
        result = self.get_value(key, default_value)
        return bool(result)
    
    def get_float(self, key: str, default_value: float = 0.0) -> float:
        """獲取浮點數值"""
        result = self.get_value(key, default_value)
        return float(result)
    
    def get_str(self, key: str, default_value: str = '') -> str:
        """獲取字符串值"""
        result = self.get_value(key, default_value)
        return str(result)
    
    def get_voice_mod_settings(self) -> Dict[str, Any]:
        """獲取語音修改設定字典"""
        settings = {}
        for key in self.default_config.keys():
            if key != 'verbose_logging':  # 排除調試設定
                settings[key] = self.get_value(key, self.default_config[key])
        return settings
    
    def update_voice_mod_settings(self, settings: Dict[str, Any]):
        """更新語音修改設定"""
        for key, value in settings.items():
            if key in self.default_config:
                self.set_value(key, value)
        self.save_config()
    
    def get_preset_configurations(self) -> Dict[str, Dict[str, Any]]:
        """獲取預設配置範例"""
        return {
            "Pitch Up (Male to Female)": {
                'manual_mode': True,
                'pitch_shift': 4.0,
                'formant_shift': 2.0,
                'eq_treble': 0.2,
                'effect_blend': 0.8,
            },
            "Pitch Down (Female to Male)": {
                'manual_mode': True,
                'pitch_shift': -4.0,
                'formant_shift': -2.0,
                'eq_bass': 0.3,
                'effect_blend': 0.8,
            },
            "Robot Voice": {
                'voice_profile': 'Robot',
                'profile_intensity': 0.6,
                'manual_mode': False,
            },
            "Cinematic Deep": {
                'voice_profile': 'Cinematic',
                'profile_intensity': 0.7,
                'manual_mode': False,
            },
            "Monster Voice": {
                'voice_profile': 'Monster',
                'profile_intensity': 0.5,
                'manual_mode': False,
            },
            "Child Voice": {
                'voice_profile': 'Child',
                'profile_intensity': 0.4,
                'manual_mode': False,
            },
            "Broadcasting": {
                'voice_profile': 'Broadcast',
                'profile_intensity': 0.8,
                'manual_mode': False,
            },
            "Subtle Enhancement": {
                'manual_mode': True,
                'compression': 0.3,
                'eq_mid': 0.2,
                'eq_treble': 0.1,
                'effect_blend': 0.5,
            },
        }
    
    def apply_preset(self, preset_name: str) -> bool:
        """應用預設配置"""
        presets = self.get_preset_configurations()
        if preset_name in presets:
            preset_config = presets[preset_name]
            
            # 先重置為默認值
            self.reset_to_defaults()
            
            # 啟用語音修改
            preset_config['voice_mod_enabled'] = True
            
            # 應用預設
            self.update_voice_mod_settings(preset_config)
            
            print(f"已應用語音修改預設: {preset_name}")
            return True
        else:
            print(f"未找到預設配置: {preset_name}")
            return False
    
    def reset_to_defaults(self):
        """重置為默認設定"""
        for key, value in self.default_config.items():
            self.set_value(key, value)
        self.save_config()
        print("語音修改設定已重置為默認值")
    
    def enable_voice_mod(self, enabled: bool = True):
        """啟用或禁用語音修改功能"""
        self.set_value('voice_mod_enabled', enabled)
        self.save_config()
        status = "啟用" if enabled else "禁用"
        print(f"語音修改功能已{status}")
    
    def get_current_profile_info(self) -> str:
        """獲取當前配置的描述信息"""
        if not self.get_bool('voice_mod_enabled'):
            return "語音修改已禁用"
        
        if self.get_bool('manual_mode'):
            # 手動模式
            effects = []
            pitch = self.get_float('pitch_shift')
            formant = self.get_float('formant_shift')
            
            if abs(pitch) > 0.1:
                effects.append(f"音調{pitch:+.1f}")
            if abs(formant) > 0.1:
                effects.append(f"音色{formant:+.1f}")
            
            other_effects = []
            if self.get_float('reverb_amount') > 0.1:
                other_effects.append("混響")
            if self.get_float('distortion') > 0.1:
                other_effects.append("失真")
            if self.get_float('compression') > 0.1:
                other_effects.append("壓縮")
            
            effects.extend(other_effects)
            
            if effects:
                return f"手動模式: {', '.join(effects)}"
            else:
                return "手動模式: 無效果"
        else:
            # 配置文件模式
            profile = self.get_str('voice_profile')
            intensity = self.get_float('profile_intensity')
            if profile == 'None':
                return "配置文件: 無"
            else:
                return f"配置文件: {profile} (強度: {intensity:.1f})"
    
    def validate_settings(self) -> list:
        """驗證設定的有效性，返回警告列表"""
        warnings = []
        settings = self.get_voice_mod_settings()
        
        # 檢查音調偏移範圍
        if abs(settings['pitch_shift']) > 12.0:
            warnings.append(f"音調偏移超出建議範圍 (-12到12): {settings['pitch_shift']}")
        
        # 檢查音色偏移範圍
        if abs(settings['formant_shift']) > 5.0:
            warnings.append(f"音色偏移超出建議範圍 (-5到5): {settings['formant_shift']}")
        
        # 檢查效果參數範圍
        effects_to_check = ['reverb_amount', 'echo_delay', 'distortion', 'compression']
        for effect in effects_to_check:
            if settings[effect] < 0 or settings[effect] > 1.0:
                warnings.append(f"{effect} 超出有效範圍 (0-1): {settings[effect]}")
        
        # 檢查EQ範圍
        eq_settings = ['eq_bass', 'eq_mid', 'eq_treble']
        for eq in eq_settings:
            if settings[eq] < -1.0 or settings[eq] > 1.0:
                warnings.append(f"{eq} 超出有效範圍 (-1到1): {settings[eq]}")
        
        # 檢查音量調整
        if abs(settings['output_volume']) > 20.0:
            warnings.append(f"輸出音量調整過大，可能導致失真: {settings['output_volume']} dB")
        
        return warnings 