@echo off
chcp 65001 >nul
echo ================================
echo 防禦偵測系統 - Windows 版
echo ================================
echo.

REM 檢查 Python
echo 檢查 Python 安裝...
python --version >nul 2>&1
if errorlevel 1 (
    echo 錯誤：找不到 Python！
    echo 請先安裝 Python 3.8 或以上版本
    echo https://www.python.org/downloads/
    pause
    exit /b 1
)

python --version

REM 檢查是否有虛擬環境
if exist venv\Scripts\activate.bat (
    echo 找到虛擬環境，啟動中...
    call venv\Scripts\activate.bat
) else (
    echo 建立虛擬環境...
    python -m venv venv
    if errorlevel 1 (
        echo 建立虛擬環境失敗！
        pause
        exit /b 1
    )
    
    call venv\Scripts\activate.bat
    
    echo.
    echo 升級 pip...
    python -m pip install --upgrade pip
    
    echo.
    echo 安裝相依套件...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo 安裝套件失敗！
        pause
        exit /b 1
    )
)

REM 建立必要目錄
if not exist webcam-shots mkdir webcam-shots
if not exist weapons_img mkdir weapons_img
if not exist fonts mkdir fonts

REM 檢查字型
if not exist fonts\NotoSansCJKtc-Regular.otf (
    echo.
    echo =====================================
    echo 警告：找不到中文字型檔案
    echo 請將 NotoSansCJKtc-Regular.otf 
    echo 放入 fonts\ 目錄
    echo 程式將使用系統預設字型
    echo =====================================
    echo.
    timeout /t 3 >nul
)

REM 檢查設定檔
if not exist period_config.csv (
    echo 警告：找不到 period_config.csv
    echo 將使用預設時間設定
    echo.
)

if not exist weapon_config.csv (
    echo 警告：找不到 weapon_config.csv
    echo 將使用預設武器設定
    echo.
)

REM 啟動程式
echo.
echo 啟動防禦偵測系統...
echo =====================================
echo.

python main.py

REM 檢查結束狀態
if errorlevel 1 (
    echo.
    echo =====================================
    echo 程式異常結束！
    echo 錯誤代碼: %errorlevel%
    echo =====================================
    pause
) else (
    echo.
    echo 程式正常結束
    timeout /t 3 >nul
)