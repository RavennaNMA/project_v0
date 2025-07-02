# Location: project_v2/services/tts_service.py
# Usage: TTS 語音合成服務，用於朗讀英文字幕

import pyttsx3
import threading
import queue
import time
import re
from PyQt6.QtCore import QObject, pyqtSignal, QThread, QTimer
from utils import TTSConfigLoader


class TTSWorker(QThread):
    """TTS 工作線程，處理語音合成"""
    
    tts_started = pyqtSignal()
    tts_finished = pyqtSignal()
    tts_error = pyqtSignal(str)
    
    def __init__(self, config_loader=None):
        super().__init__()
        self.text_queue = queue.Queue()
        self.running = True
        self.engine = None
        self.current_text = ""
        
        # 加載配置
        self.config = config_loader if config_loader else TTSConfigLoader()
        
        # 驗證配置
        config_errors = self.config.validate_config()
        if config_errors:
            print("TTS配置警告:")
            for key, error in config_errors.items():
                print(f"  {error}")
        
        # 測試模式
        if self.config.get_bool('test_mode', False):
            print("TTS測試模式已啟用")
        
    def init_engine(self):
        """初始化 TTS 引擎"""
        try:
            # 根據配置選擇引擎
            engine_name = self.config.get_str('engine_priority', 'sapi5')
            
            if engine_name == 'sapi5':
                self.engine = pyttsx3.init('sapi5')
            else:
                self.engine = pyttsx3.init()
            
            # 設定語音
            self._setup_voice()
            
            # 設定語音參數
            rate = self.config.get_int('rate', 120)
            volume = self.config.get_float('volume', 0.7)
            
            self.engine.setProperty('rate', rate)
            self.engine.setProperty('volume', volume)
            
            if self.config.get_bool('verbose_logging', True):
                print(f"TTS引擎設定: 速度={rate}, 音量={volume}")
            
            # 嘗試設定音調（實驗性功能）
            pitch_adjustment = self.config.get_int('pitch_adjustment', 0)
            if pitch_adjustment != 0:
                self._try_set_pitch(pitch_adjustment)
            
            # 測試模式播放測試音頻
            if self.config.get_bool('test_mode', False):
                test_text = self.config.get_str('test_text', 'TTS test successful.')
                QTimer.singleShot(1000, lambda: self._test_speech(test_text))
            
            return True
            
        except Exception as e:
            print(f"TTS 引擎初始化失敗: {e}")
            return False
    
    def _setup_voice(self):
        """設定語音"""
        if not self.engine:
            print("TTS: 引擎未初始化")
            return
            
        try:
            voices = self.engine.getProperty('voices')
            if not voices:
                print("TTS: 未找到任何語音")
                return
            
            # 顯示可用語音（僅在詳細模式下）
            if self.config.get_bool('verbose_logging', True):
                print(f"TTS: 找到 {len(voices)} 個可用語音")
            
            selection_mode = self.config.get_str('voice_selection_mode', 'auto')
            preferred_voice_id = self.config.get_str('preferred_voice_id', '')
            
            selected_voice = None
            
            if selection_mode == 'manual' and preferred_voice_id:
                # 手動選擇指定的語音
                for voice in voices:
                    if voice.id == preferred_voice_id:
                        selected_voice = voice
                        break
                
                if selected_voice and self.engine:
                    self.engine.setProperty('voice', selected_voice.id)
                    print(f"TTS: 使用指定語音 {selected_voice.name}")
                else:
                    print(f"TTS: 未找到指定語音ID，使用自動選擇")
                    self._auto_select_voice(voices)
            else:
                # 自動選擇英文語音
                self._auto_select_voice(voices)
                
        except Exception as e:
            print(f"TTS 語音設定失敗: {e}")
    
    def _auto_select_voice(self, voices):
        """自動選擇最佳英文語音"""
        # 優先級：David > Zira > 其他英文語音 > 默認
        priority_voices = ['david', 'zira']
        
        selected_voice = None
        
        # 優先選擇 David 或 Zira
        for priority_name in priority_voices:
            for voice in voices:
                if priority_name in voice.name.lower():
                    selected_voice = voice
                    break
            if selected_voice:
                break
        
        # 如果沒找到優先語音，選擇任何英文語音
        if not selected_voice:
            for voice in voices:
                voice_name = voice.name.lower()
                if ('english' in voice_name or 'en-us' in voice_name or 
                    'en-gb' in voice_name or 'en' in voice.id.lower()):
                    selected_voice = voice
                    break
        
        # 最後備選：使用第一個語音
        if not selected_voice and voices:
            selected_voice = voices[0]
        
        if selected_voice and self.engine:
            self.engine.setProperty('voice', selected_voice.id)
            print(f"TTS: 自動選擇語音 {selected_voice.name}")
        else:
            print("TTS: 無法選擇語音")
    
    def _try_set_pitch(self, pitch_adjustment):
        """嘗試設定音調（實驗性功能）"""
        if not self.engine:
            return
            
        try:
            # 某些TTS引擎支持音調調整
            current_rate = self.engine.getProperty('rate')
            # 這是一個簡化的音調調整，實際效果取決於引擎
            adjusted_rate = max(50, min(300, current_rate + pitch_adjustment))
            
            if adjusted_rate != current_rate:
                self.engine.setProperty('rate', adjusted_rate)
                if self.config.get_bool('verbose_logging', True):
                    print(f"TTS: 音調調整應用，速度調整為 {adjusted_rate}")
        except Exception as e:
            if self.config.get_bool('verbose_logging', True):
                print(f"TTS: 音調調整不支持: {e}")
    
    def _test_speech(self, test_text):
        """測試語音"""
        if not self.engine:
            print("TTS測試失敗: 引擎未初始化")
            return
            
        try:
            print(f"TTS測試: {test_text}")
            self.engine.say(test_text)
            self.engine.runAndWait()
        except Exception as e:
            print(f"TTS測試失敗: {e}")
    
    def add_text(self, text):
        """添加文本到朗讀隊列"""
        if text and text.strip():
            self.text_queue.put(text.strip())
    
    def clear_queue(self):
        """清空朗讀隊列"""
        while not self.text_queue.empty():
            try:
                self.text_queue.get_nowait()
            except queue.Empty:
                break
    
    def stop_current(self):
        """停止當前朗讀"""
        if self.engine:
            try:
                self.engine.stop()
            except:
                pass
    
    def run(self):
        """主運行循環"""
        if not self.init_engine():
            self.tts_error.emit("TTS 引擎初始化失敗")
            return
        
        print("TTS 服務已啟動")
        
        while self.running:
            try:
                # 等待新的文本，超時1秒
                text = self.text_queue.get(timeout=1.0)
                
                if not text or not self.running:
                    continue
                
                self.current_text = text
                print(f"TTS: 開始朗讀 '{text}'")
                
                self.tts_started.emit()
                
                # 執行語音合成
                if self.engine:
                    self.engine.say(text)
                    self.engine.runAndWait()
                
                print(f"TTS: 完成朗讀 '{text}'")
                self.tts_finished.emit()
                
            except queue.Empty:
                # 超時，繼續循環
                continue
            except Exception as e:
                print(f"TTS 錯誤: {e}")
                self.tts_error.emit(str(e))
                time.sleep(0.1)
        
        print("TTS 服務已停止")
    
    def shutdown(self):
        """關閉 TTS 服務"""
        self.running = False
        self.clear_queue()
        self.stop_current()
        
        # 添加一個空項目來喚醒隊列等待
        try:
            self.text_queue.put("", timeout=0.1)
        except:
            pass


