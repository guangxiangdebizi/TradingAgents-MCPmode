#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TradingAgents-MCPmode Web前端
简化版单页面应用
"""

import streamlit as st
import os
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from src.workflow_orchestrator import WorkflowOrchestrator
except ImportError as e:
    WorkflowOrchestrator = None
    st.error(f"无法导入WorkflowOrchestrator: {e}")

# 页面配置
st.set_page_config(
    page_title="TradingAgents-MCPmode",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化会话状态
if "selected_menu" not in st.session_state:
    st.session_state.selected_menu = "首页"
if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = None
if "analysis_running" not in st.session_state:
    st.session_state.analysis_running = False
if "selected_session_file" not in st.session_state:
    st.session_state.selected_session_file = None
if "current_session_data" not in st.session_state:
    st.session_state.current_session_data = None
if "analysis_status" not in st.session_state:
    st.session_state.analysis_status = ""
if "analysis_progress" not in st.session_state:
    st.session_state.analysis_progress = 0
if "analysis_completed" not in st.session_state:
    st.session_state.analysis_completed = False
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None


def setup_sidebar():
    """设置侧边栏导航"""
    st.sidebar.title("🤖 TradingAgents-MCPmode")
    st.sidebar.markdown("基于MCP工具的多智能体交易分析系统")
    
    # 主导航菜单
    menu_options = [
        "🏠 首页",
        "📊 实时分析",
        "📈 分析师团队",
        "🔄 看涨看跌辩论",
        "👔 研究经理/交易员",
        "⚠️ 风险辩论/风险经理",
        "📋 历史报告"
    ]
    
    selected = st.sidebar.selectbox(
        "选择页面",
        menu_options,
        index=0,
        key="menu_selector"
    )
    
    # 更新选中的菜单
    st.session_state.selected_menu = selected.split(" ", 1)[1]  # 去掉emoji
    
    # 系统状态
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 系统状态")
    
    if st.session_state.analysis_running:
        st.sidebar.warning("🔄 分析进行中...")
    else:
        st.sidebar.info("💤 系统空闲")
    
    # 环境检查
    env_file = Path(".env")
    if env_file.exists():
        st.sidebar.success("✅ 环境配置已加载")
    else:
        st.sidebar.error("❌ 未找到.env配置文件")


def show_home_page():
    """首页"""
    st.title("🏠 TradingAgents-MCPmode")
    st.markdown("### 基于MCP工具的多智能体交易分析系统")
    
    # 系统概览
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("智能体数量", "15")
        st.metric("分析维度", "7")
    
    with col2:
        st.metric("辩论机制", "2层")
        st.metric("支持市场", "3个")
    
    with col3:
        # 显示历史会话数量
        dump_dir = Path("src/dump")
        if dump_dir.exists():
            session_count = len(list(dump_dir.glob("session_*.json")))
            st.metric("历史会话", f"{session_count}")
        else:
            st.metric("历史会话", "0")
        st.metric("导出格式", "4种")
    
    # 工作流程图
    st.markdown("---")
    st.markdown("### 🔄 智能体工作流程")
    
    st.markdown("""
    #### 📊 四阶段分析流程：
    
    **阶段1: 分析师团队** 📊
    - 🏢 公司概述分析师 → 📈 市场分析师 → 😊 情绪分析师 → 📰 新闻分析师 → 📋 基本面分析师 → 👥 股东分析师 → 🏭 产品分析师
    
    **阶段2: 投资辩论** 💭
    - 📈 看涨研究员 ↔ 📉 看跌研究员 (循环辩论)
    
    **阶段3: 投资决策** 👔
    - 🎯 研究经理 → 💰 交易员
    
    **阶段4: 风险管理** ⚠️
    - ⚡ 激进风险分析师 ↔ 🛡️ 保守风险分析师 ↔ ⚖️ 中性风险分析师 → 🎯 风险经理
    """)
    
    # 使用说明
    st.markdown("---")
    st.markdown("### 📝 使用说明")
    
    st.info("""
    1. **首次使用**：请在项目根目录下配置.env文件，设置LLM API密钥和参数
    2. **MCP权限**：在.env文件中设置各智能体的MCP_ENABLED参数为true/false
    3. **开始分析**：在"实时分析"页面输入自然语言查询开始分析
    4. **查看结果**：分析完成后可在各智能体页面查看详细结果
    5. **历史管理**：在"历史报告"页面选择、加载和导出历史分析结果
    """)





def show_analysis_page():
    """实时分析页面"""
    st.title("📊 实时分析")
    
    # 检查WorkflowOrchestrator是否可用
    if WorkflowOrchestrator is None:
        st.error("😱 无法加载WorkflowOrchestrator，请检查后端配置")
        return
    
    # 分析输入
    query = st.text_area(
        "📝 请输入您的分析查询",
        placeholder="例如：给我分析一下600833吧\n例如：分析苹果公司(AAPL)的投资价值",
        height=100
    )
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("🚀 开始分析", type="primary", disabled=st.session_state.analysis_running):
            if query:
                # 开始分析！这里调用真实的分析功能
                start_analysis(query)
            else:
                st.error("请输入分析查询")
    
    with col2:
        if st.button("⏹️ 停止分析", disabled=not st.session_state.analysis_running):
            st.session_state.analysis_running = False
            st.session_state.analysis_status = "已停止"
            st.info("分析已停止")
            st.rerun()
    
    # 显示分析状态
    if st.session_state.analysis_running or st.session_state.analysis_completed:
        st.markdown("---")
        st.markdown("### 📈 分析进度")
        
        status = st.session_state.get('analysis_status', '正在初始化...')
        progress = st.session_state.get('analysis_progress', 0)
        
        # 显示进度条和状态
        progress_bar = st.progress(progress / 100.0)
        st.text(status)
        
        # 如果分析完成且有结果
        if st.session_state.analysis_completed and st.session_state.analysis_result:
            st.success("✅ 分析完成！")
            st.info("📊 请在各智能体页面查看详细结果，或者在历史报告页面管理会话。")
            
            # 显示一些基本信息
            if isinstance(st.session_state.analysis_result, dict):
                result = st.session_state.analysis_result
                
                # 显示执行统计
                mcp_calls = len(result.get('mcp_tool_calls', []))
                agent_history = result.get('agent_execution_history', [])
                agent_executions = len(agent_history)
                mcp_enabled_agents = len([h for h in agent_history if h.get("mcp_used", False)])
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("智能体执行次数", agent_executions)
                with col2:
                    st.metric("MCP工具调用", mcp_calls)
                with col3:
                    st.metric("启用MCP的智能体", f"{mcp_enabled_agents}/{agent_executions}")
            
            # 重置按钮
            if st.button("🔄 开始新的分析"):
                reset_analysis_state()
                st.rerun()
    
    # 显示配置状态
    st.markdown("---")
    st.markdown("### ⚙️ 系统状态")
    
    # 检查配置文件
    env_file = Path(".env")
    config_file = Path("mcp_config.json")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if env_file.exists():
            st.success("✅ .env配置文件存在")
        else:
            st.error("❌ .env配置文件不存在")
    
    with col2:
        if config_file.exists():
            st.success("✅ MCP配置文件存在")
        else:
            st.error("❌ MCP配置文件不存在")


def start_analysis(query: str):
    """开始分析（使用简单的同步方式）"""
    # 重置状态
    st.session_state.analysis_running = True
    st.session_state.analysis_completed = False
    st.session_state.analysis_status = "正在初始化..."
    st.session_state.analysis_progress = 0
    st.session_state.analysis_result = None
    
    # 直接在主线程中运行分析（避免线程问题）
    run_analysis_sync(query)


def run_analysis_sync(query: str):
    """同步运行分析（简化版）"""
    try:
        # 加载环境变量
        load_dotenv()
        
        # 更新状态
        st.session_state.analysis_status = "正在初始化工作流编排器..."
        st.session_state.analysis_progress = 10
        
        # 使用asyncio.run运行异步函数
        import asyncio
        result = asyncio.run(run_single_analysis_async(query))
        
        # 分析成功
        st.session_state.analysis_result = result
        st.session_state.analysis_completed = True
        st.session_state.analysis_status = "✅ 分析完成！"
        st.session_state.analysis_progress = 100
        st.session_state.analysis_running = False
        
        # 显示成功信息
        st.success("🎉 分析完成！请在各智能体页面查看结果。")
        st.rerun()
            
    except Exception as e:
        # 分析失败
        error_msg = str(e)
        st.session_state.analysis_status = f"❌ 分析错误: {error_msg}"
        st.session_state.analysis_running = False
        st.session_state.analysis_completed = False
        
        # 显示错误信息
        st.error(f"分析失败: {error_msg}")
        st.rerun()


async def run_single_analysis_async(user_query: str) -> Optional[dict]:
    """运行单次分析（完全按照 main.py 的逻辑）"""
    orchestrator = WorkflowOrchestrator("mcp_config.json")
    
    try:
        # 初始化
        st.session_state.analysis_status = "正在初始化工作流编排器..."
        st.session_state.analysis_progress = 10
        await orchestrator.initialize()
        
        # 显示配置信息
        st.session_state.analysis_status = "正在加载配置信息..."
        st.session_state.analysis_progress = 20
        
        workflow_info = orchestrator.get_workflow_info()
        enabled_agents = orchestrator.get_enabled_agents()
        
        st.session_state.analysis_status = f"启用的智能体: {len(enabled_agents)}个"
        st.session_state.analysis_progress = 30
        
        # 运行分析
        st.session_state.analysis_status = f"正在分析: {user_query}"
        st.session_state.analysis_progress = 50
        
        result = await orchestrator.run_analysis(user_query)
        
        st.session_state.analysis_status = "正在处理结果..."
        st.session_state.analysis_progress = 90
        
        return result
        
    except Exception as e:
        st.session_state.analysis_status = f"分析过程中发生错误: {e}"
        raise
    finally:
        await orchestrator.close()


def reset_analysis_state():
    """重置分析状态"""
    st.session_state.analysis_running = False
    st.session_state.analysis_completed = False
    st.session_state.analysis_status = ""
    st.session_state.analysis_progress = 0
    st.session_state.analysis_result = None


def show_history_page():
    """历史报告页面"""
    st.title("📋 历史报告")
    st.markdown("### 所有历史会话管理和多格式导出")
    
    # 获取所有JSON文件
    dump_dir = Path("src/dump")
    if not dump_dir.exists():
        st.warning("❌ dump目录不存在，请先运行分析生成历史数据")
        return
    
    json_files = list(dump_dir.glob("session_*.json"))
    if not json_files:
        st.info("📭 暂无历史分析数据")
        return
    
    # 按修改时间排序，最新的在前
    json_files = sorted(json_files, key=lambda f: f.stat().st_mtime, reverse=True)
    
    # 文件选择
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("#### 📂 选择历史会话")
        
        # 文件列表显示
        file_options = []
        for json_file in json_files:
            file_time = datetime.fromtimestamp(json_file.stat().st_mtime)
            file_size = json_file.stat().st_size
            file_options.append(f"{json_file.name} ({file_time.strftime('%Y-%m-%d %H:%M:%S')}, {file_size}B)")
        
        selected_index = st.selectbox(
            "选择要查看的历史会话",
            range(len(file_options)),
            format_func=lambda i: file_options[i],
            key="history_file_selector"
        )
        
        selected_file = json_files[selected_index]
        
    with col2:
        st.markdown("#### 🎯 快速操作")
        
        # 刷新按钮
        if st.button("🔄 刷新文件列表"):
            st.rerun()
        
        # 加载会话数据按钮
        if st.button("📖 加载会话数据", type="primary"):
            try:
                with open(selected_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                st.session_state.selected_session_file = str(selected_file)
                st.session_state.current_session_data = session_data
                st.success(f"✅ 已加载会话: {selected_file.name}")
                st.rerun()
            except Exception as e:
                st.error(f"❌ 加载失败: {str(e)}")
    
    # 显示当前加载的会话信息
    if st.session_state.current_session_data:
        st.markdown("---")
        st.markdown("### 📊 当前会话信息")
        
        data = st.session_state.current_session_data
        
        # 基本信息
        info_col1, info_col2, info_col3 = st.columns(3)
        with info_col1:
            st.metric("会话ID", data.get('session_id', 'N/A'))
        with info_col2:
            st.metric("状态", data.get('status', 'N/A'))
        with info_col3:
            completed_agents = len([agent for agent in data.get('agents', []) if agent.get('status') == 'completed'])
            st.metric("完成智能体", f"{completed_agents}/{len(data.get('agents', []))}")
        
        # 用户查询
        if data.get('user_query'):
            st.markdown("#### 🔍 分析查询")
            st.info(data['user_query'])
        
        # 导出功能
        st.markdown("---")
        st.markdown("### 📤 导出选项")
        
        export_col1, export_col2, export_col3 = st.columns(3)
        
        with export_col1:
            if st.button("📝 导出Markdown", use_container_width=True):
                try:
                    # 使用现有的JSON转换器
                    from src.dumptools.json_to_markdown import JSONToMarkdownConverter
                    converter = JSONToMarkdownConverter("src/dump")
                    result = converter.convert_json_to_markdown(st.session_state.selected_session_file)
                    if result:
                        st.success(f"✅ Markdown导出成功: {result}")
                    else:
                        st.error("❌ Markdown导出失败")
                except Exception as e:
                    st.error(f"❌ 导出错误: {str(e)}")
        
        with export_col2:
            st.button("📄 导出PDF", use_container_width=True, help="PDF导出功能开发中")
        
        with export_col3:
            st.button("📃 导出DOCX", use_container_width=True, help="DOCX导出功能开发中")
        
        # 会话详情预览
        st.markdown("---")
        st.markdown("### 👁️ 会话详情预览")
        
        # 智能体结果标签页
        if data.get('agents'):
            completed_agents = [agent for agent in data['agents'] if agent.get('status') == 'completed']
            
            if completed_agents:
                # 按智能体类型分组
                agent_groups = {
                    "分析师团队": ['company_overview_analyst', 'market_analyst', 'sentiment_analyst', 
                                'news_analyst', 'fundamentals_analyst', 'shareholder_analyst', 'product_analyst'],
                    "投资辩论": ['bull_researcher', 'bear_researcher'],
                    "管理层": ['research_manager', 'trader'],
                    "风险管理": ['aggressive_risk_analyst', 'safe_risk_analyst', 'neutral_risk_analyst', 'risk_manager']
                }
                
                group_tabs = st.tabs(list(agent_groups.keys()))
                
                for tab_idx, (group_name, agent_names) in enumerate(agent_groups.items()):
                    with group_tabs[tab_idx]:
                        group_agents = [agent for agent in completed_agents if agent.get('agent_name') in agent_names]
                        
                        if group_agents:
                            for agent in group_agents:
                                agent_name = agent.get('agent_name', 'Unknown')
                                
                                # 智能体名称映射
                                name_mapping = {
                                    'company_overview_analyst': '🏢 公司概述分析师',
                                    'market_analyst': '📈 市场分析师',
                                    'sentiment_analyst': '😊 情绪分析师',
                                    'news_analyst': '📰 新闻分析师',
                                    'fundamentals_analyst': '📋 基本面分析师',
                                    'shareholder_analyst': '👥 股东分析师',
                                    'product_analyst': '🏭 产品分析师',
                                    'bull_researcher': '📈 看涨研究员',
                                    'bear_researcher': '📉 看跌研究员',
                                    'research_manager': '🎯 研究经理',
                                    'trader': '💰 交易员',
                                    'aggressive_risk_analyst': '⚡ 激进风险分析师',
                                    'safe_risk_analyst': '🛡️ 保守风险分析师',
                                    'neutral_risk_analyst': '⚖️ 中性风险分析师',
                                    'risk_manager': '🎯 风险经理'
                                }
                                
                                display_name = name_mapping.get(agent_name, f"🤖 {agent_name}")
                                
                                with st.expander(display_name, expanded=False):
                                    if agent.get('result'):
                                        st.markdown(agent['result'])
                                    else:
                                        st.info("该智能体暂无分析结果")
                        else:
                            st.info(f"{group_name}暂无完成的分析结果")
            else:
                st.info("该会话中暂无完成的智能体分析结果")
        else:
            st.info("该会话中暂无智能体数据")
    
    else:
        st.info("👆 请先选择并加载历史会话数据")


def show_agent_results_with_history(title: str, agent_names: list):
    """显示智能体结果（支持历史数据）"""
    st.title(title)
    
    # 检查是否有历史会话数据
    if st.session_state.current_session_data:
        data = st.session_state.current_session_data
        st.info(f"📖 当前显示历史会话: {Path(st.session_state.selected_session_file).name}")
        
        # 找到相关智能体
        agents = data.get('agents', [])
        relevant_agents = [agent for agent in agents if agent.get('agent_name') in agent_names and agent.get('status') == 'completed']
        
        if relevant_agents:
            # 智能体名称映射
            name_mapping = {
                'company_overview_analyst': '🏢 公司概述分析师',
                'market_analyst': '📈 市场分析师',
                'sentiment_analyst': '😊 情绪分析师',
                'news_analyst': '📰 新闻分析师',
                'fundamentals_analyst': '📋 基本面分析师',
                'shareholder_analyst': '👥 股东分析师',
                'product_analyst': '🏭 产品分析师',
                'bull_researcher': '📈 看涨研究员',
                'bear_researcher': '📉 看跌研究员',
                'research_manager': '🎯 研究经理',
                'trader': '💰 交易员',
                'aggressive_risk_analyst': '⚡ 激进风险分析师',
                'safe_risk_analyst': '🛡️ 保守风险分析师',
                'neutral_risk_analyst': '⚖️ 中性风险分析师',
                'risk_manager': '🎯 风险经理'
            }
            
            # 为每个智能体创建标签页
            if len(relevant_agents) > 1:
                agent_tabs = st.tabs([name_mapping.get(agent['agent_name'], agent['agent_name']) for agent in relevant_agents])
                
                for tab_idx, agent in enumerate(relevant_agents):
                    with agent_tabs[tab_idx]:
                        if agent.get('result'):
                            st.markdown(agent['result'])
                        else:
                            st.info("该智能体暂无分析结果")
            else:
                # 只有一个智能体，直接显示
                agent = relevant_agents[0]
                if agent.get('result'):
                    st.markdown(agent['result'])
                else:
                    st.info("该智能体暂无分析结果")
        else:
            st.warning(f"在当前历史会话中未找到相关智能体的完成结果")
    else:
        st.info("📋 请先在'历史报告'页面选择并加载历史会话数据")
        st.markdown("或者在'实时分析'页面开始新的分析")


def main():
    """主函数"""
    # 设置侧边栏
    setup_sidebar()
    
    # 根据选中的菜单显示对应页面
    try:
        if st.session_state.selected_menu == "首页":
            show_home_page()
        elif st.session_state.selected_menu == "实时分析":
            show_analysis_page()
        elif st.session_state.selected_menu == "分析师团队":
            show_agent_results_with_history("📈 分析师团队", 
                                           ['company_overview_analyst', 'market_analyst', 'sentiment_analyst', 
                                            'news_analyst', 'fundamentals_analyst', 'shareholder_analyst', 'product_analyst'])
        elif st.session_state.selected_menu == "看涨看跌辩论":
            show_agent_results_with_history("🔄 看涨看跌辩论", ['bull_researcher', 'bear_researcher'])
        elif st.session_state.selected_menu == "研究经理/交易员":
            show_agent_results_with_history("👔 研究经理/交易员", ['research_manager', 'trader'])
        elif st.session_state.selected_menu == "风险辩论/风险经理":
            show_agent_results_with_history("⚠️ 风险辩论/风险经理", 
                                           ['aggressive_risk_analyst', 'safe_risk_analyst', 'neutral_risk_analyst', 'risk_manager'])
        elif st.session_state.selected_menu == "历史报告":
            show_history_page()
        else:
            show_home_page()
            
    except Exception as e:
        st.error(f"页面加载出错: {str(e)}")
        st.session_state.selected_menu = "首页"
        show_home_page()


if __name__ == "__main__":
    main()
