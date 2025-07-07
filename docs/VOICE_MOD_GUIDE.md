# 語音修改功能使用指南

## 概述

此防禦系統現已集成了強大的語音修改功能，基於 [ComfyUI-Geeky-Kokoro-TTS](https://github.com/GeekyGhost/ComfyUI-Geeky-Kokoro-TTS) 項目的實現。您可以對TTS語音進行各種修改，包括音調調整、音色變換、音頻效果等。

## ✨ 主要功能

### 🎛️ 音調調整 (Pitch Adjustment)
- **範圍**: -12.0 到 +12.0 半音
- **效果**: 改變聲音的高低音調
- **用途**: 男聲轉女聲、女聲轉男聲等

### 🎭 音色變換 (Formant Shift)
- **範圍**: -5.0 到 +5.0
- **效果**: 改變聲道特徵，模擬不同年齡/性別
- **用途**: 成人聲轉兒童聲、調整聲音特色

### 🎪 語音配置文件
- **Robot**: 機器人聲音
- **Cinematic**: 電影預告片深沉聲音
- **Monster**: 怪物/反派聲音
- **Singer**: 歌唱優化聲音
- **Child**: 兒童聲音
- **Darth Vader**: 黑武士風格聲音
- **Broadcast**: 廣播/專業播音聲音

### 🔊 音頻效果
- **Reverb**: 混響效果
- **Echo**: 回聲效果
- **Distortion**: 失真效果
- **Compression**: 動態壓縮
- **EQ**: 三段均衡器 (低頻/中頻/高頻)

## 📋 配置檔案

語音修改設定儲存在 `voice_mod_config.txt` 檔案中：

```ini
# 語音修改配置檔案

# 總開關
voice_mod_enabled=true

# 語音配置文件模式 (推薦使用預設配置)
voice_profile=None
profile_intensity=0.7
manual_mode=false

# 全局效果設定
effect_blend=1.0
output_volume=0.0

# 手動模式設定 (當 manual_mode=true 時生效)
# 音調調整：正值提高音調，負值降低音調
pitch_shift=0.0

# 音色調整：正值更像小孩，負值更像成人
formant_shift=0.0

# 空間效果
reverb_amount=0.0
echo_delay=0.0

# 音色效果
distortion=0.0
compression=0.0

# EQ 均衡器
eq_bass=0.0
eq_mid=0.0
eq_treble=0.0
```

## 🚀 快速開始

### 1. 啟用語音修改功能
```ini
voice_mod_enabled=true
```

### 2. 選擇模式

#### 方法A: 使用預設配置文件 (推薦)
```ini
manual_mode=false
voice_profile=Robot
profile_intensity=0.6
```

#### 方法B: 手動調整
```ini
manual_mode=true
pitch_shift=3.0
formant_shift=1.0
```

### 3. 測試功能
```bash
python test_voice_mod.py quick
```

## 🎯 常用範例

### 男聲轉女聲
```ini
voice_mod_enabled=true
manual_mode=true
pitch_shift=4.0
formant_shift=2.0
eq_treble=0.2
effect_blend=0.8
```

### 女聲轉男聲
```ini
voice_mod_enabled=true
manual_mode=true
pitch_shift=-4.0
formant_shift=-2.0
eq_bass=0.3
effect_blend=0.8
```

### 機器人聲音
```ini
voice_mod_enabled=true
manual_mode=false
voice_profile=Robot
profile_intensity=0.6
```

### 電影預告風格
```ini
voice_mod_enabled=true
manual_mode=false
voice_profile=Cinematic
profile_intensity=0.7
```

### 廣播主持人聲音
```ini
voice_mod_enabled=true
manual_mode=true
compression=0.7
eq_bass=0.2
eq_mid=0.4
eq_treble=-0.1
```

## ⚙️ 進階設定

### 效果混合
- `effect_blend=1.0`: 100% 應用效果
- `effect_blend=0.5`: 50% 原聲 + 50% 效果
- `effect_blend=0.0`: 100% 原聲（無效果）

### 音量調整
- `output_volume=0.0`: 原始音量
- `output_volume=3.0`: 增加 3dB
- `output_volume=-6.0`: 降低 6dB

### 配置文件強度
- `profile_intensity=1.0`: 最大強度
- `profile_intensity=0.5`: 中等強度
- `profile_intensity=0.3`: 輕微效果

## 🔧 測試工具

### 基本測試
```bash
python test_voice_mod.py quick
```

### 完整測試套件
```bash
python test_voice_mod.py
```

### 特定功能測試
```bash
python test_voice_mod.py pitch      # 音調測試
python test_voice_mod.py profiles   # 配置文件測試
python test_voice_mod.py preset     # 預設配置測試
python test_voice_mod.py effects    # 音頻效果測試
```

### 詳細調試
```bash
python test_voice_mod_debug.py
```

## 📊 參數建議範圍

| 參數 | 建議範圍 | 說明 |
|------|----------|------|
| pitch_shift | ±2.0 | 日常使用的溫和調整 |
| pitch_shift | ±6.0 | 性別轉換的明顯效果 |
| formant_shift | ±1.0 | 搭配音調使用 |
| reverb_amount | 0.1-0.4 | 適度的空間感 |
| compression | 0.3-0.7 | 專業音質 |
| eq_* | ±0.3 | 微調音色 |

## ⚠️ 注意事項

1. **效果強度**: 建議從較小的值開始測試，逐漸增加
2. **音質**: 過度的效果可能影響語音清晰度
3. **性能**: librosa 和 resampy 庫可提供更好的音質，但不是必需的
4. **實時性**: 語音修改會增加一些處理時間
5. **音量**: 避免 output_volume 超過 ±10dB 以防失真

## 🔍 故障排除

### 語音修改沒有效果
1. 檢查 `voice_mod_enabled=true`
2. 確認參數值不為0
3. 檢查 `effect_blend` 不為0

### 音質不佳
1. 安裝高品質音頻庫: `pip install librosa resampy`
2. 減少效果強度
3. 調整 `profile_intensity` 到較低值

### 性能問題
1. 減少同時使用的效果數量
2. 降低效果強度
3. 使用預設配置文件而非手動模式

## 📚 更多資源

- [原始項目](https://github.com/GeekyGhost/ComfyUI-Geeky-Kokoro-TTS)
- [Kokoro TTS 文檔](https://github.com/hexgrad/Kokoro-82M)
- 系統日誌中的詳細錯誤信息
- `test_voice_mod_debug.py` 提供的診斷信息

## 🎉 享受您的語音修改體驗！

現在您可以讓防禦系統使用各種不同的聲音進行警告和互動，從專業的廣播聲音到有趣的機器人聲音，甚至是神秘的電影反派聲音！ 