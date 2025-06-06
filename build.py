import os
import sys
import shutil
from PyInstaller.__main__ import run

def build_app():
    """打包应用为单个可执行文件"""
    print("开始打包应用...")
    
    # 清理之前的构建文件
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    if os.path.exists('build'):
        shutil.rmtree('build')
    
    # 定义打包参数
    args = [
        '--name=DeepSeek聊天总结工具',
        '--onefile',
        '--windowed',
        '--clean',
        '--add-data=icon.svg;.',  # 添加图标文件
        'main.py'
    ]
    
    # 运行PyInstaller
    run(args)
    
    print("打包完成！可执行文件位于 dist 目录。")
    print("注意：此应用需要外部chatlog服务运行，请确保chatlog服务已启动并配置正确的服务地址。")

if __name__ == "__main__":
    build_app()