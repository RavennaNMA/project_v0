# Location: project_v2/ui/caption_widget.py
# Usage: 字幕顯示元件，支援單語和雙語顯示，包含打字機效果和TTS即時同步

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QRect, QObject
from PyQt6.QtGui import QFont, QPalette, QColor, QPainter, QFontMetrics
from utils.font_manager import FontManager
import re
import time


class CaptionWidget(QWidget):
    """字幕顯示元件"""
    
    typing_complete = pyqtSignal()
    tc_typing_complete = pyqtSignal()  # TC打字完成信号
    en_typing_complete = pyqtSignal()  # EN打字完成信号
    
    def __init__(self, parent=None, scale_factor=1.0, font_size=28):
        super().__init__(parent)
        self.scale_factor = scale_factor
        self.full_text = ""
        self.current_text = ""
        self.current_index = 0
        self.is_showing = False
        
        # 雙語模式相關
        self.is_bilingual_mode = False
        self.tc_text = ""
        self.en_text = ""
        self.current_phase = ""  # "tc", "en", "simultaneous"
        self.tc_lines_cache = []
        
        # 打字機效果計時器
        self.typing_timer = QTimer()
        self.typing_timer.timeout.connect(self.type_next_character)
        
        # 設定透明背景
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAutoFillBackground(False)
        
        # 字型設定
        base_font_size = int(font_size * scale_factor)
        self.caption_font = QFont("Noto Sans CJK TC", base_font_size)
        
        # 文字邊距
        self.padding = 20
        self.line_spacing = 10
        
        # TTS同步功能
        self.tts_sync_enabled = False
        self.tts_text = ""
        self.tts_start_time = None
        self.char_timings = []  # 每個字符的預計時間點
        self.target_tts_position = 0  # TTS目標位置
        
        # 隱藏控制項
        self.hide()
        
    def show_caption(self, text, typing_speed=50):
        """顯示單語字幕"""
        self.full_text = text
        self.current_text = ""
        self.current_index = 0
        self.is_showing = True
        self.is_bilingual_mode = False
        
        self.show()
        
        # 如果啟用TTS同步，不使用常規計時器，完全依賴TTS進度
        if not self.tts_sync_enabled:
            typing_speed_int = int(typing_speed)
            self.typing_timer.start(typing_speed_int)
            print(f"啟動常規打字計時器，速度: {typing_speed_int}ms")
        else:
            print(f"TTS同步模式：等待TTS進度驅動逐字打字")
        
        self.update()
        
    def show_bilingual_caption(self, tc_text, en_text, typing_speed=50):
        """顯示雙語字幕 - 同時打字版本"""
        self.is_bilingual_mode = True
        self.tc_text = tc_text
        self.en_text = en_text
        self.current_phase = "simultaneous"  # 同時打字模式
        
        # 重置打字狀態
        self.tc_current_text = ""
        self.en_current_text = ""
        self.tc_index = 0
        self.en_index = 0
        self._tc_completed = False
        self._en_completed = False
        self.is_showing = True
        
        # 清空缓存
        self.tc_lines_cache = []
        
        self.show()
        
        # 如果啟用TTS同步，不使用常規計時器，完全依賴TTS進度
        if not self.tts_sync_enabled:
            typing_speed_int = int(typing_speed)
            self.typing_timer.start(typing_speed_int)
            print(f"雙語模式：啟動常規打字計時器，速度: {typing_speed_int}ms")
        else:
            print(f"雙語模式TTS同步：等待TTS進度驅動逐字打字")
        
        self.update()
        
    def enable_tts_sync(self, tts_text, tts_rate_wpm=140):
        """啟用TTS實時進度同步模式 - 逐字打字效果"""
        self.tts_sync_enabled = True
        self.tts_text = tts_text
        self.tts_text_length = len(tts_text)
        self.current_tts_position = 0
        self.last_valid_tts_position = 0  # 記錄最後一個有效進度
        self.target_tts_position = 0  # 目標TTS位置
        
        # 停止原來的打字計時器
        if self.typing_timer.isActive():
            self.typing_timer.stop()
            
        # 啟動更快的逐字打字計時器，與TTS進度更新頻率匹配
        self.tts_typing_timer = QTimer()
        self.tts_typing_timer.timeout.connect(self._gradual_tts_typing)
        self.tts_typing_timer.start(20)  # 25ms間隔，比TTS更新更快
        
        print(f"TTS逐字同步啟用: 字符數={len(tts_text)}, 25ms快速打字跟隨TTS進度")
        
    def update_tts_progress(self, current_pos, total_len):
        """更新TTS進度並同步字幕顯示 - 實時逐字同步"""
        if not self.tts_sync_enabled:
            return
            
        # 安全檢查：過濾異常的TTS進度值
        if current_pos < 0 or current_pos > total_len * 2:
            print(f"DEBUG: 過濾異常TTS進度: {current_pos}/{total_len}")
            return
            
        # 確保進度只能前進
        if current_pos >= self.last_valid_tts_position or current_pos < 10:
            self.last_valid_tts_position = current_pos
        else:
            current_pos = self.last_valid_tts_position
            
        # 更新目標TTS位置，讓打字計時器逐步追趕
        self.target_tts_position = current_pos
        
        print(f"📡 TTS進度更新: {current_pos}/{total_len} - 設定字幕目標位置")
            
    def update_tts_word_progress(self, current_chunk):
        """更新當前播放的文字片段"""
        if not self.tts_sync_enabled:
            return
            
        # 發出調試信息
        print(f"字幕同步到語音片段: '{current_chunk}'")
        
        # 可以在這裡添加更精細的同步邏輯
        # 例如高亮當前播放的文字片段
        self.current_speaking_chunk = current_chunk
        
        # 強制重繪以顯示當前片段
        self.update()
            
    def _sync_single_display_with_progress(self, tts_position):
        """根據TTS進度同步單語顯示"""
        if hasattr(self, 'full_text') and self.full_text:
            # 確保位置不超出文本長度
            target_index = min(tts_position, len(self.full_text))
            
            if target_index > self.current_index:
                self.current_text = self.full_text[:target_index]
                self.current_index = target_index
                
                # 調試信息
                print(f"單語字幕同步更新: 顯示到第 {target_index} 字符，內容: '{self.current_text[-20:]}'")
                
                # 強制更新顯示
                self.update()
                
                # 不要在這裡觸發完成信號，等待真正的TTS完成
                    
    def _sync_bilingual_display_with_progress(self, tts_position):
        """根據TTS進度同步雙語顯示"""
        if not (hasattr(self, 'en_text') and hasattr(self, 'tc_text')):
            return
            
        # 計算英文進度 (TTS基於英文文本)
        en_target_index = min(tts_position, len(self.en_text))
        
        # 更新英文字幕
        if en_target_index > self.en_index:
            self.en_current_text = self.en_text[:en_target_index]
            self.en_index = en_target_index
            
            # 調試信息
            print(f"英文字幕同步更新: 顯示到第 {en_target_index} 字符，內容: '{self.en_current_text[-20:]}'")
            
            # 不要在這裡觸發完成信號，等待真正的TTS完成
        
        # 根據英文進度計算中文進度
        en_progress = self.en_index / len(self.en_text) if len(self.en_text) > 0 else 0
        tc_target_index = int(en_progress * len(self.tc_text))
        
        # 更新中文字幕
        if tc_target_index > self.tc_index:
            self.tc_current_text = self.tc_text[:tc_target_index]
            self.tc_index = tc_target_index
            
            # 調試信息
            print(f"中文字幕同步更新: 顯示到第 {tc_target_index} 字符，內容: '{self.tc_current_text[-20:]}'")
            
            # 不要在這裡觸發完成信號，等待真正的TTS完成
        
        # 強制更新顯示
        self.update()
        
        # 不在這裡檢查完成，等待真正的TTS完成信號
        
    def _sync_single_display_with_progress_immediate(self, tts_position):
        """立即根據TTS進度同步單語顯示 - 真正實時"""
        if hasattr(self, 'full_text') and self.full_text:
            # 直接設置到TTS進度位置，實現真正同步
            target_index = min(tts_position, len(self.full_text))
            
            # 確保至少顯示第一個字符，即使TTS進度為0
            if target_index == 0 and tts_position > 0:
                target_index = 1
            
            if target_index != self.current_index:
                self.current_index = target_index
                self.current_text = self.full_text[:self.current_index]
                
                # 顯示當前字符
                if target_index > 0:
                    current_char = self.full_text[target_index-1] if target_index <= len(self.full_text) else ''
                    display_char = '[SPACE]' if current_char == ' ' else current_char
                    print(f"🎯 實時同步: 第{target_index}字 -> '{display_char}' (TTS: {tts_position})")
                
                self.update()
                
    def _sync_bilingual_display_with_progress_immediate(self, tts_position):
        """立即根據TTS進度同步雙語顯示 - 真正實時"""
        if not (hasattr(self, 'en_text') and hasattr(self, 'tc_text')):
            return
            
        # 英文直接同步到TTS位置
        en_target_index = min(tts_position, len(self.en_text))
        
        if en_target_index != self.en_index:
            self.en_index = en_target_index
            self.en_current_text = self.en_text[:self.en_index]
            
            if en_target_index > 0:
                current_char = self.en_text[en_target_index-1] if en_target_index <= len(self.en_text) else ''
                display_char = '[SPACE]' if current_char == ' ' else current_char
                print(f"🎯 英文實時同步: 第{en_target_index}字 -> '{display_char}' (TTS: {tts_position})")
            
        # 中文按比例同步
        en_progress = self.en_index / len(self.en_text) if len(self.en_text) > 0 else 0
        tc_target_index = int(en_progress * len(self.tc_text))
        
        if tc_target_index != self.tc_index:
            self.tc_index = tc_target_index
            self.tc_current_text = self.tc_text[:self.tc_index]
            
            if tc_target_index > 0:
                current_char = self.tc_text[tc_target_index-1] if tc_target_index <= len(self.tc_text) else ''
                print(f"🎯 中文實時同步: 第{tc_target_index}字 -> '{current_char}' (進度: {en_progress:.2f})")
        
        self.update()
        
    def _gradual_tts_typing(self):
        """逐字打字追趕TTS進度 - 真正的打字效果"""
        if not self.tts_sync_enabled:
            return
            
        if self.is_bilingual_mode:
            self._gradual_bilingual_typing()
        else:
            self._gradual_single_typing()
            
    def _gradual_single_typing(self):
        """單語逐字追趕TTS進度"""
        if not hasattr(self, 'full_text') or not self.full_text:
            return
            
        # 計算需要追趕的距離
        distance = self.target_tts_position - self.current_index
        
        # 智能追趕：如果落後太多，一次打多個字；如果接近，正常打字
        if distance > 0:
            if distance > 10:
                # 落後很多時，快速追趕（一次打2-3個字）
                step = min(3, distance, len(self.full_text) - self.current_index)
            elif distance > 5:
                # 中等落後，稍快打字（一次打2個字）
                step = min(2, distance, len(self.full_text) - self.current_index)
            else:
                # 接近同步，正常逐字打字
                step = 1
            
            if self.current_index < len(self.full_text):
                self.current_index += step
                self.current_text = self.full_text[:self.current_index]
                
                # 顯示當前打字字符
                if step == 1:
                    current_char = self.full_text[self.current_index-1] if self.current_index > 0 else ''
                    display_char = '[SPACE]' if current_char == ' ' else current_char
                    print(f"⌨️ 逐字打字: 第{self.current_index}字 -> '{display_char}' (目標:{self.target_tts_position})")
                else:
                    print(f"⚡ 快速追趕: +{step}字 -> 第{self.current_index}字 (目標:{self.target_tts_position}, 距離:{distance})")
                
                self.update()
            
    def _gradual_bilingual_typing(self):
        """雙語逐字追趕TTS進度"""
        if not (hasattr(self, 'en_text') and hasattr(self, 'tc_text')):
            return
            
        # 計算英文需要追趕的距離
        en_distance = self.target_tts_position - self.en_index
        
        # 英文智能追趕TTS進度
        if en_distance > 0 and self.en_index < len(self.en_text):
            if en_distance > 10:
                # 落後很多時，快速追趕
                en_step = min(3, en_distance, len(self.en_text) - self.en_index)
            elif en_distance > 5:
                # 中等落後，稍快打字
                en_step = min(2, en_distance, len(self.en_text) - self.en_index)
            else:
                # 接近同步，正常逐字打字
                en_step = 1
            
            self.en_index += en_step
            self.en_current_text = self.en_text[:self.en_index]
            
            if en_step == 1:
                current_char = self.en_text[self.en_index-1] if self.en_index > 0 else ''
                display_char = '[SPACE]' if current_char == ' ' else current_char
                print(f"⌨️ 英文逐字: 第{self.en_index}字 -> '{display_char}' (目標:{self.target_tts_position})")
            else:
                print(f"⚡ 英文快速追趕: +{en_step}字 -> 第{self.en_index}字 (距離:{en_distance})")
            
        # 中文按比例追趕
        en_progress = self.en_index / len(self.en_text) if len(self.en_text) > 0 else 0
        tc_target = int(en_progress * len(self.tc_text))
        tc_distance = tc_target - self.tc_index
        
        if tc_distance > 0 and self.tc_index < len(self.tc_text):
            if tc_distance > 5:
                # 中文追趕可以更快一些，因為中文通常較短
                tc_step = min(2, tc_distance, len(self.tc_text) - self.tc_index)
            else:
                tc_step = 1
                
            self.tc_index += tc_step
            self.tc_current_text = self.tc_text[:self.tc_index]
            
            if tc_step == 1:
                current_char = self.tc_text[self.tc_index-1] if self.tc_index > 0 else ''
                print(f"⌨️ 中文逐字: 第{self.tc_index}字 -> '{current_char}' (目標:{tc_target})")
            else:
                print(f"⚡ 中文快速追趕: +{tc_step}字 -> 第{self.tc_index}字")
            
        self.update()
        
    def _tts_sync_typing(self):
        """TTS同步的逐字打字效果"""
        if not self.tts_sync_enabled:
            return
            
        # 根據當前TTS進度決定應該顯示到哪個字符
        target_index = min(self.current_tts_position, self.tts_text_length)
        
        if self.is_bilingual_mode:
            self._tts_sync_bilingual_typing(target_index)
        else:
            self._tts_sync_single_typing(target_index)
            
    def _tts_sync_single_typing(self, target_index):
        """TTS同步的單語逐字打字"""
        if hasattr(self, 'full_text') and self.full_text:
            # 逐字推進到目標位置
            if target_index > self.current_index:
                # 一次只推進一個字符，實現逐字效果
                self.current_index += 1
                self.current_text = self.full_text[:self.current_index]
                
                # 顯示當前字符（如果是空格則顯示 [SPACE]）
                current_char = self.current_text[-1:] if self.current_text else ''
                display_char = '[SPACE]' if current_char == ' ' else current_char
                print(f"逐字打字: 第{self.current_index}字 -> '{display_char}' (TTS進度:{target_index})")
                
                self.update()
                
    def _tts_sync_bilingual_typing(self, target_index):
        """TTS同步的雙語逐字打字"""
        if not (hasattr(self, 'en_text') and hasattr(self, 'tc_text')):
            return
            
        # 計算英文應該顯示到的位置
        en_target_index = min(target_index, len(self.en_text))
        
        # 逐字推進英文
        if en_target_index > self.en_index:
            self.en_index += 1
            self.en_current_text = self.en_text[:self.en_index]
            
            print(f"英文逐字: 第{self.en_index}字 -> '{self.en_current_text[-1:]}' (目標:{en_target_index})")
            
        # 根據英文進度計算中文進度
        en_progress = self.en_index / len(self.en_text) if len(self.en_text) > 0 else 0
        tc_target_index = int(en_progress * len(self.tc_text))
        
        # 逐字推進中文
        if tc_target_index > self.tc_index:
            self.tc_index += 1
            self.tc_current_text = self.tc_text[:self.tc_index]
            
            print(f"中文逐字: 第{self.tc_index}字 -> '{self.tc_current_text[-1:]}' (目標:{tc_target_index})")
        
        self.update()
        
    def _sync_with_tts(self):
        """與TTS即時同步"""
        if not self.tts_sync_enabled or not self.tts_start_time:
            return
            
        current_time = time.time()
        elapsed_time = current_time - self.tts_start_time
        
        # 找到當前應該顯示到哪個字符
        target_index = 0
        for i, char_time in enumerate(self.char_timings):
            if elapsed_time >= char_time:
                target_index = i + 1
            else:
                break
        
        # 更新顯示
        if self.is_bilingual_mode:
            # 雙語模式：同步更新兩種語言
            self._sync_bilingual_display(target_index)
        else:
            # 單語模式
            if target_index > self.current_index:
                self.current_text = self.full_text[:target_index]
                self.current_index = target_index
                self.update()
                
                if self.current_index >= len(self.full_text):
                    print("All caption typing complete")
                    self.typing_complete.emit()
                    
    def _sync_bilingual_display(self, en_target_index):
        """同步雙語顯示"""
        # 更新英文
        if en_target_index > self.en_index and self.en_index < len(self.en_text):
            self.en_current_text = self.en_text[:en_target_index]
            self.en_index = en_target_index
            
            if self.en_index >= len(self.en_text) and not self._en_completed:
                self._en_completed = True
                self.en_typing_complete.emit()
        
        # 計算中文應該顯示的比例
        en_progress = self.en_index / len(self.en_text) if len(self.en_text) > 0 else 0
        tc_target_index = int(en_progress * len(self.tc_text))
        
        # 更新中文
        if tc_target_index > self.tc_index and self.tc_index < len(self.tc_text):
            self.tc_current_text = self.tc_text[:tc_target_index]
            self.tc_index = tc_target_index
            
            if self.tc_index >= len(self.tc_text) and not self._tc_completed:
                self._tc_completed = True
                self.tc_typing_complete.emit()
        
        self.update()
        
        # 檢查是否都完成
        if self._tc_completed and self._en_completed:
            print("All caption typing complete")
            self.typing_complete.emit()
            
    def disable_tts_sync(self):
        """禁用TTS同步，並立即完成字幕顯示 - 在真正TTS完成時調用"""
        if not self.tts_sync_enabled:
            return
            
        print("TTS真正完成，觸發字幕完成信號")
        self.tts_sync_enabled = False
        self.tts_start_time = None
        
        # 停止逐字打字計時器
        if hasattr(self, 'tts_typing_timer') and self.tts_typing_timer.isActive():
            self.tts_typing_timer.stop()
        
        # 立即完成所有字幕顯示
        if self.is_bilingual_mode:
            # 完成雙語顯示
            if hasattr(self, 'tc_text') and hasattr(self, 'en_text'):
                self.tc_current_text = self.tc_text
                self.en_current_text = self.en_text
                self.tc_index = len(self.tc_text)
                self.en_index = len(self.en_text)
                
                if not getattr(self, '_tc_completed', False):
                    self._tc_completed = True
                    print("TC typing complete")
                    self.tc_typing_complete.emit()
                    
                if not getattr(self, '_en_completed', False):
                    self._en_completed = True
                    print("EN typing complete")
                    self.en_typing_complete.emit()
                    
                print("All caption typing complete")
                self.typing_complete.emit()
        else:
            # 完成單語顯示
            if hasattr(self, 'full_text'):
                self.current_text = self.full_text
                self.current_index = len(self.full_text)
                print("All caption typing complete")
                self.typing_complete.emit()
        
        self.update()
            
        if hasattr(self, 'char_timings'):
            self.char_timings = []

    def type_next_character(self):
        """打字機效果 - 如果啟用TTS同步則跳過"""
        if self.tts_sync_enabled:
            return
            
        if self.is_bilingual_mode and self.current_phase == "simultaneous":
            self._handle_simultaneous_typing()
        else:
            self._handle_single_typing()
    
    def _handle_single_typing(self):
        """處理單語打字"""
        if self.current_index < len(self.full_text):
            self.current_text = self.full_text[:self.current_index + 1]
            self.current_index += 1
            self.update()
        else:
            self.typing_timer.stop()
            self.typing_complete.emit()
    
    def _handle_simultaneous_typing(self):
        """處理同時打字模式 - 改進的同步算法"""
        tc_total = len(self.tc_text)
        en_total = len(self.en_text)
        
        # 計算當前進度
        tc_progress = self.tc_index / tc_total if tc_total > 0 else 1.0
        en_progress = self.en_index / en_total if en_total > 0 else 1.0
        
        # 決定要推進哪個語言
        tc_advancing = False
        en_advancing = False
        
        # 如果兩個都還沒完成
        if not self._tc_completed and not self._en_completed:
            # 比較進度，推進落後的那個
            if tc_progress <= en_progress and self.tc_index < tc_total:
                tc_advancing = True
            if en_progress <= tc_progress and self.en_index < en_total:
                en_advancing = True
            
            # 確保至少有一個在推進
            if not tc_advancing and not en_advancing:
                if self.tc_index < tc_total:
                    tc_advancing = True
                elif self.en_index < en_total:
                    en_advancing = True
        else:
            # 如果其中一個完成了，繼續推進另一個
            if not self._tc_completed and self.tc_index < tc_total:
                tc_advancing = True
            if not self._en_completed and self.en_index < en_total:
                en_advancing = True
        
        # 執行推進
        if tc_advancing:
            self.tc_current_text = self.tc_text[:self.tc_index + 1]
            self.tc_index += 1
            
            if self.tc_index >= tc_total:
                self._tc_completed = True
                self.tc_typing_complete.emit()
                
        if en_advancing:
            self.en_current_text = self.en_text[:self.en_index + 1]
            self.en_index += 1
            
            if self.en_index >= en_total:
                self._en_completed = True
                self.en_typing_complete.emit()
        
        self.update()
        
        # 檢查是否都完成
        if self._tc_completed and self._en_completed:
            self.typing_timer.stop()
            self.typing_complete.emit()
            
    def hide(self):
        """隱藏字幕"""
        self.typing_timer.stop()
        
        # 停止TTS逐字打字計時器
        if hasattr(self, 'tts_typing_timer') and self.tts_typing_timer.isActive():
            self.tts_typing_timer.stop()
        
        self.current_text = ""
        self.is_showing = False
        self.is_bilingual_mode = False
        self.tc_lines_cache = []
        
        # 重置狀態
        self.tc_current_text = ""
        self.en_current_text = ""
        self._tc_completed = False
        self._en_completed = False
        
        # 重置TTS同步
        self.disable_tts_sync()
            
        super().hide()
        
    def paintEvent(self, event):
        """繪製字幕和背景"""
        if not self.is_showing:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        painter.setFont(self.caption_font)
        metrics = QFontMetrics(self.caption_font)
        
        if self.is_bilingual_mode:
            self._paint_bilingual(painter, metrics)
        else:
            self._paint_single_language(painter, metrics)
                
    def _paint_single_language(self, painter, metrics):
        """繪製單語字幕"""
        if not self.current_text:
            return
            
        lines = self._wrap_text(self.current_text, metrics)
        line_height = metrics.height()
        total_height = len(lines) * (line_height + self.line_spacing) - self.line_spacing + 2 * self.padding
        y_offset = self.height() - total_height
        
        for i, line in enumerate(lines):
            if line.strip():
                self._draw_text_line(painter, line, i, y_offset, line_height, metrics)
                
    def _paint_bilingual(self, painter, metrics):
        """繪製雙語字幕"""
        line_height = metrics.height()
        
        tc_lines = []
        en_lines = []
        
        if hasattr(self, 'tc_current_text') and self.tc_current_text:
            tc_lines = self._wrap_text(self.tc_current_text, metrics)
        
        if hasattr(self, 'en_current_text') and self.en_current_text:
            en_lines = self._wrap_text(self.en_current_text, metrics)
        
        total_lines = len(tc_lines) + len(en_lines)
        if total_lines > 0 and len(tc_lines) > 0 and len(en_lines) > 0:
            total_lines += 1  # 語言之間的間隔
            
        total_height = total_lines * (line_height + self.line_spacing) - self.line_spacing + 2 * self.padding
        y_offset = self.height() - total_height
        
        current_line = 0
        
        # 繪製中文
        for line in tc_lines:
            if line.strip():
                self._draw_text_line(painter, line, current_line, y_offset, line_height, metrics)
            current_line += 1
            
        # 語言之間的間隔
        if len(tc_lines) > 0 and len(en_lines) > 0:
            current_line += 1
            
        # 繪製英文
        for line in en_lines:
            if line.strip():
                self._draw_text_line(painter, line, current_line, y_offset, line_height, metrics)
            current_line += 1
                
    def _draw_text_line(self, painter, line, line_index, y_offset, line_height, metrics):
        """繪製單行文本"""
        line_width = metrics.horizontalAdvance(line)
        
        bg_x = (self.width() - line_width) // 2 - self.padding
        bg_y = y_offset + line_index * (line_height + self.line_spacing) - 5
        bg_width = line_width + 2 * self.padding
        bg_height = line_height + 10
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(0, 0, 0, 180))
        painter.drawRoundedRect(bg_x, bg_y, bg_width, bg_height, 5, 5)
        
        painter.setPen(QColor(255, 255, 255))
        text_x = (self.width() - line_width) // 2
        text_y = y_offset + line_index * (line_height + self.line_spacing) + line_height - 5
        painter.drawText(text_x, text_y, line)

    def _wrap_text(self, text, metrics):
        """文字自動換行"""
        if not text:
            return []
            
        text = self._clean_text_for_display(text)
        lines = []
        max_width = self.width() - 2 * self.padding
        
        # 檢測是否為中文文本
        chinese_char_count = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
        total_char_count = len(text)
        is_mostly_chinese = chinese_char_count > total_char_count * 0.5
        
        if is_mostly_chinese:
            # 中文按字符換行
            lines = self._wrap_by_character(text, metrics, max_width)
        else:
            # 英文按單詞換行
            words = text.split(' ')
            current_line = ""
            
            for word in words:
                test_line = current_line + (' ' if current_line else '') + word
                line_width = metrics.horizontalAdvance(test_line)
                
                if line_width > max_width and current_line:
                    lines.append(current_line.strip())
                    current_line = word
                else:
                    current_line = test_line
                    
            if current_line.strip():
                lines.append(current_line.strip())
        
        return lines

    def _clean_text_for_display(self, text):
        """清理文本，避免顯示問題"""
        if not text:
            return text
        
        # 移除不可見字符
        text = re.sub(r'[^\x00-\x7F\u4e00-\u9fff]+', ' ', text)
        
        # 合併多個空格
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()

    def _wrap_by_character(self, text, metrics, max_width):
        """按字符換行（主要用於中文）"""
        lines = []
        current_line = ""
        
        for char in text:
            test_line = current_line + char
            line_width = metrics.horizontalAdvance(test_line)
            
            if line_width > max_width and current_line:
                lines.append(current_line)
                current_line = char
            else:
                current_line = test_line
                
        if current_line:
            lines.append(current_line)
            
        return lines