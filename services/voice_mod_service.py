# Location: project_v2/services/voice_mod_service.py
# Usage: 語音修改服務，提供音調調整、音色變換、音頻效果等功能

import numpy as np
import threading
import queue
import time
from typing import Optional, Tuple, Union, Dict, Any
from PyQt6.QtCore import QObject, pyqtSignal

# 音頻處理庫導入與降級處理
try:
    import librosa
    import resampy
    LIBROSA_AVAILABLE = True
    RESAMPY_AVAILABLE = True
    print("高品質音頻處理庫可用: librosa + resampy")
except ImportError:
    LIBROSA_AVAILABLE = False
    RESAMPY_AVAILABLE = False
    print("警告: librosa/resampy 不可用，將使用基礎音頻處理")

try:
    from scipy import signal
    from scipy.signal import butter, sosfilt
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    print("警告: scipy 不可用，某些音頻效果將被禁用")

try:
    import soundfile as sf
    SOUNDFILE_AVAILABLE = True
except ImportError:
    SOUNDFILE_AVAILABLE = False


class VoiceProfile:
    """語音配置文件，定義預設的語音變換效果"""
    
    # 預設語音配置
    PROFILES = {
        "None": {
            "enabled": False,
        },
        "Cinematic": {
            "pitch_shift": -2.0,
            "formant_shift": -1.0,
            "reverb_amount": 0.4,
            "compression": 0.3,
            "eq_bass": 0.2,
            "eq_mid": 0.1,
            "eq_treble": -0.1,
        },
        "Monster": {
            "pitch_shift": -8.0,
            "formant_shift": -3.0,
            "distortion": 0.3,
            "reverb_amount": 0.2,
            "eq_bass": 0.4,
            "eq_mid": -0.2,
        },
        "Singer": {
            "compression": 0.6,
            "reverb_amount": 0.3,
            "eq_mid": 0.3,
            "eq_treble": 0.2,
            "formant_shift": 0.2,
        },
        "Robot": {
            "pitch_shift": 0.0,
            "formant_shift": 0.0,
            "distortion": 0.4,
            "eq_mid": -0.3,
            "eq_treble": 0.1,
        },
        "Child": {
            "pitch_shift": 4.0,
            "formant_shift": 2.0,
            "eq_treble": 0.3,
            "eq_mid": 0.1,
        },
        "Darth Vader": {
            "pitch_shift": -6.0,
            "formant_shift": -2.0,
            "echo_delay": 0.2,
            "compression": 0.4,
            "eq_bass": 0.3,
            "eq_mid": -0.1,
        },
        "Elderly": {
            "pitch_shift": -1.5,
            "formant_shift": -0.8,
            "eq_mid": -0.2,
            "eq_treble": 0.3,
            "distortion": 0.1,
        },
        "Broadcast": {
            "compression": 0.7,
            "eq_bass": 0.2,
            "eq_mid": 0.4,
            "eq_treble": -0.1,
        },
        "Ghost": {
            "pitch_shift": 1.0,
            "formant_shift": 0.5,
            "reverb_amount": 0.7,
            "echo_delay": 0.3,
            "compression": 0.2,
        },
        "Giant": {
            "pitch_shift": -5.0,
            "formant_shift": -3.0,
            "reverb_amount": 0.4,
            "eq_bass": 0.6,
        }
    }


