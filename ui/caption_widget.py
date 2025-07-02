# Location: project_v2/ui/caption_widget.py
# Usage: 字幕顯示元件，支援單語和雙語顯示，包含打字機效果和TTS同步

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
        self.font = QFont("Noto Sans CJK TC", base_font_size)
        
        # 文字邊距
        self.padding = 20
        self.line_spacing = 10  # 進一步增加行距從15到20
        
        # TTS同步功能
        self.tts_sync_enabled = False
        self.tts_text = ""
        self.tts_start_time = None
        self.char_timings = []  # 每個字符的預計時間點
        
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
        
        # 如果啟用TTS同步，不使用常規計時器
        if not self.tts_sync_enabled:
            self.typing_timer.start(typing_speed)
        
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
        
        # 如果啟用TTS同步，不使用常規計時器
        if not self.tts_sync_enabled:
            typing_speed_int = int(typing_speed)
            self.typing_timer.start(typing_speed_int)
        
        self.update()
        
    def enable_tts_sync(self, tts_text, tts_rate_wpm=140):
        """啟用TTS實時同步模式"""
        self.tts_sync_enabled = True
        self.tts_text = tts_text
        self.tts_start_time = time.time()
        
        # 計算每個字符的預計時間點（加入延遲緩衝）
        self.char_timings = []
        words = tts_text.split()
        current_time = 0.2  # 加入200ms的初始延遲，讓TTS有時間開始
        char_index = 0
        
        # 為每個單詞分配時間
        for word in words:
            word_duration = 60.0 / tts_rate_wpm  # 每個單詞的時間
            
            # 在單詞內平均分配字符時間，但加入額外延遲
            for i, char in enumerate(word):
                # 字符在朗讀中稍微延後出現（朗讀到一半時才顯示）
                char_delay_ratio = 0.6  # 字符在單詞朗讀60%時出現
                char_time = current_time + (i / len(word) + char_delay_ratio) * word_duration
                if char_index < len(tts_text):
                    self.char_timings.append(char_time)
                    char_index += 1
            
            # 空格時間（單詞結束後）
            if char_index < len(tts_text):
                self.char_timings.append(current_time + word_duration)
                char_index += 1
                
            current_time += word_duration
        
        # 確保所有字符都有時間點
        while len(self.char_timings) < len(tts_text):
            self.char_timings.append(current_time)
            current_time += 0.1
        
        # 平滑推進相關變量
        self.last_update_time = time.time()
        self.pending_chars = 0  # 待顯示的字符數
        self.smooth_interval = 0.05  # 50ms平滑間隔
        
        # 停止原來的打字計時器，使用較低頻率的平滑檢查
        if self.typing_timer.isActive():
            self.typing_timer.stop()
            
        # 啟動平滑同步檢查（每50ms檢查一次，但平滑推進）
        self.sync_timer = QTimer()
        self.sync_timer.timeout.connect(self._sync_with_tts_smooth)
        self.sync_timer.start(50)  # 50ms間隔，平衡性能和流暢度
        
        print(f"TTS平滑同步啟用: 字符數={len(tts_text)}, 詞數={len(words)}")
        
    def _sync_with_tts_smooth(self):
        """與TTS實時同步 - 平滑版本"""
        if not self.tts_sync_enabled or not self.tts_start_time:
            return
            
        current_time = time.time()
        elapsed_time = current_time - self.tts_start_time
        
        # 計算當前應該顯示到哪個字符
        if self.is_bilingual_mode:
            current_pos = self.en_index
            target_text = self.en_text
        else:
            current_pos = self.current_index
            target_text = self.full_text
        
        # 找到理想的目標位置（但不會太超前）
        ideal_target_pos = current_pos
        for i in range(current_pos, len(target_text)):
            if i < len(self.char_timings) and self.char_timings[i] <= elapsed_time:
                ideal_target_pos = i + 1
            else:
                break
        
        # 計算實際要推進的字符數（平滑控制）
        chars_behind = ideal_target_pos - current_pos
        
        if chars_behind > 0:
            # 計算平滑推進速度
            time_since_last_update = current_time - self.last_update_time
            
            if chars_behind <= 2:
                # 輕微落後，正常速度推進
                chars_to_advance = 1
            elif chars_behind <= 5:
                # 中等落後，稍快推進
                chars_to_advance = min(2, chars_behind)
            else:
                # 嚴重落後，快速追趕但不超過限制
                chars_to_advance = min(3, chars_behind)
            
            # 避免推進太快：確保不會超前超過2個字符
            future_pos = current_pos + chars_to_advance
            max_advance_pos = current_pos + 2
            
            # 檢查未來位置是否過於超前
            if future_pos < len(self.char_timings):
                future_target_time = self.char_timings[future_pos - 1]
                if future_target_time > elapsed_time + 0.3:  # 如果會超前300ms以上
                    chars_to_advance = 1  # 只推進1個字符
            
            chars_to_advance = min(chars_to_advance, max_advance_pos - current_pos)
            
            if chars_to_advance > 0:
                self._advance_characters_smooth(chars_to_advance)
                self.last_update_time = current_time
                
                # 調試信息（降低頻率）
                if current_pos % 100 == 0 or current_pos < 20:
                    print(f"平滑同步: 位置{current_pos + chars_to_advance}/{len(target_text)}, 落後{chars_behind}字符, 推進{chars_to_advance}, 時間{elapsed_time:.1f}s")
        
        elif chars_behind < -2:
            # 如果超前太多，暫停一下
            pass
    
    def _advance_characters_smooth(self, chars_to_advance):
        """平滑推進字符 - 改進雙語同步版本"""
        if self.is_bilingual_mode:
            # 推進英文
            new_en_pos = min(self.en_index + chars_to_advance, len(self.en_text))
            self.en_current_text = self.en_text[:new_en_pos]
            self.en_index = new_en_pos
            
            # 計算理想的中英文同步推進
            if not self._tc_completed and self.tc_index < len(self.tc_text):
                # 計算當前進度
                en_progress = self.en_index / len(self.en_text) if len(self.en_text) > 0 else 0
                tc_progress = self.tc_index / len(self.tc_text) if len(self.tc_text) > 0 else 0
                
                # 目標：中文進度應該等於英文進度
                target_tc_pos = int(en_progress * len(self.tc_text))
                tc_chars_needed = target_tc_pos - self.tc_index
                
                # 確保中文至少推進1個字符（避免停滯）
                if tc_chars_needed <= 0 and en_progress > tc_progress:
                    tc_chars_needed = 1
                
                # 限制中文推進速度（避免跳躍太快）
                max_tc_advance = max(1, chars_to_advance + 1)  # 中文可以比英文稍快一點
                tc_chars_to_add = min(tc_chars_needed, max_tc_advance)
                tc_chars_to_add = max(0, tc_chars_to_add)  # 確保不為負數
                
                if tc_chars_to_add > 0:
                    new_tc_pos = min(self.tc_index + tc_chars_to_add, len(self.tc_text))
                    self.tc_current_text = self.tc_text[:new_tc_pos]
                    self.tc_index = new_tc_pos
                
                # 調試同步信息
                if self.en_index % 50 == 0 or self.en_index < 30:
                    print(f"雙語同步: EN {self.en_index}/{len(self.en_text)}({en_progress:.2%}), TC {self.tc_index}/{len(self.tc_text)}({tc_progress:.2%}), 推進TC={tc_chars_to_add}")
                
                if self.tc_index >= len(self.tc_text):
                    self._tc_completed = True
                    self.tc_typing_complete.emit()
            
            if self.en_index >= len(self.en_text):
                self._en_completed = True
                self.en_typing_complete.emit()
                
            if self._tc_completed and self._en_completed:
                self._finish_sync_typing()
        else:
            # 單語模式
            new_pos = min(self.current_index + chars_to_advance, len(self.full_text))
            self.current_text = self.full_text[:new_pos]
            self.current_index = new_pos
            
            if self.current_index >= len(self.full_text):
                self._finish_sync_typing()
        
        self.update()
        
    def _finish_sync_typing(self):
        """完成同步打字"""
        if hasattr(self, 'sync_timer'):
            self.sync_timer.stop()
        print("TTS同步打字完成")
        self.typing_complete.emit()
        
    def disable_tts_sync(self):
        """禁用TTS同步"""
        self.tts_sync_enabled = False
        self.tts_start_time = None
        
        if hasattr(self, 'sync_timer'):
            self.sync_timer.stop()
            
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
        """處理同時打字模式"""
        tc_advancing = not self._tc_completed and self.tc_index < len(self.tc_text)
        en_advancing = not self._en_completed and self.en_index < len(self.en_text)
        
        if tc_advancing:
            self.tc_current_text = self.tc_text[:self.tc_index + 1]
            self.tc_index += 1
            
        if en_advancing:
            self.en_current_text = self.en_text[:self.en_index + 1]
            self.en_index += 1
        
        if tc_advancing and self.tc_index >= len(self.tc_text):
            self._tc_completed = True
            self.tc_typing_complete.emit()
            
        if en_advancing and self.en_index >= len(self.en_text):
            self._en_completed = True
            self.en_typing_complete.emit()
        
        self.update()
        
        if self._tc_completed and self._en_completed:
            self.typing_timer.stop()
            self.typing_complete.emit()
            
    def hide(self):
        """隱藏字幕"""
        self.typing_timer.stop()
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
        
        painter.setFont(self.font)
        metrics = QFontMetrics(self.font)
        
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
            total_lines += 1
            
        total_height = total_lines * (line_height + self.line_spacing) - self.line_spacing + 2 * self.padding
        y_offset = self.height() - total_height
        
        current_line = 0
        for line in tc_lines:
            if line.strip():
                self._draw_text_line(painter, line, current_line, y_offset, line_height, metrics)
            current_line += 1
            
        if len(tc_lines) > 0 and len(en_lines) > 0:
            current_line += 1
            
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
        
        chinese_char_count = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
        total_char_count = len(text)
        is_mostly_chinese = chinese_char_count > total_char_count * 0.5
        
        if is_mostly_chinese:
            lines = self._wrap_by_character(text, metrics, max_width)
        else:
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
        """清理文本"""
        if not text:
            return text
        
        text = re.sub(r'[^\x00-\x7F\u4e00-\u9fff]+', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _wrap_by_character(self, text, metrics, max_width):
        """按字符換行"""
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