# ComfyUI語音修改同步系統使用指南 🎵

## 🎯 系統概述

現在您擁有一個完整的語音修改同步系統，可以在ComfyUI圖形界面和您的主項目之間進行參數同步。

### 🔧 系統組件

1. **ComfyUI + Geeky Kokoro TTS** - 圖形化語音修改界面
2. **同步服務** (`services/comfyui_sync_service.py`) - 監聽ComfyUI變化
3. **控制面板** (`comfyui_voice_controller.py`) - 本地參數控制
4. **主項目整合** (`main.py`) - 自動應用語音修改

## 🚀 快速開始

### 1. 啟動ComfyUI
```bash
cd ComfyUI
python main.py --cpu --listen
```
然後瀏覽器打開：http://127.0.0.1:8188

### 2. 啟動語音控制面板
```bash
python comfyui_voice_controller.py
```

### 3. 啟動主項目
```bash
python main.py
```

## 🎛️ 使用方法

### 方法1：使用ComfyUI圖形界面

1. **在ComfyUI中添加語音修改節點**：
   - 右鍵點擊工作區
   - Add Node → Geeky Kokoro TTS → **Geeky Kokoro Voice Mod**

2. **調整參數**：
   - **Pitch Shift**: 音調偏移 (-12到+12半音)
   - **Formant Shift**: 音色偏移 (-5到+5)
   - **Voice Profile**: 預設語音風格
   - **Effect Intensity**: 效果強度

3. **執行工作流**：
   - 參數會自動同步到主項目
   - 在主項目中播放英文文本即可聽到效果

### 方法2：使用語音控制面板

1. **打開控制面板**：
   ```bash
   python comfyui_voice_controller.py
   ```

2. **調整參數**：
   - 使用滑桿和數值框調整各種效果
   - 選擇預設配置快速設定

3. **同步到主項目**：
   - 點擊「📥 同步到主項目」按鈕
   - 配置會立即更新到voice_mod_config.txt

4. **測試效果**：
   - 點擊「🎵 測試語音效果」
   - 或運行：`python test_voice_mod.py`

### 方法3：直接修改配置文件

編輯 `voice_mod_config.txt`：
```
voice_mod_enabled=True
voice_profile=None
pitch_shift=4.0        # 男聲轉女聲
formant_shift=2.0
reverb_amount=0.1
effect_blend=1.0
```

## 📋 預設配置範例

### 男聲轉女聲
```
pitch_shift=4.0
formant_shift=2.0
reverb_amount=0.1
compression=0.2
```

### 女聲轉男聲
```
pitch_shift=-4.0
formant_shift=-2.0
compression=0.3
```

### 機器人聲音
```
pitch_shift=1.0
formant_shift=-1.0
reverb_amount=0.2
echo_delay=0.1
compression=0.5
```

### 電影旁白
```
pitch_shift=-2.0
reverb_amount=0.4
compression=0.4
output_volume=1.0
```

## ⚙️ 配置說明

### main.py中的設定

```python
# 語音修改功能控制
VOICE_MOD_ENABLED = True                     # 啟用語音修改
VOICE_MOD_SYNC_FROM_COMFYUI = True          # 從ComfyUI同步設定

# 手動參數 (當SYNC_FROM_COMFYUI=False時使用)
VOICE_MOD_PITCH_SHIFT = 0.0                 # 音調偏移
VOICE_MOD_FORMANT_SHIFT = 0.0               # 音色偏移
VOICE_MOD_REVERB_AMOUNT = 0.0               # 混響量
VOICE_MOD_ECHO_DELAY = 0.0                  # 回聲延遲
VOICE_MOD_COMPRESSION = 0.0                 # 壓縮量
VOICE_MOD_EFFECT_BLEND = 1.0                # 效果混合比例
VOICE_MOD_OUTPUT_VOLUME = 0.0               # 輸出音量
```

### 參數範圍指南

| 參數 | 範圍 | 說明 |
|------|------|------|
| pitch_shift | -12 到 +12 | 半音偏移，+4約為男轉女，-4約為女轉男 |
| formant_shift | -5 到 +5 | 音色變化，正值更尖銳，負值更低沉 |
| reverb_amount | 0.0 到 1.0 | 混響效果，0.2-0.4適合大部分情況 |
| echo_delay | 0.0 到 1.0 | 回聲延遲，通常0.1-0.3 |
| compression | 0.0 到 1.0 | 動態壓縮，0.2-0.5增強聲音 |
| effect_blend | 0.0 到 1.0 | 原聲與效果混合比例 |
| output_volume | -20 到 +20 | 輸出音量dB調整 |

## 🔄 同步機制

### 自動同步流程
1. ComfyUI執行工作流 → 2. 同步服務檢測變化 → 3. 更新配置文件 → 4. 主項目自動應用

### 手動同步方式
1. **控制面板同步**：使用語音控制面板的同步按鈕
2. **配置文件同步**：直接編輯voice_mod_config.txt
3. **API同步**：程式碼中調用同步服務API

## 🧪 測試工具

### 快速測試
```bash
python test_voice_mod.py
```

### 詳細測試
```bash
python test_voice_mod_debug.py
```

### 控制面板測試
1. 開啟控制面板
2. 調整參數
3. 點擊「🎵 測試語音效果」

## 🛠️ 故障排除

### ComfyUI連接問題
- 確保ComfyUI正在運行：http://127.0.0.1:8188
- 檢查防火牆設定
- 重啟ComfyUI服務

### 語音效果不生效
1. 檢查`voice_mod_enabled=True`
2. 確認配置文件更新時間
3. 重啟主項目
4. 檢查依賴庫是否正確安裝

### 參數同步失敗
- 檢查websocket連接狀態
- 確認ComfyUI節點類型正確
- 查看控制面板日誌

### 音質問題
- 確保安裝了`librosa`和`resampy`
- 檢查音頻設備設定
- 調整`effect_blend`參數

## 📱 實際使用場景

### 場景1：即時語音風格調整
1. 啟動ComfyUI和控制面板
2. 在控制面板選擇預設風格
3. 微調參數
4. 同步到主項目
5. 即時聽到效果變化

### 場景2：工作流自動化
1. 在ComfyUI設計語音處理工作流
2. 保存為預設工作流
3. 每次執行自動同步參數
4. 主項目自動應用新設定

### 場景3：批量配置管理
1. 使用控制面板建立多組預設
2. 快速切換不同語音風格
3. 測試並保存最佳配置
4. 在主項目中使用最佳設定

## 🎉 進階功能

### 自定義語音風格
- 在控制面板創建新的預設組合
- 保存個人化配置
- 分享配置給其他用戶

### 動態參數調整
- 程式運行時實時調整參數
- 根據內容類型自動切換風格
- 建立智能語音適應系統

### 整合其他服務
- 結合語音識別調整輸出風格
- 根據文本內容智能選擇語音配置
- 建立多語言語音風格系統

---

## 🎯 總結

您現在擁有一個功能完整的語音修改同步系統：

✅ **圖形化操作** - ComfyUI直觀的節點編輯界面  
✅ **本地控制** - 專用的語音控制面板  
✅ **自動同步** - 配置變化自動應用到主項目  
✅ **靈活配置** - 支持手動和自動模式  
✅ **豐富預設** - 多種語音風格快速選擇  
✅ **實時測試** - 即時預覽語音效果  

享受您的語音修改之旅！🎵✨ 