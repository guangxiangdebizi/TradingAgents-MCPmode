#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TradingAgents-MCPmode 主程序
基于MCP工具的多智能体交易分析系统
"""

import os
import sys
import asyncio
import argparse
from typing import Optional
from dotenv import load_dotenv

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.workflow_orchestrator import WorkflowOrchestrator
from src.agent_states import AgentState


def setup_logging(debug_mode: bool = False, log_file: Optional[str] = None):
    """简化的日志配置"""
    pass  # 不再需要复杂的日志配置


def print_banner():
    """打印程序横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                    TradingAgents-MCPmode                    ║
║                基于MCP工具的多智能体交易分析系统                ║
║                                                              ║
║  🤖 多智能体协作  📊 实时数据分析  🔧 MCP工具集成  📈 交易决策   ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)





def print_analysis_result(result):
    """打印分析结果
    
    Args:
        result: 可以是 AgentState 对象或字典
    """
    # 处理 LangGraph 返回的字典格式
    if isinstance(result, dict):
        state = result
        # 安全获取字典值的辅助函数
        def safe_get(key, default=""):
            return state.get(key, default)
        
        def safe_get_list(key):
            return state.get(key, [])
    else:
        # AgentState 对象
        state = result
        def safe_get(key, default=""):
            return getattr(state, key, default)
        
        def safe_get_list(key):
            return getattr(state, key, [])
    
    print("\n" + "="*80)
    

    
    # 基本信息
    print(f"🏢 用户问题: {safe_get('user_query')}")
    print(f"❓ 用户查询: {safe_get('user_query')}")
    from datetime import datetime
    print(f"⏰ 分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("\n" + "-"*40 + " 分析报告 " + "-"*40)
    
    # 市场分析报告
    market_report = safe_get('market_report')
    if market_report:
        print("\n📈 市场分析报告:")
        print(market_report)
    
    # 情绪分析报告
    sentiment_report = safe_get('sentiment_report')
    if sentiment_report:
        print("\n😊 情绪分析报告:")
        print(sentiment_report)
    
    # 新闻分析报告
    news_report = safe_get('news_report')
    if news_report:
        print("\n📰 新闻分析报告:")
        print(news_report)
    
    # 基本面分析报告
    fundamentals_report = safe_get('fundamentals_report')
    if fundamentals_report:
        print("\n📊 基本面分析报告:")
        print(fundamentals_report)
    
    print("\n" + "-"*40 + " 投资决策 " + "-"*40)
    
    # 投资计划
    investment_plan = safe_get('investment_plan')
    if investment_plan:
        print("\n💡 投资计划:")
        print(investment_plan)
    
    # 交易员投资计划
    trader_investment_plan = safe_get('trader_investment_plan')
    if trader_investment_plan:
        print("\n💰 交易员计划:")
        print(trader_investment_plan)
    
    print("\n" + "-"*40 + " 风险管理 " + "-"*40)
    
    # 最终交易决策
    final_trade_decision = safe_get('final_trade_decision')
    if final_trade_decision:
        print("\n🎯 最终交易决策:")
        print(final_trade_decision)
    
    print("\n" + "-"*40 + " 执行统计 " + "-"*40)
    
    # 执行统计
    mcp_calls = len(safe_get_list('mcp_tool_calls'))
    agent_executions = len(safe_get_list('agent_execution_history'))
    agent_history = safe_get_list('agent_execution_history')
    mcp_enabled_agents = len([h for h in agent_history if h.get("mcp_used", False)])
    
    print(f"\n📊 执行统计:")
    print(f"  • 智能体执行次数: {agent_executions}")
    print(f"  • MCP工具调用次数: {mcp_calls}")
    print(f"  • 启用MCP的智能体: {mcp_enabled_agents}/{agent_executions}")
    
    # 投资辩论统计
    investment_debate_state = safe_get('investment_debate_state', {})
    risk_debate_state = safe_get('risk_debate_state', {})
    investment_rounds = investment_debate_state.get("count", 0) if isinstance(investment_debate_state, dict) else 0
    risk_rounds = risk_debate_state.get("count", 0) if isinstance(risk_debate_state, dict) else 0
    print(f"  • 投资辩论轮次: {investment_rounds}")
    print(f"  • 风险辩论轮次: {risk_rounds}")
    
    # 错误和警告
    errors = safe_get_list('errors')
    if errors:
        print(f"\n❌ 错误 ({len(errors)}):")
        for i, error in enumerate(errors, 1):
            print(f"  {i}. {error}")
    
    warnings = safe_get_list('warnings')
    if warnings:
        print(f"\n⚠️ 警告 ({len(warnings)}):")
        for i, warning in enumerate(warnings, 1):
            print(f"  {i}. {warning}")
    
    print("\n" + "="*80)


async def run_single_analysis(user_query: str, config_file: str):
    """运行单次分析"""
    orchestrator = WorkflowOrchestrator(config_file)
    
    try:
        # 初始化
        print("正在初始化工作流编排器...")
        await orchestrator.initialize()
        
        # 显示配置信息
        workflow_info = orchestrator.get_workflow_info()
        agent_permissions = orchestrator.get_agent_permissions()
        enabled_agents = orchestrator.get_enabled_agents()
        
        print(f"智能体总数: {workflow_info['agents_count']}")
        print(f"启用MCP的智能体: {len(enabled_agents)}")
        print(f"MCP工具总数: {workflow_info['mcp_tools_info']['total_tools']}")
        
        if enabled_agents:
            print(f"启用MCP的智能体: {', '.join(enabled_agents)}")
        
        # 运行分析
        print(f"开始分析用户问题: {user_query}")
        result = await orchestrator.run_analysis(user_query)
        
        # 显示结果
        print_analysis_result(result)
        
        return result
        
    except Exception as e:
        print(f"❌ 分析过程中发生错误: {e}")
        raise
    finally:
        await orchestrator.close()


async def run_interactive_mode(config_file: str):
    """运行交互模式"""
    orchestrator = WorkflowOrchestrator(config_file)
    
    try:
        # 初始化
        print("正在初始化工作流编排器...")
        await orchestrator.initialize()
        
        # 显示配置信息
        workflow_info = orchestrator.get_workflow_info()
        enabled_agents = orchestrator.get_enabled_agents()
        
        print(f"\n🤖 智能体总数: {workflow_info['agents_count']}")
        print(f"🔧 MCP工具总数: {workflow_info['mcp_tools_info']['total_tools']}")
        print(f"✅ 启用MCP的智能体: {len(enabled_agents)}")
        
        if enabled_agents:
            print(f"📋 启用列表: {', '.join(enabled_agents)}")
        
        print("\n" + "="*60)
        print("🚀 交互模式已启动")
        print("💡 输入 'quit' 或 'exit' 退出程序")
        print("💡 输入 'help' 查看帮助信息")
        print("="*60)
        
        while True:
            try:
                print("\n" + "-"*40)
                user_query = input("💬 请输入您的问题 (或 'quit' 退出): ").strip()
                
                if user_query.lower() in ['quit', 'exit', 'q']:
                    print("👋 再见！")
                    break
                
                if user_query.lower() == 'help':
                    print("\n📖 帮助信息:")
                    print("  • 支持自然语言查询，无需指定市场和日期")
                    print("  • 例如: '分析一下苹果公司的股票'")
                    print("  • 例如: '给我分析平安银行的投资价值'")
                    print("  • 例如: '腾讯控股怎么样？'")
                    print("  • 智能体会自动识别股票并获取最新数据")
                    print("  • 输入 'quit' 或 'exit' 退出程序")
                    continue
                
                if not user_query:
                    print("❌ 请输入有效的问题")
                    continue
                
                # 运行分析
                print(f"\n🔄 开始分析用户问题: {user_query}")
                result = await orchestrator.run_analysis(user_query)
                
                # 显示结果
                print_analysis_result(result)
                

                
                # 询问是否继续
                continue_analysis = input("\n🔄 是否继续提问？(y/N): ").strip().lower()
                if continue_analysis not in ['y', 'yes']:
                    print("👋 感谢使用！")
                    break
                    
            except KeyboardInterrupt:
                print("\n\n👋 用户中断，程序退出")
                break
            except Exception as e:
                print(f"❌ 交互过程中发生错误: {e}")
                print(f"❌ 发生错误: {e}")
                continue
                
    finally:
        await orchestrator.close()


def main():
    """主函数"""
    # 加载环境变量
    load_dotenv()
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description="TradingAgents-MCPmode - 基于MCP工具的多智能体交易分析系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python main.py                                    # 交互模式
  python main.py -c AAPL                          # 分析苹果股票
  python main.py -c "苹果公司股票分析"              # 自然语言查询
  python main.py -c "平安银行"                    # 分析A股
  python main.py --interactive                     # 明确指定交互模式
  python main.py --debug --log-file analysis.log  # 调试模式并保存日志
        """
    )
    
    parser.add_argument("-c", "--query", help="用户问题或查询内容")
    parser.add_argument("-i", "--interactive", action="store_true", help="交互模式")
    parser.add_argument("--config", default="mcp_config.json", help="MCP配置文件路径")
    parser.add_argument("--debug", action="store_true", help="启用调试模式")
    parser.add_argument("--log-file", help="日志文件路径")
    parser.add_argument("--version", action="version", version="TradingAgents-MCPmode 1.0.0")
    
    args = parser.parse_args()
    
    # 设置日志
    # 强制开启调试模式以进行问题排查
    args.debug = True
    debug_mode = args.debug or os.getenv("DEBUG_MODE", "false").lower() == "true"
    setup_logging(debug_mode, args.log_file)
    
    # 打印横幅
    print_banner()
    
    # 检查配置文件
    if not os.path.exists(args.config):
        print(f"❌ 配置文件不存在: {args.config}")
        sys.exit(1)
    
    try:
        if args.query:
            # 单次分析模式
            print(f"单次分析模式: {args.query}")
            asyncio.run(run_single_analysis(args.query, args.config))
        else:
            # 交互模式
            print("启动交互模式")
            asyncio.run(run_interactive_mode(args.config))
            
    except KeyboardInterrupt:
        print("用户中断程序")
        sys.exit(0)
    except Exception as e:
        print(f"❌ 程序执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()