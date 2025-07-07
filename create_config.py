#!/usr/bin/env python3
"""創建 tts_config.txt 配置文件"""

config_content = """enabled=true
realtime_mode=true
kokoro_lang_code=a
kokoro_voice=am_adam
kokoro_speed=1.1
min_english_chars=3
auto_clean_text=true
max_chunk_length=80
min_chunk_length=8
verbose_logging=true
test_mode=false
test_text=Hello! This is a test of Kokoro TTS system. The voice quality should be excellent."""

with open('tts_config.txt', 'w', encoding='utf-8') as f:
    f.write(config_content)

print("✅ tts_config.txt 已創建") 