import cv2
import time
import threading
import queue
import numpy as np
import random
import gc
from concurrent.futures import ThreadPoolExecutor
import configparser
import os


class AnimConfig:
    def __init__(self, config_file='anim_config.txt'):
        self.config = configparser.ConfigParser()
        if os.path.exists(config_file):
            self.config.read(config_file, encoding='utf-8')
        else:
            self._create_default_config(config_file)
    
    def _create_default_config(self, config_file):
        """若設定檔不存在，建立預設設定"""
        print(f"設定檔 {config_file} 未找到，正在建立預設設定...")
        # 使用預設值建立設定
        self.config['BASIC'] = {
            'position_smooth': '0.15',
            'state1_duration': '33',
            'state2_duration': '34',
            'state3_duration': '13',
            'state4_duration': '20'
        }
        self.config['VISUAL'] = {
            'color_r': '255',
            'color_g': '255', 
            'color_b': '255',
            'alpha': '200',
            'flicker_probability': '0.2'
        }
        # 儲存預設設定
        with open(config_file, 'w', encoding='utf-8') as f:
            self.config.write(f)
    
    def get_float(self, section, key, default=0.0):
        try:
            return self.config.getfloat(section, key)
        except:
            return default
    
    def get_int(self, section, key, default=0):
        try:
            return self.config.getint(section, key)
        except:
            return default


