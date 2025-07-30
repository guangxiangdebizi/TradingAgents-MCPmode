#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSON分析报告转Markdown文档转换器
将JSON格式的交易分析报告转换为Markdown文档
"""

import json
import sys
from pathlib import Path
from datetime import datetime

def get_agent_display_info(agent_type):
    """获取智能体的显示信息"""
    agent_info = {
        'market_analyst': {
            'name': '市场技术分析师',
            'icon': '📊'
        },
        'sentiment_analyst': {
            'name': '市场情绪分析师', 
            'icon': '📈'
        },
        'news_analyst': {
            'name': '新闻分析师',
            'icon': '📰'
        },
        'fundamental_analyst': {
            'name': '基本面分析师',
            'icon': '📋'
        },
        'technical_analyst': {
            'name': '技术分析师', 
            'icon': '📉'
        },
        'market_researcher': {
            'name': '市场研究员',
            'icon': '🔍'
        },
        'news_researcher': {
            'name': '新闻研究员',
            'icon': '📰'
        },
        'portfolio_manager': {
            'name': '投资组合经理',
            'icon': '💼'
        },
        'risk_management_manager': {
            'name': '风险管理经理',
            'icon': '🛡️'
        },
        'neutral_risk_analyst': {
            'name': '中性风险分析师',
            'icon': '⚖️'
        },
        'senior_trader': {
            'name': '高级交易员',
            'icon': '💰'
        }
    }
    return agent_info.get(agent_type, {
        'name': agent_type.replace('_', ' ').title(),
        'icon': '🤖'
    })

def extract_content_from_result(result_data):
    """从结果数据中提取实际内容"""
    if isinstance(result_data, dict):
        if 'content' in result_data:
            content = result_data['content']
            # 如果content是字符串形式的字典，尝试解析
            if isinstance(content, str) and content.startswith("{"):
                try:
                    parsed_content = eval(content)  # 注意：这里使用eval，实际应用中应该更安全
                    if isinstance(parsed_content, dict) and 'result' in parsed_content:
                        return parsed_content['result']
                except:
                    pass
            return content
        elif 'result' in result_data:
            return result_data['result']
    elif isinstance(result_data, str):
        return result_data
    return str(result_data)

def format_content(content):
    """格式化内容，处理特殊字符和格式"""
    if not content:
        return ""
    
    # 移除多余的空行
    lines = content.split('\n')
    formatted_lines = []
    prev_empty = False
    
    for line in lines:
        line = line.strip()
        if not line:
            if not prev_empty:
                formatted_lines.append('')
            prev_empty = True
        else:
            formatted_lines.append(line)
            prev_empty = False
    
    return '\n'.join(formatted_lines)

def create_markdown_report(json_file_path):
    """创建Markdown格式的分析报告"""
    try:
        # 读取JSON文件
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 开始构建Markdown内容
        markdown_content = []
        
        # 添加标题
        markdown_content.append("# 📈 智能交易分析报告\n")
        
        # 添加基本信息
        if 'user_query' in data:
            markdown_content.append(f"**分析目标**: {data['user_query']}\n")
        
        if 'created_at' in data:
            markdown_content.append(f"**生成时间**: {data['created_at']}\n")
        
        if 'status' in data:
            markdown_content.append(f"**分析状态**: {data['status']}\n")
        
        markdown_content.append("---\n")
        
        # 处理智能体分析结果
        if 'agents_data' in data:
            markdown_content.append("## 🤖 智能体分析详情\n")
            
            for agent_type, agent_data in data['agents_data'].items():
                if not agent_data:
                    continue
                
                agent_info = get_agent_display_info(agent_type)
                
                # 智能体标题
                markdown_content.append(f"### {agent_info['icon']} {agent_info['name']}\n")
                
                # 处理结果数据
                if 'results' in agent_data and agent_data['results']:
                    for result in agent_data['results']:
                        content = extract_content_from_result(result)
                        if content:
                            formatted_content = format_content(content)
                            markdown_content.append(formatted_content + "\n")
                
                # 添加状态信息
                if 'status' in agent_data:
                    markdown_content.append(f"**状态**: {agent_data['status']}\n")
                
                if 'start_time' in agent_data and 'end_time' in agent_data:
                    markdown_content.append(f"**执行时间**: {agent_data['start_time']} - {agent_data['end_time']}\n")
                
                markdown_content.append("---\n")
        
        # 添加最终建议（如果有）
        if 'final_recommendation' in data and data['final_recommendation']:
            markdown_content.append("## 💡 最终投资建议\n")
            markdown_content.append(format_content(data['final_recommendation']) + "\n")
            markdown_content.append("---\n")
        
        # 添加风险提示
        markdown_content.append("## ⚠️ 风险提示\n")
        risk_text = (
            "本报告仅供参考，不构成投资建议。投资有风险，入市需谨慎。\n"
            "请根据自身风险承受能力和投资目标做出投资决策。\n"
            "过往业绩不代表未来表现，市场价格可能大幅波动。\n"
        )
        markdown_content.append(risk_text)
        
        # 添加页脚
        markdown_content.append("---\n")
        markdown_content.append(f"*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
        
        # 保存Markdown文件
        json_path = Path(json_file_path)
        output_path = json_path.parent / f"{json_path.stem}_report.md"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(markdown_content))
        
        print(f"✅ Markdown报告已生成: {output_path}")
        print(f"🎉 转换成功！可以用任何文本编辑器或Markdown查看器打开: {output_path}")
        
        return str(output_path)
        
    except Exception as e:
        print(f"❌ 转换失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """主函数"""
    if len(sys.argv) != 2:
        print("使用方法: python json_to_markdown_converter.py <json_file_path>")
        print("示例: python json_to_markdown_converter.py progress_logs/session_20250729_161432.json")
        sys.exit(1)
    
    json_file_path = sys.argv[1]
    
    if not Path(json_file_path).exists():
        print(f"❌ 文件不存在: {json_file_path}")
        sys.exit(1)
    
    create_markdown_report(json_file_path)

if __name__ == "__main__":
    main()