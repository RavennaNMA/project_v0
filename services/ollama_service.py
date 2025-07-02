# Location: project_v2/services/ollama_service.py
# Usage: Ollama AI 服務，處理圖像分析和策略生成

from PyQt6.QtCore import QObject, QThread, pyqtSignal
import ollama
import base64
import json
import os
import re


class OllamaThread(QThread):
    """Ollama 執行緒"""
    result_ready = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    progress_update = pyqtSignal(str)
    
    def __init__(self, image_path, weapon_list, prompt_template):
        super().__init__()
        self.image_path = image_path
        self.weapon_list = weapon_list
        self.prompt_template = prompt_template
        
        # 模型設定
        self.img_model = "llava"
        self.desc_model = "yi:9b-chat-v1.5-q4_K_M"
        
    def run(self):
        """執行 AI 分析"""
        try:
            # 第一階段：圖像分析
            self.progress_update.emit("正在分析圖像...")
            image_description = self._analyze_image()
            
            if not image_description:
                raise Exception("圖像分析失敗")
                
            # 第二階段：策略生成
            self.progress_update.emit("正在生成策略...")
            response = self._generate_strategy(image_description)
            
            self.result_ready.emit(response)
            
        except Exception as e:
            self.error_occurred.emit(str(e))
            
    def _analyze_image(self):
        """使用圖像模型分析圖片"""
        try:
            # 讀取圖片並轉換為 base64
            with open(self.image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode()
                
            # 呼叫 llava 模型
            response = ollama.generate(
                model=self.img_model,
                prompt="Describe this person's appearance, clothing, and any notable features in detail.",
                images=[image_data]
            )
            
            if response and 'response' in response:
                # 在控制台輸出 llava 模型回應
                print(f"\n=== LLAVA (img_model) Response ===")
                print(response['response'])
                print("=" * 50)
                return response['response']
                
        except Exception as e:
            print(f"圖像分析錯誤: {e}")
            
        return None
        
    def _generate_strategy(self, image_description):
        """使用語言模型生成策略"""
        try:
            # 準備武器列表
            weapon_list_str = "\n".join([
                f"- {weapon['id']}: {weapon['name']}"
                for weapon in self.weapon_list
            ])
            
            # 填充提示詞模板
            prompt = self.prompt_template.format(
                image_description=image_description,
                weapon_list=weapon_list_str
            )
            
            # 呼叫 yi 模型
            response = ollama.generate(
                model=self.desc_model,
                prompt=prompt
            )
            
            if response and 'response' in response:
                # 在控制台輸出 desc_model 回應
                print(f"\n=== DESC_MODEL (yi:9b-chat-v1.5-q4_K_M) Response ===")
                print(response['response'])
                print("=" * 60)
                
                # 解析回應
                return self._parse_response(response['response'])
                
        except Exception as e:
            print(f"策略生成錯誤: {e}")
            
        # 返回預設回應
        return {
            'caption': 'Defense protocol activated.',
            'caption_tc': '防禦協議已啟動。',
            'weapons': ['01', '02']
        }
        
    def _parse_response(self, response_text):
        """解析 AI 回應"""
        result = {
            'caption': '',
            'caption_tc': '',
            'weapons': []
        }
        
        lines = response_text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('Caption_TC:'):
                caption_tc = line.replace('Caption_TC:', '').strip()
                # 清理字幕內容：移除武器相關信息
                caption_tc = self._clean_caption_text(caption_tc)
                result['caption_tc'] = caption_tc
            elif line.startswith('Caption_EN:'):
                caption_en = line.replace('Caption_EN:', '').strip()
                # 清理字幕內容：移除武器相關信息
                caption_en = self._clean_caption_text(caption_en)
                result['caption'] = caption_en
            elif line.startswith('Weapons:'):
                weapons_str = line.replace('Weapons:', '').strip()
                # 解析武器 ID，確保只提取純數字編號
                weapons = []
                for part in weapons_str.replace('[', '').replace(']', '').split(','):
                    weapon_id = part.strip().strip("'\"")
                    if weapon_id:
                        # 提取純數字編號 (如 "02_閃光燈" -> "02", "01" -> "01")
                        match = re.match(r'^(\d{2})', weapon_id)
                        if match:
                            weapons.append(match.group(1))
                        elif weapon_id.isdigit():
                            # 如果是純數字，確保是兩位數格式
                            weapons.append(f"{int(weapon_id):02d}")
                print(f"DEBUG: 解析到的武器ID列表: {weapons}")
                result['weapons'] = weapons[:3]  # 最多 3 個
                
        # 再次清理字幕，防止任何武器信息洩漏
        if result['caption_tc']:
            result['caption_tc'] = self._clean_caption_text(result['caption_tc'])
        if result['caption']:
            result['caption'] = self._clean_caption_text(result['caption'])
                
        # 確保有內容
        if not result['caption_tc'] and result['caption']:
            result['caption_tc'] = self._clean_caption_text(result['caption'])
        elif not result['caption'] and result['caption_tc']:
            result['caption'] = self._clean_caption_text(result['caption_tc'])
            
        if not result['weapons']:
            result['weapons'] = ['01', '02']
            
        return result
        
    def _clean_caption_text(self, text):
        """清理字幕文本，移除武器相關信息和不當內容"""
        if not text:
            return text
            
        # 移除常見的武器信息格式
        # 移除 "Weapons:" 開頭的行
        text = re.sub(r'Weapons:\s*\[.*?\]', '', text, flags=re.IGNORECASE)
        text = re.sub(r'Weapons:\s*.*', '', text, flags=re.IGNORECASE)
        
        # 移除包含武器編號的內容 (如 [01, 02, 03] 或 weapon1_id 等)
        text = re.sub(r'\[[\d\s,]+\]', '', text)
        text = re.sub(r'\[.*?weapon.*?\]', '', text, flags=re.IGNORECASE)
        text = re.sub(r'weapon\d+_id', '', text, flags=re.IGNORECASE)
        
        # 移除武器相關詞語和短語
        text = re.sub(r'\bweapons?\b\s*(are|is|were|was)?\s*(effective|selected|recommended|chosen)?', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\bselected\s+weapons?\b', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\bweapon\s+(selection|choice)\b', '', text, flags=re.IGNORECASE)
        
        # 移除多餘的標點符號和空白
        text = re.sub(r'\s+', ' ', text)  # 多個空格合併為一個
        text = re.sub(r'[,\s]*$', '', text)  # 移除結尾的逗號和空格
        text = re.sub(r'^[,\s]*', '', text)  # 移除開頭的逗號和空格
        
        # 清理連續的標點符號
        text = re.sub(r'[,.;:]+', '.', text)
        text = re.sub(r'\.+', '.', text)  # 多個句號合併為一個
        
        # 清理句子開頭和結尾
        text = re.sub(r'^\.\s*', '', text)  # 移除開頭的句號
        text = re.sub(r'\s*\.$', '.', text)  # 確保只有一個結尾句號
        
        return text.strip()


class OllamaService(QObject):
    """Ollama 服務管理器"""
    
    analysis_complete = pyqtSignal(dict)
    analysis_error = pyqtSignal(str)
    progress_update = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.thread = None
        self.prompt_template = self._load_prompt_template()
        
    def _load_prompt_template(self):
        """載入提示詞模板"""
        template_path = "prompt_config.txt"
        
        if os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            # 預設模板
            return """You are analyzing a person in a survival scenario based on their appearance.

Image description: {image_description}

Available defensive tools:
{weapon_list}

Based on the person's characteristics, select 2-3 most suitable defensive tools and provide survival advice.

Response format:
Caption_TC: [繁體中文生存策略，80字內]
Caption_EN: [English survival strategy, within 80 words]
Weapons: [weapon1_id, weapon2_id, weapon3_id]"""

    def analyze_image(self, image_path, weapon_list):
        """分析圖像"""
        if self.thread and self.thread.isRunning():
            return
            
        self.thread = OllamaThread(image_path, weapon_list, self.prompt_template)
        self.thread.result_ready.connect(self.analysis_complete.emit)
        self.thread.error_occurred.connect(self._handle_error)
        self.thread.progress_update.connect(self.progress_update.emit)
        self.thread.start()
        
    def _handle_error(self, error):
        """處理錯誤"""
        print(f"Ollama 錯誤: {error}")
        
        # 使用預設回應
        default_response = {
            'caption': 'System analysis unavailable. Activating default protocol.',
            'caption_tc': '系統分析不可用。啟動預設協議。',
            'weapons': ['01', '02']
        }
        
        self.analysis_complete.emit(default_response)