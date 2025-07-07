#!/usr/bin/env python3
"""
Apply ComfyUI TTS Studio Settings to Main Program
將 ComfyUI TTS Studio 的設置應用到主程序
"""
import json
import os
import sys
from pathlib import Path

# 添加項目根目錄到路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_comfyui_workflow(workflow_path):
    """載入 ComfyUI 工作流程"""
    try:
        with open(workflow_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ 載入工作流程失敗: {e}")
        return None

def extract_tts_settings(workflow_data):
    """從工作流程中提取 TTS 設置"""
    tts_config = {}
    voice_mod_config = {}
    
    try:
        for node in workflow_data.get("nodes", []):
            node_type = node.get("type", "")
            widgets_values = node.get("widgets_values", [])
            
            # 處理 GeekyKokoroTTS 節點
            if node_type == "GeekyKokoroTTS" and len(widgets_values) >= 7:
                text = widgets_values[0]
                voice = widgets_values[1]  # 🇺🇸 🚹 Onyx
                speed = widgets_values[2]
                use_gpu = widgets_values[3]
                enable_blending = widgets_values[4]
                second_voice = widgets_values[5] if len(widgets_values) > 5 else None
                blend_ratio = widgets_values[6] if len(widgets_values) > 6 else 0.5
                
                # 映射語音名稱到 Kokoro 代碼
                voice_mapping = {
                    "🇺🇸 🚹 Onyx": "am_onyx",
                    "🇺🇸 🚹 Michael": "am_michael", 
                    "🇺🇸 🚹 Adam": "am_adam",
                    "🇺🇸 🚹 Echo": "am_echo",
                    "🇺🇸 🚹 Liam": "am_liam",
                    "🇺🇸 🚹 Eric": "am_eric",
                    "🇺🇸 🚹 Fenrir": "am_fenrir",
                    "🇺🇸 🚹 Puck": "am_puck",
                    "🇺🇸 🚺 Heart ❤️": "af_heart",
                    "🇺🇸 🚺 Bella 🔥": "af_bella",
                    "🇺🇸 🚺 Nicole 🎧": "af_nicole",
                    "🇺🇸 🚺 Sarah": "af_sarah",
                    "🇺🇸 🚺 Nova": "af_nova",
                    "🇺🇸 🚺 Sky": "af_sky",
                    "🇺🇸 🚺 Alloy": "af_alloy",
                    "🇬🇧 🚺 Emma": "bf_emma",
                    "🇬🇧 🚺 Isabella": "bf_isabella",
                    "🇬🇧 🚹 George": "bm_george",
                    "🇬🇧 🚹 Lewis": "bm_lewis",
                    "🇬🇧 🚹 Daniel": "bm_daniel",
                    "🇬🇧 🚹 Fable": "bm_fable"
                }
                
                kokoro_voice = voice_mapping.get(voice, "am_onyx")
                
                # 根據語音確定語言代碼
                if kokoro_voice.startswith("am_") or kokoro_voice.startswith("af_"):
                    lang_code = "a"  # American English
                elif kokoro_voice.startswith("bm_") or kokoro_voice.startswith("bf_"):
                    lang_code = "b"  # British English
                else:
                    lang_code = "a"  # 默認美式英語
                
                tts_config.update({
                    "kokoro_lang_code": lang_code,
                    "kokoro_voice": kokoro_voice,
                    "kokoro_speed": float(speed),
                    "enabled": True,
                    "realtime_mode": True,
                    "verbose_logging": True
                })
                
                print(f"📢 TTS 設置:")
                print(f"   語音: {voice} -> {kokoro_voice}")
                print(f"   語言: {lang_code}")
                print(f"   速度: {speed}")
                print(f"   語音混合: {enable_blending}")
                
            # 處理 GeekyKokoroAdvancedVoice 節點
            elif node_type == "GeekyKokoroAdvancedVoice" and len(widgets_values) >= 15:
                effect_blend = widgets_values[0]
                output_volume = widgets_values[1]
                voice_profile = widgets_values[2]
                profile_intensity = widgets_values[3]
                manual_mode = widgets_values[4]
                pitch_shift = widgets_values[5]
                formant_shift = widgets_values[6]
                reverb_amount = widgets_values[7]
                echo_delay = widgets_values[8]
                distortion = widgets_values[9]
                compression = widgets_values[10]
                eq_bass = widgets_values[11]
                eq_mid = widgets_values[12]
                eq_treble = widgets_values[13]
                use_gpu = widgets_values[14]
                
                voice_mod_config.update({
                    "voice_mod_enabled": True,
                    "voice_profile": voice_profile,
                    "profile_intensity": float(profile_intensity),
                    "manual_mode": bool(manual_mode),
                    "effect_blend": float(effect_blend),
                    "output_volume": float(output_volume),
                    "pitch_shift": float(pitch_shift),
                    "formant_shift": float(formant_shift),
                    "reverb_amount": float(reverb_amount),
                    "echo_delay": float(echo_delay),
                    "distortion": float(distortion),
                    "compression": float(compression),
                    "eq_bass": float(eq_bass),
                    "eq_mid": float(eq_mid),
                    "eq_treble": float(eq_treble),
                    "verbose_logging": True
                })
                
                print(f"🎛️  語音修改設置:")
                print(f"   配置文件: {voice_profile}")
                print(f"   手動模式: {manual_mode}")
                print(f"   音調偏移: {pitch_shift}")
                print(f"   效果混合: {effect_blend}")
                
    except Exception as e:
        print(f"❌ 提取設置錯誤: {e}")
    
    return tts_config, voice_mod_config

def update_tts_config(tts_config):
    """更新 TTS 配置文件"""
    config_path = Path("config/tts_config.txt")
    
    try:
        # 確保配置目錄存在
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 讀取現有配置
        existing_config = {}
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        existing_config[key.strip()] = value.strip()
        
        # 合併配置
        existing_config.update(tts_config)
        
        # 寫入配置文件
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write("# ================================================================\n")
            f.write("# TTS 語音合成系統配置文件 - 由 ComfyUI Studio 同步\n")
            f.write("# ================================================================\n\n")
            
            f.write("# 基本設定\n")
            f.write(f"enabled={existing_config.get('enabled', True)}\n")
            f.write(f"realtime_mode={existing_config.get('realtime_mode', True)}\n")
            f.write(f"verbose_logging={existing_config.get('verbose_logging', True)}\n\n")
            
            f.write("# 語音設定\n")
            f.write(f"kokoro_lang_code={existing_config.get('kokoro_lang_code', 'a')}\n")
            f.write(f"kokoro_voice={existing_config.get('kokoro_voice', 'am_onyx')}\n")
            f.write(f"kokoro_speed={existing_config.get('kokoro_speed', 1.0)}\n\n")
            
            f.write("# 文字處理設定\n")
            f.write(f"min_english_chars={existing_config.get('min_english_chars', 3)}\n")
            f.write(f"auto_clean_text={existing_config.get('auto_clean_text', True)}\n")
            f.write(f"max_chunk_length={existing_config.get('max_chunk_length', 80)}\n")
            f.write(f"min_chunk_length={existing_config.get('min_chunk_length', 8)}\n\n")
            
            f.write("# 測試設定\n")
            f.write(f"test_mode={existing_config.get('test_mode', False)}\n")
            f.write(f"test_text={existing_config.get('test_text', 'Hello! This is a test of Kokoro TTS system.')}\n")
        
        print(f"✅ TTS 配置已更新: {config_path}")
        
    except Exception as e:
        print(f"❌ 更新 TTS 配置失敗: {e}")

def update_voice_mod_config(voice_mod_config):
    """更新語音修改配置文件"""
    config_path = Path("config/voice_mod_config.txt")
    
    try:
        # 確保配置目錄存在
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 讀取現有配置
        existing_config = {}
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        existing_config[key.strip()] = value.strip()
        
        # 合併配置
        existing_config.update({k: str(v) for k, v in voice_mod_config.items()})
        
        # 寫入配置文件
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write("# 語音修改配置檔案 - 由 ComfyUI Studio 同步\n")
            
            for key, value in existing_config.items():
                f.write(f"{key}={value}\n")
        
        print(f"✅ 語音修改配置已更新: {config_path}")
        
    except Exception as e:
        print(f"❌ 更新語音修改配置失敗: {e}")

def show_current_settings():
    """顯示當前應用的設置"""
    print("\n📊 當前應用的設置:")
    print("=" * 50)
    
    # 讀取 TTS 配置
    tts_config_path = Path("config/tts_config.txt")
    if tts_config_path.exists():
        print("🎤 TTS 設置:")
        try:
            with open(tts_config_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        if key.strip() in ['kokoro_voice', 'kokoro_speed', 'kokoro_lang_code', 'enabled']:
                            print(f"   {key.strip()}: {value.strip()}")
        except Exception as e:
            print(f"   讀取錯誤: {e}")
    
    # 讀取語音修改配置
    voice_mod_config_path = Path("config/voice_mod_config.txt")
    if voice_mod_config_path.exists():
        print("\n🎛️  語音修改設置:")
        try:
            with open(voice_mod_config_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        if key in ['voice_mod_enabled', 'voice_profile', 'manual_mode', 
                                 'pitch_shift', 'effect_blend', 'output_volume']:
                            print(f"   {key}: {value.strip()}")
        except Exception as e:
            print(f"   讀取錯誤: {e}")

def main():
    """主函數"""
    print("🔄 ComfyUI TTS Studio 設置應用工具")
    print("=" * 50)
    
    # 檢查工作流程文件
    workflow_path = Path("ComfyUI/workflows/tts_studio.json")
    if not workflow_path.exists():
        print(f"❌ 找不到工作流程文件: {workflow_path}")
        print("請確保已創建 TTS Studio 工作流程")
        return
    
    # 載入工作流程
    print(f"📁 載入工作流程: {workflow_path}")
    workflow_data = load_comfyui_workflow(workflow_path)
    if not workflow_data:
        return
    
    # 提取設置
    print("🔍 提取設置...")
    tts_config, voice_mod_config = extract_tts_settings(workflow_data)
    
    if not tts_config and not voice_mod_config:
        print("❌ 未找到任何 TTS 或語音修改設置")
        return
    
    # 應用設置
    print("\n📝 應用設置到主程序...")
    
    if tts_config:
        update_tts_config(tts_config)
    
    if voice_mod_config:
        update_voice_mod_config(voice_mod_config)
    
    # 顯示結果
    show_current_settings()
    
    print("\n🎉 設置應用完成！")
    print("💡 提示:")
    print("   1. 重新啟動主程序以使新設置生效")
    print("   2. 或者使用配置熱重載功能（如果支援）")
    print("   3. 可以使用語音測試功能驗證效果")

if __name__ == "__main__":
    main() 