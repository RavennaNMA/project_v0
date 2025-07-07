#!/usr/bin/env python3
# Location: project_v2/kokoro_tts_studio.py
# Usage: Kokoro TTS Studio - 完整的語音合成與修改工作室

import sys
import os
import json
import time
import threading
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QSlider, QPushButton, QTextEdit,
                            QGroupBox, QGridLayout, QSpinBox, QDoubleSpinBox,
                            QCheckBox, QComboBox, QMessageBox, QProgressBar,
                            QTabWidget, QFileDialog, QSplitter, QFrame)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QUrl
from PyQt6.QtGui import QFont, QIcon, QPalette, QColor
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

# 導入我們的服務
from services.tts_service import TTSService
from services.voice_mod_service import VoiceModService
from utils.voice_mod_config_loader import VoiceModConfigLoader

class AudioGenerationThread(QThread):
    """音頻生成線程"""
    finished = pyqtSignal(str)  # 生成完成信號，傳遞音頻文件路徑
    error = pyqtSignal(str)     # 錯誤信號
    progress = pyqtSignal(int)  # 進度信號

    def __init__(self, text, voice_config):
        super().__init__()
        self.text = text
        self.voice_config = voice_config
        self.output_path = "studio_output.wav"
        
    def run(self):
        """執行音頻生成"""
        try:
            self.progress.emit(10)
            
            # 初始化TTS服務
            tts_service = TTSService()
            self.progress.emit(30)
            
            # 初始化語音修改服務
            voice_mod_service = VoiceModService()
            self.progress.emit(50)
            
            # 生成基礎音頻
            audio_data = tts_service._generate_audio(self.text)
            self.progress.emit(70)
            
            # 應用語音修改
            if self.voice_config.get('voice_mod_enabled', True):
                modified_audio = voice_mod_service.process_audio(audio_data, self.voice_config)
            else:
                modified_audio = audio_data
            self.progress.emit(90)
            
            # 保存音頻
            import scipy.io.wavfile as wavfile
            import numpy as np
            
            # 確保音頻是正確的格式
            if modified_audio.dtype != np.int16:
                # 轉換為16位整數
                audio_int16 = (modified_audio * 32767).astype(np.int16)
            else:
                audio_int16 = modified_audio
                
            wavfile.write(self.output_path, 24000, audio_int16)
            self.progress.emit(100)
            
            self.finished.emit(self.output_path)
            
        except Exception as e:
            self.error.emit(str(e))

