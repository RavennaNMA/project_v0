#!/usr/bin/env python3
"""
ComfyUI 配置同步工具
監聽 ComfyUI 的輸出並同步配置到主程序
"""
import json
import time
import threading
import webbrowser
import sys
import os
from pathlib import Path

# 添加項目根目錄到路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from services.comfyui_sync_service import ComfyUISyncService
except ImportError as e:
    print(f"❌ 無法導入同步服務: {e}")
    print("請確保在項目根目錄中運行此腳本")
    sys.exit(1)

def open_comfyui_with_workflow():
    """在瀏覽器中打開 ComfyUI 並載入工作流程"""
    workflow_path = Path("ComfyUI/workflows/tts_studio.json")
    if workflow_path.exists():
        # 使用文件 URL 方式載入工作流程
        comfyui_url = "http://127.0.0.1:8188"
        print(f"🌐 正在瀏覽器中打開 ComfyUI: {comfyui_url}")
        webbrowser.open(comfyui_url)
        time.sleep(3)  # 等待 ComfyUI 完全載入
        print("📋 請在 ComfyUI 中載入工作流程：")
        print(f"    1. 點擊 'Load' 按鈕")
        print(f"    2. 選擇：{workflow_path.absolute()}")
        print("    3. 或直接將 JSON 文件拖拽到 ComfyUI 介面中")
    else:
        print("❌ 找不到工作流程文件")

def monitor_config_changes(sync_service):
    """監控配置變化"""
    def on_config_updated(config):
        print(f"🔄 配置已更新: {', '.join(config.keys())}")
        
    def on_connection_changed(connected):
        if connected:
            print("✅ 已連接到 ComfyUI")
        else:
            print("❌ 與 ComfyUI 斷開連接")
    
    # 連接信號
    sync_service.config_updated.connect(on_config_updated)
    sync_service.connection_status_changed.connect(on_connection_changed)

def main():
    print("🔄 ComfyUI 配置同步服務")
    print("=" * 40)
    
    try:
        # 啟動同步服務
        sync_service = ComfyUISyncService()
        
        # 監控配置變化
        monitor_config_changes(sync_service)
        
        # 啟動同步
        sync_service.start_sync()
        
        # 等待 ComfyUI 啟動
        print("⏳ 等待 ComfyUI 服務...")
        time.sleep(5)
        
        # 檢查連接
        if sync_service.is_comfyui_connected():
            print("✅ ComfyUI 服務器連接成功")
            open_comfyui_with_workflow()
        else:
            print("⚠️  ComfyUI 服務器未響應，將繼續嘗試連接...")
        
        print("\n📋 TTS Studio 使用說明：")
        print("1. 在 ComfyUI 中載入 tts_studio.json 工作流程")
        print("2. 調整 'GeekyKokoroTTS' 節點的文字和語音模型")
        print("3. 調整 'GeekyKokoroAdvancedVoice' 節點的音效參數")
        print("4. 點擊 'Queue Prompt' 執行並生成語音")
        print("5. 配置會自動同步到 config/voice_mod_config.txt")
        print("6. 主程序會自動使用最新的語音設定")
        
        print("\n🔍 配置監控中...")
        print("   • 語音模型選擇")
        print("   • 語音修改參數 (音調、混響、壓縮等)")
        print("   • 音效混合設定")
        
        print("\n按 Ctrl+C 停止同步服務...")
        
        # 保持服務運行
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 正在停止同步服務...")
            sync_service.stop_sync()
            
    except Exception as e:
        print(f"❌ 同步服務出錯: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
