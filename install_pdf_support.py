#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF支持安装脚本

此脚本帮助安装PDF报告生成所需的依赖项。
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def check_wkhtmltopdf():
    """检查wkhtmltopdf是否已安装"""
    try:
        result = subprocess.run(['wkhtmltopdf', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ wkhtmltopdf 已安装")
            print(f"版本信息: {result.stdout.strip()}")
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    print("❌ wkhtmltopdf 未安装")
    return False

def check_pdfkit():
    """检查pdfkit是否已安装"""
    try:
        import pdfkit
        print("✅ pdfkit 已安装")
        return True
    except ImportError:
        print("❌ pdfkit 未安装")
        return False

def install_pdfkit():
    """安装pdfkit"""
    print("正在安装 pdfkit...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pdfkit'], 
                      check=True)
        print("✅ pdfkit 安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ pdfkit 安装失败: {e}")
        return False

def get_wkhtmltopdf_download_info():
    """获取wkhtmltopdf下载信息"""
    system = platform.system().lower()
    
    if system == 'windows':
        return {
            'url': 'https://wkhtmltopdf.org/downloads.html',
            'instructions': [
                "1. 访问 https://wkhtmltopdf.org/downloads.html",
                "2. 下载 Windows 版本的安装包",
                "3. 运行安装程序并按照提示安装",
                "4. 确保安装路径添加到系统 PATH 环境变量中",
                "5. 重启命令行或IDE后重新运行此脚本验证安装"
            ]
        }
    elif system == 'darwin':  # macOS
        return {
            'url': 'https://wkhtmltopdf.org/downloads.html',
            'instructions': [
                "使用 Homebrew 安装 (推荐):",
                "  brew install wkhtmltopdf",
                "",
                "或者手动下载:",
                "1. 访问 https://wkhtmltopdf.org/downloads.html",
                "2. 下载 macOS 版本",
                "3. 安装 .pkg 文件"
            ]
        }
    else:  # Linux
        return {
            'url': 'https://wkhtmltopdf.org/downloads.html',
            'instructions': [
                "Ubuntu/Debian:",
                "  sudo apt-get update",
                "  sudo apt-get install wkhtmltopdf",
                "",
                "CentOS/RHEL/Fedora:",
                "  sudo yum install wkhtmltopdf",
                "  # 或者 sudo dnf install wkhtmltopdf",
                "",
                "或者从官网下载: https://wkhtmltopdf.org/downloads.html"
            ]
        }

def main():
    print("🔧 PDF支持安装检查")
    print("=" * 50)
    
    # 检查当前状态
    pdfkit_installed = check_pdfkit()
    wkhtmltopdf_installed = check_wkhtmltopdf()
    
    print("\n📋 安装状态:")
    print(f"  pdfkit: {'✅ 已安装' if pdfkit_installed else '❌ 未安装'}")
    print(f"  wkhtmltopdf: {'✅ 已安装' if wkhtmltopdf_installed else '❌ 未安装'}")
    
    # 安装缺失的组件
    if not pdfkit_installed:
        print("\n🔧 安装 pdfkit...")
        if install_pdfkit():
            pdfkit_installed = True
    
    if not wkhtmltopdf_installed:
        print("\n🔧 安装 wkhtmltopdf")
        download_info = get_wkhtmltopdf_download_info()
        print("请按照以下步骤安装 wkhtmltopdf:")
        for instruction in download_info['instructions']:
            print(f"  {instruction}")
        print(f"\n📎 下载链接: {download_info['url']}")
    
    # 最终状态检查
    print("\n" + "=" * 50)
    if pdfkit_installed and wkhtmltopdf_installed:
        print("🎉 PDF支持已完全配置！")
        print("现在可以在Streamlit应用中生成PDF报告了。")
        
        # 测试PDF生成
        print("\n🧪 测试PDF生成功能...")
        try:
            from src.report_generator import ReportGenerator
            generator = ReportGenerator()
            deps = generator.check_dependencies()
            if deps['pdf']:
                print("✅ PDF生成功能测试通过")
            else:
                print("❌ PDF生成功能测试失败")
        except Exception as e:
            print(f"❌ PDF生成功能测试失败: {e}")
    else:
        print("⚠️  PDF支持配置未完成")
        print("请完成上述安装步骤后重新运行此脚本。")
    
    print("\n📖 使用说明:")
    print("1. 在Streamlit应用的侧边栏中选择 'pdf' 格式")
    print("2. 点击 '📊 生成报告' 按钮")
    print("3. 等待PDF生成完成后下载")

if __name__ == '__main__':
    main()