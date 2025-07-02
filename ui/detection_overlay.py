# Location: project_v2/ui/detection_overlay.py
# Usage: 人臉檢測框動畫覆蓋層 - 基於 test_frame_effect 的動畫系統

import cv2
import random
import numpy as np
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QImage, QPixmap
from PyQt6.QtCore import QTimer, pyqtSignal
from utils import AnimConfigLoader


class VisualRect:
    """視覺矩形動畫類 - 完全基於 test_frame_effect/text_camera3.py 實現"""
    
    def __init__(self, x, y, w, h, config):
        self.config = config
        self.target_x = x
        self.target_y = y
        
        # 從配置獲取框放大倍數 (默認1.5倍)
        size_multiplier = self.config.get_float('BASIC', 'frame_size_multiplier', 1.5)
        self.target_w = w * size_multiplier
        self.target_h = h * size_multiplier
        
        self.x = x
        self.y = y
        self.w = 0
        self.h = 0
        self.outside_w = 0
        self.outside_h = 0
        
        self.time_count = 0
        self.state = 0
        self.start_line = 0
        self.end_line = 0
        self.max_time = 0  # 記錄最大時間，避免重置
        
        # 從設定檔載入動畫參數
        self.position_smooth = self.config.get_float('BASIC', 'position_smooth', 0.08)
        self.state1_duration = self.config.get_int('BASIC', 'state1_duration', 60)
        self.state2_duration = self.config.get_int('BASIC', 'state2_duration', 60)
        self.state3_duration = self.config.get_int('BASIC', 'state3_duration', 60)
        self.state4_duration = self.config.get_int('BASIC', 'state4_duration', 60)
        
        # 計算總動畫時長
        self.total_duration = self.state1_duration + self.state2_duration + self.state3_duration + self.state4_duration
        
    def update(self, target_x, target_y, target_w, target_h):
        """更新目標位置和尺寸"""
        # 從配置獲取框放大倍數
        size_multiplier = self.config.get_float('BASIC', 'frame_size_multiplier', 1.5)
        
        # 更新目標位置和尺寸
        self.target_x = target_x
        self.target_y = target_y
        self.target_w = target_w * size_multiplier
        self.target_h = target_h * size_multiplier
       
        # 使用設定檔中的位置平滑參數 - 更穩定的平滑
        self.x += (self.target_x - self.x) * self.position_smooth
        self.y += (self.target_y - self.y) * self.position_smooth
       
        # 穩定的時間計數器 - 只增加，不重置
        self.time_count += 1
        self.max_time = max(self.max_time, self.time_count)
        
        # 動畫完成後保持在最終狀態，避免重置
        if self.time_count >= self.total_duration:
            self.state = 4  # 保持在最終狀態
        elif self.time_count < self.state1_duration:
            self.state = 1
        elif self.time_count < self.state1_duration + self.state2_duration:
            self.state = 2
        elif self.time_count < self.state1_duration + self.state2_duration + self.state3_duration:
            self.state = 3
        else:
            self.state = 4
            
        # 狀態1: 外框角落線條出現
        if self.state >= 1:
            outside_smooth = self.config.get_float('STATE1', 'outside_smooth', 0.12)
            self.outside_w += (self.target_w - self.outside_w) * outside_smooth
            self.outside_h += (self.target_h - self.outside_h) * outside_smooth
            
        # 狀態2: 內框出現 - 保持之前狀態的效果
        if self.state >= 2:
            inner_smooth = self.config.get_float('STATE2', 'inner_smooth', 0.1)
            self.w += (self.target_w - self.w) * inner_smooth
            self.h += (self.target_h - self.h) * inner_smooth
            
        # 狀態3: 十字線開始出現 - 保持之前狀態的效果
        if self.state >= 3:
            cross_start_smooth = self.config.get_float('STATE3', 'cross_start_smooth', 0.08)
            self.start_line += (1 - self.start_line) * cross_start_smooth
            
        # 狀態4: 十字線完全延伸 - 保持之前狀態的效果
        if self.state >= 4:
            cross_end_smooth = self.config.get_float('STATE4', 'cross_end_smooth', 0.12)
            self.end_line += (1 - self.end_line) * cross_end_smooth

    def draw(self, frame):
        """繪製動畫框 - 完全基於 test_frame_effect 實現"""
        # 使用設定檔中的閃爍機率
        flicker_prob = self.config.get_float('VISUAL', 'flicker_probability', 0.2)
        show = random.random() > flicker_prob
        
        if show and (self.state in [1, 2, 3, 4]):
            # 使用設定檔中的顏色 (BGR格式)
            color = self.config.get_color_bgr()
            
            # 狀態1和以後: 繪製角落線條
            self._draw_corner_lines(frame, color)
            
        # 狀態2和3: 繪製內框
        if show and (self.state in [2, 3]):
            self._draw_inner_rectangle(frame, color)
       
        # 狀態3和4: 繪製十字準星
        if show and (self.state in [3, 4]):
            self._draw_cross_lines(frame, color)

    def _draw_corner_lines(self, frame, color):
        """繪製角落線條"""
        # 使用設定參數的角落線條
        corner_length = self.config.get_float('STATE1', 'corner_length_ratio', 0.07)
        line_thickness = self.config.get_int('STATE1', 'line_thickness', 1)
        
        # 轉換為整數坐標
        center_x = int(self.x)
        center_y = int(self.y)
        half_w = int(self.outside_w * 0.5)
        half_h = int(self.outside_h * 0.5)
        corner_len_w = int(self.outside_w * corner_length)
        corner_len_h = int(self.outside_h * corner_length)
        
        # 左上角
        cv2.line(frame, 
                (center_x - half_w, center_y - half_h),
                (center_x - half_w + corner_len_w, center_y - half_h), 
                color, line_thickness)
        cv2.line(frame, 
                (center_x - half_w, center_y - half_h),
                (center_x - half_w, center_y - half_h + corner_len_h), 
                color, line_thickness)
        
        # 右上角
        cv2.line(frame, 
                (center_x + half_w, center_y - half_h),
                (center_x + half_w - corner_len_w, center_y - half_h), 
                color, line_thickness)
        cv2.line(frame, 
                (center_x + half_w, center_y - half_h),
                (center_x + half_w, center_y - half_h + corner_len_h), 
                color, line_thickness)
        
        # 右下角
        cv2.line(frame, 
                (center_x + half_w, center_y + half_h),
                (center_x + half_w - corner_len_w, center_y + half_h), 
                color, line_thickness)
        cv2.line(frame, 
                (center_x + half_w, center_y + half_h),
                (center_x + half_w, center_y + half_h - corner_len_h), 
                color, line_thickness)
        
        # 左下角
        cv2.line(frame, 
                (center_x - half_w, center_y + half_h),
                (center_x - half_w + corner_len_w, center_y + half_h), 
                color, line_thickness)
        cv2.line(frame, 
                (center_x - half_w, center_y + half_h),
                (center_x - half_w, center_y + half_h - corner_len_h), 
                color, line_thickness)

    def _draw_inner_rectangle(self, frame, color):
        """繪製內框半透明矩形"""
        # 使用配置參數
        inner_alpha = self.config.get_float('STATE2', 'inner_alpha', 50) / 255.0
        inner_size_ratio = self.config.get_float('STATE2', 'inner_size_ratio', 0.9)
        
        # 創建半透明覆蓋層
        overlay = frame.copy()
        inner_w = int(self.w * inner_size_ratio)
        inner_h = int(self.h * inner_size_ratio)
        
        cv2.rectangle(overlay,
                     (int(self.x - inner_w*0.5), int(self.y - inner_h*0.5)),
                     (int(self.x + inner_w*0.5), int(self.y + inner_h*0.5)),
                     color, -1)
        
        cv2.addWeighted(overlay, inner_alpha, frame, 1 - inner_alpha, 0, frame)

    def _draw_cross_lines(self, frame, color):
        """繪製十字準星線條"""
        # 使用配置參數
        cross_length_h = self.config.get_float('STATE3', 'cross_length_ratio_h', 0.59)
        cross_length_w = self.config.get_float('STATE3', 'cross_length_ratio_w', 0.55)
        line_thickness = self.config.get_int('STATE4', 'line_thickness', 2)
        
        # 計算十字線位置
        start_h = int(self.start_line * self.h * cross_length_h)
        end_h = int(self.end_line * self.h * cross_length_h)
        start_w = int(self.start_line * self.w * cross_length_w)
        end_w = int(self.end_line * self.w * cross_length_w)
        
        # 垂直線 - 上
        cv2.line(frame,
                (int(self.x), int(self.y - start_h)),
                (int(self.x), int(self.y - end_h)),
                color, line_thickness)
        # 垂直線 - 下
        cv2.line(frame,
                (int(self.x), int(self.y + start_h)),
                (int(self.x), int(self.y + end_h)),
                color, line_thickness)
        # 水平線 - 右
        cv2.line(frame,
                (int(self.x + start_w), int(self.y)),
                (int(self.x + end_w), int(self.y)),
                color, line_thickness)
        # 水平線 - 左
        cv2.line(frame,
                (int(self.x - start_w), int(self.y)),
                (int(self.x - end_w), int(self.y)),
                color, line_thickness)


