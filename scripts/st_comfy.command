#!/bin/bash
# Location: project_v2/scripts/st_comfy.command
# Usage: ComfyUI + Geeky Kokoro TTS 啟動腳本（Mac 版）

# 取得腳本所在目錄並移動到項目根目錄
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$DIR")"
cd "$PROJECT_ROOT"

echo "🎨 ================================"
echo "🎵 ComfyUI + Geeky Kokoro TTS 工作室"
echo "🎨 ================================"
echo "工作目錄: $(pwd)"

# 檢查 Python 版本
echo "檢查 Python 版本..."
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
else
    echo "❌ 錯誤：找不到 Python！"
    echo "請先安裝 Python 3.8 或以上版本"
    read -p "按 Enter 鍵結束..."
    exit 1
fi

echo "Python 版本: $($PYTHON_CMD --version)"

# 檢查並啟動虛擬環境
if [ -d "venv" ]; then
    echo "🔌 啟動虛擬環境..."
    source venv/bin/activate
    echo "✅ 虛擬環境已啟動"
else
    echo "❌ 找不到虛擬環境，請先執行 st_mac.command"
    read -p "按 Enter 鍵結束..."
    exit 1
fi

# ComfyUI 安裝目錄
COMFYUI_DIR="ComfyUI"
COMFYUI_URL="https://github.com/comfyanonymous/ComfyUI.git"
GEEKY_NODE_URL="https://github.com/GeekyGhost/ComfyUI-Geeky-Kokoro-TTS.git"

# 檢查並安裝 ComfyUI
if [ ! -d "$COMFYUI_DIR" ]; then
    echo "📦 ComfyUI 未安裝，正在下載..."
    git clone "$COMFYUI_URL" "$COMFYUI_DIR"
    if [ $? -eq 0 ]; then
        echo "✅ ComfyUI 下載完成"
    else
        echo "❌ ComfyUI 下載失敗"
        read -p "按 Enter 鍵結束..."
        exit 1
    fi
else
    echo "✅ ComfyUI 已存在"
fi

# 檢查並安裝 Geeky Kokoro TTS 節點
GEEKY_NODE_DIR="$COMFYUI_DIR/custom_nodes/ComfyUI-Geeky-Kokoro-TTS"
if [ ! -d "$GEEKY_NODE_DIR" ]; then
    echo "🎵 正在安裝 Geeky Kokoro TTS 節點..."
    mkdir -p "$COMFYUI_DIR/custom_nodes"
    cd "$COMFYUI_DIR/custom_nodes"
    git clone "$GEEKY_NODE_URL"
    cd "$PROJECT_ROOT"
    
    # 安裝節點依賴
    if [ -f "$GEEKY_NODE_DIR/requirements.txt" ]; then
        echo "📋 安裝 Geeky Kokoro TTS 依賴..."
        pip install -r "$GEEKY_NODE_DIR/requirements.txt"
    fi
    echo "✅ Geeky Kokoro TTS 節點安裝完成"
else
    echo "✅ Geeky Kokoro TTS 節點已存在"
fi

# 創建工作流程目錄
WORKFLOW_DIR="$COMFYUI_DIR/workflows"
mkdir -p "$WORKFLOW_DIR"

# 創建預設工作流程文件
WORKFLOW_FILE="$WORKFLOW_DIR/geeky_kokoro_tts_studio.json"
echo "📝 創建 Geeky Kokoro TTS 工作流程..."

