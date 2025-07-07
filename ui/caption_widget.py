# Location: project_v2/ui/caption_widget.py
# Usage: 字幕顯示元件，支援單語和雙語顯示，包含打字機效果和TTS即時同步

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QRect, QObject
from PyQt6.QtGui import QFont, QPalette, QColor, QPainter, QFontMetrics
from utils.font_manager import FontManager
import re
import time


class CaptionWidget(QWidget):
    """字幕顯示元件 - 優化的TTS同步版本"""
    
    typing_complete = pyqtSignal()
    tc_typing_complete = pyqtSignal()
    en_typing_complete = pyqtSignal()
    
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
        self.tc_current_text = ""
        self.en_current_text = ""
        self.tc_index = 0
        self.en_index = 0
        self._tc_completed = False
        self._en_completed = False
        
        # 統一的顯示計時器 - 簡化邏輯
        self.display_timer = QTimer()
        self.display_timer.timeout.connect(self._update_display)
        
        # TTS同步相關
        self.tts_sync_enabled = False
        self.tts_target_position = 0
        self.last_tts_update_time = 0
        
        # 設定透明背景
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAutoFillBackground(False)
        
        # 字型設定
        base_font_size = int(font_size * scale_factor)
        self.caption_font = QFont("Noto Sans CJK TC", base_font_size)
        
        # 文字邊距
        self.padding = 20
        self.line_spacing = 10
        
        # 字符數量限制（統一中英文）- 可從配置載入
        self.max_chars_per_line = 65  # 每行最大字符數
        self.chinese_char_weight = 1.8  # 中文字符權重（相對於英文）
        
        # 嘗試從配置文件載入設定
        self._load_wrapping_config()
        
        # 隱藏控制項
        self.hide()
        
    def _load_wrapping_config(self):
        """從配置文件載入換行設定"""
        try:
            from utils.config_loader import ConfigLoader
            config_loader = ConfigLoader()
            config = config_loader.load_period_config()
            
            # 載入字符限制設定
            self.max_chars_per_line = config.get('caption_max_chars_per_line', 40)
            self.chinese_char_weight = config.get('caption_chinese_char_weight', 1.8)
            
            print(f"載入字幕換行設定: 每行{self.max_chars_per_line}字符, 中文權重{self.chinese_char_weight}")
        except Exception as e:
            print(f"載入換行配置失敗: {e}, 使用預設值")
        
    def show_caption(self, text, typing_speed=80):
        """顯示單語字幕 - 優化版本"""
        self.full_text = text
        self.current_text = ""
        self.current_index = 0
        self.is_showing = True
        self.is_bilingual_mode = False
        self._typing_completed = False  # 重置完成標誌
        
        self.show()
        
        # 使用統一的顯示機制
        if not self.tts_sync_enabled:
            # 調整打字速度，更平滑
            interval = max(int(typing_speed), 30)  # 最少30ms間隔
            self.display_timer.start(interval)
            print(f"啟動字幕顯示計時器，間隔: {interval}ms")
        else:
            # TTS同步模式使用固定的快速更新頻率
            self.display_timer.start(16)  # 60fps 更新頻率
            print(f"TTS同步模式：使用60fps更新頻率")
        
        self.update()
        
    def show_bilingual_caption(self, tc_text, en_text, typing_speed=80):
        """顯示雙語字幕 - 優化版本"""
        self.is_bilingual_mode = True
        self.tc_text = tc_text
        self.en_text = en_text
        
        # 重置狀態
        self.tc_current_text = ""
        self.en_current_text = ""
        self.tc_index = 0
        self.en_index = 0
        self._tc_completed = False
        self._en_completed = False
        self._typing_completed = False  # 重置完成標誌
        self.is_showing = True
        
        self.show()
        
        # 使用統一的顯示機制
        if not self.tts_sync_enabled:
            interval = max(int(typing_speed), 30)  # 最少30ms間隔
            self.display_timer.start(interval)
            print(f"雙語字幕顯示計時器，間隔: {interval}ms")
        else:
            self.display_timer.start(16)  # 60fps 更新頻率
            print(f"雙語TTS同步模式：使用60fps更新頻率")
        
        self.update()
        
    def enable_tts_sync(self, tts_text, tts_rate_wpm=140):
        """啟用TTS同步模式 - 簡化版本"""
        self.tts_sync_enabled = True
        self.tts_text = tts_text
        self.tts_target_position = 0
        self.last_tts_update_time = time.time()
        
        print(f"TTS同步啟用: 文字長度={len(tts_text)}")
        
    def update_tts_progress(self, current_pos, total_len):
        """更新TTS進度 - 修復句子間隔字符延遲"""
        if not self.tts_sync_enabled:
            return
            
        # 過濾異常進度值
        if current_pos < 0 or current_pos > total_len * 1.5:
            return
            
        # 立即更新進度，不做延遲
        if current_pos >= self.tts_target_position:
            old_position = self.tts_target_position
            self.tts_target_position = current_pos
            self.last_tts_update_time = time.time()
            
            # 💪 強化片段完成檢測
            progress_jump = current_pos - old_position
            
            # 條件1: 大跳躍（明顯的片段結束）
            if progress_jump > 5:
                print(f"🔄 檢測到進度跳躍: {old_position}→{current_pos} (+{progress_jump})")
                self._force_complete_to_position(current_pos)
                
            # 條件2: 重複的相同進度值（TTS發送多次確保字幕收到）
            elif current_pos == old_position and current_pos > 0:
                print(f"🔄 收到重複進度確認: {current_pos}")
                self._force_complete_to_position(current_pos)
                
            # 條件3: 正常進度更新也立即處理
            else:
                self._update_tts_sync_display()
            
        # 調試信息 - 更頻繁顯示，便於調試
        if current_pos % 3 == 0 or current_pos == total_len:
            progress = (current_pos / total_len * 100) if total_len > 0 else 0
            print(f"📊 TTS進度: {current_pos}/{total_len} ({progress:.1f}%)")
            
    def _force_complete_to_position(self, target_pos):
        """強制完成字幕顯示到指定位置 - 解決句子間隔延遲"""
        if not self.is_showing:
            return
            
        print(f"💪 強制完成字幕到位置: {target_pos}")
        
        if self.is_bilingual_mode:
            # 雙語模式強制完成
            if hasattr(self, 'en_text') and self.en_text:
                en_target = min(target_pos, len(self.en_text))
                if en_target > self.en_index:
                    self.en_index = en_target
                    self.en_current_text = self.en_text[:self.en_index]
                    print(f"  英文強制到: {self.en_index}/{len(self.en_text)}")
                    
                    if self.en_index >= len(self.en_text) and not self._en_completed:
                        self._en_completed = True
                        self.en_typing_complete.emit()
            
            if hasattr(self, 'tc_text') and self.tc_text:
                # 中文按比例強制完成
                en_progress = self.en_index / len(self.en_text) if len(self.en_text) > 0 else 0
                tc_target = int(en_progress * len(self.tc_text))
                
                if tc_target > self.tc_index:
                    self.tc_index = tc_target
                    self.tc_current_text = self.tc_text[:self.tc_index]
                    print(f"  中文強制到: {self.tc_index}/{len(self.tc_text)}")
                    
                    if self.tc_index >= len(self.tc_text) and not self._tc_completed:
                        self._tc_completed = True
                        self.tc_typing_complete.emit()
        else:
            # 單語模式強制完成
            if hasattr(self, 'full_text') and self.full_text:
                target_index = min(target_pos, len(self.full_text))
                if target_index > self.current_index:
                    self.current_index = target_index
                    self.current_text = self.full_text[:self.current_index]
                    print(f"  單語強制到: {self.current_index}/{len(self.full_text)}")
                    
                    if self.current_index >= len(self.full_text):
                        if not hasattr(self, '_typing_completed') or not self._typing_completed:
                            self._typing_completed = True
                            self.typing_complete.emit()
        
        # 立即更新顯示
        self.update()
        
    def _update_display(self):
        """統一的顯示更新機制"""
        if not self.is_showing:
            return
            
        if self.tts_sync_enabled:
            self._update_tts_sync_display()
        else:
            self._update_normal_display()
            
    def _update_tts_sync_display(self):
        """TTS同步顯示更新 - 修復結尾卡頓問題"""
        # 計算目標顯示位置
        target_pos = self.tts_target_position
        
        # 檢查是否接近結尾 - 如果TTS進度超過90%，更主動地完成顯示
        current_time = time.time()
        time_since_last_update = current_time - self.last_tts_update_time
        
        if self.is_bilingual_mode:
            # 雙語模式
            if hasattr(self, 'en_text') and self.en_text:
                # 英文直接同步到TTS位置
                en_target = min(target_pos, len(self.en_text))
                
                # 英文積極完成邏輯 - 修復每句延遲
                if (en_target >= len(self.en_text) * 0.9 and 
                    time_since_last_update > 0.3 and 
                    self.en_index < len(self.en_text)):
                    en_target = len(self.en_text)
                    print(f"🔧 強制完成英文顯示: {en_target}/{len(self.en_text)}")
                # 英文進度停滯檢測
                elif (en_target > len(self.en_text) * 0.7 and 
                      time_since_last_update > 0.2 and 
                      en_target == self.en_index and 
                      self.en_index < len(self.en_text)):
                    en_target = min(self.en_index + 3, len(self.en_text))
                    print(f"🔧 英文句子推進: {self.en_index}→{en_target}")
                
                if en_target > self.en_index:
                    self.en_index = en_target
                    self.en_current_text = self.en_text[:self.en_index]
                    
                    # 檢查英文完成
                    if self.en_index >= len(self.en_text) and not self._en_completed:
                        self._en_completed = True
                        self.en_typing_complete.emit()
                
                # 中文按比例同步
                if hasattr(self, 'tc_text') and self.tc_text:
                    en_progress = self.en_index / len(self.en_text) if len(self.en_text) > 0 else 0
                    tc_target = int(en_progress * len(self.tc_text))
                    
                    # 中文積極完成邏輯 - 修復每句延遲
                    if (tc_target >= len(self.tc_text) * 0.9 and 
                        time_since_last_update > 0.3 and 
                        self.tc_index < len(self.tc_text)):
                        tc_target = len(self.tc_text)
                        print(f"🔧 強制完成中文顯示: {tc_target}/{len(self.tc_text)}")
                    # 中文進度停滯檢測
                    elif (tc_target > len(self.tc_text) * 0.7 and 
                          time_since_last_update > 0.2 and 
                          tc_target == self.tc_index and 
                          self.tc_index < len(self.tc_text)):
                        tc_target = min(self.tc_index + 2, len(self.tc_text))  # 中文字符較少推進
                        print(f"🔧 中文句子推進: {self.tc_index}→{tc_target}")
                    
                    if tc_target > self.tc_index:
                        self.tc_index = tc_target
                        self.tc_current_text = self.tc_text[:self.tc_index]
                        
                        # 檢查中文完成
                        if self.tc_index >= len(self.tc_text) and not self._tc_completed:
                            self._tc_completed = True
                            self.tc_typing_complete.emit()
        else:
            # 單語模式
            if hasattr(self, 'full_text') and self.full_text:
                target_index = min(target_pos, len(self.full_text))
                
                # 更積極的結尾完成邏輯 - 修復每句延遲
                force_complete = False
                
                # 條件1: 接近結尾且沒更新 (針對整體結尾)
                if (target_index >= len(self.full_text) * 0.9 and 
                    time_since_last_update > 0.3 and  # 縮短到300ms
                    self.current_index < len(self.full_text)):
                    force_complete = True
                    print(f"🔧 整體結尾強制完成: {target_index}/{len(self.full_text)}")
                
                # 條件2: 進度停滯檢測 (針對每句結尾延遲)
                elif (target_index > len(self.full_text) * 0.7 and  # 70%以後就開始檢測
                      time_since_last_update > 0.2 and  # 200ms沒更新
                      target_index == self.current_index and  # 進度停滯
                      self.current_index < len(self.full_text)):
                    force_complete = True
                    target_index = min(self.current_index + 5, len(self.full_text))  # 推進5個字符
                    print(f"🔧 句子結尾推進: {self.current_index}→{target_index}")
                
                if force_complete:
                    pass  # 使用上面設定的target_index
                
                if target_index > self.current_index:
                    self.current_index = target_index
                    self.current_text = self.full_text[:self.current_index]
                    
                    # 檢查完成 - 現在主動觸發完成
                    if self.current_index >= len(self.full_text):
                        print("📝 字幕顯示完成")
                        # 觸發完成信號，但不停止計時器（等TTS完成）
                        if not hasattr(self, '_typing_completed') or not self._typing_completed:
                            self._typing_completed = True
                            self.typing_complete.emit()
        
        self.update()
        
    def _update_normal_display(self):
        """常規顯示更新（非TTS同步）"""
        if self.is_bilingual_mode:
            self._update_bilingual_normal()
        else:
            self._update_single_normal()
            
    def _update_single_normal(self):
        """單語常規更新"""
        if self.current_index < len(self.full_text):
            self.current_index += 1
            self.current_text = self.full_text[:self.current_index]
            self.update()
        else:
            self.display_timer.stop()
            self.typing_complete.emit()
            
    def _update_bilingual_normal(self):
        """雙語常規更新 - 平衡推進"""
        tc_total = len(self.tc_text) if hasattr(self, 'tc_text') else 0
        en_total = len(self.en_text) if hasattr(self, 'en_text') else 0
        
        # 計算當前進度
        tc_progress = self.tc_index / tc_total if tc_total > 0 else 1.0
        en_progress = self.en_index / en_total if en_total > 0 else 1.0
        
        # 推進落後的語言
        advanced = False
        
        if not self._tc_completed and tc_progress <= en_progress and self.tc_index < tc_total:
            self.tc_index += 1
            self.tc_current_text = self.tc_text[:self.tc_index]
            advanced = True
            
            if self.tc_index >= tc_total:
                self._tc_completed = True
                self.tc_typing_complete.emit()
                
        if not self._en_completed and en_progress <= tc_progress and self.en_index < en_total:
            self.en_index += 1
            self.en_current_text = self.en_text[:self.en_index]
            advanced = True
            
            if self.en_index >= en_total:
                self._en_completed = True
                self.en_typing_complete.emit()
        
        if advanced:
            self.update()
            
        # 檢查是否都完成
        if self._tc_completed and self._en_completed:
            self.display_timer.stop()
            self.typing_complete.emit()
            
    def disable_tts_sync(self):
        """禁用TTS同步並完成顯示"""
        if not self.tts_sync_enabled:
            return
            
        print("TTS完成，完成字幕顯示")
        self.tts_sync_enabled = False
        self._typing_completed = False  # 重置標誌供下次使用
        
        # 停止計時器
        if self.display_timer.isActive():
            self.display_timer.stop()
        
        # 完成所有字幕顯示
        if self.is_bilingual_mode:
            if hasattr(self, 'tc_text') and hasattr(self, 'en_text'):
                self.tc_current_text = self.tc_text
                self.en_current_text = self.en_text
                self.tc_index = len(self.tc_text)
                self.en_index = len(self.en_text)
                
                if not self._tc_completed:
                    self._tc_completed = True
                    self.tc_typing_complete.emit()
                    
                if not self._en_completed:
                    self._en_completed = True
                    self.en_typing_complete.emit()
                    
                self.typing_complete.emit()
        else:
            if hasattr(self, 'full_text'):
                self.current_text = self.full_text
                self.current_index = len(self.full_text)
                self.typing_complete.emit()
        
        self.update()
            
    def hide(self):
        """隱藏字幕"""
        if self.display_timer.isActive():
            self.display_timer.stop()
        
        self.current_text = ""
        self.is_showing = False
        self.is_bilingual_mode = False
        
        # 重置狀態
        self.tc_current_text = ""
        self.en_current_text = ""
        self._tc_completed = False
        self._en_completed = False
        
        # 重置TTS同步
        self.tts_sync_enabled = False
        
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
        """繪製單語字幕 - 帶逐行背景"""
        if not self.current_text:
            return
            
        # 獲取完整文字的所有行
        full_lines = self._wrap_text(self.full_text, metrics) if self.full_text else []
        if not full_lines:
            return
            
        # 根據當前顯示的字符數量，計算應該顯示到第幾行
        current_lines, current_line_partial = self._get_current_display_lines(self.current_text, full_lines)
        
        line_height = metrics.height()
        total_height = len(full_lines) * (line_height + self.line_spacing) - self.line_spacing + 2 * self.padding
        
        # 確保文字在可見區域內
        available_height = self.height()
        if total_height > available_height:
            y_offset = 0
        else:
            y_offset = available_height - total_height
        
        y_offset = max(0, y_offset)
        
        # 繪製背景和文字 - 只繪製已顯示的行
        for i in range(len(current_lines)):
            line_text = current_lines[i]
            if i == len(current_lines) - 1 and current_line_partial:
                # 最後一行可能只顯示部分文字
                line_text = current_line_partial
            
            if line_text.strip():
                self._draw_text_line_with_background(painter, line_text, i, y_offset, line_height, metrics)
                
    def _paint_bilingual(self, painter, metrics):
        """繪製雙語字幕 - 帶逐行背景"""
        line_height = metrics.height()
        
        # 獲取完整文字的所有行
        tc_full_lines = self._wrap_text(self.tc_text, metrics) if hasattr(self, 'tc_text') and self.tc_text else []
        en_full_lines = self._wrap_text(self.en_text, metrics) if hasattr(self, 'en_text') and self.en_text else []
        
        # 計算當前顯示的行
        tc_current_lines, tc_partial = [], ""
        en_current_lines, en_partial = [], ""
        
        if hasattr(self, 'tc_current_text') and self.tc_current_text:
            tc_current_lines, tc_partial = self._get_current_display_lines(self.tc_current_text, tc_full_lines)
        
        if hasattr(self, 'en_current_text') and self.en_current_text:
            en_current_lines, en_partial = self._get_current_display_lines(self.en_current_text, en_full_lines)
        
        # 計算總行數（包括已顯示的）
        total_displayed_lines = len(tc_current_lines) + len(en_current_lines)
        if tc_partial:
            total_displayed_lines += 1
        if en_partial:
            total_displayed_lines += 1
        if len(tc_current_lines) > 0 and len(en_current_lines) > 0:
            total_displayed_lines += 1  # 語言間隔
            
        if total_displayed_lines == 0:
            return  # 沒有文字要顯示
            
        # 計算完整佈局（基於所有文字）
        total_full_lines = len(tc_full_lines) + len(en_full_lines)
        if total_full_lines > 0 and len(tc_full_lines) > 0 and len(en_full_lines) > 0:
            total_full_lines += 1  # 語言間隔
            
        total_height = total_full_lines * (line_height + self.line_spacing) - self.line_spacing + 2 * self.padding
        
        # 確保文字在可見區域內
        available_height = self.height()
        if total_height > available_height:
            y_offset = 0
        else:
            y_offset = available_height - total_height
        
        y_offset = max(0, y_offset)
        
        current_line = 0
        
        # 繪製中文（已顯示的行）
        for i, line in enumerate(tc_current_lines):
            if line.strip():
                self._draw_text_line_with_background(painter, line, current_line, y_offset, line_height, metrics)
            current_line += 1
            
        # 繪製中文部分行
        if tc_partial and tc_partial.strip():
            self._draw_text_line_with_background(painter, tc_partial, current_line, y_offset, line_height, metrics)
            current_line += 1
            
        # 語言之間的間隔
        if len(tc_current_lines) > 0 and len(en_current_lines) > 0:
            current_line += 1
            
        # 繪製英文（已顯示的行）
        for i, line in enumerate(en_current_lines):
            if line.strip():
                self._draw_text_line_with_background(painter, line, current_line, y_offset, line_height, metrics)
            current_line += 1
            
        # 繪製英文部分行
        if en_partial and en_partial.strip():
            self._draw_text_line_with_background(painter, en_partial, current_line, y_offset, line_height, metrics)
            current_line += 1
                
    def _wrap_text(self, text, metrics):
        """基於字符數量的統一換行處理 - 中英文使用相同限制"""
        if not text:
            return []
            
        lines = []
        current_line = ""
        current_weight = 0.0
        
        # 處理每個字符
        i = 0
        while i < len(text):
            char = text[i]
            
            # 計算字符權重
            char_weight = self._get_char_weight(char)
            
            # 檢查是否超過限制
            if current_weight + char_weight <= self.max_chars_per_line:
                # 字符可以添加到當前行
                current_line += char
                current_weight += char_weight
                i += 1
            else:
                # 當前行已滿，需要換行
                if current_line:
                    # 嘗試在合適的地方斷行
                    wrapped_result = self._smart_break_line_by_chars(current_line, char, text, i)
                    lines.append(wrapped_result['line'])
                    current_line = wrapped_result['remaining']
                    current_weight = self._calculate_line_weight(current_line)
                    i = wrapped_result['next_index']
                else:
                    # 單個字符就超限了，強制添加
                    current_line = char
                    current_weight = char_weight
                    i += 1
        
        # 添加最後一行
        if current_line:
            lines.append(current_line)
            
        return lines if lines else [""]
        
    def _get_char_weight(self, char):
        """計算字符權重"""
        # 中文字符（包括中文標點）
        if '\u4e00' <= char <= '\u9fff' or char in '，。！？；：「」『』':
            return self.chinese_char_weight
        # 英文和其他字符
        else:
            return 1.0
            
    def _calculate_line_weight(self, line):
        """計算一行文字的總權重"""
        total_weight = 0.0
        for char in line:
            total_weight += self._get_char_weight(char)
        return total_weight
        
    def _smart_break_line_by_chars(self, current_line, next_char, full_text, current_index):
        """基於字符數量的智能斷行 - 優先在合適位置斷開"""
        # 在標點符號後斷行（中英文）
        punctuation = "，。！？；：,. !?;:"
        
        # 從行尾往前找合適的斷點（最多回溯10個字符）
        for i in range(len(current_line) - 1, max(0, len(current_line) - 10), -1):
            if current_line[i] in punctuation:
                # 在標點後斷行
                break_point = i + 1
                return {
                    'line': current_line[:break_point],
                    'remaining': current_line[break_point:] + next_char,
                    'next_index': current_index + 1
                }
        
        # 在空格處斷行（主要為英文）
        for i in range(len(current_line) - 1, max(0, len(current_line) - 8), -1):
            if current_line[i] == ' ':
                break_point = i + 1
                return {
                    'line': current_line[:break_point].rstrip(),
                    'remaining': current_line[break_point:].lstrip() + next_char,
                    'next_index': current_index + 1
                }
        
        # 如果找不到好的斷點，在3/4處強制斷行
        break_point = max(1, len(current_line) * 3 // 4)
        return {
            'line': current_line[:break_point],
            'remaining': current_line[break_point:] + next_char,
            'next_index': current_index + 1
        }
        
    def _smart_break_line(self, current_line, next_char, full_text, current_index):
        """智能斷行 - 優先在合適位置斷開（舊版本，保留兼容性）"""
        # 重定向到新的字符數量版本
        return self._smart_break_line_by_chars(current_line, next_char, full_text, current_index)
        
    def _get_current_display_lines(self, current_text, full_lines):
        """根據當前顯示的字符計算應該顯示到第幾行"""
        if not current_text or not full_lines:
            return [], ""
            
        char_count = 0
        current_lines = []
        current_line_partial = ""
        
        for line in full_lines:
            if char_count + len(line) <= len(current_text):
                # 這行完全顯示
                current_lines.append(line)
                char_count += len(line)
            else:
                # 這行部分顯示
                remaining_chars = len(current_text) - char_count
                if remaining_chars > 0:
                    current_line_partial = line[:remaining_chars]
                break
                
        return current_lines, current_line_partial
        
    def _draw_text_line_with_background(self, painter, text, line_index, y_offset, line_height, metrics):
        """繪製帶背景的單行文字"""
        # 計算位置
        y = y_offset + self.padding + line_index * (line_height + self.line_spacing)
        
        # 計算文字寬度並居中
        text_width = metrics.horizontalAdvance(text)
        x = (self.width() - text_width) // 2
        
        # 繪製半透明黑色背景
        background_padding = 8
        background_rect = QRect(
            x - background_padding, 
            y, 
            text_width + 2 * background_padding, 
            line_height
        )
        
        painter.fillRect(background_rect, QColor(0, 0, 0, 102))  # 40% 透明度 (255 * 0.4 = 102)
        
        # 繪製文字陰影
        painter.setPen(QColor(0, 0, 0, 180))
        painter.drawText(x + 2, y + line_height - 2, text)
        
        # 繪製主文字
        painter.setPen(QColor(255, 255, 255, 255))
        painter.drawText(x, y + line_height - 4, text)
        
    def _draw_text_line(self, painter, text, line_index, y_offset, line_height, metrics):
        """繪製單行文字（無背景版本）"""
        # 重定向到帶背景版本
        self._draw_text_line_with_background(painter, text, line_index, y_offset, line_height, metrics)