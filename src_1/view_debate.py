#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的HTML查看器 - 直接在浏览器中打开辩论报告
"""

import webbrowser
import os
from pathlib import Path

def open_debate_report():
    """打开辩论报告HTML文件"""
    html_file = Path("debate_dynamic.html").absolute()
    
    if html_file.exists():
        # 使用file://协议在浏览器中打开HTML文件
        file_url = f"file:///{html_file.as_posix()}"
        print(f"🚀 正在打开辩论报告页面...")
        print(f"📍 文件路径: {html_file}")
        print(f"🌐 浏览器地址: {file_url}")
        
        webbrowser.open(file_url)
        print("✅ 页面已在默认浏览器中打开")
    else:
        print("❌ HTML文件不存在:", html_file)

if __name__ == "__main__":
    open_debate_report()
