#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSON to Markdown Converter
专门为dump文件夹下的JSON文档导出为Markdown的工具
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional


class JSONToMarkdownConverter:
    """JSON转Markdown转换器"""
    
    def __init__(self, dump_dir: str = "src/dump"):
        """初始化转换器
        
        Args:
            dump_dir: dump文件夹路径
        """
        self.dump_dir = Path(dump_dir)
        self.output_dir = Path("markdown_reports")
        
        # 确保输出目录存在
        self.output_dir.mkdir(exist_ok=True)
    
    def convert_json_to_markdown(self, json_file_path: str) -> Optional[str]:
        """将JSON文件转换为Markdown
        
        Args:
            json_file_path: JSON文件路径
            
        Returns:
            生成的Markdown文件路径，失败返回None
        """
        try:
            # 读取JSON文件
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 生成Markdown内容
            markdown_content = self._generate_markdown(data)
            
            # 生成输出文件名
            json_filename = Path(json_file_path).stem
            output_file = self.output_dir / f"{json_filename}.md"
            
            # 写入Markdown文件
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            print(f"✅ Markdown报告已生成: {output_file}")
            return str(output_file)
            
        except Exception as e:
            print(f"❌ 转换失败: {e}")
            return None
    
    def _generate_markdown(self, data: Dict[str, Any]) -> str:
        """生成Markdown内容"""
        md_lines = []
        
        # 标题
        session_id = data.get('session_id', 'Unknown')
        md_lines.append(f"# 交易分析报告 - {session_id}")
        md_lines.append("")
        
        # 基本信息
        md_lines.append("## 📋 基本信息")
        md_lines.append("")
        md_lines.append(f"- **会话ID**: {data.get('session_id', 'N/A')}")
        md_lines.append(f"- **创建时间**: {data.get('created_at', 'N/A')}")
        md_lines.append(f"- **更新时间**: {data.get('updated_at', 'N/A')}")
        md_lines.append(f"- **状态**: {data.get('status', 'N/A')}")
        md_lines.append("")
        
        # 用户查询
        if 'user_query' in data:
            md_lines.append("## 🔍 用户查询")
            md_lines.append("")
            md_lines.append(f"> {data['user_query']}")
            md_lines.append("")
        
        # 智能体执行情况 - 只导出已完成的智能体
        if 'agents' in data and data['agents']:
            # 过滤出status为completed的智能体
            completed_agents = [agent for agent in data['agents'] if agent.get('status') == 'completed']
            
            if completed_agents:
                md_lines.append("## 🤖 智能体执行情况（已完成）")
                md_lines.append("")
                
                for agent in completed_agents:
                    agent_name = agent.get('agent_name', 'Unknown Agent')
                    md_lines.append(f"### {agent_name}")
                    md_lines.append("")
                    
                    # 基本信息
                    md_lines.append(f"- **状态**: {agent.get('status', 'N/A')}")
                    md_lines.append(f"- **开始时间**: {agent.get('start_time', 'N/A')}")
                    if agent.get('end_time'):
                        md_lines.append(f"- **结束时间**: {agent.get('end_time')}")
                    md_lines.append(f"- **执行结果**: {agent.get('result', 'N/A')}")
                    md_lines.append("")
                    
                    # 执行内容
                    if agent.get('action'):
                        md_lines.append("**执行内容**:")
                        md_lines.append("")
                        md_lines.append("```")
                        md_lines.append(str(agent['action']))
                        md_lines.append("```")
                        md_lines.append("")
        
        # 阶段信息
        if 'stages' in data and data['stages']:
            md_lines.append("## 📊 执行阶段")
            md_lines.append("")
            for i, stage in enumerate(data['stages'], 1):
                md_lines.append(f"### 阶段 {i}")
                md_lines.append("")
                md_lines.append(f"**内容**: {stage}")
                md_lines.append("")
        
        # MCP调用情况
        if 'mcp_calls' in data and data['mcp_calls']:
            md_lines.append("## 🔧 MCP工具调用")
            md_lines.append("")
            for i, call in enumerate(data['mcp_calls'], 1):
                md_lines.append(f"### 调用 {i}")
                md_lines.append("")
                md_lines.append(f"**工具**: {call.get('tool', 'N/A')}")
                md_lines.append(f"**时间**: {call.get('timestamp', 'N/A')}")
                if call.get('result'):
                    md_lines.append(f"**结果**: {call['result']}")
                md_lines.append("")
        
        # 错误信息
        if 'errors' in data and data['errors']:
            md_lines.append("## ❌ 错误信息")
            md_lines.append("")
            for error in data['errors']:
                md_lines.append(f"- {error}")
            md_lines.append("")
        
        # 警告信息
        if 'warnings' in data and data['warnings']:
            md_lines.append("## ⚠️ 警告信息")
            md_lines.append("")
            for warning in data['warnings']:
                md_lines.append(f"- {warning}")
            md_lines.append("")
        
        # 生成时间戳
        md_lines.append("---")
        md_lines.append("")
        md_lines.append(f"*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        
        return "\n".join(md_lines)
    
    def convert_latest_json(self) -> Optional[str]:
        """转换最新的JSON文件
        
        Returns:
            生成的Markdown文件路径，失败返回None
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
            
            # 转换为Markdown
            return self.convert_json_to_markdown(str(latest_json))
            
        except Exception as e:
            print(f"❌ 转换过程中发生错误: {e}")
            return None
    
    def convert_all_json(self) -> List[str]:
        """转换所有JSON文件
        
        Returns:
            生成的Markdown文件路径列表
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
                result = self.convert_json_to_markdown(str(json_file))
                if result:
                    results.append(result)
            
            return results
            
        except Exception as e:
            print(f"❌ 批量转换过程中发生错误: {e}")
            return []
    
    def list_available_json_files(self) -> List[str]:
        """列出可用的JSON文件
        
        Returns:
            JSON文件路径列表
        """
        try:
            json_files = list(self.dump_dir.glob("session_*.json"))
            return [str(f) for f in sorted(json_files, key=lambda f: f.stat().st_mtime, reverse=True)]
        except Exception as e:
            print(f"❌ 列出文件时发生错误: {e}")
            return []


def main():
    """主函数 - 命令行工具"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="JSON to Markdown Converter - 将dump文件夹下的JSON文档转换为Markdown"
    )
    parser.add_argument("-f", "--file", help="指定要转换的JSON文件路径")
    parser.add_argument("-l", "--latest", action="store_true", help="转换最新的JSON文件")
    parser.add_argument("-a", "--all", action="store_true", help="转换所有JSON文件")
    parser.add_argument("--list", action="store_true", help="列出所有可用的JSON文件")
    parser.add_argument("-d", "--dump-dir", default="src/dump", help="dump文件夹路径")
    
    args = parser.parse_args()
    
    converter = JSONToMarkdownConverter(args.dump_dir)
    
    if args.list:
        # 列出所有可用文件
        files = converter.list_available_json_files()
        if files:
            print("📋 可用的JSON文件:")
            for i, file_path in enumerate(files, 1):
                file_name = Path(file_path).name
                file_time = datetime.fromtimestamp(Path(file_path).stat().st_mtime)
                print(f"  {i}. {file_name} ({file_time.strftime('%Y-%m-%d %H:%M:%S')})")
        else:
            print("❌ 未找到任何JSON文件")
    
    elif args.all:
        # 转换所有文件
        results = converter.convert_all_json()
        if results:
            print(f"🎉 批量转换完成，共生成 {len(results)} 个Markdown文件")
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
            result = converter.convert_json_to_markdown(args.file)
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
