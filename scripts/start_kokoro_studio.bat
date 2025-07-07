@echo off
title Kokoro TTS Studio Launcher
echo.
echo 🎵 正在啟動 Kokoro TTS Studio...
echo.

cd /d "%~dp0"

echo 檢查Python環境...
python --version
if errorlevel 1 (
    echo ❌ Python 未安裝或未在PATH中
    pause
    exit /b 1
)

echo.
echo 檢查依賴包...
python -c "import PyQt6; print('✅ PyQt6 已安裝')" 2>nul || (
    echo ❌ PyQt6 未安裝，正在安裝...
    pip install PyQt6
)

echo.
echo 🚀 啟動 Kokoro TTS Studio...
python kokoro_tts_studio.py

if errorlevel 1 (
    echo.
    echo ❌ 啟動失敗，請檢查錯誤信息
    pause
) 