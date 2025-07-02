#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TTS 語音列表工具
用於查看系統中所有可用的Text-to-Speech語音
運行此腳本可以幫助你選擇合適的語音ID用於TTS_config.txt
"""

import sys
import os

# 添加項目路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    """主函數"""
    print("=" * 60)
    print("TTS 語音列表工具")
    print("=" * 60)
    
    try:
        from utils.tts_config_loader import TTSConfigLoader
        
        # 創建配置加載器
        config_loader = TTSConfigLoader()
        
        # 顯示當前配置
        print("\n當前TTS配置:")
        print(f"  啟用狀態: {config_loader.get_bool('enabled', True)}")
        print(f"  語音選擇模式: {config_loader.get_str('voice_selection_mode', 'auto')}")
        print(f"  語音速度: {config_loader.get_int('rate', 120)}")
        print(f"  音量: {config_loader.get_float('volume', 0.7)}")
        
        # 顯示所有可用語音
        config_loader.print_available_voices()
        
        # 如果配置了特定語音，顯示其信息
        preferred_voice_id = config_loader.get_str('preferred_voice_id', '')
        if preferred_voice_id:
            print(f"\n當前配置的語音ID:")
            print(f"  {preferred_voice_id}")
            
            # 檢查語音是否存在
            voices = config_loader.get_all_available_voices()
            voice_exists = any(voice['id'] == preferred_voice_id for voice in voices)
            
            if voice_exists:
                print("  ✓ 語音ID有效")
            else:
                print("  ✗ 語音ID無效或不存在")
        
        # 提供建議
        print("\n" + "=" * 60)
        print("使用建議:")
        print("1. 複製想要的語音ID到 TTS_config.txt 的 preferred_voice_id 設定中")
        print("2. 將 voice_selection_mode 設為 'manual'")
        print("3. 根據需要調整 rate (語音速度) 和 volume (音量)")
        print("4. 重新啟動程序使設定生效")
        print("=" * 60)
        
    except ImportError as e:
        print(f"錯誤: 無法導入必要模組 - {e}")
        print("請確保你在正確的項目目錄中運行此腳本")
    except Exception as e:
        print(f"錯誤: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    
    # 等待用戶按鍵後退出
    input("\n按Enter鍵退出...")
    sys.exit(exit_code) 