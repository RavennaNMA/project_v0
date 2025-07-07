# Location: project_v2/core/arduino_controller.py
# Usage: Arduino 控制器，用於控制硬體設備

import serial
import serial.tools.list_ports
import time
import platform
from PyQt6.QtCore import QThread, QObject, pyqtSignal


class ArduinoThread(QThread):
    """Arduino 控制執行緒"""
    status_changed = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    pin_state_changed = pyqtSignal(int, str)  # pin, state
    
    def __init__(self, port, baudrate=9600):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None
        self.is_running = False
        self.command_queue = []
        
    def run(self):
        """執行緒主迴圈"""
        try:
            self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=1)
            self.status_changed.emit(f"已連接到 {self.port}")
            
            self.is_running = True
            
            # 初始化所有腳位為 LOW
            self._init_pins()
            
            while self.is_running:
                if self.command_queue:
                    cmd = self.command_queue.pop(0)
                    
                    # 檢查指令類型
                    if cmd.get('type') == 'pin_state':
                        self._execute_pin_state_command(cmd)
                    else:
                        self._execute_command(cmd)
                    
                self.msleep(10)
                
        except Exception as e:
            self.error_occurred.emit(f"Arduino 錯誤: {str(e)}")
        finally:
            if self.serial_conn and self.serial_conn.is_open:
                self.serial_conn.close()
                
    def _init_pins(self):
        """初始化所有腳位"""
        for pin in range(2, 14):  # 數位腳位 2-13
            self._send_command(f"L{pin}")
            time.sleep(0.01)
            
    def _send_command(self, command):
        """發送指令到 Arduino"""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.write(f"{command}\n".encode())
            self.serial_conn.flush()
            
    def _execute_command(self, cmd):
        """執行腳位控制指令"""
        pin = cmd['pin']
        wait_before = cmd.get('wait_before', 0)
        high_time = cmd.get('high_time', 1000)
        wait_after = cmd.get('wait_after', 0)
        
        # 前延遲
        if wait_before > 0:
            time.sleep(wait_before / 1000.0)
            
        # 設為 HIGH
        self._send_command(f"H{pin}")
        self.status_changed.emit(f"Pin {pin} -> HIGH")
        self.pin_state_changed.emit(pin, "HIGH")
        
        # 維持 HIGH
        time.sleep(high_time / 1000.0)
        
        # 設回 LOW
        self._send_command(f"L{pin}")
        self.status_changed.emit(f"Pin {pin} -> LOW")
        self.pin_state_changed.emit(pin, "LOW")
        
        # 後延遲
        if wait_after > 0:
            time.sleep(wait_after / 1000.0)
            
    def add_command(self, pin, wait_before=0, high_time=1000, wait_after=0):
        """新增控制指令"""
        self.command_queue.append({
            'pin': pin,
            'wait_before': wait_before,
            'high_time': high_time,
            'wait_after': wait_after
        })
        
    def add_pin_state_command(self, pin, state, wait_before=0):
        """新增Pin狀態控制指令（不自動切換）"""
        self.command_queue.append({
            'type': 'pin_state',
            'pin': pin,
            'state': state,  # 'HIGH' or 'LOW'
            'wait_before': wait_before
        })
        
    def _execute_pin_state_command(self, cmd):
        """執行Pin狀態控制指令"""
        pin = cmd['pin']
        state = cmd['state']
        wait_before = cmd.get('wait_before', 0)
        
        # 前延遲
        if wait_before > 0:
            time.sleep(wait_before / 1000.0)
            
        # 直接設置Pin狀態
        if state == 'HIGH':
            self._send_command(f"H{pin}")
            self.status_changed.emit(f"Pin {pin} -> HIGH (持續)")
            self.pin_state_changed.emit(pin, "HIGH")
        elif state == 'LOW':
            self._send_command(f"L{pin}")
            self.status_changed.emit(f"Pin {pin} -> LOW")
            self.pin_state_changed.emit(pin, "LOW")
        
    def stop(self):
        """停止執行緒"""
        self.is_running = False
        self.wait()


class ArduinoController(QObject):
    """Arduino 控制器"""
    status_changed = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.arduino_thread = None
        self.is_connected = False
        self.current_port = None
        self.pin_states = {}  # 追蹤pin狀態
        
        # 初始化所有pin為LOW
        for pin in range(2, 14):
            self.pin_states[pin] = "LOW"
        
    def connect(self, port):
        """連接 Arduino"""
        if self.arduino_thread and self.arduino_thread.isRunning():
            self.disconnect()
            
        self.arduino_thread = ArduinoThread(port)
        self.arduino_thread.status_changed.connect(self._on_status_changed)
        self.arduino_thread.error_occurred.connect(self._on_error)
        self.arduino_thread.pin_state_changed.connect(self.update_pin_state)
        self.arduino_thread.start()
        
        self.current_port = port
        self.is_connected = True
        
    def disconnect(self):
        """斷開連接"""
        if self.arduino_thread:
            self.arduino_thread.stop()
            self.arduino_thread = None
            
        self.is_connected = False
        self.current_port = None
        self.status_changed.emit("已斷開連接")
        
    def _on_status_changed(self, status):
        """處理狀態變更"""
        self.status_changed.emit(status)
        
    def _on_error(self, error):
        """處理錯誤"""
        self.error_occurred.emit(error)
        self.is_connected = False
        
    def control_pin(self, pin, wait_before=0, high_time=1000, wait_after=0):
        """控制腳位"""
        if not self.is_connected or not self.arduino_thread:
            self.error_occurred.emit("Arduino 未連接")
            return
            
        self.arduino_thread.add_command(pin, wait_before, high_time, wait_after)
        
    def set_pin_state(self, pin, state, wait_before=0):
        """直接設置Pin狀態（不自動切換）"""
        if not self.is_connected or not self.arduino_thread:
            self.error_occurred.emit("Arduino 未連接")
            return
            
        print(f"Setting Pin {pin} to {state} via direct command")
        self.arduino_thread.add_pin_state_command(pin, state, wait_before)
        
    def get_pin_state(self, pin):
        """獲取pin狀態"""
        return self.pin_states.get(pin, "LOW")
        
    def update_pin_state(self, pin, state):
        """更新pin狀態"""
        self.pin_states[pin] = state
        
    @staticmethod
    def get_available_ports():
        """取得可用的串口列表"""
        ports = []
        system = platform.system()
        
        for port in serial.tools.list_ports.comports():
            # 根據系統過濾串口
            if system == "Darwin":  # macOS
                if "usb" in port.device.lower() or "cu." in port.device:
                    ports.append((port.device, port.description))
            elif system == "Windows":
                if "COM" in port.device:
                    ports.append((port.device, port.description))
            else:  # Linux
                if "ttyUSB" in port.device or "ttyACM" in port.device:
                    ports.append((port.device, port.description))
                    
        return ports 