class KokoroTTSStudio(QMainWindow):
    """Kokoro TTS Studio 主窗口"""
    
    def __init__(self):
        super().__init__()
        self.audio_thread = None
        self.media_player = None
        self.audio_output = None
        self.current_audio_file = None
        
        # 語音配置
        self.voice_config = {
            'voice_mod_enabled': True,
            'pitch_shift': 0.0,
            'formant_shift': 0.0,
            'reverb_amount': 0.0,
            'echo_delay': 0.0,
            'compression': 0.0,
            'effect_blend': 1.0,
            'output_volume': 0.0,
            'manual_mode': True
        }
        
        self.init_ui()
        self.init_media_player()
        self.load_presets()
        
    def init_ui(self):
        """初始化用戶界面"""
        self.setWindowTitle("🎵 Kokoro TTS Studio - 語音合成工作室")
        self.setGeometry(100, 100, 1200, 800)
        
        # 設置樣式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555555;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #3c3c3c;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: #00aaff;
            }
            QPushButton {
                background-color: #0078d4;
                border: none;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
            QTextEdit {
                background-color: #404040;
                border: 1px solid #666666;
                border-radius: 4px;
                color: #ffffff;
                font-size: 12px;
            }
            QSlider::groove:horizontal {
                background-color: #555555;
                height: 8px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background-color: #00aaff;
                width: 18px;
                border-radius: 9px;
            }
        """)
        
        # 主控件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # 使用分割器布局
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_widget_layout = QVBoxLayout(main_widget)
        main_widget_layout.addWidget(main_splitter)
        
        # 左側面板 - 文本和控制
        left_panel = self.create_left_panel()
        main_splitter.addWidget(left_panel)
        
        # 右側面板 - 參數調整
        right_panel = self.create_right_panel()
        main_splitter.addWidget(right_panel)
        
        # 設置分割比例
        main_splitter.setSizes([600, 600])
        
    def create_left_panel(self):
        """創建左側面板"""
        left_widget = QWidget()
        layout = QVBoxLayout(left_widget)
        
        # 文本輸入區域
        text_group = QGroupBox("📝 文本輸入")
        text_layout = QVBoxLayout(text_group)
        
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("在此輸入要合成語音的文本...\n\n範例:\nHello, this is a test of voice synthesis.\nYou can adjust parameters and preview instantly!")
        self.text_input.setMaximumHeight(200)
        text_layout.addWidget(self.text_input)
        
        # 快速文本按鈕
        quick_text_layout = QHBoxLayout()
        quick_texts = [
            ("測試短句", "Hello, how are you today?"),
            ("長句測試", "This is a longer sentence to test the voice synthesis capabilities."),
            ("情感測試", "I'm excited to try this new voice modification technology!")
        ]
        
        for name, text in quick_texts:
            btn = QPushButton(name)
            btn.clicked.connect(lambda checked, t=text: self.text_input.setPlainText(t))
            quick_text_layout.addWidget(btn)
        
        text_layout.addLayout(quick_text_layout)
        layout.addWidget(text_group)
        
        # 生成控制區域
        control_group = QGroupBox("🎛️ 生成控制")
        control_layout = QVBoxLayout(control_group)
        
        # 生成按鈕
        generate_layout = QHBoxLayout()
        
        self.generate_btn = QPushButton("🎵 生成語音")
        self.generate_btn.clicked.connect(self.generate_audio)
        self.generate_btn.setStyleSheet("QPushButton { font-size: 14px; padding: 12px 24px; }")
        generate_layout.addWidget(self.generate_btn)
        
        self.play_btn = QPushButton("▶️ 播放")
        self.play_btn.clicked.connect(self.play_audio)
        self.play_btn.setEnabled(False)
        generate_layout.addWidget(self.play_btn)
        
        self.stop_btn = QPushButton("⏹️ 停止")
        self.stop_btn.clicked.connect(self.stop_audio)
        self.stop_btn.setEnabled(False)
        generate_layout.addWidget(self.stop_btn)
        
        self.save_btn = QPushButton("💾 保存")
        self.save_btn.clicked.connect(self.save_audio)
        self.save_btn.setEnabled(False)
        generate_layout.addWidget(self.save_btn)
        
        control_layout.addLayout(generate_layout)
        
        # 進度條
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        control_layout.addWidget(self.progress_bar)
        
        # 狀態標籤
        self.status_label = QLabel("✨ 準備就緒，請輸入文本並調整參數")
        self.status_label.setStyleSheet("color: #00ff00; font-size: 12px;")
        control_layout.addWidget(self.status_label)
        
        layout.addWidget(control_group)
        
        # 預設配置區域
        preset_group = QGroupBox("🎭 語音風格預設")
        preset_layout = QVBoxLayout(preset_group)
        
        self.preset_combo = QComboBox()
        self.preset_combo.currentTextChanged.connect(self.apply_preset)
        preset_layout.addWidget(self.preset_combo)
        
        preset_buttons_layout = QHBoxLayout()
        
        self.save_preset_btn = QPushButton("💾 保存預設")
        self.save_preset_btn.clicked.connect(self.save_current_preset)
        preset_buttons_layout.addWidget(self.save_preset_btn)
        
        self.delete_preset_btn = QPushButton("🗑️ 刪除預設")
        self.delete_preset_btn.clicked.connect(self.delete_preset)
        preset_buttons_layout.addWidget(self.delete_preset_btn)
        
        preset_layout.addLayout(preset_buttons_layout)
        layout.addWidget(preset_group)
        
        # 添加彈性空間
        layout.addStretch()
        
        return left_widget
        
    def create_right_panel(self):
        """創建右側參數面板"""
        right_widget = QWidget()
        layout = QVBoxLayout(right_widget)
        
        # 參數調整區域
        params_group = QGroupBox("🔧 語音參數調整")
        params_layout = QGridLayout(params_group)
        
        # 參數配置
        param_configs = [
            ("pitch_shift", "音調偏移", -12.0, 12.0, 0.5, " 半音", "調整音調高低，+4約為男轉女聲，-4約為女轉男聲"),
            ("formant_shift", "音色偏移", -5.0, 5.0, 0.1, "", "調整聲音特質，正值更尖銳，負值更低沉"),
            ("reverb_amount", "混響效果", 0.0, 1.0, 0.1, "", "添加空間混響感，營造不同環境聲音"),
            ("echo_delay", "回聲延遲", 0.0, 1.0, 0.1, "", "添加回聲效果，增強聲音層次"),
            ("compression", "動態壓縮", 0.0, 1.0, 0.1, "", "壓縮動態範圍，讓聲音更飽滿"),
            ("effect_blend", "效果混合", 0.0, 1.0, 0.1, "", "原聲與效果的混合比例"),
            ("output_volume", "輸出音量", -20.0, 20.0, 1.0, " dB", "調整最終輸出音量")
        ]
        
        self.param_widgets = {}
        
        for i, (param_name, display_name, min_val, max_val, step, suffix, tooltip) in enumerate(param_configs):
            # 標籤
            label = QLabel(f"{display_name}:")
            label.setToolTip(tooltip)
            params_layout.addWidget(label, i, 0)
            
            # 數值顯示
            value_label = QLabel("0.0" + suffix)
            value_label.setMinimumWidth(80)
            value_label.setStyleSheet("color: #00aaff; font-weight: bold;")
            params_layout.addWidget(value_label, i, 1)
            
            # 滑桿
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setMinimum(int(min_val / step))
            slider.setMaximum(int(max_val / step))
            slider.setValue(int(self.voice_config[param_name] / step))
            slider.valueChanged.connect(self.create_param_updater(param_name, step, suffix, value_label))
            params_layout.addWidget(slider, i, 2)
            
            # 重置按鈕
            reset_btn = QPushButton("🔄")
            reset_btn.setMaximumWidth(30)
            reset_btn.clicked.connect(self.create_param_resetter(param_name, slider, step, suffix, value_label))
            params_layout.addWidget(reset_btn, i, 3)
            
            self.param_widgets[param_name] = {
                'slider': slider,
                'label': value_label,
                'step': step,
                'suffix': suffix
            }
        
        layout.addWidget(params_group)
        
        # 全局控制
        global_group = QGroupBox("🌐 全局控制")
        global_layout = QVBoxLayout(global_group)
        
        # 啟用語音修改
        self.enable_voice_mod = QCheckBox("啟用語音修改效果")
        self.enable_voice_mod.setChecked(True)
        self.enable_voice_mod.stateChanged.connect(self.update_voice_mod_enabled)
        global_layout.addWidget(self.enable_voice_mod)
        
        # 全局重置
        global_buttons_layout = QHBoxLayout()
        
        reset_all_btn = QPushButton("🔄 重置所有參數")
        reset_all_btn.clicked.connect(self.reset_all_parameters)
        global_buttons_layout.addWidget(reset_all_btn)
        
        random_btn = QPushButton("🎲 隨機參數")
        random_btn.clicked.connect(self.randomize_parameters)
        global_buttons_layout.addWidget(random_btn)
        
        global_layout.addLayout(global_buttons_layout)
        layout.addWidget(global_group)
        
        # 實時預覽
        preview_group = QGroupBox("👁️ 實時預覽")
        preview_layout = QVBoxLayout(preview_group)
        
        self.auto_preview = QCheckBox("參數變化時自動重新生成")
        preview_layout.addWidget(self.auto_preview)
        
        quick_preview_btn = QPushButton("⚡ 快速預覽")
        quick_preview_btn.clicked.connect(self.quick_preview)
        preview_layout.addWidget(quick_preview_btn)
        
        layout.addWidget(preview_group)
        
        # 添加彈性空間
        layout.addStretch()
        
        return right_widget
    
    def create_param_updater(self, param_name, step, suffix, value_label):
        """創建參數更新函數"""
        def update_param(value):
            real_value = value * step
            self.voice_config[param_name] = real_value
            value_label.setText(f"{real_value:.1f}{suffix}")
            
            # 如果啟用自動預覽，延遲生成
            if self.auto_preview.isChecked():
                self.schedule_auto_preview()
        return update_param
    
    def create_param_resetter(self, param_name, slider, step, suffix, value_label):
        """創建參數重置函數"""
        def reset_param():
            slider.setValue(0)
            self.voice_config[param_name] = 0.0
            value_label.setText(f"0.0{suffix}")
        return reset_param
    
    def update_voice_mod_enabled(self, state):
        """更新語音修改啟用狀態"""
        self.voice_config['voice_mod_enabled'] = state == Qt.CheckState.Checked.value
    
    def schedule_auto_preview(self):
        """調度自動預覽"""
        # 使用定時器避免頻繁生成
        if hasattr(self, 'preview_timer'):
            self.preview_timer.stop()
        
        self.preview_timer = QTimer()
        self.preview_timer.setSingleShot(True)
        self.preview_timer.timeout.connect(self.auto_generate)
        self.preview_timer.start(1500)  # 1.5秒後生成
    
    def auto_generate(self):
        """自動生成語音"""
        if self.text_input.toPlainText().strip():
            self.generate_audio()
    
    def init_media_player(self):
        """初始化媒體播放器"""
        try:
            self.audio_output = QAudioOutput()
            self.media_player = QMediaPlayer()
            self.media_player.setAudioOutput(self.audio_output)
            self.media_player.mediaStatusChanged.connect(self.on_media_status_changed)
        except Exception as e:
            print(f"初始化媒體播放器失敗: {e}")
    
    def generate_audio(self):
        """生成音頻"""
        text = self.text_input.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "提示", "請先輸入要合成的文本！")
            return
        
        if self.audio_thread and self.audio_thread.isRunning():
            QMessageBox.information(self, "提示", "正在生成中，請稍候...")
            return
        
        # 禁用按鈕並顯示進度
        self.generate_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("🔄 正在生成語音...")
        
        # 啟動生成線程
        self.audio_thread = AudioGenerationThread(text, self.voice_config.copy())
        self.audio_thread.finished.connect(self.on_audio_generated)
        self.audio_thread.error.connect(self.on_generation_error)
        self.audio_thread.progress.connect(self.progress_bar.setValue)
        self.audio_thread.start()
    
    def on_audio_generated(self, audio_path):
        """音頻生成完成"""
        self.current_audio_file = audio_path
        self.generate_btn.setEnabled(True)
        self.play_btn.setEnabled(True)
        self.save_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("✅ 語音生成完成！點擊播放按鈕試聽")
        
        # 自動播放
        self.play_audio()
    
    def on_generation_error(self, error_msg):
        """生成錯誤處理"""
        self.generate_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"❌ 生成失敗: {error_msg}")
        QMessageBox.critical(self, "錯誤", f"語音生成失敗:\n{error_msg}")
    
    def play_audio(self):
        """播放音頻"""
        if not self.current_audio_file or not os.path.exists(self.current_audio_file):
            QMessageBox.warning(self, "提示", "沒有可播放的音頻文件！")
            return
        
        try:
            if self.media_player:
                self.media_player.setSource(QUrl.fromLocalFile(os.path.abspath(self.current_audio_file)))
                self.media_player.play()
                self.play_btn.setEnabled(False)
                self.stop_btn.setEnabled(True)
                self.status_label.setText("🎵 正在播放...")
        except Exception as e:
            QMessageBox.critical(self, "錯誤", f"播放失敗:\n{e}")
    
    def stop_audio(self):
        """停止播放"""
        if self.media_player:
            self.media_player.stop()
            self.play_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.status_label.setText("⏹️ 播放已停止")
    
    def on_media_status_changed(self, status):
        """媒體狀態變化"""
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.play_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.status_label.setText("✅ 播放完成")
    
    def save_audio(self):
        """保存音頻"""
        if not self.current_audio_file:
            QMessageBox.warning(self, "提示", "沒有可保存的音頻！")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存音頻", "voice_output.wav", "音頻文件 (*.wav)"
        )
        
        if file_path:
            try:
                import shutil
                shutil.copy2(self.current_audio_file, file_path)
                QMessageBox.information(self, "成功", f"音頻已保存到:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "錯誤", f"保存失敗:\n{e}")
    
    def quick_preview(self):
        """快速預覽（使用短句）"""
        original_text = self.text_input.toPlainText()
        self.text_input.setPlainText("Quick preview test.")
        self.generate_audio()
        # 不恢復原文本，讓用戶自己決定
    
    def reset_all_parameters(self):
        """重置所有參數"""
        for param_name, widgets in self.param_widgets.items():
            widgets['slider'].setValue(0)
            self.voice_config[param_name] = 0.0
            widgets['label'].setText(f"0.0{widgets['suffix']}")
        
        self.enable_voice_mod.setChecked(True)
        self.voice_config['voice_mod_enabled'] = True
        self.status_label.setText("🔄 所有參數已重置")
    
    def randomize_parameters(self):
        """隨機化參數"""
        import random
        
        # 定義隨機範圍（相對保守的範圍）
        random_ranges = {
            'pitch_shift': (-6, 6),
            'formant_shift': (-2, 2), 
            'reverb_amount': (0, 0.5),
            'echo_delay': (0, 0.3),
            'compression': (0, 0.5),
            'effect_blend': (0.5, 1.0),
            'output_volume': (-5, 5)
        }
        
        for param_name, (min_val, max_val) in random_ranges.items():
            if param_name in self.param_widgets:
                widgets = self.param_widgets[param_name]
                random_value = random.uniform(min_val, max_val)
                slider_value = int(random_value / widgets['step'])
                widgets['slider'].setValue(slider_value)
                
        self.status_label.setText("🎲 參數已隨機化，可以生成試聽效果")
    
    def load_presets(self):
        """載入預設配置"""
        presets = {
            "默認": {
                'pitch_shift': 0.0, 'formant_shift': 0.0, 'reverb_amount': 0.0,
                'echo_delay': 0.0, 'compression': 0.0, 'effect_blend': 1.0, 'output_volume': 0.0
            },
            "男聲轉女聲": {
                'pitch_shift': 4.0, 'formant_shift': 2.0, 'reverb_amount': 0.1,
                'echo_delay': 0.0, 'compression': 0.2, 'effect_blend': 1.0, 'output_volume': 0.0
            },
            "女聲轉男聲": {
                'pitch_shift': -4.0, 'formant_shift': -2.0, 'reverb_amount': 0.0,
                'echo_delay': 0.0, 'compression': 0.3, 'effect_blend': 1.0, 'output_volume': 0.0
            },
            "機器人聲音": {
                'pitch_shift': 1.0, 'formant_shift': -1.0, 'reverb_amount': 0.2,
                'echo_delay': 0.1, 'compression': 0.5, 'effect_blend': 0.8, 'output_volume': 2.0
            },
            "電影旁白": {
                'pitch_shift': -2.0, 'formant_shift': 0.0, 'reverb_amount': 0.4,
                'echo_delay': 0.0, 'compression': 0.4, 'effect_blend': 1.0, 'output_volume': 1.0
            },
            "兒童聲音": {
                'pitch_shift': 6.0, 'formant_shift': 3.0, 'reverb_amount': 0.0,
                'echo_delay': 0.0, 'compression': 0.1, 'effect_blend': 1.0, 'output_volume': 0.0
            },
            "廣播主持": {
                'pitch_shift': -1.0, 'formant_shift': 0.5, 'reverb_amount': 0.2,
                'echo_delay': 0.0, 'compression': 0.6, 'effect_blend': 1.0, 'output_volume': 2.0
            }
        }
        
        self.presets = presets
        self.preset_combo.clear()
        self.preset_combo.addItems(list(presets.keys()))
    
    def apply_preset(self, preset_name):
        """應用預設配置"""
        if preset_name in self.presets:
            preset_config = self.presets[preset_name]
            
            for param_name, value in preset_config.items():
                if param_name in self.param_widgets:
                    widgets = self.param_widgets[param_name]
                    slider_value = int(value / widgets['step'])
                    widgets['slider'].setValue(slider_value)
                    
            self.status_label.setText(f"✨ 已應用預設: {preset_name}")
    
    def save_current_preset(self):
        """保存當前設定為預設"""
        from PyQt6.QtWidgets import QInputDialog
        
        name, ok = QInputDialog.getText(self, "保存預設", "請輸入預設名稱:")
        if ok and name:
            current_config = {}
            for param_name in self.param_widgets.keys():
                current_config[param_name] = self.voice_config[param_name]
            
            self.presets[name] = current_config
            
            # 更新下拉選單
            current_text = self.preset_combo.currentText()
            self.preset_combo.clear()
            self.preset_combo.addItems(list(self.presets.keys()))
            self.preset_combo.setCurrentText(name)
            
            self.status_label.setText(f"💾 預設 '{name}' 已保存")
    
    def delete_preset(self):
        """刪除預設"""
        current_preset = self.preset_combo.currentText()
        if current_preset == "默認":
            QMessageBox.warning(self, "提示", "無法刪除默認預設！")
            return
        
        reply = QMessageBox.question(self, "確認刪除", f"確定要刪除預設 '{current_preset}' 嗎？")
        if reply == QMessageBox.StandardButton.Yes:
            if current_preset in self.presets:
                del self.presets[current_preset]
                self.preset_combo.removeItem(self.preset_combo.currentIndex())
                self.status_label.setText(f"🗑️ 預設 '{current_preset}' 已刪除")
    
    def closeEvent(self, event):
        """關閉事件"""
        if self.audio_thread and self.audio_thread.isRunning():
            self.audio_thread.terminate()
            self.audio_thread.wait()
        
        if self.media_player:
            self.media_player.stop()
        
        event.accept()


def main():
    """主函數"""
    app = QApplication(sys.argv)
    app.setApplicationName("Kokoro TTS Studio")
    
    # 設置應用程序圖標（如果有的話）
    # app.setWindowIcon(QIcon("icon.ico"))
    
    window = KokoroTTSStudio()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main()) 