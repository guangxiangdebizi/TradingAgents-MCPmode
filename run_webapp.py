#!/usr/bin/env python3
"""
智能交易分析系统 - Web应用启动脚本

这个脚本用于启动Streamlit web应用界面。

使用方法:
    python run_webapp.py
    
或者直接运行:
    streamlit run streamlit_app.py
"""

import subprocess
import sys
import os
from pathlib import Path

def check_dependencies():
    """检查必要的依赖"""
    required_packages = ['streamlit', 'loguru', 'asyncio']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ 缺少以下依赖包: {', '.join(missing_packages)}")
        print("请运行以下命令安装:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True

def main():
    """主函数"""
    print("🚀 启动智能交易分析系统 Web 应用...")
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 获取当前脚本目录
    current_dir = Path(__file__).parent
    streamlit_app_path = current_dir / "streamlit_app.py"
    
    # 检查streamlit_app.py是否存在
    if not streamlit_app_path.exists():
        print(f"❌ 找不到 streamlit_app.py 文件: {streamlit_app_path}")
        sys.exit(1)
    
    # 启动Streamlit应用
    try:
        print(f"📱 启动 Streamlit 应用: {streamlit_app_path}")
        print("🌐 应用将在浏览器中自动打开")
        print("⏹️  按 Ctrl+C 停止应用")
        print("-" * 50)
        
        # 运行streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            str(streamlit_app_path),
            "--server.address", "localhost",
            "--server.port", "8501",
            "--browser.gatherUsageStats", "false"
        ])
        
    except KeyboardInterrupt:
        print("\n👋 应用已停止")
    except Exception as e:
        print(f"❌ 启动应用时发生错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()