class TTSService(QObject):
    """TTS 服務主類"""
    
    # 信號定義
    tts_started = pyqtSignal()
    tts_finished = pyqtSignal()
    tts_error = pyqtSignal(str)
    
    def __init__(self, enabled=True, config_loader=None):
        super().__init__()
        self.config = config_loader if config_loader else TTSConfigLoader()
        self.enabled = enabled and self.config.get_bool('enabled', True)
        self.worker = None
        self.is_speaking = False
        
        if self.enabled:
            self.init_worker()
    
    def init_worker(self):
        """初始化 TTS 工作線程"""
        try:
            self.worker = TTSWorker(self.config)
            
            # 連接信號
            self.worker.tts_started.connect(self.on_tts_started)
            self.worker.tts_finished.connect(self.on_tts_finished)
            self.worker.tts_error.connect(self.on_tts_error)
            
            # 啟動工作線程
            self.worker.start()
            
            print("TTS 服務初始化成功")
            
        except Exception as e:
            print(f"TTS 服務初始化失敗: {e}")
            self.enabled = False
    
    def speak_text(self, text):
        """朗讀文本"""
        if not self.enabled or not self.worker or not text:
            return
        
        # 只朗讀英文文本，過濾掉中文和特殊字符
        filtered_text = self.filter_english_text(text)
        
        if filtered_text:
            print(f"TTS: 準備朗讀 '{filtered_text}'")
            self.worker.add_text(filtered_text)
        else:
            print(f"TTS: 文本過濾後為空，跳過朗讀: '{text}'")
    
    def filter_english_text(self, text):
        """過濾文本，只保留英文內容"""
        if not text:
            return ""
        
        # 是否自動清理文本
        if not self.config.get_bool('auto_clean_text', True):
            return text
        
        # 只保留英文字母、數字、空格和基本標點符號
        if self.config.get_bool('speak_punctuation', False):
            # 保留更多標點符號
            filtered = re.sub(r'[^\w\s\.\,\!\?\:\;\-\'\"\(\)\[\]]', ' ', text)
        else:
            # 簡化標點符號
            filtered = re.sub(r'[^\w\s\.\,\!\?\:\;\-\'\"]', ' ', text)
        
        # 移除多餘的空格
        filtered = re.sub(r'\s+', ' ', filtered).strip()
        
        # 檢查是否包含足夠的英文內容
        english_chars = re.findall(r'[a-zA-Z]', filtered)
        min_chars = self.config.get_int('min_english_chars', 3)
        
        if len(english_chars) < min_chars:
            return ""
        
        return filtered
    
    def stop_speaking(self):
        """停止當前朗讀"""
        if self.worker:
            self.worker.stop_current()
            self.worker.clear_queue()
        self.is_speaking = False
    
    def clear_queue(self):
        """清空朗讀隊列"""
        if self.worker:
            self.worker.clear_queue()
    
    def on_tts_started(self):
        """TTS 開始事件"""
        self.is_speaking = True
        self.tts_started.emit()
    
    def on_tts_finished(self):
        """TTS 完成事件"""
        self.is_speaking = False
        self.tts_finished.emit()
    
    def on_tts_error(self, error_msg):
        """TTS 錯誤事件"""
        print(f"TTS 錯誤: {error_msg}")
        self.is_speaking = False
        self.tts_error.emit(error_msg)
    
    def set_enabled(self, enabled):
        """設定 TTS 是否啟用"""
        self.enabled = enabled
        
        if not enabled and self.worker:
            self.stop_speaking()
    
    def is_available(self):
        """檢查 TTS 是否可用"""
        return self.enabled and self.worker is not None
    
    def shutdown(self):
        """關閉 TTS 服務"""
        if self.worker:
            self.worker.shutdown()
            self.worker.wait(3000)  # 等待最多3秒
            self.worker = None
        
        print("TTS 服務已關閉") 