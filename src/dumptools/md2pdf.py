#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown to PDF Converter
基于json_to_markdown.py的两步转换：JSON → Markdown → PDF
"""

import os
import sys
from pathlib import Path
from typing import Optional, List
import argparse
from datetime import datetime

# 导入markdown转换器
from json_to_markdown import JSONToMarkdownConverter

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
except ImportError:
    print("❌ 缺少依赖包，请安装：pip install reportlab")
    sys.exit(1)

import os
import sys
from pathlib import Path
from typing import Optional, List, Tuple
import argparse
from datetime import datetime
import re
import html

# 导入自定义模块
from json_to_markdown import JSONToMarkdownConverter


class MarkdownToPDFConverter:
    """Markdown转PDF转换器"""
    
    def __init__(self, dump_dir: str = "src/dump"):
        """初始化转换器
        
        Args:
            dump_dir: dump文件夹路径
        """
        self.dump_dir = Path(dump_dir)
        # 保持原有的输出目录设置
        self.output_dir = self.dump_dir.parent / "output"
        self.output_dir.mkdir(exist_ok=True)
        
        # 初始化Markdown转换器
        from json_to_markdown import JSONToMarkdownConverter
        self.md_converter = JSONToMarkdownConverter(str(self.dump_dir))
        
        # 注册字体
        self._register_fonts()
    
    def _register_fonts(self):
        """注册中文字体和emoji字体"""
        try:
            # 注册中文字体
            font_paths = [
                "C:/Windows/Fonts/msyh.ttc",  # 微软雅黑
                "C:/Windows/Fonts/simhei.ttf",  # 黑体
                "C:/Windows/Fonts/simsun.ttc",  # 宋体
            ]
            
            for font_path in font_paths:
                if os.path.exists(font_path):
                    if font_path.endswith('.ttc'):
                        pdfmetrics.registerFont(TTFont('ChineseFont', font_path, subfontIndex=0))
                    else:
                        pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                    break
            
            # 注册emoji字体
            emoji_font_path = "C:/Windows/Fonts/seguiemj.ttf"  # Segoe UI Emoji
            if os.path.exists(emoji_font_path):
                pdfmetrics.registerFont(TTFont('EmojiFont', emoji_font_path))
            
        except Exception as e:
            print(f"⚠️ 字体注册失败: {e}")
    
    def _get_styles(self):
        """获取样式表"""
        styles = getSampleStyleSheet()
        
        # 标题样式
        styles.add(ParagraphStyle(
            name='ChineseTitle',
            parent=styles['Title'],
            fontName='ChineseFont',
            fontSize=18,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.black
        ))
        
        # 一级标题样式
        styles.add(ParagraphStyle(
            name='ChineseHeading1',
            parent=styles['Heading1'],
            fontName='ChineseFont',
            fontSize=16,
            spaceAfter=12,
            spaceBefore=12,
            textColor=colors.black
        ))
        
        # 二级标题样式
        styles.add(ParagraphStyle(
            name='ChineseHeading2',
            parent=styles['Heading2'],
            fontName='ChineseFont',
            fontSize=14,
            spaceAfter=10,
            spaceBefore=10,
            textColor=colors.black
        ))
        
        # 三级标题样式
        styles.add(ParagraphStyle(
            name='ChineseHeading3',
            parent=styles['Heading3'],
            fontName='ChineseFont',
            fontSize=12,
            spaceAfter=8,
            spaceBefore=8,
            textColor=colors.black
        ))
        
        # 四级标题样式
        styles.add(ParagraphStyle(
            name='ChineseHeading4',
            parent=styles['Heading3'],
            fontName='ChineseFont',
            fontSize=11,
            spaceAfter=6,
            spaceBefore=6,
            textColor=colors.black
        ))
        
        # 正文样式
        styles.add(ParagraphStyle(
            name='ChineseNormal',
            parent=styles['Normal'],
            fontName='ChineseFont',
            fontSize=10,
            spaceAfter=6,
            alignment=TA_JUSTIFY
        ))
        
        # 代码样式
        styles.add(ParagraphStyle(
            name='ChineseCode',
            parent=styles['Code'],
            fontName='Courier',
            fontSize=9,
            spaceAfter=6,
            leftIndent=20,
            backgroundColor=colors.lightgrey
        ))
        
        # 引用样式
        styles.add(ParagraphStyle(
            name='ChineseQuote',
            parent=styles['Normal'],
            fontName='ChineseFont',
            fontSize=10,
            leftIndent=20,
            rightIndent=20,
            spaceAfter=6,
            textColor=colors.grey
        ))
        
        return styles
    
    def _process_emoji_text(self, text):
        """处理文本中的emoji，使用合适的字体"""
        # 检测emoji并用特殊标记包围
        emoji_pattern = r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002600-\U000027BF\U0001F900-\U0001F9FF\U0001F018-\U0001F270]'
        
        def replace_emoji(match):
            emoji = match.group(0)
            return f'<font name="EmojiFont">{emoji}</font>'
        
        return re.sub(emoji_pattern, replace_emoji, text)
    
    def _parse_markdown_to_pdf_elements(self, markdown_content: str, styles) -> List:
        """解析Markdown内容为PDF元素"""
        elements = []
        lines = markdown_content.split('\n')
        i = 0
        page_num = 1  # 简化的页码计算
        
        while i < len(lines):
            line = lines[i].strip()
            
            if not line:
                elements.append(Spacer(1, 6))
                i += 1
                continue
            
            # 处理标题
            if line.startswith('#'):
                level = len(line) - len(line.lstrip('#'))
                title = line.lstrip('#').strip()
                
                # 添加到目录
                self.toc_entries.append((level, title, page_num))
                
                # 处理emoji
                title_with_emoji = self._process_emoji_text(title)
                
                if level == 1:
                    elements.append(Paragraph(title_with_emoji, styles['ChineseHeading1']))
                elif level == 2:
                    elements.append(Paragraph(title_with_emoji, styles['ChineseHeading2']))
                elif level == 3:
                    elements.append(Paragraph(title_with_emoji, styles['ChineseHeading3']))
                else:
                    elements.append(Paragraph(title_with_emoji, styles['ChineseHeading4']))
            
            i += 1
        
        return elements
    
    def convert_json_to_pdf_via_markdown(self, json_file_path: str) -> Optional[str]:
        """通过Markdown中间步骤将JSON转换为PDF
        
        Args:
            json_file_path: JSON文件路径
            
        Returns:
            生成的PDF文件路径，失败返回None
        """
        try:
            # 第一步：JSON转Markdown
            print(f"📄 第一步：将JSON转换为Markdown...")
            md_file_path = self.md_converter.convert_json_to_markdown(json_file_path)
            
            if not md_file_path or not os.path.exists(md_file_path):
                print("❌ Markdown转换失败")
                return None
            
            # 第二步：Markdown转PDF
            print(f"📄 第二步：将Markdown转换为PDF...")
            
            # 读取Markdown文件
            with open(md_file_path, 'r', encoding='utf-8') as f:
                markdown_content = f.read()
            
            # 生成PDF文件名
            json_filename = Path(json_file_path).stem
            pdf_file = self.output_dir / f"{json_filename}.pdf"
            
            # 创建PDF文档
            doc = SimpleDocTemplate(
                str(pdf_file),
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # 获取样式
            styles = self._get_styles()
            
            # 重置目录项
            self.toc_entries = []
            
            # 解析Markdown内容
            content_elements = self._parse_markdown_to_pdf_elements(markdown_content, styles)
            
            # 创建完整的文档结构：目录 + 内容
            story = []
            
            # 添加目录
            if self.toc_entries:
                toc_elements = self._create_toc(styles)
                story.extend(toc_elements)
            
            # 添加内容
            story.extend(content_elements)
            
            # 构建PDF
            doc.build(story)
            
            print(f"✅ PDF报告已生成: {pdf_file}")
            return str(pdf_file)
            
        except Exception as e:
            print(f"❌ 转换失败: {e}")
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
            return self.convert_json_to_pdf_via_markdown(str(latest_json))
            
        except Exception as e:
            print(f"❌ 转换过程中发生错误: {e}")
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
                result = self.convert_json_to_pdf_via_markdown(str(json_file))
                if result:
                    results.append(result)
            
            return results
            
        except Exception as e:
            print(f"❌ 批量转换过程中发生错误: {e}")
            return []


def main():
    """主函数 - 命令行工具"""
    parser = argparse.ArgumentParser(
        description="Markdown to PDF Converter - 通过Markdown中间步骤将JSON转换为PDF"
    )
    parser.add_argument("-f", "--file", help="指定要转换的JSON文件路径")
    parser.add_argument("-l", "--latest", action="store_true", help="转换最新的JSON文件")
    parser.add_argument("-a", "--all", action="store_true", help="转换所有JSON文件")
    parser.add_argument("-d", "--dump-dir", default="src/dump", help="dump文件夹路径")
    
    args = parser.parse_args()
    
    converter = MarkdownToPDFConverter(args.dump_dir)
    
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
            result = converter.convert_json_to_pdf_via_markdown(args.file)
            if result:
                print(f"🎉 转换完成: {result}")
        else:
            print(f"❌ 文件不存在: {args.file}")
    
    else:
        # 默认转换最新文件
        result = converter.convert_latest_json()
        if result:
            print(f"🎉 转换完成: {result}")


if __name__ == "__main__":
    main()