# Location: project_v2/core/camera_manager.py
# Usage: 相機管理與畫面擷取

import cv2
import numpy as np
from PyQt6.QtCore import QObject, QThread, pyqtSignal
from PyQt6.QtGui import QImage
import os
from datetime import datetime


class CameraThread(QThread):
    """相機執行緒"""
    frame_ready = pyqtSignal(np.ndarray)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, camera_index=0):
        super().__init__()
        self.camera_index = camera_index
        self.is_running = False
        self.cap = None
        
    def run(self):
        """執行緒主迴圈"""
        try:
            # 使用 CAP_DSHOW 在 Windows 上可以加快相機開啟速度
            import platform
            if platform.system() == "Windows":
                self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
            else:
                self.cap = cv2.VideoCapture(self.camera_index)
            
            # 設定較小的緩衝區以減少延遲
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            # 設定相機參數
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
            self.cap.set(cv2.CAP_PROP_FPS, 60)
            
            if not self.cap.isOpened():
                self.error_occurred.emit("無法開啟相機")
                return
                
            self.is_running = True
            
            # 丟棄前幾個畫面，因為可能是舊的
            for _ in range(5):
                self.cap.read()
            
            while self.is_running:
                ret, frame = self.cap.read()
                if ret:
                    # 不做裁切，保持原始比例
                    # 在顯示時再進行適當的縮放
                    self.frame_ready.emit(frame)
                else:
                    self.error_occurred.emit("讀取畫面失敗")
                    break
                    
                # 減少延遲，提高 FPS
                self.msleep(16)  # ~60 FPS
                
        except Exception as e:
            self.error_occurred.emit(f"相機錯誤: {str(e)}")
        finally:
            if self.cap:
                self.cap.release()
                
    def stop(self):
        """停止執行緒"""
        self.is_running = False
        self.wait()


class CameraManager(QObject):
    """相機管理器"""
    frame_ready = pyqtSignal(np.ndarray)
    screenshot_saved = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.camera_thread = None
        self.current_frame = None
        self.camera_index = 0
        
        # 確保截圖目錄存在
        self.screenshot_dir = "webcam-shots"
        os.makedirs(self.screenshot_dir, exist_ok=True)
        
    def start(self, camera_index=0):
        """啟動相機"""
        self.camera_index = camera_index
        
        if self.camera_thread and self.camera_thread.isRunning():
            self.stop()
            
        self.camera_thread = CameraThread(camera_index)
        self.camera_thread.frame_ready.connect(self._on_frame_ready)
        self.camera_thread.error_occurred.connect(self.error_occurred.emit)
        self.camera_thread.start()
        
    def stop(self):
        """停止相機"""
        if self.camera_thread:
            self.camera_thread.stop()
            self.camera_thread = None
            
    def _on_frame_ready(self, frame):
        """處理新畫面"""
        self.current_frame = frame.copy()
        self.frame_ready.emit(frame)
        
    def take_screenshot(self):
        """擷取當前畫面"""
        if self.current_frame is None:
            self.error_occurred.emit("無可用畫面")
            return None
            
        # 生成檔名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.jpg"
        filepath = os.path.join(self.screenshot_dir, filename)
        
        # 儲存圖片
        cv2.imwrite(filepath, self.current_frame)
        self.screenshot_saved.emit(filepath)
        
        return filepath
        
    @staticmethod
    def get_available_cameras():
        """取得可用相機列表"""
        cameras = []
        for i in range(10):  # 檢查前 10 個索引
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                cameras.append((i, f"Camera {i}"))
                cap.release()
        return cameras
        
    @staticmethod
    def frame_to_qimage(frame):
        """將 OpenCV frame 轉換為 QImage"""
        height, width, channel = frame.shape
        bytes_per_line = 3 * width
        
        # BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        return QImage(rgb_frame.data, width, height, 
                     bytes_per_line, QImage.Format.Format_RGB888)