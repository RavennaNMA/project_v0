# 🎵 ComfyUI TTS Studio 使用指南

ComfyUI TTS Studio 是一個視覺化的語音合成和修改工作室，讓你可以透過拖拽節點的方式輕鬆調整語音參數，並自動同步到主程序。

## 📋 功能特色

### 🎤 語音合成
- **多語音模型**：支援多種 Geeky Kokoro 語音模型
- **語音混合**：可混合兩種不同語音創造獨特效果
- **即時預覽**：調整參數後立即試聽效果

### 🎛️ 高級語音修改
- **音調調整**：pitch_shift（音調偏移）
- **共振峰調整**：formant_shift（音色變化）
- **混響效果**：reverb_amount（空間感）
- **回音延遲**：echo_delay（回音效果）
- **動態壓縮**：compression（音量平衡）
- **等化器**：eq_bass, eq_mid, eq_treble（頻率調整）

### 🔄 自動配置同步
- **即時同步**：ComfyUI 中的參數變化自動同步到主程序
- **配置監控**：實時監控語音修改參數變化
- **無縫整合**：修改後的設定直接應用到主程序 TTS 系統

## 🚀 快速開始

### 1. 啟動 ComfyUI Studio
```bash
# 在專案根目錄執行
./st_comfy.command
```

或手動啟動：
```bash
# 啟動 ComfyUI 服務器
cd ComfyUI
../venv/bin/python3 main.py --listen 127.0.0.1 --port 8188 &

# 啟動配置同步服務
python3 scripts/comfyui_config_sync.py &
```

### 2. 載入 TTS 工作流程
1. 在瀏覽器中打開 http://127.0.0.1:8188
2. 點擊右下角的 **"Load"** 按鈕
3. 選擇檔案：`ComfyUI/workflows/tts_studio.json`
4. 或直接將 JSON 檔案拖拽到 ComfyUI 介面中

### 3. 工作流程說明

載入後你會看到以下節點：

```
[GeekyKokoroTTS] → [PreviewAudio (原始)]
        ↓
[GeekyKokoroAdvancedVoice] → [PreviewAudio (修改後)]
```

## 🎯 使用步驟

### 第一步：設定基本語音參數

在 **GeekyKokoroTTS** 節點中：
- **文字輸入**：輸入要合成的文字內容
- **語音模型**：選擇語音（🇺🇸 🚹 Onyx, 🇺🇸 🚹 Michael 等）
- **語音速度**：調整播放速度（0.5-2.0）
- **語音混合**：啟用可混合兩種語音

### 第二步：調整高級語音效果

在 **GeekyKokoroAdvancedVoice** 節點中：

#### 📊 基本參數
- **effect_blend**：效果混合強度（0.0-1.0）
- **output_volume**：輸出音量調整
- **voice_profile**：語音預設檔案（None/Custom/Robot 等）
- **profile_intensity**：預設強度（0.0-1.0）

#### 🔧 手動調整（manual_mode = true）
- **pitch_shift**：音調偏移（-12.0 到 +12.0 半音）
- **formant_shift**：共振峰偏移（改變音色）
- **reverb_amount**：混響強度（0.0-1.0）
- **echo_delay**：回音延遲時間
- **distortion**：失真效果強度
- **compression**：動態壓縮（0.0-1.0）

#### 🎚️ 等化器
- **eq_bass**：低頻調整（-1.0 到 +1.0）
- **eq_mid**：中頻調整
- **eq_treble**：高頻調整

### 第三步：預覽和測試

1. **原始預覽**：在第一個 PreviewAudio 節點中試聽原始語音
2. **效果預覽**：在第二個 PreviewAudio 節點中試聽修改後的語音
3. **參數調整**：根據效果調整 GeekyKokoroAdvancedVoice 節點參數
4. **重新執行**：點擊 **"Queue Prompt"** 重新生成音頻

### 第四步：應用到主程序

當你在 ComfyUI 中點擊 **"Queue Prompt"** 執行工作流程時：

1. **自動偵測**：配置同步服務會偵測到參數變化
2. **提取配置**：從工作流程中提取所有語音修改參數
3. **同步保存**：自動更新 `config/voice_mod_config.txt`
4. **主程序應用**：主程序會自動使用新的語音設定

### 手動應用設置

如果需要立即將當前 ComfyUI 設置應用到主程序：

#### 方法一：快速應用（推薦）
```bash
# 雙擊執行
./apply_tts_settings.command
```

#### 方法二：命令行應用
```bash
# 在項目根目錄執行
python3 scripts/apply_comfyui_settings.py
```

#### 方法三：手動同步
```bash
# 啟動配置同步服務
python3 scripts/comfyui_config_sync.py
```

## 📁 文件結構

```
project-v2/
├── st_comfy.command              # 主啟動腳本
├── apply_tts_settings.command    # 快速設置應用腳本
├── ComfyUI/
│   └── workflows/
│       └── tts_studio.json      # TTS 工作流程
├── scripts/
│   ├── comfyui_config_sync.py   # 配置同步服務
│   └── apply_comfyui_settings.py # 設置應用腳本
├── services/
│   └── comfyui_sync_service.py  # 同步服務核心
└── config/
    ├── tts_config.txt           # TTS 主配置文件
    └── voice_mod_config.txt     # 語音修改配置文件
```

