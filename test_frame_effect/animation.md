# 🎯 人臉檢測動畫系統詳細說明

## 📋 系統概述

本人臉檢測動畫系統採用四階段漸進式動畫，在檢測到人臉時逐步顯示瞄準框效果。系統結合穩定的人臉檢測演算法與可自訂的動畫參數，提供流暢且專業的視覺效果。

## 🎨 動畫四階段詳細說明

### 階段1：外框角落線條出現 (40幅畫面)
**視覺效果：**
- 在人臉位置出現四個角落的L型線條
- 線條從無到有漸進出現
- 形成一個瞄準框的基本輪廓

**技術實現：**
```python
# 外框尺寸逐漸增長
self.outside_w += (self.target_w - self.outside_w) * outside_smooth
self.outside_h += (self.target_h - self.outside_h) * outside_smooth

# 繪製四個角落的L型線條
cv2.line(frame, 角落起點, 角落終點, color, line_thickness)
```

**可調參數：**
- `state1_duration`: 持續時間 (預設40幅畫面)
- `outside_smooth`: 外框增長平滑度 (預設0.12)
- `corner_length_ratio`: 角落線條長度比例 (預設0.07)
- `line_thickness`: 線條粗細 (預設1)

### 階段2：內框半透明區域出現 (40幅畫面)
**視覺效果：**
- 在角落線條內側出現半透明填充區域
- 保持階段1的角落線條效果
- 增強瞄準框的立體感

**技術實現：**
```python
# 內框尺寸逐漸增長
self.w += (self.target_w - self.w) * inner_smooth
self.h += (self.target_h - self.h) * inner_smooth

# 建立半透明覆蓋層
overlay = frame.copy()
cv2.rectangle(overlay, 內框範圍, color, -1)
cv2.addWeighted(overlay, inner_alpha, frame, 1 - inner_alpha, 0, frame)
```

**可調參數：**
- `state2_duration`: 持續時間 (預設40幅畫面)
- `inner_smooth`: 內框增長平滑度 (預設0.1)
- `inner_alpha`: 內框透明度 (預設50, 範圍0-255)
- `inner_size_ratio`: 內框相對於外框的尺寸比例 (預設0.9)

### 階段3：十字準星開始延伸 (20幅畫面)
**視覺效果：**
- 從中心點開始延伸十字準星線條
- 保持前兩階段的所有視覺效果
- 十字線從短逐漸變長

**技術實現：**
```python
# 十字線起始部分逐漸延伸
self.start_line += (1 - self.start_line) * cross_start_smooth

# 繪製四個方向的十字線
cv2.line(frame, 中心點, start_line終點, color, line_thickness)
```

**可調參數：**
- `state3_duration`: 持續時間 (預設20幅畫面)
- `cross_start_smooth`: 十字線起始延伸平滑度 (預設0.08)
- `cross_length_ratio_h`: 十字線垂直長度比例 (預設0.59)
- `cross_length_ratio_w`: 十字線水平長度比例 (預設0.55)

### 階段4：十字準星完全延伸 (30幅畫面)
**視覺效果：**
- 十字準星線條完全延伸到邊緣
- 形成完整的瞄準鏡效果
- 所有動畫元素都達到最終狀態

**技術實現：**
```python
# 十字線終端部分延伸完成
self.end_line += (1 - self.end_line) * cross_end_smooth

# 繪製完整的十字準星
cv2.line(frame, start_line終點, end_line終點, color, line_thickness)
```

**可調參數：**
- `state4_duration`: 持續時間 (預設30幅畫面)
- `cross_end_smooth`: 十字線終端延伸平滑度 (預設0.12)

## ⚙️ 核心運行邏輯

### 🔄 動畫狀態管理
```python
# 累積式狀態系統 - 保持先前階段效果
if self.state >= 1:  # 階段1及以後
    # 繪製角落線條
if self.state >= 2:  # 階段2及以後  
    # 繪製角落線條 + 內框
if self.state >= 3:  # 階段3及以後
    # 繪製角落線條 + 內框 + 十字線起始
if self.state >= 4:  # 階段4
    # 繪製所有效果 + 完整十字線
```

### 📏 尺寸計算邏輯
```python
# 檢測框自動放大1.5倍
self.target_w = detected_width * 1.5
self.target_h = detected_height * 1.5

# 平滑追蹤目標位置
self.x += (self.target_x - self.x) * position_smooth
self.y += (self.target_y - self.y) * position_smooth
```

