# Location: project_v2/core/state_machine.py
# Usage: 狀態機管理系統，控制整體流程

from enum import Enum
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
import time


class SystemState(Enum):
    """系統狀態定義"""
    DETECTING = "DETECTING"
    SCREENSHOT_TRIGGER = "SCREENSHOT_TRIGGER" 
    LLM_LOADING = "LLM_LOADING"
    CAPTION = "CAPTION"
    IMG_SHOW = "IMG_SHOW"
    RESET = "RESET"


class StateMachine(QObject):
    """狀態機控制器"""
    
    # 狀態變更信號
    state_changed = pyqtSignal(SystemState)
    
    # 各狀態事件信號
    screenshot_requested = pyqtSignal()
    llm_analysis_requested = pyqtSignal(str)  # 圖片路徑
    caption_display_requested = pyqtSignal(dict)  # AI 回應
    weapon_display_requested = pyqtSignal(list)  # 武器列表
    reset_requested = pyqtSignal()
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.current_state = SystemState.DETECTING
        self.detection_start_time = None
        self.face_detected = False
        self.no_llm_mode = False
        
        # 計時器
        self.state_timer = QTimer()
        self.state_timer.timeout.connect(self._handle_state_timeout)
        
    def set_no_llm_mode(self, enabled):
        """設定 No LLM 模式"""
        self.no_llm_mode = enabled
        
    def start(self):
        """啟動狀態機"""
        self.transition_to(SystemState.DETECTING)
        
    def stop(self):
        """停止狀態機"""
        self.state_timer.stop()
        
    def transition_to(self, new_state):
        """狀態轉換"""
        print(f"State transition: {self.current_state.value} -> {new_state.value}")
        self.current_state = new_state
        self.state_timer.stop()
        
        # 發送狀態變更信號
        self.state_changed.emit(new_state)
        
        # 處理新狀態
        self._enter_state(new_state)
        
    def _enter_state(self, state):
        """進入新狀態的處理"""
        if state == SystemState.DETECTING:
            # 重置偵測
            self.detection_start_time = None
            self.face_detected = False
            
        elif state == SystemState.SCREENSHOT_TRIGGER:
            # 觸發截圖
            self.screenshot_requested.emit()
            # 直接轉到下一狀態
            if self.no_llm_mode:
                # No LLM 模式：跳過 AI 分析
                default_response = {
                    'caption': 'Emergency defense protocol activated.',
                    'caption_tc': '緊急防禦協議啟動。',
                    'weapons': ['01', '02']
                }
                self.transition_to(SystemState.CAPTION)
                self.caption_display_requested.emit(default_response)
            else:
                self.transition_to(SystemState.LLM_LOADING)
                
        elif state == SystemState.LLM_LOADING:
            # 等待 AI 分析完成
            pass
            
        elif state == SystemState.CAPTION:
            # 字幕顯示不使用計時器，等待 typing_complete 信號
            pass
            
        elif state == SystemState.IMG_SHOW:
            # 武器展示會由 weapon display 控制時間
            pass
            
        elif state == SystemState.RESET:
            # 重置並等待冷卻
            self.reset_requested.emit()
            cooldown = self.config.get('cooldown_time', 3.0) * 1000
            self.state_timer.start(int(cooldown))
            
    def _handle_state_timeout(self):
        """處理狀態超時"""
        self.state_timer.stop()
        
        if self.current_state == SystemState.RESET:
            # 冷卻完成，返回偵測
            self.transition_to(SystemState.DETECTING)
            
    def update_face_detection(self, face_detected):
        """更新人臉偵測狀態"""
        if self.current_state != SystemState.DETECTING:
            return
            
        if face_detected and not self.face_detected:
            # 開始偵測
            self.face_detected = True
            self.detection_start_time = time.time()
            
        elif not face_detected and self.face_detected:
            # 偵測中斷
            self.face_detected = False
            self.detection_start_time = None
            
        elif face_detected and self.face_detected:
            # 檢查是否達到觸發閾值
            if self.detection_start_time:
                elapsed = time.time() - self.detection_start_time
                threshold = self.config.get('detect_duration', 3.0)
                if elapsed >= threshold:
                    self.transition_to(SystemState.SCREENSHOT_TRIGGER)
                    
    def on_llm_complete(self, response):
        """AI 分析完成"""
        if self.current_state == SystemState.LLM_LOADING:
            self.transition_to(SystemState.CAPTION)
            self.caption_display_requested.emit(response)
            
    def on_weapon_display_requested(self, weapon_ids):
        """武器展示請求"""
        if self.current_state == SystemState.CAPTION:
            self.transition_to(SystemState.IMG_SHOW)
            self.weapon_display_requested.emit(weapon_ids)
            
    def on_weapon_display_complete(self):
        """武器展示完成"""
        if self.current_state == SystemState.IMG_SHOW:
            self.transition_to(SystemState.RESET)
            
    def get_detection_time(self):
        """獲取當前偵測時間"""
        if self.face_detected and self.detection_start_time:
            return time.time() - self.detection_start_time
        return 0.0