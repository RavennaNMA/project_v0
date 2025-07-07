# ComfyUI節點控制語音修改指南 🎛️

## 🎯 這就是您想要的控制方式！

現在您可以直接在ComfyUI中使用 **Geeky Kokoro Voice Mod** 節點來控制語音參數，調整後的設定會自動同步到您的主項目！

---

## 🚀 快速開始

### 步驟1：啟動ComfyUI
```bash
cd ComfyUI
python main.py --cpu --listen
```
然後瀏覽器打開：**http://127.0.0.1:8188**

### 步驟2：啟動節點監聽器
在另一個終端運行：
```bash
python comfyui_node_listener.py
```
這個程序會在後台監聽您在ComfyUI中的節點參數變化。

### 步驟3：在ComfyUI中添加語音修改節點
1. **右鍵點擊**工作區空白處
2. 選擇 **Add Node**
3. 導航到：**Geeky Kokoro TTS** → **Geeky Kokoro Voice Mod**

---

## 🎛️ 節點參數說明

### Geeky Kokoro Voice Mod 節點的主要參數：

| 參數名稱 | 範圍 | 效果說明 |
|----------|------|----------|
| **Pitch Shift** | -12 到 +12 | 音調偏移（半音）<br/>+4 = 男轉女聲<br/>-4 = 女轉男聲 |
| **Formant Shift** | -5 到 +5 | 音色變化<br/>正值更尖銳，負值更低沉 |
| **Reverb Amount** | 0.0 到 1.0 | 混響效果強度 |
| **Echo Delay** | 0.0 到 1.0 | 回聲延遲效果 |
| **Compression** | 0.0 到 1.0 | 動態壓縮 |
| **Effect Blend** | 0.0 到 1.0 | 原聲與效果混合比例 |
| **Output Volume** | -20 到 +20 | 輸出音量調整(dB) |

---

## 🎵 常用語音效果設定

### 男聲轉女聲
```
Pitch Shift: +4.0
Formant Shift: +2.0
Reverb Amount: 0.1
Compression: 0.2
Effect Blend: 1.0
```

### 女聲轉男聲
```
Pitch Shift: -4.0
Formant Shift: -2.0
Compression: 0.3
Effect Blend: 1.0
```

### 機器人聲音
```
Pitch Shift: +1.0
Formant Shift: -1.0
Reverb Amount: 0.2
Echo Delay: 0.1
Compression: 0.5
Effect Blend: 0.8
```

### 電影旁白聲
```
Pitch Shift: -2.0
Reverb Amount: 0.4
Compression: 0.4
Output Volume: +1.0
Effect Blend: 1.0
```

---

## 🔄 自動同步工作流程

### 1. 您在ComfyUI中的操作：
1. 調整 **Geeky Kokoro Voice Mod** 節點的參數
2. 點擊 **Queue Prompt** 執行工作流
3. 等待執行完成

### 2. 系統自動執行：
1. **節點監聽器**檢測到參數變化
2. 自動提取新的語音參數
3. 更新 `voice_mod_config.txt` 配置文件
4. 您的主項目下次播放語音時會自動應用新設定

### 3. 即時驗證：
運行以下命令測試新的語音效果：
```bash
python test_voice_mod.py
```

---

## 📋 完整使用流程

### 1. 系統啟動
```bash
# 終端1：啟動ComfyUI
cd ComfyUI
python main.py --cpu --listen

# 終端2：啟動節點監聽器  
python comfyui_node_listener.py

# 瀏覽器：打開ComfyUI界面
http://127.0.0.1:8188
```

### 2. 創建語音修改工作流
1. 在ComfyUI中添加節點：
   - **Geeky Kokoro Voice Mod** (語音修改)
   - **Text Input** (輸入測試文本)
   - **Audio Save** (保存音頻，可選)

2. 連接節點：
   - Text → Voice Mod → Audio Save

3. 設定參數：
   - 在Voice Mod節點中調整您想要的語音效果

### 3. 執行和同步
1. 點擊 **Queue Prompt** 執行工作流
2. 觀察節點監聽器的輸出：
   ```
   🎬 工作流開始執行 (ID: xxxxx)
   ✅ 已同步語音參數到主項目: {'pitch_shift': 4.0, 'formant_shift': 2.0}
   ```

### 4. 驗證效果
在您的主項目中播放英文文本，或運行：
```bash
python test_voice_mod.py
```

---

## 🛠️ 故障排除

### ComfyUI連接問題
- **檢查URL**：確保可以訪問 http://127.0.0.1:8188
- **重啟ComfyUI**：如果界面無響應，重新啟動ComfyUI
- **檢查端口**：確保8188端口沒有被其他程序占用

### 節點監聽器問題
- **監聽器未啟動**：確保運行 `python comfyui_node_listener.py`
- **連接失敗**：檢查ComfyUI是否運行正常
- **權限問題**：確保可以寫入 `voice_mod_config.txt`

### 參數不同步
- **節點類型錯誤**：確保使用的是 "Geeky Kokoro Voice Mod" 節點
- **執行失敗**：檢查工作流是否成功執行
- **配置文件**：檢查 `voice_mod_config.txt` 是否更新

### 語音效果不生效
- **配置未載入**：重啟主項目以載入新配置
- **依賴缺失**：確保安裝了 librosa 和 resampy
- **參數範圍**：檢查參數是否在有效範圍內

---

## 🎉 進階技巧

### 1. 保存工作流預設
- 在ComfyUI中設定好參數後，點擊 **Save** 保存工作流
- 為不同的語音風格創建不同的工作流文件
- 需要時快速載入對應的預設

### 2. 批量測試參數
- 創建多個Voice Mod節點，設定不同參數
- 一次執行多種效果，快速比較
- 選出最佳設定後用於主項目

### 3. 動態調整
- 在工作流執行過程中實時調整參數
- 觀察監聽器輸出，確認同步狀態
- 立即在主項目中測試效果

### 4. 組合效果
- 使用多個Voice Mod節點串聯
- 創建更複雜的語音效果
- 每個節點專門處理一種效果類型

---

## 🎯 總結

現在您擁有完全基於ComfyUI節點的語音控制系統：

✅ **直接節點控制** - 在ComfyUI中調整 Geeky Kokoro Voice Mod 節點參數  
✅ **自動參數同步** - 節點變化自動同步到主項目  
✅ **即時效果驗證** - 調整後立即在主項目中生效  
✅ **工作流保存** - 保存不同的語音風格預設  
✅ **可視化操作** - 圖形化節點編輯，直觀易用  

這正是您想要的控制方式：**直接在ComfyUI中用節點控制，不需要額外的Python控制面板！**

享受您的ComfyUI語音控制體驗！🎵✨ 