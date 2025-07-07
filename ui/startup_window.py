# Location: project_v2/ui/startup_window.py
# Usage: 啟動視窗，提供相機預覽、串口選擇等設定

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                           QLabel, QComboBox, QPushButton, QCheckBox, 
                           QGroupBox, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap, QFont
import cv2
import numpy as np

from core.camera_manager import CameraManager
from core.arduino_controller import ArduinoController


class StartupWindow(QMainWindow):
    """啟動設定視窗"""
    
    start_requested = pyqtSignal(dict)  # 發送啟動參數
    
    def __init__(self):
        super().__init__()
        self.camera_manager = CameraManager()
        
        # 預覽更新計時器 - 必須在 setup_ui 之前初始化
        self.preview_timer = QTimer()
        self.preview_timer.timeout.connect(self.update_preview)
        
        # 初始化屬性
        self.is_loading = True
        self.current_frame = None
        self.camera_started = False
        
        self.setup_ui()
        self.load_devices()
        
        # 載入完成
        self.is_loading = False
        
        # 延遲啟動相機，讓視窗先顯示
        QTimer.singleShot(100, self.start_default_camera)
        
    def setup_ui(self):
        """設定 UI"""
        self.setWindowTitle("DefenseSystem - 啟動設定")
        self.setFixedSize(1200, 800)  # 增加寬度，減少高度
        
        # 主容器
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)  # 改為水平佈局
        main_layout.setSpacing(20)
        
        # 左側：相機預覽區
        preview_group = QGroupBox("相機預覽")
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_label = QLabel()
        self.preview_label.setFixedSize(400, 640)  # 5:8 豎屏比例預覽 (1200x1920的縮小版)
        self.preview_label.setStyleSheet("border: 1px solid #ccc;")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setText("載入相機中...")
        preview_layout.addWidget(self.preview_label)
        
        main_layout.addWidget(preview_group)
        
        # 右側：設定區
        settings_container = QWidget()
        settings_layout = QVBoxLayout(settings_container)
        settings_layout.setSpacing(15)
        
        # 標題
        title_label = QLabel("DefenseSystem")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        settings_layout.addWidget(title_label)
        
        # 設定區
        settings_group = QGroupBox("系統設定")
        settings_layout_inner = QVBoxLayout(settings_group)
        
        # 相機選擇
        camera_layout = QHBoxLayout()
        camera_layout.addWidget(QLabel("選擇相機："))
        self.camera_combo = QComboBox()
        self.camera_combo.currentIndexChanged.connect(self.on_camera_changed)
        camera_layout.addWidget(self.camera_combo, 1)
        settings_layout_inner.addLayout(camera_layout)
        
        # Arduino 串口選擇
        arduino_layout = QHBoxLayout()
        arduino_layout.addWidget(QLabel("Arduino 串口："))
        self.arduino_combo = QComboBox()
        arduino_layout.addWidget(self.arduino_combo, 1)
        settings_layout_inner.addLayout(arduino_layout)
        
        # 重新整理按鈕
        refresh_layout = QHBoxLayout()
        refresh_btn = QPushButton("重新整理串口")
        refresh_btn.clicked.connect(self.refresh_arduino_ports)
        refresh_layout.addWidget(refresh_btn)
        settings_layout_inner.addLayout(refresh_layout)
        
        settings_layout.addWidget(settings_group)
        
        # 選項區
        options_group = QGroupBox("顯示選項")
        options_layout = QVBoxLayout(options_group)
        
        # 全螢幕選項
        self.fullscreen_check = QCheckBox("全螢幕模式")
        self.fullscreen_check.toggled.connect(self.on_fullscreen_toggled)
        options_layout.addWidget(self.fullscreen_check)
        
        # Mini 模式選項
        self.mini_mode_check = QCheckBox("Mini 模式 (縮小一半)")
        options_layout.addWidget(self.mini_mode_check)
        
        # Debug 模式選項
        self.debug_check = QCheckBox("Debug 模式")
        options_layout.addWidget(self.debug_check)
        
        # No LLM 模式選項
        self.no_llm_check = QCheckBox("No LLM 模式 (跳過 AI 分析)")
        options_layout.addWidget(self.no_llm_check)
        
        settings_layout.addWidget(options_group)
        
        # 狀態顯示
        self.status_label = QLabel("準備就緒")
        self.status_label.setStyleSheet("color: green; font-weight: bold;")
        settings_layout.addWidget(self.status_label)
        
        # 啟動按鈕
        start_btn = QPushButton("啟動防禦系統")
        start_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        start_btn.clicked.connect(self.on_start_clicked)
        settings_layout.addWidget(start_btn)
        
        # 添加彈性空間
        settings_layout.addStretch()
        
        main_layout.addWidget(settings_container)
        
    def on_fullscreen_toggled(self, checked):
        """全螢幕選項切換時"""
        if checked:
            # 全螢幕模式時停用 mini mode
            self.mini_mode_check.setChecked(False)
            self.mini_mode_check.setEnabled(False)
        else:
            self.mini_mode_check.setEnabled(True)
            
    def start_default_camera(self):
        """啟動預設相機"""
        if self.camera_combo.count() > 0:
            camera_data = self.camera_combo.itemData(0)
            if camera_data is not None and camera_data >= 0:
                self.on_camera_changed(0)
                
    def load_devices(self):
        """載入可用裝置"""
        # 載入相機
        cameras = CameraManager.get_available_cameras()
        self.camera_combo.clear()
        if cameras:
            for idx, name in cameras:
                self.camera_combo.addItem(name, idx)
        else:
            self.camera_combo.addItem("未偵測到相機", -1)
            
        # 載入 Arduino 串口
        self.refresh_arduino_ports()
        
    def refresh_arduino_ports(self):
        """重新整理 Arduino 串口"""
        ports = ArduinoController.get_available_ports()
        self.arduino_combo.clear()
        self.arduino_combo.addItem("無 (選配)", None)
        
        for port, desc in ports:
            self.arduino_combo.addItem(f"{port} - {desc}", port)
            
    def on_camera_changed(self, index):
        """相機選擇變更"""
        if self.is_loading:
            return
            
        if index >= 0:
            camera_index = self.camera_combo.currentData()
            if camera_index is not None and camera_index >= 0:
                self.start_camera_preview(camera_index)
                
    def start_camera_preview(self, camera_index):
        """開始相機預覽"""
        # 停止現有相機
        if self.camera_started:
            self.camera_manager.stop()
            self.preview_timer.stop()
            
        self.camera_manager.frame_ready.connect(self.on_frame_ready)
        self.camera_manager.error_occurred.connect(self.on_camera_error)
        self.camera_manager.start(camera_index)
        self.preview_timer.start(33)  # ~30 FPS
        self.camera_started = True
        self.status_label.setText("相機預覽中")
        
    def on_frame_ready(self, frame):
        """更新預覽畫面"""
        self.current_frame = frame
        
    def update_preview(self):
        """更新預覽顯示"""
        if self.current_frame is not None:
            # 💪 恢復豎屏預覽，匹配主視窗的實際裁切格式
            # 使用與主視窗相同的裁切邏輯
            cropped_frame = self.crop_frame_to_portrait(self.current_frame)
            
            # 縮放到預覽尺寸（5:8豎屏，適配1200x1920）
            preview_width = 400
            preview_height = 640
            
            resized = cv2.resize(cropped_frame, (preview_width, preview_height), 
                               interpolation=cv2.INTER_LINEAR)
            
            # 轉換為 QPixmap
            qimage = CameraManager.frame_to_qimage(resized)
            pixmap = QPixmap.fromImage(qimage)
            self.preview_label.setPixmap(pixmap)
            
    def crop_frame_to_portrait(self, frame):
        """從1920x1080相機畫面裁切出中間的1200x1920豎屏區域（與main_window相同邏輯）"""
        height, width = frame.shape[:2]
        
        # 確保輸入是標準相機格式
        if width != 1920 or height != 1080:
            frame = cv2.resize(frame, (1920, 1080), interpolation=cv2.INTER_LINEAR)
            height, width = 1080, 1920
        
        # 💪 適應1200x1920螢幕比例
        # 目標比例 1200:1920 = 5:8
        # 從1080高度計算對應的5:8寬度：1080 * 5/8 = 675像素
        target_crop_width = int(1080 * 5 / 8)  # 675像素
        
        # 從1920x1080裁切出中間的675x1080區域
        crop_x = (1920 - target_crop_width) // 2  # 居中裁切
        crop_y = 0
        
        # 裁切出正確比例的區域
        cropped_frame = frame[crop_y:crop_y + 1080, crop_x:crop_x + target_crop_width]
        
        # 縮放到目標尺寸1200x1920（保持正確比例，不會拉伸變形）
        portrait_frame = cv2.resize(cropped_frame, (1200, 1920), interpolation=cv2.INTER_LINEAR)
        
        return portrait_frame
        
    def on_camera_error(self, error):
        """處理相機錯誤"""
        self.status_label.setText(f"相機錯誤: {error}")
        self.preview_label.setText("相機錯誤")
        
    def on_start_clicked(self):
        """啟動按鈕點擊"""
        # 檢查相機
        camera_index = self.camera_combo.currentData()
        if camera_index is None or camera_index < 0:
            QMessageBox.warning(self, "警告", "請選擇有效的相機")
            return
            
        # 收集啟動參數
        params = {
            'camera_index': camera_index,
            'arduino_port': self.arduino_combo.currentData(),
            'fullscreen': self.fullscreen_check.isChecked(),
            'debug_mode': self.debug_check.isChecked(),
            'no_llm_mode': self.no_llm_check.isChecked(),
            'mini_mode': self.mini_mode_check.isChecked()  # 新增參數
        }
        
        # 停止預覽
        self.preview_timer.stop()
        self.camera_manager.stop()
        
        # 發送啟動信號
        self.start_requested.emit(params)
        self.close()
        
    def closeEvent(self, event):
        """關閉事件"""
        # 停止計時器
        if hasattr(self, 'preview_timer'):
            self.preview_timer.stop()
            
        # 停止相機
        if hasattr(self, 'camera_manager'):
            self.camera_manager.stop()
            
        event.accept()