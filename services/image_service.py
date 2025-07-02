# Location: project_v2/services/image_service.py
# Usage: 圖像處理服務，包含預載入和快取功能

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QPixmap
import os
from PIL import Image
import numpy as np


class ImageService(QObject):
    """圖像處理服務"""
    
    image_loaded = pyqtSignal(str, QPixmap)
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.image_cache = {}
        self.weapons_dir = "weapons_img"
        
    def preload_weapon_images(self, weapon_config):
        """預載入所有武器圖片"""
        for weapon_id, weapon_info in weapon_config.items():
            image_path = os.path.join(self.weapons_dir, weapon_info['image_path'])
            
            if os.path.exists(image_path):
                try:
                    pixmap = QPixmap(image_path)
                    if not pixmap.isNull():
                        self.image_cache[weapon_id] = pixmap
                        print(f"預載入武器圖片: {weapon_id}")
                except Exception as e:
                    print(f"載入圖片失敗 {image_path}: {e}")
                    
    def get_weapon_image(self, weapon_id):
        """取得武器圖片"""
        if weapon_id in self.image_cache:
            return self.image_cache[weapon_id]
        return None
        
    def process_screenshot(self, image_path, target_size=(1080, 1920)):
        """處理截圖"""
        try:
            # 使用 PIL 開啟圖片
            image = Image.open(image_path)
            
            # 調整大小
            if image.size != target_size:
                image = image.resize(target_size, Image.Resampling.LANCZOS)
                
            # 儲存處理後的圖片
            processed_path = image_path.replace('.jpg', '_processed.jpg')
            image.save(processed_path, quality=95)
            
            return processed_path
            
        except Exception as e:
            self.error_occurred.emit(f"處理截圖失敗: {str(e)}")
            return image_path
            
    def apply_filter(self, image_path, filter_type='dramatic'):
        """套用濾鏡效果"""
        try:
            image = Image.open(image_path)
            
            if filter_type == 'dramatic':
                # 增加對比度和飽和度
                from PIL import ImageEnhance
                
                # 增加對比度
                enhancer = ImageEnhance.Contrast(image)
                image = enhancer.enhance(1.3)
                
                # 增加飽和度
                enhancer = ImageEnhance.Color(image)
                image = enhancer.enhance(1.2)
                
                # 調整亮度
                enhancer = ImageEnhance.Brightness(image)
                image = enhancer.enhance(0.9)
                
            elif filter_type == 'emergency':
                # 紅色警報效果
                image = image.convert('RGB')
                pixels = np.array(image)
                
                # 增強紅色通道
                pixels[:, :, 0] = np.minimum(pixels[:, :, 0] * 1.5, 255)
                pixels[:, :, 1] = pixels[:, :, 1] * 0.7
                pixels[:, :, 2] = pixels[:, :, 2] * 0.7
                
                image = Image.fromarray(pixels.astype('uint8'))
                
            # 儲存濾鏡效果
            filtered_path = image_path.replace('.jpg', f'_{filter_type}.jpg')
            image.save(filtered_path, quality=95)
            
            return filtered_path
            
        except Exception as e:
            self.error_occurred.emit(f"套用濾鏡失敗: {str(e)}")
            return image_path
            
    def create_thumbnail(self, image_path, size=(200, 200)):
        """建立縮圖"""
        try:
            image = Image.open(image_path)
            image.thumbnail(size, Image.Resampling.LANCZOS)
            
            thumb_path = image_path.replace('.jpg', '_thumb.jpg')
            image.save(thumb_path, quality=85)
            
            return thumb_path
            
        except Exception as e:
            self.error_occurred.emit(f"建立縮圖失敗: {str(e)}")
            return None
            
    def cleanup_cache(self):
        """清理圖片快取"""
        self.image_cache.clear()
        print("圖片快取已清理")