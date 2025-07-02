# Location: project_v2/utils/font_manager.py
# Usage: 字型管理器，處理中文字型載入

import os
from PyQt6.QtGui import QFont, QFontDatabase
from PyQt6.QtCore import QObject


class FontManager(QObject):
    """字型管理器"""
    
    def __init__(self):
        super().__init__()
        self.font_loaded = False
        self.font_family = None
        self.load_custom_font()
        
    def load_custom_font(self):
        """載入自訂字型"""
        font_path = os.path.join("fonts", "NotoSansCJKtc-Regular.otf")
        
        if os.path.exists(font_path):
            font_id = QFontDatabase.addApplicationFont(font_path)
            
            if font_id != -1:
                families = QFontDatabase.applicationFontFamilies(font_id)
                if families:
                    self.font_family = families[0]
                    self.font_loaded = True
                    print(f"成功載入字型: {self.font_family}")
                else:
                    print("無法取得字型家族名稱")
            else:
                print(f"載入字型失敗: {font_path}")
        else:
            print(f"找不到字型檔案: {font_path}")
            
    def get_font(self, size=12, bold=False):
        """取得字型"""
        if self.font_loaded and self.font_family:
            font = QFont(self.font_family)
        else:
            # 使用系統預設字型
            font = QFont()
            font.setFamily(self._get_system_font())
            
        font.setPointSize(size)
        font.setBold(bold)
        
        return font
        
    def _get_system_font(self):
        """取得系統預設中文字型"""
        import platform
        
        system = platform.system()
        if system == "Darwin":  # macOS
            return "PingFang TC"
        elif system == "Windows":
            return "Microsoft YaHei"
        else:  # Linux
            return "Noto Sans CJK TC"
            
    def get_available_fonts(self):
        """取得可用的中文字型列表"""
        chinese_fonts = []
        
        for family in QFontDatabase.families():
            # 檢查是否支援中文
            if any(char in family.lower() for char in ['chinese', 'cjk', 'tc', 'sc', '中文', '黑體', '宋體']):
                chinese_fonts.append(family)
                
        return chinese_fonts