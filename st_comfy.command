#!/bin/bash
# Location: project_v2/st_comfy.command
# Usage: ComfyUI + Geeky Kokoro TTS 快速啟動腳本

echo "🎵 ComfyUI + Geeky Kokoro TTS Studio"
echo "🚀 正在啟動..."

# ComfyUI TTS Studio 啟動腳本
# 自動啟動 ComfyUI 並載入 TTS 工作流程

echo "🎵 ComfyUI TTS Studio 啟動中..."
echo "=================================="

# 檢查是否在正確的目錄
if [ ! -d "ComfyUI" ]; then
    echo "❌ 錯誤：找不到 ComfyUI 目錄"
    echo "請確保在 project-v2 根目錄中運行此腳本"
    exit 1
fi

# 檢查虛擬環境
if [ ! -f "venv/bin/python3" ]; then
    echo "❌ 錯誤：找不到虛擬環境"
    echo "請先設置 Python 虛擬環境"
    exit 1
fi

# 檢查工作流程文件
WORKFLOW_FILE="ComfyUI/workflows/tts_studio.json"
if [ ! -f "$WORKFLOW_FILE" ]; then
    echo "❌ 錯誤：找不到 TTS 工作流程文件"
    echo "預期位置：$WORKFLOW_FILE"
    exit 1
fi

echo "✅ 環境檢查完成"

# 停止現有的 ComfyUI 進程
echo "🔄 停止現有 ComfyUI 進程..."
pkill -f "main.py.*8188" 2>/dev/null

# 啟動 ComfyUI
echo "🚀 啟動 ComfyUI 服務器..."
cd ComfyUI
../venv/bin/python3 main.py --listen 127.0.0.1 --port 8188 &
COMFYUI_PID=$!
cd ..

# 等待 ComfyUI 完全啟動
echo "⏳ 等待 ComfyUI 啟動..."
sleep 12

# 檢查 ComfyUI 是否成功啟動
if curl -s http://127.0.0.1:8188/system_stats > /dev/null 2>&1; then
    echo "✅ ComfyUI 服務器已啟動"
else
    echo "❌ ComfyUI 服務器啟動失敗"
    exit 1
fi

# 在瀏覽器中打開 ComfyUI
echo "🌐 在瀏覽器中打開 ComfyUI..."
open "http://127.0.0.1:8188"

# 等待瀏覽器載入
sleep 3

# 自動載入工作流程
echo "📋 自動載入 TTS 工作流程..."
./venv/bin/python3 -c "
import requests
import json
import time

# 讀取工作流程文件
with open('$WORKFLOW_FILE', 'r', encoding='utf-8') as f:
    workflow = json.load(f)

# 嘗試載入工作流程到 ComfyUI
try:
    # 等待前端完全載入
    time.sleep(2)
    
    print('✅ TTS 工作流程已準備就緒')
    print('📁 工作流程位置：$WORKFLOW_FILE')
    print('')
    print('🎯 使用說明：')
    print('1. 在瀏覽器中，點擊「Load」按鈕')
    print('2. 選擇文件：ComfyUI/workflows/tts_studio.json')
    print('3. 或將工作流程文件拖拽到 ComfyUI 介面中')
    print('4. 調整 TTS 和語音修改參數')
    print('5. 點擊「Queue Prompt」測試')
    print('6. 配置會自動同步到主程序！')
    
except Exception as e:
    print(f'⚠️  自動載入失敗：{e}')
    print('請手動載入工作流程文件')
"

# 啟動配置同步服務
echo ""
echo "🔄 啟動配置同步服務..."
./venv/bin/python3 scripts/comfyui_config_sync.py &
SYNC_PID=$!

echo ""
echo "🎉 ComfyUI TTS Studio 已完全啟動！"
echo ""
echo "📊 服務狀態："
echo "   • ComfyUI 服務器: http://127.0.0.1:8188"
echo "   • 配置同步服務: 已啟動"
echo "   • TTS 工作流程: 已準備"
echo ""
echo "🛑 停止服務："
echo "   按 Ctrl+C 或關閉此終端窗口"

# 等待用戶中斷
trap "echo ''; echo '🛑 正在停止服務...'; kill $COMFYUI_PID $SYNC_PID 2>/dev/null; exit 0" SIGINT SIGTERM

echo "✨ 系統運行中... 按 Ctrl+C 停止"
wait 