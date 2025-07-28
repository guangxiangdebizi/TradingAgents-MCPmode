#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交易分析报告生成工具

支持将JSON格式的交易分析结果转换为多种格式的报告：
- Markdown (.md)
- Word文档 (.docx) - 需要安装 python-docx
- PDF文档 (.pdf) - 需要安装 pdfkit 和 wkhtmltopdf

使用方法:
    python generate_report.py input.json --format markdown --output report.md
    python generate_report.py input.json --format docx --output report.docx
    python generate_report.py input.json --format pdf --output report.pdf
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.report_generator import ReportGenerator
from loguru import logger


def load_json_data(file_path: str) -> Dict[str, Any]:
    """加载JSON数据文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"文件不存在: {file_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"JSON格式错误: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"读取文件失败: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="交易分析报告生成工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python generate_report.py data.json --format markdown
  python generate_report.py data.json --format docx --output my_report.docx
  python generate_report.py data.json --format pdf --title "我的交易分析报告"

支持的格式:
  markdown, md    - Markdown格式 (默认)
  docx, word      - Microsoft Word文档 (需要 python-docx)
  pdf             - PDF文档 (需要 pdfkit 和 wkhtmltopdf)
        """
    )
    
    parser.add_argument(
        'input_file',
        help='输入的JSON数据文件路径'
    )
    
    parser.add_argument(
        '--format', '-f',
        choices=['markdown', 'md', 'docx', 'word', 'pdf'],
        default='markdown',
        help='输出格式 (默认: markdown)'
    )
    
    parser.add_argument(
        '--output', '-o',
        help='输出文件路径 (如果不指定，将自动生成)'
    )
    
    parser.add_argument(
        '--title', '-t',
        default='交易分析报告',
        help='报告标题 (默认: 交易分析报告)'
    )
    
    parser.add_argument(
        '--check-deps',
        action='store_true',
        help='检查依赖项并退出'
    )
    
    parser.add_argument(
        '--list-formats',
        action='store_true',
        help='列出支持的格式并退出'
    )
    
    args = parser.parse_args()
    
    # 创建报告生成器
    generator = ReportGenerator()
    
    # 检查依赖项
    if args.check_deps:
        deps = generator.check_dependencies()
        print("依赖项检查结果:")
        for format_name, available in deps.items():
            status = "✅ 可用" if available else "❌ 不可用"
            print(f"  {format_name}: {status}")
        
        if not deps['docx']:
            print("\n安装DOCX支持: pip install python-docx")
        if not deps['pdf']:
            print("\n安装PDF支持:")
            print("  1. pip install pdfkit")
            print("  2. 下载并安装 wkhtmltopdf: https://wkhtmltopdf.org/downloads.html")
        
        sys.exit(0)
    
    # 列出支持的格式
    if args.list_formats:
        formats = generator.get_supported_formats()
        print("支持的输出格式:")
        for fmt in formats:
            print(f"  - {fmt}")
        sys.exit(0)
    
    # 检查输入文件
    if not Path(args.input_file).exists():
        logger.error(f"输入文件不存在: {args.input_file}")
        sys.exit(1)
    
    # 检查格式是否支持
    if args.format not in generator.get_supported_formats():
        logger.error(f"不支持的格式: {args.format}")
        logger.info(f"支持的格式: {generator.get_supported_formats()}")
        sys.exit(1)
    
    try:
        # 加载数据
        logger.info(f"正在加载数据文件: {args.input_file}")
        data = load_json_data(args.input_file)
        
        # 生成报告
        logger.info(f"正在生成 {args.format} 格式的报告...")
        output_path = generator.generate_report(
            data=data,
            output_format=args.format,
            output_path=args.output,
            title=args.title
        )
        
        print(f"\n✅ 报告生成成功!")
        print(f"📄 文件路径: {Path(output_path).absolute()}")
        print(f"📊 格式: {args.format.upper()}")
        print(f"📝 标题: {args.title}")
        
        # 显示文件大小
        file_size = Path(output_path).stat().st_size
        if file_size < 1024:
            size_str = f"{file_size} B"
        elif file_size < 1024 * 1024:
            size_str = f"{file_size / 1024:.1f} KB"
        else:
            size_str = f"{file_size / (1024 * 1024):.1f} MB"
        print(f"📦 文件大小: {size_str}")
        
    except Exception as e:
        logger.error(f"生成报告失败: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()