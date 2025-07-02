# 防禦偵測系統 v2

即時人臉偵測系統，整合 AI 分析與 Arduino 控制，支援 Mac 和 Windows 平台。

## 系統特色

- 🎯 **高效能人臉偵測**：使用 MediaPipe 實現 30+ FPS 即時偵測
- 🤖 **雙模型 AI 分析**：圖像識別 + 策略生成（可選）
- 🎮 **Arduino 整合**：自動化物理回饋控制
- 🖼️ **動態視覺效果**：偵測動畫、淡入淡出、打字機字幕
- 💻 **跨平台支援**：Mac 和 Windows 雙平台執行
- 🚀 **簡易啟動**：雙擊執行，無需命令列

## 系統需求

### 軟體需求
- Python 3.8 或以上
- Ollama（選配，用於 AI 功能）
- 網路攝影機（建議 1080p 或以上）

### 硬體需求
- 作業系統：macOS 10.15+ 或 Windows 10/11
- 記憶體：8GB RAM（建議 16GB）
- Arduino Uno/Mega（選配）

## 快速開始

### Mac 用戶

1. **下載專案**
   ```bash
   git clone [專案網址]
   cd project_v2
   ```

2. **設定執行權限**
   ```bash
   chmod +x st_mac.command
   ```

3. **雙擊執行**
   - 在 Finder 中找到 `st_mac.command`
   - 雙擊執行
   - 首次執行會自動安裝相依套件

### Windows 用戶

1. **下載專案並解壓縮**

2. **方法一：使用批次檔**
   - 雙擊 `start_windows.bat`
   - 首次執行會自動建立虛擬環境並安裝套件

3. **方法二：使用執行檔**
   ```cmd
   python build_windows.py
   ```
   - 選擇 'y' 建立 .exe 檔案
   - 執行 `dist/DefenseDetectionSystem.exe`

## 設定檔案說明

### period_config.csv
控制系統各階段的時間設定：
- `detect_duration`：人臉偵測觸發時間（秒）
- `screenshot_fade_in`：截圖淡入時間
- `caption_typing_speed`：字幕打字速度（毫秒/字）
- `cooldown_time`：系統重置冷卻時間

### weapon_config.csv
定義武器資訊與控制參數：
- 武器編號、名稱、圖片路徑
- Arduino 腳位編號
- 控制時序（延遲、HIGH 時間、等待時間）
- 顯示效果時間（淡入、顯示、淡出）

### prompt_config.txt
AI 分析的提示詞模板，可自訂分析邏輯

## 目錄結構

```
project_v2/
├── st_mac.command          # Mac 啟動檔
├── start_windows.bat       # Windows 批次檔
├── main.py                 # 主程式
├── requirements.txt        # Python 套件清單
├── period_config.csv       # 時間設定
├── weapon_config.csv       # 武器設定
├── prompt_config.txt       # AI 提示詞
├── core/                   # 核心功能
├── ui/                     # 使用者介面
├── services/               # 服務模組
├── utils/                  # 工具函式
├── fonts/                  # 字型檔案
├── webcam-shots/          # 截圖儲存
└── weapons_img/           # 武器圖片
```

## 使用教學

### 啟動系統

1. **相機選擇**：啟動時選擇要使用的網路攝影機
2. **Arduino 設定**：選擇串口（選配）
3. **模式選擇**：
   - 全螢幕模式
   - Debug 模式（顯示系統狀態）
   - No LLM 模式（跳過 AI 分析）

### 運作流程

1. **偵測階段**：系統持續偵測人臉
2. **觸發擷取**：偵測到人臉 3 秒後自動擷取畫面
3. **AI 分析**：分析圖像並生成防禦策略（可跳過）
4. **顯示結果**：顯示截圖、字幕與武器圖片
5. **物理回饋**：控制 Arduino 執行對應動作
6. **系統重置**：冷卻後返回偵測狀態

## AI 功能設定

### 安裝 Ollama

1. 前往 [Ollama 官網](https://ollama.ai) 下載安裝
2. 安裝所需模型：
   ```bash
   ollama pull llava
   ollama pull yi:9b-q4_K_M
   ```

### No LLM 模式

如果不使用 AI 功能，可在啟動時勾選「No LLM 模式」，系統將：
- 跳過圖像分析階段
- 使用預設防禦策略
- 自動選擇武器 01 和 02

## Arduino 整合

### 接線說明

- 數位腳位 2-13：連接到繼電器或 LED
- GND：共地連接

### 控制邏輯

1. 所有腳位預設為 LOW
2. 觸發時按照設定順序執行：
   - 等待前延遲
   - 設定為 HIGH
   - 維持指定時間
   - 恢復為 LOW
   - 等待後延遲

### Arduino 程式碼範例

```cpp
void setup() {
  Serial.begin(9600);
  for(int i = 2; i <= 13; i++) {
    pinMode(i, OUTPUT);
    digitalWrite(i, LOW);
  }
}

void loop() {
  if(Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    char action = cmd.charAt(0);
    int pin = cmd.substring(1).toInt();
    
    if(action == 'H') {
      digitalWrite(pin, HIGH);
    } else if(action == 'L') {
      digitalWrite(pin, LOW);
    }
  }
}
```

## 故障排除

### 相機無法開啟
- **Mac**：檢查系統偏好設定 > 安全性與隱私 > 相機權限
- **Windows**：檢查隱私設定 > 相機存取權

### 找不到 Arduino
- 確認 Arduino 已正確連接
- 安裝對應的驅動程式
- 檢查串口是否被其他程式佔用

### AI 分析失敗
- 確認 Ollama 已安裝並執行中
- 檢查是否已下載所需模型
- 可使用 No LLM 模式跳過 AI 功能

### 中文顯示問題
- 確認 `fonts/NotoSansCJKtc-Regular.otf` 檔案存在
- 系統會自動使用平台預設中文字型作為備援

## 進階設定

### 自訂武器

1. 準備武器圖片（建議 PNG 格式，透明背景）
2. 放入 `weapons_img/` 目錄
3. 編輯 `weapon_config.csv` 新增武器資訊
4. 重新啟動系統

### 調整時間參數

編輯 `period_config.csv` 可調整：
- 偵測靈敏度
- 動畫速度
- 顯示時間
- 系統反應速度

### 自訂 AI 提示詞

編輯 `prompt_config.txt` 可自訂：
- 分析重點
- 回應格式
- 武器選擇邏輯

## 開發者資訊

### 建置開發環境

```bash
# 建立虛擬環境
python -m venv venv

# 啟動虛擬環境
# Mac/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 安裝開發套件
pip install -r requirements.txt
```

### 程式架構

- **狀態機模式**：管理系統運作流程
- **多執行緒**：相機、AI、Arduino 獨立執行緒
- **信號槽機制**：元件間通訊使用 PyQt6 信號
- **模組化設計**：核心、UI、服務分離

## 授權資訊

本專案採用 MIT 授權條款

## 聯絡資訊

如有問題或建議，請透過 GitHub Issues 回報。