#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown to PDF Converter
基于json_to_markdown.py的两步转换：JSON → Markdown → PDF
"""

import os
import sys
from pathlib import Path
from typing import Optional, List, Tuple
import argparse
from datetime import datetime
import re
import html

# 导入markdown转换器
try:
    from .json_to_markdown import JSONToMarkdownConverter
except ImportError:
    try:
        from json_to_markdown import JSONToMarkdownConverter
    except ImportError:
        from src.dumptools.json_to_markdown import JSONToMarkdownConverter

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

class MarkdownToPDFConverter:
    """Markdown转PDF转换器"""
    
    def __init__(self, dump_dir: str = "src/dump"):
        """初始化转换器
        
        Args:
            dump_dir: dump文件夹路径
        """
        self.dump_dir = Path(dump_dir)
        # 输出到 dumptools/pdf_reports/ 目录
        self.output_dir = Path(__file__).parent / "pdf_reports"
        self.output_dir.mkdir(exist_ok=True)
        
        # 初始化Markdown转换器
        self.md_converter = JSONToMarkdownConverter(str(self.dump_dir))
        
        # 注册字体
        self._register_fonts()
    
    def _register_fonts(self):
        """注册中文字体和emoji字体（含加粗族）"""
        try:
            # 候选字体（Windows/macOS/Linux 常见路径）
            candidates_regular = [
                # Windows
                "C:/Windows/Fonts/msyh.ttc",  # 微软雅黑(集)
                "C:/Windows/Fonts/msyh.ttf",
                "C:/Windows/Fonts/simhei.ttf",  # 黑体
                "C:/Windows/Fonts/simsun.ttc",  # 宋体(集)
                # macOS
                "/System/Library/Fonts/PingFang.ttc",
                "/System/Library/Fonts/STHeiti Light.ttc",
                # Linux (Noto)
                "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                "/usr/share/fonts/opentype/noto/NotoSansCJKSC-Regular.otf",
                "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
            ]

            candidates_bold = [
                # Windows
                "C:/Windows/Fonts/msyhbd.ttc",  # 微软雅黑 Bold(集)
                "C:/Windows/Fonts/msyhbd.ttf",
                "C:/Windows/Fonts/simhei.ttf",  # 黑体作为粗体替代
                # macOS
                "/System/Library/Fonts/PingFang.ttc",
                # Linux (Noto)
                "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
                "/usr/share/fonts/opentype/noto/NotoSansCJKSC-Bold.otf",
                "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
            ]

            def register_one(name: str, path: str, subfont_index: int | None = None):
                if subfont_index is not None:
                    pdfmetrics.registerFont(TTFont(name, path, subfontIndex=subfont_index))
                else:
                    pdfmetrics.registerFont(TTFont(name, path))

            # 注册常规体
            chinese_regular_registered = False
            for p in candidates_regular:
                if os.path.exists(p):
                    if p.endswith('.ttc'):
                        # 大多数 .ttc 的 0 索引为常规体
                        register_one('ChineseFont', p, 0)
                    else:
                        register_one('ChineseFont', p)
                    chinese_regular_registered = True
                    break

            # 注册粗体（若找不到则回退到常规体）
            chinese_bold_registered = False
            for p in candidates_bold:
                if os.path.exists(p):
                    if p.endswith('.ttc'):
                        # 对于 msyhbd.ttc，常规在 0，粗体在 0 或 1，尝试 1，不行则 0
                        try:
                            register_one('ChineseFont-Bold', p, 1)
                        except Exception:
                            register_one('ChineseFont-Bold', p, 0)
                    else:
                        register_one('ChineseFont-Bold', p)
                    chinese_bold_registered = True
                    break

            # 若未注册粗体，则用常规体占位，避免粗体回退到 Helvetica 导致缺字
            if not chinese_bold_registered and chinese_regular_registered:
                # 使用相同文件名作为粗体占位
                pdfmetrics.registerFont(TTFont('ChineseFont-Bold', candidates_regular[0] if os.path.exists(candidates_regular[0]) else p))

            # 注册字体族，确保报告中加粗能正确选择 CJK 字体
            try:
                from reportlab.pdfbase.pdfmetrics import registerFontFamily
                registerFontFamily('ChineseFont', normal='ChineseFont', bold='ChineseFont-Bold', italic='ChineseFont', boldItalic='ChineseFont-Bold')
            except Exception:
                pass

            # 注册emoji字体
            emoji_candidates = [
                "C:/Windows/Fonts/seguiemj.ttf",  # Windows Segoe UI Emoji
                "/System/Library/Fonts/Apple Color Emoji.ttc",  # macOS
                "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",  # Linux
            ]
            for p in emoji_candidates:
                if os.path.exists(p):
                    pdfmetrics.registerFont(TTFont('EmojiFont', p))
                    break

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
        
        # 代码样式（也用中文字体，避免代码中包含中文时出现方块）
        styles.add(ParagraphStyle(
            name='ChineseCode',
            parent=styles['Code'],
            fontName='ChineseFont',
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
    
    def _convert_inline_markdown_to_markup(self, text: str) -> str:
        """将常见的行内Markdown语法转换为ReportLab可识别的标记。
        支持: 粗体(**或__), 斜体(*或_), 行内代码(`code`), 链接[text](url)
        """
        # 先处理行内代码，避免其中的星号被误判
        def repl_code(m):
            code = m.group(1)
            return f'<font name="Courier">{html.escape(code)}</font>'
        text = re.sub(r'`([^`]+)`', repl_code, text)

        # 粗体 (优先处理，避免与斜体冲突)
        text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
        text = re.sub(r'__(.+?)__', r'<b>\1</b>', text)

        # 斜体
        text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<i>\1</i>', text)
        text = re.sub(r'(?<!_)_(?!_)(.+?)(?<!_)_(?!_)', r'<i>\1</i>', text)

        # 链接 [text](url)
        def repl_link(m):
            label, url = m.group(1), m.group(2)
            return f'<a href="{html.escape(url)}" color="blue"><u>{html.escape(label)}</u></a>'
        text = re.sub(r'\[(.+?)\]\((.+?)\)', repl_link, text)

        return text

    def _escape_html_preserve_tags(self, text: str, allowed_tags=("font", "b", "i", "u", "a", "br")) -> str:
        """转义HTML但保留允许的简单标签。"""
        # 为每类标签建立占位符
        placeholders = []
        temp_text = text
        for tag in allowed_tags:
            pattern = re.compile(fr'<{tag}[^>]*?>|</{tag}>')
            for m in pattern.finditer(temp_text):
                token = f'__TAG_{len(placeholders)}__'
                placeholders.append((token, m.group(0)))
                temp_text = temp_text.replace(m.group(0), token)

        # 转义
        escaped = html.escape(temp_text)

        # 还原标签
        for token, original in placeholders:
            escaped = escaped.replace(token, original)
        return escaped
    
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
            
            # 处理引用
            elif line.startswith('> '):
                quote = line[2:].strip()
                quote = self._convert_inline_markdown_to_markup(quote)
                quote_with_emoji = self._process_emoji_text(quote)
                safe = self._escape_html_preserve_tags(quote_with_emoji)
                elements.append(Paragraph(safe, styles['ChineseQuote']))
            
            # 处理列表
            elif line.startswith('- '):
                item = line[2:].strip()
                item = self._convert_inline_markdown_to_markup(item)
                item_with_emoji = self._process_emoji_text(item)
                safe = self._escape_html_preserve_tags(item_with_emoji)
                elements.append(Paragraph(f"• {safe}", styles['ChineseNormal']))

            # 处理有序列表
            elif re.match(r'^\d+[\.)]\s+', line):
                m = re.match(r'^(\d+)[\.)]\s+(.*)$', line)
                num, content = m.group(1), m.group(2)
                content = self._convert_inline_markdown_to_markup(content)
                content_with_emoji = self._process_emoji_text(content)
                safe = self._escape_html_preserve_tags(content_with_emoji)
                elements.append(Paragraph(f"{num}. {safe}", styles['ChineseNormal']))
            
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
                
                # 解析表格并添加到元素
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
                    # 分行添加代码
                    for code_line in code_text.split('\n'):
                        elements.append(Paragraph(self._escape_html_preserve_emoji(code_line), styles['ChineseCode']))
            
            # 处理普通文本
            else:
                if line:
                    # 行内Markdown -> Markup，再处理emoji并转义（保留标签）
                    line = self._convert_inline_markdown_to_markup(line)
                    text_with_emoji = self._process_emoji_text(line)
                    escaped_text = self._escape_html_preserve_tags(text_with_emoji)
                    elements.append(Paragraph(escaped_text, styles['ChineseNormal']))
            
            i += 1
        
        return elements
    
    def _escape_html_preserve_emoji(self, text):
        """转义HTML字符但保留emoji"""
        # 先保护emoji标记
        emoji_pattern = r'<font name="EmojiFont">(.*?)</font>'
        emoji_matches = re.findall(emoji_pattern, text)
        
        # 临时替换emoji标记
        temp_text = text
        for i, emoji in enumerate(emoji_matches):
            temp_text = temp_text.replace(f'<font name="EmojiFont">{emoji}</font>', f'__EMOJI_{i}__')
        
        # 转义HTML
        escaped_text = html.escape(temp_text)
        
        # 恢复emoji标记
        for i, emoji in enumerate(emoji_matches):
            escaped_text = escaped_text.replace(f'__EMOJI_{i}__', f'<font name="EmojiFont">{emoji}</font>')
        
        return escaped_text
    
    def _add_table_to_elements(self, table_rows, elements, styles):
        """将表格添加到元素列表"""
        # 解析表格数据
        table_data = []
        for row in table_rows:
            # 移除首尾的|符号并分割
            cells = [cell.strip() for cell in row.strip('|').split('|')]
            table_data.append(cells)
        
        # 跳过分隔行（通常是第二行，包含---）
        if len(table_data) > 1 and all('---' in cell or '-' in cell for cell in table_data[1]):
            table_data.pop(1)
        
        if table_data and len(table_data) > 0:
            # 创建表格
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'ChineseFont'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('FONTNAME', (0, 1), (-1, -1), 'ChineseFont'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(table)
            elements.append(Spacer(1, 12))
    
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
            
            # 解析Markdown内容
            content_elements = self._parse_markdown_to_pdf_elements(markdown_content, styles)
            
            # 构建PDF
            doc.build(content_elements)
            
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