cat > "$WORKFLOW_FILE" << 'EOF'
{
  "last_node_id": 15,
  "last_link_id": 20,
  "nodes": [
    {
      "id": 1,
      "type": "Geeky Kokoro TTS",
      "pos": [100, 100],
      "size": [400, 600],
      "flags": {},
      "order": 0,
      "mode": 0,
      "inputs": [],
      "outputs": [
        {
          "name": "AUDIO",
          "type": "AUDIO",
          "links": [1],
          "slot_index": 0
        },
        {
          "name": "CONFIG",
          "type": "CONFIG",
          "links": [2],
          "slot_index": 1
        }
      ],
      "properties": {
        "Node name for S&R": "Geeky Kokoro TTS"
      },
      "widgets_values": [
        "Hello! This is a test of the enhanced Kokoro TTS system with voice modification capabilities.",
        "am_adam",
        1.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        1.0,
        0.0,
        "anime",
        0.5,
        true,
        true
      ],
      "title": "🎵 Geeky Kokoro TTS Studio"
    },
    {
      "id": 2,
      "type": "Geeky Voice Modifier",
      "pos": [550, 100],
      "size": [350, 500],
      "flags": {},
      "order": 1,
      "mode": 0,
      "inputs": [
        {
          "name": "AUDIO",
          "type": "AUDIO",
          "link": 1,
          "slot_index": 0
        },
        {
          "name": "CONFIG",
          "type": "CONFIG",
          "link": 2,
          "slot_index": 1
        }
      ],
      "outputs": [
        {
          "name": "AUDIO",
          "type": "AUDIO",
          "links": [3],
          "slot_index": 0
        }
      ],
      "properties": {
        "Node name for S&R": "Geeky Voice Modifier"
      },
      "widgets_values": [
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        1.0,
        0.0,
        "professional",
        0.7,
        true
      ],
      "title": "🎛️ Voice Modifier"
    },
    {
      "id": 3,
      "type": "Audio Preview",
      "pos": [950, 100],
      "size": [300, 200],
      "flags": {},
      "order": 2,
      "mode": 0,
      "inputs": [
        {
          "name": "audio",
          "type": "AUDIO",
          "link": 3
        }
      ],
      "outputs": [],
      "properties": {
        "Node name for S&R": "Audio Preview"
      },
      "title": "🎧 Preview"
    },
    {
      "id": 4,
      "type": "Audio Save",
      "pos": [950, 350],
      "size": [300, 150],
      "flags": {},
      "order": 3,
      "mode": 0,
      "inputs": [
        {
          "name": "audio",
          "type": "AUDIO",
          "link": 4
        }
      ],
      "outputs": [],
      "properties": {
        "Node name for S&R": "Audio Save"
      },
      "widgets_values": [
        "output",
        "kokoro_tts"
      ],
      "title": "💾 Save Audio"
    },
    {
      "id": 5,
      "type": "Note",
      "pos": [100, 750],
      "size": [800, 200],
      "flags": {},
      "order": 4,
      "mode": 0,
      "inputs": [],
      "outputs": [],
      "properties": {
        "text": "🎵 Geeky Kokoro TTS Studio - 語音合成與修改工作室\n\n📝 使用說明：\n1. 在左側「Geeky Kokoro TTS」節點中輸入要合成的文字\n2. 選擇語音模型 (voice) 和調整基本參數 (speed, pitch 等)\n3. 在中間「Voice Modifier」節點中調整語音效果 (reverb, echo 等)\n4. 點擊「Queue Prompt」執行工作流程\n5. 在右側「Preview」節點中預聽效果\n6. 滿意後可通過「Save Audio」節點保存音頻\n7. 配置會自動同步到主程序的 voice_mod_config.txt\n\n🔧 重要：修改參數後記得點擊「Queue Prompt」重新生成音頻！\n\n📁 工作流程檔案位置：ComfyUI/workflows/geeky_kokoro_tts_studio.json"
      },
      "title": "📋 使用說明"
    }
  ],
  "links": [
    [1, 1, 0, 2, 0, "AUDIO"],
    [2, 1, 1, 2, 1, "CONFIG"],
    [3, 2, 0, 3, 0, "AUDIO"],
    [4, 2, 0, 4, 0, "AUDIO"]
  ],
  "groups": [
    {
      "title": "🎵 TTS 語音合成區",
      "bounding": [80, 50, 450, 670],
      "color": "#3f789e",
      "font_size": 24
    },
    {
      "title": "🎛️ 語音修改區",
      "bounding": [530, 50, 380, 570],
      "color": "#a1309b",
      "font_size": 24
    },
    {
      "title": "🎧 輸出預覽區",
      "bounding": [930, 50, 340, 470],
      "color": "#b58b2a",
      "font_size": 24
    }
  ],
  "config": {},
  "extra": {},
  "version": 0.4
}
EOF

echo "✅ 工作流程文件已創建: $WORKFLOW_FILE"

# 安裝 ComfyUI 必要依賴
echo "📦 檢查 ComfyUI 依賴..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install -r "$COMFYUI_DIR/requirements.txt" 2>/dev/null || true

# 創建配置同步腳本
SYNC_SCRIPT="scripts/comfyui_config_sync.py"
echo "🔄 創建配置同步腳本..."