### 🎯 人臉檢測穩定化
```python
# 加權平均濾波 (最近5幅畫面)
weights = [0.4, 0.3, 0.2, 0.1]  # 新幅畫面權重更高
smoothed_position = weighted_average(face_history, weights)

# 智慧容錯機制
if face_lost_count <= max_lost_frames:
    return stable_face  # 使用歷史位置
```

## 🛠️ 設定檔參數詳解

### [BASIC] 基本動畫參數
| 參數 | 說明 | 預設值 | 範圍 |
|------|------|--------|------|
| `position_smooth` | 位置追蹤平滑度 | 0.08 | 0.01-1.0 |
| `state1_duration` | 階段1持續幅畫面數 | 40 | 10-100 |
| `state2_duration` | 階段2持續幅畫面數 | 40 | 10-100 |
| `state3_duration` | 階段3持續幅畫面數 | 20 | 5-50 |
| `state4_duration` | 階段4持續幅畫面數 | 30 | 10-80 |

### [VISUAL] 視覺效果參數
| 參數 | 說明 | 預設值 | 範圍 |
|------|------|--------|------|
| `color_r` | 紅色分量 | 255 | 0-255 |
| `color_g` | 綠色分量 | 255 | 0-255 |
| `color_b` | 藍色分量 | 255 | 0-255 |
| `flicker_probability` | 閃爍機率 | 0.2 | 0.0-1.0 |

### [STATE1-4] 各階段專屬參數
| 參數 | 說明 | 預設值 | 範圍 |
|------|------|--------|------|
| `outside_smooth` | 外框變化平滑度 | 0.12 | 0.01-1.0 |
| `inner_smooth` | 內框變化平滑度 | 0.1 | 0.01-1.0 |
| `cross_start_smooth` | 十字線起始平滑度 | 0.08 | 0.01-0.5 |
| `cross_end_smooth` | 十字線結束平滑度 | 0.12 | 0.01-0.5 |
| `corner_length_ratio` | 角落線條長度比例 | 0.07 | 0.01-0.5 |
| `line_thickness` | 線條粗細 | 1 | 1-10 |
| `inner_alpha` | 內框透明度 | 50 | 0-255 |
| `inner_size_ratio` | 內框尺寸比例 | 0.9 | 0.1-1.0 |

## 🔧 人臉檢測演算法

### 檢測優化策略
1. **高斯模糊預處理** - 減少雜訊干擾
2. **嚴格檢測參數** - scaleFactor=1.05, minNeighbors=6
3. **尺寸限制** - minSize=(30,30), maxSize=(300,300)
4. **單臉模式** - 只保留最大面積的人臉

### 平滑化處理
1. **歷史記錄** - 保存最近5幅畫面的檢測結果
2. **加權平均** - 新幅畫面權重較高
3. **智慧預測** - 短時間丟失使用歷史位置
4. **容錯機制** - 允許最多10幅畫面的檢測失敗

### 狀態監控
- **"Face: Stable (1)"** - 檢測穩定
- **"Face: Detected (1)"** - 剛檢測到
- **"Face: Lost (3/10)"** - 暫時丟失，容錯中
- **"Face: Searching..."** - 搜尋人臉中

## 📈 效能優化

### 處理策略
- **降解析度檢測** - 640x360處理，提升速度
- **適中檢測頻率** - 30FPS平衡效能與穩定性
- **非阻塞佇列** - 智慧幅畫面管理
- **純OpenCV渲染** - 硬體加速圖形處理

### 記憶體管理
- **智慧垃圾回收** - 定期清理暫存變數
- **歷史記錄限制** - 只保留必要的5幅畫面
- **單執行緒檢測** - 減少執行緒切換開銷

## 🎮 操作說明

### 鍵盤控制
- **L** - 新增左側訓練資料
- **R** - 新增右側訓練資料  
- **Q** - 退出程式

### 即時調整
1. 編輯 `anim_config.txt`
2. 儲存檔案
3. 下次檢測到人臉時自動應用新設定

## 💡 自訂建議

### 提升穩定性
- 降低 `position_smooth` (0.05-0.08)
- 增加各階段 `duration` 
- 降低各種 `smooth` 參數

### 提升反應速度  
- 提高 `position_smooth` (0.15-0.25)
- 減少各階段 `duration`
- 提高各種 `smooth` 參數

### 視覺效果調整
- 修改 `color_r/g/b` 改變顏色
- 調整 `line_thickness` 改變線條粗細
- 修改 `inner_alpha` 調整透明度
- 調整 `corner_length_ratio` 改變角落長度

---

**這個動畫系統提供了專業級的人臉檢測視覺效果，所有參數都可以即時調整！** 🎯✨ 