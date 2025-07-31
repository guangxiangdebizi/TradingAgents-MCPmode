#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一导出工具
支持将dump文件夹下的JSON文档导出为多种格式
"""

import argparse
import os
from pathlib import Path
from datetime import datetime

from . import JSONToMarkdownConverter, PDF_AVAILABLE, DOCX_AVAILABLE

if PDF_AVAILABLE:
    from . import JSONToPDFConverter

if DOCX_AVAILABLE:
    from . import JSONToDocxConverter


def main():
    """主函数 - 统一导出工具"""
    parser = argparse.ArgumentParser(
        description="统一导出工具 - 将dump文件夹下的JSON文档转换为多种格式",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
支持的导出格式:
  markdown (md)  - Markdown文档 (总是可用)
  pdf           - PDF文档 (需要安装: pip install reportlab markdown2)
  docx          - Word文档 (需要安装: pip install python-docx)

使用示例:
  python -m src.dumptools.export_tool --format markdown --latest
  python -m src.dumptools.export_tool --format pdf --all
  python -m src.dumptools.export_tool --format docx --file session_123.json
  python -m src.dumptools.export_tool --format all --latest
        """
    )
    
    parser.add_argument(
        "--format", "-f",
        choices=['markdown', 'md', 'pdf', 'docx', 'all'],
        default='markdown',
        help="导出格式 (默认: markdown)"
    )
    parser.add_argument(
        "--file",
        help="指定要转换的JSON文件路径"
    )
    parser.add_argument(
        "--latest", "-l",
        action="store_true",
        help="转换最新的JSON文件"
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="转换所有JSON文件"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="列出所有可用的JSON文件"
    )
    parser.add_argument(
        "--dump-dir", "-d",
        default="src/dump",
        help="dump文件夹路径 (默认: src/dump)"
    )
    
    args = parser.parse_args()
    
    # 显示可用格式
    available_formats = ['markdown']
    if PDF_AVAILABLE:
        available_formats.append('pdf')
    if DOCX_AVAILABLE:
        available_formats.append('docx')
    
    print(f"📋 可用的导出格式: {', '.join(available_formats)}")
    
    # 列出文件
    if args.list:
        converter = JSONToMarkdownConverter(args.dump_dir)
        files = converter.list_available_json_files()
        if files:
            print("\n📁 可用的JSON文件:")
            for i, file_path in enumerate(files, 1):
                file_name = Path(file_path).name
                file_time = datetime.fromtimestamp(Path(file_path).stat().st_mtime)
                print(f"  {i}. {file_name} ({file_time.strftime('%Y-%m-%d %H:%M:%S')})")
        else:
            print("❌ 未找到任何JSON文件")
        return
    
    # 检查格式可用性
    if args.format == 'pdf' and not PDF_AVAILABLE:
        print("❌ PDF导出不可用，请安装: pip install reportlab markdown2")
        return
    
    if args.format == 'docx' and not DOCX_AVAILABLE:
        print("❌ DOCX导出不可用，请安装: pip install python-docx")
        return
    
    # 执行导出
    results = []
    formats_to_export = []
    
    if args.format == 'all':
        formats_to_export = available_formats
    else:
        format_name = 'markdown' if args.format == 'md' else args.format
        if format_name in available_formats:
            formats_to_export = [format_name]
        else:
            print(f"❌ 不支持的格式: {args.format}")
            return
    
    print(f"\n🚀 开始导出，格式: {', '.join(formats_to_export)}")
    
    for format_name in formats_to_export:
        print(f"\n📝 正在导出 {format_name.upper()} 格式...")
        
        # 创建对应的转换器
        if format_name == 'markdown':
            converter = JSONToMarkdownConverter(args.dump_dir)
        elif format_name == 'pdf':
            converter = JSONToPDFConverter(args.dump_dir)
        elif format_name == 'docx':
            converter = JSONToDocxConverter(args.dump_dir)
        
        # 执行转换
        try:
            if args.all:
                format_results = converter.convert_all_json()
                if format_results:
                    results.extend(format_results)
                    print(f"✅ {format_name.upper()} 批量转换完成，共生成 {len(format_results)} 个文件")
                else:
                    print(f"❌ {format_name.upper()} 批量转换失败")
            
            elif args.latest:
                result = converter.convert_latest_json()
                if result:
                    results.append(result)
                    print(f"✅ {format_name.upper()} 转换完成: {result}")
                else:
                    print(f"❌ {format_name.upper()} 转换失败")
            
            elif args.file:
                if os.path.exists(args.file):
                    if format_name == 'markdown':
                        result = converter.convert_json_to_markdown(args.file)
                    elif format_name == 'pdf':
                        result = converter.convert_json_to_pdf(args.file)
                    elif format_name == 'docx':
                        result = converter.convert_json_to_docx(args.file)
                    
                    if result:
                        results.append(result)
                        print(f"✅ {format_name.upper()} 转换完成: {result}")
                    else:
                        print(f"❌ {format_name.upper()} 转换失败")
                else:
                    print(f"❌ 文件不存在: {args.file}")
            
            else:
                # 默认转换最新文件
                result = converter.convert_latest_json()
                if result:
                    results.append(result)
                    print(f"✅ {format_name.upper()} 转换完成: {result}")
                else:
                    print(f"❌ {format_name.upper()} 转换失败")
                    
        except Exception as e:
            print(f"❌ {format_name.upper()} 转换过程中发生错误: {e}")
    
    # 总结
    if results:
        print(f"\n🎉 导出完成！共生成 {len(results)} 个文件:")
        for result in results:
            print(f"  📄 {result}")
    else:
        print("\n❌ 没有文件被成功导出")


if __name__ == "__main__":
    main()