class AudioEffectsProcessor:
    """音頻效果處理器"""
    
    def __init__(self, sample_rate: int = 24000):
        self.sample_rate = sample_rate
        
    def apply_pitch_shift(self, audio: np.ndarray, semitones: float) -> np.ndarray:
        """應用音調偏移"""
        if abs(semitones) < 0.1:
            return audio
            
        try:
            if LIBROSA_AVAILABLE:
                # 高品質音調偏移
                return librosa.effects.pitch_shift(
                    audio, 
                    sr=self.sample_rate, 
                    n_steps=semitones,
                    bins_per_octave=12
                )
            else:
                # 基礎實現：重採樣方法
                shift_factor = 2 ** (semitones / 12.0)
                indices = np.arange(len(audio)) / shift_factor
                indices = np.clip(indices, 0, len(audio) - 1)
                return np.interp(indices, np.arange(len(audio)), audio)
        except Exception as e:
            print(f"音調偏移處理失敗: {e}")
            return audio
    
    def apply_formant_shift(self, audio: np.ndarray, shift: float) -> np.ndarray:
        """應用音色偏移（模擬聲道形狀變化）"""
        if abs(shift) < 0.1:
            return audio
            
        try:
            if LIBROSA_AVAILABLE:
                # 使用音調變化模擬音色變化
                stft = librosa.stft(audio, hop_length=512)
                magnitude, phase = np.abs(stft), np.angle(stft)
                
                # 頻譜偏移模擬音色變化
                shift_factor = 1.0 + (shift * 0.1)
                n_bins, n_frames = magnitude.shape
                new_magnitude = np.zeros_like(magnitude)
                
                for i in range(n_bins):
                    new_i = int(i * shift_factor)
                    if 0 <= new_i < n_bins:
                        new_magnitude[new_i] += magnitude[i]
                
                # 重建音頻
                new_stft = new_magnitude * np.exp(1j * phase)
                result = librosa.istft(new_stft, hop_length=512)
                
                # 確保輸出長度與輸入相同
                if len(result) != len(audio):
                    if len(result) > len(audio):
                        result = result[:len(audio)]
                    else:
                        # 補零到原始長度
                        padded = np.zeros(len(audio))
                        padded[:len(result)] = result
                        result = padded
                        
                return result
            else:
                # 基礎實現：簡單濾波
                if shift > 0:
                    # 提高高頻（更小的聲道）
                    return self._apply_basic_eq(audio, bass=0, mid=0, treble=shift*0.3)
                else:
                    # 降低高頻（更大的聲道）
                    return self._apply_basic_eq(audio, bass=-shift*0.2, mid=0, treble=shift*0.2)
        except Exception as e:
            print(f"音色偏移處理失敗: {e}")
            return audio
    
    def apply_reverb(self, audio: np.ndarray, amount: float) -> np.ndarray:
        """應用混響效果"""
        if amount < 0.05:
            return audio
            
        try:
            audio_length = len(audio)
            reverb_audio = np.copy(audio)
            
            # 多個延遲回聲創造混響感
            delays = [0.03, 0.07, 0.11, 0.15]  # 不同延遲時間
            decay = 0.6 * amount  # 衰減因子
            
            for delay_time in delays:
                delay_samples = int(delay_time * self.sample_rate)
                if delay_samples > 0 and delay_samples < audio_length:
                    # 確保陣列大小匹配
                    echo_length = audio_length - delay_samples
                    if echo_length > 0:
                        reverb_audio[delay_samples:delay_samples + echo_length] += audio[:echo_length] * decay
                    decay *= 0.7  # 遞減衰減
                
            return reverb_audio
        except Exception as e:
            print(f"混響處理失敗: {e}")
            return audio
    
    def apply_echo(self, audio: np.ndarray, delay: float) -> np.ndarray:
        """應用回聲效果"""
        if delay < 0.05:
            return audio
            
        try:
            audio_length = len(audio)
            echo_delay = int(0.2 * delay * self.sample_rate)  # 最大200ms延遲
            echo_audio = np.copy(audio)
            
            if echo_delay > 0 and echo_delay < audio_length:
                echo_length = audio_length - echo_delay
                if echo_length > 0:
                    echo_audio[echo_delay:echo_delay + echo_length] += audio[:echo_length] * (0.5 * delay)
                
            return echo_audio
        except Exception as e:
            print(f"回聲處理失敗: {e}")
            return audio
    
    def apply_distortion(self, audio: np.ndarray, amount: float) -> np.ndarray:
        """應用失真效果"""
        if amount < 0.01:
            return audio
            
        try:
            # 軟失真：tanh壓縮
            drive = 1.0 + amount * 10.0
            distorted = np.tanh(audio * drive) / drive
            
            # 混合原始和失真信號
            return audio * (1.0 - amount) + distorted * amount
        except Exception as e:
            print(f"失真處理失敗: {e}")
            return audio
    
    def apply_compression(self, audio: np.ndarray, amount: float) -> np.ndarray:
        """應用動態壓縮"""
        if amount < 0.1:
            return audio
            
        try:
            # 簡單壓縮：降低動態範圍
            threshold = 0.5 * (1.0 - amount)  # 壓縮閾值
            ratio = 2.0 + amount * 8.0  # 壓縮比例
            
            compressed = np.copy(audio)
            mask = np.abs(compressed) > threshold
            compressed[mask] = np.sign(compressed[mask]) * (
                threshold + (np.abs(compressed[mask]) - threshold) / ratio
            )
            
            # 補償增益
            gain = 1.0 + amount * 0.5
            return compressed * gain
        except Exception as e:
            print(f"壓縮處理失敗: {e}")
            return audio
    
    def apply_eq(self, audio: np.ndarray, bass: float, mid: float, treble: float) -> np.ndarray:
        """應用三段EQ"""
        if abs(bass) < 0.05 and abs(mid) < 0.05 and abs(treble) < 0.05:
            return audio
            
        return self._apply_basic_eq(audio, bass, mid, treble)
    
    def _apply_basic_eq(self, audio: np.ndarray, bass: float, mid: float, treble: float) -> np.ndarray:
        """基礎EQ實現"""
        try:
            if SCIPY_AVAILABLE:
                # 使用butterworth濾波器
                eq_audio = np.copy(audio)
                
                # 低頻段 (80-250Hz)
                if abs(bass) > 0.05:
                    sos_bass = butter(2, [80, 250], btype='band', fs=self.sample_rate, output='sos')
                    bass_signal = sosfilt(sos_bass, audio)
                    eq_audio += bass_signal * bass
                
                # 中頻段 (250-4000Hz)  
                if abs(mid) > 0.05:
                    sos_mid = butter(2, [250, 4000], btype='band', fs=self.sample_rate, output='sos')
                    mid_signal = sosfilt(sos_mid, audio)
                    eq_audio += mid_signal * mid
                
                # 高頻段 (4000Hz+)
                if abs(treble) > 0.05:
                    sos_treble = butter(2, 4000, btype='high', fs=self.sample_rate, output='sos')
                    treble_signal = sosfilt(sos_treble, audio)
                    eq_audio += treble_signal * treble
                
                return eq_audio
            else:
                # 基礎頻率增強/衰減
                freq_weights = np.ones_like(audio)
                if bass != 0:
                    freq_weights *= (1.0 + bass * 0.3)
                if treble != 0:
                    freq_weights *= (1.0 + treble * 0.2)
                return audio * freq_weights
        except Exception as e:
            print(f"EQ處理失敗: {e}")
            return audio


