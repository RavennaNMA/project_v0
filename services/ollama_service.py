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
        """解析 AI 回應 - 強化版"""
        result = {
            'caption': '',
            'caption_tc': '',
            'weapons': []
        }
        
        # 先移除多餘的空白和換行
        response_text = response_text.strip()
        print(f"DEBUG: 原始回應文本:\n{response_text}")
        
        # 使用正則表達式強制分離中英文內容
        # 匹配 Caption_TC: 開頭到 Caption_EN: 之前的內容
        tc_match = re.search(r'Caption_TC:\s*(.*?)(?=Caption_EN:|Weapons:|$)', response_text, re.DOTALL | re.IGNORECASE)
        if tc_match:
            caption_tc = tc_match.group(1).strip()
            # 移除可能包含的英文部分
            caption_tc = re.sub(r'Caption_EN:.*', '', caption_tc, flags=re.DOTALL | re.IGNORECASE)
            caption_tc = self._clean_caption_text(caption_tc)
            # 驗證是否主要為中文
            if caption_tc and self._is_primarily_chinese(caption_tc):
                result['caption_tc'] = caption_tc[:180]  # 適當增加到120字，確保完整性
                
        # 匹配 Caption_EN: 開頭到 Weapons: 之前的內容
        en_match = re.search(r'Caption_EN:\s*(.*?)(?=Weapons:|$)', response_text, re.DOTALL | re.IGNORECASE)
        if en_match:
            caption_en = en_match.group(1).strip()
            caption_en = self._clean_caption_text(caption_en)
            # 驗證是否主要為英文
            if caption_en and self._is_primarily_english(caption_en):
                result['caption'] = caption_en[:800]  # 增加到800字符，確保包含完整句子
                
        # 匹配武器列表
        weapons_match = re.search(r'Weapons:\s*\[?([^\]]*)\]?', response_text, re.IGNORECASE)
        if weapons_match:
            weapons_str = weapons_match.group(1).strip()
            weapons = []
            
            # 解析武器ID - 更嚴格的匹配
            for part in re.findall(r'\d+', weapons_str):
                if part.isdigit() and 1 <= int(part) <= 10:
                    weapons.append(f"{int(part):02d}")
                    
            print(f"DEBUG: 解析到的武器ID列表: {weapons}")
            result['weapons'] = weapons[:3] if weapons else ['01', '02']
        else:
            result['weapons'] = ['01', '02']
        
        # 最終清理，確保沒有武器相關信息
        if result['caption_tc']:
            result['caption_tc'] = self._clean_caption_text(result['caption_tc'])
        if result['caption']:
            result['caption'] = self._clean_caption_text(result['caption'])
            
        # 確保有內容
        if not result['caption_tc'] and result['caption']:
            # 如果沒有中文但有英文，不要複製英文到中文
            pass
        elif not result['caption'] and result['caption_tc']:
            # 如果沒有英文但有中文，不要複製中文到英文
            pass
            
        # 如果沒有找到武器，使用預設
        if not result['weapons']:
            result['weapons'] = ['01', '02']
            
        # 調試輸出
        print(f"DEBUG: 解析結果:")
        print(f"  caption_tc: '{result['caption_tc']}'")
        print(f"  caption: '{result['caption']}'")
        print(f"  weapons: {result['weapons']}")
            
        return result
        
    def _clean_caption_text(self, text):
        """清理字幕文本，移除武器相關信息和不當內容"""
        if not text:
            return text
            
        # 移除常見的武器信息格式
        # 移除 "Weapons:" 開頭的內容
        text = re.sub(r'Weapons:\s*\[.*?\]', '', text, flags=re.IGNORECASE)
        text = re.sub(r'Weapons:\s*.*', '', text, flags=re.IGNORECASE)
        
        # 移除包含武器編號的內容
        text = re.sub(r'\[[\d\s,]+\]', '', text)
        text = re.sub(r'\[.*?weapon.*?\]', '', text, flags=re.IGNORECASE)
        text = re.sub(r'weapon\d+_id', '', text, flags=re.IGNORECASE)
        
        # 移除武器相關詞語
        text = re.sub(r'\bweapons?\b\s*(are|is|were|was)?\s*(effective|selected|recommended|chosen)?', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\bselected\s+weapons?\b', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\bweapon\s+(selection|choice)\b', '', text, flags=re.IGNORECASE)
        
        # 移除可能的重複內容（例如Caption_TC: Caption_TC: ...）
        text = re.sub(r'Caption_TC:\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'Caption_EN:\s*', '', text, flags=re.IGNORECASE)
        
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
        
        # 如果整個文本只剩下標點符號，返回空字符串
        if re.match(r'^[.,;:\s]*$', text):
            return ''
        
        return text.strip()
        
    def _is_primarily_chinese(self, text):
        """檢查文本是否主要為中文"""
        if not text:
            return False
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        total_chars = len(re.findall(r'[a-zA-Z\u4e00-\u9fff]', text))
        return total_chars > 0 and (chinese_chars / total_chars) > 0.7
        
    def _is_primarily_english(self, text):
        """檢查文本是否主要為英文"""
        if not text:
            return False
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        total_chars = len(re.findall(r'[a-zA-Z\u4e00-\u9fff]', text))
        return total_chars > 0 and (english_chars / total_chars) > 0.7


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