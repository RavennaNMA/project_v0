#!/usr/bin/env python3
# Location: project_v2/comfyui_voice_controller.py
# Usage: ComfyUI語音修改控制工具

import sys
import json
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QSlider, QPushButton, QTextEdit,
                            QGroupBox, QGridLayout, QSpinBox, QDoubleSpinBox,
                            QCheckBox, QComboBox, QMessageBox)
from PyQt6.QtCore import Qt, QTimer
from services.comfyui_sync_service import ComfyUISyncService

class VoiceControllerWindow(QMainWindow):
    """ComfyUI語音修改控制面板"""
    
    def __init__(self):
        super().__init__()
        self.sync_service = None
        self.init_ui()
        self.init_sync_service()
        
    def init_ui(self):
        """初始化用戶界面"""
        self.setWindowTitle("ComfyUI語音修改控制面板")
        self.setGeometry(100, 100, 800, 700)
        
        # 主控件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # 連接狀態區域
        self.create_connection_section(layout)
        
        # 語音修改控制區域
        self.create_voice_control_section(layout)
        
        # 預設配置區域
        self.create_preset_section(layout)
        
        # 日誌區域
        self.create_log_section(layout)
        
        # 操作按鈕
        self.create_action_buttons(layout)
        
    def create_connection_section(self, parent_layout):
        """創建連接狀態區域"""
        group = QGroupBox("ComfyUI連接狀態")
        layout = QHBoxLayout(group)
        
        self.status_label = QLabel("🔴 未連接")
        self.status_label.setStyleSheet("font-size: 14px; padding: 5px;")
        layout.addWidget(self.status_label)
        
        self.comfyui_url_label = QLabel("http://127.0.0.1:8188")
        layout.addWidget(self.comfyui_url_label)
        
        layout.addStretch()
        
        self.refresh_btn = QPushButton("刷新連接")
        self.refresh_btn.clicked.connect(self.refresh_connection)
        layout.addWidget(self.refresh_btn)
        
        parent_layout.addWidget(group)
        
    def create_voice_control_section(self, parent_layout):
        """創建語音修改控制區域"""
        group = QGroupBox("語音修改參數")
        layout = QGridLayout(group)
        
        # 音調偏移
        layout.addWidget(QLabel("音調偏移 (Pitch Shift):"), 0, 0)
        self.pitch_shift = QDoubleSpinBox()
        self.pitch_shift.setRange(-12.0, 12.0)
        self.pitch_shift.setSingleStep(0.5)
        self.pitch_shift.setValue(0.0)
        self.pitch_shift.setSuffix(" 半音")
        layout.addWidget(self.pitch_shift, 0, 1)
        
        # 音色偏移
        layout.addWidget(QLabel("音色偏移 (Formant Shift):"), 1, 0)
        self.formant_shift = QDoubleSpinBox()
        self.formant_shift.setRange(-5.0, 5.0)
        self.formant_shift.setSingleStep(0.1)
        self.formant_shift.setValue(0.0)
        layout.addWidget(self.formant_shift, 1, 1)
        
        # 混響量
        layout.addWidget(QLabel("混響量 (Reverb):"), 2, 0)
        self.reverb_amount = QDoubleSpinBox()
        self.reverb_amount.setRange(0.0, 1.0)
        self.reverb_amount.setSingleStep(0.1)
        self.reverb_amount.setValue(0.0)
        layout.addWidget(self.reverb_amount, 2, 1)
        
        # 回聲延遲
        layout.addWidget(QLabel("回聲延遲 (Echo):"), 3, 0)
        self.echo_delay = QDoubleSpinBox()
        self.echo_delay.setRange(0.0, 1.0)
        self.echo_delay.setSingleStep(0.1)
        self.echo_delay.setValue(0.0)
        layout.addWidget(self.echo_delay, 3, 1)
        
        # 壓縮量
        layout.addWidget(QLabel("壓縮量 (Compression):"), 4, 0)
        self.compression = QDoubleSpinBox()
        self.compression.setRange(0.0, 1.0)
        self.compression.setSingleStep(0.1)
        self.compression.setValue(0.0)
        layout.addWidget(self.compression, 4, 1)
        
        # 效果混合
        layout.addWidget(QLabel("效果混合 (Effect Blend):"), 5, 0)
        self.effect_blend = QDoubleSpinBox()
        self.effect_blend.setRange(0.0, 1.0)
        self.effect_blend.setSingleStep(0.1)
        self.effect_blend.setValue(1.0)
        layout.addWidget(self.effect_blend, 5, 1)
        
        # 輸出音量
        layout.addWidget(QLabel("輸出音量 (Volume):"), 6, 0)
        self.output_volume = QDoubleSpinBox()
        self.output_volume.setRange(-20.0, 20.0)
        self.output_volume.setSingleStep(1.0)
        self.output_volume.setValue(0.0)
        self.output_volume.setSuffix(" dB")
        layout.addWidget(self.output_volume, 6, 1)
        
        parent_layout.addWidget(group)
        
    def create_preset_section(self, parent_layout):
        """創建預設配置區域"""
        group = QGroupBox("快速預設")
        layout = QHBoxLayout(group)
        
        # 預設選擇
        self.preset_combo = QComboBox()
        self.preset_combo.addItems([
            "自定義",
            "男聲轉女聲 (+4 半音)",
            "女聲轉男聲 (-4 半音)", 
            "機器人聲音",
            "電影旁白",
            "兒童聲音",
            "怪物聲音"
        ])
        self.preset_combo.currentTextChanged.connect(self.apply_preset)
        layout.addWidget(QLabel("預設配置:"))
        layout.addWidget(self.preset_combo)
        
        layout.addStretch()
        
        # 重置按鈕
        reset_btn = QPushButton("重置所有參數")
        reset_btn.clicked.connect(self.reset_all_parameters)
        layout.addWidget(reset_btn)
        
        parent_layout.addWidget(group)
        
    def create_log_section(self, parent_layout):
        """創建日誌區域"""
        group = QGroupBox("同步日誌")
        layout = QVBoxLayout(group)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
        
        parent_layout.addWidget(group)
        
    def create_action_buttons(self, parent_layout):
        """創建操作按鈕"""
        layout = QHBoxLayout()
        
        # 同步到ComfyUI
        sync_to_comfyui_btn = QPushButton("📤 推送到 ComfyUI")
        sync_to_comfyui_btn.clicked.connect(self.sync_to_comfyui)
        layout.addWidget(sync_to_comfyui_btn)
        
        # 同步到主項目
        sync_to_main_btn = QPushButton("📥 同步到主項目")
        sync_to_main_btn.clicked.connect(self.sync_to_main_project)
        layout.addWidget(sync_to_main_btn)
        
        # 測試語音
        test_voice_btn = QPushButton("🎵 測試語音效果")
        test_voice_btn.clicked.connect(self.test_voice_effect)
        layout.addWidget(test_voice_btn)
        
        layout.addStretch()
        
        # 關閉按鈕
        close_btn = QPushButton("關閉")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        
        parent_layout.addLayout(layout)
        
    def init_sync_service(self):
        """初始化同步服務"""
        try:
            self.sync_service = ComfyUISyncService()
            self.sync_service.connection_status_changed.connect(self.on_connection_status_changed)
            self.sync_service.config_updated.connect(self.on_config_updated)
            self.sync_service.start_sync()
            
            self.log("✅ ComfyUI同步服務已啟動")
            
        except Exception as e:
            self.log(f"❌ 同步服務啟動失敗: {e}")
            
    def on_connection_status_changed(self, connected):
        """連接狀態變化處理"""
        if connected:
            self.status_label.setText("🟢 已連接")
            self.status_label.setStyleSheet("color: green; font-size: 14px; padding: 5px;")
            self.log("🔗 ComfyUI連接已建立")
        else:
            self.status_label.setText("🔴 未連接")
            self.status_label.setStyleSheet("color: red; font-size: 14px; padding: 5px;")
            self.log("❌ ComfyUI連接已斷開")
            
    def on_config_updated(self, config):
        """配置更新處理"""
        self.log(f"📨 收到配置更新: {config}")
        self.update_ui_from_config(config)
        
    def update_ui_from_config(self, config):
        """根據配置更新UI"""
        if 'pitch_shift' in config:
            self.pitch_shift.setValue(float(config['pitch_shift']))
        if 'formant_shift' in config:
            self.formant_shift.setValue(float(config['formant_shift']))
        if 'reverb_amount' in config:
            self.reverb_amount.setValue(float(config['reverb_amount']))
        if 'echo_delay' in config:
            self.echo_delay.setValue(float(config['echo_delay']))
        if 'compression' in config:
            self.compression.setValue(float(config['compression']))
        if 'effect_blend' in config:
            self.effect_blend.setValue(float(config['effect_blend']))
        if 'output_volume' in config:
            self.output_volume.setValue(float(config['output_volume']))
            
    def get_current_config(self):
        """獲取當前UI配置"""
        return {
            'pitch_shift': self.pitch_shift.value(),
            'formant_shift': self.formant_shift.value(),
            'reverb_amount': self.reverb_amount.value(),
            'echo_delay': self.echo_delay.value(),
            'compression': self.compression.value(),
            'effect_blend': self.effect_blend.value(),
            'output_volume': self.output_volume.value(),
            'voice_mod_enabled': True,
            'manual_mode': True
        }
        
    def apply_preset(self, preset_name):
        """應用預設配置"""
        presets = {
            "男聲轉女聲 (+4 半音)": {
                'pitch_shift': 4.0,
                'formant_shift': 2.0,
                'reverb_amount': 0.1,
                'echo_delay': 0.0,
                'compression': 0.2,
                'effect_blend': 1.0,
                'output_volume': 0.0
            },
            "女聲轉男聲 (-4 半音)": {
                'pitch_shift': -4.0,
                'formant_shift': -2.0,
                'reverb_amount': 0.0,
                'echo_delay': 0.0,
                'compression': 0.3,
                'effect_blend': 1.0,
                'output_volume': 0.0
            },
            "機器人聲音": {
                'pitch_shift': 1.0,
                'formant_shift': -1.0,
                'reverb_amount': 0.2,
                'echo_delay': 0.1,
                'compression': 0.5,
                'effect_blend': 0.8,
                'output_volume': 2.0
            },
            "電影旁白": {
                'pitch_shift': -2.0,
                'formant_shift': 0.0,
                'reverb_amount': 0.4,
                'echo_delay': 0.0,
                'compression': 0.4,
                'effect_blend': 1.0,
                'output_volume': 1.0
            },
            "兒童聲音": {
                'pitch_shift': 6.0,
                'formant_shift': 3.0,
                'reverb_amount': 0.0,
                'echo_delay': 0.0,
                'compression': 0.1,
                'effect_blend': 1.0,
                'output_volume': 0.0
            },
            "怪物聲音": {
                'pitch_shift': -8.0,
                'formant_shift': -3.0,
                'reverb_amount': 0.6,
                'echo_delay': 0.3,
                'compression': 0.7,
                'effect_blend': 1.0,
                'output_volume': 3.0
            }
        }
        
        if preset_name in presets:
            config = presets[preset_name]
            self.update_ui_from_config(config)
            self.log(f"✨ 已應用預設: {preset_name}")
            
    def reset_all_parameters(self):
        """重置所有參數"""
        self.pitch_shift.setValue(0.0)
        self.formant_shift.setValue(0.0)
        self.reverb_amount.setValue(0.0)
        self.echo_delay.setValue(0.0)
        self.compression.setValue(0.0)
        self.effect_blend.setValue(1.0)
        self.output_volume.setValue(0.0)
        self.preset_combo.setCurrentText("自定義")
        self.log("🔄 已重置所有參數")
        
    def sync_to_comfyui(self):
        """同步當前設定到ComfyUI"""
        try:
            config = self.get_current_config()
            # 這裡可以實現將配置發送到ComfyUI的邏輯
            # 目前ComfyUI不支持接收外部配置，所以這是模擬
            self.log(f"📤 模擬推送配置到ComfyUI: {config}")
            QMessageBox.information(self, "提示", 
                                  "目前ComfyUI不支持直接接收外部配置。\n"
                                  "請在ComfyUI中手動調整Geeky Kokoro Voice Mod節點的參數。")
        except Exception as e:
            self.log(f"❌ 推送配置失敗: {e}")
            
    def sync_to_main_project(self):
        """同步當前設定到主項目"""
        try:
            config = self.get_current_config()
            if self.sync_service:
                self.sync_service.manually_sync_config(config)
                self.log(f"📥 已同步配置到主項目: {config}")
                QMessageBox.information(self, "成功", "配置已同步到主項目！")
            else:
                self.log("❌ 同步服務未啟動")
        except Exception as e:
            self.log(f"❌ 同步到主項目失敗: {e}")
            
    def test_voice_effect(self):
        """測試語音效果"""
        try:
            # 首先同步配置
            self.sync_to_main_project()
            
            # 提示用戶運行測試
            QMessageBox.information(self, "測試語音", 
                                  "配置已更新！\n\n"
                                  "請運行以下命令測試語音效果：\n"
                                  "python test_voice_mod.py\n\n"
                                  "或直接在主程序中播放英文文本。")
            self.log("🎵 請使用 test_voice_mod.py 測試語音效果")
            
        except Exception as e:
            self.log(f"❌ 測試準備失敗: {e}")
            
    def refresh_connection(self):
        """刷新連接"""
        if self.sync_service:
            self.log("🔄 正在刷新連接...")
            # 觸發連接檢查
            self.sync_service._check_connection()
        
    def log(self, message):
        """添加日誌"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        
    def closeEvent(self, event):
        """關閉事件"""
        if self.sync_service:
            self.sync_service.stop_sync()
        event.accept()


def main():
    """主函數"""
    app = QApplication(sys.argv)
    window = VoiceControllerWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main()) 