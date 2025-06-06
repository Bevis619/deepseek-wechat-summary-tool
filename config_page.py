import os
import json
import sys
from PyQt5.QtWidgets import (QWidget, QLabel, QLineEdit, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QComboBox, QMessageBox, QGroupBox, QFormLayout,
                             QSpacerItem, QSizePolicy)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

def get_config_path():
    """获取配置文件路径，兼容开发环境和打包后的环境"""
    if getattr(sys, 'frozen', False):
        # 打包后的环境
        application_path = os.path.dirname(sys.executable)
    else:
        # 开发环境
        application_path = os.path.dirname(os.path.abspath(__file__))
    
    return os.path.join(application_path, "config.json")

class ConfigPage(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.setup_style()
        self.load_config()
    
    def setup_style(self):
        """设置UI样式"""
        # 设置字体
        font = QFont("微软雅黑", 9)
        self.setFont(font)
        
        # 设置按钮样式
        button_style = """
            QPushButton {
                background-color: #4a86e8;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3a76d8;
            }
            QPushButton:pressed {
                background-color: #2a66c8;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """
        
        # 设置输入框样式
        input_style = """
            QLineEdit {
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 6px;
                background-color: #ffffff;
            }
            QLineEdit:focus {
                border: 1px solid #4a86e8;
            }
        """
        
        # 设置组合框样式
        combobox_style = """
            QComboBox {
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 6px;
                background-color: #ffffff;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: right;
                width: 20px;
                border-left: 1px solid #cccccc;
            }
        """
        
        # 设置组框样式
        group_style = """
            QGroupBox {
                font-weight: bold;
                border: 1px solid #cccccc;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """
        
        # 应用样式
        self.save_button.setStyleSheet(button_style)
        self.api_key_input.setStyleSheet(input_style)
        self.api_url_input.setStyleSheet(input_style)
        self.chatlog_service_url_input.setStyleSheet(input_style)
        self.model_combo.setStyleSheet(combobox_style)
        self.deepseek_group.setStyleSheet(group_style)
        self.chatlog_service_group.setStyleSheet(group_style)
    
    def init_ui(self):
        # 创建主布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # DeepSeek配置组
        self.deepseek_group = QGroupBox("DeepSeek API配置")
        deepseek_layout = QFormLayout()
        deepseek_layout.setContentsMargins(15, 20, 15, 15)
        deepseek_layout.setSpacing(15)
        
        # API密钥
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("请输入DeepSeek API密钥...")
        self.api_key_input.setEchoMode(QLineEdit.Password)  # 密码模式
        deepseek_layout.addRow("API密钥:", self.api_key_input)
        
        # API地址
        self.api_url_input = QLineEdit("https://api.deepseek.com/v1")
        deepseek_layout.addRow("API地址:", self.api_url_input)
        
        # 模型选择
        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "deepseek-chat",
            "deepseek-reasoner"
        ])
        deepseek_layout.addRow("模型选择:", self.model_combo)
        
        self.deepseek_group.setLayout(deepseek_layout)
        
        # Chatlog服务配置组
        self.chatlog_service_group = QGroupBox("Chatlog服务配置")
        chatlog_service_layout = QFormLayout()
        chatlog_service_layout.setContentsMargins(15, 20, 15, 15)
        chatlog_service_layout.setSpacing(15)
        
        # Chatlog服务地址
        self.chatlog_service_url_input = QLineEdit()
        self.chatlog_service_url_input.setPlaceholderText("请输入Chatlog服务地址...")
        chatlog_service_layout.addRow("服务地址:", self.chatlog_service_url_input)
        
        self.chatlog_service_group.setLayout(chatlog_service_layout)
        
        # 保存按钮
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("保存配置")
        self.save_button.setMinimumHeight(40)
        self.save_button.clicked.connect(self.save_config)
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addStretch()
        
        # 添加到主布局
        main_layout.addWidget(self.deepseek_group)
        main_layout.addWidget(self.chatlog_service_group)
        main_layout.addLayout(button_layout)
        main_layout.addStretch(1)  # 添加弹性空间
        
        self.setLayout(main_layout)
    
    def load_config(self):
        """加载配置"""
        config_path = get_config_path()
        print(f"正在加载配置文件: {config_path}")  # 调试信息
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    
                    # 加载API密钥
                    api_key = config.get("api_key", "")
                    self.api_key_input.setText(api_key)
                    print(f"加载API密钥: {'***已设置***' if api_key else '未设置'}")  # 调试信息
                    
                    # 加载API地址
                    api_url = config.get("api_url", "https://api.deepseek.com/v1")
                    self.api_url_input.setText(api_url)
                    
                    # 设置模型
                    model = config.get("model", "deepseek-chat")
                    index = self.model_combo.findText(model)
                    if index >= 0:
                        self.model_combo.setCurrentIndex(index)
                    
                    # 设置chatlog服务地址
                    chatlog_service_url = config.get("chatlog_service_url", "http://127.0.0.1:5030/api/v1")
                    self.chatlog_service_url_input.setText(chatlog_service_url)
                    
                    print("配置加载成功")  # 调试信息
            except Exception as e:
                print(f"加载配置失败: {str(e)}")
                # 设置默认值
                self.api_url_input.setText("https://api.deepseek.com/v1")
                self.chatlog_service_url_input.setText("http://127.0.0.1:5030/api/v1")
        else:
            print("配置文件不存在，使用默认设置")  # 调试信息
            # 默认设置
            self.api_url_input.setText("https://api.deepseek.com/v1")
            self.chatlog_service_url_input.setText("http://127.0.0.1:5030/api/v1")
    
    def save_config(self):
        """保存配置"""
        # 确保所有字段都有值
        api_key = self.api_key_input.text().strip()
        api_url = self.api_url_input.text().strip() or "https://api.deepseek.com/v1"
        model = self.model_combo.currentText() or "deepseek-chat"
        chatlog_service_url = self.chatlog_service_url_input.text().strip() or "http://127.0.0.1:5030/api/v1"
        
        config = {
            "api_key": api_key,
            "api_url": api_url,
            "model": model,
            "chatlog_service_url": chatlog_service_url
        }
        
        config_path = get_config_path()
        print(f"正在保存配置到: {config_path}")  # 调试信息
        print(f"保存的配置: API密钥={'***已设置***' if api_key else '未设置'}, API地址={api_url}, 模型={model}")  # 调试信息
        
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
            
            print("配置保存成功")  # 调试信息
            QMessageBox.information(self, "成功", "配置已保存")
        except Exception as e:
            error_msg = f"无法保存配置: {str(e)}"
            print(f"保存配置失败: {error_msg}")  # 调试信息
            QMessageBox.critical(self, "保存失败", error_msg)
    
    def get_config(self):
        """获取当前配置"""
        return {
            "api_key": self.api_key_input.text(),
            "api_url": self.api_url_input.text(),
            "model": self.model_combo.currentText(),
            "chatlog_service_url": self.chatlog_service_url_input.text()
        }