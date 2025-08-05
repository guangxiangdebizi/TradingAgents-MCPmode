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
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.colors import black, blue, red, grey
except ImportError:
    print("❌ 缺少依赖包，请安装：pip install reportlab")
    sys.exit(1)


class MarkdownToPDFConverter:
    """Markdown转PDF转换器"""
    
    def __init__(self, dump_dir: str = "src/dump"):
        """初始化转换器
        
        Args:
            dump_dir: dump文件夹路径
        """
        self.dump_dir = Path(dump_dir)
        self.markdown_dir = Path("markdown_reports")
        self.output_dir = Path("pdf_reports")
        
        # 确保输出目录存在
        self.output_dir.mkdir(exist_ok=True)
        
        # 注册中文字体
        self._register_fonts()
        
        # 初始化markdown转换器
        self.md_converter = JSONToMarkdownConverter(dump_dir)
    
    def _register_fonts(self):
        """注册中文字体"""
        try:
            # 尝试注册微软雅黑
            font_paths = [
                "C:/Windows/Fonts/msyh.ttc",  # 微软雅黑
                "C:/Windows/Fonts/simhei.ttf",  # 黑体
                "C:/Windows/Fonts/simsun.ttc",  # 宋体
            ]
            
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                        print(f"✅ 成功注册中文字体: {font_path}")
                        break
                    except Exception as e:
                        continue
            else:
                print("⚠️ 未找到中文字体，将使用默认字体")
                
        except Exception as e:
            print(f"⚠️ 字体注册失败: {e}")
    
    def _setup_styles(self):
        """设置PDF样式"""
        styles = getSampleStyleSheet()
        
        # 标题样式
        styles.add(ParagraphStyle(
            name='ChineseTitle',
            parent=styles['Title'],
            fontName='ChineseFont',
            fontSize=18,
            spaceAfter=20,
            alignment=TA_CENTER
        ))
        
        # 二级标题样式
        styles.add(ParagraphStyle(
            name='ChineseHeading1',
            parent=styles['Heading1'],
            fontName='ChineseFont',
            fontSize=14,
            spaceAfter=12,
            spaceBefore=12
        ))
        
        # 三级标题样式
        styles.add(ParagraphStyle(
            name='ChineseHeading2',
            parent=styles['Heading2'],
            fontName='ChineseFont',
            fontSize=12,
            spaceAfter=8,
            spaceBefore=8
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
            spaceBefore=6,
            leftIndent=20
        ))
        
        return styles
    
    def _parse_markdown_to_pdf_elements(self, markdown_content: str, styles):
        """解析Markdown内容为PDF元素"""
        elements = []
        lines = markdown_content.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if not line:
                elements.append(Spacer(1, 6))
                i += 1
                continue
            
            # 处理标题
            if line.startswith('# '):
                title = line[2:].strip()
                elements.append(Paragraph(title, styles['ChineseTitle']))
                elements.append(Spacer(1, 12))
            elif line.startswith('## '):
                heading = line[3:].strip()
                elements.append(Paragraph(heading, styles['ChineseHeading1']))
                elements.append(Spacer(1, 8))
            elif line.startswith('### '):
                heading = line[4:].strip()
                elements.append(Paragraph(heading, styles['ChineseHeading2']))
                elements.append(Spacer(1, 6))
            
            # 处理引用
            elif line.startswith('> '):
                quote = line[2:].strip()
                import html
                quote = html.escape(quote)
                elements.append(Paragraph(f"<i>{quote}</i>", styles['ChineseNormal']))
            
            # 处理列表
            elif line.startswith('- '):
                item = line[2:].strip()
                import html
                item = html.escape(item)
                elements.append(Paragraph(f"• {item}", styles['ChineseNormal']))
            
            # 处理表格
            elif '|' in line and line.strip().startswith('|'):
                # 收集表格行
                table_rows = []
                table_rows.append(line.strip())
                
                # 继续读取表格行
                j = i + 1
                while j < len(lines):
                    next_line = lines[j].strip()
                    if next_line and '|' in next_line and next_line.startswith('|'):
                        table_rows.append(next_line)
                        j += 1
                    else:
                        break
                
                # 解析表格并添加到文档
                if len(table_rows) > 1:
                    self._add_table_to_elements(table_rows, elements, styles)
                    i = j - 1  # 调整索引
            
            # 处理代码块
            elif line.startswith('```'):
                i += 1
                code_lines = []
                while i < len(lines) and not lines[i].strip().startswith('```'):
                    code_lines.append(lines[i])
                    i += 1
                
                if code_lines:
                    code_text = '\n'.join(code_lines)
                    # 保持完整内容，不进行截断
                    # HTML转义处理
                    code_text = self._escape_html_preserve_emoji(code_text)
                    elements.append(Paragraph(f"<pre>{code_text}</pre>", styles['ChineseCode']))
                    elements.append(Spacer(1, 6))
            
            # 处理普通文本
            else:
                if line:
                    import html
                    import re
                    # 先处理粗体文本（在转义前）
                    line = re.sub(r'\*\*(.*?)\*\*', r'<BOLD>\1</BOLD>', line)
                    # HTML转义处理（但保留emoji）
                    line = self._escape_html_preserve_emoji(line)
                    # 恢复粗体标签
                    line = line.replace('&lt;BOLD&gt;', '<b>').replace('&lt;/BOLD&gt;', '</b>')
                    elements.append(Paragraph(line, styles['ChineseNormal']))
            
            i += 1
        
        return elements
    
    def _escape_html_preserve_emoji(self, text):
        """HTML转义但保留emoji字符"""
        import html
        import re
        
        # 匹配emoji的正则表达式（Unicode范围）
        emoji_pattern = re.compile(
            r'[\U0001F600-\U0001F64F]|'  # 表情符号
            r'[\U0001F300-\U0001F5FF]|'  # 杂项符号和象形文字
            r'[\U0001F680-\U0001F6FF]|'  # 交通和地图符号
            r'[\U0001F1E0-\U0001F1FF]|'  # 区域指示符号
            r'[\U00002600-\U000026FF]|'  # 杂项符号
            r'[\U00002700-\U000027BF]|'  # 装饰符号
            r'[\U0001F900-\U0001F9FF]|'  # 补充符号和象形文字
            r'[\U0001FA70-\U0001FAFF]'   # 扩展A符号和象形文字
        )
        
        # 找到所有emoji
        emojis = emoji_pattern.findall(text)
        
        # 用占位符替换emoji
        temp_text = text
        placeholders = {}
        for i, emoji in enumerate(emojis):
            placeholder = f'__EMOJI_{i}__'
            placeholders[placeholder] = emoji
            temp_text = temp_text.replace(emoji, placeholder, 1)
        
        # HTML转义
        escaped_text = html.escape(temp_text)
        
        # 恢复emoji
        for placeholder, emoji in placeholders.items():
            escaped_text = escaped_text.replace(placeholder, emoji)
        
        return escaped_text
    
    def _add_table_to_elements(self, table_rows, elements, styles):
        """将表格添加到元素列表"""
        # 解析表格数据
        table_data = []
        for row in table_rows:
            # 移除首尾的|符号并分割
            cells = [cell.strip() for cell in row.strip('|').split('|')]
            # HTML转义处理（保留emoji）
            cells = [self._escape_html_preserve_emoji(cell) for cell in cells]
            table_data.append(cells)
        
        # 跳过分隔行（通常是第二行，包含---）
        if len(table_data) > 1 and all('---' in cell or '-' in cell for cell in table_data[1]):
            table_data.pop(1)
        
        if table_data:
            # 创建表格
            table = Table(table_data)
            
            # 设置表格样式
            table_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), grey),  # 表头背景
                ('TEXTCOLOR', (0, 0), (-1, 0), black),  # 表头文字颜色
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # 居中对齐
                ('FONTNAME', (0, 0), (-1, -1), 'ChineseFont'),  # 中文字体
                ('FONTSIZE', (0, 0), (-1, -1), 9),  # 字体大小
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),  # 底部填充
                ('TOPPADDING', (0, 0), (-1, -1), 6),  # 顶部填充
                ('GRID', (0, 0), (-1, -1), 1, black),  # 网格线
            ])
            
            table.setStyle(table_style)
            elements.append(table)
            elements.append(Spacer(1, 12))  # 添加间距
    
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
            doc = SimpleDocTemplate(str(pdf_file), pagesize=A4)
            styles = self._setup_styles()
            
            # 解析Markdown内容
            elements = self._parse_markdown_to_pdf_elements(markdown_content, styles)
            
            # 生成PDF
            doc.build(elements)
            
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