#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TradingAgents-MCPmode Web前端
"""

import streamlit as st
import sys
import os
import asyncio
import threading
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
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
    page_title="AI实验室 - TradingAgents",
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


@st.cache_data(ttl=2)
def get_real_analysis_progress():
    """统一进度读取：从真实的会话JSON文件获取进度（带缓存优化）"""
    try:
        dump_dir = Path("src/dump")
        if not dump_dir.exists():
            return None
            
        # 查找最新的会话文件
        session_files = list(dump_dir.glob("session_*.json"))
        if not session_files:
            return None
            
        latest_session = max(session_files, key=lambda f: f.stat().st_mtime)
        
        # 解析会话进度
        with open(latest_session, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        agents = data.get('agents', [])
        total_agents = 15  # 总共15个智能体
        completed_agents = len([a for a in agents if a.get('status') == 'completed'])
        
        progress = (completed_agents / total_agents) * 100 if total_agents > 0 else 0
        
        # 确定当前执行阶段和状态
        current_stage = determine_current_stage(agents)
        
        # 生成状态描述
        if data.get('status') == 'completed':
            status = "分析完成"
        elif data.get('status') == 'cancelled':
            status = "分析已取消"
        elif completed_agents == 0:
            status = "正在初始化..."
        else:
            running_agent = next((a for a in agents if a.get('status') == 'running'), None)
            if running_agent:
                agent_name = running_agent.get('agent_name', '未知智能体')
                display_name = get_agent_display_name(agent_name)
                status = f"正在执行: {display_name}"
            else:
                status = f"已完成 {completed_agents}/{total_agents} 个智能体"
        
        # 获取最后更新时间 - 相对时间显示
        file_time = datetime.fromtimestamp(latest_session.stat().st_mtime)
        now = datetime.now()
        time_diff = now - file_time
        
        if time_diff.total_seconds() < 60:
            last_update = "刚刚"
        elif time_diff.total_seconds() < 3600:
            minutes = int(time_diff.total_seconds() / 60)
            last_update = f"{minutes}分钟前"
        elif time_diff.total_seconds() < 86400:
            hours = int(time_diff.total_seconds() / 3600)
            last_update = f"{hours}小时前"
        else:
            last_update = file_time.strftime('%m-%d %H:%M')
        
        return {
            'progress': progress,
            'status': status,
            'current_stage': current_stage,
            'completed_agents': completed_agents,
            'total_agents': total_agents,
            'last_update': last_update,
            'session_file': str(latest_session),
            'precise_time': file_time.strftime('%Y-%m-%d %H:%M:%S')  # 精确时间供悬停显示
        }
        
    except Exception as e:
        print(f"获取分析进度失败: {e}")
        return None


def determine_current_stage(agents):
    """确定当前执行阶段"""
    # 阶段0: 公司概述
    company_overview_done = any(a.get('agent_name') == 'company_overview_analyst' 
                              and a.get('status') == 'completed' for a in agents)
    if not company_overview_done:
        return 0
    
    # 阶段1: 分析师团队 (6个分析师)
    analyst_names = ['market_analyst', 'sentiment_analyst', 'news_analyst', 
                    'fundamentals_analyst', 'shareholder_analyst', 'product_analyst']
    analysts_done = sum(1 for name in analyst_names 
                       if any(a.get('agent_name') == name and a.get('status') == 'completed' 
                             for a in agents))
    if analysts_done < 6:
        return 1
    
    # 阶段2: 研究员辩论
    bull_done = any(a.get('agent_name') == 'bull_researcher' 
                   and a.get('status') == 'completed' for a in agents)
    bear_done = any(a.get('agent_name') == 'bear_researcher' 
                   and a.get('status') == 'completed' for a in agents)
    if not (bull_done and bear_done):
        return 2
    
    # 阶段3: 管理层
    manager_done = any(a.get('agent_name') == 'research_manager' 
                      and a.get('status') == 'completed' for a in agents)
    trader_done = any(a.get('agent_name') == 'trader' 
                     and a.get('status') == 'completed' for a in agents)
    if not (manager_done and trader_done):
        return 3
    
    # 阶段4: 风险管理
    return 4


def get_agent_display_name(agent_name):
    """获取智能体显示名称"""
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
    return name_mapping.get(agent_name, f"🤖 {agent_name}")


def format_file_size(size_bytes):
    """格式化文件大小为人类可读格式"""
    if size_bytes < 1024:
        return f"{size_bytes}B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f}KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f}MB"


@st.cache_data(ttl=5)
def get_session_files_list():
    """获取会话文件列表（带缓存优化）"""
    dump_dir = Path("src/dump")
    if not dump_dir.exists():
        return []
    
    json_files = list(dump_dir.glob("session_*.json"))
    if not json_files:
        return []
    
    # 按修改时间排序，最新的在前
    return sorted(json_files, key=lambda f: f.stat().st_mtime, reverse=True)


def connect_orchestrator():
    """连接WorkflowOrchestrator"""
    try:
        with st.spinner("正在连接系统..."):
            orchestrator = WorkflowOrchestrator("mcp_config.json")
            # 使用异步运行初始化
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(orchestrator.initialize())
            
            st.session_state.orchestrator = orchestrator
            st.success("✅ 系统连接成功！")
            st.rerun()
    except Exception as e:
        st.error(f"❌ 连接失败: {e}")


def disconnect_orchestrator():
    """断开WorkflowOrchestrator连接"""
    try:
        if st.session_state.get('orchestrator'):
            orchestrator = st.session_state.orchestrator
            # 异步关闭连接
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(orchestrator.close())
            
        st.session_state.orchestrator = None
        st.success("✅ 系统连接已断开")
        st.rerun()
    except Exception as e:
        st.error(f"❌ 断开连接失败: {e}")


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
    """实时分析模块 - 控制条吸顶设计"""
    st.markdown("### 🔍 实时分析")
    
    # 检查WorkflowOrchestrator是否可用
    if WorkflowOrchestrator is None:
        st.error("😱 无法加载WorkflowOrchestrator，请检查后端配置")
        return
    
    # 吸顶控制条 - 紧凑的4列布局
    control_col1, control_col2, control_col3, control_col4 = st.columns([3, 1, 1, 2])
    
    with control_col1:
        query = st.text_input(
            "查询",
            placeholder="例如：给我分析一下600833吧",
            key="analysis_query_compact",
            label_visibility="collapsed"
        )
    
    with control_col2:
        orchestrator_connected = st.session_state.get('orchestrator') is not None
        if orchestrator_connected:
            if st.button("🔌 断开", key="disconnect_compact"):
                disconnect_orchestrator()
                st.rerun()
        else:
            if st.button("🔗 连接", key="connect_compact"):
                connect_orchestrator()
                st.rerun()
    
    with control_col3:
        if st.session_state.analysis_running:
            if st.button("⏹️ 停止", type="secondary", key="stop_compact"):
                stop_analysis()
                st.rerun()
        else:
            analysis_disabled = not query or not orchestrator_connected
            if st.button("🚀 开始", type="primary", disabled=analysis_disabled, key="start_compact"):
                if query:
                    start_analysis(query)
                    st.rerun()
    
    with control_col4:
        # 进度条和状态（细条形式）
        progress_data = get_real_analysis_progress()
        is_running = st.session_state.get('analysis_running', False)
        is_completed = st.session_state.get('analysis_completed', False)
        
        if progress_data and (is_running or is_completed):
            progress = progress_data['progress']
            status = progress_data['status']
            completed_agents = progress_data['completed_agents']
            total_agents = progress_data['total_agents']
            
            # 细进度条
            st.progress(progress / 100.0)
            st.caption(f"{status} ({completed_agents}/{total_agents})")
            
            # 检查完成状态
            if progress >= 100 or status == "分析完成":
                st.session_state.analysis_running = False
                st.session_state.analysis_completed = True
            elif status == "分析已取消":
                st.session_state.analysis_running = False
        else:
            # 备用状态显示
            analysis_state_obj = st.session_state.get('analysis_state_obj')
            if analysis_state_obj and (is_running or is_completed):
                st.progress(analysis_state_obj.progress / 100.0)
                st.caption(analysis_state_obj.status)
            elif is_running:
                progress = st.session_state.get('analysis_progress', 0)
                status = st.session_state.get('analysis_status', '正在运行...')
                st.progress(progress / 100.0)
                st.caption(status)
    
    # 连接状态提示（简化）
    if not orchestrator_connected:
        st.warning("⚠️ 请先连接系统")
        return
    
    # 完成状态提示（简化）
    if st.session_state.analysis_completed:
        st.success("✅ 分析完成！请查看下方结果。")
        
        # 显示执行统计
        result = st.session_state.get('analysis_result')
        if isinstance(result, dict):
            mcp_calls = len(result.get('mcp_tool_calls', []))
            agent_history = result.get('agent_execution_history', [])
            agent_executions = len(agent_history)
            mcp_enabled_agents = len([h for h in agent_history if h.get("mcp_used", False)])
            
            stats_col1, stats_col2, stats_col3 = st.columns(3)
            with stats_col1:
                st.metric("智能体执行", agent_executions)
            with stats_col2:
                st.metric("MCP调用", mcp_calls)
            with stats_col3:
                st.metric("启用MCP", f"{mcp_enabled_agents}/{agent_executions}")
    
    elif st.session_state.analysis_running:
        # 进度容器定时刷新 - 降频到2-3秒
        time.sleep(2)
        st.rerun()


def show_history_management():
    """历史会话管理 - 即选即载+搜索过滤+两列布局"""
    st.markdown("### 📚 历史会话")
    
    # 获取所有JSON文件（使用缓存优化）
    json_files = get_session_files_list()
    if not json_files:
        st.info("📭 暂无历史分析数据")
        return
    
    # 搜索过滤
    search_query = st.text_input(
        "🔍 搜索会话",
        placeholder="按文件名或日期搜索...",
        key="history_search"
    )
    
    # 过滤文件列表
    filtered_files = []
    file_options = []
    
    for json_file in json_files:
        file_time = datetime.fromtimestamp(json_file.stat().st_mtime)
        file_size = format_file_size(json_file.stat().st_size)
        display_name = f"{json_file.name} ({file_time.strftime('%m-%d %H:%M')}, {file_size})"
        
        # 搜索过滤
        if not search_query or search_query.lower() in display_name.lower():
            filtered_files.append(json_file)
            file_options.append(display_name)
    
    if not filtered_files:
        st.info("🔍 未找到匹配的会话")
        return
    
    # 两列布局：左侧选择器，右侧概要+导出
    left_col, right_col = st.columns([2, 3])
    
    with left_col:
        st.markdown("**选择会话**")
        
        # 记忆选中项索引
        if "history_selected_index" not in st.session_state:
            st.session_state.history_selected_index = 0
        
        def on_session_change():
            """会话选择变化时自动加载"""
            selected_idx = st.session_state.history_selector
            if selected_idx < len(filtered_files):
                selected_file = str(filtered_files[selected_idx])
                load_session_data(selected_file)
                st.session_state.history_selected_index = selected_idx
        
        selected_index = st.selectbox(
            "历史会话列表",
            range(len(file_options)),
            index=min(st.session_state.history_selected_index, len(file_options) - 1),
            format_func=lambda i: file_options[i],
            key="history_selector",
            on_change=on_session_change,
            label_visibility="collapsed"
        )
    
    with right_col:
        st.markdown("**会话概要**")
        
        if st.session_state.current_session_data:
            # 显示当前加载的会话概要
            current_file = st.session_state.selected_session_file
            if current_file:
                file_path = Path(current_file)
                file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                
                # 解析会话数据获取概要信息
                try:
                    data = st.session_state.current_session_data
                    agents = data.get('agents', [])
                    completed_agents = len([a for a in agents if a.get('status') == 'completed'])
                    mcp_calls = len(data.get('mcp_tool_calls', []))
                    user_query = data.get('user_query', '未知查询')
                    
                    # 紧凑的概要显示
                    st.success(f"✅ 已加载: {file_path.name}")
                    st.caption(f"📅 {file_time.strftime('%Y-%m-%d %H:%M:%S')}")
                    st.caption(f"🤖 完成智能体: {completed_agents}/15")
                    st.caption(f"🔧 MCP调用: {mcp_calls}")
                    st.caption(f"💬 查询: {user_query[:50]}...")
                    
                    # 导出按钮（紧凑布局）
                    st.markdown("**快速导出**")
                    export_col1, export_col2, export_col3 = st.columns(3)
                    
                    with export_col1:
                        if st.button("📄 MD", key="export_md_compact", help="导出Markdown"):
                            export_to_markdown()
                    
                    with export_col2:
                        if st.button("📄 PDF", key="export_pdf_compact", help="导出PDF"):
                            export_to_pdf()
                    
                    with export_col3:
                        if st.button("📄 Word", key="export_word_compact", help="导出Word"):
                            export_to_docx()
                            
                except Exception as e:
                    st.error(f"解析会话数据失败: {e}")
        else:
            st.info("请选择一个会话进行加载")


def show_export_options():
    """导出选项 - 简化版本（主要功能已集成到历史管理中）"""
    if not st.session_state.current_session_data or not st.session_state.selected_session_file:
        return
    
    # 简化的导出提示
    st.markdown("### 📤 导出报告")
    st.info("💡 提示：可在上方历史会话区域直接导出当前加载的会话")


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
    """显示单个智能体结果 - 摘要+展开模式"""
    agent_name = agent.get('agent_name', 'Unknown')
    display_name = get_agent_display_name(agent_name)
    result_content = agent.get('result', '')
    
    if not result_content:
        with st.expander(display_name, expanded=False):
            st.info("该智能体暂无分析结果")
        return
    
    # 生成摘要（前200-300字符）
    summary_length = 250
    if len(result_content) <= summary_length:
        # 内容较短，直接显示全部
        with st.expander(display_name, expanded=False):
            st.markdown(result_content)
    else:
        # 内容较长，显示摘要+展开按钮
        summary = result_content[:summary_length].strip()
        
        # 找到最后一个完整句子的结尾
        last_period = max(summary.rfind('。'), summary.rfind('.'), summary.rfind('！'), summary.rfind('!'))
        if last_period > summary_length * 0.7:  # 如果句号位置合理
            summary = summary[:last_period + 1]
        
        with st.expander(display_name, expanded=False):
            # 默认显示摘要
            st.markdown(f"{summary}...")
            
            # 展开全文按钮
            expand_key = f"expand_{agent_name}_{hash(result_content) % 10000}"
            if st.button("📖 展开全文", key=expand_key):
                st.markdown("---")
                st.markdown("**完整分析结果：**")
                st.markdown(result_content)


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
    # 检查连接状态
    if not st.session_state.get('orchestrator'):
        st.error("系统未连接，无法开始分析")
        return
    
    # 重置状态
    st.session_state.analysis_running = True
    st.session_state.analysis_completed = False
    st.session_state.analysis_cancelled = False
    st.session_state.analysis_status = "正在初始化..."
    st.session_state.analysis_progress = 0
    st.session_state.analysis_result = None
    
    # 将orchestrator传递给分析函数
    run_analysis_sync(query, st.session_state.orchestrator)


def run_analysis_sync(query: str, orchestrator):
    """在后台线程中运行分析，避免阻塞Streamlit主线程"""
    # 使用全局变量存储状态，避免ScriptRunContext问题
    import threading
    
    class AnalysisState:
        def __init__(self):
            self.cancelled = False
            self.running = True
            self.completed = False
            self.status = "正在初始化..."
            self.progress = 0
            self.result = None
            self.error = None
    
    # 创建状态对象
    analysis_state = AnalysisState()
    
    def run_analysis_thread():
        """后台线程执行分析"""
        try:
            load_dotenv()
            
            # 检查是否已被取消
            if analysis_state.cancelled:
                analysis_state.status = "❌ 分析已取消"
                analysis_state.running = False
                return
            
            # 将orchestrator传递给分析函数（通过函数属性）
            run_single_analysis_async_safe._orchestrator = orchestrator
            
            # 在新的事件循环中运行异步函数
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(run_single_analysis_async_safe(query, analysis_state))
                
                # 再次检查是否已被取消
                if analysis_state.cancelled:
                    analysis_state.status = "❌ 分析已取消"
                    analysis_state.running = False
                    return
                
                # 分析成功
                analysis_state.result = result
                analysis_state.completed = True
                analysis_state.status = "✅ 分析完成！"
                analysis_state.progress = 100
                analysis_state.running = False
                
            finally:
                loop.close()
                # 清理orchestrator引用
                if hasattr(run_single_analysis_async_safe, '_orchestrator'):
                    delattr(run_single_analysis_async_safe, '_orchestrator')
                
        except Exception as e:
            # 检查是否是取消导致的异常
            if analysis_state.cancelled:
                analysis_state.status = "❌ 分析已取消"
            else:
                error_msg = str(e)
                analysis_state.status = f"❌ 分析错误: {error_msg}"
                analysis_state.error = error_msg
            analysis_state.running = False
            analysis_state.completed = False
    
    # 启动后台线程
    thread = threading.Thread(target=run_analysis_thread, daemon=True)
    thread.start()
    
    # 存储线程引用和状态对象
    st.session_state.analysis_thread = thread
    st.session_state.analysis_state_obj = analysis_state


async def run_single_analysis_async_safe(user_query: str, analysis_state) -> Optional[dict]:
    """安全的异步分析函数，重用已连接的orchestrator"""
    # 从session_state获取已连接的orchestrator
    # 注意：这里需要通过全局变量传递，因为在后台线程中无法直接访问session_state
    orchestrator = getattr(run_single_analysis_async_safe, '_orchestrator', None)
    
    if not orchestrator:
        analysis_state.status = "错误：系统未连接"
        return None
    
    try:
        # 检查取消状态
        if analysis_state.cancelled:
            return None
            
        analysis_state.status = "正在加载配置信息..."
        analysis_state.progress = 20
        
        workflow_info = orchestrator.get_workflow_info()
        enabled_agents = orchestrator.get_enabled_agents()
        
        # 检查取消状态
        if analysis_state.cancelled:
            return None
            
        analysis_state.status = f"启用的智能体: {len(enabled_agents)}个"
        analysis_state.progress = 30
        
        # 检查取消状态
        if analysis_state.cancelled:
            return None
            
        analysis_state.status = f"正在分析: {user_query}"
        analysis_state.progress = 50
        
        # 创建取消检查器函数
        def cancel_checker():
            return analysis_state.cancelled
        
        result = await orchestrator.run_analysis(user_query, cancel_checker)
        
        # 检查取消状态
        if analysis_state.cancelled:
            return None
            
        analysis_state.status = "正在处理结果..."
        analysis_state.progress = 90
        
        return result
        
    except Exception as e:
        # 检查是否是取消导致的异常
        if analysis_state.cancelled:
            return None
        analysis_state.status = f"分析过程中发生错误: {e}"
        raise
    # 注意：不再关闭orchestrator，因为它是重用的连接

# 保留原有函数以保持兼容性
async def run_single_analysis_async(user_query: str) -> Optional[dict]:
    """原有的异步分析函数（保留兼容性）"""
    # 使用虚拟状态对象
    class DummyState:
        def __init__(self):
            self.cancelled = False
    
    dummy_state = DummyState()
    return await run_single_analysis_async_safe(user_query, dummy_state)


def stop_analysis():
    """停止正在运行的分析"""
    st.session_state.analysis_cancelled = True
    st.session_state.analysis_running = False
    st.session_state.analysis_status = "正在停止分析..."
    
    # 设置状态对象的取消标志
    analysis_state_obj = st.session_state.get('analysis_state_obj')
    if analysis_state_obj:
        analysis_state_obj.cancelled = True
        analysis_state_obj.running = False
        analysis_state_obj.status = "正在停止分析..."
    
    # 如果有运行中的线程，标记为取消
    if hasattr(st.session_state, 'analysis_thread') and st.session_state.analysis_thread:
        # 线程会检查 analysis_cancelled 标志并自行退出
        pass

def reset_analysis_state():
    """重置分析状态"""
    st.session_state.analysis_running = False
    st.session_state.analysis_completed = False
    st.session_state.analysis_cancelled = False
    st.session_state.analysis_status = "系统空闲"
    st.session_state.analysis_progress = 0
    st.session_state.analysis_result = None
    st.session_state.current_session_data = None
    st.session_state.analysis_thread = None


def show_advanced_configuration():
    """高级配置区域"""
    with st.expander("⚙️ 高级配置", expanded=False):
        st.markdown("### 🔧 系统配置")
        
        config_col1, config_col2 = st.columns(2)
        
        with config_col1:
            st.markdown("#### 📝 环境配置 (.env)")
            
            # 读取.env文件
            env_path = Path(".env")
            if env_path.exists():
                with open(env_path, 'r', encoding='utf-8') as f:
                    env_content = f.read()
            else:
                env_content = "# 环境配置文件\n"
            
            # 环境配置编辑器
            new_env_content = st.text_area(
                "编辑环境配置",
                value=env_content,
                height=200,
                key="env_editor"
            )
            
            if st.button("💾 保存环境配置"):
                try:
                    with open(env_path, 'w', encoding='utf-8') as f:
                        f.write(new_env_content)
                    st.success("✅ 环境配置已保存")
                    
                    # 提示需要重连
                    if st.session_state.get('orchestrator'):
                        st.warning("⚠️ 配置已更改，建议断开重连以生效")
                        if st.button("🔄 一键重连"):
                            disconnect_orchestrator()
                            connect_orchestrator()
                except Exception as e:
                    st.error(f"❌ 保存失败: {e}")
        
        with config_col2:
            st.markdown("#### 🛠️ MCP工具配置")
            
            # MCP权限配置
            st.markdown("**智能体MCP权限开关**")
            
            # 按团队分组显示权限开关
            agent_groups = {
                "分析师团队": [
                    ("company_overview_analyst", "🏢 公司概述分析师"),
                    ("market_analyst", "📈 市场分析师"),
                    ("sentiment_analyst", "😊 情绪分析师"),
                    ("news_analyst", "📰 新闻分析师"),
                    ("fundamentals_analyst", "📋 基本面分析师"),
                    ("shareholder_analyst", "👥 股东分析师"),
                    ("product_analyst", "🏭 产品分析师")
                ],
                "研究团队": [
                    ("bull_researcher", "🐂 看涨研究员"),
                    ("bear_researcher", "🐻 看跌研究员")
                ],
                "管理层": [
                    ("research_manager", "👔 研究经理"),
                    ("trader", "💼 交易员")
                ],
                "风险管理团队": [
                    ("aggressive_risk_analyst", "⚖️ 风险看涨研究员"),
                    ("safe_risk_analyst", "⚖️ 风险看跌研究员"),
                    ("neutral_risk_analyst", "⚖️ 中立风险分析师"),
                    ("risk_manager", "🛡️ 风险经理")
                ]
            }
            
            # 读取当前权限配置
            load_dotenv()
            config_changed = False
            
            for group_name, agents in agent_groups.items():
                st.markdown(f"**{group_name}**")
                for agent_key, agent_name in agents:
                    env_key = f"MCP_ENABLED_{agent_key.upper()}"
                    current_value = os.getenv(env_key, "false").lower() == "true"
                    
                    new_value = st.checkbox(
                        agent_name,
                        value=current_value,
                        key=f"mcp_{agent_key}"
                    )
                    
                    if new_value != current_value:
                        config_changed = True
                        # 更新环境变量
                        os.environ[env_key] = "true" if new_value else "false"
            
            if config_changed:
                if st.button("💾 保存MCP权限配置"):
                    try:
                        # 更新.env文件中的MCP权限配置
                        update_mcp_permissions_in_env()
                        st.success("✅ MCP权限配置已保存")
                        
                        # 提示需要重连
                        if st.session_state.get('orchestrator'):
                            st.warning("⚠️ 权限配置已更改，建议断开重连以生效")
                    except Exception as e:
                        st.error(f"❌ 保存失败: {e}")
        
        st.markdown("---")
        st.markdown("#### 🔗 连接状态管理")
        
        conn_status_col1, conn_status_col2, conn_status_col3 = st.columns(3)
        
        with conn_status_col1:
            if st.session_state.get('orchestrator'):
                st.success("🟢 系统已连接")
            else:
                st.error("🔴 系统未连接")
        
        with conn_status_col2:
            if st.button("🔄 重新加载配置"):
                load_dotenv()
                st.success("✅ 配置已重新加载")
        
        with conn_status_col3:
            if st.button("🧹 清理会话状态"):
                reset_analysis_state()
                st.success("✅ 会话状态已清理")


def update_mcp_permissions_in_env():
    """更新.env文件中的MCP权限配置"""
    env_path = Path(".env")
    
    # 读取现有内容
    if env_path.exists():
        with open(env_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    else:
        lines = []
    
    # 更新MCP权限配置
    agent_keys = [
        "company_overview_analyst", "market_analyst", "sentiment_analyst", "news_analyst",
        "fundamentals_analyst", "shareholder_analyst", "product_analyst",
        "bull_researcher", "bear_researcher", "research_manager", "trader",
        "aggressive_risk_analyst", "safe_risk_analyst", "neutral_risk_analyst", "risk_manager"
    ]
    
    # 构建新的配置行
    new_lines = []
    processed_keys = set()
    
    for line in lines:
        line = line.strip()
        if line.startswith("MCP_ENABLED_"):
            # 提取键名
            key_part = line.split('=')[0].replace("MCP_ENABLED_", "").lower()
            if key_part in agent_keys:
                # 使用新值
                env_key = f"MCP_ENABLED_{key_part.upper()}"
                new_value = os.getenv(env_key, "false")
                new_lines.append(f"{env_key}={new_value}\n")
                processed_keys.add(key_part)
            else:
                new_lines.append(line + "\n")
        else:
            new_lines.append(line + "\n")
    
    # 添加未处理的键
    for key in agent_keys:
        if key not in processed_keys:
            env_key = f"MCP_ENABLED_{key.upper()}"
            value = os.getenv(env_key, "false")
            new_lines.append(f"{env_key}={value}\n")
    
    # 写回文件
    with open(env_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)


def main():
    """主界面 - 紧凑化设计"""
    # 加载样式
    load_page_styles()
    
    # 显示专业抬头
    st.markdown(create_header_html(), unsafe_allow_html=True)
    
    # 系统概览（紧凑版）
    show_system_overview()
    
    # 工作流程图（紧凑版）
    show_workflow_diagram()
    
    # 实时分析区域
    st.markdown('<div style="margin: 15px 0 10px 0;"></div>', unsafe_allow_html=True)
    show_real_time_analysis()
    
    # 历史会话管理
    st.markdown('<div style="margin: 15px 0 10px 0;"></div>', unsafe_allow_html=True)
    show_history_management()
    
    # 导出选项（简化版）
    st.markdown('<div style="margin: 15px 0 10px 0;"></div>', unsafe_allow_html=True)
    show_export_options()
    
    # 分析结果展示
    st.markdown('<div style="margin: 15px 0 10px 0;"></div>', unsafe_allow_html=True)
    show_analysis_results()
    
    # 高级配置区域（折叠式）
    with st.expander("⚙️ 高级配置", expanded=False):
        show_advanced_configuration()
    
    # 底部状态信息（紧凑版）
    env_status = "✅" if Path(".env").exists() else "❌"
    mcp_status = "✅" if Path("mcp_config.json").exists() else "❌"
    
    status_html = f"""
    <div style="text-align: center; color: var(--text-muted); font-size: 0.8rem; margin-top: 1rem; padding: 8px;">
        <p>系统状态: 环境配置 {env_status} | MCP配置 {mcp_status} | 🏛️ 人工智能实验室</p>
    </div>
    """
    
    st.markdown(status_html, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
