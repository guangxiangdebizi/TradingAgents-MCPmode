#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSON to PDF Converter (via Markdown)
采用两步转换流程：JSON → Markdown → PDF
"""

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

try:
    import markdown2
    from weasyprint import HTML, CSS
    from weasyprint.fonts import FontConfiguration
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
    try:
        import markdown2
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib import colors
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
        import re
        REPORTLAB_AVAILABLE = True
    except ImportError:
        REPORTLAB_AVAILABLE = False
        print("⚠️ PDF导出依赖未安装，请选择以下之一:")
        print("📦 推荐方案: pip install markdown2 weasyprint")
        print("📦 备选方案: pip install markdown2 reportlab")

try:
    from .json_to_markdown import JSONToMarkdownConverter
except ImportError:
    # 如果相对导入失败，尝试绝对导入
    import sys
    import os
    from pathlib import Path
    
    # 添加当前目录到路径
    current_dir = Path(__file__).parent
    sys.path.insert(0, str(current_dir))
    
    # 尝试导入
    try:
        from json_to_markdown import JSONToMarkdownConverter
    except ImportError:
        # 如果还是失败，尝试从上级目录导入
        parent_dir = current_dir.parent
        sys.path.insert(0, str(parent_dir))
        from dumptools.json_to_markdown import JSONToMarkdownConverter


class JSONToPDFConverter:
    """JSON转PDF转换器（通过Markdown中间格式）"""
    
    def __init__(self, dump_dir: str = "src/dump"):
        """初始化转换器
        
        Args:
            dump_dir: dump文件夹路径
        """
        if not (WEASYPRINT_AVAILABLE or REPORTLAB_AVAILABLE):
            raise ImportError("PDF导出依赖未安装，请安装: pip install markdown2 weasyprint 或 pip install markdown2 reportlab")
            
        self.dump_dir = Path(dump_dir)
        self.output_dir = Path("pdf_reports")
        
        # 确保输出目录存在
        self.output_dir.mkdir(exist_ok=True)
        
        # 创建Markdown转换器
        self.markdown_converter = JSONToMarkdownConverter(dump_dir)
    
    def _get_css_styles(self) -> str:
        """获取PDF样式表"""
        return """
        @page {
            size: A4;
            margin: 2cm;
            @bottom-right {
                content: counter(page) "/" counter(pages);
            }
        }
        
        body {
            font-family: "Microsoft YaHei", "Segoe UI", Arial, sans-serif;
            font-size: 11pt;
            line-height: 1.6;
            color: #333;
        }
        
        h1 {
            font-size: 20pt;
            font-weight: bold;
            text-align: center;
            margin-bottom: 1em;
            color: #2c3e50;
        }
        
        h2 {
            font-size: 16pt;
            font-weight: bold;
            margin-top: 1.5em;
            margin-bottom: 0.5em;
            color: #34495e;
            border-bottom: 2px solid #3498db;
            padding-bottom: 0.2em;
        }
        
        h3 {
            font-size: 14pt;
            font-weight: bold;
            margin-top: 1em;
            margin-bottom: 0.5em;
            color: #34495e;
        }
        
        p {
            margin-bottom: 0.5em;
            text-align: justify;
        }
        
        ul, ol {
            margin-bottom: 1em;
            padding-left: 2em;
        }
        
        li {
            margin-bottom: 0.3em;
        }
        
        blockquote {
            margin: 1em 0;
            padding: 0.5em 1em;
            background-color: #f8f9fa;
            border-left: 4px solid #3498db;
            font-style: italic;
        }
        
        code {
            font-family: "Consolas", "Monaco", monospace;
            font-size: 9pt;
            background-color: #f8f9fa;
            padding: 0.2em 0.4em;
            border-radius: 3px;
        }
        
        pre {
            background-color: #f8f9fa;
            padding: 1em;
            border-radius: 5px;
            border: 1px solid #e9ecef;
            overflow-x: auto;
            margin: 1em 0;
        }
        
        pre code {
            background-color: transparent;
            padding: 0;
        }
        
        .emoji {
            font-family: "Segoe UI Emoji", "Apple Color Emoji", "Noto Color Emoji";
        }
        
        hr {
            border: none;
            border-top: 1px solid #bdc3c7;
            margin: 2em 0;
        }
        
        .footer {
            text-align: center;
            font-style: italic;
            color: #7f8c8d;
            margin-top: 2em;
        }
        """
    
    def _markdown_to_pdf_weasyprint(self, markdown_content: str, output_path: str) -> bool:
        """使用WeasyPrint将Markdown转换为PDF"""
        try:
            # 将Markdown转换为HTML
            html_content = markdown2.markdown(
                markdown_content,
                extras=[
                    'fenced-code-blocks',
                    'tables',
                    'break-on-newline',
                    'strike',
                    'task_list'
                ]
            )
            
            # 添加HTML框架和样式
            full_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                {self._get_css_styles()}
                </style>
            </head>
            <body>
                {html_content}
            </body>
            </html>
            """
            
            # 生成PDF
            HTML(string=full_html).write_pdf(output_path)
            return True
            
        except Exception as e:
            print(f"⚠️ WeasyPrint转换失败: {e}")
            return False
    
    def _markdown_to_pdf_reportlab(self, markdown_content: str, output_path: str) -> bool:
        """使用ReportLab将Markdown转换为PDF（备选方案）"""
        try:
            # 简化的Markdown解析和转换
            doc = SimpleDocTemplate(output_path, pagesize=A4)
            story = []
            
            # 简单处理Markdown内容
            lines = markdown_content.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    story.append(Spacer(1, 6))
                elif line.startswith('# '):
                    # 一级标题
                    story.append(Paragraph(line[2:], self._get_title_style()))
                elif line.startswith('## '):
                    # 二级标题
                    story.append(Paragraph(line[3:], self._get_heading_style()))
                elif line.startswith('### '):
                    # 三级标题
                    story.append(Paragraph(line[4:], self._get_subheading_style()))
                elif line.startswith('- ') or line.startswith('* '):
                    # 列表项
                    story.append(Paragraph(f"• {line[2:]}", self._get_normal_style()))
                elif line.startswith('> '):
                    # 引用
                    story.append(Paragraph(line[2:], self._get_quote_style()))
                elif line.startswith('```'):
                    # 代码块（简化处理）
                    continue
                else:
                    # 正文
                    if line:
                        story.append(Paragraph(line, self._get_normal_style()))
            
            doc.build(story)
            return True
            
        except Exception as e:
            print(f"⚠️ ReportLab转换失败: {e}")
            return False
    
    def _get_title_style(self):
        """获取标题样式"""
        return ParagraphStyle(
            'Title',
            fontSize=20,
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
    
    def _get_heading_style(self):
        """获取一级标题样式"""
        return ParagraphStyle(
            'Heading1',
            fontSize=16,
            spaceAfter=12,
            fontName='Helvetica-Bold'
        )
    
    def _get_subheading_style(self):
        """获取二级标题样式"""
        return ParagraphStyle(
            'Heading2',
            fontSize=14,
            spaceAfter=10,
            fontName='Helvetica-Bold'
        )
    
    def _get_normal_style(self):
        """获取正文样式"""
        return ParagraphStyle(
            'Normal',
            fontSize=11,
            spaceAfter=6,
            alignment=TA_JUSTIFY,
            fontName='Helvetica'
        )
    
    def _get_quote_style(self):
        """获取引用样式"""
        return ParagraphStyle(
            'Quote',
            fontSize=11,
            spaceAfter=6,
            leftIndent=20,
            fontName='Helvetica-Oblique'
        )
    
    def convert_json_to_pdf(self, json_file_path: str) -> Optional[str]:
        """将JSON文件转换为PDF（通过Markdown中间格式）
        
        Args:
            json_file_path: JSON文件路径
            
        Returns:
            生成的PDF文件路径，失败返回None
        """
        try:
            # 第一步：将JSON转换为Markdown
            print(f"📄 步骤1: 将JSON转换为Markdown...")
            
            # 使用临时文件存放Markdown内容
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as temp_md:
                temp_md_path = temp_md.name
            
            # 调用Markdown转换器
            md_result = self.markdown_converter.convert_json_to_markdown(json_file_path)
            if not md_result:
                print(f"❌ 第一步失败：JSON转换为Markdown失败")
                return None
            
            # 读取生成的Markdown内容
            with open(md_result, 'r', encoding='utf-8') as f:
                markdown_content = f.read()
            
            # 第二步：将Markdown转换为PDF
            print(f"📄 步骤2: 将Markdown转换为PDF...")
            
            # 生成输出文件名
            json_filename = Path(json_file_path).stem
            output_file = self.output_dir / f"{json_filename}.pdf"
            
            # 尝试使用WeasyPrint（推荐）
            if WEASYPRINT_AVAILABLE:
                success = self._markdown_to_pdf_weasyprint(markdown_content, str(output_file))
                if success:
                    print(f"✅ PDF报告已生成: {output_file}")
                    return str(output_file)
                else:
                    print(f"⚠️ WeasyPrint失败，尝试使用ReportLab...")
            
            # 备选：使用ReportLab
            if REPORTLAB_AVAILABLE:
                success = self._markdown_to_pdf_reportlab(markdown_content, str(output_file))
                if success:
                    print(f"✅ PDF报告已生成: {output_file}")
                    return str(output_file)
                else:
                    print(f"❌ ReportLab也失败了")
            
            print(f"❌ PDF转换失败：没有可用的PDF生成器")
            return None
            
        except Exception as e:
            print(f"❌ PDF转换失败: {e}")
            return None
    

    
    def convert_latest_json(self) -> Optional[str]:
        """转换最新的JSON文件
        
        Returns:
            生成的PDF文件路径，失败返回None
        """
        try:
            # 查找dump目录下的所有JSON文件
            json_files = list(self.dump_dir.glob("session_*.json"))
            
            if not json_files:
                print(f"❌ 在 {self.dump_dir} 目录下未找到JSON文件")
                return None
            
            # 找到最新的文件
            latest_json = max(json_files, key=lambda f: f.stat().st_mtime)
            print(f"📄 找到最新的JSON文件: {latest_json.name}")
            
            # 转换为PDF
            return self.convert_json_to_pdf(str(latest_json))
            
        except Exception as e:
            print(f"❌ PDF转换过程中发生错误: {e}")
            return None
    
    def convert_all_json(self) -> List[str]:
        """转换所有JSON文件
        
        Returns:
            生成的PDF文件路径列表
        """
        try:
            # 查找dump目录下的所有JSON文件
            json_files = list(self.dump_dir.glob("session_*.json"))
            
            if not json_files:
                print(f"❌ 在 {self.dump_dir} 目录下未找到JSON文件")
                return []
            
            results = []
            for json_file in json_files:
                print(f"📄 转换文件: {json_file.name}")
                result = self.convert_json_to_pdf(str(json_file))
                if result:
                    results.append(result)
            
            return results
            
        except Exception as e:
            print(f"❌ PDF批量转换过程中发生错误: {e}")
            return []


def main():
    """主函数 - 命令行工具"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="JSON to PDF Converter - 将dump文件夹下的JSON文档转换为PDF"
    )
    parser.add_argument("-f", "--file", help="指定要转换的JSON文件路径")
    parser.add_argument("-l", "--latest", action="store_true", help="转换最新的JSON文件")
    parser.add_argument("-a", "--all", action="store_true", help="转换所有JSON文件")
    parser.add_argument("-d", "--dump-dir", default="src/dump", help="dump文件夹路径")
    
    args = parser.parse_args()
    
    try:
        converter = JSONToPDFConverter(args.dump_dir)
        
        if args.all:
            # 转换所有文件
            results = converter.convert_all_json()
            if results:
                print(f"🎉 批量转换完成，共生成 {len(results)} 个PDF文件")
            else:
                print("❌ 批量转换失败")
        
        elif args.latest:
            # 转换最新文件
            result = converter.convert_latest_json()
            if result:
                print(f"🎉 转换完成: {result}")
        
        elif args.file:
            # 转换指定文件
            if os.path.exists(args.file):
                result = converter.convert_json_to_pdf(args.file)
                if result:
                    print(f"🎉 转换完成: {result}")
            else:
                print(f"❌ 文件不存在: {args.file}")
        
        else:
            # 默认转换最新文件
            result = converter.convert_latest_json()
            if result:
                print(f"🎉 转换完成: {result}")
                
    except ImportError as e:
        print(f"❌ 依赖缺失: {e}")
        print("📦 请安装必要的依赖:")
        print("   pip install reportlab markdown2")


if __name__ == "__main__":
    main()
