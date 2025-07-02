#!/usr/bin/env python3
# -*- coding: utf-8 -*-

print("TTS 測試程序 v3.0 - 支持配置文件重載")

import pyttsx3

# 測試文本
test_texts = [
    "System analysis unavailable. Activating default protocol.",
    "Target acquired. Defensive measures engaged.", 
    "Security breach detected. Initiating lockdown sequence.",
    "Warning: Unauthorized personnel detected in restricted area.",
    "Emergency defense protocol activated successfully."
]

def load_config():
    """載入TTS配置 - 直接讀取配置文件"""
    config = {
        'rate': 120,
        'volume': 0.7,
        'voice_id': 'TTS_MS_EN-US_DAVID_11.0'
    }
    
    try:
        print("正在載入 TTS_config.txt...")
        with open('TTS_config.txt', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    if key == 'rate':
                        try:
                            config['rate'] = int(value)
                        except ValueError:
                            pass
                    elif key == 'volume':
                        try:
                            config['volume'] = float(value)
                        except ValueError:
                            pass
                    elif key == 'preferred_voice_id':
                        config['voice_id'] = value
        
        print(f"配置載入成功: 速度={config['rate']}, 音量={config['volume']}")
        return config
        
    except FileNotFoundError:
        print("TTS_config.txt 不存在，使用默認配置")
        return config
    except Exception as e:
        print(f"載入配置文件時出錯: {e}，使用默認配置")
        return config

def apply_config(engine, config):
    """應用配置到TTS引擎"""
    try:
        engine.setProperty('rate', config['rate'])
        engine.setProperty('volume', config['volume'])
        
        # 設置語音
        if config['voice_id']:
            voices = engine.getProperty('voices')
            for voice in voices:
                if config['voice_id'] in voice.id:
                    engine.setProperty('voice', voice.id)
                    print(f"已設定語音: {voice.name}")
                    break
        
        print(f"TTS設定已應用: 速度={config['rate']}, 音量={config['volume']}")
        
    except Exception as e:
        print(f"應用配置時出錯: {e}")

def show_current_settings(engine):
    """顯示當前TTS設定"""
    try:
        rate = engine.getProperty('rate')
        volume = engine.getProperty('volume')
        voice_id = engine.getProperty('voice')
        
        # 獲取語音名稱
        voices = engine.getProperty('voices')
        voice_name = "未知"
        for voice in voices:
            if voice.id == voice_id:
                voice_name = voice.name
                break
        
        print(f"\n當前TTS設定:")
        print(f"  速度: {rate}")
        print(f"  音量: {volume}")
        print(f"  語音: {voice_name}")
        
    except Exception as e:
        print(f"獲取設定時出錯: {e}")

def main():
    print("初始化TTS引擎...")
    
    try:
        engine = pyttsx3.init()
        print("TTS引擎初始化成功")
        
        # 載入並應用初始配置
        config = load_config()
        apply_config(engine, config)
        
        current_index = 0
        
        while True:
            text = test_texts[current_index]
            print(f"\n{'='*60}")
            print(f"當前測試文本 ({current_index + 1}/{len(test_texts)}):")
            print(f"'{text}'")
            print("="*60)
            print("操作選項:")
            print("  Enter      - 播放當前文本")
            print("  n + Enter  - 下一個測試文本")
            print("  p + Enter  - 上一個測試文本")
            print("  r + Enter  - 重新載入配置文件")
            print("  s + Enter  - 顯示當前設定")
            print("  c + Enter  - 手動調整設定")
            print("  q + Enter  - 退出程序")
            
            choice = input("\n請選擇 > ").strip().lower()
            
            if choice == 'q':
                print("退出程序")
                break
                
            elif choice == 'n':
                current_index = (current_index + 1) % len(test_texts)
                print(f"切換到測試文本 {current_index + 1}")
                
            elif choice == 'p':
                current_index = (current_index - 1) % len(test_texts)
                print(f"切換到測試文本 {current_index + 1}")
                
            elif choice == 'r':
                # 重新載入配置文件
                print("\n重新載入配置文件...")
                config = load_config()
                apply_config(engine, config)
                
            elif choice == 's':
                # 顯示當前設定
                show_current_settings(engine)
                
            elif choice == 'c':
                # 手動調整設定
                print("\n手動調整設定:")
                try:
                    new_rate = input(f"輸入新速度 (50-300, 當前: {engine.getProperty('rate')}): ").strip()
                    if new_rate:
                        rate = int(new_rate)
                        if 50 <= rate <= 300:
                            engine.setProperty('rate', rate)
                            print(f"速度設定為: {rate}")
                        else:
                            print("速度必須在50-300之間")
                    
                    new_volume = input(f"輸入新音量 (0.0-1.0, 當前: {engine.getProperty('volume')}): ").strip()
                    if new_volume:
                        volume = float(new_volume)
                        if 0.0 <= volume <= 1.0:
                            engine.setProperty('volume', volume)
                            print(f"音量設定為: {volume}")
                        else:
                            print("音量必須在0.0-1.0之間")
                            
                except ValueError:
                    print("請輸入有效數字")
                    
            else:
                # 播放當前文本
                print(f"\n正在播放: '{text}'")
                show_current_settings(engine)
                try:
                    engine.say(text)
                    engine.runAndWait()
                    print("✓ 播放完成")
                except Exception as e:
                    print(f"✗ 播放失敗: {e}")
                    
        print("\nTTS測試程序已關閉")
        
    except Exception as e:
        print(f"TTS初始化失敗: {e}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n程序被用戶中斷")
    except Exception as e:
        print(f"程序執行出錯: {e}")
        import traceback
        traceback.print_exc() 