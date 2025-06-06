import json
import requests
import urllib.parse
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QWidget, QLabel, QLineEdit, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QDateEdit, QListWidget, QTextEdit, 
                             QMessageBox, QListWidgetItem, QSplitter, QComboBox,
                             QFrame, QGroupBox, QTextBrowser, QDialog, QDialogButtonBox,
                             QApplication)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QDate, QTimer
from PyQt5.QtGui import QFont, QColor, QPalette, QIcon

class DeepSeekThread(QThread):
    """处理DeepSeek API请求的线程"""
    update_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()
    error_signal = pyqtSignal(str)
    
    def __init__(self, api_key, api_url, model, messages):
        super().__init__()
        self.api_key = api_key
        self.api_url = api_url
        self.model = model
        self.messages = messages
    
    def run(self):
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            data = {
                "model": self.model,
                "messages": self.messages,
                "stream": True
            }
            
            # 使用流式API，添加超时设置
            response = requests.post(
                f"{self.api_url}/chat/completions",
                headers=headers,
                json=data,
                stream=True,
                timeout=(10, 60)  # 连接超时10秒，读取超时60秒
            )
            
            if response.status_code != 200:
                error_msg = f"API请求失败: {response.status_code} - {response.text}"
                self.error_signal.emit(error_msg)
                return
            
            # 处理流式响应
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        line = line[6:]
                        if line == "[DONE]":
                            break
                        try:
                            chunk = json.loads(line)
                            if 'choices' in chunk and len(chunk['choices']) > 0:
                                delta = chunk['choices'][0].get('delta', {})
                                content = delta.get('content', '')
                                if content:
                                    self.update_signal.emit(content)
                        except json.JSONDecodeError:
                            pass
            
            self.finished_signal.emit()
        except requests.exceptions.Timeout:
            self.error_signal.emit("API请求超时，请检查网络连接或稍后重试")
        except requests.exceptions.ConnectionError:
            self.error_signal.emit("连接错误，请检查网络连接或API地址是否正确")
        except Exception as e:
            self.error_signal.emit(f"处理请求时出错: {str(e)}")


