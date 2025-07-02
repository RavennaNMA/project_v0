# Location: project_v2/services/tts_service.py
# Usage: TTS 語音合成服務，用於朗讀英文字幕，支援即時同步

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
    tts_progress = pyqtSignal(int, int)  # (當前字符位置, 總字符數)
    
    def __init__(self, config_loader=None):
        super().__init__()
        self.text_queue = queue.Queue()
        self.running = True
        self.engine = None
        self.current_text = ""
        self.is_speaking = False
        
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
        
        # 初始化進度追蹤
        self.current_position = 0
        self.text_length = 0
        
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
            
            # 嘗試設定音調（實驗性功能）
            pitch_adjustment = self.config.get_int('pitch_adjustment', 0)
            if pitch_adjustment != 0:
                self._try_set_pitch(pitch_adjustment)
            
            # 設定語音事件回調
            self._setup_callbacks()
            
            if self.config.get_bool('verbose_logging', True):
                print(f"TTS引擎設定: 速度={rate}, 音量={volume}")
            
            # 測試模式播放測試音頻
            if self.config.get_bool('test_mode', False):
                test_text = self.config.get_str('test_text', 'TTS test successful.')
                QTimer.singleShot(1000, lambda: self._test_speech(test_text))
            
            return True
            
        except Exception as e:
            print(f"TTS 引擎初始化失敗: {e}")
            return False
    
    def _setup_callbacks(self):
        """設定TTS事件回調"""
        if not self.engine:
            return
            
        try:
            # 連接語音事件
            self.engine.connect('started-utterance', self._on_speech_start)
            self.engine.connect('started-word', self._on_word)
            self.engine.connect('finished-utterance', self._on_speech_end)
        except Exception as e:
            print(f"TTS回調設定失敗: {e}")
    
    def _on_speech_start(self, name):
        """語音開始事件"""
        self.is_speaking = True
        self.current_position = 0
        
    def _on_word(self, name, location, length):
        """單詞朗讀事件"""
        try:
            if location is not None and length is not None:
                self.current_position = location + length
                if self.text_length > 0:
                    self.tts_progress.emit(self.current_position, self.text_length)
        except Exception as e:
            # 有些TTS引擎可能不完全支持word事件
            if self.config.get_bool('verbose_logging', True):
                print(f"TTS word event error: {e}")
    
    def _on_speech_end(self, name, completed):
        """語音結束事件"""
        self.is_speaking = False
        
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
            # 嘗試直接設定pitch屬性（某些引擎支持）
            current_pitch = self.engine.getProperty('pitch')
            if current_pitch is not None:
                # pitch通常是0-200的範圍，100是正常
                new_pitch = 100 + pitch_adjustment
                new_pitch = max(0, min(200, new_pitch))
                self.engine.setProperty('pitch', new_pitch)
                print(f"TTS: 音調設定為 {new_pitch}")
            else:
                # 如果不支持pitch，嘗試通過調整rate來模擬
                current_rate = self.engine.getProperty('rate')
                # 音調調整可以稍微影響速度
                adjusted_rate = current_rate + (pitch_adjustment * 0.5)
                adjusted_rate = max(50, min(300, adjusted_rate))
                self.engine.setProperty('rate', int(adjusted_rate))
                if self.config.get_bool('verbose_logging', True):
                    print(f"TTS: 通過速度調整模擬音調，速度={adjusted_rate}")
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
                # 等待新的文本，超時設定從配置讀取
                timeout = self.config.get_float('queue_timeout', 1.0)
                text = self.text_queue.get(timeout=timeout)
                
                if not text or not self.running:
                    continue
                
                self.current_text = text
                self.text_length = len(text)
                self.current_position = 0
                
                print(f"TTS: 開始朗讀 '{text}'")
                
                self.tts_started.emit()
                
                # 處理文本中的停頓標記
                processed_text = self._process_text_pauses(text)
                
                # 執行語音合成
                if self.engine:
                    self.engine.say(processed_text)
                    self.engine.runAndWait()
                
                print(f"TTS: 完成朗讀 '{text}'")
                self.tts_finished.emit()
                
                # 文本處理延遲
                delay = self.config.get_int('text_processing_delay', 100)
                if delay > 0:
                    time.sleep(delay / 1000.0)
                
            except queue.Empty:
                # 超時，繼續循環
                continue
            except Exception as e:
                print(f"TTS 錯誤: {e}")
                self.tts_error.emit(str(e))
                
                # 錯誤重試
                retry_count = self.config.get_int('error_retry_count', 2)
                if retry_count > 0:
                    time.sleep(0.5)
                    # 重新初始化引擎
                    self.init_engine()
        
        print("TTS 服務已停止")
    
    def _process_text_pauses(self, text):
        """處理文本中的停頓標記"""
        # 支援的停頓標記：
        # [pause:0.5] - 停頓0.5秒
        # ... - 自然停頓
        # , - 短停頓
        # . - 句子停頓
        
        processed = text
        
        # 處理自定義停頓標記
        import re
        pause_pattern = r'\[pause:(\d+\.?\d*)\]'
        
        # 某些TTS引擎支持SSML標記
        if self.config.get_bool('use_ssml', False):
            # 替換為SSML停頓標記
            processed = re.sub(pause_pattern, r'<break time="\1s"/>', processed)
            # 包裝在SSML標籤中
            processed = f'<speak>{processed}</speak>'
        else:
            # 移除停頓標記（大多數引擎不支持）
            processed = re.sub(pause_pattern, '', processed)
        
        # 加強標點符號的停頓效果
        if self.config.get_bool('enhance_punctuation_pauses', True):
            # 在句號後加入稍長停頓
            processed = processed.replace('. ', '... ')
            # 在逗號後加入短停頓
            processed = processed.replace(', ', ',, ')
        
        return processed
    
    def get_estimated_duration(self, text):
        """估算文本朗讀時長"""
        if not text:
            return 0.0
            
        # 基於配置的語速估算
        rate = self.config.get_int('rate', 120)  # words per minute
        
        # 簡單估算：假設平均每個單詞5個字符
        words = len(text.split())
        if words == 0:
            # 按字符估算
            words = len(text) / 5.0
        
        # 計算基礎時長（秒）
        duration = (words / rate) * 60.0
        
        # 考慮停頓
        # 句號停頓
        sentence_count = text.count('.')
        duration += sentence_count * 0.5
        
        # 逗號停頓
        comma_count = text.count(',')
        duration += comma_count * 0.2
        
        return duration
    
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
    tts_progress = pyqtSignal(int, int)  # (當前字符位置, 總字符數)
    
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
            self.worker.tts_progress.connect(self.on_tts_progress)
            
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
            # 如果配置了自動停止上一個
            if self.config.get_bool('auto_stop_previous', False):
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
    
    def on_tts_progress(self, current_pos, total_len):
        """TTS 進度更新"""
        self.tts_progress.emit(current_pos, total_len)
    
    def set_enabled(self, enabled):
        """設定 TTS 是否啟用"""
        self.enabled = enabled
        
        if not enabled and self.worker:
            self.stop_speaking()
    
    def is_available(self):
        """檢查 TTS 是否可用"""
        return self.enabled and self.worker is not None
    
    def get_estimated_duration(self, text):
        """獲取預估朗讀時長"""
        if self.worker:
            return self.worker.get_estimated_duration(text)
        return 0.0
    
    def shutdown(self):
        """關閉 TTS 服務"""
        if self.worker:
            self.worker.shutdown()
            self.worker.wait(3000)  # 等待最多3秒
            self.worker = None
        
        print("TTS 服務已關閉")