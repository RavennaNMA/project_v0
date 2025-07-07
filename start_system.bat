@echo off
cd /d "%~dp0"
title 防禦偵測系統

echo ================================
echo 防禦偵測系統 - Windows 版
echo ================================
echo.

REM 檢查是否有虛擬環境
if exist venv\Scripts\activate.bat (
    echo 啟動虛擬環境...
    call venv\Scripts\activate.bat
) else (
    echo 建立虛擬環境...
    python -m venv venv
    call venv\Scripts\activate.bat
    
    echo 安裝相依套件...
    pip install --upgrade pip
    pip install -r requirements.txt
)

REM 建立必要目錄
if not exist webcam-shots mkdir webcam-shots
if not exist weapons_img mkdir weapons_img
if not exist fonts mkdir fonts
if not exist config mkdir config

REM 檢查字型
if not exist fonts\NotoSansCJKtc-Regular.otf (
    echo.
    echo 警告：找不到中文字型檔案
    echo 請將 NotoSansCJKtc-Regular.otf 放入 fonts\ 目錄
    echo 程式將使用系統預設字型
    echo.
)

REM 檢查配置檔案
if not exist config\period_config.csv (
    echo 警告：找不到配置檔案，將使用預設設定
)

REM 啟動程式
echo.
echo 啟動防禦偵測系統...
echo.
python main.py

REM 如果程式異常結束
if errorlevel 1 (
    echo.
    echo 程式異常結束
    pause
) 