class VisualRect:
    def __init__(self, x, y, w, h, config):
        self.config = config
        self.target_x = x
        self.target_y = y
        # 增加框的基礎尺寸 (放大1.5倍)
        self.target_w = w * 1.5
        self.target_h = h * 1.5
       
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
        self.position_smooth = self.config.get_float('BASIC', 'position_smooth', 0.08)  # 降低平滑度，更穩定
        self.state1_duration = self.config.get_int('BASIC', 'state1_duration', 40)  # 延長各階段時間
        self.state2_duration = self.config.get_int('BASIC', 'state2_duration', 40)
        self.state3_duration = self.config.get_int('BASIC', 'state3_duration', 20)
        self.state4_duration = self.config.get_int('BASIC', 'state4_duration', 30)
        
        # 計算總動畫時長
        self.total_duration = self.state1_duration + self.state2_duration + self.state3_duration + self.state4_duration


    def update(self, target_x, target_y, target_w, target_h):
        # 更新目標位置和尺寸 (放大1.5倍以獲得更大的框)
        self.target_x = target_x
        self.target_y = target_y
        self.target_w = target_w * 1.5
        self.target_h = target_h * 1.5
       
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
           
        # 狀態1: 外框角落線條出現 - 使用更穩定的平滑值
        if self.state >= 1:
            outside_smooth = self.config.get_float('STATE1', 'outside_smooth', 0.12)  # 更穩定
            self.outside_w += (self.target_w - self.outside_w) * outside_smooth
            self.outside_h += (self.target_h - self.outside_h) * outside_smooth
            
        # 狀態2: 內框出現 - 保持之前狀態的效果
        if self.state >= 2:
            inner_smooth = self.config.get_float('STATE2', 'inner_smooth', 0.1)  # 更穩定
            self.w += (self.target_w - self.w) * inner_smooth
            self.h += (self.target_h - self.h) * inner_smooth
            
        # 狀態3: 十字線開始出現 - 保持之前狀態的效果
        if self.state >= 3:
            cross_start_smooth = self.config.get_float('STATE3', 'cross_start_smooth', 0.08)  # 更穩定
            self.start_line += (1 - self.start_line) * cross_start_smooth
            
        # 狀態4: 十字線完全延伸 - 保持之前狀態的效果
        if self.state >= 4:
            cross_end_smooth = self.config.get_float('STATE4', 'cross_end_smooth', 0.12)  # 更穩定
            self.end_line += (1 - self.end_line) * cross_end_smooth


    def draw(self, frame):
        # 使用設定檔中的閃爍機率
        flicker_prob = self.config.get_float('VISUAL', 'flicker_probability', 0.2)
        show = random.random() > flicker_prob
       
        if show and (self.state in [1, 2, 3, 4]):
            # 使用設定檔中的顏色
            color_r = self.config.get_int('VISUAL', 'color_r', 255)
            color_g = self.config.get_int('VISUAL', 'color_g', 255)
            color_b = self.config.get_int('VISUAL', 'color_b', 255)
            color = (color_b, color_g, color_r)  # OpenCV使用BGR格式
            
            # 使用設定參數的角落線條
            corner_length = self.config.get_float('STATE1', 'corner_length_ratio', 0.07)
            line_thickness = self.config.get_int('STATE1', 'line_thickness', 2)
            
            # Convert to integer coordinates
            center_x = int(self.x)
            center_y = int(self.y)
            half_w = int(self.outside_w * 0.5)
            half_h = int(self.outside_h * 0.5)
            corner_len_w = int(self.outside_w * corner_length)
            corner_len_h = int(self.outside_h * corner_length)
            
            # Up left corner
            cv2.line(frame, 
                    (center_x - half_w, center_y - half_h),
                    (center_x - half_w + corner_len_w, center_y - half_h), 
                    color, line_thickness)
            cv2.line(frame, 
                    (center_x - half_w, center_y - half_h),
                    (center_x - half_w, center_y - half_h + corner_len_h), 
                    color, line_thickness)
            
            # Up right corner
            cv2.line(frame, 
                    (center_x + half_w, center_y - half_h),
                    (center_x + half_w - corner_len_w, center_y - half_h), 
                    color, line_thickness)
            cv2.line(frame, 
                    (center_x + half_w, center_y - half_h),
                    (center_x + half_w, center_y - half_h + corner_len_h), 
                    color, line_thickness)
            
            # Down right corner
            cv2.line(frame, 
                    (center_x + half_w, center_y + half_h),
                    (center_x + half_w - corner_len_w, center_y + half_h), 
                    color, line_thickness)
            cv2.line(frame, 
                    (center_x + half_w, center_y + half_h),
                    (center_x + half_w, center_y + half_h - corner_len_h), 
                    color, line_thickness)
            
            # Down left corner
            cv2.line(frame, 
                    (center_x - half_w, center_y + half_h),
                    (center_x - half_w + corner_len_w, center_y + half_h), 
                    color, line_thickness)
            cv2.line(frame, 
                    (center_x - half_w, center_y + half_h),
                    (center_x - half_w, center_y + half_h - corner_len_h), 
                    color, line_thickness)
       
        if show and (self.state in [2, 3]):
            # Draw inner rectangle using config parameters
            inner_alpha = self.config.get_float('STATE2', 'inner_alpha', 50) / 255.0
            inner_size_ratio = self.config.get_float('STATE2', 'inner_size_ratio', 0.9)
            
            # Create semi-transparent overlay
            overlay = frame.copy()
            inner_w = int(self.w * inner_size_ratio)
            inner_h = int(self.h * inner_size_ratio)
            
            cv2.rectangle(overlay,
                         (int(self.x - inner_w*0.5), int(self.y - inner_h*0.5)),
                         (int(self.x + inner_w*0.5), int(self.y + inner_h*0.5)),
                         color, -1)
            
            cv2.addWeighted(overlay, inner_alpha, frame, 1 - inner_alpha, 0, frame)
       
        if show and (self.state in [3, 4]):
            # Draw cross lines using config parameters
            cross_length_h = self.config.get_float('STATE3', 'cross_length_ratio_h', 0.59)
            cross_length_w = self.config.get_float('STATE3', 'cross_length_ratio_w', 0.55)
            
            # Calculate cross line positions
            start_h = int(self.start_line * self.h * cross_length_h)
            end_h = int(self.end_line * self.h * cross_length_h)
            start_w = int(self.start_line * self.w * cross_length_w)
            end_w = int(self.end_line * self.w * cross_length_w)
            
            # Up
            cv2.line(frame,
                    (int(self.x), int(self.y - start_h)),
                    (int(self.x), int(self.y - end_h)),
                    color, line_thickness)
            # Down
            cv2.line(frame,
                    (int(self.x), int(self.y + start_h)),
                    (int(self.x), int(self.y + end_h)),
                    color, line_thickness)
            # Right
            cv2.line(frame,
                    (int(self.x + start_w), int(self.y)),
                    (int(self.x + end_w), int(self.y)),
                    color, line_thickness)
            # Left
            cv2.line(frame,
                    (int(self.x - start_w), int(self.y)),
                    (int(self.x - end_w), int(self.y)),
                    color, line_thickness)


