#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TradingAgents-MCPmode Web前端
国金证券人工智能实验室 - 专业一体化交易分析平台
"""

import streamlit as st
import os
import sys
import json
import asyncio
import threading
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入样式加载器
try:
    from src.web.css_loader import (
        load_financial_css, inject_custom_html, create_header_html,
        create_metric_card_html, create_status_indicator_html,
        create_section_card_html, create_workflow_stage_html,
        apply_button_style
    )
except ImportError as e:
    st.error(f"无法导入CSS样式模块: {e}")

# 导入工作流程编排器
try:
    from src.workflow_orchestrator import WorkflowOrchestrator
except ImportError as e:
    WorkflowOrchestrator = None
    st.error(f"无法导入WorkflowOrchestrator: {e}")

# 导入导出工具
try:
    from src.dumptools.json_to_markdown import JSONToMarkdownConverter
    from src.dumptools.md2pdf import MarkdownToPDFConverter 
    from src.dumptools.md2docx import MarkdownToDocxConverter
except ImportError as e:
    st.error(f"无法导入导出工具: {e}")
    JSONToMarkdownConverter = None
    MarkdownToPDFConverter = None
    MarkdownToDocxConverter = None

# 页面配置
st.set_page_config(
    page_title="国金证券AI实验室 - TradingAgents",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 初始化会话状态
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


def load_page_styles():
    """加载页面样式"""
    # 加载自定义CSS
    load_financial_css()
    # 隐藏Streamlit默认元素
    inject_custom_html()
    # 应用按钮样式
    apply_button_style()


def show_system_overview():
    """系统概览区域"""
    # 获取系统统计数据
    dump_dir = Path("src/dump")
    session_count = len(list(dump_dir.glob("session_*.json"))) if dump_dir.exists() else 0
    
    # 创建指标网格
    metrics_html = f"""
    <div class="metric-grid">
        {create_metric_card_html("智能体数量", "15", "分布式分析")}
        {create_metric_card_html("分析维度", "7", "全方位覆盖")}
        {create_metric_card_html("辩论机制", "2层", "看涨/看跌+风险")}
        {create_metric_card_html("市场支持", "3个", "A股/港股/美股")}
        {create_metric_card_html("历史会话", str(session_count), "可查看和导出")}
        {create_metric_card_html("导出格式", "3种", "MD/PDF/DOCX")}
    </div>
    """
    
    st.markdown(metrics_html, unsafe_allow_html=True)


def show_workflow_diagram():
    """工作流程图"""
    workflow_html = f"""
    {create_section_card_html("🔄 智能体工作流程", f"""
        {create_workflow_stage_html("阶段1: 分析师团队", [
            "🏢 公司概述", "📈 市场技术", "😊 市场情绪",
            "📰 新闻信息", "📋 基本面", "👥 股东结构", "🏭 产品分析"
        ])}
        {create_workflow_stage_html("阶段2: 一层辩论", [
            "🐂 看涨研究员", "🐻 看跌研究员"
        ])}
        {create_workflow_stage_html("阶段3: 管理层决策", [
            "🎯 研究经理", "💰 交易员"
        ])}
        {create_workflow_stage_html("阶段4: 风险管理", [
            "⚡ 激进风险", "🛡️ 保守风险", "⚖️ 中性风险", "🎯 风险经理"
        ])}
    """, "🔄")}
    """
    
    st.markdown(workflow_html, unsafe_allow_html=True)


def show_real_time_analysis():
    """实时分析模块"""
    analysis_html = f"""
    {create_section_card_html("🔍 实时分析", """
        <p>在下方输入您的查询，系统将调用15个专业智能体进行全方位分析</p>
    """, "🔍")}
    """
    
    st.markdown(analysis_html, unsafe_allow_html=True)
    
    # 检查WorkflowOrchestrator是否可用
    if WorkflowOrchestrator is None:
        st.error("😱 无法加载WorkflowOrchestrator，请检查后端配置")
        return
    
    # 分析输入
    query = st.text_area(
        "请输入您的分析查询",
        placeholder="例如：给我分析一下600833吧\n例如：分析苹果公司(AAPL)的投资价值",
        height=100,
        key="analysis_query"
    )
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("🚀 开始分析", type="primary", disabled=st.session_state.analysis_running):
            if query:
                start_analysis(query)
            else:
                st.error("请输入分析查询")
    
    with col2:
        if st.button("⏹️ 停止分析", disabled=not st.session_state.analysis_running):
            st.session_state.analysis_running = False
            st.session_state.analysis_status = "已停止"
            st.info("分析已停止")
            st.rerun()
    
    with col3:
        if st.button("🔄 重置状态"):
            reset_analysis_state()
            st.rerun()
    
    # 显示分析状态
    if st.session_state.analysis_running or st.session_state.analysis_completed:
        status = st.session_state.get('analysis_status', '正在初始化...')
        progress = st.session_state.get('analysis_progress', 0)
        
        # 使用HTML创建更美观的状态显示
        if st.session_state.analysis_running:
            status_html = create_status_indicator_html('running', status)
        elif st.session_state.analysis_completed:
            status_html = create_status_indicator_html('completed', "分析完成")
        else:
            status_html = create_status_indicator_html('idle', "系统空闲")
        
        st.markdown(status_html, unsafe_allow_html=True)
        
        # 进度条
        st.progress(progress / 100.0)
        
        # 如果分析完成且有结果
        if st.session_state.analysis_completed and st.session_state.analysis_result:
            result = st.session_state.analysis_result
            if isinstance(result, dict):
                # 显示执行统计
                mcp_calls = len(result.get('mcp_tool_calls', []))
                agent_history = result.get('agent_execution_history', [])
                agent_executions = len(agent_history)
                mcp_enabled_agents = len([h for h in agent_history if h.get("mcp_used", False)])
                
                stats_html = f"""
                <div class="metric-grid">
                    {create_metric_card_html("智能体执行", str(agent_executions))}
                    {create_metric_card_html("MCP调用", str(mcp_calls))}
                    {create_metric_card_html("启用MCP", f"{mcp_enabled_agents}/{agent_executions}")}
                </div>
                """
                st.markdown(stats_html, unsafe_allow_html=True)


def show_history_management():
    """历史会话管理"""
    history_html = f"""
    {create_section_card_html("📚 历史会话", """
        <p>选择、加载和导出历史分析会话</p>
    """, "📚")}
    """
    
    st.markdown(history_html, unsafe_allow_html=True)
    
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
    
    # 显示最近的3个会话作为快速访问
    col1, col2, col3 = st.columns(3)
    
    for idx, json_file in enumerate(json_files[:3]):
        with [col1, col2, col3][idx]:
            file_time = datetime.fromtimestamp(json_file.stat().st_mtime)
            
            with st.container():
                st.markdown(f"""
                <div class="session-card" onclick="load_session('{json_file}')">
                    <div class="session-title">{json_file.name}</div>
                    <div class="session-meta">{file_time.strftime('%m-%d %H:%M')}</div>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"📖 加载", key=f"load_{idx}"):
                    load_session_data(str(json_file))
    
    # 完整文件选择器
    if len(json_files) > 3:
        st.markdown("#### 📋 所有历史会话")
        
        file_options = []
        for json_file in json_files:
            file_time = datetime.fromtimestamp(json_file.stat().st_mtime)
            file_size = json_file.stat().st_size
            file_options.append(f"{json_file.name} ({file_time.strftime('%Y-%m-%d %H:%M:%S')}, {file_size}B)")
        
        selected_index = st.selectbox(
            "选择历史会话",
            range(len(file_options)),
            format_func=lambda i: file_options[i],
            key="full_history_selector"
        )
        
        if st.button("📖 加载选中会话"):
            load_session_data(str(json_files[selected_index]))


