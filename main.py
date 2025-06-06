import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QVBoxLayout, QWidget
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt

from config_page import ConfigPage
from summary_page import SummaryPage
import ctypes

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.setup_style()
        self.showMaximized()
    
    def setup_style(self):
        """设置应用样式"""
        # 设置窗口标题和图标
        self.setWindowTitle("DeepSeek聊天总结工具")
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.svg")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # 设置窗口大小和位置
        self.setMinimumSize(1000, 700)
        self.setGeometry(100, 100, 1200, 800)
        
        # 设置全局字体
        app = QApplication.instance()
        font = QFont("微软雅黑", 9)
        app.setFont(font)
        
        # 设置全局样式
        app.setStyle("Fusion")
        
        # 设置标签页样式
        tab_style = """
            QTabWidget::pane {
                border: 1px solid #cccccc;
                background: white;
                border-radius: 4px;
            }
            QTabWidget::tab-bar {
                left: 5px;
            }
            QTabBar::tab {
                background: #f0f0f0;
                border: 1px solid #cccccc;
                border-bottom-color: #cccccc;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 8px 12px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #4a86e8;
                color: white;
            }
            QTabBar::tab:!selected {
                margin-top: 2px;
            }
        """
        self.tab_widget.setStyleSheet(tab_style)
    
    def init_ui(self):
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建标签页部件
        self.tab_widget = QTabWidget()
        
        # 创建配置页面
        self.config_page = ConfigPage()
        
        # 创建聊天记录总结页面
        self.summary_page = SummaryPage(self.config_page)
        
        # 添加标签页
        self.tab_widget.addTab(self.summary_page, "聊天记录总结")
        self.tab_widget.addTab(self.config_page, "配置")
        
        # 添加标签页部件到主布局
        main_layout.addWidget(self.tab_widget)

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if __name__ == "__main__":
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized()  # 启动时最大化窗口
    sys.exit(app.exec_())