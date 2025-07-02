# Location: project_v2/build_windows.py
# Usage: Windows 打包腳本，使用 PyInstaller 建立執行檔

import os
import sys
import shutil
import PyInstaller.__main__


def build_windows_exe():
    """建立 Windows 執行檔"""
    
    print("=================================")
    print("防禦偵測系統 - Windows 打包工具")
    print("=================================")
    
    # 檢查 PyInstaller
    try:
        import PyInstaller
        print(f"PyInstaller 版本: {PyInstaller.__version__}")
    except ImportError:
        print("錯誤：找不到 PyInstaller")
        print("請執行: pip install pyinstaller")
        return False
        
    # 清理舊的建置
    print("\n清理舊的建置檔案...")
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"已刪除: {dir_name}")
            
    # 準備資源檔案
    print("\n準備資源檔案...")
    data_files = [
        ('fonts', 'fonts'),
        ('weapons_img', 'weapons_img'),
        ('period_config.csv', '.'),
        ('weapon_config.csv', '.'),
        ('prompt_config.txt', '.')
    ]
    
    # 建立 PyInstaller 參數
    pyinstaller_args = [
        'main.py',
        '--name=DefenseDetectionSystem',
        '--windowed',
        '--onefile',
        '--clean',
        '--noconfirm',
        '--icon=NONE',  # 如果有圖示檔案，在這裡指定
    ]
    
    # 加入資源檔案
    for src, dst in data_files:
        if os.path.exists(src):
            pyinstaller_args.extend(['--add-data', f'{src};{dst}'])
        else:
            print(f"警告：找不到 {src}")
            
    # 加入隱藏的 imports
    hidden_imports = [
        'cv2',
        'mediapipe',
        'PyQt6.QtCore',
        'PyQt6.QtGui', 
        'PyQt6.QtWidgets',
        'serial',
        'serial.tools',
        'serial.tools.list_ports',
        'ollama',
        'PIL',
        'numpy'
    ]
    
    for module in hidden_imports:
        pyinstaller_args.extend(['--hidden-import', module])
        
    # 執行 PyInstaller
    print("\n開始打包...")
    print("參數:", ' '.join(pyinstaller_args))
    
    try:
        PyInstaller.__main__.run(pyinstaller_args)
        print("\n打包完成！")
        
        # 複製額外檔案到 dist 目錄
        if os.path.exists('dist'):
            print("\n複製設定檔案...")
            
            # 建立必要目錄
            os.makedirs('dist/webcam-shots', exist_ok=True)
            os.makedirs('dist/weapons_img', exist_ok=True)
            os.makedirs('dist/fonts', exist_ok=True)
            
            # 複製設定檔
            config_files = ['period_config.csv', 'weapon_config.csv', 'prompt_config.txt']
            for file in config_files:
                if os.path.exists(file):
                    shutil.copy(file, 'dist/')
                    print(f"已複製: {file}")
                    
            # 複製字型
            if os.path.exists('fonts/NotoSansCJKtc-Regular.otf'):
                shutil.copy('fonts/NotoSansCJKtc-Regular.otf', 'dist/fonts/')
                print("已複製字型檔案")
                
            print("\n執行檔位置: dist/DefenseDetectionSystem.exe")
            print("\n請將以下檔案放入 dist 目錄後再執行：")
            print("1. weapons_img/ 目錄中的武器圖片")
            print("2. fonts/NotoSansCJKtc-Regular.otf (如果尚未複製)")
            
        return True
        
    except Exception as e:
        print(f"\n打包失敗: {e}")
        return False


def create_batch_file():
    """建立批次檔"""
    batch_content = """@echo off
echo ================================
echo 防禦偵測系統 - Windows 版
echo ================================
echo.

REM 檢查是否有虛擬環境
if exist venv\\Scripts\\activate.bat (
    echo 啟動虛擬環境...
    call venv\\Scripts\\activate.bat
) else (
    echo 建立虛擬環境...
    python -m venv venv
    call venv\\Scripts\\activate.bat
    
    echo 安裝相依套件...
    pip install --upgrade pip
    pip install -r requirements.txt
)

REM 建立必要目錄
if not exist webcam-shots mkdir webcam-shots
if not exist weapons_img mkdir weapons_img
if not exist fonts mkdir fonts

REM 檢查字型
if not exist fonts\\NotoSansCJKtc-Regular.otf (
    echo.
    echo 警告：找不到中文字型檔案
    echo 請將 NotoSansCJKtc-Regular.otf 放入 fonts\\ 目錄
    echo 程式將使用系統預設字型
    echo.
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
"""
    
    with open('start_windows.bat', 'w', encoding='utf-8') as f:
        f.write(batch_content)
        
    print("已建立 start_windows.bat")


if __name__ == "__main__":
    # 建立批次檔
    create_batch_file()
    
    # 詢問是否要建立執行檔
    response = input("\n是否要建立 .exe 執行檔？(y/n): ")
    
    if response.lower() == 'y':
        success = build_windows_exe()
        
        if success:
            print("\n打包成功！")
        else:
            print("\n打包失敗！")
            
    print("\n完成！")