class VoiceModService(QObject):
    """語音修改服務主類"""
    
    # 信號定義
    processing_started = pyqtSignal()
    processing_finished = pyqtSignal()
    processing_error = pyqtSignal(str)
    
    def __init__(self, sample_rate: int = 24000):
        super().__init__()
        self.sample_rate = sample_rate
        self.processor = AudioEffectsProcessor(sample_rate)
        
        # 默認設定
        self.current_settings = {
            'voice_profile': 'None',
            'profile_intensity': 0.7,
            'manual_mode': False,
            'effect_blend': 1.0,
            'output_volume': 0.0,  # dB
            'pitch_shift': 0.0,
            'formant_shift': 0.0,
            'reverb_amount': 0.0,
            'echo_delay': 0.0,
            'distortion': 0.0,
            'compression': 0.0,
            'eq_bass': 0.0,
            'eq_mid': 0.0,
            'eq_treble': 0.0,
        }
        
        print("語音修改服務初始化完成")
        print(f"可用功能: librosa={LIBROSA_AVAILABLE}, scipy={SCIPY_AVAILABLE}")
    
    def process_audio(self, audio: np.ndarray, settings: Optional[Dict] = None) -> np.ndarray:
        """處理音頻並應用語音修改效果"""
        try:
            self.processing_started.emit()
            
            if audio is None or len(audio) == 0:
                raise ValueError("音頻數據為空")
            
            # 使用提供的設定或當前設定
            if settings:
                current_settings = {**self.current_settings, **settings}
            else:
                current_settings = self.current_settings
            
            # 正規化音頻到 [-1, 1]
            audio = self._normalize_audio(audio)
            original_audio = np.copy(audio)
            
            # 獲取效果參數
            if current_settings['manual_mode']:
                # 手動模式：使用手動設定的參數
                effect_params = self._get_manual_params(current_settings)
            else:
                # 配置模式：使用語音配置文件
                effect_params = self._get_profile_params(
                    current_settings['voice_profile'], 
                    current_settings['profile_intensity']
                )
            
            # 應用效果
            processed_audio = self._apply_all_effects(audio, effect_params)
            
            # 效果混合
            effect_blend = current_settings.get('effect_blend', 1.0)
            if effect_blend < 1.0:
                processed_audio = (
                    original_audio * (1.0 - effect_blend) + 
                    processed_audio * effect_blend
                )
            
            # 音量調整
            output_volume_db = current_settings.get('output_volume', 0.0)
            if abs(output_volume_db) > 0.1:
                volume_factor = 10 ** (output_volume_db / 20.0)
                processed_audio *= volume_factor
            
            # 軟限制防止削波
            processed_audio = self._soft_clip(processed_audio)
            
            self.processing_finished.emit()
            return processed_audio
            
        except Exception as e:
            error_msg = f"語音修改處理失敗: {e}"
            print(error_msg)
            self.processing_error.emit(error_msg)
            return audio  # 返回原始音頻
    
    def _get_manual_params(self, settings: Dict) -> Dict:
        """獲取手動模式的效果參數"""
        return {
            'pitch_shift': settings.get('pitch_shift', 0.0),
            'formant_shift': settings.get('formant_shift', 0.0),
            'reverb_amount': settings.get('reverb_amount', 0.0),
            'echo_delay': settings.get('echo_delay', 0.0),
            'distortion': settings.get('distortion', 0.0),
            'compression': settings.get('compression', 0.0),
            'eq_bass': settings.get('eq_bass', 0.0),
            'eq_mid': settings.get('eq_mid', 0.0),
            'eq_treble': settings.get('eq_treble', 0.0),
        }
    
    def _get_profile_params(self, profile_name: str, intensity: float) -> Dict:
        """獲取語音配置文件的效果參數"""
        if profile_name not in VoiceProfile.PROFILES:
            return self._get_default_params()
        
        profile = VoiceProfile.PROFILES[profile_name]
        if not profile.get('enabled', True):
            return self._get_default_params()
        
        # 應用強度係數
        params = {}
        for key, value in profile.items():
            if key != 'enabled' and isinstance(value, (int, float)):
                params[key] = value * intensity
            else:
                params[key] = value
        
        return params
    
    def _get_default_params(self) -> Dict:
        """獲取默認效果參數（無效果）"""
        return {
            'pitch_shift': 0.0,
            'formant_shift': 0.0,
            'reverb_amount': 0.0,
            'echo_delay': 0.0,
            'distortion': 0.0,
            'compression': 0.0,
            'eq_bass': 0.0,
            'eq_mid': 0.0,
            'eq_treble': 0.0,
        }
    
    def _apply_all_effects(self, audio: np.ndarray, params: Dict) -> np.ndarray:
        """按順序應用所有音頻效果"""
        processed = np.copy(audio)
        
        # 1. 音調偏移
        if 'pitch_shift' in params and abs(params['pitch_shift']) > 0.1:
            processed = self.processor.apply_pitch_shift(processed, params['pitch_shift'])
        
        # 2. 音色偏移
        if 'formant_shift' in params and abs(params['formant_shift']) > 0.1:
            processed = self.processor.apply_formant_shift(processed, params['formant_shift'])
        
        # 3. 空間效果
        if 'reverb_amount' in params and params['reverb_amount'] > 0.05:
            processed = self.processor.apply_reverb(processed, params['reverb_amount'])
        
        if 'echo_delay' in params and params['echo_delay'] > 0.05:
            processed = self.processor.apply_echo(processed, params['echo_delay'])
        
        # 4. 失真
        if 'distortion' in params and params['distortion'] > 0.01:
            processed = self.processor.apply_distortion(processed, params['distortion'])
        
        # 5. EQ均衡
        bass = params.get('eq_bass', 0.0)
        mid = params.get('eq_mid', 0.0)
        treble = params.get('eq_treble', 0.0)
        if abs(bass) > 0.05 or abs(mid) > 0.05 or abs(treble) > 0.05:
            processed = self.processor.apply_eq(processed, bass, mid, treble)
        
        # 6. 壓縮（最後應用）
        if 'compression' in params and params['compression'] > 0.1:
            processed = self.processor.apply_compression(processed, params['compression'])
        
        return processed
    
    def _normalize_audio(self, audio: np.ndarray) -> np.ndarray:
        """正規化音頻數據"""
        if len(audio) == 0:
            return audio
            
        # 轉換為float32
        if audio.dtype != np.float32:
            if audio.dtype == np.int16:
                audio = audio.astype(np.float32) / 32768.0
            elif audio.dtype == np.int32:
                audio = audio.astype(np.float32) / 2147483648.0
            else:
                audio = audio.astype(np.float32)
        
        # 確保在 [-1, 1] 範圍內
        max_val = np.max(np.abs(audio))
        if max_val > 1.0:
            audio = audio / max_val
            
        return audio
    
    def _soft_clip(self, audio: np.ndarray) -> np.ndarray:
        """軟限制防止音頻削波"""
        return np.tanh(audio * 0.9) * 0.95
    
    def update_settings(self, settings: Dict):
        """更新語音修改設定"""
        self.current_settings.update(settings)
        
    def get_available_profiles(self) -> list:
        """獲取可用的語音配置文件列表"""
        return list(VoiceProfile.PROFILES.keys())
    
    def get_current_settings(self) -> Dict:
        """獲取當前設定"""
        return self.current_settings.copy()
    
    def reset_to_defaults(self):
        """重置為默認設定"""
        self.current_settings = {
            'voice_profile': 'None',
            'profile_intensity': 0.7,
            'manual_mode': False,
            'effect_blend': 1.0,
            'output_volume': 0.0,
            'pitch_shift': 0.0,
            'formant_shift': 0.0,
            'reverb_amount': 0.0,
            'echo_delay': 0.0,
            'distortion': 0.0,
            'compression': 0.0,
            'eq_bass': 0.0,
            'eq_mid': 0.0,
            'eq_treble': 0.0,
        }
        print("語音修改設定已重置為默認值") 