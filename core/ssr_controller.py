# Location: project_v2/core/ssr_controller.py
# Usage: SSR (Solid State Relay) 燈光控制器，控制場景燈光效果

import os
import csv
from PyQt6.QtCore import QObject, QThread, pyqtSignal, QTimer
import time


class SSRConfig:
    """SSR配置類"""
    def __init__(self):
        self.ssr1_pin = 12
        self.ssr1_delay_before = 500
        self.ssr1_delay_after = 500
        
        self.ssr2_pin = 13
        self.ssr2_delay_before = 300
        self.ssr2_delay_after = 300
        
        self.load_config()
        
    def load_config(self):
        """載入SSR配置"""
        config_path = "otherssr_config.csv"
        
        if not os.path.exists(config_path):
            print(f"SSR配置檔案不存在: {config_path}，使用預設值")
            self.create_default_config()
            return
            
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 4 and row[0]:
                        ssr_name = row[0].strip().lower()
                        
                        if ssr_name == 'ssr1':
                            self.ssr1_pin = int(row[1])
                            self.ssr1_delay_before = int(row[2])
                            self.ssr1_delay_after = int(row[3])
                        elif ssr_name == 'ssr2':
                            self.ssr2_pin = int(row[1])
                            self.ssr2_delay_before = int(row[2])
                            self.ssr2_delay_after = int(row[3])
                            
            print(f"SSR配置載入成功")
            print(f"  SSR1: Pin={self.ssr1_pin}, 前延遲={self.ssr1_delay_before}ms, 後延遲={self.ssr1_delay_after}ms")
            print(f"  SSR2: Pin={self.ssr2_pin}, 前延遲={self.ssr2_delay_before}ms, 後延遲={self.ssr2_delay_after}ms")
            
        except Exception as e:
            print(f"載入SSR配置失敗: {e}")
            self.create_default_config()
            
    def create_default_config(self):
        """建立預設配置檔案"""
        config_path = "otherssr_config.csv"
        
        try:
            with open(config_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['ssr1', '12', '500', '500'])
                writer.writerow(['ssr2', '13', '300', '300'])
                
            print(f"已建立預設SSR配置檔案: {config_path}")
            
        except Exception as e:
            print(f"建立SSR配置檔案失敗: {e}")


class SSRThread(QThread):
    """SSR控制執行緒"""
    
    status_changed = pyqtSignal(str)
    ssr1_ready = pyqtSignal()  # SSR1準備完成
    ssr2_ready = pyqtSignal()  # SSR2準備完成（進入SPOTLIGHT）
    
    def __init__(self, arduino_controller, ssr_config):
        super().__init__()
        self.arduino = arduino_controller
        self.config = ssr_config
        self.ssr1_active = False
        self.ssr2_active = False
        self.ssr1_processed = False
        self.ssr2_processed = False
        self.should_stop = False
        
    def activate_ssr1(self):
        """啟動SSR1"""
        print("Activating SSR1")
        self.ssr1_active = True
        self.ssr1_processed = False  # 重置處理狀態，允許重新啟動
        
    def activate_ssr2(self):
        """啟動SSR2"""
        print("Activating SSR2")
        self.ssr2_active = True
        self.ssr2_processed = False  # 重置處理狀態，允許重新啟動
        
    def deactivate_all(self):
        """關閉所有SSR"""
        self.should_stop = True
        
    def run(self):
        """執行緒主邏輯 - 動態檢查和處理SSR任務"""
        # 主循環，持續檢查需要處理的SSR任務
        while not self.should_stop:
            # 檢查SSR1
            if self.ssr1_active and not self.ssr1_processed:
                print(f"Processing SSR1: Pin {self.config.ssr1_pin}")
                # 等待前延遲
                if self.config.ssr1_delay_before > 0:
                    self.status_changed.emit(f"SSR1等待前延遲 {self.config.ssr1_delay_before}ms")
                    self.msleep(self.config.ssr1_delay_before)
                    
                # 設定為HIGH（持續）
                if self.arduino:
                    print(f"Setting SSR1 Pin {self.config.ssr1_pin} to HIGH (持續)")
                    self.arduino.set_pin_state(self.config.ssr1_pin, 'HIGH', 0)
                    self.status_changed.emit(f"SSR1 Pin {self.config.ssr1_pin} -> HIGH (持續)")
                else:
                    print("Warning: Arduino controller not available for SSR1")
                
                self.ssr1_processed = True
                self.ssr1_ready.emit()
                
            # 檢查SSR2
            if self.ssr2_active and not self.ssr2_processed:
                print(f"Processing SSR2: Pin {self.config.ssr2_pin}")
                # 等待前延遲
                if self.config.ssr2_delay_before > 0:
                    self.status_changed.emit(f"SSR2等待前延遲 {self.config.ssr2_delay_before}ms")
                    self.msleep(self.config.ssr2_delay_before)
                    
                # 設定為HIGH（持續）
                if self.arduino:
                    print(f"Setting SSR2 Pin {self.config.ssr2_pin} to HIGH (持續)")
                    self.arduino.set_pin_state(self.config.ssr2_pin, 'HIGH', 0)
                    self.status_changed.emit(f"SSR2 Pin {self.config.ssr2_pin} -> HIGH (持續)")
                else:
                    print("Warning: Arduino controller not available for SSR2")
                    
                self.ssr2_processed = True
                self.ssr2_ready.emit()
                
            # 短暫休眠，避免過度佔用CPU
            self.msleep(50)
            
        # 線程正常結束，不自動關閉SSR（由stop_all_lighting明確控制）
        print("SSR thread ending, SSR states maintained until explicit stop")


