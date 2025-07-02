# Location: project_v2/ui/main_window.py
# Usage: 主視窗，整合所有功能模組

from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QGraphicsOpacityEffect
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal, QRect
from PyQt6.QtGui import QPainter, QPixmap, QFont, QFontDatabase
import os
import cv2
import numpy as np

from core import StateMachine, SystemState, CameraManager, FaceDetector, ArduinoController
from ui.detection_overlay import DetectionOverlay
from ui.caption_widget import CaptionWidget
from services import OllamaService, ImageService, TTSService
from utils import ConfigLoader, FontManager


class MainWindow(QMainWindow):
    """主程式視窗"""
    
    def __init__(self, startup_params):
        super().__init__()
        self.startup_params = startup_params
        
        # 設定縮放因子
        self.scale_factor = 0.5 if startup_params.get('mini_mode', False) else 1.0
        self.window_width = int(1080 * self.scale_factor)
        self.window_height = int(1920 * self.scale_factor)
        
        # 載入設定
        self.config_loader = ConfigLoader()
        self.config = self.config_loader.load_period_config()
        self.weapon_config = self.config_loader.load_weapon_config()
        
        # 初始化元件
        self.init_components()
        self.setup_ui()
        self.connect_signals()
        
        # 啟動系統 - 延遲啟動相機以避免黑屏
        QTimer.singleShot(100, self.start_system)
        
    def init_components(self):
        """初始化系統元件"""
        # 核心元件
        self.state_machine = StateMachine(self.config)
        self.camera_manager = CameraManager()
        self.face_detector = FaceDetector(self.config)
        
        # Arduino (選配)
        self.arduino_controller = None
        if self.startup_params['arduino_port']:
            self.arduino_controller = ArduinoController()
            self.arduino_controller.connect(self.startup_params['arduino_port'])
            
        # 服務
        self.ollama_service = OllamaService()
        self.image_service = ImageService()
        
        # TTS 服務 - 根據配置啟用
        tts_enabled = self.startup_params.get('tts_enabled', True)
        self.tts_service = TTSService(enabled=tts_enabled)
        
        # 設定TTS參數
        if self.tts_service.is_available():
            # 注意：TTS參數會在worker線程中的init_engine中設定
            print(f"TTS 服務已啟用，速度: {self.startup_params.get('tts_rate', 160)}, 音量: {self.startup_params.get('tts_volume', 0.8)}")
        
        # 狀態
        self.current_screenshot_path = None
        self.current_weapons = []
        self.weapon_display_index = 0
        
        # 新增：狀態完成追蹤
        self.caption_completed = False
        self.tts_completed = True
        self.wait_timer_completed = False
        
        # FPS 計算
        self.fps_timer = QTimer()
        self.fps_timer.timeout.connect(self.update_fps)
        self.fps_timer.start(1000)
        self.frame_count = 0
        self.current_fps = 0
        
    def setup_ui(self):
        """設定 UI"""
        title = "DefenseSystem" + (" - Mini Mode" if self.startup_params.get('mini_mode', False) else "")
        self.setWindowTitle(title)
        
        # 設定視窗大小
        if self.startup_params['fullscreen']:
            self.showFullScreen()
        else:
            self.setFixedSize(self.window_width, self.window_height)
            
        # 設定黑色背景
        self.setStyleSheet("background-color: black;")
        
        # 主容器
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # 相機顯示
        self.camera_label = QLabel(self.central_widget)
        self.camera_label.resize(self.window_width, self.window_height)
        self.camera_label.setScaledContents(False)  # 不要自動縮放，我們手動處理
        self.camera_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera_label.setStyleSheet("background-color: #111;")
        
        # 載入中提示
        self.loading_label = QLabel("載入相機中...", self.central_widget)
        loading_font_size = int(self.startup_params.get('loading_text_size', 24) * self.scale_factor)
        self.loading_label.setStyleSheet("""
            color: white;
            font-size: %dpx;
            background-color: transparent;
        """ % loading_font_size)
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label.resize(self.window_width, 100)
        self.loading_label.move(0, self.window_height // 2 - 50)
        
        # 偵測動畫層 - 使用新動畫系統
        self.detection_overlay = DetectionOverlay(self.central_widget)
        self.detection_overlay.resize(self.window_width, self.window_height)
        
        # 連接檢測狀態信號
        self.detection_overlay.detection_updated.connect(self.on_detection_state_changed)
        
        # 截圖顯示層
        self.screenshot_label = QLabel(self.central_widget)
        self.screenshot_label.resize(self.window_width, self.window_height)
        self.screenshot_label.setScaledContents(True)
        self.screenshot_label.hide()
        
        # 字幕顯示 - 初始隱藏
        caption_text_size = self.startup_params.get('caption_text_size', 28)
        self.caption_widget = CaptionWidget(self.central_widget, self.scale_factor, caption_text_size)
        self.caption_widget.resize(self.window_width, self.window_height)
        self.caption_widget.hide()
        
        # 武器圖片顯示
        self.weapon_label = QLabel(self.central_widget)
        self.weapon_label.resize(self.window_width, self.window_height)
        self.weapon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.weapon_label.setScaledContents(False)  # 保持原始比例
        self.weapon_label.hide()
        
        # 黑屏遮罩 - 用於武器切換轉場
        self.black_overlay = QLabel(self.central_widget)
        self.black_overlay.resize(self.window_width, self.window_height)
        self.black_overlay.setStyleSheet("background-color: black;")
        self.black_overlay.hide()
        
        # Debug 顯示 - 更左上，字體更大
        if self.startup_params['debug_mode']:
            self.debug_label = QLabel(self.central_widget)
            self.debug_label.move(int(5 * self.scale_factor), int(5 * self.scale_factor))
            self.debug_label.resize(int(500 * self.scale_factor), int(250 * self.scale_factor))
            debug_font_size = int(self.startup_params.get('debug_text_size', 16) * self.scale_factor)
            self.debug_label.setStyleSheet("""
                color: white;
                background-color: rgba(0, 0, 0, 192);
                padding: %dpx;
                font-family: monospace;
                font-size: %dpx;
                font-weight: bold;
            """ % (int(8 * self.scale_factor), debug_font_size))
            self.debug_label.show()
            
    def connect_signals(self):
        """連接信號"""
        # 狀態機信號
        self.state_machine.state_changed.connect(self.on_state_changed)
        self.state_machine.screenshot_requested.connect(self.take_screenshot)
        self.state_machine.llm_analysis_requested.connect(self.start_llm_analysis)
        self.state_machine.caption_display_requested.connect(self.display_caption)
        self.state_machine.weapon_display_requested.connect(self.display_weapons)
        self.state_machine.reset_requested.connect(self.reset_system)
        
        # 相機信號
        self.camera_manager.frame_ready.connect(self.process_frame)
        
        # 人臉偵測信號
        self.face_detector.face_detected.connect(self.on_face_detected)
        
        # Ollama 服務信號
        self.ollama_service.analysis_complete.connect(self.on_llm_complete)
        
        # 字幕完成信號
        self.caption_widget.typing_complete.connect(self.on_caption_typing_complete)
        self.caption_widget.tc_typing_complete.connect(self.on_tc_typing_complete)
        self.caption_widget.en_typing_complete.connect(self.on_en_typing_complete)
        
        # 檢測狀態信號 (已在setup_ui中連接)
        # self.detection_overlay.detection_updated.connect(self.on_detection_state_changed)
        
        # TTS 信號連接
        if hasattr(self, 'tts_service'):
            self.tts_service.tts_finished.connect(self.on_tts_finished)
        
    def start_system(self):
        """啟動系統"""
        # 設定 No LLM 模式
        self.state_machine.set_no_llm_mode(self.startup_params['no_llm_mode'])
        
        # 啟動相機
        self.camera_manager.start(self.startup_params['camera_index'])
        
        # 第一個畫面到達時隱藏載入提示
        self.first_frame_received = False
        
        # 啟動狀態機
        self.state_machine.start()
        
    def process_frame(self, frame):
        """處理相機畫面"""
        self.frame_count += 1
        
        # 隱藏載入提示
        if not self.first_frame_received:
            self.first_frame_received = True
            self.loading_label.hide()
        
        # 從 1920x1080 裁切出中間的 1080x1920 區域
        cropped_frame = self.crop_frame_to_portrait(frame)
        
        # 根據 mini mode 進行縮放
        if self.startup_params.get('mini_mode', False):
            # Mini mode: 縮小一半
            target_width = int(1080 * 0.5)
            target_height = int(1920 * 0.5)
        else:
            # Full mode: 保持原始大小
            target_width = 1080
            target_height = 1920
        
        # 縮放到目標尺寸
        if cropped_frame.shape[1] != target_width or cropped_frame.shape[0] != target_height:
            cropped_frame = cv2.resize(cropped_frame, (target_width, target_height), 
                                     interpolation=cv2.INTER_LINEAR)
        
        # 在幀上繪製檢測框（如果需要）
        final_frame = self.detection_overlay.draw_on_frame(cropped_frame)
        
        # 顯示畫面
        qimage = CameraManager.frame_to_qimage(final_frame)
        pixmap = QPixmap.fromImage(qimage)
        self.camera_label.setPixmap(pixmap)
        
        # 人臉偵測 - 高性能版本，减少重复计算
            detection_result = self.face_detector.process_frame(frame)
        current_state = self.state_machine.current_state
        
            if detection_result:
            # 調整偵測結果座標以配合裁切後的顯示
            adjusted_bbox = self.adjust_detection_coordinates(detection_result, frame.shape, target_width, target_height)
            if adjusted_bbox:  # 只有當人臉在裁切區域內時才處理
                self.last_detection_bbox = adjusted_bbox
                
                # 只在 DETECTING 狀態更新狀態機
                if current_state == SystemState.DETECTING:
                    self.state_machine.update_face_detection(True)
                
                # 更新偵測框動畫 - 在除了 CAPTION 狀態之外的所有狀態顯示
                if current_state != SystemState.CAPTION:
                    # 更新偵測框動畫 - 使用新方法
                    face_rect = (int(adjusted_bbox['x']), int(adjusted_bbox['y']), 
                               int(adjusted_bbox['width']), int(adjusted_bbox['height']))
                    self.detection_overlay.update_faces([face_rect])
                else:
                    # 清除檢測框
                    self.detection_overlay.clear_detections()
            else:
                # 人臉不在裁切區域內
                self.last_detection_bbox = None
                if current_state == SystemState.DETECTING:
                    self.state_machine.update_face_detection(False)
                self.detection_overlay.clear_detections()
        else:
            # 沒有偵測到人臉
            self.last_detection_bbox = None
            if current_state == SystemState.DETECTING:
                self.state_machine.update_face_detection(False)
            self.detection_overlay.clear_detections()
                
    def crop_frame_to_portrait(self, frame):
        """從 1920x1080 裁切出中間的 1080x1920 區域"""
        height, width = frame.shape[:2]
        
        # 確保輸入是 1920x1080
        if width != 1920 or height != 1080:
            # 如果不是，先調整到 1920x1080
            frame = cv2.resize(frame, (1920, 1080), interpolation=cv2.INTER_LINEAR)
            width, height = 1920, 1080
        
        # 正確的裁切邏輯：
        # 從 1920x1080 裁切出 1080x1920
        # 由於原始高度只有 1080，我們需要從寬度上裁切更多來補償高度不足
        
        # 計算裁切區域
        # 我們需要 1080 寬度，所以水平裁切
        crop_x = (1920 - 1080) // 2  # 水平居中裁切
        
        # 對於高度，我們有兩個選擇：
        # 1. 保持原始高度 1080，但這樣會得到 1080x1080
        # 2. 從寬度上裁切更多來得到 9:16 的比例
        
        # 選擇方案 2：計算需要裁切的寬度來得到 9:16 比例
        target_ratio = 9/16  # 目標比例 (寬:高)
        current_height = 1080
        
        # 計算需要的寬度來得到 9:16 比例
        required_width = int(current_height * target_ratio)  # 1080 * (9/16) = 607.5
        
        # 從中間裁切出 607.5x1080 的區域
        crop_x = (1920 - required_width) // 2
        
        # 裁切出 607.5x1080 的區域
        cropped = frame[0:1080, crop_x:crop_x+required_width]
        
        # 縮放到 1080x1920
        portrait_crop = cv2.resize(cropped, (1080, 1920), interpolation=cv2.INTER_LINEAR)
        
        return portrait_crop
        
    def adjust_detection_coordinates(self, detection_result, original_shape, display_width, display_height):
        """調整偵測座標以配合裁切後的顯示"""
        orig_h, orig_w = original_shape[:2]  # 1080, 1920
        
        # 計算實際裁切參數（參考 crop_frame_to_portrait）
        target_ratio = 9/16  # 目標比例 (寬:高)
        required_width = int(orig_h * target_ratio)  # 1080 * (9/16) = 607.5
        crop_x = (orig_w - required_width) // 2  # 從1920裁切到607.5的起始x座標
        
        # 第一步：將原始檢測坐標調整到裁切區域
        # 檢查人臉是否在裁切區域內
        face_left = detection_result['x']
        face_right = detection_result['x'] + detection_result['width']
        
        # 如果人臉不在裁切區域內，返回None
        if face_right < crop_x or face_left > crop_x + required_width:
            return None
            
        # 調整到裁切區域座標系
        adjusted_x = max(0, detection_result['x'] - crop_x)
        adjusted_y = detection_result['y']
        adjusted_width = min(detection_result['width'], required_width - adjusted_x)
        adjusted_height = detection_result['height']
        
        # 確保人臉在裁切區域範圍內
        if adjusted_x + adjusted_width <= 0 or adjusted_y + adjusted_height <= 0:
            return None
            
        # 第二步：從裁切區域 (607.5x1080) 縮放到 (1080x1920)
        crop_scale_x = 1080 / required_width  # 1080 / 607.5 ≈ 1.78
        crop_scale_y = 1920 / orig_h  # 1920 / 1080 ≈ 1.78
        
        scaled_x = adjusted_x * crop_scale_x
        scaled_y = adjusted_y * crop_scale_y
        scaled_width = adjusted_width * crop_scale_x
        scaled_height = adjusted_height * crop_scale_y
        
        # 第三步：根據顯示模式進行最終縮放
        final_scale_x = display_width / 1080
        final_scale_y = display_height / 1920
        
        final_x = scaled_x * final_scale_x
        final_y = scaled_y * final_scale_y
        final_width = scaled_width * final_scale_x
        final_height = scaled_height * final_scale_y
        
        return {
            'x': final_x,
            'y': final_y,
            'width': final_width,
            'height': final_height,
            'confidence': detection_result.get('confidence', 0)
        }
            
    def on_face_detected(self, detected, bbox):
        """處理人臉偵測結果"""
        # 注意：檢測框更新邏輯已移到 process_frame 中
        # 這個函數現在主要用於其他可能的人臉檢測事件處理
        pass
    
    def on_detection_state_changed(self, has_faces):
        """處理檢測狀態變化"""
        if self.startup_params['debug_mode']:
            print(f"檢測狀態變化: {'有人臉' if has_faces else '無人臉'}")
        # 可以在這裡添加其他檢測狀態變化的處理邏輯
            
    def on_state_changed(self, state):
        """處理狀態變更"""
        print(f"State changed to: {state.value}")
        
        # 更新 debug 顯示
        if self.startup_params['debug_mode']:
            self.update_debug_info()
            
    def take_screenshot(self):
        """擷取畫面"""
        self.current_screenshot_path = self.camera_manager.take_screenshot()
        
        if self.current_screenshot_path:
            # 如果是 No LLM 模式，直接使用預設回應
            if self.startup_params['no_llm_mode']:
                default_response = {
                    'caption': 'Emergency defense protocol activated.',
                    'caption_tc': '緊急防禦協議啟動。',
                    'weapons': ['01', '02']
                }
                self.state_machine.on_llm_complete(default_response)
            else:
                # 發送 AI 分析請求
                self.state_machine.llm_analysis_requested.emit(self.current_screenshot_path)
                
    def start_llm_analysis(self, image_path):
        """開始 AI 分析"""
        weapon_list = self.config_loader.get_weapon_list()
        self.ollama_service.analyze_image(image_path, weapon_list)
        
    def on_llm_complete(self, response):
        """AI 分析完成"""
        self.state_machine.on_llm_complete(response)
        
    def display_caption(self, response):
        """顯示字幕和截圖"""
        # 重置完成狀態
        self.caption_completed = False
        self.tts_completed = True  # 預設為完成，如果有TTS才會設為False
        self.wait_timer_completed = False
        
        # 顯示截圖
        if self.current_screenshot_path:
            # 載入原始截圖
            original_frame = cv2.imread(self.current_screenshot_path)
            if original_frame is not None:
                # 應用相同的裁切邏輯
                cropped_frame = self.crop_frame_to_portrait(original_frame)
                
                # 根據 mini mode 進行縮放
                if self.startup_params.get('mini_mode', False):
                    # Mini mode: 縮小一半
                    target_width = int(1080 * 0.5)
                    target_height = int(1920 * 0.5)
                else:
                    # Full mode: 保持原始大小
                    target_width = 1080
                    target_height = 1920
                
                # 縮放到目標尺寸
                if cropped_frame.shape[1] != target_width or cropped_frame.shape[0] != target_height:
                    cropped_frame = cv2.resize(cropped_frame, (target_width, target_height), 
                                             interpolation=cv2.INTER_LINEAR)
                
                # 轉換為 QPixmap
                qimage = CameraManager.frame_to_qimage(cropped_frame)
                pixmap = QPixmap.fromImage(qimage)
            self.screenshot_label.setPixmap(pixmap)
            
            # Fade in 效果
            self.fade_in_widget(self.screenshot_label)
            else:
                # 如果載入失敗，使用原始方法
                pixmap = QPixmap(self.current_screenshot_path)
                self.screenshot_label.setPixmap(pixmap)
                self.fade_in_widget(self.screenshot_label)
            
        # 檢查是否有中英文字幕
        caption_tc = response.get('caption_tc', '')
        caption_en = response.get('caption', '')  # 英文字幕存在caption字段
        typing_speed = self.config.get('caption_typing_speed', 50)
        
        # 儲存武器列表
        self.current_weapons = response.get('weapons', [])
        
        # 準備TTS和字幕同步
        tts_rate = 140  # 從TTS配置獲取速度，預設140 WPM
        if hasattr(self, 'tts_service') and self.tts_service.worker and self.tts_service.worker.config:
            tts_rate = self.tts_service.worker.config.get_int('rate', 140)
        
        # 開始字幕顯示
        if caption_tc and caption_en:
            # 雙語模式：先啟用TTS同步，再顯示字幕
            if caption_en and hasattr(self, 'tts_service') and self.tts_service.is_available():
                self.caption_widget.enable_tts_sync(caption_en, tts_rate)
                print(f"TTS: 字幕出現，啟用同步並開始朗讀: '{caption_en}'")
                self.tts_completed = False  # 標記TTS未完成
                self.tts_service.speak_text(caption_en)
            
            self.caption_widget.show_bilingual_caption(caption_tc, caption_en, typing_speed)
        elif caption_tc:
            # 只有中文
            self.caption_widget.show_caption(caption_tc, typing_speed)
        elif caption_en:
            # 只有英文：啟用TTS同步
            if hasattr(self, 'tts_service') and self.tts_service.is_available():
                self.caption_widget.enable_tts_sync(caption_en, tts_rate)
                print(f"TTS: 字幕出現，啟用同步並開始朗讀: '{caption_en}'")
                self.tts_completed = False  # 標記TTS未完成
                self.tts_service.speak_text(caption_en)
            
            self.caption_widget.show_caption(caption_en, typing_speed)
        else:
            # 沒有字幕，直接標記完成
            self.caption_completed = True
            self.check_all_completed()
        
    def on_tc_typing_complete(self):
        """TC字幕打字完成"""
        print("TC typing complete")
        
    def on_en_typing_complete(self):
        """EN字幕打字完成"""
        print("EN typing complete")
        
    def on_caption_typing_complete(self):
        """字幕打字完成（單語模式）或雙語都完成"""
        print("All caption typing complete")
        self.caption_completed = True
        
        # 啟動等待計時器
        wait_time = self.config.get('caption_wait_after', 2.0) * 1000
        QTimer.singleShot(int(wait_time), self.on_wait_timer_complete)
        
    def on_tts_finished(self):
        """TTS朗讀完成"""
        print("TTS speaking complete")
        self.tts_completed = True
        
        # 禁用TTS同步模式
        if hasattr(self, 'caption_widget'):
            self.caption_widget.disable_tts_sync()
            
        self.check_all_completed()
        
    def on_wait_timer_complete(self):
        """等待計時器完成"""
        print("Wait timer complete")
        self.wait_timer_completed = True
        self.check_all_completed()
        
    def check_all_completed(self):
        """檢查所有事件是否完成，如果都完成則進入下一狀態"""
        if self.caption_completed and self.tts_completed and self.wait_timer_completed:
            print("All events completed - moving to weapon display")
            self.state_machine.on_weapon_display_requested(self.current_weapons)
                         
    def display_weapons(self, weapon_ids):
        """顯示武器"""
        if not weapon_ids:
            self.state_machine.on_weapon_display_complete()
            return
            
        # 隱藏字幕和截圖，準備顯示武器
        self.caption_widget.hide()
        self.screenshot_label.hide()
        
        # 顯示黑屏遮罩作為起始轉場
        self.black_overlay.show()
            
        self.weapon_display_index = 0
        self.current_weapons = weapon_ids
        self.display_next_weapon()
        
    def display_next_weapon(self):
        """顯示下一個武器"""
        if self.weapon_display_index >= len(self.current_weapons):
            # 所有武器顯示完成，隱藏黑屏遮罩
            self.black_overlay.hide()
            self.state_machine.on_weapon_display_complete()
            return
            
        weapon_id = self.current_weapons[self.weapon_display_index]
        weapon_info = self.weapon_config.get(weapon_id)
        
        # Debug: 武器顯示信息
        print(f"Debug: 顯示武器 - ID: {weapon_id}, 索引: {self.weapon_display_index}")
        print(f"Debug: 武器配置存在: {weapon_info is not None}")
        if weapon_info:
            print(f"Debug: 武器名稱: {weapon_info['name']}, 圖片: {weapon_info['image_path']}")
        else:
            print(f"Debug: 錯誤 - 找不到武器ID '{weapon_id}' 的配置！")
            print(f"Debug: 可用武器ID: {list(self.weapon_config.keys())}")
        
        if weapon_info:
            # 顯示武器圖片
            self.show_weapon_image(weapon_info)
            
            # 控制 Arduino
            if self.arduino_controller and weapon_info['pin']:
                self.arduino_controller.control_pin(
                    weapon_info['pin'],
                    weapon_info['wait_before'],
                    weapon_info['high_time'],
                    weapon_info['wait_after']
                )
        else:
            # 如果找不到武器配置，顯示錯誤信息並跳過
            print(f"警告: 武器ID '{weapon_id}' 找不到配置，跳過顯示")
                
        self.weapon_display_index += 1
        
        # 計算下一個武器的顯示時間
        if weapon_info:
            fade_in = weapon_info.get('image_fade_in', 1.0)
            display = weapon_info.get('image_display', 3.0)
            fade_out = weapon_info.get('image_fade_out', 1.0)
            switch_delay = self.config.get('weapon_switch_delay', 0.5)
            
            total_time = (fade_in + display + fade_out + switch_delay) * 1000
        else:
            total_time = 2000  # 如果找不到配置，2秒後繼續下一個
            
        QTimer.singleShot(int(total_time), self.display_next_weapon)
        
    def show_weapon_image(self, weapon_info):
        """顯示武器圖片"""
        image_path = os.path.join("weapons_img", weapon_info['image_path'])
        
        # Debug: 圖片路徑信息
        print(f"Debug: 載入武器圖片 - 路徑: {image_path}")
        print(f"Debug: 圖片文件存在: {os.path.exists(image_path)}")
        
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            
            # 檢查圖片是否成功載入
            if pixmap.isNull():
                print(f"錯誤: 無法載入圖片 {image_path}")
                return
                
            print(f"Debug: 圖片載入成功 - 尺寸: {pixmap.width()}x{pixmap.height()}")
            
            # 在視窗中居中顯示原始大小
            # 如果圖片太大，才進行縮放
            if pixmap.width() > self.window_width or pixmap.height() > self.window_height:
                original_size = f"{pixmap.width()}x{pixmap.height()}"
                pixmap = pixmap.scaled(self.window_width, self.window_height, 
                                     Qt.AspectRatioMode.KeepAspectRatio,
                                     Qt.TransformationMode.SmoothTransformation)
                print(f"Debug: 圖片已縮放 - 從 {original_size} 到 {pixmap.width()}x{pixmap.height()}")
                                     
            self.weapon_label.setPixmap(pixmap)
            print(f"Debug: 武器圖片已設置到 weapon_label")
            
            # Fade in
            fade_in_time = weapon_info.get('image_fade_in', 1.0) * 1000
            self.fade_in_weapon_with_black_transition(int(fade_in_time))
            
            # Schedule fade out
            display_time = weapon_info.get('image_display', 3.0) * 1000
            fade_out_time = weapon_info.get('image_fade_out', 1.0) * 1000
            
            QTimer.singleShot(int(display_time), 
                            lambda: self.fade_out_weapon_with_black_transition(int(fade_out_time)))
        else:
            print(f"錯誤: 武器圖片文件不存在 - {image_path}")
            # 可以考慮顯示一個預設圖片或錯誤提示
        
    def fade_in_weapon_with_black_transition(self, duration):
        """帶黑屏轉場的武器淡入效果"""
        # 確保黑屏遮罩在最上層
        self.black_overlay.raise_()
        self.black_overlay.show()
        
        # 顯示武器圖片（在黑屏下方）
        self.weapon_label.show()
        
        # 先淡出黑屏遮罩
        effect = QGraphicsOpacityEffect()
        self.black_overlay.setGraphicsEffect(effect)
        
        self.fade_animation = QPropertyAnimation(effect, b"opacity")
        self.fade_animation.setDuration(duration)
        self.fade_animation.setStartValue(1)
        self.fade_animation.setEndValue(0)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.fade_animation.finished.connect(self.black_overlay.hide)
        self.fade_animation.start()
        
    def fade_out_weapon_with_black_transition(self, duration):
        """帶黑屏轉場的武器淡出效果"""
        # 先淡入黑屏遮罩
        self.black_overlay.show()
        self.black_overlay.raise_()
        
        effect = QGraphicsOpacityEffect()
        self.black_overlay.setGraphicsEffect(effect)
        
        self.fade_out_animation = QPropertyAnimation(effect, b"opacity")
        self.fade_out_animation.setDuration(duration)
        self.fade_out_animation.setStartValue(0)
        self.fade_out_animation.setEndValue(1)
        self.fade_out_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.fade_out_animation.finished.connect(self.weapon_label.hide)
        self.fade_out_animation.start()
                            
    def reset_system(self):
        """重置系統"""
        # 隱藏所有顯示元件
        self.detection_overlay.clear_detections()
        self.screenshot_label.hide()
        self.caption_widget.hide()
        self.weapon_label.hide()
        self.black_overlay.hide()  # 隱藏黑屏遮罩
        
        # 刪除截圖
        if self.current_screenshot_path and os.path.exists(self.current_screenshot_path):
            try:
                os.remove(self.current_screenshot_path)
            except:
                pass
                
        self.current_screenshot_path = None
        self.current_weapons = []
        
        # 重置狀態追蹤
        self.caption_completed = False
        self.tts_completed = True  # 預設為完成
        self.wait_timer_completed = False
        
    def fade_in_widget(self, widget, duration=None):
        """淡入效果"""
        if duration is None:
            duration = int(self.config.get('screenshot_fade_in', 1.0) * 1000)
            
        effect = QGraphicsOpacityEffect()
        widget.setGraphicsEffect(effect)
        widget.show()
        
        self.fade_animation = QPropertyAnimation(effect, b"opacity")
        self.fade_animation.setDuration(duration)
        self.fade_animation.setStartValue(0)
        self.fade_animation.setEndValue(1)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.fade_animation.start()
        
    def fade_out_widget(self, widget, duration=None):
        """淡出效果"""
        if duration is None:
            duration = int(self.config.get('screenshot_fade_out', 1.0) * 1000)
            
        effect = widget.graphicsEffect()
        if not effect:
            effect = QGraphicsOpacityEffect()
            widget.setGraphicsEffect(effect)
            
        self.fade_out_animation = QPropertyAnimation(effect, b"opacity")
        self.fade_out_animation.setDuration(duration)
        self.fade_out_animation.setStartValue(1)
        self.fade_out_animation.setEndValue(0)
        self.fade_out_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.fade_out_animation.finished.connect(widget.hide)
        self.fade_out_animation.start()
        
    def update_fps(self):
        """更新 FPS"""
        self.current_fps = self.frame_count
        self.frame_count = 0
        
        if self.startup_params['debug_mode']:
            self.update_debug_info()
            
    def update_debug_info(self):
        """更新 Debug 資訊"""
        if hasattr(self, 'debug_label'):
            detection_time = self.state_machine.get_detection_time()
            arduino_status = "Connected" if self.arduino_controller and self.arduino_controller.is_connected else "Not connected"
            llm_mode = "No LLM" if self.startup_params['no_llm_mode'] else "Normal"
            mode = "Mini Mode" if self.startup_params.get('mini_mode', False) else "Full Mode"
            
            # 顯示當前武器列表
            weapons_display = "None"
            if hasattr(self, 'current_weapons') and self.current_weapons:
                weapons_display = f"[{', '.join(self.current_weapons)}]"
            
            debug_text = f"""State: {self.state_machine.current_state.value}
FPS: {self.current_fps}
Detection Time: {detection_time:.1f}s
Arduino: {arduino_status}
LLM Mode: {llm_mode}
Display: {mode}
Weapons: {weapons_display}
Window: {self.window_width}x{self.window_height}"""
            
            self.debug_label.setText(debug_text)
            
    def closeEvent(self, event):
        """關閉事件"""
        self.state_machine.stop()
        self.camera_manager.stop()
        self.face_detector.release()
        
        if self.arduino_controller:
            self.arduino_controller.disconnect()
        
        # 關閉TTS服務
        if hasattr(self, 'tts_service'):
            print("正在關閉TTS服務...")
            self.tts_service.shutdown()
            
        event.accept()