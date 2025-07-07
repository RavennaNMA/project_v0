# Location: project_v2/core/face_detector.py
# Usage: 使用 MediaPipe 進行高效能人臉偵測

import mediapipe as mp
import numpy as np
from PyQt6.QtCore import QObject, pyqtSignal
import cv2


class FaceDetector(QObject):
    """MediaPipe 人臉偵測器"""
    
    face_detected = pyqtSignal(bool, object)  # (偵測到與否, 偵測框資訊)
    
    def __init__(self, config=None):
        super().__init__()
        
        self.config = config or {}
        
        # 初始化 MediaPipe
        self.mp_face_detection = mp.solutions.face_detection
        
        # 從配置取得靈敏度
        confidence = self.config.get('detection_sensitivity', 0.5)
        
        try:
            self.face_detection = self.mp_face_detection.FaceDetection(
                model_selection=0,  # 0: 短距離模型 (更快)
                min_detection_confidence=confidence
            )
        except Exception as e:
            print(f"Failed to initialize MediaPipe face detection: {e}")
            self.face_detection = None
        
        self.last_detection = None
        self.main_face_id = 0
        
        # 穩定性過濾參數
        self.position_threshold = 5  # 位置變化閾值（像素）
        self.size_threshold = 0.1    # 尺寸變化閾值（比例）
        
    def process_frame(self, frame):
        """處理畫面並偵測人臉"""
        if frame is None or self.face_detection is None:
            return None
        
        # 额外的安全检查
        if not hasattr(frame, 'shape') or len(frame.shape) < 2:
            return None
            
        try:
            # 轉換為 RGB (MediaPipe 需要)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # 執行偵測
            results = self.face_detection.process(rgb_frame)
            
            if results and hasattr(results, 'detections') and results.detections:
                # 選擇最大的臉部 (通常是最近的)
                best_detection = self._select_main_face(results.detections, frame.shape)
                
                if best_detection:
                    # 轉換為畫面座標
                    bbox = self._get_bbox_coords(best_detection, frame.shape)
                    
                    # 穩定性過濾：只有當變化足夠大時才更新
                    if self._should_update_detection(bbox):
                        self.last_detection = bbox
                        self.face_detected.emit(True, bbox)
                        return bbox
                    elif self.last_detection:
                        # 使用上次的檢測結果，減少抖動
                        self.face_detected.emit(True, self.last_detection)
                        return self.last_detection
            
            # 沒有偵測到人臉
            self.last_detection = None
            self.face_detected.emit(False, None)
            return None
            
        except Exception as e:
            print(f"Face detection error: {e}")
            # 發生錯誤時，不發送偵測信號
            return None
        
    def _select_main_face(self, detections, frame_shape):
        """選擇主要追蹤的人臉"""
        if not detections:
            return None
            
        h, w = frame_shape[:2]
        best_detection = None
        max_area = 0
        
        for detection in detections:
            try:
                if hasattr(detection, 'location_data') and detection.location_data:
                    bbox = detection.location_data.relative_bounding_box
                    if bbox:
                        area = bbox.width * bbox.height * w * h
                        
                        if area > max_area:
                            max_area = area
                            best_detection = detection
            except Exception as e:
                print(f"Error processing detection: {e}")
                continue
                
        return best_detection
        
    def _get_bbox_coords(self, detection, frame_shape):
        """將相對座標轉換為絕對座標"""
        try:
            h, w = frame_shape[:2]
            
            # 安全地訪問bounding box
            if not hasattr(detection, 'location_data') or not detection.location_data:
                return None
                
            bbox = detection.location_data.relative_bounding_box
            if not bbox:
                return None
            
            x = int(bbox.xmin * w)
            y = int(bbox.ymin * h)
            width = int(bbox.width * w)
            height = int(bbox.height * h)
            
            # 確保座標在畫面範圍內
            x = max(0, min(x, w - 1))
            y = max(0, min(y, h - 1))
            width = min(width, w - x)
            height = min(height, h - y)
            
            # 安全地獲取confidence值
            confidence = 0.0
            try:
                if hasattr(detection, 'score') and detection.score:
                    confidence = detection.score[0] if len(detection.score) > 0 else 0.0
            except (AttributeError, IndexError, TypeError):
                confidence = 0.0
            
            return {
                'x': x,
                'y': y,
                'width': width,
                'height': height,
                'confidence': confidence
            }
            
        except Exception as e:
            print(f"Error getting bbox coordinates: {e}")
            return None
    
    def _should_update_detection(self, new_bbox):
        """判斷是否應該更新檢測結果（穩定性過濾）"""
        if not self.last_detection or not new_bbox:
            return True
        
        last = self.last_detection
        
        # 檢查位置變化
        pos_diff_x = abs(new_bbox['x'] - last['x'])
        pos_diff_y = abs(new_bbox['y'] - last['y'])
        if pos_diff_x > self.position_threshold or pos_diff_y > self.position_threshold:
            return True
        
        # 檢查尺寸變化
        last_area = last['width'] * last['height']
        new_area = new_bbox['width'] * new_bbox['height']
        if last_area > 0:
            size_change = abs(new_area - last_area) / last_area
            if size_change > self.size_threshold:
                return True
        
        return False
        
    def draw_detection(self, frame, bbox):
        """在畫面上繪製偵測框 (用於測試)"""
        if bbox:
            x, y, w, h = bbox['x'], bbox['y'], bbox['width'], bbox['height']
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            # 顯示信心度
            conf_text = f"{bbox['confidence']:.2f}"
            cv2.putText(frame, conf_text, (x, y - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                       
        return frame
        
    def release(self):
        """釋放資源"""
        if hasattr(self, 'face_detection') and self.face_detection is not None:
            try:
                self.face_detection.close()
            except Exception as e:
                print(f"Error closing face detection: {e}") 