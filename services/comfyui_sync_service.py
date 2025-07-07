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
                if self.ws:
                    self.ws.run_forever()
            
            ws_thread = threading.Thread(target=run_ws, daemon=True)
            ws_thread.start()
            
        except Exception as e:
            print(f"WebSocket連接失敗: {e}")
    
    def _on_websocket_message(self, ws, message):
        """處理WebSocket消息"""
        try:
            data = json.loads(message)
            if data.get("type") == "executing":
                # 節點正在執行，獲取當前工作流程配置
                self._sync_current_workflow()
            elif data.get("type") == "executed":
                # 節點執行完成，同步配置
                self._sync_current_workflow()
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
    
    def _sync_current_workflow(self):
        """同步當前工作流程的配置"""
        try:
            # 獲取當前活動的工作流程
            response = requests.get(f"{self.comfyui_url}/api/prompt", timeout=2)
            if response.status_code == 200:
                prompt_data = response.json()
                
                # 檢查是否有執行中或最近的提示
                if prompt_data.get("exec_info", {}).get("queue_remaining") == 0:
                    # 獲取歷史記錄中最新的配置
                    self._get_latest_config_from_history()
            
        except Exception as e:
            print(f"同步工作流程配置錯誤: {e}")
    
    def _get_latest_config_from_history(self):
        """從歷史記錄中獲取最新配置"""
        try:
            response = requests.get(f"{self.comfyui_url}/history", timeout=2)
            if response.status_code == 200:
                history = response.json()
                
                # 獲取最新的執行記錄
                for prompt_id, prompt_info in history.items():
                    workflow = prompt_info.get("prompt", {})
                    if workflow:
                        config = self._extract_tts_config_from_workflow(workflow)
                        if config:
                            self._update_voice_config(config)
                        break  # 只處理最新的
                        
        except Exception as e:
            print(f"獲取歷史配置錯誤: {e}")
    
    def _extract_tts_config_from_workflow(self, workflow):
        """從工作流程中提取 TTS 配置"""
        config = {}
        
        try:
            for node_id, node_data in workflow.items():
                class_type = node_data.get("class_type", "")
                inputs = node_data.get("inputs", {})
                
                # 處理 GeekyKokoroTTS 節點
                if class_type == "GeekyKokoroTTS":
                    if "voice" in inputs:
                        config["voice_model"] = inputs["voice"]
                    if "speed" in inputs:
                        config["speed"] = float(inputs["speed"])
                    if "enable_blending" in inputs:
                        config["enable_blending"] = bool(inputs["enable_blending"])
                
                # 處理 GeekyKokoroAdvancedVoice 節點
                elif class_type == "GeekyKokoroAdvancedVoice":
                    # 映射 ComfyUI 參數到配置文件參數
                    param_mapping = {
                        "effect_blend": "effect_blend",
                        "output_volume": "output_volume", 
                        "voice_profile": "voice_profile",
                        "profile_intensity": "profile_intensity",
                        "manual_mode": "manual_mode",
                        "pitch_shift": "pitch_shift",
                        "formant_shift": "formant_shift",
                        "reverb_amount": "reverb_amount",
                        "echo_delay": "echo_delay",
                        "distortion": "distortion",
                        "compression": "compression",
                        "eq_bass": "eq_bass",
                        "eq_mid": "eq_mid",
                        "eq_treble": "eq_treble",
                        "use_gpu": "use_gpu"
                    }
                    
                    for comfy_param, config_param in param_mapping.items():
                        if comfy_param in inputs:
                            value = inputs[comfy_param]
                            # 類型轉換
                            if isinstance(value, (int, float)):
                                config[config_param] = float(value)
                            elif isinstance(value, bool):
                                config[config_param] = value
                            elif isinstance(value, str):
                                config[config_param] = value
            
            return config if config else None
            
        except Exception as e:
            print(f"提取TTS配置錯誤: {e}")
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
            
            print(f"✅ 配置已同步: {len(new_config)} 個參數")
            
        except Exception as e:
            print(f"更新語音配置錯誤: {e}")
    
    def _save_comfyui_config(self, config):
        """保存到ComfyUI配置文件"""
        try:
            config_data = {
                "timestamp": time.time(),
                "config": config
            }
            
            with open(self.comfyui_config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"保存ComfyUI配置錯誤: {e}")
    
    def _update_main_config(self, config):
        """更新主配置文件"""
        try:
            # 讀取現有配置
            current_config = self._read_main_config()
            
            # 更新配置
            current_config.update(config)
            
            # 寫回配置文件
            self._write_main_config(current_config)
            
            print(f"📝 主配置文件已更新")
            
        except Exception as e:
            print(f"更新主配置錯誤: {e}")
    
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
            print(f"讀取主配置錯誤: {e}")
            
        return config
    
    def _write_main_config(self, config):
        """寫入主配置文件"""
        try:
            # 確保目錄存在
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                f.write("# 語音修改配置檔案\n")
                
                for key, value in config.items():
                    if isinstance(value, bool):
                        f.write(f"{key}={str(value)}\n")
                    elif isinstance(value, (int, float)):
                        f.write(f"{key}={value}\n")
                    else:
                        f.write(f"{key}={value}\n")
                        
        except Exception as e:
            print(f"寫入主配置錯誤: {e}")
    
    def _parse_config_value(self, value):
        """解析配置值"""
        try:
            # 布爾值
            if value.lower() in ('true', 'false'):
                return value.lower() == 'true'
            # 浮點數
            elif '.' in value:
                return float(value)
            # 整數
            elif value.isdigit() or (value.startswith('-') and value[1:].isdigit()):
                return int(value)
            # 字符串
            else:
                return value
        except:
            return value
    
    def get_current_config(self):
        """獲取當前配置"""
        return self.last_known_config.copy()
    
    def is_comfyui_connected(self):
        """檢查ComfyUI是否連接"""
        return self.is_connected
    
    def manually_sync_config(self, config):
        """手動同步配置"""
        self._update_voice_config(config)
    
    def get_comfyui_url(self):
        """獲取ComfyUI URL"""
        return self.comfyui_url 