class SSRController(QObject):
    """SSR控制器主類"""
    
    status_changed = pyqtSignal(str)
    spotlight_ready = pyqtSignal()  # 聚光燈準備完成
    caption_lighting_ready = pyqtSignal()  # 字幕燈光準備完成
    
    def __init__(self, arduino_controller=None):
        super().__init__()
        self.arduino = arduino_controller
        self.config = SSRConfig()
        self.ssr_thread = None
        
    def start_caption_lighting(self):
        """開始字幕燈光（SSR1）"""
        print(f"Starting caption lighting: SSR1 Pin {self.config.ssr1_pin}")
        
        if self.ssr_thread and self.ssr_thread.isRunning():
            print("SSR thread already running, activating SSR1 on existing thread")
            # 線程已運行，直接啟動SSR1
            self.ssr_thread.activate_ssr1()
            self.status_changed.emit("字幕燈光已啟動（現有線程）")
            return
            
        # 創建新線程
        print("Creating new SSR thread for caption lighting")
        self.ssr_thread = SSRThread(self.arduino, self.config)
        self.ssr_thread.status_changed.connect(self.on_status_changed)
        self.ssr_thread.ssr1_ready.connect(self.on_ssr1_ready)  # 連接SSR1完成信號
        self.ssr_thread.ssr2_ready.connect(self.on_ssr2_ready)
        
        self.ssr_thread.activate_ssr1()
        self.ssr_thread.start()
        
        self.status_changed.emit("字幕燈光已啟動")
        
    def start_spotlight(self):
        """開始聚光燈（SSR2）"""
        print(f"Starting spotlight: SSR2 Pin {self.config.ssr2_pin}")
        if self.ssr_thread and self.ssr_thread.isRunning():
            print("SSR thread running, activating SSR2")
            self.ssr_thread.activate_ssr2()
            self.status_changed.emit("聚光燈已啟動")
        else:
            # 如果線程還沒啟動，創建新線程
            print("Creating new SSR thread for spotlight")
            self.ssr_thread = SSRThread(self.arduino, self.config)
            self.ssr_thread.status_changed.connect(self.on_status_changed)
            self.ssr_thread.ssr1_ready.connect(self.on_ssr1_ready)
            self.ssr_thread.ssr2_ready.connect(self.on_ssr2_ready)
            
            self.ssr_thread.activate_ssr2()
            self.ssr_thread.start()
            
    def stop_all_lighting(self):
        """停止所有燈光"""
        print("Stopping all SSR lighting")
        
        # 直接控制Arduino，立即關閉所有SSR
        if self.arduino:
            # 同時關閉SSR1和SSR2
            if hasattr(self, 'ssr_thread') and self.ssr_thread:
                if self.ssr_thread.ssr1_processed:
                    print(f"Setting SSR1 Pin {self.config.ssr1_pin} to LOW")
                    self.arduino.set_pin_state(self.config.ssr1_pin, 'LOW', 0)
                    self.status_changed.emit(f"SSR1 Pin {self.config.ssr1_pin} -> LOW")
                
                if self.ssr_thread.ssr2_processed:
                    print(f"Setting SSR2 Pin {self.config.ssr2_pin} to LOW")
                    self.arduino.set_pin_state(self.config.ssr2_pin, 'LOW', 0)
                    self.status_changed.emit(f"SSR2 Pin {self.config.ssr2_pin} -> LOW")
        
        # 停止線程
        if self.ssr_thread and self.ssr_thread.isRunning():
            self.ssr_thread.should_stop = True
            self.ssr_thread.wait(1000)  # 等待最多1秒
            
        self.status_changed.emit("所有燈光已關閉")
        
    def on_status_changed(self, status):
        """狀態變更處理"""
        self.status_changed.emit(status)
        
    def on_ssr1_ready(self):
        """SSR1準備完成"""
        print("SSR1 (字幕燈光) 已啟動")
        self.caption_lighting_ready.emit()
        
    def on_ssr2_ready(self):
        """SSR2準備完成"""
        print("SSR2 (聚光燈) 已啟動") 
        self.spotlight_ready.emit()
        
    def cleanup(self):
        """清理資源"""
        if self.ssr_thread and self.ssr_thread.isRunning():
            self.ssr_thread.deactivate_all()
            self.ssr_thread.wait(2000)
            
    def reload_config(self):
        """重新載入配置"""
        self.config.load_config()

    def get_ssr_status(self):
        """獲取當前SSR狀態（用於調試）"""
        status = {
            'thread_running': self.ssr_thread and self.ssr_thread.isRunning(),
            'ssr1_active': False,
            'ssr2_active': False,
            'ssr1_processed': False,
            'ssr2_processed': False
        }
        
        if self.ssr_thread:
            status['ssr1_active'] = self.ssr_thread.ssr1_active
            status['ssr2_active'] = self.ssr_thread.ssr2_active
            status['ssr1_processed'] = self.ssr_thread.ssr1_processed
            status['ssr2_processed'] = self.ssr_thread.ssr2_processed
            
        return status
        
    def print_debug_status(self):
        """列印調試狀態"""
        status = self.get_ssr_status()
        print("=== SSR Debug Status ===")
        print(f"SSR1 Pin: {self.config.ssr1_pin}")
        print(f"SSR2 Pin: {self.config.ssr2_pin}")
        print(f"Thread Running: {status['thread_running']}")
        print(f"SSR1 Active: {status['ssr1_active']}, Processed: {status['ssr1_processed']}")
        print(f"SSR2 Active: {status['ssr2_active']}, Processed: {status['ssr2_processed']}")
        print("========================")