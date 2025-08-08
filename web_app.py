#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TradingAgents-MCPmode Web前端 - 超简化版本
删除了有问题的摘要展开功能和高级配置模块
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
    from src.web.css_loader import load_financial_css, inject_custom_html, create_header_html
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

# 隐藏Streamlit警告信息
import warnings
warnings.filterwarnings("ignore")

# 隐藏控制台日志
import logging
logging.getLogger().setLevel(logging.ERROR)

# 隐藏Streamlit的一些UI元素
try:
    st.set_option('client.showErrorDetails', False)
    st.set_option('client.toolbarMode', 'minimal')
except:
    pass

# 添加CSS隐藏不需要的元素
st.markdown("""
<style>
/* 隐藏成功提示框 */
.stAlert[data-testid="stAlertContainer"] {
    display: none !important;
}

/* 隐藏警告提示框 */
.stAlert {
    display: none !important;
}

/* 隐藏所有通知 */
[data-baseweb="notification"] {
    display: none !important;
}

/* 隐藏Streamlit的默认警告 */
.stException {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

# 初始化会话状态
if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = None
if "analysis_running" not in st.session_state:
    st.session_state.analysis_running = False
if "selected_session_file" not in st.session_state:
    st.session_state.selected_session_file = None
if "current_session_data" not in st.session_state:
    st.session_state.current_session_data = None
if "analysis_completed" not in st.session_state:
    st.session_state.analysis_completed = False


def load_page_styles():
    """加载页面样式"""
    try:
        load_financial_css()
        inject_custom_html()
    except:
        pass


@st.cache_data(ttl=5)
def get_session_files_list():
    """获取会话文件列表"""
    try:
        dump_dir = Path("src/dump")
        if not dump_dir.exists():
            return []
        return sorted(dump_dir.glob("session_*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
    except:
        return []


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
        'research_manager': '👔 研究经理',
        'trader': '💼 交易员',
        'aggressive_risk_analyst': '⚡ 激进风险分析师',
        'safe_risk_analyst': '🛡️ 保守风险分析师',
        'neutral_risk_analyst': '⚖️ 中性风险分析师',
        'risk_manager': '🎯 风险经理'
    }
    return name_mapping.get(agent_name, agent_name)


def connect_orchestrator():
    """连接WorkflowOrchestrator"""
    if WorkflowOrchestrator is None:
        return False
    
    try:
        load_dotenv()
        orchestrator = WorkflowOrchestrator()
        st.session_state.orchestrator = orchestrator
        return True
    except Exception as e:
        print(f"连接失败: {e}")  # 只在控制台输出，不在前端显示
        return False


def disconnect_orchestrator():
    """断开WorkflowOrchestrator连接"""
    if st.session_state.get('orchestrator'):
        st.session_state.orchestrator = None
        st.success("✅ 系统已断开连接")


def show_real_time_analysis():
    """实时分析模块 - 自动连接版本"""
    if WorkflowOrchestrator is None:
        st.error("😱 无法加载WorkflowOrchestrator，请检查后端配置")
        return
    
    # 自动连接系统（如果未连接）
    if not st.session_state.get('orchestrator'):
        if connect_orchestrator():
            st.session_state.auto_connected = True
    
    # 简化的输入和控制
    query = st.text_input(
        "输入查询",
        placeholder="例如：给我分析一下600833吧",
        key="analysis_query_simple"
    )
    
    # 简化的按钮布局 - 只显示开始/停止
    btn_col1, btn_col2 = st.columns(2)
    
    with btn_col1:
        if st.session_state.analysis_running:
            if st.button("⏹️ 停止分析", use_container_width=True):
                stop_analysis()
        else:
            orchestrator_connected = st.session_state.get('orchestrator') is not None
            analysis_disabled = not query or not orchestrator_connected
            if st.button("🚀 开始分析", disabled=analysis_disabled, use_container_width=True):
                if query:
                    start_analysis(query)
    
    with btn_col2:
        # 简化的进度显示
        if st.session_state.get('analysis_running') or st.session_state.get('analysis_completed'):
            progress_data = get_real_analysis_progress()
            if progress_data:
                progress = progress_data['progress']
                st.progress(progress / 100.0)
                st.caption(f"{progress_data['status']} ({progress_data['completed_agents']}/15)")
        else:
            # 显示连接状态
            if st.session_state.get('orchestrator'):
                st.success("🟢 系统已就绪")
            else:
                st.error("🔴 系统未连接")
    
    # 完成提示
    if st.session_state.analysis_completed:
        st.success("✅ 分析完成！请查看下方结果。")


def show_history_management():
    """历史会话管理 - 超简化版本"""
    # 获取所有JSON文件
    json_files = get_session_files_list()
    if not json_files:
        st.info("📭 暂无历史分析数据")
        return
    
    # 简化的文件选择
    file_options = []
    for json_file in json_files:
        file_time = datetime.fromtimestamp(json_file.stat().st_mtime)
        display_name = f"{json_file.name} ({file_time.strftime('%m-%d %H:%M')})"
        file_options.append(display_name)
    
    # 记忆选中项索引
    if "history_selected_index" not in st.session_state:
        st.session_state.history_selected_index = 0
    
    def on_session_change():
        """会话选择变化时自动加载"""
        selected_idx = st.session_state.history_selector_simple
        if selected_idx < len(json_files):
            selected_file = str(json_files[selected_idx])
            load_session_data(selected_file)
            st.session_state.history_selected_index = selected_idx
    
    selected_index = st.selectbox(
        "选择历史会话",
        range(len(file_options)),
        index=min(st.session_state.history_selected_index, len(file_options) - 1),
        format_func=lambda i: file_options[i],
        key="history_selector_simple",
        on_change=on_session_change
    )
    
    # 静默加载会话信息，不显示提示
    if st.session_state.current_session_data:
        # 静默处理，不显示任何提示
        pass


def show_export_options():
    """导出选项 - 超简化版本"""
    if not st.session_state.current_session_data or not st.session_state.selected_session_file:
        st.info("请先加载会话数据")
        return
    
    # 简化的导出按钮
    export_col1, export_col2, export_col3 = st.columns(3)
    
    with export_col1:
        if st.button("📄 导出MD", key="export_md_simple"):
            export_to_markdown()
    
    with export_col2:
        if st.button("📄 导出PDF", key="export_pdf_simple"):
            export_to_pdf()
    
    with export_col3:
        if st.button("📄 导出Word", key="export_word_simple"):
            export_to_docx()


def show_analysis_results():
    """分析结果展示 - 简化版本"""
    if not st.session_state.current_session_data:
        st.info("请先运行分析或加载历史会话查看结果")
        return
    
    data = st.session_state.current_session_data
    
    # 显示会话基本信息
    info_col1, info_col2, info_col3 = st.columns(3)
    with info_col1:
        st.metric("会话ID", data.get('session_id', 'N/A')[:8] + "...")
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
    """显示单个智能体结果 - 简洁直接模式，不搞复杂的摘要展开"""
    agent_name = agent.get('agent_name', 'Unknown')
    display_name = get_agent_display_name(agent_name)
    result_content = agent.get('result', '')
    
    if not result_content:
        with st.expander(display_name, expanded=False):
            st.info("该智能体暂无分析结果")
        return
    
    # 直接显示完整内容，删除有问题的摘要展开功能
    with st.expander(display_name, expanded=False):
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
        # 静默加载，不显示任何提示，不调用st.rerun()
    except Exception as e:
        # 静默处理错误，不在前端显示
        print(f"加载失败: {str(e)}")


@st.cache_data(ttl=2)
def get_real_analysis_progress():
    """从真实的会话JSON文件获取进度"""
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
                status = f"已完成 {completed_agents} 个智能体"
        
        return {
            'progress': progress,
            'status': status,
            'completed_agents': completed_agents,
            'total_agents': total_agents,
            'session_file': str(latest_session)
        }
        
    except Exception as e:
        return None


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
    
    # 将orchestrator传递给分析函数
    run_analysis_sync(query, st.session_state.orchestrator)


def run_analysis_sync(query: str, orchestrator):
    """在后台线程中运行分析，避免阻塞Streamlit主线程"""
    import threading
    
    class AnalysisState:
        def __init__(self):
            self.cancelled = False
            self.running = True
            self.completed = False
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
                analysis_state.running = False
                return
            
            # 在新的事件循环中运行异步函数
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(run_single_analysis_async_safe(query, orchestrator, analysis_state))
                
                # 再次检查是否已被取消
                if analysis_state.cancelled:
                    analysis_state.running = False
                    return
                
                # 分析成功
                analysis_state.result = result
                analysis_state.completed = True
                analysis_state.running = False
                
            finally:
                loop.close()
                
        except Exception as e:
            # 检查是否是取消导致的异常
            if not analysis_state.cancelled:
                error_msg = str(e)
                analysis_state.error = error_msg
            analysis_state.running = False
            analysis_state.completed = False
    
    # 启动后台线程
    thread = threading.Thread(target=run_analysis_thread, daemon=True)
    thread.start()
    
    # 存储线程引用和状态对象
    st.session_state.analysis_thread = thread
    st.session_state.analysis_state_obj = analysis_state


async def run_single_analysis_async_safe(user_query: str, orchestrator, analysis_state) -> Optional[dict]:
    """安全的异步分析函数"""
    try:
        # 检查取消状态
        if analysis_state.cancelled:
            return None
            
        workflow_info = orchestrator.get_workflow_info()
        enabled_agents = orchestrator.get_enabled_agents()
        
        # 检查取消状态
        if analysis_state.cancelled:
            return None
        
        # 创建取消检查器函数
        def cancel_checker():
            return analysis_state.cancelled
        
        result = await orchestrator.run_analysis(user_query, cancel_checker)
        
        # 检查取消状态
        if analysis_state.cancelled:
            return None
        
        return result
        
    except Exception as e:
        # 检查是否是取消导致的异常
        if analysis_state.cancelled:
            return None
        raise


def stop_analysis():
    """停止正在运行的分析"""
    st.session_state.analysis_cancelled = True
    st.session_state.analysis_running = False
    
    # 设置状态对象的取消标志
    analysis_state_obj = st.session_state.get('analysis_state_obj')
    if analysis_state_obj:
        analysis_state_obj.cancelled = True
        analysis_state_obj.running = False


def main():
    """主界面 - 超紧凑设计，用户快速看到报告"""
    # 加载样式
    load_page_styles()
    
    # 显示专业抬头
    try:
        st.markdown(create_header_html(), unsafe_allow_html=True)
    except:
        st.title("🏛️ AI实验室 - TradingAgents")
    
    # 核心功能区域 - 左右布局，减少滚动
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # 实时分析区域（紧凑版）
        st.markdown("### 🔍 实时分析")
        show_real_time_analysis()
        
        # 历史会话管理（紧凑版）
        st.markdown("### 📚 历史会话")
        show_history_management()
    
    with col2:
        # 导出选项（紧凑版）
        st.markdown("### 📤 导出报告")
        show_export_options()
        
        # 系统状态（超紧凑版）
        env_status = "✅" if Path(".env").exists() else "❌"
        mcp_status = "✅" if Path("mcp_config.json").exists() else "❌"
        
        st.markdown(f"**系统状态:** 环境 {env_status} | MCP {mcp_status}")
    
    # 分析结果展示 - 放在最前面，用户不用滚动就能看到
    st.markdown("---")
    st.markdown("### 📈 分析结果")
    show_analysis_results()


if __name__ == "__main__":
    main()
