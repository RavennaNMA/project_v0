#!/bin/bash
# Location: project_v2/st_mac.command
# Usage: Mac 啟動指令檔（可雙擊執行）

# 取得腳本所在目錄
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "================================"
echo "防禦偵測系統 - Mac 版"
echo "================================"

# 檢查 Python 版本
echo "檢查 Python 版本..."
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
else
    echo "錯誤：找不到 Python！"
    echo "請先安裝 Python 3.8 或以上版本"
    echo "https://www.python.org/downloads/"
    read -p "按 Enter 鍵結束..."
    exit 1
fi

# 顯示 Python 版本
$PYTHON_CMD --version

# 檢查虛擬環境
if [ -d "venv" ]; then
    echo "找到虛擬環境，啟動中..."
    source venv/bin/activate
else
    echo "建立虛擬環境..."
    $PYTHON_CMD -m venv venv
    source venv/bin/activate
    
    echo "安裝相依套件..."
    pip install --upgrade pip
    pip install -r requirements.txt
fi

# 建立必要目錄
mkdir -p webcam-shots
mkdir -p weapons_img
mkdir -p fonts

# 檢查字型檔案
if [ ! -f "fonts/NotoSansCJKtc-Regular.otf" ]; then
    echo ""
    echo "警告：找不到中文字型檔案"
    echo "請將 NotoSansCJKtc-Regular.otf 放入 fonts/ 目錄"
    echo "程式將使用系統預設字型"
    echo ""
fi

# 啟動程式
echo ""
echo "啟動防禦偵測系統..."
echo ""
python main.py

# 如果程式異常結束，保持視窗開啟
if [ $? -ne 0 ]; then
    echo ""
    echo "程式異常結束"
    read -p "按 Enter 鍵關閉..."
fi