def show_export_options():
    """导出选项"""
    if not st.session_state.current_session_data or not st.session_state.selected_session_file:
        st.info("请先加载历史会话数据")
        return
    
    export_html = f"""
    {create_section_card_html("📤 导出选项", """
        <p>将当前加载的会话导出为不同格式的报告</p>
    """, "📤")}
    """
    
    st.markdown(export_html, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 导出Markdown", use_container_width=True):
            export_to_markdown()
    
    with col2:
        if st.button("📄 导出PDF", use_container_width=True):
            export_to_pdf()
    
    with col3:
        if st.button("📄 导出Word", use_container_width=True):
            export_to_docx()


def show_analysis_results():
    """分析结果展示"""
    if not st.session_state.current_session_data:
        st.info("请先运行分析或加载历史会话查看结果")
        return
    
    results_html = f"""
    {create_section_card_html("📈 分析结果", """
        <p>当前会话的详细智能体分析结果</p>
    """, "📈")}
    """
    
    st.markdown(results_html, unsafe_allow_html=True)
    
    data = st.session_state.current_session_data
    
    # 显示会话基本信息
    info_col1, info_col2, info_col3 = st.columns(3)
    with info_col1:
        st.metric("会话ID", data.get('session_id', 'N/A'))
    with info_col2:
        st.metric("状态", data.get('status', 'N/A'))
    with info_col3:
        completed_agents = len([agent for agent in data.get('agents', []) if agent.get('status') == 'completed'])
        st.metric("完成智能体", f"{completed_agents}/{len(data.get('agents', []))}")
    
    # 显示用户查询
    if data.get('user_query'):
        st.markdown("**🔍 分析查询:**")
        st.info(data['user_query'])
    
    # 智能体结果标签页
    if data.get('agents'):
        completed_agents = [agent for agent in data['agents'] if agent.get('status') == 'completed']
        
        if completed_agents:
            # 按智能体类型分组
            agent_groups = {
                "📊 分析师团队": ['company_overview_analyst', 'market_analyst', 'sentiment_analyst', 
                            'news_analyst', 'fundamentals_analyst', 'shareholder_analyst', 'product_analyst'],
                "🔄 看涨看跌辩论": ['bull_researcher', 'bear_researcher'],
                "👔 研究与交易": ['research_manager', 'trader'],
                "⚖️ 风险管理": ['aggressive_risk_analyst', 'safe_risk_analyst', 'neutral_risk_analyst', 'risk_manager']
            }
            
            group_tabs = st.tabs(list(agent_groups.keys()))
            
            for tab_idx, (group_name, agent_names) in enumerate(agent_groups.items()):
                with group_tabs[tab_idx]:
                    group_agents = [agent for agent in completed_agents if agent.get('agent_name') in agent_names]
                    
                    if group_agents:
                        for agent in group_agents:
                            show_agent_result(agent)
                    else:
                        st.info(f"{group_name.split(' ', 1)[1]}暂无完成的分析结果")
        else:
            st.info("该会话中暂无完成的智能体分析结果")
    else:
        st.info("该会话中暂无智能体数据")


def show_agent_result(agent: Dict[str, Any]):
    """显示单个智能体结果"""
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
        'bull_researcher': '🐂 看涨研究员',
        'bear_researcher': '🐻 看跌研究员',
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


# 导出功能
def export_to_markdown():
    """导出Markdown"""
    if not JSONToMarkdownConverter:
        st.error("❌ Markdown导出器不可用")
        return
    
    try:
        converter = JSONToMarkdownConverter("src/dump")
        result = converter.convert_json_to_markdown(st.session_state.selected_session_file)
        if result and os.path.exists(result):
            st.success(f"✅ Markdown导出成功: {result}")
            
            # 提供下载链接
            with open(result, 'r', encoding='utf-8') as f:
                content = f.read()
            
            st.download_button(
                label="⬇️ 下载Markdown文件",
                data=content,
                file_name=f"{Path(result).name}",
                mime="text/markdown"
            )
        else:
            st.error("❌ Markdown导出失败")
    except Exception as e:
        st.error(f"❌ 导出错误: {str(e)}")


def export_to_pdf():
    """导出PDF"""
    if not MarkdownToPDFConverter:
        st.error("❌ PDF导出器不可用")
        return
    
    try:
        converter = MarkdownToPDFConverter("src/dump")
        result = converter.convert_json_to_pdf_via_markdown(st.session_state.selected_session_file)
        if result and os.path.exists(result):
            st.success(f"✅ PDF导出成功: {result}")
            
            # 提供下载链接
            with open(result, 'rb') as f:
                content = f.read()
            
            st.download_button(
                label="⬇️ 下载PDF文件",
                data=content,
                file_name=f"{Path(result).name}",
                mime="application/pdf"
            )
        else:
            st.error("❌ PDF导出失败")
    except Exception as e:
        st.error(f"❌ PDF导出错误: {str(e)}")


def export_to_docx():
    """导出Word文档"""
    if not MarkdownToDocxConverter:
        st.error("❌ DOCX导出器不可用")
        return
    
    try:
        converter = MarkdownToDocxConverter("src/dump")
        result = converter.convert_json_to_docx_via_markdown(st.session_state.selected_session_file)
        if result and os.path.exists(result):
            st.success(f"✅ DOCX导出成功: {result}")
            
            # 提供下载链接
            with open(result, 'rb') as f:
                content = f.read()
            
            st.download_button(
                label="⬇️ 下载Word文件",
                data=content,
                file_name=f"{Path(result).name}",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        else:
            st.error("❌ DOCX导出失败")
    except Exception as e:
        st.error(f"❌ DOCX导出错误: {str(e)}")


def load_session_data(json_file_path: str):
    """加载会话数据"""
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
        st.session_state.selected_session_file = json_file_path
        st.session_state.current_session_data = session_data
        st.success(f"✅ 已加载会话: {Path(json_file_path).name}")
        st.rerun()
    except Exception as e:
        st.error(f"❌ 加载失败: {str(e)}")


def start_analysis(query: str):
    """开始分析"""
    # 重置状态
    st.session_state.analysis_running = True
    st.session_state.analysis_completed = False
    st.session_state.analysis_status = "正在初始化..."
    st.session_state.analysis_progress = 0
    st.session_state.analysis_result = None
    
    # 运行分析
    run_analysis_sync(query)


def run_analysis_sync(query: str):
    """同步运行分析"""
    try:
        load_dotenv()
        
        st.session_state.analysis_status = "正在初始化工作流编排器..."
        st.session_state.analysis_progress = 10
        
        # 使用asyncio.run运行异步函数
        result = asyncio.run(run_single_analysis_async(query))
        
        # 分析成功
        st.session_state.analysis_result = result
        st.session_state.analysis_completed = True
        st.session_state.analysis_status = "✅ 分析完成！"
        st.session_state.analysis_progress = 100
        st.session_state.analysis_running = False
        
        st.success("🎉 分析完成！请查看下方结果。")
        st.rerun()
            
    except Exception as e:
        error_msg = str(e)
        st.session_state.analysis_status = f"❌ 分析错误: {error_msg}"
        st.session_state.analysis_running = False
        st.session_state.analysis_completed = False
        
        st.error(f"分析失败: {error_msg}")
        st.rerun()


async def run_single_analysis_async(user_query: str) -> Optional[dict]:
    """运行单次分析"""
    orchestrator = WorkflowOrchestrator("mcp_config.json")
    
    try:
        st.session_state.analysis_status = "正在初始化工作流编排器..."
        st.session_state.analysis_progress = 10
        await orchestrator.initialize()
        
        st.session_state.analysis_status = "正在加载配置信息..."
        st.session_state.analysis_progress = 20
        
        workflow_info = orchestrator.get_workflow_info()
        enabled_agents = orchestrator.get_enabled_agents()
        
        st.session_state.analysis_status = f"启用的智能体: {len(enabled_agents)}个"
        st.session_state.analysis_progress = 30
        
        st.session_state.analysis_status = f"正在分析: {user_query}"
        st.session_state.analysis_progress = 50
        
        result = await orchestrator.run_analysis(user_query)
        
        st.session_state.analysis_status = "正在处理结果..."
        st.session_state.analysis_progress = 90
        
        # 将结果加载到会话状态
        if result:
            st.session_state.current_session_data = result
        
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


def main():
    """主界面"""
    # 加载样式
    load_page_styles()
    
    # 显示专业抬头
    st.markdown(create_header_html(), unsafe_allow_html=True)
    
    # 系统概览
    show_system_overview()
    
    # 工作流程图
    show_workflow_diagram()
    
    st.markdown("---")
    
    # 实时分析区域
    show_real_time_analysis()
    
    st.markdown("---")
    
    # 历史会话管理
    show_history_management()
    
    st.markdown("---")
    
    # 导出选项
    show_export_options()
    
    st.markdown("---")
    
    # 分析结果展示
    show_analysis_results()
    
    # 底部状态信息
    st.markdown("---")
    
    # 检查配置状态
    env_status = "✅" if Path(".env").exists() else "❌"
    mcp_status = "✅" if Path("mcp_config.json").exists() else "❌"
    
    status_html = f"""
    <div style="text-align: center; color: var(--text-muted); font-size: 0.9rem; margin-top: 2rem;">
        <p>系统状态: 环境配置 {env_status} | MCP配置 {mcp_status} | 🏛️ 国金证券人工智能实验室</p>
    </div>
    """
    
    st.markdown(status_html, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
