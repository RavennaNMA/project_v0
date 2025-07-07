# Location: project_v2/test_voice_mod_debug.py
# Usage: 詳細的語音修改調試測試

import time
from utils.voice_mod_config_loader import VoiceModConfigLoader
from services.voice_mod_service import VoiceModService
import numpy as np

def test_voice_mod_service_directly():
    """直接測試語音修改服務"""
    print("🔧 直接測試語音修改服務...")
    
    # 創建語音修改服務
    voice_mod = VoiceModService(sample_rate=24000)
    
    # 測試配置
    settings = {
        'manual_mode': True,
        'pitch_shift': 3.0,
        'formant_shift': 1.0,
        'effect_blend': 1.0,
        'output_volume': 0.0
    }
    
    voice_mod.update_settings(settings)
    print(f"📋 應用設定: {settings}")
    
    # 創建測試音頻數據
    sample_rate = 24000
    duration = 1.0  # 1秒
    frequency = 440  # A4音符
    
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    test_audio = 0.3 * np.sin(2 * np.pi * frequency * t)
    
    print(f"🎵 生成測試音頻: {len(test_audio)} 個樣本, 頻率 {frequency}Hz")
    
    # 應用語音修改
    try:
        processed_audio = voice_mod.process_audio(test_audio)
        print(f"✅ 語音修改處理成功")
        print(f"📊 原始音頻範圍: {test_audio.min():.3f} 到 {test_audio.max():.3f}")
        print(f"📊 處理後範圍: {processed_audio.min():.3f} 到 {processed_audio.max():.3f}")
        
        # 檢查是否有變化
        if np.allclose(test_audio, processed_audio, rtol=1e-3):
            print("⚠️ 警告: 音頻數據似乎沒有變化")
        else:
            print("✅ 音頻已被修改")
            
        return True
    except Exception as e:
        print(f"❌ 語音修改處理失敗: {e}")
        return False

def test_config_and_dependencies():
    """測試配置和依賴項"""
    print("\n🔍 檢查配置和依賴項...")
    
    # 檢查配置載入器
    try:
        config = VoiceModConfigLoader()
        print("✅ 語音修改配置載入器正常")
        
        settings = config.get_voice_mod_settings()
        print(f"📋 當前設定: {settings}")
        
        if settings['voice_mod_enabled']:
            print("✅ 語音修改已啟用")
        else:
            print("⚠️ 語音修改已禁用")
            
    except Exception as e:
        print(f"❌ 配置載入器錯誤: {e}")
        return False
    
    # 檢查依賴庫
    try:
        import librosa
        print("✅ librosa 可用")
    except ImportError:
        print("⚠️ librosa 不可用，將使用基礎實現")
    
    try:
        import resampy
        print("✅ resampy 可用")
    except ImportError:
        print("⚠️ resampy 不可用，將使用基礎實現")
    
    try:
        from scipy import signal
        print("✅ scipy 可用")
    except ImportError:
        print("⚠️ scipy 不可用，某些效果可能不可用")
    
    return True

def test_tts_voice_mod_integration():
    """測試TTS與語音修改的整合"""
    print("\n🔗 測試TTS與語音修改整合...")
    
    # 先配置語音修改
    config = VoiceModConfigLoader()
    config.update_voice_mod_settings({
        'voice_mod_enabled': True,
        'manual_mode': True,
        'pitch_shift': 2.0,
        'formant_shift': 0.5,
        'effect_blend': 1.0
    })
    
    print("📋 設定音調偏移 +2.0 半音")
    
    try:
        from services.tts_service import TTSService
        tts = TTSService(enabled=True)
        
        if not tts.is_available():
            print("❌ TTS服務不可用")
            return False
        
        # 檢查語音修改是否被載入
        if hasattr(tts.worker, 'voice_mod_service'):
            if tts.worker.voice_mod_service:
                print("✅ TTS工作線程中語音修改服務已載入")
                print(f"📋 語音修改啟用狀態: {tts.worker.voice_mod_enabled}")
            else:
                print("⚠️ TTS工作線程中語音修改服務為None")
        else:
            print("❌ TTS工作線程中沒有voice_mod_service屬性")
        
        # 播放測試
        test_text = "This is a test of voice modification integration."
        print(f"🎵 播放測試: {test_text}")
        
        tts.speak_text(test_text)
        time.sleep(5)
        
        tts.shutdown()
        print("✅ TTS整合測試完成")
        return True
        
    except Exception as e:
        print(f"❌ TTS整合測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("🚀 語音修改詳細調試測試")
    print("=" * 60)
    
    tests = [
        ("依賴和配置檢查", test_config_and_dependencies),
        ("語音修改服務直接測試", test_voice_mod_service_directly),
        ("TTS整合測試", test_tts_voice_mod_integration),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n>>> {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 測試出錯: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("📊 測試結果摘要:")
    for test_name, success in results:
        status = "✅ 通過" if success else "❌ 失敗"
        print(f"  {test_name}: {status}")
    
    successful_tests = sum(1 for _, success in results if success)
    print(f"\n總計: {successful_tests}/{len(results)} 項測試通過")

if __name__ == "__main__":
    main() 