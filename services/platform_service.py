# Location: project_v2/services/platform_service.py
# Usage: 跨平台相容性服務

import platform
import os
import sys
import subprocess
from PyQt6.QtCore import QObject


class PlatformService(QObject):
    """平台相關服務"""
    
    def __init__(self):
        super().__init__()
        self.system = platform.system()
        self.is_mac = self.system == "Darwin"
        self.is_windows = self.system == "Windows"
        self.is_linux = self.system == "Linux"
        
    def get_platform_info(self):
        """取得平台資訊"""
        return {
            'system': self.system,
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version()
        }
        
    def get_resource_path(self, relative_path):
        """取得資源路徑（支援打包後的執行檔）"""
        if hasattr(sys, '_MEIPASS'):
            # PyInstaller 打包後的路徑
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.abspath(relative_path)
        
    def open_file_explorer(self, path):
        """開啟檔案總管並定位到指定路徑"""
        try:
            if self.is_windows:
                os.startfile(path)
            elif self.is_mac:
                subprocess.run(['open', path])
            elif self.is_linux:
                subprocess.run(['xdg-open', path])
        except Exception as e:
            print(f"開啟檔案總管失敗: {e}")
            
    def get_camera_permissions(self):
        """檢查相機權限（主要針對 macOS）"""
        if self.is_mac:
            # macOS 需要相機權限
            try:
                # 這裡可以加入檢查權限的邏輯
                # 目前假設已授權
                return True
            except:
                return False
        else:
            # Windows 和 Linux 通常不需要特別權限
            return True
            
    def request_camera_permission(self):
        """請求相機權限"""
        if self.is_mac:
            # macOS 會在第一次使用時自動請求權限
            print("請在系統偏好設定中授予相機權限")
            return True
        return True
        
    def get_serial_port_pattern(self):
        """取得串口命名模式"""
        if self.is_windows:
            return "COM"
        elif self.is_mac:
            return "/dev/cu."
        else:
            return "/dev/tty"
            
    def make_executable(self, file_path):
        """設定檔案為可執行（Unix-like 系統）"""
        if not self.is_windows:
            try:
                import stat
                st = os.stat(file_path)
                os.chmod(file_path, st.st_mode | stat.S_IEXEC)
                return True
            except Exception as e:
                print(f"設定執行權限失敗: {e}")
                return False
        return True
        
    def get_default_font(self):
        """取得系統預設字型"""
        if self.is_windows:
            return "Microsoft YaHei"
        elif self.is_mac:
            return "PingFang TC"
        else:
            return "Noto Sans CJK TC"
            
    def get_temp_dir(self):
        """取得暫存目錄"""
        import tempfile
        return tempfile.gettempdir()
        
    def check_dependencies(self):
        """檢查系統相依性"""
        dependencies = {
            'python': sys.version_info >= (3, 8),
            'qt6': True,  # 已經 import 成功就是有安裝
            'opencv': self._check_opencv(),
            'mediapipe': self._check_mediapipe()
        }
        
        missing = [dep for dep, installed in dependencies.items() if not installed]
        
        return {
            'all_satisfied': len(missing) == 0,
            'missing': missing,
            'details': dependencies
        }
        
    def _check_opencv(self):
        """檢查 OpenCV"""
        try:
            import cv2
            return True
        except ImportError:
            return False
            
    def _check_mediapipe(self):
        """檢查 MediaPipe"""
        try:
            import mediapipe
            return True
        except ImportError:
            return False