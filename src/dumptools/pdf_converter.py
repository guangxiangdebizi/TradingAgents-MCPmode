#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown to PDF Converter (Simple & Reliable)
将Markdown格式的报告转换为PDF文件，保持原有格式和样式
使用reportlab直接生成PDF，避免HTML解析问题
"""

import os
import sys
import argparse
import re
from pathlib import Path

try:
    import markdown2
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm
    from reportlab.lib import colors
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
    import html
except ImportError as e:
    print(f"❌ 缺少必要的依赖包: {e}")
    print("请运行: pip install markdown2 reportlab")
    sys.exit(1)

class MarkdownToPDFConverter:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._register_chinese_fonts()
        self._create_custom_styles()
        
    def _register_chinese_fonts(self):
        """注册中文字体"""
        try:
            # Windows系统字体路径
            font_paths = [
                (r"C:\Windows\Fonts\msyh.ttc", "YaHei"),  # 微软雅黑
                (r"C:\Windows\Fonts\simsun.ttc", "SimSun"),  # 宋体
                (r"C:\Windows\Fonts\simhei.ttf", "SimHei"),  # 黑体
            ]
            
            self.chinese_font = None
            for font_path, font_name in font_paths:
                if os.path.exists(font_path):
                    try:
                        pdfmetrics.registerFont(TTFont(font_name, font_path))
                        self.chinese_font = font_name
                        print(f"✅ 成功注册中文字体: {font_name}")
                        break
                    except Exception as e:
                        print(f"⚠️  字体注册失败 {font_name}: {e}")
                        continue
            
            if not self.chinese_font:
                print("⚠️  未找到中文字体，将使用默认字体")
                self.chinese_font = "Helvetica"
                
        except Exception as e:
            print(f"⚠️  字体注册过程出错: {e}")
            self.chinese_font = "Helvetica"
    
    def _create_custom_styles(self):
        """创建自定义样式"""
        # 标题样式
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=20,
            spaceAfter=16,
            spaceBefore=12,
            fontName=self.chinese_font,
            textColor=colors.HexColor('#2c3e50'),
            alignment=TA_LEFT
        )
        
        # 二级标题样式
        self.heading2_style = ParagraphStyle(
            'CustomHeading2',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            spaceBefore=10,
            fontName=self.chinese_font,
            textColor=colors.HexColor('#34495e'),
            alignment=TA_LEFT
        )
        
        # 三级标题样式
        self.heading3_style = ParagraphStyle(
            'CustomHeading3',
            parent=self.styles['Heading3'],
            fontSize=14,
            spaceAfter=10,
            spaceBefore=8,
            fontName=self.chinese_font,
            textColor=colors.HexColor('#2c3e50'),
            alignment=TA_LEFT
        )
        
        # 四级标题样式
        self.heading4_style = ParagraphStyle(
            'CustomHeading4',
            parent=self.styles['Heading4'],
            fontSize=12,
            spaceAfter=8,
            spaceBefore=6,
            fontName=self.chinese_font,
            textColor=colors.HexColor('#34495e'),
            alignment=TA_LEFT
        )
        
        # 正文样式
        self.normal_style = ParagraphStyle(
            'CustomNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            fontName=self.chinese_font,
            alignment=TA_JUSTIFY,
            leading=14
        )
        
        # 列表样式
        self.bullet_style = ParagraphStyle(
            'CustomBullet',
            parent=self.normal_style,
            leftIndent=20,
            bulletIndent=10,
            spaceAfter=3
        )
        
        # 代码样式
        self.code_style = ParagraphStyle(
            'CustomCode',
            parent=self.styles['Code'],
            fontSize=9,
            fontName='Courier',
            backColor=colors.HexColor('#f8f9fa'),
            borderColor=colors.HexColor('#e1e8ed'),
            borderWidth=1,
            leftIndent=10,
            rightIndent=10,
            spaceAfter=6,
            spaceBefore=6
        )
    
    def _clean_text(self, text):
        """清理文本，移除markdown标记和XML标签"""
        if not text:
            return ""
        
        # 移除XML标签（如<mcreference>、<mcfile>等）
        text = re.sub(r'<[^>]+>', '', text)
        
        # 移除markdown链接
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        
        # 移除markdown图片
        text = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', r'\1', text)
        
        # 移除markdown代码标记
        text = re.sub(r'`([^`]+)`', r'\1', text)
        
        # 移除markdown粗体和斜体标记
        text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', text)
        text = re.sub(r'\*([^\*]+)\*', r'\1', text)
        text = re.sub(r'__([^_]+)__', r'\1', text)
        text = re.sub(r'_([^_]+)_', r'\1', text)
        
        # 处理HTML实体
        text = html.unescape(text)
        
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _create_adaptive_table(self, table_data):
        """创建自适应表格，处理列宽和内容换行"""
        if not table_data or len(table_data) < 1:
            return None
        
        # 计算可用宽度（A4页面宽度减去边距）
        page_width = A4[0] - 144  # 72*2 for margins
        
        # 计算列数
        max_cols = max(len(row) for row in table_data)
        
        # 为每列分配宽度
        col_widths = [page_width / max_cols] * max_cols
        
        # 处理表格数据，将长文本转换为Paragraph对象以支持换行
        processed_data = []
        for row_idx, row in enumerate(table_data):
            processed_row = []
            for col_idx, cell in enumerate(row):
                if col_idx < len(col_widths):
                    # 清理单元格文本
                    clean_cell = self._clean_text(str(cell))
                    
                    # 如果是表头（第一行），使用不同的样式
                    if row_idx == 0:
                        cell_style = ParagraphStyle(
                            'TableHeader',
                            parent=self.normal_style,
                            fontSize=9,
                            fontName=self.chinese_font,
                            alignment=TA_CENTER,
                            textColor=colors.HexColor('#2c3e50'),
                            leading=12
                        )
                    else:
                        cell_style = ParagraphStyle(
                            'TableCell',
                            parent=self.normal_style,
                            fontSize=8,
                            fontName=self.chinese_font,
                            alignment=TA_LEFT,
                            leading=10
                        )
                    
                    # 创建Paragraph对象以支持自动换行
                    if clean_cell:
                        processed_row.append(Paragraph(clean_cell, cell_style))
                    else:
                        processed_row.append(Paragraph(' ', cell_style))
                else:
                    processed_row.append('')
            
            # 确保所有行都有相同的列数
            while len(processed_row) < max_cols:
                processed_row.append('')
            
            processed_data.append(processed_row)
        
        # 创建表格
        table = Table(processed_data, colWidths=col_widths, repeatRows=1)
        
        # 设置表格样式
        table_style = [
            # 表头样式
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8f9fa')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('FONTNAME', (0, 0), (-1, 0), self.chinese_font),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            
            # 表格内容样式
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), self.chinese_font),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            
            # 边框和间距
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#ddd')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]
        
        table.setStyle(TableStyle(table_style))
        
        return table
    
    def _parse_markdown_to_elements(self, md_content):
        """解析Markdown内容为PDF元素"""
        lines = md_content.split('\n')
        elements = []
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if not line:
                i += 1
                continue
            
            # 处理标题
            if line.startswith('#'):
                level = len(line) - len(line.lstrip('#'))
                title_text = self._clean_text(line.lstrip('#').strip())
                
                if level == 1:
                    elements.append(Paragraph(title_text, self.title_style))
                elif level == 2:
                    elements.append(Paragraph(title_text, self.heading2_style))
                elif level == 3:
                    elements.append(Paragraph(title_text, self.heading3_style))
                else:
                    elements.append(Paragraph(title_text, self.heading4_style))
                
                elements.append(Spacer(1, 6))
            
            # 处理列表
            elif line.startswith(('-', '*', '+')) or re.match(r'^\d+\.', line):
                # 收集连续的列表项
                list_items = []
                while i < len(lines) and lines[i].strip():
                    current_line = lines[i].strip()
                    if current_line.startswith(('-', '*', '+')) or re.match(r'^\d+\.', current_line):
                        # 移除列表标记
                        item_text = re.sub(r'^[-*+]\s*|^\d+\.\s*', '', current_line)
                        item_text = self._clean_text(item_text)
                        if item_text:
                            list_items.append(f"• {item_text}")
                    elif current_line.startswith('  ') and list_items:  # 续行
                        list_items[-1] += " " + current_line.strip()
                    else:
                        break
                    i += 1
                
                # 添加列表项
                for item in list_items:
                    elements.append(Paragraph(item, self.bullet_style))
                
                elements.append(Spacer(1, 6))
                continue
            
            # 处理代码块
            elif line.startswith('```'):
                code_lines = []
                i += 1
                while i < len(lines) and not lines[i].strip().startswith('```'):
                    code_lines.append(lines[i])
                    i += 1
                
                if code_lines:
                    code_text = '\n'.join(code_lines)
                    elements.append(Paragraph(code_text, self.code_style))
                    elements.append(Spacer(1, 6))
            
            # 处理表格
            elif '|' in line and line.count('|') >= 2:
                table_rows = []
                # 收集表格行
                while i < len(lines) and '|' in lines[i]:
                    current_line = lines[i].strip()
                    if current_line:
                        # 分割单元格，过滤空白单元格
                        row_data = [cell.strip() for cell in current_line.split('|')]
                        # 移除首尾的空元素（由于行首行尾的|导致的）
                        if row_data and not row_data[0]:
                            row_data.pop(0)
                        if row_data and not row_data[-1]:
                            row_data.pop()
                        
                        if row_data:
                            table_rows.append(row_data)
                    i += 1
                
                if table_rows and len(table_rows) >= 1:
                    # 跳过分隔行（通常是第二行，包含---等分隔符）
                    filtered_rows = []
                    for row in table_rows:
                        # 检查是否为分隔行
                        is_separator = all(
                            cell.replace('-', '').replace(':', '').replace(' ', '') == '' 
                            for cell in row
                        )
                        if not is_separator:
                            filtered_rows.append(row)
                    
                    if filtered_rows:
                        # 使用新的自适应表格方法
                        table = self._create_adaptive_table(filtered_rows)
                        if table:
                            # 使用KeepTogether防止表格跨页断裂
                            elements.append(KeepTogether([table]))
                            elements.append(Spacer(1, 12))
                continue
            
            # 处理分隔线
            elif line.startswith('---') or line.startswith('***'):
                elements.append(Spacer(1, 12))
                # 添加一条线
                from reportlab.platypus import HRFlowable
                elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#ecf0f1')))
                elements.append(Spacer(1, 12))
            
            # 处理普通段落
            else:
                # 收集连续的段落行
                para_lines = [line]
                i += 1
                while i < len(lines) and lines[i].strip() and not lines[i].startswith(('#', '-', '*', '+', '```', '|', '---', '***')):
                    para_lines.append(lines[i].strip())
                    i += 1
                
                para_text = ' '.join(para_lines)
                para_text = self._clean_text(para_text)
                
                if para_text:
                    elements.append(Paragraph(para_text, self.normal_style))
                    elements.append(Spacer(1, 6))
                continue
            
            i += 1
        
        return elements
    
    def convert_to_pdf(self, md_file_path, output_pdf_path=None):
        """将Markdown文件转换为PDF"""
        try:
            # 读取Markdown文件
            with open(md_file_path, 'r', encoding='utf-8') as f:
                md_content = f.read()
            
            # 设置输出路径
            if output_pdf_path is None:
                md_path = Path(md_file_path)
                output_pdf_path = md_path.parent / f"{md_path.stem}.pdf"
            
            # 创建PDF文档
            doc = SimpleDocTemplate(
                str(output_pdf_path),
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            # 解析Markdown并生成PDF元素
            elements = self._parse_markdown_to_elements(md_content)
            
            # 生成PDF
            doc.build(elements)
            
            print(f"✅ PDF转换成功！")
            print(f"📄 输入文件: {md_file_path}")
            print(f"📋 输出文件: {output_pdf_path}")
            print(f"🔧 转换方法: reportlab (直接生成)")
            print(f"📊 文件大小: {os.path.getsize(output_pdf_path) / 1024:.1f} KB")
            
            return str(output_pdf_path)
            
        except FileNotFoundError:
            print(f"❌ 错误：找不到文件 {md_file_path}")
            return None
        except Exception as e:
            print(f"❌ 转换失败：{str(e)}")
            import traceback
            traceback.print_exc()
            return None

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="将Markdown格式的报告转换为PDF文件",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python md_to_pdf_converter.py report.md
  python md_to_pdf_converter.py report.md -o output.pdf
  python md_to_pdf_converter.py progress_logs/session_20250729_161432_report.md
        """
    )
    
    parser.add_argument(
        'input_file',
        help='输入的Markdown文件路径'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='输出的PDF文件路径（可选，默认与输入文件同名）'
    )
    
    args = parser.parse_args()
    
    # 检查输入文件是否存在
    if not os.path.exists(args.input_file):
        print(f"❌ 错误：文件 '{args.input_file}' 不存在")
        sys.exit(1)
    
    # 检查文件扩展名
    if not args.input_file.lower().endswith('.md'):
        print(f"⚠️  警告：输入文件不是.md格式，将尝试按Markdown处理")
    
    # 创建转换器并执行转换
    converter = MarkdownToPDFConverter()
    result = converter.convert_to_pdf(args.input_file, args.output)
    
    if result:
        print(f"\n🎉 转换完成！PDF文件已保存到: {result}")
    else:
        print(f"\n💥 转换失败，请检查文件格式和内容")
        sys.exit(1)

if __name__ == "__main__":
    main()