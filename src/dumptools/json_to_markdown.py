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
import re


class JSONToMarkdownConverter:
    """JSON转Markdown转换器"""
    
    def __init__(self, dump_dir: str = "src/dump", include_mcp_calls: bool = False):
        """初始化转换器
        
        Args:
            dump_dir: dump文件夹路径
            include_mcp_calls: 是否在Markdown中包含MCP工具调用信息（默认关闭）
        """
        self.dump_dir = Path(dump_dir)
        self.output_dir = Path("markdown_reports")
        self.include_mcp_calls = include_mcp_calls
        
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
    
    def _normalize_result_headers(self, result_text: str) -> str:
        """标准化 result 中的标题格式：
        - 智能识别 AI 文本中的标题层级，使其最高级别调整为二级标题（##）
        - 同时保留相对层级关系（整体平移），最大不超过六级
        例如：若文本内最顶层为 `#`，则整体 +1；若最顶层为 `###`，则整体 -1，使其顶层变为 `##`
        """
        if not result_text:
            return result_text
        
        lines = result_text.split('\n')
        normalized_lines = []

        # 收集所有标题级别（1-6级）
        heading_levels = []
        heading_matches = []
        for line in lines:
            m = re.match(r'^(#{1,6})\s*(.+?)\s*$', line)
            heading_matches.append(m)
            if m:
                level = len(m.group(1))
                heading_levels.append(level)
        
        if not heading_levels:
            return result_text
        
        min_level = min(heading_levels)
        offset = 2 - min_level  # 让最高级别调整为二级标题
        
        for idx, line in enumerate(lines):
            m = heading_matches[idx]
            if m:
                old_level = len(m.group(1))
                text = m.group(2).strip()
                new_level = old_level + offset
                if new_level < 2:
                    new_level = 2
                if new_level > 6:
                    new_level = 6
                normalized_lines.append(f"{'#' * new_level} {text}")
            else:
                normalized_lines.append(line)
        
        return '\n'.join(normalized_lines)

    def _remove_emojis(self, text: str) -> str:
        """移除文本中的所有 emoji/变体/不可见空白 等符号。"""
        emoji_pattern = re.compile(
            r"[\u2300-\u23FF\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002600-\U000027BF\U0001F900-\U0001F9FF\U0001F018-\U0001F270]",
            re.UNICODE,
        )
        cleaned = emoji_pattern.sub('', text)
        # 去除变体选择符与零宽/不可断空格等
        cleaned = re.sub(r"[\uFE0E\uFE0F\u200B\u200C\u200D\u2060\ufeff\u00A0\u202F]", '', cleaned)
        return cleaned

    def _strip_heading_prefix(self, title: str) -> str:
        """去除标题中已有的编号/序号/中文序号及收尾标点，并清理前导杂项字符。
        处理场景：
        - 15.2  二、 标题
        - 一、 标题 / 十一、 标题
        - 1) 标题 / 1.2.3. 标题
        - 前导存在不可见字符或变体选择符（如 \uFE0F）
        """
        t = title.strip()
        # 去掉不可见/变体字符
        t = re.sub(r'[\u200b\u200c\u200d\u2060\ufeff\uFE0E\uFE0F]', '', t)
        # 循环清理，直到无法再匹配（支持“图标 + 中文序号 + 顿号/逗号 + 空格”的组合）
        while True:
            before = t
            # 先强制去前置所有 emoji/符号（包含闹钟/铃铛等 U+23xx）
            t = self._remove_emojis(t)
            # 数字分级：1. / 1.2 / 1.2.3. / 1）/ 1) / 15.3 ️ 二、
            t = re.sub(r'^[\s\t]*\d+(?:\s*[\.．]\s*\d+)*\s*[\.)、．]?[\s\uFE0E\uFE0F\u200B\u200C\u200D\u2060\ufeff\u00A0\u202F]*', '', t)
            # 中文序号：一、 二、 十一、 等
            t = re.sub(r'^[\s\t]*[一二三四五六七八九十百千万零〇]+[、\.．)]\s*', '', t)
            # 其他常见前导标点/符号
            t = re.sub(r'^[\s\t]*[\-•*·]+\s*', '', t)
            t = re.sub(r'^[\s\t]*[,:：、，\.．\)\(（）]+\s*', '', t)
            if t == before:
                break
        # 兜底：删除起始处由“数字/中文数字/分隔符/不可见字符”组成的连续前缀
        t = re.sub(r'^[\s\uFE0E\uFE0F\u200B\u200C\u200D\u2060\ufeff\u00A0\u202F0-9一二三四五六七八九十百千万零〇\-•*·,:：、，\.．\)\(（）]+', '', t)
        return t.strip()

    def _number_all_headings(self, markdown_text: str) -> str:
        """为所有 Markdown 标题添加分级编号：
        # 1.
        ## 1.1
        ### 1.1.1
        #### 1.1.1.1
        编号按出现顺序自动递增；非标题行不处理。
        """
        lines = markdown_text.split('\n')
        counters = [0, 0, 0, 0, 0, 0]  # 对应1~6级
        result_lines: List[str] = []
        for line in lines:
            m = re.match(r'^(#{1,6})\s*(.+?)\s*$', line)
            if not m:
                result_lines.append(line)
                continue
            level = len(m.group(1))
            text = m.group(2)
            # 去除emoji与原有编号（循环直到稳定，处理隐藏字符导致的一次不匹配）
            prev = None
            while prev != text:
                prev = text
                text = self._remove_emojis(text)
                text = self._strip_heading_prefix(text)
            # 规范多余空白：将连续空白压缩为单个空格，同时去首尾空白
            text = re.sub(r'\s+', ' ', text).strip()
            # 去除标题中的 Markdown 强调标记（粗体/斜体）
            text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
            text = re.sub(r'__(.+?)__', r'\1', text)
            text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'\1', text)
            text = re.sub(r'(?<!_)_(?!_)(.+?)(?<!_)_(?!_)', r'\1', text)
            # 兜底：清理残留的 * / _ / `（例如不成对的 ** 或单个 *）
            text = re.sub(r'[\*`_]+', '', text)
            # 维护计数器
            idx = level - 1
            counters[idx] += 1
            for j in range(idx + 1, 6):
                counters[j] = 0
            # 生成编号前缀
            nums = [str(counters[i]) for i in range(level) if counters[i] > 0]
            number_prefix = '.'.join(nums)
            # 确保编号与标题文本之间恰好一个空格
            new_title = f"{number_prefix} {text}"
            result_lines.append(f"{'#' * level} {new_title}")
        return '\n'.join(result_lines)

    def _extract_single_h1_title(self, text: str):
        """如果文本中恰好有一个一级标题，返回(标题文本, 去除该标题后的正文)。否则返回(None, 原文)。"""
        lines = text.split('\n')
        h1_indices = [i for i, line in enumerate(lines) if re.match(r'^#\s+.+', line.strip())]
        if len(h1_indices) != 1:
            return None, text
        idx = h1_indices[0]
        title_line = lines[idx]
        m = re.match(r'^#\s+(.+)$', title_line.strip())
        title_text = m.group(1).strip() if m else title_line.lstrip('#').strip()
        # 清理emoji和旧编号
        title_text = self._strip_heading_prefix(self._remove_emojis(title_text))
        # 去掉该行
        remaining = lines[:idx] + lines[idx+1:]
        return title_text, '\n'.join(remaining)

    def _promote_headings(self, text: str, levels: int = 1) -> str:
        """将所有Markdown标题整体上提（级别数字减小），最小不低于1。"""
        def repl(match):
            hashes = match.group(1)
            heading_text = match.group(2)
            old = len(hashes)
            new = max(1, old - levels)
            return f"{'#' * new} {heading_text.strip()}"
        return re.sub(r'^(#{1,6})\s*(.+)$', repl, text, flags=re.MULTILINE)
    
    def _get_agent_mcp_calls(self, agent_name: str, mcp_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """获取指定agent的MCP调用记录"""
        return [call for call in mcp_calls if call.get('agent_name') == agent_name]
    
    def _generate_mcp_calls_section(self, agent_name: str, mcp_calls: List[Dict[str, Any]]) -> str:
        """生成指定agent的MCP调用信息"""
        lines = []
        if mcp_calls:
            lines.append(f"#### 🔧 MCP工具调用 (共{len(mcp_calls)}次)")
            lines.append("")
            for i, call in enumerate(mcp_calls, 1):
                lines.append(f"**调用 {i}**:")
                tool_name = call.get('tool_name', 'N/A')
                timestamp = call.get('timestamp', 'N/A')
                lines.append(f"- 工具: {tool_name}")
                lines.append(f"- 时间: {timestamp}")
                if call.get('tool_result'):
                    lines.append(f"- 结果: {call['tool_result'][:100]}..." if len(call.get('tool_result', '')) > 100 else f"- 结果: {call.get('tool_result', '')}")
                lines.append("")
            lines.append("---")
            lines.append("")
        return '\n'.join(lines)
    
    def _generate_markdown(self, data: Dict[str, Any]) -> str:
        """生成Markdown内容"""
        md_lines = []
        
        # ===== 封面页 =====
        user_query = data.get('user_query', '')
        cover_title = user_query if user_query else f"交易分析报告 - {data.get('session_id', 'Unknown')}"
        # 封面不使用标题级别，改为加粗强调
        md_lines.append(f"**{cover_title}**")
        md_lines.append("")
        md_lines.append(f"**研究问题：** {user_query if user_query else 'N/A'}")
        md_lines.append("")
        md_lines.append("由国金证券人工智能实验室的 Agent 自动生成")
        md_lines.append("")
        md_lines.append(f"**提交日期：** {datetime.now().strftime('%Y 年 %m 月 %d 日')}")
        md_lines.append("")
        md_lines.append("---")
        md_lines.append("")
        
        # 智能体分析结果 - 只导出已完成的智能体的结果
        if 'agents' in data and data['agents']:
            # 过滤出status为completed的智能体
            completed_agents = [agent for agent in data['agents'] if agent.get('status') == 'completed']
            
            if completed_agents:
                # 获取MCP调用数据（可开关，默认不包含）
                mcp_calls = data.get('mcp_calls', []) if self.include_mcp_calls else []
                
                for agent in completed_agents:
                    agent_name = agent.get('agent_name', 'Unknown Agent')
                    
                    # 根据智能体类型设置更好的标题
                    title_mapping = {
                        'company_overview_analyst': '公司概述分析',
                        'market_analyst': '市场技术分析',
                        'sentiment_analyst': '市场情绪分析', 
                        'news_analyst': '新闻信息分析',
                        'fundamentals_analyst': '基本面分析',
                        'shareholder_analyst': '股东结构分析',
                        'bull_researcher': '看涨观点',
                        'bear_researcher': '看跌观点',
                        # 新增：英文角色到中文映射（领导可读）
                        'product_analyst': '产品分析',
                        'research_manager': '研究经理',
                        'trader': '交易执行',
                        'aggressive_risk_analyst': '进取型风险分析',
                        'safe_risk_analyst': '稳健型风险分析',
                        'risk_manager': '风险管理'
                    }
                    
                    section_title = title_mapping.get(agent_name, agent_name)
                    clean_section_title = self._strip_heading_prefix(self._remove_emojis(section_title))

                    # 特例：如果AI内容中恰好存在一个一级标题，则用它替换Agent的大标题
                    agent_result_text = agent.get('result') or ''
                    extracted_title, rest_text = self._extract_single_h1_title(agent_result_text)
                    if extracted_title:
                        md_lines.append(f"# {extracted_title}")
                        md_lines.append("")
                        # 不再上提升余内容的标题，保持其最高级别为二级（后续统一规范）
                        content_to_use = rest_text
                    else:
                        md_lines.append(f"# {clean_section_title} 分析结果")
                        md_lines.append("")
                        content_to_use = agent_result_text
                    
                    # 显示该agent的MCP调用信息（根据开关决定是否展示）
                    if self.include_mcp_calls:
                        agent_mcp_calls = self._get_agent_mcp_calls(agent_name, mcp_calls)
                        if agent_mcp_calls:
                            mcp_section = self._generate_mcp_calls_section(agent_name, agent_mcp_calls)
                            md_lines.append(mcp_section)
                    
                    # 处理并导出分析结果
                    if content_to_use:
                        # 无论是否替换标题，统一将最高级标题规范为二级
                        normalized_result = self._normalize_result_headers(content_to_use)
                        md_lines.append(normalized_result)
                        md_lines.append("")
                        md_lines.append("---")
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

        # 合并、统一编号并移除所有emoji
        raw_markdown = "\n".join(md_lines)
        numbered_markdown = self._number_all_headings(raw_markdown)
        final_markdown = self._remove_emojis(numbered_markdown)
        return final_markdown
    
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
    parser.add_argument("--include-mcp", action="store_true", help="在Markdown中包含MCP工具调用信息（默认不包含）")
    
    args = parser.parse_args()
    
    converter = JSONToMarkdownConverter(args.dump_dir, include_mcp_calls=args.include_mcp)
    
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
