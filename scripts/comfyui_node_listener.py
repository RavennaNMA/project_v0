#!/usr/bin/env python3
# Location: project_v2/comfyui_node_listener.py
# Usage: ComfyUI節點參數監聽器，自動同步語音修改設定

import json
import time
import requests
import websocket
import threading
from pathlib import Path

class ComfyUINodeListener:
    """ComfyUI節點監聽器"""
    
    def __init__(self, comfyui_host="127.0.0.1", comfyui_port=8188):
        self.comfyui_host = comfyui_host
        self.comfyui_port = comfyui_port
        self.comfyui_url = f"http://{comfyui_host}:{comfyui_port}"
        self.ws_url = f"ws://{comfyui_host}:{comfyui_port}/ws"
        
        self.config_path = Path("../config/voice_mod_config.txt")
        self.ws = None
        self.running = False
        self.last_prompt_id = None
        
        print("🎛️ ComfyUI節點監聽器已初始化")
        
    def start_listening(self):
        """開始監聽ComfyUI節點變化"""
        self.running = True
        print("🔄 正在嘗試連接到ComfyUI...")
        
        # 檢查ComfyUI連接
        if not self._check_comfyui_connection():
            print("❌ 無法連接到ComfyUI，請確保ComfyUI正在運行：http://127.0.0.1:8188")
            return False
            
        # 連接WebSocket
        try:
            self.ws = websocket.WebSocketApp(
                f"{self.ws_url}?clientId=node_listener",
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close,
                on_open=self._on_open
            )
            
            # 在新線程中運行WebSocket
            ws_thread = threading.Thread(target=self.ws.run_forever, daemon=True)
            ws_thread.start()
            
            print("✅ ComfyUI節點監聽器已啟動，正在等待節點參數變化...")
            return True
            
        except Exception as e:
            print(f"❌ 啟動監聽器失敗: {e}")
            return False
            
    def stop_listening(self):
        """停止監聽"""
        self.running = False
        if self.ws:
            self.ws.close()
        print("⏹️ ComfyUI節點監聽器已停止")
        
    def _check_comfyui_connection(self):
        """檢查ComfyUI連接"""
        try:
            response = requests.get(f"{self.comfyui_url}/history", timeout=5)
            return response.status_code == 200
        except:
            return False
            
    def _on_open(self, ws):
        """WebSocket連接成功"""
        print("🔗 已連接到ComfyUI WebSocket")
        
    def _on_message(self, ws, message):
        """處理WebSocket消息"""
        try:
            data = json.loads(message)
            
            # 檢查是否是執行相關的消息
            if data.get("type") == "execution_start":
                execution_data = data.get("data", {})
                self.last_prompt_id = execution_data.get("prompt_id")
                print(f"🎬 工作流開始執行 (ID: {self.last_prompt_id})")
                
            elif data.get("type") == "executed":
                # 節點執行完成，檢查是否是語音修改節點
                node_data = data.get("data", {})
                self._check_voice_mod_node(node_data)
                
            elif data.get("type") == "execution_cached":
                # 從緩存執行，也檢查節點
                node_data = data.get("data", {})
                self._check_voice_mod_node(node_data)
                
        except Exception as e:
            print(f"❌ 處理消息錯誤: {e}")
            
    def _check_voice_mod_node(self, node_data):
        """檢查是否是語音修改節點並提取參數"""
        try:
            node_id = node_data.get("node")
            if not node_id:
                return
                
            # 獲取當前工作流以檢查節點類型
            if self.last_prompt_id:
                workflow_data = self._get_workflow_data()
                if workflow_data:
                    node_info = workflow_data.get(str(node_id))
                    if node_info and self._is_voice_mod_node(node_info):
                        self._extract_and_sync_parameters(node_info)
                        
        except Exception as e:
            print(f"❌ 檢查語音修改節點錯誤: {e}")
            
    def _get_workflow_data(self):
        """獲取當前工作流數據"""
        try:
            # 嘗試從歷史記錄獲取最新的prompt
            response = requests.get(f"{self.comfyui_url}/history", timeout=5)
            if response.status_code == 200:
                history = response.json()
                if self.last_prompt_id and self.last_prompt_id in history:
                    prompt_data = history[self.last_prompt_id]
                    return prompt_data.get("prompt", {})
            return None
        except Exception as e:
            print(f"❌ 獲取工作流數據錯誤: {e}")
            return None
            
    def _is_voice_mod_node(self, node_info):
        """判斷是否是語音修改節點"""
        node_type = node_info.get("class_type", "")
        return "Voice Mod" in node_type or "Geeky Kokoro" in node_type
        
    def _extract_and_sync_parameters(self, node_info):
        """提取並同步語音修改參數"""
        try:
            inputs = node_info.get("inputs", {})
            
            # 參數映射 (根據實際的Geeky Kokoro Voice Mod節點參數)
            config = {}
            
            # 提取各種參數
            if "pitch_shift" in inputs:
                config["pitch_shift"] = float(inputs["pitch_shift"])
            if "formant_shift" in inputs:
                config["formant_shift"] = float(inputs["formant_shift"])
            if "reverb_amount" in inputs:
                config["reverb_amount"] = float(inputs["reverb_amount"])
            if "echo_delay" in inputs:
                config["echo_delay"] = float(inputs["echo_delay"])
            if "compression" in inputs:
                config["compression"] = float(inputs["compression"])
            if "effect_blend" in inputs:
                config["effect_blend"] = float(inputs["effect_blend"])
            if "output_volume" in inputs:
                config["output_volume"] = float(inputs["output_volume"])
                
            # 如果提取到了參數，則同步
            if config:
                self._sync_to_main_project(config)
                
        except Exception as e:
            print(f"❌ 提取參數錯誤: {e}")
            
    def _sync_to_main_project(self, config):
        """同步配置到主項目"""
        try:
            # 讀取當前配置
            current_config = self._read_config()
            
            # 更新配置
            current_config.update(config)
            current_config["voice_mod_enabled"] = True
            current_config["manual_mode"] = True
            
            # 寫入配置文件
            self._write_config(current_config)
            
            print(f"✅ 已同步語音參數到主項目: {config}")
            
        except Exception as e:
            print(f"❌ 同步配置錯誤: {e}")
            
    def _read_config(self):
        """讀取配置文件"""
        config = {}
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            config[key.strip()] = self._parse_value(value.strip())
        except Exception as e:
            print(f"❌ 讀取配置錯誤: {e}")
        return config
        
    def _write_config(self, config):
        """寫入配置文件"""
        try:
            lines = []
            lines.append("# 語音修改配置檔案 (由ComfyUI節點自動同步)")
            lines.append(f"# 最後更新時間: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            for key, value in config.items():
                lines.append(f"{key}={value}")
                
            with open(self.config_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines) + '\n')
                
        except Exception as e:
            print(f"❌ 寫入配置錯誤: {e}")
            
    def _parse_value(self, value):
        """解析配置值"""
        if value.lower() in ['true', 'false']:
            return value.lower() == 'true'
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            return value
            
    def _on_error(self, ws, error):
        """WebSocket錯誤處理"""
        print(f"❌ WebSocket錯誤: {error}")
        
    def _on_close(self, ws, close_status_code, close_msg):
        """WebSocket關閉處理"""
        print("❌ WebSocket連接已關閉")
        if self.running:
            print("🔄 3秒後嘗試重新連接...")
            time.sleep(3)
            if self.running:
                self.start_listening()


def main():
    """主函數"""
    print("🎵 ComfyUI語音節點監聽器")
    print("=" * 50)
    
    listener = ComfyUINodeListener()
    
    try:
        if listener.start_listening():
            print("\n📋 使用說明:")
            print("1. 在ComfyUI中添加 'Geeky Kokoro Voice Mod' 節點")
            print("2. 調整節點的語音參數")
            print("3. 執行工作流 (Queue Prompt)")
            print("4. 參數會自動同步到您的主項目")
            print("\n按 Ctrl+C 停止監聽...")
            
            # 保持運行
            while listener.running:
                time.sleep(1)
        else:
            print("❌ 監聽器啟動失敗")
            
    except KeyboardInterrupt:
        print("\n👋 用戶中斷，正在停止監聽器...")
    except Exception as e:
        print(f"❌ 運行錯誤: {e}")
    finally:
        listener.stop_listening()
        

if __name__ == "__main__":
    main() 