class DetectionOverlay(QWidget):
    """檢測框覆蓋層 - 使用新動畫系統"""
    
    # 信號定義
    detection_updated = pyqtSignal(bool)  # 檢測狀態更新信號
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 載入動畫配置
        self.anim_config = AnimConfigLoader()
        
        # 驗證配置
        config_errors = self.anim_config.validate_config()
        if config_errors:
            print("動畫配置警告:")
            for key, error in config_errors.items():
                print(f"  {error}")
        
        # 檢測框列表
        self.visual_rects = []
        
        # 動畫定時器 - 60 FPS
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_animation)
        self.animation_timer.start(16)  # ~60 FPS (1000ms / 60fps = 16.67ms)
        
        # 當前檢測到的人臉
        self.current_faces = []
        self.has_faces = False
        
        # 性能統計
        self.frame_count = 0
        self.last_fps_update = 0
        self.fps = 0
        
        print(f"檢測框動畫初始化完成，總動畫時長: {self.anim_config.get_total_duration()} 幀")
    
    def update_faces(self, faces):
        """更新檢測到的人臉"""
        self.current_faces = faces
        new_has_faces = len(faces) > 0
        
        # 發送檢測狀態變化信號
        if new_has_faces != self.has_faces:
            self.has_faces = new_has_faces
            self.detection_updated.emit(self.has_faces)
        
        # 更新視覺矩形
        self._update_visual_rects()
    
    def _update_visual_rects(self):
        """更新視覺矩形列表"""
        current_count = len(self.visual_rects)
        needed_count = len(self.current_faces)
        
        # 添加新的矩形
        while len(self.visual_rects) < needed_count:
            face = self.current_faces[len(self.visual_rects)]
            x, y, w, h = face
            center_x = x + w // 2
            center_y = y + h // 2
            
            rect = VisualRect(center_x, center_y, w, h, self.anim_config)
            self.visual_rects.append(rect)
        
        # 移除多餘的矩形
        self.visual_rects = self.visual_rects[:needed_count]
        
        # 更新現有矩形的目標位置
        for i, rect in enumerate(self.visual_rects):
            if i < len(self.current_faces):
                x, y, w, h = self.current_faces[i]
                center_x = x + w // 2
                center_y = y + h // 2
                rect.update(center_x, center_y, w, h)
        
    def update_animation(self):
        """更新動畫幀"""
        # 只有在有檢測框時才進行動畫更新
        if self.visual_rects:
            # 更新每個視覺矩形的動畫狀態
            for rect in self.visual_rects:
                # 如果有當前人臉數據，繼續更新位置
                if self.current_faces:
                    for i, face in enumerate(self.current_faces):
                        if i < len(self.visual_rects):
                            x, y, w, h = face
                            center_x = x + w // 2
                            center_y = y + h // 2
                            self.visual_rects[i].update(center_x, center_y, w, h)
            
            # 觸發重繪
            self.update()
        
        # 更新FPS統計
        self.frame_count += 1
        import time
        current_time = time.time()
        if current_time - self.last_fps_update >= 1.0:
            self.fps = self.frame_count
            self.frame_count = 0
            self.last_fps_update = current_time
    
    def draw_on_frame(self, frame):
        """在OpenCV幀上繪製檢測框"""
        if not self.visual_rects:
            return frame
        
        # 為每個視覺矩形繪製動畫
        for rect in self.visual_rects:
            rect.draw(frame)
        
        return frame
    
    def clear_detections(self):
        """清除所有檢測框"""
        self.visual_rects.clear()
        self.current_faces.clear()
        if self.has_faces:
            self.has_faces = False
            self.detection_updated.emit(False)
        self.update()
    
    def reload_config(self):
        """重新載入動畫配置"""
        print("重新載入檢測框動畫配置...")
        self.anim_config.reload_config()
        
        # 驗證新配置
        config_errors = self.anim_config.validate_config()
        if config_errors:
            print("動畫配置警告:")
            for key, error in config_errors.items():
                print(f"  {error}")
        
        # 重置所有動畫狀態
        for rect in self.visual_rects:
            rect.config = self.anim_config
            rect.time_count = 0
            rect.max_time = 0
            rect.state = 0
        
        print(f"配置重載完成，新動畫時長: {self.anim_config.get_total_duration()} 幀")
    
    def get_animation_info(self):
        """獲取動畫信息"""
        info = {
            'total_rects': len(self.visual_rects),
            'animation_fps': self.fps,
            'total_duration': self.anim_config.get_total_duration(),
            'has_faces': self.has_faces
        }
        
        if self.visual_rects:
            rect = self.visual_rects[0]  # 取第一個矩形的狀態
            info.update({
                'current_state': rect.state,
                'time_count': rect.time_count,
                'animation_progress': min(100, (rect.time_count / rect.total_duration) * 100)
            })
        
        return info
        
    def paintEvent(self, event):
        """PyQt繪製事件 - 目前主要用於調試"""
        super().paintEvent(event)
        # 這裡可以添加額外的PyQt繪製邏輯，但主要繪製在OpenCV幀上進行