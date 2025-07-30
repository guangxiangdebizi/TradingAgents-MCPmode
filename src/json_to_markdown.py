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
        
        # 阶段信息
        if 'phases' in data and data['phases']:
            md_lines.append("## 📊 分析阶段")
            md_lines.append("")
            for phase_name, phase_data in data['phases'].items():
                md_lines.append(f"### {phase_name}")
                md_lines.append("")
                md_lines.append(f"- **开始时间**: {phase_data.get('start_time', 'N/A')}")
                if phase_data.get('end_time'):
                    md_lines.append(f"- **结束时间**: {phase_data.get('end_time')}")
                md_lines.append(f"- **状态**: {phase_data.get('status', 'N/A')}")
                md_lines.append("")
        
        # 智能体信息
        if 'agents' in data and data['agents']:
            md_lines.append("## 🤖 智能体执行情况")
            md_lines.append("")
            
            for agent_name, agent_data in data['agents'].items():
                md_lines.append(f"### {agent_name}")
                md_lines.append("")
                
                # 基本信息
                md_lines.append(f"- **状态**: {agent_data.get('status', 'N/A')}")
                md_lines.append(f"- **开始时间**: {agent_data.get('start_time', 'N/A')}")
                if agent_data.get('end_time'):
                    md_lines.append(f"- **结束时间**: {agent_data.get('end_time')}")
                md_lines.append("")
                
                # 执行结果
                if agent_data.get('result'):
                    md_lines.append("**执行结果:**")
                    md_lines.append("")
                    md_lines.append("```")
                    md_lines.append(str(agent_data['result']))
                    md_lines.append("```")
                    md_lines.append("")
                
                # 行动记录
                if agent_data.get('actions'):
                    md_lines.append("**行动记录:**")
                    md_lines.append("")
                    for i, action in enumerate(agent_data['actions'], 1):
                        md_lines.append(f"{i}. **{action.get('action', 'Unknown')}**")
                        if action.get('timestamp'):
                            md_lines.append(f"   - 时间: {action['timestamp']}")
                        if action.get('details'):
                            md_lines.append(f"   - 详情: {action['details']}")
                        if action.get('result'):
                            md_lines.append(f"   - 结果: {action['result']}")
                        md_lines.append("")
                
                # MCP工具调用
                if agent_data.get('mcp_calls'):
                    md_lines.append("**MCP工具调用:**")
                    md_lines.append("")
                    for i, call in enumerate(agent_data['mcp_calls'], 1):
                        md_lines.append(f"{i}. **{call.get('tool', 'Unknown')}**")
                        if call.get('timestamp'):
                            md_lines.append(f"   - 时间: {call['timestamp']}")
                        if call.get('params'):
                            md_lines.append(f"   - 参数: `{call['params']}`")
                        if call.get('result'):
                            md_lines.append(f"   - 结果: {call['result']}")
                        md_lines.append("")
        
        # 错误和警告
        if data.get('errors') or data.get('warnings'):
            md_lines.append("## ⚠️ 错误和警告")
            md_lines.append("")
            
            if data.get('errors'):
                md_lines.append("### 错误")
                md_lines.append("")
                for error in data['errors']:
                    md_lines.append(f"- **{error.get('timestamp', 'N/A')}**: {error.get('message', 'N/A')}")
                md_lines.append("")
            
            if data.get('warnings'):
                md_lines.append("### 警告")
                md_lines.append("")
                for warning in data['warnings']:
                    md_lines.append(f"- **{warning.get('timestamp', 'N/A')}**: {warning.get('message', 'N/A')}")
                md_lines.append("")
        
        # 最终结果
        if 'final_results' in data and data['final_results']:
            md_lines.append("## 🎯 最终结果")
            md_lines.append("")
            
            results = data['final_results']
            if isinstance(results, dict):
                for key, value in results.items():
                    md_lines.append(f"- **{key}**: {value}")
            else:
                md_lines.append(f"```\n{results}\n```")
            md_lines.append("")
        
        # 辩论记录
        if 'debate_records' in data and data['debate_records']:
            md_lines.append("## 💬 辩论记录")
            md_lines.append("")
            
            for i, record in enumerate(data['debate_records'], 1):
                md_lines.append(f"### 辩论轮次 {i}")
                md_lines.append("")
                if record.get('timestamp'):
                    md_lines.append(f"**时间**: {record['timestamp']}")
                    md_lines.append("")
                if record.get('content'):
                    md_lines.append("**内容**:")
                    md_lines.append("")
                    md_lines.append(f"> {record['content']}")
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