cat > "$SYNC_SCRIPT" << 'EOF'
#!/usr/bin/env python3
"""
ComfyUI 配置同步工具
監聽 ComfyUI 的輸出並同步配置到主程序
"""
import json
import time
import threading
import webbrowser
from pathlib import Path
from services.comfyui_sync_service import ComfyUISyncService

def open_comfyui_with_workflow():
    """在瀏覽器中打開 ComfyUI 並載入工作流程"""
    workflow_path = Path("ComfyUI/workflows/geeky_kokoro_tts_studio.json")
    if workflow_path.exists():
        # 使用文件 URL 方式載入工作流程
        comfyui_url = "http://127.0.0.1:8188"
        print(f"🌐 正在瀏覽器中打開 ComfyUI: {comfyui_url}")
        webbrowser.open(comfyui_url)
        time.sleep(3)  # 等待 ComfyUI 完全載入
        print("📋 請在 ComfyUI 中點擊 'Load' 按鈕並選擇：")
        print(f"    {workflow_path.absolute()}")
        print("    或直接將 JSON 文件拖拽到 ComfyUI 介面中")
    else:
        print("❌ 找不到工作流程文件")

def main():
    print("🔄 ComfyUI 配置同步服務已啟動")
    
    # 啟動同步服務
    sync_service = ComfyUISyncService()
    sync_service.start_sync()
    
    # 等待 ComfyUI 啟動
    time.sleep(5)
    open_comfyui_with_workflow()
    
    print("\n📋 使用說明：")
    print("1. 在 ComfyUI 中調整 Geeky Kokoro TTS 節點的參數")
    print("2. 點擊 'Queue Prompt' 執行工作流程")
    print("3. 配置會自動同步到 voice_mod_config.txt")
    print("4. 主程序會自動應用新的語音設置")
    print("\n按 Ctrl+C 停止同步服務...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 正在停止同步服務...")
        sync_service.stop_sync()

if __name__ == "__main__":
    main()
EOF

chmod +x "$SYNC_SCRIPT"

# 檢查是否有其他 Python 進程佔用 8188 端口
echo "🔍 檢查端口 8188..."
if lsof -i :8188 >/dev/null 2>&1; then
    echo "⚠️  端口 8188 已被佔用，正在嘗試終止..."
    pkill -f "python.*main.py.*--port.*8188" 2>/dev/null || true
    sleep 2
fi

# 啟動 ComfyUI
echo "🚀 啟動 ComfyUI 服務..."
cd ComfyUI
python main.py --listen 127.0.0.1 --port 8188 &
COMFYUI_PID=$!
cd ..

# 等待 ComfyUI 完全啟動
echo "⏳ 等待 ComfyUI 啟動中..."
for i in {1..30}; do
    if curl -s http://127.0.0.1:8188/ >/dev/null 2>&1; then
        echo "✅ ComfyUI 已成功啟動！"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ ComfyUI 啟動超時，請檢查日誌：$COMFYUI_DIR/comfyui.log"
        exit 1
    fi
    echo "   等待中... ($i/30)"
    sleep 2
done

# 啟動配置同步腳本
echo "🔄 啟動配置同步服務..."
python "$SYNC_SCRIPT" &
SYNC_PID=$!

echo ""
echo "🎉 ================================"
echo "🎵 ComfyUI + Geeky Kokoro TTS 工作室已啟動！"
echo "🎉 ================================"
echo ""
echo "🌐 ComfyUI 介面: http://127.0.0.1:8188"
echo "📁 工作流程檔案: $WORKFLOW_FILE"
echo "🔄 配置同步: 已啟動"
echo ""
echo "🔄 TTS Studio 已就緒！使用說明："
echo "════════════════════════════════"
echo "1. 🌐 瀏覽器會自動打開 ComfyUI 介面"
echo "2. 📋 載入 tts_studio.json 工作流程"
echo "3. 🎛️  調整 TTS 和語音修改參數"
echo "4. ▶️  點擊 'Queue Prompt' 執行並測試效果"
echo "5. 🔄 配置會自動同步到主程序"
echo ""
echo "💡 快速應用設置："
echo "   執行: python3 scripts/apply_comfyui_settings.py"
echo "   或按 Ctrl+C 退出並重新啟動主程序"
echo ""

# 監聽中斷信號
trap 'echo ""; echo "🛑 正在停止所有服務..."; kill $COMFYUI_PID 2>/dev/null; kill $SYNC_PID 2>/dev/null; echo "✅ 所有服務已停止"; exit 0' INT

# 保持腳本運行
wait 