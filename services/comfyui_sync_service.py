# Location: project_v2/services/comfyui_sync_service.py
# Usage: ComfyUI配置同步服務，監聽並同步語音修改參數

import json
import os
import time
import threading
import requests
from pathlib import Path
from typing import Dict, Optional, Callable
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
import websocket

class ComfyUISyncService(QObject):
    """ComfyUI配置同步服務"""
    
    # 信號定義
    config_updated = pyqtSignal(dict)  # 配置更新信號
    connection_status_changed = pyqtSignal(bool)  # 連接狀態變化
    
    def __init__(self, comfyui_host="127.0.0.1", comfyui_port=8188):
        super().__init__()
        self.comfyui_host = comfyui_host
        self.comfyui_port = comfyui_port
        self.comfyui_url = f"http://{comfyui_host}:{comfyui_port}"
        self.ws_url = f"ws://{comfyui_host}:{comfyui_port}/ws"
        
        # 配置文件路徑
        self.config_path = Path("config/voice_mod_config.txt")
        self.comfyui_config_path = Path("comfyui_voice_config.json")
        
        # 狀態管理
        self.is_connected = False
        self.ws = None
        self.sync_enabled = True
        self.last_known_config = {}
        
        # 定時器用於定期檢查連接
        self.connection_timer = QTimer()
        self.connection_timer.timeout.connect(self._check_connection)
        self.connection_timer.start(5000)  # 每5秒檢查一次
        
        print("ComfyUI同步服務已初始化")
    
    def start_sync(self):
        """開始同步服務"""
        self.sync_enabled = True
        self._try_connect_websocket()
        print("✅ ComfyUI同步服務已啟動")
    
    def stop_sync(self):
        """停止同步服務"""
        self.sync_enabled = False
        if self.ws:
            self.ws.close()
        print("⏹️ ComfyUI同步服務已停止")
    
    def _check_connection(self):
        """檢查ComfyUI連接狀態"""
        try:
            response = requests.get(f"{self.comfyui_url}/history", timeout=2)
            if response.status_code == 200:
                if not self.is_connected:
                    self.is_connected = True
                    self.connection_status_changed.emit(True)
                    print("🔗 ComfyUI連接已建立")
                    if self.sync_enabled and not self.ws:
                        self._try_connect_websocket()
            else:
                self._handle_disconnect()
        except:
            self._handle_disconnect()
    
    def _handle_disconnect(self):
        """處理連接斷開"""
        if self.is_connected:
            self.is_connected = False
            self.connection_status_changed.emit(False)
            print("❌ ComfyUI連接已斷開")
        if self.ws:
            self.ws = None
    
    def _try_connect_websocket(self):
        """嘗試連接WebSocket"""
        if not self.sync_enabled or self.ws:
            return
        
        try:
            self.ws = websocket.WebSocketApp(
                f"{self.ws_url}?clientId=voice_mod_sync",
                on_message=self._on_websocket_message,
                on_error=self._on_websocket_error,
                on_close=self._on_websocket_close
            )
            
            # 在新線程中運行WebSocket
            def run_ws():
                self.ws.run_forever()
            
            ws_thread = threading.Thread(target=run_ws, daemon=True)
            ws_thread.start()
            
        except Exception as e:
            print(f"WebSocket連接失敗: {e}")
    
    def _on_websocket_message(self, ws, message):
        """處理WebSocket消息"""
        try:
            data = json.loads(message)
            if data.get("type") == "execution_start":
                # 工作流開始執行
                pass
            elif data.get("type") == "executing":
                # 節點正在執行
                node_id = data.get("data", {}).get("node")
                if node_id:
                    self._check_node_config(node_id)
            elif data.get("type") == "executed":
                # 節點執行完成
                node_data = data.get("data", {})
                if node_data:
                    self._process_node_output(node_data)
        except Exception as e:
            print(f"處理WebSocket消息錯誤: {e}")
    
    def _on_websocket_error(self, ws, error):
        """WebSocket錯誤處理"""
        print(f"WebSocket錯誤: {error}")
    
    def _on_websocket_close(self, ws, close_status_code, close_msg):
        """WebSocket關閉處理"""
        print("WebSocket連接已關閉")
        self.ws = None
        # 如果服務仍啟用，嘗試重連
        if self.sync_enabled:
            QTimer.singleShot(3000, self._try_connect_websocket)
    
    def _check_node_config(self, node_id):
        """檢查特定節點的配置"""
        try:
            # 獲取當前工作流
            response = requests.get(f"{self.comfyui_url}/prompt", timeout=2)
            if response.status_code == 200:
                # 這裡可以解析工作流來提取語音修改節點的參數
                pass
        except Exception as e:
            print(f"檢查節點配置錯誤: {e}")
    
    def _process_node_output(self, node_data):
        """處理節點輸出數據"""
        try:
            node_id = node_data.get("node")
            output = node_data.get("output", {})
            
            # 檢查是否是語音修改節點
            if self._is_voice_mod_node(output):
                config = self._extract_voice_config(output)
                if config:
                    self._update_voice_config(config)
        except Exception as e:
            print(f"處理節點輸出錯誤: {e}")
    
    def _is_voice_mod_node(self, output):
        """判斷是否是語音修改節點"""
        # 檢查輸出是否包含語音修改相關的鍵
        voice_keys = ['pitch_shift', 'formant_shift', 'reverb_amount', 'voice_profile']
        return any(key in str(output) for key in voice_keys)
    
    def _extract_voice_config(self, output):
        """從節點輸出中提取語音配置"""
        config = {}
        try:
            # 這裡需要根據實際的節點輸出格式來解析
            # ComfyUI的語音修改節點可能會在輸出中包含參數信息
            if isinstance(output, dict):
                # 提取語音修改參數
                for key in ['pitch_shift', 'formant_shift', 'reverb_amount', 
                           'echo_delay', 'compression', 'effect_blend', 
                           'output_volume', 'voice_profile', 'profile_intensity']:
                    if key in output:
                        config[key] = output[key]
            
            return config if config else None
        except Exception as e:
            print(f"提取語音配置錯誤: {e}")
            return None
    
    def _update_voice_config(self, new_config):
        """更新語音配置"""
        try:
            # 更新內存中的配置
            self.last_known_config.update(new_config)
            
            # 保存到ComfyUI配置文件
            self._save_comfyui_config(new_config)
            
            # 更新主配置文件
            self._update_main_config(new_config)
            
            # 發射配置更新信號
            self.config_updated.emit(new_config)
            
            print(f"✅ 語音配置已更新: {new_config}")
            
        except Exception as e:
            print(f"更新語音配置錯誤: {e}")
    
    def _save_comfyui_config(self, config):
        """保存ComfyUI配置到JSON文件"""
        try:
            with open(self.comfyui_config_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'timestamp': time.time(),
                    'config': config
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存ComfyUI配置錯誤: {e}")
    
    def _update_main_config(self, config):
        """更新主配置文件"""
        try:
            # 讀取當前配置
            current_config = self._read_main_config()
            
            # 更新配置
            for key, value in config.items():
                current_config[key] = value
            
            # 寫回配置文件
            self._write_main_config(current_config)
            
        except Exception as e:
            print(f"更新主配置文件錯誤: {e}")
    
    def _read_main_config(self):
        """讀取主配置文件"""
        config = {}
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            config[key.strip()] = self._parse_config_value(value.strip())
        except Exception as e:
            print(f"讀取主配置文件錯誤: {e}")
        return config
    
    def _write_main_config(self, config):
        """寫入主配置文件"""
        try:
            lines = []
            lines.append("# 語音修改配置檔案 (由ComfyUI同步更新)")
            lines.append(f"# 最後更新時間: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            for key, value in config.items():
                lines.append(f"{key}={value}")
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines) + '\n')
                
        except Exception as e:
            print(f"寫入主配置文件錯誤: {e}")
    
    def _parse_config_value(self, value):
        """解析配置值"""
        # 嘗試轉換為合適的類型
        if value.lower() in ['true', 'false']:
            return value.lower() == 'true'
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            return value
    
    def get_current_config(self):
        """獲取當前配置"""
        return self.last_known_config.copy()
    
    def is_comfyui_connected(self):
        """檢查ComfyUI是否已連接"""
        return self.is_connected
    
    def manually_sync_config(self, config):
        """手動同步配置（用於測試）"""
        self._update_voice_config(config)
    
    def get_comfyui_url(self):
        """獲取ComfyUI URL"""
        return self.comfyui_url 