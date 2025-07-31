#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSON to PDF Converter
直接从JSON数据生成PDF报告，支持中文字符
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

# 检查ReportLab可用性
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import platform
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("❌ PDF导出依赖未安装，请安装: pip install reportlab")


class JSONToPDFConverter:
    """JSON转PDF转换器（直接转换，支持中文字符）"""
    
    def __init__(self, dump_dir: str = "src/dump"):
        """初始化转换器
        
        Args:
            dump_dir: dump文件夹路径
        """
        if not REPORTLAB_AVAILABLE:
            raise ImportError("PDF导出依赖未安装，请安装: pip install reportlab")
            
        self.dump_dir = Path(dump_dir)
        self.output_dir = Path("pdf_reports")
        
        # 确保输出目录存在
        self.output_dir.mkdir(exist_ok=True)
        
        # 注册中文字体
        self._register_chinese_fonts()
    
    def _register_chinese_fonts(self):
        """注册中文字体"""
        try:
            # 根据操作系统选择合适的中文字体
            system = platform.system()
            
            if system == "Windows":
                # Windows系统字体路径
                font_paths = [
                    "C:/Windows/Fonts/msyh.ttc",  # 微软雅黑
                    "C:/Windows/Fonts/simsun.ttc",  # 宋体
                    "C:/Windows/Fonts/simhei.ttf",  # 黑体
                ]
            elif system == "Darwin":  # macOS
                font_paths = [
                    "/System/Library/Fonts/PingFang.ttc",
                    "/System/Library/Fonts/STHeiti Light.ttc",
                ]
            else:  # Linux
                font_paths = [
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                ]
            
            # 尝试注册第一个可用的字体
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                        self.chinese_font = 'ChineseFont'
                        print(f"✅ 成功注册中文字体: {font_path}")
                        return
                    except Exception as e:
                        print(f"⚠️ 注册字体失败 {font_path}: {e}")
                        continue
            
            # 如果没有找到中文字体，使用默认字体
            print("⚠️ 未找到中文字体，将使用默认字体")
            self.chinese_font = 'Helvetica'
            
        except Exception as e:
            print(f"⚠️ 字体注册过程出错: {e}")
            self.chinese_font = 'Helvetica'
        
    def _get_styles(self):
        """获取PDF样式"""
        styles = getSampleStyleSheet()
        
        # 标题样式
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=20,
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName=self.chinese_font,
            textColor=colors.HexColor('#2c3e50')
        )
        
        # 一级标题样式
        heading1_style = ParagraphStyle(
            'CustomHeading1',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=12,
            spaceBefore=12,
            fontName=self.chinese_font,
            textColor=colors.HexColor('#34495e')
        )
        
        # 二级标题样式
        heading2_style = ParagraphStyle(
            'CustomHeading2',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=10,
            spaceBefore=10,
            fontName=self.chinese_font,
            textColor=colors.HexColor('#34495e')
        )
        
        # 正文样式
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            alignment=TA_JUSTIFY,
            fontName=self.chinese_font,
            leading=14
        )
        
        # 列表样式
        bullet_style = ParagraphStyle(
            'CustomBullet',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=4,
            leftIndent=20,
            fontName=self.chinese_font
        )
        
        # 引用样式
        quote_style = ParagraphStyle(
            'CustomQuote',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            leftIndent=20,
            rightIndent=20,
            fontName=self.chinese_font,
            textColor=colors.HexColor('#666666'),
            borderColor=colors.HexColor('#3498db'),
            borderWidth=2,
            borderPadding=10
        )
        
        # 代码样式
        code_style = ParagraphStyle(
            'CustomCode',
            parent=styles['Normal'],
            fontSize=9,
            spaceAfter=6,
            leftIndent=20,
            fontName='Courier',
            backColor=colors.HexColor('#f8f9fa')
        )
        
        return {
            'title': title_style,
            'heading1': heading1_style,
            'heading2': heading2_style,
            'normal': normal_style,
            'bullet': bullet_style,
            'quote': quote_style,
            'code': code_style
        }
    
    def _clean_text(self, text: str) -> str:
        """清理文本，处理特殊字符"""
        if not text:
            return ""
        
        # 转换为字符串并清理
        text = str(text)
        
        # 处理emoji和特殊字符，替换为文本描述
        emoji_map = {
            '📄': '[文件]',
            '📈': '[图表]',
            '📉': '[图表]',
            '✅': '[成功]',
            '❌': '[错误]',
            '⚠️': '[警告]',
            '🎯': '[目标]',
            '🔍': '[搜索]',
            '🤖': '[机器人]',
            '📦': '[包]',
            '📊': '[统计]',
            '📋': '[列表]',
            '🔧': '[工具]'
        }
        
        for emoji, replacement in emoji_map.items():
            text = text.replace(emoji, replacement)
        
        return text.strip()
    
    def _generate_pdf_content(self, data: Dict[str, Any], story: list, styles: dict):
        """生成PDF内容"""
        # 标题
        session_id = data.get('session_id', 'Unknown')
        title_text = self._clean_text(f"交易分析报告 - {session_id}")
        story.append(Paragraph(title_text, styles['title']))
        story.append(Spacer(1, 20))
        
        # 基本信息
        heading_text = self._clean_text("[列表] 基本信息")
        story.append(Paragraph(heading_text, styles['heading1']))
        
        basic_info = [
            f"会话ID: {data.get('session_id', 'N/A')}",
            f"创建时间: {data.get('created_at', 'N/A')}",
            f"更新时间: {data.get('updated_at', 'N/A')}",
            f"状态: {data.get('status', 'N/A')}"
        ]
        
        for info in basic_info:
            clean_info = self._clean_text(f"• {info}")
            story.append(Paragraph(clean_info, styles['bullet']))
        
        story.append(Spacer(1, 15))
        
        # 用户查询
        if 'user_query' in data and data['user_query']:
            heading_text = self._clean_text("[搜索] 用户查询")
            story.append(Paragraph(heading_text, styles['heading1']))
            
            query_text = self._clean_text(data['user_query'])
            story.append(Paragraph(query_text, styles['quote']))
            story.append(Spacer(1, 15))
        
        # 智能体执行情况
        if 'agents' in data and data['agents']:
            heading_text = self._clean_text("[机器人] 智能体执行情况")
            story.append(Paragraph(heading_text, styles['heading1']))
            
            for agent in data['agents']:
                agent_name = agent.get('agent_name', 'Unknown Agent')
                agent_heading = self._clean_text(agent_name)
                story.append(Paragraph(agent_heading, styles['heading2']))
                
                # 智能体信息
                agent_info = [
                    f"状态: {agent.get('status', 'N/A')}",
                    f"开始时间: {agent.get('start_time', 'N/A')}",
                ]
                
                if agent.get('end_time'):
                    agent_info.append(f"结束时间: {agent.get('end_time')}")
                
                agent_info.append(f"执行结果: {agent.get('result', 'N/A')}")
                
                for info in agent_info:
                    clean_info = self._clean_text(f"• {info}")
                    story.append(Paragraph(clean_info, styles['bullet']))
                
                # 执行内容
                if agent.get('action'):
                    story.append(Paragraph("执行内容:", styles['normal']))
                    action_text = self._clean_text(str(agent['action']))
                    if len(action_text) > 1000:
                        action_text = action_text[:1000] + "..."
                    story.append(Paragraph(action_text, styles['code']))
                
                story.append(Spacer(1, 10))
        
        # 阶段信息
        if 'stages' in data and data['stages']:
            heading_text = self._clean_text("[统计] 执行阶段")
            story.append(Paragraph(heading_text, styles['heading1']))
            
            for i, stage in enumerate(data['stages'], 1):
                stage_heading = self._clean_text(f"阶段 {i}")
                story.append(Paragraph(stage_heading, styles['heading2']))
                
                stage_content = self._clean_text(f"内容: {stage}")
                story.append(Paragraph(stage_content, styles['normal']))
                story.append(Spacer(1, 8))
        
        # MCP调用情况
        if 'mcp_calls' in data and data['mcp_calls']:
            heading_text = self._clean_text("[工具] MCP工具调用")
            story.append(Paragraph(heading_text, styles['heading1']))
            
            for i, call in enumerate(data['mcp_calls'], 1):
                call_heading = self._clean_text(f"调用 {i}")
                story.append(Paragraph(call_heading, styles['heading2']))
                
                call_info = [
                    f"工具: {call.get('tool', 'N/A')}",
                    f"时间: {call.get('timestamp', 'N/A')}"
                ]
                if call.get('result'):
                    call_info.append(f"结果: {call['result']}")
                
                for info in call_info:
                    clean_info = self._clean_text(f"• {info}")
                    story.append(Paragraph(clean_info, styles['bullet']))
                
                story.append(Spacer(1, 8))
        
        # 错误信息
        if 'errors' in data and data['errors']:
            heading_text = self._clean_text("[错误] 错误信息")
            story.append(Paragraph(heading_text, styles['heading1']))
            
            for error in data['errors']:
                error_text = self._clean_text(f"• {error}")
                story.append(Paragraph(error_text, styles['bullet']))
            
            story.append(Spacer(1, 15))
        
        # 警告信息
        if 'warnings' in data and data['warnings']:
            heading_text = self._clean_text("[警告] 警告信息")
            story.append(Paragraph(heading_text, styles['heading1']))
            
            for warning in data['warnings']:
                warning_text = self._clean_text(f"• {warning}")
                story.append(Paragraph(warning_text, styles['bullet']))
            
            story.append(Spacer(1, 15))
        
        # 最终结果
        if 'final_results' in data and data['final_results']:
            heading_text = self._clean_text("[目标] 最终结果")
            story.append(Paragraph(heading_text, styles['heading1']))
            
            for key, value in data['final_results'].items():
                result_heading = self._clean_text(key)
                story.append(Paragraph(result_heading, styles['heading2']))
                
                result_text = self._clean_text(str(value))
                if len(result_text) > 1000:
                    result_text = result_text[:1000] + "..."
                
                story.append(Paragraph(result_text, styles['code']))
                story.append(Spacer(1, 10))
        
        # 分隔线和生成时间戳
        story.append(Spacer(1, 20))
        separator_text = "─" * 50
        story.append(Paragraph(separator_text, styles['normal']))
        
        timestamp_text = f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        story.append(Paragraph(timestamp_text, styles['normal']))
    

    
    def convert_json_to_pdf(self, json_file_path: str) -> Optional[str]:
        """将JSON文件转换为PDF
        
        Args:
            json_file_path: JSON文件路径
            
        Returns:
            生成的PDF文件路径，失败返回None
        """
        try:
            # 读取JSON文件
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 生成输出文件名
            json_filename = Path(json_file_path).stem
            output_file = self.output_dir / f"{json_filename}.pdf"
            
            # 创建PDF文档
            doc = SimpleDocTemplate(str(output_file), pagesize=A4, 
                                  leftMargin=inch, rightMargin=inch,
                                  topMargin=inch, bottomMargin=inch)
            story = []
            
            # 获取样式
            styles = self._get_styles()
            
            # 生成PDF内容
            self._generate_pdf_content(data, story, styles)
            
            # 生成PDF
            doc.build(story)
            
            print(f"✅ PDF报告已生成: {output_file}")
            return str(output_file)
            
        except Exception as e:
            print(f"❌ PDF转换失败: {e}")
            import traceback
            traceback.print_exc()
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
