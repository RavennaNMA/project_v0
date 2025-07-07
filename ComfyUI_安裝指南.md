# ComfyUI + Geeky Kokoro TTS 安裝使用指南

## 🎯 概述

您現在已經成功安裝了：
1. ✅ ComfyUI (主程序)
2. ✅ ComfyUI-Geeky-Kokoro-TTS (語音修改界面節點)
3. ✅ 所有必需的依賴包
4. ⏳ 模型文件（需要下載）

## 📂 當前安裝路徑

```
project_v2/
├── ComfyUI/                           # ComfyUI主程序
│   ├── custom_nodes/
│   │   └── ComfyUI-Geeky-Kokoro-TTS/  # 語音修改節點
│   │       ├── models/                # 模型文件目錄（需要下載模型）
│   │       ├── requirements.txt       # 已安裝完成
│   │       └── ...
│   ├── main.py                        # ComfyUI啟動文件
│   └── ...
└── services/
    └── voice_mod_service.py           # 您的語音修改服務（已完成）
```

## 🔧 完成安裝

### 1. 下載模型文件

模型文件較大，需要手動下載到 `ComfyUI/custom_nodes/ComfyUI-Geeky-Kokoro-TTS/models/` 目錄：

**方法一：瀏覽器下載**
1. 開啟瀏覽器前往：https://github.com/nazdridoy/kokoro-tts/releases/tag/v1.0.0
2. 下載以下兩個文件：
   - `kokoro-v1.0.onnx` (約83MB)
   - `voices-v1.0.bin` (約1.3MB)
3. 將文件複製到 `ComfyUI/custom_nodes/ComfyUI-Geeky-Kokoro-TTS/models/` 目錄

**方法二：命令行下載**
```bash
cd ComfyUI/custom_nodes/ComfyUI-Geeky-Kokoro-TTS/models/

# 下載模型文件
curl -L -o kokoro-v1.0.onnx https://github.com/nazdridoy/kokoro-tts/releases/download/v1.0.0/kokoro-v1.0.onnx
curl -L -o voices-v1.0.bin https://github.com/nazdridoy/kokoro-tts/releases/download/v1.0.0/voices-v1.0.bin
```

### 2. 啟動ComfyUI

```bash
cd ComfyUI
python main.py --preview-method auto
```

啟動後，瀏覽器開啟：http://127.0.0.1:8188

## 🎛️ 使用語音修改界面

### 在ComfyUI中添加語音節點

1. **右鍵點擊空白處** → Add Node
2. **選擇** → Geeky Kokoro TTS → 選擇所需節點：
   - `Geeky Kokoro TTS` - 基礎TTS節點
   - `Geeky Kokoro Voice Mod` - 語音修改節點（您需要的）
   - `Geeky Kokoro Audio Combiner` - 音頻組合節點

### 語音修改節點功能

**Geeky Kokoro Voice Mod** 節點提供以下參數：

#### 📊 基礎設定
- **Voice Profile**: 預設語音配置
  - Robot, Cinematic, Monster, Singer, Child 等27+種
- **Profile Intensity**: 效果強度 (0.0-1.0)
- **Manual Mode**: 手動模式開關

#### 🎵 音調控制 (Pitch Control)
- **Pitch Shift**: 音調偏移 (-12 到 +12 半音)
  - 負值：降低音調（男聲更低沉）
  - 正值：提高音調（變成女聲風格）

#### 🎭 音色控制 (Formant Control)
- **Formant Shift**: 音色偏移 (-5 到 +5)
  - 模擬不同聲道大小

#### 🎚️ 音頻效果
- **Reverb Amount**: 混響量 (0.0-1.0)
- **Echo Delay**: 回聲延遲 (0.0-1.0)
- **Distortion**: 失真量 (0.0-1.0)
- **Compression**: 壓縮量 (0.0-1.0)

#### 🎛️ EQ均衡器
- **EQ Bass**: 低頻調整 (-1.0 到 +1.0)
- **EQ Mid**: 中頻調整 (-1.0 到 +1.0)
- **EQ Treble**: 高頻調整 (-1.0 到 +1.0)

#### 📈 輸出控制
- **Effect Blend**: 效果混合比例 (0.0-1.0)
- **Output Volume**: 輸出音量 (-20dB 到 +20dB)

## 🚀 快速開始工作流程

### 基礎語音合成工作流程
```
[文字輸入] → [Geeky Kokoro TTS] → [音頻輸出]
```

### 語音修改工作流程
```
[文字輸入] → [Geeky Kokoro TTS] → [Geeky Kokoro Voice Mod] → [音頻輸出]
```

### 常用預設配置

#### 男聲轉女聲
```
Pitch Shift: +4 to +6
Formant Shift: +2 to +3
```

#### 機器人聲音
```
Voice Profile: Robot
Profile Intensity: 0.7
```

#### 電影旁白聲音
```
Voice Profile: Cinematic
Reverb Amount: 0.3
EQ Bass: +0.2
```

## 🔍 故障排除

### 常見問題

1. **模型文件未找到**
   - 確保 `kokoro-v1.0.onnx` 和 `voices-v1.0.bin` 在正確目錄
   - 檢查文件大小是否正確

2. **節點無法載入**
   - 重啟ComfyUI
   - 檢查 `requirements.txt` 是否正確安裝

3. **音頻處理失敗**
   - 確保 librosa 和 resampy 已安裝
   - 檢查音頻輸入格式

### 測試連接

啟動ComfyUI後，如果在節點列表中看到 "Geeky Kokoro TTS" 分類，說明安裝成功。

## 🔗 與現有系統整合

您的防禦系統 (`services/voice_mod_service.py`) 與ComfyUI使用相同的核心技術：
- 相同的Kokoro TTS引擎
- 相同的語音修改算法
- 兼容的音頻處理流程

可以在兩個系統間共享配置和效果參數。

## 🎯 下一步

1. 下載模型文件
2. 啟動ComfyUI: `python main.py`
3. 瀏覽器開啟: http://127.0.0.1:8188
4. 添加 Geeky Kokoro Voice Mod 節點
5. 開始調整語音參數！

享受您的語音修改界面！ 🎵✨ 