class CameraSystem:
    def __init__(self):
        # 載入動畫設定
        self.anim_config = AnimConfig()
        
        # 初始化攝影機
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            raise Exception("無法開啟攝影機")
           
        # 設定攝影機參數
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        self.cap.set(cv2.CAP_PROP_FPS, 60)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
       
        # 讀取實際設定值
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        print(f"攝影機設定: {self.width}x{self.height} @ {self.fps}fps")
       
        # 載入人臉偵測模型
        try:
            self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        except:
            # 若上述方式失敗，嘗試直接路徑
            self.face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
       
        # 視覺效果矩形列表
        self.visual_rects = []
       
        # 訓練相關變數
        self.templates = {'left': [], 'right': []}
        self.label_text = "等待訓練..."
        self.train_cooldown = 2.0
        self.last_train_time = 0
        self.train_queue = queue.Queue()
        self.train_lock = threading.Lock()
        self.is_training = False
       
        # 啟動訓練執行緒
        self.train_thread = threading.Thread(target=self._training_worker, daemon=True)
        self.train_thread.start()
       
        # 攝影機執行緒相關
        self.frame_queue = queue.Queue(maxsize=2)  # 稍微增加緩衝
        self.running = False
        self.thread = None
       
        # 效能優化相關
        self.last_face_detection_time = 0
        self.face_detection_interval = 1.0 / 30  # 適中的檢測頻率，平衡效能與穩定性
        self.last_faces = []
        
        # 人臉檢測平滑相關
        self.face_history = []  # 儲存最近幾幅畫面的檢測結果
        self.history_size = 5   # 保留最近5幅畫面的結果用於平滑
        self.stable_face = None # 當前穩定的人臉位置
        self.face_lost_count = 0 # 丟失人臉的幅畫面計數
        self.max_lost_frames = 10 # 最大允許丟失幅畫面數
       
        # 初始化執行緒池
        self.executor = ThreadPoolExecutor(max_workers=2)  # 減少執行緒數
       
        # 處理用的解析度 - 進一步優化
        self.process_width = 640  # 減小處理解析度
        self.process_height = 360


    def _training_worker(self):
        """Background training thread"""
        while True:
            try:
                data = self.train_queue.get()
                if data is None:
                    break
                template, label = data
                with self.train_lock:
                    self.templates[label].append(template)
                    print(f"Background training done: {label}")
                    print(f"Current {label} templates count: {len(self.templates[label])}")
                self.train_queue.task_done()
            except Exception as e:
                print(f"Training thread error: {str(e)}")
            finally:
                self.is_training = False


    def extract_features(self, frame):
        try:
            small_frame = cv2.resize(frame, (32, 32))
            gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
            normalized = gray.astype(np.float32) / 255.0
            return normalized
        except Exception as e:
            print(f"Feature extraction error: {str(e)}")
            return None
        finally:
            del small_frame
            del gray
            gc.collect()


    def train(self, label):
        try:
            current_time = time.time()
            if current_time - self.last_train_time < self.train_cooldown:
                print("Training cooldown, please wait...")
                return
            self.last_train_time = current_time
            print(f"Trying to add {label} training data...")
            ret, frame = self.cap.read()
            if not ret or frame is None:
                print("Cannot read camera frame, skip training.")
                return
            template = self.extract_features(frame)
            if template is not None:
                self.train_queue.put((template, label))
                self.is_training = True
                print(f"Added {label} training data to queue")
        except Exception as e:
            print(f"Training error: {str(e)}")
        finally:
            try:
                del frame
            except:
                pass
            try:
                del template
            except:
                pass
            gc.collect()


    def classify(self, frame):
        try:
            current_template = self.extract_features(frame)
            if current_template is None:
                return None
               
            with self.train_lock:
                if not any(len(templates) > 0 for templates in self.templates.values()):
                    return None
                   
                min_diff = float('inf')
                best_label = None
               
                for label, templates in self.templates.items():
                    if not templates:
                        continue
                    diffs = [np.mean(np.abs(current_template - template)) for template in templates]
                    avg_diff = np.mean(diffs)
                   
                    if avg_diff < min_diff:
                        min_diff = avg_diff
                        best_label = label
               
                if min_diff > 0.3:
                    return "Unknown"
                return best_label
               
        except Exception as e:
            print(f"Classification error: {str(e)}")
            return None
        finally:
            del current_template
            gc.collect()


    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._camera_loop, daemon=True)
        self.thread.start()
       
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        self.train_queue.put(None)
        self.train_thread.join()
        self.cap.release()
        cv2.destroyAllWindows()
       
    def _camera_loop(self):
        last_time = time.time()
        frames = 0
       
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                print("Cannot read camera frame")
                break
               
            frames += 1
            if time.time() - last_time >= 1.0:
                print(f"Camera FPS: {frames:.2f}")
                frames = 0
                last_time = time.time()
               
            # 非阻塞地放入队列
            try:
                self.frame_queue.put(frame, block=False)
            except queue.Full:
                # 如果队列满了，丢弃最旧的帧
                try:
                    self.frame_queue.get_nowait()
                    self.frame_queue.put(frame, block=False)
                except queue.Empty:
                    pass


    def detect_faces(self, frame):
        # 降低解析度進行處理
        small_frame = cv2.resize(frame, (self.process_width, self.process_height))
        gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
        
        # 应用高斯模糊减少噪声，提高检测稳定性
        gray = cv2.GaussianBlur(gray, (3, 3), 0)
        
        # 优化检测参数：更严格的参数以提高准确性
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.05,      # 更小的缩放步长，更精确
            minNeighbors=6,        # 更高的邻居要求，减少误检
            minSize=(30, 30),      # 最小脸部尺寸
            maxSize=(300, 300),    # 最大脸部尺寸
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        # 将检测结果转换回原始分辨率
        scale_x = self.width / self.process_width
        scale_y = self.height / self.process_height
        scaled_faces = [(int(x * scale_x), int(y * scale_y), int(w * scale_x), int(h * scale_y)) for (x, y, w, h) in faces]
        
        # 只保留最大的一张脸（最可能是主要的脸）
        if len(scaled_faces) > 0:
            # 根据面积排序，选择最大的脸
            largest_face = max(scaled_faces, key=lambda face: face[2] * face[3])
            return [largest_face]
        
        return []


    def smooth_face_detection(self, detected_faces):
        """平滑人臉檢測結果，減少抖動和誤檢"""
        
        if len(detected_faces) == 0:
            # 沒有檢測到人臉
            self.face_lost_count += 1
            
            # 若短時間內丟失，使用歷史位置預測
            if self.face_lost_count <= self.max_lost_frames and self.stable_face is not None:
                return [self.stable_face]
            else:
                # 長時間丟失，清除穩定位置
                self.stable_face = None
                return []
        
        # 檢測到人臉，重置丟失計數
        self.face_lost_count = 0
        current_face = detected_faces[0]  # 只處理一張臉
        
        # 新增到歷史記錄
        self.face_history.append(current_face)
        if len(self.face_history) > self.history_size:
            self.face_history.pop(0)
        
        # 若歷史記錄不足，直接回傳當前檢測結果
        if len(self.face_history) < 3:
            self.stable_face = current_face
            return [current_face]
        
        # 計算平滑後的位置（使用最近幾幅畫面的加權平均）
        weights = [0.4, 0.3, 0.2, 0.1][:len(self.face_history)]  # 新幅畫面權重更高
        weights = weights[::-1]  # 反轉，讓最新的幅畫面權重最高
        
        total_weight = sum(weights)
        avg_x = sum(face[0] * weight for face, weight in zip(self.face_history, weights)) / total_weight
        avg_y = sum(face[1] * weight for face, weight in zip(self.face_history, weights)) / total_weight
        avg_w = sum(face[2] * weight for face, weight in zip(self.face_history, weights)) / total_weight
        avg_h = sum(face[3] * weight for face, weight in zip(self.face_history, weights)) / total_weight
        
        # 更新穩定位置
        smoothed_face = (int(avg_x), int(avg_y), int(avg_w), int(avg_h))
        self.stable_face = smoothed_face
        
        return [smoothed_face]


    def put_text_with_background(self, frame, text, position, color=(255, 255, 255), bg_color=(0, 0, 0), scale=0.8):
        font = cv2.FONT_HERSHEY_SIMPLEX
        thickness = 2
        
        # 获取文本尺寸
        (text_width, text_height), baseline = cv2.getTextSize(text, font, scale, thickness)
        
        # 绘制背景矩形
        cv2.rectangle(frame, 
                     (position[0] - 5, position[1] - text_height - 5),
                     (position[0] + text_width + 5, position[1] + baseline + 5),
                     bg_color, -1)
        
        # 绘制文字
        cv2.putText(frame, text, position, font, scale, color, thickness)


    def run(self):
        self.start()
        last_time = time.time()
        frames = 0
        fps = 0
        
        # 创建窗口
        cv2.namedWindow('Face Detection with Training', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Face Detection with Training', 1920, 1080)
       
        try:
            while self.running:
                # 處理键盘输入
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    self.running = False
                elif key == ord('l'):
                    self.train('left')
                elif key == ord('r'):
                    self.train('right')
               
                # 读取并处理画面
                if not self.frame_queue.empty():
                    frame = self.frame_queue.get()
                   
                    # 并行处理人脸检测和分类
                    current_time = time.time()
                    if current_time - self.last_face_detection_time > self.face_detection_interval:
                        # 检测人脸
                        raw_faces = self.detect_faces(frame)
                        
                        # 应用平滑滤波
                        faces = self.smooth_face_detection(raw_faces)
                        
                        # 分类（只在有稳定人脸时进行）
                        if len(faces) > 0:
                            classify_future = self.executor.submit(self.classify, frame)
                            prediction = classify_future.result()
                            if prediction is not None:
                                self.label_text = prediction
                        
                        self.last_faces = faces
                        self.last_face_detection_time = current_time
                    else:
                        faces = self.last_faces
                   
                    # 更新视觉效果矩形
                    while len(self.visual_rects) > len(faces):
                        self.visual_rects.pop()
                    while len(self.visual_rects) < len(faces):
                        x, y, w, h = faces[len(self.visual_rects)]
                        self.visual_rects.append(VisualRect(x + w/2, y + h/2, w, h, self.anim_config))
                   
                    # 更新每个矩形
                    for i, (x, y, w, h) in enumerate(faces):
                        if i < len(self.visual_rects):
                            self.visual_rects[i].update(x + w/2, y + h/2, w, h)
                   
                    # 绘制视觉效果
                    for rect in self.visual_rects:
                        rect.draw(frame)
                   
                    # 显示训练相关信息
                    self.put_text_with_background(frame, f"Result: {self.label_text}", (10, 40))
                    left_count = len(self.templates['left'])
                    right_count = len(self.templates['right'])
                    self.put_text_with_background(frame, f"Left: {left_count}, Right: {right_count}", (10, 80))
                   
                    # 计算并显示FPS
                    frames += 1
                    current_time = time.time()
                    if current_time - last_time >= 1.0:
                        fps = frames / (current_time - last_time)
                        frames = 0
                        last_time = current_time
                    self.put_text_with_background(frame, f"FPS: {fps:.2f}", (10, 120))
                   
                    # 显示训练状态
                    train_status = "Training..." if self.is_training else "Idle"
                    self.put_text_with_background(frame, f"Status: {train_status}", (10, 160))
                    
                    # 显示人脸检测状态
                    face_count = len(faces)
                    if face_count > 0:
                        if self.stable_face is not None:
                            detection_status = f"Face: Stable ({face_count})"
                        else:
                            detection_status = f"Face: Detected ({face_count})"
                    else:
                        if self.face_lost_count > 0:
                            detection_status = f"Face: Lost ({self.face_lost_count}/{self.max_lost_frames})"
                        else:
                            detection_status = "Face: Searching..."
                    self.put_text_with_background(frame, detection_status, (10, 200))
                    
                    # 显示操作提示
                    self.put_text_with_background(frame, "Press 'L' for left, 'R' for right, 'Q' to quit", (10, 240))
                   
                    # 显示画面
                    cv2.imshow('Face Detection with Training', frame)
               
        except Exception as e:
            print(f"Main loop error: {str(e)}")
        finally:
            self.stop()
            self.executor.shutdown()
            print("Program ended")


if __name__ == "__main__":
    system = CameraSystem()
    system.run()