class CustomPromptDialog(QDialog):
    """自定义提示词对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加自定义提示词")
        self.setMinimumWidth(500)
        
        # 创建布局
        layout = QVBoxLayout(self)
        
        # 提示词输入
        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText("请输入自定义提示词...")
        self.prompt_input.setMinimumHeight(200)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(QLabel("自定义提示词:"))
        layout.addWidget(self.prompt_input)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def get_prompt(self):
        return self.prompt_input.toPlainText()


class SummaryPage(QWidget):
    def __init__(self, config_page):
        super().__init__()
        self.config_page = config_page
        self.contacts = []
        self.selected_contact = None  # 添加当前选中的联系人记录
        
        # 初始化自动搜索定时器
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)  # 只触发一次
        self.search_timer.timeout.connect(self.auto_search_contacts)
        
        self.init_ui()
        self.setup_style()
        self.setup_auto_search()
        
        # 页面初始化完成后自动加载所有联系人
        self.load_all_contacts()
    
    def load_all_contacts(self):
        """页面初始化时自动加载所有联系人"""
        # 获取chatlog服务URL
        config = self.config_page.get_config()
        chatlog_base_url = config.get('chatlog_service_url', 'http://127.0.0.1:5030/api/v1')
        
        # 显示加载状态
        self.contact_list.clear()
        item = QListWidgetItem("正在加载联系人列表...")
        item.setFlags(item.flags() & ~Qt.ItemIsEnabled)  # 禁用该项
        self.contact_list.addItem(item)
        QApplication.processEvents()  # 立即更新UI
        
        try:
            # 不带参数查询所有联系人
            url = f"{chatlog_base_url}/contact?format=json"
            
            # 添加超时设置
            response = requests.get(url, timeout=(5, 30))  # 连接超时5秒，读取超时30秒
            
            if response.status_code == 200:
                data = response.json()
                self.contacts = data.get('items', [])
                
                # 更新联系人列表
                self.contact_list.clear()
                for contact in self.contacts:
                    display_name = contact.get('nickName') or contact.get('remark') or contact.get('userName')
                    item = QListWidgetItem(display_name)
                    item.setData(Qt.UserRole, contact)  # 存储完整联系人数据
                    self.contact_list.addItem(item)
                
                if not self.contacts:
                    item = QListWidgetItem("暂无联系人数据")
                    item.setFlags(item.flags() & ~Qt.ItemIsEnabled)  # 禁用该项
                    self.contact_list.addItem(item)
            else:
                # 加载失败时显示信息
                self.contact_list.clear()
                item = QListWidgetItem("加载联系人失败")
                item.setFlags(item.flags() & ~Qt.ItemIsEnabled)  # 禁用该项
                self.contact_list.addItem(item)
        except requests.exceptions.Timeout:
            self.contact_list.clear()
            item = QListWidgetItem("加载超时")
            item.setFlags(item.flags() & ~Qt.ItemIsEnabled)  # 禁用该项
            self.contact_list.addItem(item)
        except requests.exceptions.ConnectionError:
            self.contact_list.clear()
            item = QListWidgetItem("连接错误")
            item.setFlags(item.flags() & ~Qt.ItemIsEnabled)  # 禁用该项
            self.contact_list.addItem(item)
        except Exception as e:
            self.contact_list.clear()
            item = QListWidgetItem("加载出错")
            item.setFlags(item.flags() & ~Qt.ItemIsEnabled)  # 禁用该项
            self.contact_list.addItem(item)
        finally:
            # 确保UI响应
            QApplication.processEvents()
    
    def setup_auto_search(self):
        """设置自动搜索功能"""
        # 连接文本变化信号到自动搜索
        self.contact_search_input.textChanged.connect(self.on_search_text_changed)
    
    def on_search_text_changed(self):
        """搜索文本变化时的处理"""
        # 停止之前的定时器
        self.search_timer.stop()
        
        # 获取当前文本
        text = self.contact_search_input.text().strip()
        
        if text:
            # 如果有文本，设置500ms延迟后搜索
            self.search_timer.start(500)
        else:
            # 如果文本为空，清空联系人列表
            self.contact_list.clear()
            # 清空聊天记录显示
            self.chat_display.clear()
            # 清除选中的联系人
            self.selected_contact = None
    
    def auto_search_contacts(self):
        """自动搜索联系人（延迟触发）"""
        keyword = self.contact_search_input.text().strip()
        if keyword:
            self.perform_search(keyword)
    
    def setup_style(self):
        """设置UI样式"""
        # 设置字体
        font = QFont("微软雅黑", 12)
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
        
        # 设置列表样式
        list_style = """
            QListWidget {
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 2px;
                background-color: #ffffff;
            }
            QListWidget::item {
                padding: 6px;
                border-bottom: 1px solid #eeeeee;
            }
            QListWidget::item:selected {
                background-color: #e6f0ff;
                color: #000000;
            }
        """
        
        # 设置文本框样式 - 确保总结结果字体为22px
        textedit_style = """
            QTextEdit, QTextBrowser {
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 4px;
                background-color: #ffffff;
                font-size: 26px;
                font-family: "微软雅黑", "Segoe UI", Arial, sans-serif;
                line-height: 1.4;
            }
        """
        
        # 设置搜索输入框样式 - 调整字体大小
        search_input_style = """
            QLineEdit {
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                padding: 8px 12px;
                background-color: #ffffff;
                font-size: 22px;
                color: #333333;
            }
            QLineEdit:focus {
                border: 2px solid #4a86e8;
                background-color: #fafbfc;
            }
            QLineEdit::placeholder {
                color: #666666;
                font-size: 22px;
            }
        """
        
        # 设置组合框样式 - 调整字体大小
        combobox_style = """
            QComboBox {
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                padding: 8px 12px;
                background-color: #ffffff;
                font-size: 22px;
                color: #333333;
                min-height: 20px;
            }
            QComboBox:focus {
                border: 2px solid #4a86e8;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: right;
                width: 25px;
                border-left: 1px solid #e0e0e0;
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
                background-color: #f8f9fa;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid #666666;
                width: 0px;
                height: 0px;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: #ffffff;
                selection-background-color: #e6f0ff;
                padding: 4px;
                font-size: 22px;
                color: #333333;
            }
            QComboBox QAbstractItemView::item {
                padding: 10px 12px;
                border-bottom: 1px solid #f0f0f0;
                color: #333333;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #4a86e8;
                color: white;
            }
        """
        
        # 应用样式
        self.search_button.setStyleSheet(button_style)
        self.summary_button.setStyleSheet(button_style)
        self.add_prompt_button.setStyleSheet(button_style)
        self.contact_list.setStyleSheet(list_style)
        self.chat_display.setStyleSheet(textedit_style)
        self.summary_display.setStyleSheet(textedit_style)
        self.contact_search_input.setStyleSheet(search_input_style)  # 应用搜索输入框样式
        self.prompt_combo.setStyleSheet(combobox_style)
    
    def init_ui(self):
        # 创建主布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧面板 - 日期、联系人和搜索
        left_panel = QGroupBox("联系人")
        left_layout = QVBoxLayout(left_panel)
        
        # 日期选择 - 移到最上方
        date_layout = QHBoxLayout()
        date_label = QLabel("选择日期:")
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate().addDays(-1))
        # 添加日期变化信号连接
        self.date_edit.dateChanged.connect(self.on_date_changed)
        date_layout.addWidget(date_label)
        date_layout.addWidget(self.date_edit)
        
        # 联系人搜索 - 放在日期选择下方
        contact_search_label = QLabel("搜索联系人:")
        self.contact_search_input = QLineEdit()
        self.contact_search_input.setPlaceholderText("输入关键词自动搜索联系人...")
        # 添加回车键搜索功能
        self.contact_search_input.returnPressed.connect(self.search_contacts)
        
        # 搜索按钮单独一行（保留但不再必需）
        self.search_button = QPushButton("手动搜索")
        self.search_button.clicked.connect(self.search_contacts)
        self.search_button.setToolTip("点击进行手动搜索，或直接在输入框中输入进行自动搜索")
        
        # 联系人列表 - 放在最下方
        self.contact_list = QListWidget()
        self.contact_list.itemClicked.connect(self.on_contact_selected)
        
        # 添加到左侧布局
        left_layout.addLayout(date_layout)
        left_layout.addWidget(contact_search_label)
        left_layout.addWidget(self.contact_search_input)
        left_layout.addWidget(self.search_button)
        left_layout.addWidget(self.contact_list)
        
        # 右侧面板 - 聊天记录和总结
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # 聊天记录显示
        chat_group = QGroupBox("聊天记录")
        chat_layout = QVBoxLayout(chat_group)
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        chat_layout.addWidget(self.chat_display)
        
        # 总结提示词
        prompt_group = QGroupBox("总结设置")
        prompt_layout = QVBoxLayout(prompt_group)
        
        prompt_combo_layout = QHBoxLayout()
        prompt_label = QLabel("总结提示词:")
        self.prompt_combo = QComboBox()
        self.prompt_combo.addItems([
            "请帮我将群聊内容总结成一个群聊报告，包含不多于5个的话题的总结（如果还有更多话题，可以在后面简单补充）。每个话题包含以下内容：\n- 话题名(50字以内，带数字序号，同时附带热度，以🔥数量表示）\n- 参与者(不超过5个人，将重复的人名去重)\n- 时间段(从几点到几点)\n- 过程(50到200字左右）\n- 评价(50字以下)\n- 分割线： ------------\n\n另外有以下要求：\n1. 每个话题结束使用 ------------ 分割\n2. 使用中文冒号\n3. 无需大标题\n4. 开始给出本群讨论风格的整体评价，例如活跃、太水、太黄、太暴力、话题不集中、无聊诸如此类\n\n最后总结下最活跃的前五个发言者。",
            "请总结以下微信聊天记录的主要内容",
            "请提取以下微信聊天记录中的关键信息",
            "请分析以下微信聊天记录并提取重要事项"

        ])
        self.prompt_combo.setEditable(True)
        
        # 添加自定义提示词按钮
        self.add_prompt_button = QPushButton("添加自定义提示词")
        self.add_prompt_button.clicked.connect(self.add_custom_prompt)
        
        prompt_combo_layout.addWidget(prompt_label)
        prompt_combo_layout.addWidget(self.prompt_combo)
        prompt_combo_layout.addWidget(self.add_prompt_button)
        
        prompt_layout.addLayout(prompt_combo_layout)
        
        # 总结按钮
        self.summary_button = QPushButton("一键总结")
        self.summary_button.setMinimumHeight(40)
        self.summary_button.clicked.connect(self.summarize_chat)
        
        # 总结结果
        summary_group = QGroupBox("总结结果")
        summary_layout = QVBoxLayout(summary_group)
        self.summary_display = QTextBrowser()  # 使用QTextBrowser支持富文本
        self.summary_display.setOpenExternalLinks(True)  # 允许打开外部链接
        summary_layout.addWidget(self.summary_display)
        
        # 添加到右侧布局
        right_layout.addWidget(chat_group)
        right_layout.addWidget(prompt_group)
        right_layout.addWidget(self.summary_button)
        right_layout.addWidget(summary_group)
        
        # 设置右侧面板的比例
        right_layout.setStretch(0, 2)  # 聊天记录
        right_layout.setStretch(1, 1)  # 提示词
        right_layout.setStretch(3, 4)  # 总结结果
        
        # 添加面板到分割器
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        
        # 设置左右面板的比例为40:60
        splitter.setSizes([400, 600])
        
        # 设置分割器处理策略，防止面板被完全隐藏
        splitter.setChildrenCollapsible(False)  # 禁止子部件完全折叠
        
        # 设置最小尺寸限制
        left_panel.setMinimumWidth(500)  # 左侧面板最小宽度
        right_panel.setMinimumWidth(600)  # 右侧面板最小宽度
        
        # 添加分割器到主布局
        main_layout.addWidget(splitter)
        
        self.setLayout(main_layout)
    
    def on_date_changed(self):
        """日期变化时自动重新加载聊天记录"""
        if self.selected_contact:
            self.load_chat_for_contact(self.selected_contact)
    
    def add_custom_prompt(self):
        """添加自定义提示词"""
        dialog = CustomPromptDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            custom_prompt = dialog.get_prompt()
            if custom_prompt.strip():
                self.prompt_combo.addItem(custom_prompt)
                self.prompt_combo.setCurrentIndex(self.prompt_combo.count() - 1)
    
    def search_contacts(self):
        """手动搜索联系人（保留兼容性）"""
        keyword = self.contact_search_input.text().strip()
        if not keyword:
            QMessageBox.warning(self, "提示", "请输入搜索关键字")
            return
        
        self.perform_search(keyword)
    
    def perform_search(self, keyword):
        """执行搜索操作"""
        # 获取chatlog服务URL
        config = self.config_page.get_config()
        chatlog_base_url = config.get('chatlog_service_url', 'http://127.0.0.1:5030/api/v1')
        
        # 清空之前的列表
        self.contact_list.clear()
        
        # 显示加载状态
        item = QListWidgetItem("正在搜索联系人...")
        item.setFlags(item.flags() & ~Qt.ItemIsEnabled)  # 禁用该项
        self.contact_list.addItem(item)
        QApplication.processEvents()  # 立即更新UI
        
        try:
            # 构建URL并进行编码
            encoded_keyword = urllib.parse.quote(keyword)
            url = f"{chatlog_base_url}/contact?keyword={encoded_keyword}&format=json"
            
            # 添加超时设置
            response = requests.get(url, timeout=(5, 30))  # 连接超时5秒，读取超时30秒
            
            if response.status_code == 200:
                data = response.json()
                self.contacts = data.get('items', [])
                
                # 更新联系人列表
                self.contact_list.clear()
                for contact in self.contacts:
                    display_name = contact.get('nickName') or contact.get('remark') or contact.get('userName')
                    item = QListWidgetItem(display_name)
                    item.setData(Qt.UserRole, contact)  # 存储完整联系人数据
                    self.contact_list.addItem(item)
                
                if not self.contacts:
                    item = QListWidgetItem("未找到匹配的联系人")
                    item.setFlags(item.flags() & ~Qt.ItemIsEnabled)  # 禁用该项
                    self.contact_list.addItem(item)
            else:
                error_msg = f"请求失败: {response.status_code}"
                if hasattr(response, 'text'):
                    error_msg += f" - {response.text}"
                # 不再显示错误弹窗，只在列表中显示错误信息
                self.contact_list.clear()
                item = QListWidgetItem("搜索失败")
                item.setFlags(item.flags() & ~Qt.ItemIsEnabled)  # 禁用该项
                self.contact_list.addItem(item)
        except requests.exceptions.Timeout:
            # 不再显示超时弹窗，只在列表中显示信息
            self.contact_list.clear()
            item = QListWidgetItem("搜索超时")
            item.setFlags(item.flags() & ~Qt.ItemIsEnabled)  # 禁用该项
            self.contact_list.addItem(item)
        except requests.exceptions.ConnectionError:
            # 不再显示连接错误弹窗，只在列表中显示信息
            self.contact_list.clear()
            item = QListWidgetItem("连接错误")
            item.setFlags(item.flags() & ~Qt.ItemIsEnabled)  # 禁用该项
            self.contact_list.addItem(item)
        except Exception as e:
            # 不再显示错误弹窗，只在列表中显示信息
            self.contact_list.clear()
            item = QListWidgetItem("搜索出错")
            item.setFlags(item.flags() & ~Qt.ItemIsEnabled)  # 禁用该项
            self.contact_list.addItem(item)
        finally:
            # 确保UI响应
            QApplication.processEvents()
    
    def on_contact_selected(self, item):
        """当联系人被选中时获取聊天记录"""
        contact = item.data(Qt.UserRole)
        if not contact:
            return
        
        self.selected_contact = contact  # 保存当前选中的联系人
        self.load_chat_for_contact(contact)
    
    def load_chat_for_contact(self, contact):
        """为指定联系人加载聊天记录"""
        # 获取chatlog服务URL
        config = self.config_page.get_config()
        chatlog_base_url = config.get('chatlog_service_url', 'http://127.0.0.1:5030/api/v1')
        
        # 显示加载状态
        self.chat_display.setHtml("<p style='text-align:center; margin-top:50px;'><b>正在加载聊天记录，请稍候...</b></p>")
        QApplication.processEvents()  # 立即更新UI
        
        selected_date = self.date_edit.date().toString("yyyy-MM-dd")
        talker = urllib.parse.quote(contact.get('userName', ''))
        
        try:
            url = f"{chatlog_base_url}/chatlog?time={selected_date}&talker={talker}"
            # 添加超时设置
            response = requests.get(url, timeout=(5, 30))  # 连接超时5秒，读取超时30秒
            
            if response.status_code == 200:
                # 假设返回的是HTML格式的聊天记录
                chat_content = response.text
                if not chat_content.strip():
                    self.chat_display.setHtml("<p style='text-align:center; margin-top:50px;'><b>该日期没有聊天记录</b></p>")
                else:
                    self.chat_display.setHtml(chat_content)
            else:
                error_msg = f"获取聊天记录失败: {response.status_code}"
                if hasattr(response, 'text'):
                    error_msg += f" - {response.text}"
                QMessageBox.warning(self, "错误", error_msg)
                self.chat_display.setHtml("<p style='color:red; text-align:center; margin-top:50px;'><b>获取聊天记录失败</b></p>")
        except requests.exceptions.Timeout:
            QMessageBox.warning(self, "超时", "获取聊天记录超时，请检查网络连接或稍后重试")
            self.chat_display.setHtml("<p style='color:red; text-align:center; margin-top:50px;'><b>获取聊天记录超时</b></p>")
        except requests.exceptions.ConnectionError:
            QMessageBox.warning(self, "连接错误", "连接错误，请检查网络连接或chatlog服务是否正常运行")
            self.chat_display.setHtml("<p style='color:red; text-align:center; margin-top:50px;'><b>连接错误，无法获取聊天记录</b></p>")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"获取聊天记录时出错: {str(e)}")
            self.chat_display.setHtml("<p style='color:red; text-align:center; margin-top:50px;'><b>获取聊天记录时出错</b></p>")
        finally:
            # 确保UI响应
            QApplication.processEvents()
    
    def summarize_chat(self):
        """使用DeepSeek API总结聊天记录"""
        # 获取配置
        config = self.config_page.get_config()
        api_key = config.get('api_key')
        api_url = config.get('api_url')
        model = config.get('model')
        
        if not api_key:
            QMessageBox.warning(self, "配置错误", "请先在配置页面设置DeepSeek API密钥")
            return
        
        # 获取聊天内容
        chat_content = self.chat_display.toPlainText()
        if not chat_content:
            QMessageBox.warning(self, "提示", "没有可总结的聊天记录")
            return
        
        # 检查聊天内容是否为错误提示
        if "正在加载聊天记录" in chat_content or "获取聊天记录失败" in chat_content or "获取聊天记录时出错" in chat_content:
            QMessageBox.warning(self, "提示", "当前显示的不是有效的聊天记录，无法进行总结")
            return
        
        # 获取提示词
        prompt = self.prompt_combo.currentText()
        
        # 准备消息
        messages = [
            {"role": "system", "content": "你是一个专业的聊天记录总结助手，擅长提取关键信息并进行简洁总结。"},
            {"role": "user", "content": f"{prompt}\n\n{chat_content}"}
        ]
        
        # 清空之前的总结
        self.summary_display.clear()
        
        try:
            # 创建并启动线程
            self.deepseek_thread = DeepSeekThread(api_key, api_url, model, messages)
            self.deepseek_thread.update_signal.connect(self.update_summary)
            self.deepseek_thread.finished_signal.connect(self.on_summary_finished)
            self.deepseek_thread.error_signal.connect(self.on_summary_error)
            self.deepseek_thread.start()
            
            # 禁用总结按钮
            self.summary_button.setEnabled(False)
            self.summary_button.setText("正在总结...")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"启动总结线程时出错: {str(e)}")
            self.summary_button.setEnabled(True)
    
    def update_summary(self, text):
        """更新总结内容（打字机效果）"""
        # 纯文本模式
        current_text = self.summary_display.toPlainText()
        self.summary_display.setPlainText(current_text + text)
        
        # 滚动到底部
        self.summary_display.verticalScrollBar().setValue(
            self.summary_display.verticalScrollBar().maximum()
        )
    
    def on_summary_finished(self):
        """总结完成时的处理"""
        self.summary_button.setEnabled(True)
        self.summary_button.setText("一键总结")
    
    def on_summary_error(self, error_msg):
        """处理总结过程中的错误"""
        QMessageBox.critical(self, "总结错误", error_msg)
        self.summary_button.setEnabled(True)
        self.summary_button.setText("一键总结")