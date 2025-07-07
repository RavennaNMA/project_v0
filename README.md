# 防禦偵測系統 v2 - Mac 版

全新升級的即時人臉偵測系統，整合 AI 分析、語音合成、語音修改與 Arduino 控制，支援 Mac 和 Windows 平台。

## 🆕 v2 新功能

- 🗣️ **Kokoro TTS 語音合成**：高品質英語語音播放，支援多種聲音選擇
- 🎵 **語音修改功能**：即時音調調整、音色變換、混響等音頻效果
- 🔗 **ComfyUI 整合**：與 ComfyUI 工作流程同步，支援即時語音效果調整
- 📁 **優化的目錄結構**：config/、scripts/、docs/ 等分類管理
- ⚡ **更好的效能**：優化的音頻處理和即時播放

## 系統特色

- 🎯 **高效能人臉偵測**：使用 MediaPipe 實現 30+ FPS 即時偵測
- 🤖 **雙模型 AI 分析**：圖像識別 + 策略生成（可選）
- 🎮 **Arduino 整合**：自動化物理回饋控制
- 🖼️ **動態視覺效果**：偵測動畫、淡入淡出、打字機字幕
- 💻 **跨平台支援**：Mac 和 Windows 雙平台執行
- 🚀 **簡易啟動**：雙擊執行，無需命令列

## 系統需求

### Mac 系統需求
- **macOS 版本**：10.15 (Catalina) 或以上
- **架構**：Intel x64 或 Apple Silicon (M1/M2/M3/M4)
- **記憶體**：最低 8GB，建議 16GB+
- **儲存空間**：最低 10GB 可用空間
- **相機**：內建或 USB 相機（系統將請求權限）
- **Python**：3.8.0 或以上（建議 3.9.x）

### 軟體需求
- Python 3.8 或以上
- Ollama（選配，用於 AI 功能）
- 網路攝影機（建議 1080p 或以上）

### 硬體需求（可選）
- Arduino Uno/Mega（用於硬體控制）

## Mac 快速安裝

### 方法一：自動安裝（推薦）

1. **下載專案**
   ```bash
   git clone https://github.com/RavennaNMA/project_v2.git
   cd project_v2
   ```

2. **雙擊執行**
   - 在 Finder 中找到 `st_mac.command`
   - 雙擊執行（首次執行會自動安裝所有依賴）

### 方法二：手動安裝

1. **檢查 Python**
   ```bash
   python3 --version
   # 應該顯示 3.8.0 或以上版本
   ```

2. **建立虛擬環境**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **安裝依賴項**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **特別適配 Apple Silicon**
   ```bash
   # 如果您使用 M1/M2/M3/M4 Mac
   pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
   ```

5. **啟動系統**
   ```bash
   python main.py
   ```

## 🎵 新功能使用指南

### Kokoro TTS 語音系統

新版本使用 Kokoro TTS 引擎提供高品質語音合成：

- **多種語音選擇**：支援美式、英式英語等多種聲音
- **即時播放**：邊合成邊播放，低延遲響應
- **智能分段**：自動優化文字分割，保持語句自然度

配置文件：`config/tts_config.txt`

### 語音修改功能

提供豐富的音頻效果：

- **音調調整**：-12 到 +12 半音範圍
- **音色變換**：模擬不同的聲道形狀
- **音頻效果**：混響、回聲、壓縮、失真等
- **預設配置**：Cinematic、Monster、Robot 等效果

配置文件：`config/voice_mod_config.txt`

### ComfyUI 整合

- **即時同步**：與 ComfyUI 工作流程聯動
- **參數同步**：語音效果參數可從 ComfyUI 即時調整
- **WebSocket 通信**：穩定的即時通信

## 配置文件說明

### config/period_config.csv
控制系統各階段的時間設定

### config/weapon_config.csv  
定義武器資訊與控制參數

### config/tts_config.txt
TTS 語音合成詳細設定

### config/voice_mod_config.txt
語音修改效果配置

### config/prompt_config.txt
AI 分析的提示詞模板

## 目錄結構

```
project_v2/
├── st_mac.command          # Mac 啟動檔（根目錄）
├── main.py                 # 主程式
├── requirements.txt        # Python 套件清單
├── config/                 # 配置文件目錄
│   ├── period_config.csv   # 時間設定
│   ├── weapon_config.csv   # 武器設定
│   ├── tts_config.txt      # TTS 設定
│   ├── voice_mod_config.txt # 語音修改設定
│   └── prompt_config.txt   # AI 提示詞
├── scripts/                # 腳本目錄
│   ├── st_mac.command      # Mac 主啟動腳本
│   └── start_windows.bat   # Windows 啟動腳本
├── core/                   # 核心功能
├── ui/                     # 使用者介面
├── services/               # 服務模組
├── utils/                  # 工具函式
├── fonts/                  # 字型檔案
├── webcam-shots/          # 截圖儲存
└── weapons_img/           # 武器圖片
```

## 常見問題解決

### 相機權限問題
```bash
# Mac 系統偏好設定 → 安全性與隱私 → 相機
# 勾選 Terminal 和 Python
```

### 音頻相關問題
```bash
# 安裝額外的音頻庫（可選）
brew install portaudio ffmpeg
```

### Kokoro TTS 載入緩慢
首次使用時 Kokoro 需要下載語言模型，請耐心等待

### Apple Silicon 優化
系統已針對 M1/M2/M3/M4 晶片進行優化，會自動使用 CPU 版本的 PyTorch

## 效能優化建議

### 針對 Apple Silicon Mac
- 使用優化版本的 PyTorch
- 確保有足夠的記憶體（建議 16GB+）

### 記憶體管理
- 關閉不必要的應用程式
- 在活動監視器中監控系統資源

## 開發與除錯

### 啟用 Debug 模式
啟動時勾選「Debug 模式」可查看詳細系統狀態

### 檢查系統相依性
```bash
python -c "from services.platform_service import PlatformService; print(PlatformService().check_dependencies())"
```

### 查看系統資訊
```bash
python -c "from services.platform_service import PlatformService; import pprint; pprint.pprint(PlatformService().get_platform_info())"
```

## 更新日誌

### v2.0.0
- 🆕 新增 Kokoro TTS 高品質語音合成
- 🆕 新增語音修改功能，支援多種音頻效果
- 🆕 新增 ComfyUI 整合與即時同步
- 🔧 重構目錄結構，配置文件集中管理
- 🍎 優化 Mac 平台相容性，支援 Apple Silicon
- ⚡ 改善音頻處理效能與即時播放
- 📝 完善文檔與配置說明

### v1.x
- 基礎人臉偵測系統
- AI 圖像分析功能
- Arduino 硬體控制

## 技術支援

如有問題，請檢查：
1. 系統需求是否滿足
2. 虛擬環境是否正確安裝
3. 相機權限是否已授予
4. 依賴項是否完全安裝

對於技術問題，可透過 GitHub Issues 回報。