# Location: project_v2/test_voice_mod.py
# Usage: 測試語音修改功能，包括 pitch adjustment 等效果

import sys
import time
from utils.voice_mod_config_loader import VoiceModConfigLoader
from services.tts_service import TTSService

def test_basic_tts():
    """測試基礎TTS功能（無語音修改）"""
    print("🎯 測試基礎TTS功能...")
    
    # 先禁用語音修改
    config = VoiceModConfigLoader()
    config.enable_voice_mod(False)
    
    tts = TTSService(enabled=True)
    if not tts.is_available():
        print("❌ TTS服務不可用")
        return False
    
    test_text = "Hello, this is a basic TTS test without voice modification."
    print(f"播放文本: {test_text}")
    
    tts.speak_text(test_text)
    time.sleep(5)  # 等待播放完成
    
    tts.shutdown()
    print("✅ 基礎TTS測試完成")
    return True

def test_pitch_adjustment():
    """測試音調調整功能"""
    print("\n🎯 測試音調調整功能...")
    
    config = VoiceModConfigLoader()
    
    # 測試提高音調
    print("📈 測試提高音調 (+3 semitones)...")
    config.update_voice_mod_settings({
        'voice_mod_enabled': True,
        'manual_mode': True,
        'pitch_shift': 3.0,
        'formant_shift': 0.0,
        'effect_blend': 1.0,
        'output_volume': 0.0
    })
    
    tts = TTSService(enabled=True)
    if not tts.is_available():
        print("❌ TTS服務不可用")
        return False
    
    test_text = "This voice has been pitched up by 3 semitones."
    print(f"播放文本: {test_text}")
    tts.speak_text(test_text)
    time.sleep(6)
    
    # 測試降低音調
    print("📉 測試降低音調 (-3 semitones)...")
    config.update_voice_mod_settings({
        'pitch_shift': -3.0,
    })
    
    # 重新初始化以載入新設定
    tts.shutdown()
    time.sleep(1)
    
    tts = TTSService(enabled=True)
    test_text = "This voice has been pitched down by 3 semitones."
    print(f"播放文本: {test_text}")
    tts.speak_text(test_text)
    time.sleep(6)
    
    tts.shutdown()
    print("✅ 音調調整測試完成")
    return True

def test_voice_profiles():
    """測試語音配置文件"""
    print("\n🎯 測試語音配置文件...")
    
    config = VoiceModConfigLoader()
    
    # 測試機器人聲音
    print("🤖 測試機器人聲音...")
    config.update_voice_mod_settings({
        'voice_mod_enabled': True,
        'manual_mode': False,
        'voice_profile': 'Robot',
        'profile_intensity': 0.6,
        'effect_blend': 1.0
    })
    
    tts = TTSService(enabled=True)
    if not tts.is_available():
        print("❌ TTS服務不可用")
        return False
    
    test_text = "I am a robot voice. This is how I sound."
    print(f"播放文本: {test_text}")
    tts.speak_text(test_text)
    time.sleep(6)
    
    # 測試電影聲音
    print("🎬 測試電影聲音...")
    config.update_voice_mod_settings({
        'voice_profile': 'Cinematic',
        'profile_intensity': 0.7
    })
    
    tts.shutdown()
    time.sleep(1)
    
    tts = TTSService(enabled=True)
    test_text = "This is a deep, cinematic voice for movie trailers."
    print(f"播放文本: {test_text}")
    tts.speak_text(test_text)
    time.sleep(6)
    
    tts.shutdown()
    print("✅ 語音配置文件測試完成")
    return True

def test_preset_configurations():
    """測試預設配置"""
    print("\n🎯 測試預設配置...")
    
    config = VoiceModConfigLoader()
    presets = config.get_preset_configurations()
    
    print(f"可用預設: {list(presets.keys())}")
    
    # 測試男轉女聲
    print("👩 測試男轉女聲預設...")
    success = config.apply_preset("Pitch Up (Male to Female)")
    if not success:
        print("❌ 預設應用失敗")
        return False
    
    tts = TTSService(enabled=True)
    if not tts.is_available():
        print("❌ TTS服務不可用")
        return False
    
    test_text = "This male voice is being converted to sound more feminine."
    print(f"播放文本: {test_text}")
    tts.speak_text(test_text)
    time.sleep(6)
    
    tts.shutdown()
    print("✅ 預設配置測試完成")
    return True

def test_manual_effects():
    """測試手動音頻效果"""
    print("\n🎯 測試手動音頻效果...")
    
    config = VoiceModConfigLoader()
    
    # 測試混響效果
    print("🔊 測試混響效果...")
    config.update_voice_mod_settings({
        'voice_mod_enabled': True,
        'manual_mode': True,
        'pitch_shift': 0.0,
        'formant_shift': 0.0,
        'reverb_amount': 0.5,
        'compression': 0.3,
        'eq_mid': 0.2,
        'effect_blend': 1.0
    })
    
    tts = TTSService(enabled=True)
    if not tts.is_available():
        print("❌ TTS服務不可用")
        return False
    
    test_text = "This voice has reverb and compression effects applied."
    print(f"播放文本: {test_text}")
    tts.speak_text(test_text)
    time.sleep(6)
    
    tts.shutdown()
    print("✅ 手動效果測試完成")
    return True

def run_all_tests():
    """運行所有測試"""
    print("🚀 開始語音修改功能完整測試\n")
    
    tests = [
        ("基礎TTS", test_basic_tts),
        ("音調調整", test_pitch_adjustment),
        ("語音配置文件", test_voice_profiles),
        ("預設配置", test_preset_configurations),
        ("手動效果", test_manual_effects),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 測試出錯: {e}")
            results.append((test_name, False))
    
    # 顯示測試結果摘要
    print("\n📊 測試結果摘要:")
    for test_name, success in results:
        status = "✅ 通過" if success else "❌ 失敗"
        print(f"  {test_name}: {status}")
    
    successful_tests = sum(1 for _, success in results if success)
    print(f"\n總計: {successful_tests}/{len(results)} 項測試通過")
    
    return successful_tests == len(results)

def quick_pitch_test():
    """快速音調測試"""
    print("🎯 快速音調調整測試...")
    
    config = VoiceModConfigLoader()
    config.update_voice_mod_settings({
        'voice_mod_enabled': True,
        'manual_mode': True,
        'pitch_shift': 2.0,  # 提高2個半音
        'formant_shift': 1.0,  # 稍微調整音色
        'effect_blend': 1.0
    })
    
    tts = TTSService(enabled=True)
    if not tts.is_available():
        print("❌ TTS服務不可用")
        return False
    
    test_text = "Quick pitch adjustment test. The voice should sound higher."
    print(f"播放文本: {test_text}")
    tts.speak_text(test_text)
    time.sleep(5)
    
    tts.shutdown()
    print("✅ 快速測試完成")
    return True

if __name__ == "__main__":
    print("語音修改功能測試工具")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "quick":
            quick_pitch_test()
        elif sys.argv[1] == "pitch":
            test_pitch_adjustment()
        elif sys.argv[1] == "profiles":
            test_voice_profiles()
        elif sys.argv[1] == "preset":
            test_preset_configurations()
        elif sys.argv[1] == "effects":
            test_manual_effects()
        else:
            print("可用選項: quick, pitch, profiles, preset, effects")
    else:
        run_all_tests()
    
    print("\n測試完成！") 