## ⚙️ 配置參數對應

| ComfyUI 節點參數 | 配置檔案參數 | 說明 | 範圍 |
|-----------------|-------------|------|------|
| voice | kokoro_voice | 語音模型 | am_onyx, bm_george 等 |
| speed | kokoro_speed | 語音速度 | 0.5-2.0 |
| pitch_shift | pitch_shift | 音調偏移 | -12.0 ~ +12.0 |
| formant_shift | formant_shift | 共振峰偏移 | -1.0 ~ +1.0 |
| reverb_amount | reverb_amount | 混響強度 | 0.0-1.0 |
| echo_delay | echo_delay | 回音延遲 | 0.0-1.0 |
| compression | compression | 動態壓縮 | 0.0-1.0 |
| effect_blend | effect_blend | 效果混合 | 0.0-1.0 |
| output_volume | output_volume | 輸出音量 | -1.0 ~ +1.0 |

## 🔧 故障排除

### ComfyUI 無法啟動
```bash
# 檢查虛擬環境
source venv/bin/activate

# 重新安裝依賴
cd ComfyUI
pip install -r requirements.txt

# 檢查端口是否被佔用
lsof -i :8188
```

### TTS 節點錯誤
```bash
# 重新安裝 Kokoro TTS
cd ComfyUI/custom_nodes/ComfyUI-Geeky-Kokoro-TTS
pip install --no-deps "kokoro-onnx==0.1.6"
pip install "onnxruntime==1.19.2"
```

### 配置同步失敗
```bash
# 檢查配置文件權限
ls -la config/voice_mod_config.txt

# 手動測試同步服務
python3 scripts/comfyui_config_sync.py
```

### WebSocket 連接問題
- 確保 ComfyUI 完全啟動後再啟動同步服務
- 檢查防火牆是否阻擋 8188 端口
- 重啟 ComfyUI 和同步服務

### 設置不生效
```bash
# 檢查配置文件是否正確更新
cat config/tts_config.txt
cat config/voice_mod_config.txt

# 手動應用設置
python3 scripts/apply_comfyui_settings.py

# 重啟主程序
python3 main.py
```

## 📊 監控和除錯

### 查看當前應用的設置
```bash
# 使用設置應用腳本查看
python3 scripts/apply_comfyui_settings.py

# 或直接查看配置文件
cat config/tts_config.txt | grep -E "kokoro_voice|kokoro_speed"
cat config/voice_mod_config.txt | grep -E "voice_profile|pitch_shift|effect_blend"
```

### 查看同步狀態
配置同步服務會輸出即時狀態：
```
✅ ComfyUI 服務器連接成功
🔄 配置已更新: effect_blend, pitch_shift, reverb_amount
📝 主配置文件已更新
```

### 配置文件格式
生成的 `config/voice_mod_config.txt`：
```
# 語音修改配置檔案
voice_mod_enabled=True
voice_model=🇺🇸 🚹 Onyx
speed=1.0
pitch_shift=1.5
reverb_amount=0.3
compression=0.4
effect_blend=0.7
output_volume=0.0
manual_mode=True
```

## 🎯 使用技巧

### 1. 快速測試流程
1. 在 ComfyUI 中調整參數
2. 點擊 "Queue Prompt" 測試效果
3. 運行 `./apply_tts_settings.command` 應用到主程序
4. 啟動主程序驗證效果

### 2. 批量設置調試
1. 創建多個工作流程變體（如 `tts_studio_robot.json`）
2. 使用不同工作流程測試各種效果
3. 選定最佳效果後應用到主程序

### 3. 配置備份和恢復
```bash
# 備份當前設置
cp config/tts_config.txt config/tts_config.backup
cp config/voice_mod_config.txt config/voice_mod_config.backup

# 恢復設置
cp config/tts_config.backup config/tts_config.txt
cp config/voice_mod_config.backup config/voice_mod_config.txt
```

### 4. 快速預設
- 使用 `voice_profile` 快速套用預設效果
- 調整 `profile_intensity` 控制預設強度

### 5. 細緻調整
- 啟用 `manual_mode` 進行精確參數調整
- 使用等化器調整音色平衡

### 6. 效果組合
- 組合使用 reverb + echo 創造空間感
- 適度使用 compression 平衡音量

### 7. 即時預覽
- 先在原始預覽中確認基本語音
- 在效果預覽中確認修改效果
- 反覆調整直到滿意

## 📝 注意事項

1. **參數調整**：每次修改參數後記得點擊 "Queue Prompt"
2. **配置同步**：修改會自動保存，無需手動操作
3. **性能考量**：複雜效果可能增加處理時間
4. **兼容性**：確保 Python 3.9+ 環境
5. **資源使用**：大量語音合成可能消耗較多 CPU/GPU 資源

透過 ComfyUI TTS Studio，你可以直觀地調整語音參數，立即預覽效果，並無縫整合到主程序中，大幅提升語音合成的靈活性和易用性！ 